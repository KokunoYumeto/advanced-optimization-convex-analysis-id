from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
MIT = ROOT / "authority" / "mit-ocw-6.253"
ROYER = ROOT / "authority" / "royer-stochastic-gradient"
OUT = ROOT / "00_control" / "MIT_ROYER_SOURCE_FREEZE.json"

MIT_COMMIT = "58d7c86195f09dd8708b84dde28205d3199207dd"
MIT_TREE = "26d3136df9d5d7f564f0b1d068ec8d7a7c8818d6"
MIT_RESOURCE_BASE = (
    "https://ocw.mit.edu/courses/"
    "6-253-convex-analysis-and-optimization-spring-2012/"
)

MIT_CLOSURE = [
    ("lecture-notes", "6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf"),
    ("homework-01-prompt", "6b7e833111c72d30c8dc133595ae56e3_MIT6_253S12_hw01.pdf"),
    ("homework-01-solution", "1c82f0600edfc8ab4da06362882b5d7b_MIT6_253S12_hw01_sol.pdf"),
    ("homework-02-prompt", "8822623ef1e07e150f9c7f1b187b413e_MIT6_253S12_hw02.pdf"),
    ("homework-02-solution", "9930cdcf286c1f320c414b9cebaa1b47_MIT6_253S12_hw02_sol.pdf"),
    ("homework-03-prompt", "e348281657308eca9dfffffa70e80328_MIT6_253S12_hw03.pdf"),
    ("homework-03-solution", "7cac6d51273426678c66de3949ec8f41_MIT6_253S12_hw03_sol.pdf"),
    ("homework-04-prompt", "970fa2cdff9b50292b977eb5b7d88da8_MIT6_253S12_hw04.pdf"),
    ("homework-04-solution", "f3c9d9506f80f996010915cf8a86b57d_MIT6_253S12_hw04_sol.pdf"),
    ("homework-05-prompt", "c55025e7eddd84b56c166e7d4bdce687_MIT6_253S12_hw05.pdf"),
    ("homework-05-solution", "906236c9b1adcc1aac789d7cd04ebe1a_MIT6_253S12_hw05_sol.pdf"),
    ("spring-2010-midterm-with-solution", "22c593932434f1bb33f1ddcf7f52f367_MIT6_253S12_mid_S10_sol.pdf"),
    ("spring-2012-midterm-with-solution", "772b8b0aace4b5eaa1397b2da8adad87_MIT6_253S12_midterm_sol.pdf"),
]

