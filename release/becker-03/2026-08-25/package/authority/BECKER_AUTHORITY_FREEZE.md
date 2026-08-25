# Becker authority freeze - exact commit 98ed6930084c

Freeze date: 2026-08-25 UTC

Scope: Stephen Becker's public `convex-optimization-class` repository, frozen without any Git command from official GitHub API, raw, and codeload endpoints. This freeze is an authority witness and candidate-source pool. It is not a blanket admission of every repository component into the Indonesian edition.

## Repository and revision identity

- Official repository: <https://github.com/stephenbeckr/convex-optimization-class>
- Official commit page: <https://github.com/stephenbeckr/convex-optimization-class/commit/98ed6930084c435ba0f675f7646ced1f2fd8729e>
- Commit: `98ed6930084c435ba0f675f7646ced1f2fd8729e`
- Tree: `f04670e3f7be3d4836c380fd8bd31883e0b992c9`
- Parent: `51aab4cb0e367cab34a99e504d56ef5f00991010`
- Author and committer: Stephen Becker
- Authored and committed: `2026-06-24T02:37:45Z`
- Commit message: `Add readme`
- GitHub verification state: unsigned (`verified=false`, reason `unsigned`); this is recorded as provenance, not treated as a content failure.
- Repository API snapshot on 2026-08-25 reports default branch `main`, current `main` tip equal to the frozen commit, SPDX license `MIT`, and `archived=false`, `disabled=false`.

The exact official codeload ZIP is:

`archive/convex-optimization-class-98ed6930084c435ba0f675f7646ced1f2fd8729e.zip`

It is 164,525,001 bytes with SHA-256 `52ec99acf2bfb7f4db308a7b0988ef9cfd28404a822c5cf0ac922d7f43c41821`. The ZIP contains one safe root, 180 files, 16 explicit directory entries, and 168,574,596 uncompressed file bytes. The extracted root is:

`extract/convex-optimization-class-98ed6930084c435ba0f675f7646ced1f2fd8729e/`

The official recursive tree response is not truncated: 195 API tree entries, of which 180 are blobs. Every extracted file's computed Git blob SHA-1 and byte size matches the corresponding official API blob. There are zero missing, extra, size-mismatched, or blob-ID-mismatched files. `BECKER_FILE_INVENTORY.csv` carries the per-file paths, byte counts, SHA-256 values, computed Git blob IDs, API blob IDs, and comparison result. `BECKER_ARCHIVE_TREE_VERIFICATION.json` carries the closure result.

## License and component rights

The root `LICENSE` is the MIT License, copyright 2017 Stephen Becker. The raw license downloaded from the frozen commit and the archive's root `LICENSE` are byte-identical: 1,071 bytes, SHA-256 `c026320fa977e084507f66ce2d4de70f3955b39a590f5cdd6e10e690e7a13cac`. Any admitted Becker text must preserve the copyright and MIT permission notice.

The root license must not erase explicit component notices:

- `utilities/firstOrderMethods.py` and `utilities/secondOrderMethods.py` embed a Modified BSD/BSD-3-Clause license and a 2023 Stephen Becker copyright notice.
- Four ADiGator polynomial-data-fit files under `Demos/AD_demos/ADiGator_demo/polydatafit/` carry GNU GPL version 3 notices and credit Matthew J. Weinstein and Anil V. Rao.
- Repository PDFs and demos may incorporate third-party material or external software. No such component enters the bounded source subset without its own rights check.

The candidate source root `TypedNotes/APPM5720Notes.tex` has no narrower component-license override and is covered by the repository's MIT grant. `TypedNotes/README.md` credits the Fall 2018 typed notes to Mitchell Krock; `APPM5720Notes.tex` also names Mitchell Krock. Those authorship credits must be retained. The separate verbose lecture-note series is credited to Jaden Wang and must retain that credit if ever used.

## Exact source inventory

The frozen tree has 180 files and 168,574,596 file bytes. It contains exactly:

- 42 TeX files: `TypedNotes/APPM5720Notes.tex`; 39 `TypedNotes/lecture_notes_tex/lec_XX.tex` files; `master.tex`; and `preamble.tex`.
- 1 local style file, `TypedNotes/notes.sty`.
- 70 PDFs, including 45 PDF-only files under `Notes/`, 5 Spring 2025 homework-assignment PDFs, helper/handout/project PDFs, and two compiled typed-note PDFs.
- 14 Jupyter notebooks, 6 Python files, 20 MATLAB `.m` files, 2 MATLAB live scripts, 2 MAT files, 2 pickle files, one C source, one Mach-O MEX binary, and one generated HTML demonstration.
- No Makefile, `latexmkrc`, Tectonic manifest, dependency lockfile, or other declared build driver.

The two genuine TeX aggregation roots are:

