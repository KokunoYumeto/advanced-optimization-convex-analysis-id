# O015 build and QA record

As of: 2026-08-21  
Unit: Habring Chapter 3 — Subgradients / Subgradien  
Admission: PASS

## Build inputs

- Wrapper: `source/id-ID/D90-HAB-03-subgradien-id.tex` — 3,940 bytes — SHA-256 `48fe2efc3fa2b724963e40942906061c5d7dc54c92ae4280641e951d55b4d669`.
- Translated chapter: `source/id-ID/habring-03-subgradien-id.tex` — 19,266 bytes — SHA-256 `d04ff82898c157f56924c6c08fd204bcd97625f060847fd8a0b6f7a2b90b0a5c`.
- Macros: `source/id-ID/macros-id.tex` — 4,465 bytes — SHA-256 `135642edfaffb7ec15e02e330dde76e694abe957da5f1a401c8563f9d885c1c2`.
- Class: `source/id-ID/shinybook.cls` — 10,133 bytes — SHA-256 `83514a06b2884dcaa02575bb3409d2f8cc9cf2fc6e6aef344b442d424850f2c0`.
- Figures are exact copies of the two arXiv-v1 raster assets and are bound separately in `COMPONENT_RIGHTS.csv` and the backend.

The final retained build used pdfTeX 1.40.29 / MiKTeX 26.5 and four `pdflatex` passes from `source/id-ID`, with output directed to `build/habring-unit-03-id`. The exact historical shell command was not captured as a standalone receipt; `pass4.console.txt` and the final `.log` are retained. Reproduction must use the listed input hashes and the same toolchain/options: `-interaction=nonstopmode -halt-on-error -file-line-error`.

## Final artifact

- Build PDF: `build/habring-unit-03-id/D90-HAB-03-subgradien-id.pdf`.
- Publication copy: `output/pdf/D90-HAB-03-subgradien-id.pdf`.
- Both: 516,084 bytes; 15 A4 pages; SHA-256 `45f7bc24ff46079881e42be9aa6f1b508c324a208f2b4dd82e35e7e3a6d544b4`.
- Final log: 101,648 bytes; SHA-256 `217291b4c0d275977674b03a5e1dc05bc293503c7583e9ef41a1a2cbca80a6ad`.
- Final text extraction: 25,751 bytes; SHA-256 `531760f570f311256d5b141bd5f28e5495469d9bdf0f2f0c70ce5260a400d2eb`.
- Two consecutive final builds were byte-identical.

## Structural and mathematical QA

`python qa/audit_subgradient_unit.py` passes:

- authority and target hashes exact;
- 61/61 ordered environments preserved;
- 11/11 stable segment markers present and ordered;
- source labels retained, with one declared target chapter label;
- two expected figure paths retained;
- 230 source and 252 target formula surfaces aligned into 46 explicit delta blocks;
- every non-editorial delta is ledger-bound;
- formula-delta manifest SHA-256 `c979be4ecb19687c87ef590feda4d5ba8f083a945a0e0cda98236d8d7581b681`.

An independent final rereview of target SHA-256 `d04ff828…` found P1=0, P2=0, P3=0. It separately confirmed the standing-space conventions, proof-exposition delta, finite-dimensional qualifications, supporting-hyperplane repair, and all referenced adverse-ledger IDs.

## Computation QA

`python qa/validate_subgradient_unit.py` passes with Python 3.13.9, NumPy 2.4.4, and SciPy 1.17.1:

- HiGHS solves the epigraph LP for `min |x-1|` at `x=1`, objective 0;
- SLSQP verifies the composite two-variable `l1` example at approximately `(1.5, 0.375)`;
- the explicit subgradient optimality residual is `6.50e-8` in infinity norm.

Result: `qa/SUBGRADIENT_SOLVER_RESULTS.json` — 980 bytes — SHA-256 `65dde2a94aeb55e71667146509f4b5302e947d2e79af2da8339dd6049974cc52`.

## Visual, text, and accessibility QA

All 15 physical pages were rendered and inspected in three contact sheets. The two mathematical figures and the reader-facing corrections appendix were also checked at higher resolution. No clipping, overlap, blank page, broken glyph, or unreadable formula was found. The extracted text has no active English prose residue under the bounded reader scan.

The PDF is unencrypted, searchable, and declares `/Lang` as `id-ID`. Both figures have Indonesian descriptions in the editable source. The PDF is not tagged; no semantic HTML/EPUB surface is claimed at this boundary.

## Nonblocking toolchain warnings

The final log contains only inherited/template/toolchain warnings: obsolete `xcolor` `hyperref` option; KOMA-Script with `tocloft`; unavailable Indonesian modules for `glossaries`, `tracklang`/`datatool`, and `biblatex`. It contains no overfull or underfull box, unresolved reference, undefined control sequence, or LaTeX error.

---

# Habring Chapter 4 build and QA record

As of: 2026-08-21  
Unit: Habring Chapter 4 — Projected subgradient descent / Metode subgradien terproyeksi  
Admission: PASS

## Build inputs