EXPECTED = {
    "mit_course_zip": (41452759, "32e241f7101943e285c8b56ca61ae117b647d67015ff8b1048ab598319d7389f"),
    "mit_complete_notes": (8030116, "41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181"),
    "mit_repo_zip": (32975, "e0ded208972802866e0a5a733163c4792f487a2367ee008f7fb9a1f919853f28"),
    "royer_notes": (684631, "3290c61e870ef807ae92c4ace309449ee46ab3aa544e033c100f4a005311dfd3"),
    "royer_lab01_zip": (382975, "88e18ea096b87bd12d182072bfbf6fd12ac73d666e16911a3f015ee9a574d461"),
    "royer_lab02_zip": (371793, "0a0a908157dcf07f0dd3874c118e416dad3033a5f04f9cb37ae248b2f8feb623"),
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path, **extra: object) -> dict[str, object]:
    record: dict[str, object] = {
        "path": rel(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    record.update(extra)
    return record


def pdf_artifact(path: Path, **extra: object) -> dict[str, object]:
    reader = PdfReader(path)
    return artifact(path, pages=len(reader.pages), **extra)


def assert_anchor(name: str, record: dict[str, object]) -> None:
    expected_bytes, expected_sha = EXPECTED[name]
    if record["bytes"] != expected_bytes or record["sha256"] != expected_sha:
        raise RuntimeError(
            f"anchor mismatch for {name}: "
            f"{record['bytes']} / {record['sha256']}"
        )


def safe_zip_inventory(
    zip_path: Path,
    extracted_root: Path,
    output_tsv: Path,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    names: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or re.match(r"^[A-Za-z]:", name):
                raise RuntimeError(f"unsafe ZIP entry in {zip_path}: {name}")
            names.append(name)
            is_dir = info.is_dir()
            data = b"" if is_dir else archive.read(info)
            if not is_dir:
                extracted = extracted_root.joinpath(*pure.parts)
                if not extracted.is_file():
                    raise RuntimeError(f"missing extracted ZIP member: {extracted}")
                if extracted.read_bytes() != data:
                    raise RuntimeError(f"extracted ZIP member mismatch: {extracted}")
            rows.append(
                {
                    "path": name,
                    "kind": "directory" if is_dir else "file",
                    "bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "crc32": f"{info.CRC:08x}",
                    "sha256": "" if is_dir else sha256_bytes(data),
                }
            )
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        raise RuntimeError(f"duplicate ZIP entries in {zip_path}: {duplicates}")
    output_tsv.parent.mkdir(parents=True, exist_ok=True)
    with output_tsv.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["path", "kind", "bytes", "compressed_bytes", "crc32", "sha256"],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    return {
        "archive": artifact(zip_path),
        "entry_count": len(rows),
        "file_count": sum(row["kind"] == "file" for row in rows),
        "uncompressed_bytes": sum(int(row["bytes"]) for row in rows),
        "duplicates": 0,
        "unsafe_entries": 0,
        "extracted_identity": "pass",
        "entry_manifest": artifact(output_tsv),
    }


def notebook_record(path: Path, role: str) -> dict[str, object]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cells = notebook.get("cells", [])
    code = [cell for cell in cells if cell.get("cell_type") == "code"]
    markdown = [cell for cell in cells if cell.get("cell_type") == "markdown"]
    return artifact(
        path,
        role=role,
        cells=len(cells),
        code_cells=len(code),
        markdown_cells=len(markdown),
        code_cells_with_outputs=sum(bool(cell.get("outputs")) for cell in code),
        total_outputs=sum(len(cell.get("outputs", [])) for cell in code),
        empty_code_cells=sum(not "".join(cell.get("source", [])).strip() for cell in code),
        null_execution_count=sum(cell.get("execution_count") is None for cell in code),
    )


def main() -> None:
    mit_course_zip = MIT / "downloads" / "6.253-spring-2012.zip"
    mit_repo_zip = MIT / "repository" / f"6.253-spring-2012-{MIT_COMMIT}.zip"
    mit_course_entries = MIT / "downloads" / "6.253-spring-2012.entries.sha256.tsv"
    mit_repo_entries = MIT / "repository" / f"6.253-spring-2012-{MIT_COMMIT}.entries.sha256.tsv"
    lab01_entries = ROYER / "downloads" / "SourcesLabSG01.entries.sha256.tsv"
    lab02_entries = ROYER / "downloads" / "SourcesLabSG02.entries.sha256.tsv"

    mit_zip = safe_zip_inventory(
        mit_course_zip,
        MIT / "course-archive",
        mit_course_entries,
    )
    repo_zip = safe_zip_inventory(
        mit_repo_zip,
        MIT / "repository" / "snapshot",
        mit_repo_entries,
    )
    lab01_zip = safe_zip_inventory(
        ROYER / "downloads" / "SourcesLabSG01.zip",
        ROYER / "labs" / "lab01",
        lab01_entries,
    )
    lab02_zip = safe_zip_inventory(
        ROYER / "downloads" / "SourcesLabSG02.zip",
        ROYER / "labs" / "lab02",
        lab02_entries,
    )

    assert_anchor("mit_course_zip", mit_zip["archive"])
    assert_anchor("mit_repo_zip", repo_zip["archive"])
    assert_anchor("royer_lab01_zip", lab01_zip["archive"])
    assert_anchor("royer_lab02_zip", lab02_zip["archive"])

    static = MIT / "course-archive" / "static_resources"
    pdf_inventory = []
    for path in sorted(static.glob("*.pdf"), key=lambda item: item.name.lower()):
        pdf_inventory.append(
            pdf_artifact(
                path,
                name=path.name,
                official_url=MIT_RESOURCE_BASE + path.name,
            )
        )
    if len(pdf_inventory) != 39:
        raise RuntimeError(f"expected 39 MIT PDFs, found {len(pdf_inventory)}")

    by_name = {str(record["name"]): record for record in pdf_inventory}
    closure = []
    for role, name in MIT_CLOSURE:
        if name not in by_name:
            raise RuntimeError(f"missing MIT closure file: {name}")
        closure.append({"role": role, **by_name[name]})
    closure_bytes = sum(int(record["bytes"]) for record in closure)
    closure_pages = sum(int(record["pages"]) for record in closure)
    if len(closure) != 13 or closure_bytes != 10417664 or closure_pages != 395:
        raise RuntimeError(
            f"MIT closure mismatch: {len(closure)} / {closure_bytes} / {closure_pages}"
        )
    assert_anchor("mit_complete_notes", closure[0])

    commit_path = MIT / "repository" / f"commit-{MIT_COMMIT}.json"
    tree_path = MIT / "repository" / f"tree-{MIT_TREE}.json"
    branch_path = MIT / "repository" / "branch-main-observed-20260822.json"
    commit_json = json.loads(commit_path.read_text(encoding="utf-8"))
    tree_json = json.loads(tree_path.read_text(encoding="utf-8"))
    branch_json = json.loads(branch_path.read_text(encoding="utf-8"))
    if commit_json["sha"] != MIT_COMMIT or commit_json["commit"]["tree"]["sha"] != MIT_TREE:
        raise RuntimeError("MIT commit API identity mismatch")
    if tree_json["sha"] != MIT_TREE or tree_json.get("truncated"):
        raise RuntimeError("MIT tree API identity mismatch")
    if branch_json["commit"]["sha"] != MIT_COMMIT:
        raise RuntimeError("MIT main branch observation mismatch")

    snapshot_files = [
        path
        for path in (MIT / "repository" / "snapshot").rglob("*")
        if path.is_file()
    ]
    snapshot_extensions = Counter(path.suffix.lower() or "<none>" for path in snapshot_files)
    if any(path.suffix.lower() in {".pdf", ".tex", ".ltx"} for path in snapshot_files):
        raise RuntimeError("unexpected mathematical PDF/TeX in MIT metadata repository")

    royer_notes = pdf_artifact(
        ROYER / "downloads" / "LectureNotesOML-SG.pdf",
        role="stochastic-gradient-notes",
        official_url="https://www.lamsade.dauphine.fr/~croyer/ensdocs/SG/LectureNotesOML-SG.pdf",
    )
    assert_anchor("royer_notes", royer_notes)
    royer_boards = [
        pdf_artifact(
            ROYER / "downloads" / f"boardSG0{index}.pdf",
            role=f"virtual-board-{index}",
            official_url=(
                "https://www.lamsade.dauphine.fr/~croyer/ensdocs/SG/"
                f"boardSG0{index}.pdf"
            ),
        )
        for index in range(1, 4)
    ]
    royer_notebooks = [
        notebook_record(
            ROYER / "labs" / "lab01" / "LabSG01-2324.ipynb",
            "laboratory-01",
        ),
        notebook_record(
            ROYER / "labs" / "lab02" / "LabSG02.ipynb",
            "laboratory-02",
        ),
    ]

    manifest: dict[str, object] = {
        "schema": "o015-mit-royer-source-freeze-v1",
        "lane": "O015",
        "role": "D90 Advanced Optimization and Convex Analysis",
        "frozen_on": "2026-08-22",
        "result": "pass_with_declared_gaps",
        "mit_ocw_6_253": {
            "title": "Convex Analysis and Optimization",
            "creator": "Dimitri P. Bertsekas",
            "term": "Spring 2012",
            "official_course": MIT_RESOURCE_BASE,
            "official_lecture_notes": MIT_RESOURCE_BASE + "pages/lecture-notes/",
            "official_assignments": MIT_RESOURCE_BASE + "pages/assignments/",
            "official_exams": MIT_RESOURCE_BASE + "pages/exams/",
            "official_download": MIT_RESOURCE_BASE + "6.253-spring-2012.zip",
            "official_pages": [
                artifact(MIT / "official-pages" / name)
                for name in [
                    "course.html",
                    "lecture-notes.html",
                    "assignments.html",
                    "exams.html",
                    "download.html",
                    "terms.html",
                    "CC-BY-NC-SA-4.0-legalcode.txt",
                ]
            ],
            "course_archive": mit_zip,
            "repository": {
                "url": "https://github.com/mitocwcontent/6.253-spring-2012",
                "commit": MIT_COMMIT,
                "tree": MIT_TREE,
                "main_observed_at_commit": True,
                "commit_api": artifact(commit_path),
                "tree_api": artifact(tree_path),
                "branch_api": artifact(branch_path),
                "archive": repo_zip,
                "tree_entries": len(tree_json["tree"]),
                "tree_blobs": sum(item["type"] == "blob" for item in tree_json["tree"]),
                "tree_directories": sum(item["type"] == "tree" for item in tree_json["tree"]),
                "snapshot_files": len(snapshot_files),
                "snapshot_extensions": dict(sorted(snapshot_extensions.items())),
                "mathematical_tex_files": 0,
                "pdf_files": 0,
                "disposition": "OCW/Hugo metadata only; not mathematical editable source",
            },
            "resource_pdf_inventory": pdf_inventory,
            "selected_teaching_closure": {
                "files": closure,
                "count": len(closure),
                "bytes": closure_bytes,
                "pages": closure_pages,
                "homework_prompt_pages": sum(
                    int(record["pages"])
                    for record in closure
                    if str(record["role"]).endswith("prompt")
                ),
                "homework_solution_pages": sum(
                    int(record["pages"])
                    for record in closure
                    if str(record["role"]).endswith("solution")
                    and "midterm" not in str(record["role"])
                ),
                "midterm_pages": sum(
                    int(record["pages"])
                    for record in closure
                    if "midterm" in str(record["role"])
                ),
            },
            "supplementary_or_redundant": {
                "individual_lecture_pdfs": 25,
                "athena_summary_pdf": next(
                    record for record in pdf_inventory if "summary" in str(record["name"]).lower()
                ),
                "disposition": (
                    "individual lecture PDFs duplicate the complete notes; the 59-page "
                    "Athena Scientific summary is a third-party, permission-ambiguous "
                    "component and is excluded"
                ),
            },
            "license": {
                "expression": "CC BY-NC-SA 4.0",
                "translation_permitted": True,
                "requirements": [
                    "attribution",
                    "license link",
                    "identify changes",
                    "noncommercial use",
                    "ShareAlike",
                    "no additional restrictions",
                    "MIT name and logo restrictions",
                    "no implied endorsement",
                ],
                "third_party_exception": (
                    "complete-notes page 1 says all figures are courtesy of Athena "
                    "Scientific and used with permission; no Athena figure bytes or layout "
                    "are admitted into the derivative"
                ),
            },
            "known_solution_gap": (
                "the Spring 2012 midterm solution contains the literal placeholder "
                "'(a) To be added.'; repair must be separately authored and attributed"
            ),
            "pilot_boundary": {
                "authority_pdf": rel(static / MIT_CLOSURE[0][1]),
                "pdf_pages": [2, 3, 4, 5],
                "title": "Lecture 1 - The Role of Convexity in Optimization",
                "next_topic_starts_page": 6,
                "athena_figures_in_boundary": 0,
                "disposition": "admitted for fail-closed semantic-source pilot",
            },
        },
        "royer_stochastic_gradient": {
            "title": "Optimization for Machine Learning - Stochastic Gradient",
            "creator": "Clément W. Royer",
            "official_course": "https://www.lamsade.dauphine.fr/~croyer/teachSG.html",
            "official_page": artifact(ROYER / "official-pages" / "teachSG.html"),
            "notes": royer_notes,
            "laboratory_archives": [lab01_zip, lab02_zip],
            "notebooks": royer_notebooks,
            "virtual_boards": royer_boards,
            "selected_core_pages": int(royer_notes["pages"]),
            "virtual_board_pages_not_counted_in_core": sum(
                int(record["pages"]) for record in royer_boards
            ),
            "license": {
                "expression": "CC BY-NC 4.0",
                "declared_on_official_course_page_for_materials_on_page": True,
                "legalcode": artifact(
                    ROYER / "official-pages" / "CC-BY-NC-4.0-legalcode.txt"
                ),
                "translation_permitted": True,
                "requirements": [
                    "attribution",
                    "license link",
                    "identify changes",
                    "noncommercial use",
                    "no additional restrictions",
                    "no implied endorsement",
                ],
            },
            "editable_source": {
                "notes_tex": False,
                "notebooks": True,
                "notebook_dependencies_unpinned": True,
            },
            "exercise_solution_closure": {
                "formal_exercises": 3,
                "solutions": 3,
                "hints": 0,
                "lab01": "substantially executed",
                "lab02": (
                    "not answer-complete: four unanswered discussion cells and an "
                    "unimplemented optional Momentum/Adam section"
                ),
            },
            "component_credits": [
                "A. Gramfort",
                "Robert Gower",
            ],
        },
        "selected_external_core": {
            "mit_pages": closure_pages,
            "royer_pages": int(royer_notes["pages"]),
            "pages": closure_pages + int(royer_notes["pages"]),
            "expected_pages": 440,
        },
    }
    if manifest["selected_external_core"]["pages"] != 440:  # type: ignore[index]
        raise RuntimeError("selected external core is not 440 pages")

    OUT.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "result": "pass_with_declared_gaps",
                "manifest": artifact(OUT),
                "mit_course_archive": mit_zip,
                "mit_teaching_closure": {
                    "files": len(closure),
                    "bytes": closure_bytes,
                    "pages": closure_pages,
                },
                "mit_repository": {
                    "commit": MIT_COMMIT,
                    "tree": MIT_TREE,
                    "tree_entries": len(tree_json["tree"]),
                    "blobs": sum(item["type"] == "blob" for item in tree_json["tree"]),
                },
                "royer_notes": royer_notes,
                "royer_notebooks": royer_notebooks,
                "selected_external_core_pages": 440,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