1. `TypedNotes/APPM5720Notes.tex`, supported by co-located `TypedNotes/notes.sty`, with the upstream witness `TypedNotes/APPM5720Notes.pdf` (49 pages, untagged).
2. `TypedNotes/lecture_notes_tex/master.tex`, intended to aggregate 38 of the 39 `lec_XX.tex` files and supported by same-directory `preamble.tex`, with upstream witness `TypedNotes/lecture_notes.pdf` (143 A4 pages, untagged). `lec_34.tex` exists but is omitted from `master.tex`.

The full machine-readable TeX, PDF, homework, heading, environment, dependency, figure-reference, topic, and component-rights census is in `BECKER_TEX_CLOSURE.json`.

## Build probe and fail-closed facts

All probes used isolated task-local source copies and task-local build directories. MiKTeX package auto-installation was disabled; no system package was installed and no third-party asset was fetched.

`TypedNotes/APPM5720Notes.tex` is the only proven source-closed TeX root. An unmodified one-pass `pdflatex` build exits 0 and produces a legible 48-page PDF in the current MiKTeX 26.5 environment. Two clean fixed-epoch runs both exit 0 with the same page structure but different PDF hashes, so byte-deterministic admission has not yet been established. The archived upstream PDF has 49 pages and was produced by an older TeX toolchain. This source root is lawful and practically buildable, but a deterministic wrapper/canonicalization gate is still required for a release derivative.

`TypedNotes/lecture_notes_tex/master.tex` is not source-complete and is not admissible:

- `master.tex` and all 39 lecture modules contain exactly 40 occurrences of `\input{../preamble.tex}`. From their actual directory this strict relative path resolves to absent `TypedNotes/preamble.tex`; the present file is `TypedNotes/lecture_notes_tex/preamble.tex`.
- An unmodified isolated build with a separate output directory fails immediately and exactly with `LaTeX Error: File '../preamble.tex' not found`.
- A reversible isolated-copy repair of all 40 references to `\input{preamble.tex}` advances only to undeclared environment dependencies (`filemod-expmin.sty`, with `gincltex` also absent). No system packages were installed to force the probe.
- More importantly, the 39 lecture sources contain 24 `includegraphics` references and every referenced figure is absent from the entire frozen tree. There is no `TypedNotes/lecture_notes_tex/figures/` directory. These are archive-absent source dependencies, not files that may be guessed or recreated.

The upstream 143-page compiled PDF is therefore a visual witness, not proof of editable reader closure. The master and its individual lecture modules remain fail-closed unless a later official, pinned, lawfully reusable source supplies the exact missing figure bytes and a deterministic build passes.

The public homework closure is also incomplete. `Homeworks/README.md` states explicitly that the assignments are in the repository but their solutions are on Canvas. The five Spring 2025 assignment PDFs, helper assets, and solution-labelled demonstrations do not constitute a complete public exercise/hint/answer/solution layer.

Accessibility is limited: both compiled typed-note PDFs report `Tagged: no`; the repository provides LaTeX source for the two typed-note families but no semantic HTML book, EPUB, tagged PDF, alt-text layer, or accessible exercise-solution navigation. The 24 missing figures further prevent a source-driven accessible reconstruction of the Jaden Wang master.

## Evidence identities

| Evidence | Bytes | SHA-256 |
|---|---:|---|
| `api/commit-98ed6930084c435ba0f675f7646ced1f2fd8729e.json` | 4,777 | `5db1622ed8443c7b8bd4b3439e619af3cd74c1ce2e926c936a76841bfc8d3826` |
| `api/tree-f04670e3f7be3d4836c380fd8bd31883e0b992c9-recursive.json` | 51,779 | `2c9e607fe30ce506c65557dc5fc989f7c302097200d1b8458a8de507719311ef` |
| `api/repository-2026-08-25.json` | 6,147 | `dabe983c6307aec40b47fdd5649ec63d57c63f7f2afb66544a193e3c68f3e5bb` |
| `api/branch-main-2026-08-25.json` | 3,923 | `b2cc2735a5f3d3f6bc746d8f2b06e9784854d0ab588ceba153c565a4159d1999` |
| `BECKER_FILE_INVENTORY.csv` | 39,017 | `4a0671a25dae2958ebf35a35ae00990cc182e011d98099f7cccc2faa4e5bb65d` |
| `BECKER_ARCHIVE_TREE_VERIFICATION.json` | 3,982 | `6c71915ad92bce36cf777317d3734ff64b64a1e57a86160a1c109b45dc095d78` |
| `BECKER_TEX_CLOSURE.json` | 53,116 | `ed8daa4ea9747077789a8dd6ab5d336f329ab5e0163990f170a16bee453965e1` |
| `BECKER_BUILD_PROBE.json` | 6,281 | `397dbe19aa334d74f27d5f55e5beb6a00a2af4b5ccdb83ba7c372f4b1cf32c2d` |

No translation, publication, upstream contact, or Git operation was performed during this freeze.
