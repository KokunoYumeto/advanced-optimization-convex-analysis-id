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

---

# Habring Chapter 6 build and QA record

As of: 2026-08-22  
Unit: Habring Chapter 6 — Acceleration / Akselerasi  
Admission: PASS

## Build inputs

- Wrapper: `source/id-ID/D90-HAB-06-akselerasi-id.tex` — 5,491 bytes — SHA-256 `46903dd6b6ff8c845624931d37d9b24fd37cd89f0bf77601ba11539c59dfd5b9`.
- Translated chapter: `source/id-ID/habring-06-akselerasi-id.tex` — 24,690 bytes — SHA-256 `b1e27d912bc94722ec1c33257598c074eec8a6f5bf81f43b8946f85b48f4c35a`.
- Authority chapter: `authority/habring/source-v1/acceleration.tex` — 18,873 bytes — SHA-256 `2ff1e10e9421c0fe01a09140e3e230cb2d3728c30c572bb6ca5513b229f1e605`.

The retained build used pdfTeX 1.40.29 / MiKTeX 26.5 with `latexmk` 4.88 and Biber, from `source/id-ID`, with `SOURCE_DATE_EPOCH=1783900800`, `FORCE_SOURCE_DATE=1`, `TZ=UTC`, and output directed to `build/habring-unit-06-id`. The wrapper locally disables microtype expansion, loads the Libertine/newtx font maps, and localizes equation cross-references as Indonesian `persamaan`; shared Chapter 3–5 inputs were not changed.

## Final artifact

- Build and publication PDF: `output/pdf/D90-HAB-06-akselerasi-id.pdf` — 392,662 bytes; 15 A4 pages; SHA-256 `cb9edf46d8d2582591ad3114f9a2b316073825dfd48079d12560793ad4bca0a0`.
- Final log: `build/habring-unit-06-id/D90-HAB-06-akselerasi-id.log` — 97,942 bytes; SHA-256 `0775c19ecd2e8356e7b33bd50c30871f233e0c7d05dd703ba2ec19a4f7f560f0`.
- Final text extraction: `qa/D90-HAB-06-akselerasi-id.txt` — 37,033 bytes; SHA-256 `d2679e94ce7e44cdcf183b17e73295b5b5093a1612b2460c0c6ecba512431cda`.
- Two forced fixed-epoch final builds reproduced the PDF byte-for-byte.

## Structural and mathematical QA

`python qa/audit_acceleration_unit.py` passes. The audit script is 17,917 bytes with SHA-256 `f97926aecce6f63a1dcc7733785e0f283e064888ed68d6642d676dcdac3fc8c4`; its 37,873-byte report has SHA-256 `e82f254fb7e69d498162ffcdfb70fe7d4929556351f892872bb8e65da3715b4b`.

- all 99 ordered environments and all seven labels match the authority exactly;
- all twelve stable segment markers occur in order;
- the exact internal-reference surface is restored: four `cref` and four `eqref` invocations in authority order;
- the source and target both contain no citation, figure, asset, footnote, or included-file surface;
- the source editorial verification request is exposed as one rendered self-study verification prompt;
- 166 authority and 241 target formula surfaces align into 32 explicit delta blocks, with manifest SHA-256 `886d80e0a759977c0c176d9b97e595b4c3515ecd52446a8c8b714146a9be3f4a`;
- all 47 required correction surfaces are present and bound to exact ledger events O015-HAB-ADV-0039 through O015-HAB-ADV-0049.

An independent complete review of the pre-fix target identified two P2 and one P3 findings. The frozen post-fix delta review of target SHA-256 `b1e27d912…` passes with P1=0, P2=0, P3=0. It confirms the lower-bound quantifier order and hypotheses, the complete scaled Schur–Jury minimax proof including the equal-curvature case, and the exact reference/topology closure. It separately confirmed the Gelfand/Jordan proof, spectral corollary, local heavy-ball analysis, and FISTA energy/rate argument.

## Computation QA

`python qa/validate_acceleration_unit.py` passes with Python 3.13.9, NumPy 2.4.4, and SciPy 1.17.1. The 33,735-byte validator has SHA-256 `12aa1feacc6230131ce9b82a769177449a8af7ed586ccbf56f0b7ce`; its 37,060-byte result has SHA-256 `135ded1ed0f4f3ca70616822d8856a85d3747458c9ca6e765dab72a11d3b88f0`.

- Gelfand witnesses cover defective Jordan, nonnormal diagonalizable, complex-pair, and nilpotent matrices; the nilpotent case reaches exact zero at power four without dividing by a zero spectral radius.
- Heavy-ball witnesses cover a general admissible case, the `beta=0` zero-root edge, and the minimax parameters. The optimal modal radius is `2/3`, with maximum modulus error `1.11e-16`.
- FISTA passes 518 deterministic fundamental-inequality checks with maximum violation zero. The Lyapunov-energy drift is `4.62e-11`, below the `2e-9` tolerance, and both corrected explicit rate bounds have zero violation.
- At 40 equal gradient/prox evaluations, the FISTA objective gap is `3.0715e-05`, versus `1.4867e-04` for proximal gradient. These are deterministic witnesses, not replacements for the analytic proofs.

## Visual, text, and accessibility QA

All 15 pages of the final post-localization PDF were rendered at 120 dpi and inspected in a five-row contact sheet; formula-heavy pages and the corrections appendix were inspected full size. No clipping, collision, blank page, broken glyph, or unreadable formula was found. A bounded English-residue scan is empty after localizing `Eq.` to `persamaan`.

The PDF is unencrypted, searchable, and declares `/Lang` as `id-ID`; all fonts are embedded and expose Unicode mappings. It is not tagged, so accessibility remains `pass_with_limitation`; independent Indonesian language review remains `not_recorded`.

The final log has no LaTeX error, undefined control sequence, unresolved reference or citation, or missing glyph. It retains two small mathematical overfull warnings (7.08 pt and 3.00 pt); both displays were inspected at full size and remain visibly within the page without clipping. Other warnings are inherited locale/class/toolchain fallbacks.

## Four-unit backend verification

`python qa/extend_backend_ch06.py` followed by `python qa/validate_backend.py` passes with zero errors across two final generation/validation cycles; the JSONL and CSV exports are byte-identical between cycles. The 40,091-byte Chapter 6 generator has SHA-256 `286a4fabd006e748c9681533338c172096c0f42252bb87836a2bf3b1cd77d6a7`; the 25,048-byte validator has SHA-256 `20c45a79ca698a45d640719da547fd27c045055665d4f4315f7e094e7e3574b5`.

The backend contains 449 records, adding 112 Chapter 6 records to the 337-record baseline. Its 39 stable translation segments are distributed 11/8/8/12 across Chapters 3/4/5/6. Entity counts are: 52 artifacts, 4 assets, 55 concepts, 49 corrections, 1 course, 2 editions, 19 learning surfaces, 1 program, 36 QA events, 126 relations, 1 resource, 16 rights records, 39 segments, 43 terms, and 5 units. All 337 pre-Chapter-6 records match a freshly regenerated Chapter 5 baseline except legitimate current control/artifact byte and hash refreshes. Independent Indonesian language review remains `not_recorded`; PDF accessibility remains `pass_with_limitation` for all admitted untagged readers. Final JSONL/CSV byte identities are refreshed once more after the control updates in this paragraph and are taken from the terminal validator output to avoid a self-referential prose hash loop.