- Wrapper: `source/id-ID/D90-HAB-04-metode-subgradien-terproyeksi-id.tex` — 4,297 bytes — SHA-256 `4efde33cf820393e001153370cdf52f96bd8b22d24582ca17063cc87e492d249`.
- Translated chapter: `source/id-ID/habring-04-metode-subgradien-terproyeksi-id.tex` — 16,612 bytes — SHA-256 `29fdc330007009bd765a17ca1dcd0cf130ff802312ebb402bf03413da5f96a7d`.
- Authority chapter: `authority/habring/source-v1/projected_subgradient_method.tex` — 14,391 bytes — SHA-256 `44ac28a0f0b67fed4855f7ed91089fab52f77804115f2a06201bff98437bd8da`.
- The wrapper uses the frozen authority bibliography `authority/habring/source-v1/references.bib` directly.

The retained build used pdfTeX 1.40.29 / MiKTeX 26.5 with `latexmk` 4.88 and Biber, from `source/id-ID`, with `SOURCE_DATE_EPOCH=1786643315`, `TZ=UTC`, and output directed to `build/habring-unit-04-id`.

## Final artifact

- Build PDF: `build/habring-unit-04-id/D90-HAB-04-metode-subgradien-terproyeksi-id.pdf`.
- Publication copy: `output/pdf/D90-HAB-04-metode-subgradien-terproyeksi-id.pdf`.
- Both: 370,824 bytes; 13 A4 pages; SHA-256 `5c9991af837995b2e24f4a9060eb3b0efe7b2d71a9bbde01948eeb81ebfd63b7`.
- Final log: 101,402 bytes; SHA-256 `1e389bcb5d005b5b65772e7383766cfe3317293cd7da48491ea65ce38e3db87d`.
- Final text extraction: 27,027 bytes; SHA-256 `1b835413d44817328ca9945962963ae4bdeadec0d5fa3eba0dfb88b5005253e7`.
- A forced full rebuild reproduced the PDF byte-for-byte.

## Structural and mathematical QA

`python qa/audit_projected_subgradient_unit.py` passes:

- authority and target hashes exact;
- all 67 ordered environments and four authority labels preserved;
- eight stable translation segments present and ordered;
- three footnotes, the Beck citation, both informal exercise prompts, and the no-figure closure retained;
- 140 authority and 169 target formula surfaces aligned into 40 explicit delta blocks;
- every substantive delta is bound to O015-HAB-ADV-0019 through O015-HAB-ADV-0027;
- formula-delta manifest SHA-256 `d0453330d42781afffe1e1b7ad3d5a663533509f43a754f9958785b9646171b4`.

An independent final rereview of target SHA-256 `29fdc330…` found P1=0, P2=0, P3=0. It separately confirmed the Hilbert-space projection proof, projection characterization and nonexpansiveness, the fundamental inequality, Polyak and general step rules, the corrected strongly convex constants and induction, both exercises, and the transparency of all nine ledger entries.

## Computation QA

`python qa/validate_projected_subgradient_unit.py` passes with Python 3.13.9, NumPy 2.4.4, and SciPy 1.17.1:

- 512 deterministic projection samples satisfy the variational inequality and nonexpansiveness with maximum residual 0;
- a constrained nonsmooth example validates the fundamental inequality, Polyak and general schedules, and the nonzero-subgradient-at-constrained-optimum counterexample;
- an SLSQP epigraph solve validates the strongly convex value and distance rates with maximum residual 0.

Result: `qa/PROJECTED_SUBGRADIENT_SOLVER_RESULTS.json` — 1,773 bytes — SHA-256 `67719078430b0e3fbfabca3dbfac3d08fed6594659c5d0b2ae69cfd2a1cbb04a`.

## Visual, text, and accessibility QA

All 13 physical pages were rendered and inspected in a contact sheet; the chapter opening, Polyak proof/rate, and correction appendix were also inspected at full size. No clipping, overlap, blank page, broken glyph, or unreadable formula was found. The bounded English-residue scan found only cited English source titles.

The PDF is unencrypted, searchable, and declares `/Lang` as `id-ID`. It is not tagged; no semantic HTML/EPUB surface is claimed at this boundary.

## Nonblocking toolchain warnings

The final log contains only inherited/template/toolchain warnings: the locale fallback, obsolete `xcolor` `hyperref` option, KOMA-Script with `tocloft`, and unavailable Indonesian localization for `biblatex`. It contains no overfull or underfull box, unresolved reference, undefined control sequence, or LaTeX error.

## Two-unit backend verification

`python qa/validate_backend.py` passes with zero errors after deterministic generation/validation. The backend contains 238 records and 19 stable translation segments. After the final component-rights refresh, `backend/records.jsonl` is 161,956 bytes with SHA-256 `cfc027adbb6104adf9290222d5e37403eefcd6d3af9abe7acc765a52daabfca0`; its lossless `backend/records.csv` projection is 195,684 bytes with SHA-256 `9bc78b5f038bb784d92a04b1682781b3f00edcccd6008f0c0a789ca35ae36916`. Chapter 3 and Chapter 4 both record passed independent mathematical rereviews; independent Indonesian language review remains `not_recorded`, and PDF accessibility remains `pass_with_limitation` because the PDFs are untagged.
