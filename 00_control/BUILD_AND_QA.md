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

---

# Habring Chapter 5 build and QA record

As of: 2026-08-22  
Unit: Habring Chapter 5 — Proximal Gradient Methods / Metode Gradien Proksimal  
Admission: PASS

## Build inputs

- Wrapper: `source/id-ID/D90-HAB-05-metode-gradien-proksimal-id.tex` — 4,817 bytes — SHA-256 `8c67641de7ebf2e06afefa2309c09823e78a4d3d5dbba89a28536392d82c359d`.
- Translated chapter: `source/id-ID/habring-05-metode-gradien-proksimal-id.tex` — 20,575 bytes — SHA-256 `1292f09d375ff0e0ff12e7c87e673596400bb94f228db70d49f9a517b1678691`.
- Authority chapter: `authority/habring/source-v1/proximal_gradient.tex` — 18,464 bytes — SHA-256 `59d5694742f0e2f9f46da0c1418b5fe0ff18521c49078ed29c843b6e8c701f6e`.
- The wrapper uses the frozen authority bibliography `authority/habring/source-v1/references.bib` directly.

The retained build used pdfTeX 1.40.29 / MiKTeX 26.5 with `latexmk` 4.88 and Biber, from `source/id-ID`, with `SOURCE_DATE_EPOCH=1786665600`, `TZ=UTC`, and output directed to `build/habring-unit-05-id`.

## Final artifact

- Build PDF: `build/habring-unit-05-id/D90-HAB-05-metode-gradien-proksimal-id.pdf`.
- Publication copy: `output/pdf/D90-HAB-05-metode-gradien-proksimal-id.pdf`.
- Both: 473,685 bytes; 15 A4 pages; SHA-256 `6f8aa99f6d0395f3c732ed64d2b5cadd5d95ff2195e2504e959d31a3c010731d`.
- Final log: 99,841 bytes; SHA-256 `462372113f47285d8a7940c1d31c779b673c8ae1da85401840310cab9acd8deb`.
- Final text extraction: 33,973 bytes; SHA-256 `a2fdf8d859cd6767f951dfa4a17c8b89c470d98b13d24e01ce1783191e2313f8`.
- A forced full rebuild reproduced the PDF byte-for-byte.

## Structural and mathematical QA

`python qa/audit_proximal_gradient_unit.py` passes:

- authority and target hashes exact;
- all 78 ordered environments preserved;
- eight stable translation segments present and ordered;
- nine label occurrences retained in source order, with the duplicated second authority label transparently remapped to `proximal:eq:moreau_diff2_bound`;
- the Beck citation, all three informal learner prompts or their completed dispositions, the one unnumbered display, and the no-figure/no-footnote/no-input closure retained;
- 162 authority and 188 target formula surfaces aligned into 38 explicit delta blocks;
- every substantive delta is bound to O015-HAB-ADV-0028 through O015-HAB-ADV-0038;
- formula-delta manifest SHA-256 `3b910b86e304b2ba472df7fbf642db5928824ee999b551cc60f287b2c5705a3c`.

An independent rereview of the complete target and a final byte-delta rereview of target SHA-256 `1292f09d…` found P1=0, P2=0, P3=0. It confirmed the proximal existence/uniqueness and fixed-point arguments, Moreau definition and smoothing proof, completed projection/soft-threshold/Euclidean-shrinkage example, all six prox rules, the smooth descent lemma, and the corrected step conditions, polarization, indexing, rate, and full-sequence convergence theorem.

## Computation QA

`python qa/validate_proximal_gradient_unit.py` passes with Python 3.13.9, NumPy 2.4.4, and SciPy 1.17.1:

- box projection agrees with independent SLSQP to `2.23e-14` in infinity norm;
- coordinate soft threshold agrees with an SLSQP epigraph solve to `2.67e-7`, and Euclidean shrinkage agrees with an independent radial solve to `4.68e-9`;
- the Moreau-envelope gradient formula agrees with centered finite differences to `4.68e-10`;
- a quadratic-plus-`l1` forward–backward run uses the exact spectral constant `L=4.6167578080095515` and `tau L=0.95`; descent, telescoping, monotonicity, and corrected `O(1/n)` value bounds have no positive violation beyond floating-point noise;
- the independently solved optimum has gradient-mapping norm `9.79e-8`.

Result: `qa/PROXIMAL_GRADIENT_SOLVER_RESULTS.json` — 5,769 bytes — SHA-256 `de96482c608bbca67fc0a14eeb32a4e69890a97b8f6834a389ea198d2b440a54`.

## Visual, text, and accessibility QA

All 15 physical pages were rendered at 120 dpi and inspected in a contact sheet. The chapter opening, prox formulas/rules, Moreau proof, convergence theorem, two-page correction appendix, and attribution page were also inspected at full size. No clipping, overlap, blank page, broken glyph, or unreadable formula was found. The bounded English-residue scan found only the cited English source title and the explicitly identified source chapter title.

The PDF is unencrypted, searchable, and declares `/Lang` as `id-ID`. It is not tagged; no semantic HTML/EPUB surface is claimed at this boundary. Independent Indonesian language review remains `not_recorded`.

## Nonblocking toolchain warnings

The final log contains only inherited/template/toolchain warnings: locale fallback, obsolete `xcolor` `hyperref` option, KOMA-Script with `tocloft`, and unavailable Indonesian localization for `biblatex`. It contains no overfull or underfull box, unresolved reference or citation, undefined control sequence, or LaTeX error.

## Three-unit backend verification

`python qa/extend_backend_ch05.py` followed by `python qa/validate_backend.py` passes with zero errors. The backend contains 337 records and 27 stable translation segments: Chapter 3 has 11, Chapter 4 has 8, and Chapter 5 has 8. The Chapter 5 extension adds 99 records across the unit, segments, concepts, terms, source learning surfaces, corrections, QA, artifacts, rights, and relations. Two generation/validation cycles were byte-identical, and a separate baseline reconstruction proved the 238 pre-Chapter-5 records semantically unchanged except for legitimate artifact byte/hash refreshes. Independent Indonesian language review remains `not_recorded`; PDF accessibility remains `pass_with_limitation` because the reader PDFs are untagged. Final JSONL/CSV hashes are refreshed after the current control records below and must be read from the validator output rather than this prose to avoid a self-referential artifact-hash loop.
