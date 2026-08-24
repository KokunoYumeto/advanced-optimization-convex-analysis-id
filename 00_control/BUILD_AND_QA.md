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

---

# Habring Chapter 7 build and QA record

As of: 2026-08-22  
Unit: Habring Chapter 7 — Duality / Dualitas  
Admission: PASS

## Build inputs

- Wrapper: `source/id-ID/D90-HAB-07-dualitas-id.tex` — 8,615 bytes — SHA-256 `3b6e710e37c07cc9ec82ca919451c313c52fa762d58c7b01c6792a78a0098797`.
- Translated chapter: `source/id-ID/habring-07-dualitas-id.tex` — 35,428 bytes — SHA-256 `11e9ad614f7ac4e3107e78bc3bed03a6d4acfe22f2a65fca26433b0ae3209fd9`.
- Authority chapter: `authority/habring/source-v1/duality.tex` — 30,761 bytes — SHA-256 `0b112dee2582813cec5629c02df1dda329f690f944b60f4694b1c5762129bea9`.
- Integrated correction records: `O015-HAB-ADV-0050` through `O015-HAB-ADV-0075`; the exact 26-record proposal is 15,830 bytes with SHA-256 `57dbba9afdee2fc453dde9fbb97621c1a6897ff5377c1ec6a210827a8dce675d`.

The retained build used pdfTeX 1.40.29 / MiKTeX 26.5 with `latexmk` 4.88 and Biber, from `source/id-ID`, with `SOURCE_DATE_EPOCH=1783900800`, `FORCE_SOURCE_DATE=1`, `TZ=UTC`, and output directed to `build/habring-unit-07-id`.

## Final artifact

- Build and output PDF: `output/pdf/D90-HAB-07-dualitas-id.pdf` — 445,733 bytes; 21 A4 pages; PDF 1.5; SHA-256 `c4354e1e1366bdb20cebb9c6eca26fba172d6d82a6ad22dd9e2e470da2baeb6e`.
- Final log: `build/habring-unit-07-id/D90-HAB-07-dualitas-id.log` — 105,821 bytes — SHA-256 `795b594b1c78e0a0769fe6b7f292fea0d6ddc81a054cad00a4d857da0cab217d`.
- Final text extraction: `qa/D90-HAB-07-dualitas-id.txt` — 53,128 bytes — SHA-256 `b473c80434a35ec607c6a9b9da3dcc31e3d5a3a233ae1f7da72293a87d65a544`.
- Two forced fixed-epoch final builds reproduced the PDF byte-for-byte.

## Structural and mathematical QA

`python qa/audit_duality_unit.py` passes twice deterministically with zero failures on the exact frozen target. The 36,689-byte script has SHA-256 `4e29ad8cc208ab35f35e8dfc2bb323343977e7badcaed7aa7d8cfa75392cf35b`; its 32,121-byte report has SHA-256 `fd909b00e4274a31c9e9c707cbb9039d5e03233876d0c0094c66c1049802307f`.

- all 148 ordered source environments are preserved;
- all eleven stable segment markers occur in source order;
- all 24 label occurrences are retained, with only the duplicated final source label remapped uniquely and its reference changed in lockstep;
- all 21 `eqref`, 3 `cref`, 1 `Cref`, 9 `ref`, 2 citations, 1 footnote, 9 items, and 5 learner prompts are preserved;
- the source and target have no figure, asset, or included-file surface;
- 254 source and 296 target formula surfaces align into 49 explicit delta blocks, with every one of the 43 substantive blocks bound to an integrated correction event;
- the 81,046-byte formula-delta manifest has SHA-256 `fe72e72d0223117a0b34727d235ced9b6bf2af17cf48154e6b670d2ce75d89fb`.

Independent full-target and final-delta rereviews pass with P1=0, P2=0, P3=0. They confirm the finite-dimensional Hilbert/Riesz convention, conjugacy and biconjugacy repairs, Fenchel--Rockafellar scope, Moreau scaling, primal--dual gap, PDHG update/ergodic proof, and ADMM typing, stationarity, residual, Lyapunov, and objective arguments.

## Computation QA

`python qa/validate_duality_unit.py` passes twice with byte-identical stdout and no stderr. The 45,213-byte validator has SHA-256 `127bed94abe4b506ebd999a46ea71b31457f2f4cc65c7fdd7cd4efcc60569c5b`; its exact 10,830-byte receipt has SHA-256 `9ceeadd90b4868f600241301813a8f24c1d1279690abc8cbf96baa3faf62f3c3`.

The suite checks Fenchel/subdifferential and scaled-Moreau identities; an independent SciPy Fenchel--Rockafellar witness; PDHG one-step inequalities, convergence, metric coefficients, averaging indices, and the zero-operator branch; and ADMM primal/dual residuals, Lyapunov descent, and objective convergence with negative controls. These deterministic witnesses support, but do not replace, the included analytic review.

## Visual, text, and accessibility QA

All 21 pages of the exact final PDF were rendered at 120 dpi and inspected in three contact sheets. Formula-heavy primal--dual/ADMM pages, the correction appendix, and the one repaired proof-heading/list transition were inspected at full size. No clipping, collision, blank page, broken glyph, or unreadable formula was found. The bounded English-residue scan is empty.

The PDF is unencrypted, searchable on every page, and declares `/Lang` as `id-ID`; every embedded font exposes a Unicode mapping. It is not tagged, so accessibility remains `pass_with_limitation`; independent Indonesian language review remains `not_recorded`.

## Toolchain and backend verification

The final log has no LaTeX error, undefined control sequence, unresolved reference or citation, missing glyph, overfull/underfull box, or rerun request. Remaining notices are inherited locale/class/toolchain fallbacks.

`python qa/extend_backend_ch07.py` followed by `python qa/validate_backend.py` passes across two deterministic generation/validation cycles. The five-unit backend has 50 stable translation segments distributed 11/8/8/12/11 across Chapters 3/4/5/6/7. Its exact current record count and JSONL/CSV byte identities are taken from the terminal validator output after all control-file updates, avoiding a self-referential artifact-hash loop. Pre-Chapter-7 semantic records remain unchanged except legitimate current artifact/control hash refreshes.

---

# Habring Chapter 8 build and QA record

As of: 2026-08-22  
Unit: Habring Chapter 8 — Stochastic Gradient Descent / Penurunan Gradien Stokastik  
Admission: PASS

## Build inputs and artifact

- Authority: `authority/habring/source-v1/stochastic.tex` — 4,665 bytes — SHA-256 `610d11b59d8dfabbbbe6fbc509a0f9ac1727540458c67f8cd3b7bab49566a07d`.
- Target: `source/id-ID/habring-08-penurunan-gradien-stokastik-id.tex` — 6,378 bytes — SHA-256 `f610aaec91aa9b76582f251458da65d25cc37a933a51da478cad13ee16e5a344`.
- Wrapper: `source/id-ID/D90-HAB-08-penurunan-gradien-stokastik-id.tex` — 5,129 bytes — SHA-256 `d00ea41830af388c227a1054025f049a9315da6f41675573965042d320eb7428`.
- Integrated corrections: `O015-HAB-ADV-0076` through `O015-HAB-ADV-0083`; exact eight-record proposal SHA-256 `a815d0211da31b21a25a3f9fd8a2c1ec5fcc7da5e7a62c980f75df40ae65d45d`.
- Build/output PDF: `output/pdf/D90-HAB-08-penurunan-gradien-stokastik-id.pdf` — 346,785 bytes; 8 A4 pages; SHA-256 `c1ed028667c5df3fd0a837807e2a17bf7a9e1fa3170938853c9a96b9670fa86a`.
- Final log: 98,530 bytes; SHA-256 `59609048d4930761a5de52f05aa65f80cf3da36dc7f64bd624c1ec539e64702c`.
- Final text extraction: `qa/D90-HAB-08-penurunan-gradien-stokastik-id.txt` — 13,751 bytes; SHA-256 `8556e8138248e163bff23d1778e1d2d782d7c0b3bfa6c1c4df5adaed439a05c6`.

Two full builds from `source/id-ID` with `SOURCE_DATE_EPOCH=1783900800`, `FORCE_SOURCE_DATE=1`, `TZ=UTC`, `latexmk`/pdfTeX, and Biber produced identical PDF bytes.

## Structural, mathematical, and computation QA

`python qa/audit_stochastic_unit.py` passes twice byte-identically with P1=0, P2=0, P3=0. The 29,112-byte script has SHA-256 `d6a201efc1489fd8220510408bb65cf3cb56d5603b130f46287c6ec8f5be905e`; its 12,202-byte report has SHA-256 `d44495208072e4555011dce4cf6155d434bc526574614d2683b8a97484f730dc`.

- all 24 ordered environments and all nonblank source lines are covered by three stable segments;
- the sole label/reference pair and no-citation/no-figure/no-footnote/no-exercise closure are exact;
- 38 source and 61 target formula surfaces align into seven substantive delta blocks, every one bound to the eight integrated correction events;
- the 24,702-byte formula-delta manifest has SHA-256 `2f9632d02071ded0c84d54ca17af019137cecfe18245d94a7e9243449c0e9fe9`.

The independent source/target review found no remaining target defect. It confirms the normalized finite-sum oracle, well-posed projected iteration, conditional filtration/oracle assumptions, exact second-moment identity, consistent best-iterate definition, restored factor, and sharp `S_K`/`Q_K` bound.

`python qa/validate_stochastic_unit.py` passes 24/24 gates twice with byte-identical output. The 18,417-byte validator has SHA-256 `ef05e828b83ab285e5ba090dc27753cd758d5c3e1697f9c138b57bf052a7006e`; its 21,107-byte receipt has SHA-256 `3b78aa1140a08cf811493f37496b10c2955f02bec570385dcde6480f37578f22`.

It verifies the normalized finite-sum mean and missing-`N` negative control; three exact conditional-oracle states and their variance decomposition; metric projection and the one-step recurrence; ten exact-enumeration best-iterate cases under two schedules; and the source's failing extra-`Q_K` asymptotics. The minimum theorem-bound margin is `1/8`. For `tau_k=(k+1)^(-1/5)` at `K=100000`, the correct `Q_K/S_K` term is approximately `0.1332502401`, while the erroneous `Q_K^2/S_K` term is approximately `221.9331877`.

## Visual, text, accessibility, and backend QA

All eight exact final pages were rendered and inspected in a contact sheet; theorem/proof and correction pages were inspected at full size. No clipping, collision, broken glyph, blank content page, or unreadable formula was found. The bounded English-residue scan is empty. The log has no TeX error, unresolved reference, missing glyph, box warning, or rerun request.

The PDF is unencrypted and searchable on every page, declares `/Lang` `id-ID`, and embeds all fonts with Unicode mappings. It remains untagged, so accessibility is `pass_with_limitation`; independent Indonesian language review remains `not_recorded`.

`python qa/extend_backend_ch08.py` followed by `python qa/validate_backend.py` passes across two deterministic generation/validation cycles. The six-unit backend has 53 stable translation segments distributed 11/8/8/12/11/3 across Chapters 3/4/5/6/7/8. Its exact current record count and JSONL/CSV byte identities are taken from the final validator output after all control updates, avoiding a self-referential artifact-hash loop. Pre-Chapter-8 semantic records remain unchanged except legitimate current artifact/control hash refreshes.

---

# Habring Chapter 9 build and QA record

As of: 2026-08-22  
Unit: Habring Chapter 9 — Excursion on Optimal Transport / Selingan tentang Transportasi Optimal  
Admission: PASS

## Build inputs and artifact

- Authority: `authority/habring/source-v1/optimal_transport.tex` — 15,378 bytes / 264 lines — SHA-256 `719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba`.
- Target: `source/id-ID/habring-09-transportasi-optimal-id.tex` — 21,252 bytes / 352 lines — SHA-256 `45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd`.
- Wrapper: `source/id-ID/D90-HAB-09-transportasi-optimal-id.tex` — 6,822 bytes / 87 lines — SHA-256 `1e308a2bed0d1a6f5cdcff09cce932674cf32842a135bc88a5a34bc96c483ff6`.
- Corrected unit-local bibliography: `source/id-ID/references-ot-id.bib` — 306 bytes / 9 lines — SHA-256 `93611c4b6a753478c51c601e59ef6cd3e290677e2e2d25b104d5d3b74df03126`.
- Integrated corrections: `O015-HAB-ADV-0084` through `O015-HAB-ADV-0096`; proposed content ledger SHA-256 `643fde3fbe1409732ef2df8fdef52465e4df7a583fd9bbeb2137a6122f548add`.
- Build/output PDF: `output/pdf/D90-HAB-09-transportasi-optimal-id.pdf` — 498,244 bytes / 15 A4 pages — SHA-256 `edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214`.
- Final log: 103,255 bytes — SHA-256 `2b083221c49f6fbdede8f541e68cd9129632a74168d7855c1ddc14c1bf48b3a4`.
- Final text extraction: 30,053 bytes — SHA-256 `283864c3fc84d414ff721f128a0f10e4b61b4646c0f5edcd53551ee13f911859`.

Two fixed-epoch builds from `source/id-ID`, with `SOURCE_DATE_EPOCH=1783900800`, `FORCE_SOURCE_DATE=1`, `TZ=UTC`, and `latexmk -gg -pdf`, produced byte-identical PDF files.

## Admission result

The strict audit passes twice: all 47 ordered environments, five labels, native TikZ figure, citation/footnote/glossary surfaces, and every nonblank authority line are preserved in nine stable segments. Its report SHA-256 is `eb8b194c01dd7610dcdb7325322765ab16b3ec9cf907d28f9463fa11692767aa`; the 35-block / 34-substantive formula manifest SHA-256 is `796e13fbf1f221139f0233d30b2464dfb026027eb5b9ce44b66b58c2f2e169ef`. All substantive deltas bind to exact integrated corrections.

The open validator passes 41/41 gates twice. It checks a rectangular 3-by-4 OT primal/dual witness with objective 0.575 and zero gap, Wasserstein-2 squared distance 3, a positive entropic Sinkhorn plan in 27 iterations with maximum marginal residual `3.608224830031759e-15`, factorization/KKT/scaling/strict-convexity witnesses, and four negative controls. Receipt SHA-256: `4f751c615f2d7f03622b1447b3985ad1d660bd4f758cf4c4fb61d4d384b4e7a0`.

All 15 pages were rendered and inspected; formula-heavy pages and the correction appendix were inspected full size. No clipping, collision, blank content page, broken glyph, or unreadable formula remains. The final independent rereview is P1=0, P2=0, P3=0. The PDF is searchable, declares `/Lang` `id-ID`, embeds all fonts with Unicode mappings, and remains untagged. Semantic HTML/EPUB and independent human Indonesian review remain open. Full evidence is in `CHAPTER09_SOURCE_AUDIT.md` (SHA-256 `49f3d61892cf7587281fa3a95525b7f7ae1814223c38fe3de76efc02a193a85b`) and `qa/CHAPTER09_WORKLOG.md` (SHA-256 `0527b8b61dee2ffccd493e8331b7d57f592ba3ec9b5ef87226c15cb1a342e99e`).

`python qa/extend_backend_ch09.py` followed by `python qa/validate_backend.py` passes across two deterministic generation/validation cycles. The seven-unit backend contains 793 records and 62 stable translation segments distributed 11/8/8/12/11/3/9 across Chapters 3/4/5/6/7/8/9; final export identities are emitted by the validator after live control updates.

---

# Penn Chapter 3 build and QA record

As of: 2026-08-22  
Unit: Penn Chapter 3 — Introduction to Gradient Ascent and Line Search Methods / Pengantar Pendakian Gradien dan Metode Pencarian Garis  
Admission: PASS

## Build inputs and artifact

- Authority: `authority/penn-state/source/ClassNotes/Section3.tex` — 41,715 bytes / 608 lines — SHA-256 `d4ae6142e2366b12575eafddc833df067518af114e9816187668cc367be43010`.
- Target: `source/id-ID/penn-03-pendakian-gradien-dan-pencarian-garis-id.tex` — 44,364 bytes / 646 lines — SHA-256 `7c75d0ae56a5a912d561d91ece607f088a4ff4f3de4dbc3396ce40d6d7d6a229`.
- Wrapper: `source/id-ID/D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.tex` — 8,203 bytes / 192 lines — SHA-256 `0876d121d417ef4f73f308eac62056a55499628af44713e06246315852dcfa38`.
- Bundled-bibliography excerpt: `source/id-ID/references-penn-ch03-id.bbl` — 852 bytes / 25 lines — SHA-256 `d3e645c03298c14fee272d44b5d471a81d31aec60a95d4f568b4923edde63867`.
- Integrated corrections: `O015-PENN-ADV-0004` through `O015-PENN-ADV-0024`; proposal SHA-256 `80aa5a3f7b4f46c7dfe01f58f6f68555c9aeaeb91d0877eaf27cbb447c4a67fa`.
- Build/output PDF: `output/pdf/D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.pdf` — 515,851 bytes / 20 A4 pages — SHA-256 `e1be82d06572c51b403608cd9595cc5adf2dc64cfa93f53001eba94e48f77e3e`.
- Final log: 27,077 bytes / 697 lines — SHA-256 `2702aa4b756fec32557368a144ddfe9a91f32363e034cefea9956034178a74f6`.
- Final text extraction: 47,464 bytes / 828 lines — SHA-256 `9880848f06e2f1104a88213f3a9f7629db87c6cc8bf0b515281cf553ed1895bc`.

Two complete builds from `source/id-ID`, with `SOURCE_DATE_EPOCH=1783900800`, `FORCE_SOURCE_DATE=1`, `TZ=UTC`, and `latexmk -gg -pdf`, produced byte-identical PDF files. The final log has no TeX error, undefined control sequence, unresolved reference/citation, missing glyph, overfull/underfull box, or rerun request. The only retained log notice is an OT1 bold-small-caps font substitution; direct inclusion of the frozen bibliography excerpt produces an expected terminal-only latexmk notice.

## Structural, mathematical, and computation QA

`python qa/audit_penn_ch03_unit.py` passes twice byte-identically. All 142 ordered environments, 35 labels, 37 unique reference targets, nine citations, four figure calls, twelve exercises, and all 608 authority lines in eight segments close exactly. The 499 source and 570 target math records align into 230 canonical-equal pairs and 89 delta blocks, with zero unbound blocks and zero unknown correction bindings. The report SHA-256 is `97af8d897decb2aac58355d97cf65898c1396e18c08deca5e1e8834a6b49d588`; the formula-manifest SHA-256 is `af04268dddc2cc3b74ccfe775967673bcfebab911d5d298c61df2a5a68ff653c`. Independent final rereview is P1=0, P2=0, P3=0.

`python qa/validate_penn_ch03_unit.py` passes 31/31 checks twice, including eleven negative controls. It validates bracketing, dichotomy, golden-section evaluation reuse/contraction/plateau failure, bisection, strong-concavity distance control, quartic extrema, Newton curvature/sign/failure cases, and exact local convergence-rate behavior. Result SHA-256: `dcf133cf7ca8aefebb3193711c8ceb1b719d9756b15778971572f1762e6b0565`.

## Visual, text, and accessibility QA

All 20 final pages were rendered at 120 dpi and inspected in a 4-by-5 contact sheet; the title/about/contents pages, Newton-rate page, bibliography, correction appendix, and attribution page were inspected full size. No blank page, clipping, collision, broken glyph, or unreadable formula remains. The title was reflowed manually to remove the non-content blank verso produced by the default book title machinery.

The PDF is A4/PDF 1.5, unencrypted, searchable on every page, declares `/Lang` `id-ID`, exposes six outlines, and has no form fields, widgets, or JavaScript. It is untagged. Nineteen reader fonts expose Unicode maps; eighteen embedded font resources inside the four inherited vector figures do not. Accessibility therefore passes with an explicit limitation; independent Indonesian language review remains unrecorded.

Full authority, rights, closure, and admission evidence is in `PENN_CH03_SOURCE_AUDIT.md`. Semantic HTML/EPUB, interactive computation, and the independent solution/mastery layer remain open.

`python qa/extend_backend_penn_ch03.py` followed by `python qa/validate_backend_penn_ch03.py` passes across two deterministic generation/validation cycles. The canonical backend now has 973 records and 70 stable translation segments. The Penn extension adds 180 records: 17 artifacts, four assets, 14 concepts, 21 corrections, two editions, 19 learning surfaces, 12 QA events, 59 relations, one resource, seven rights records, eight segments, 14 terms, and two units. JSONL: 718,846 bytes, SHA-256 `77fe247050077fda23c9a0bb2aa9c329f7c72d2e2e5f4b8890956b9df32343ec`; lossless CSV: 860,463 bytes, SHA-256 `5fe10a172f5abd9b847cf99c71620c02c460649d531537dbd61283a2c2d7f0cf`.

The 698-record Habring semantic baseline is unchanged at record-set SHA-256 `41fd7e0f51828f4c70f9f56a8ab424ad1ee944bb3f02ba5a654ff059bbeab878`. Ninety-four immutable baseline artifact records remain unchanged. The sole enumerated baseline refresh is `artifact.o015.adverse-ledger`, updated from the pre-admission 99-record ledger to the live 120-record identity; the refreshed 793-record baseline set has SHA-256 `7588bdc2e110564bd420e5bcf7bd1737b3f91dd50eabfa213eaa12fa757bfe4f`. Validation returns zero errors.

---

# Penn Chapter 4 build and QA record

As of: 2026-08-22  
Unit: Penn Chapter 4 — Approximate Line Search and Convergence of Gradient Ascent / Pencarian Garis Hampiran dan Konvergensi Pendakian Gradien  
Admission: PASS

## Build inputs and artifact

- Authority: `authority/penn-state/source/ClassNotes/Section4.tex` — 34,684 bytes / 469 lines — SHA-256 `76113034709b5914fa920076f2e882ccf30157e78ce5bdf4593a5d39af1886d5`.
- Target: `source/id-ID/penn-04-pencarian-garis-hampiran-dan-konvergensi-id.tex` — 33,313 bytes / 613 lines — SHA-256 `c5c0f09d38454177e61c2a97c9beef07771d5f4f715cc7a4a81a871ff54ced8f`.
- Wrapper: `source/id-ID/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex` — 8,018 bytes / 187 lines — SHA-256 `b40ac7e4e1ee69afd0f7f82dbfc9042c6df79c1aaf2ccca78ec9e639b2030edc`.
- Bundled-bibliography excerpt: `source/id-ID/references-penn-ch04-id.bbl` — 625 bytes / 16 lines — SHA-256 `037e62878f1a562314a33054da8f4df4e49c029bbad31c2ec75066cd3e1a99f3`.
- Integrated corrections: `O015-PENN-ADV-0025` through `O015-PENN-ADV-0037`; proposal SHA-256 `fa9c5c0b097b7349a959ca6c1c9c797fc0ed2ea61e91148badec62bb239b7bbd`.
- Build/output PDF: `output/pdf/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf` — 847,350 bytes / 17 A4 pages — SHA-256 `c0f283aa7d70eba05de6a35c98bc0aa55f3177ab40702bf7eed5de45a7b6ab8a`.
- Final log: 27,564 bytes / 706 lines — SHA-256 `f247633a55e47a6fc002899bc9dbd24128f0949e39cc2954f78164411c301174`.
- Final text extraction: 26,421 bytes / 845 lines — SHA-256 `3ee30d8a4948910d40d8f61bec87a8e36e29f1934c6000dab1d9a8c96f5e518f`.

Two complete builds from `source/id-ID`, with `SOURCE_DATE_EPOCH=1783900800`, `FORCE_SOURCE_DATE=1`, `TZ=UTC`, and `latexmk -gg -pdf`, produced byte-identical PDF files. The final log has no TeX error, undefined control sequence, unresolved reference/citation, missing glyph, overfull/underfull box, or rerun request. The only retained log notice is an OT1 bold-small-caps font substitution; direct inclusion of the frozen bibliography excerpt produces an expected terminal-only latexmk notice.

## Structural, mathematical, and computation QA

`python qa/audit_penn_ch04_candidate.py` passes twice byte-identically. All 112 ordered environments, 32 labels, 66 displayed-formula pairs, 52 source reference calls and complete target closure, four citations, five figure calls, four exercises, and all 469 authority lines in seven segments pass 22 fail-closed gates. Twenty-six determined formula pairs bind to all 13 corrections. The report SHA-256 is `c43e0195fc7da99590efd17b83ace3ca6a5721bc5156e86d2121a877b85e2c0a`; the formula-manifest SHA-256 is `fe7aa0bbd5cab4ff50cdf855a3bcf3c73f6ad0e007e2ce2033369cf54ed4a65e`. Independent final rereview found and fixed one P3 capture-theorem wording defect and finishes with P1=0, P2=0, P3=0.

`python qa/validate_penn_ch04_math.py` passes 12/12 checks twice. It validates ascent-form Wolfe signs and negative controls, finite Armijo backtracking, the failure recurrence, deterministic Kantorovich/exact-ascent witnesses, the corrected quadratic matrix/condition factor, and eventual unit-step/superlinear Newton behavior. Script SHA-256: `6f2ebf4a462043d327b5eb8c7e238808b6098aea2c193eab66cfa43794cd4bc4`; result SHA-256: `44c2b1a2509775e182e38b125f6c25ca49eb2f7e23e68ec2fce6878bf7704dd2`.

## Visual, text, and accessibility QA

All 17 final pages were rendered at 130 dpi and inspected in a four-column contact sheet; title, figure, algorithm, proof, correction, and rights pages were inspected full size. The source's two forced `[p]` algorithm floats initially created an otherwise mostly empty algorithm page; changing only their placement to `[htbp]` reflowed both boxes with their surrounding proof and example. The final reader has no blank page, clipping, collision, broken figure, or unreadable formula. Exact evidence is in `qa/PENN_CH04_VISUAL_QA.json`, SHA-256 `e700d08476f7aaa018ca31687d2eea2e8a50729599f760d300dd5b6f89211e70`.

The PDF is A4/PDF 1.5, unencrypted, searchable on all 17 pages, declares `/Lang` `id-ID`, exposes six outlines, and has no forms or JavaScript. It is untagged. Of 36 font resources, 26 expose Unicode maps and ten inherited vector-figure resources do not. Accessibility therefore passes with an explicit limitation; independent Indonesian language review remains unrecorded.

Full authority, rights, closure, and admission evidence is in `PENN_CH04_SOURCE_AUDIT.md`. Semantic HTML/EPUB, interactive computation, and the independent solution/mastery layer remain open.

## Backend admission

`python qa/extend_backend_penn_ch04.py` followed by `python qa/validate_backend_penn_ch04.py` passes across two byte-identical cycles. The nine-unit backend contains 1,128 records and 77 stable translation segments. Penn Chapter 4 adds 155 records and seven segments; its record-set SHA-256 is `b956955faee9f9f41b1212952d5c76c6d0eea2f30b33e4881198e48e8a409714`. The stabilized 973-record baseline has record-set SHA-256 `a53d556fe87bab226e120d7df3611b15e38cabb3defb19e850d481dd72058f9c`; its 861 semantic records remain `e20bb942a17185bfcabbc0e0377ce3608697530162664ebe06fba4400ec706a9`, and its 109 non-refreshed artifacts remain `0694bc4785d8712429c783002f0940d61c3832c32de8b8fc5fc436c128ca21e1`. Only `artifact.o015.adverse-ledger`, `artifact.o015.component-rights`, and `artifact.o015.coverage-overlap` are authorized live-binding refreshes.

Final JSONL: 829,770 bytes, SHA-256 `d378b1fcaf46fc83076a9961da16ff96d5f50e22912ede054be923a6bd389650`. Final lossless CSV: 994,096 bytes, SHA-256 `b36ecc26c8080786d6f0eacd3d3af7ffb6bbf81151400b561853751b72cc34df`. The 65,190-byte extension script has SHA-256 `f1e8f13c48bf5b76f0eb0212190ebe247a7ab40a11100dade9ba0fcacdc7ae14`; the 34,749-byte validator has SHA-256 `a56508efbd0b84f485b3fecaec77df41fb5410657a2c89bdf1a2676e4e79f15b`. Validation returns `errors=[]`.

---

# Penn Chapter 5 build and QA record

As of: 2026-08-22  
Unit: Penn Chapter 5 — Newton's Method and Corrections / Metode Newton dan Koreksinya  
Admission: PASS; optional Penn/Habring companion boundary frozen after this unit

## Build inputs and artifact

- Authority: `authority/penn-state/source/ClassNotes/Section5.tex` — 22,371 bytes / 317 lines — SHA-256 `15186b99be0913d83046e3e32eaf7a378d3a4fccd222219984b091ddf7f9a428`.
- Target: `source/id-ID/penn-05-metode-newton-dan-koreksi-id.tex` — 27,317 bytes / 400 lines — SHA-256 `0f6afd7da2268661124f967f299ac9df89bb6a8f5683b3e4e8fea32718a8549a`.
- Wrapper: `source/id-ID/D90-PENN-05-metode-newton-dan-koreksi-id.tex` — 7,230 bytes / 175 lines — SHA-256 `82450c4cdbe6de904c7cba1ee22922869f5d2e2caf19be69285092a5ea987e55`.
- Bibliography excerpt: `source/id-ID/references-penn-ch05-id.bbl` — 625 bytes / 16 lines — SHA-256 `037e62878f1a562314a33054da8f4df4e49c029bbad31c2ec75066cd3e1a99f3`.
- Integrated corrections: `O015-PENN-ADV-0038` through `O015-PENN-ADV-0049`; all twelve proposed records are byte-identically appended to the live adverse ledger.
- Final PDF: `output/pdf/D90-PENN-05-metode-newton-dan-koreksi-id.pdf` — 2,691,780 bytes / 15 A4 pages — SHA-256 `427db2c5a4428dfbe222d7e1d4f5c5349d4f78484a8593c412328fe94a7353c6`.
- Canonical log: 27,062 bytes / 700 lines — SHA-256 `bb3e9416233d14400ced235b69eeb95f76e6347dfeabbfd2c06727b543aed8be`.
- Extracted text: 29,195 bytes / 541 lines — SHA-256 `78fc7ecf877b7707c6c33736210449d502bbc148b84994b65b0d2fc4791365d3`.

Two complete fixed-epoch builds produced byte-identical PDFs. The canonical log contains no TeX error, undefined reference or citation, overfull box, missing glyph, or rerun request; one contained underfull caption warning is accepted.

## Structural, mathematical, computation, and rights QA

The final structural audit passes twice and preserves all 84 ordered environments, all ten labels, all five exercises, the sole citation, four figure calls, the exact 35 displayed-formula sequence, the complete reference closure, and every source line in seven gap-free segments. `qa/PENN_CH05_STRUCTURE_REPORT.json` is 26,392 bytes, SHA-256 `89757169df04a17c4e19bb72469aa6cd5ebb094e4c1298e3b8b78b44b3d9146a`.

The independent rereview raised and resolved one P2 and three P3 findings and closes at P1=0, P2=0, P3=0. Its 9,373-byte receipt has SHA-256 `239e4d79f90c570ac95ceb22cab097b41980c308abb39f940fe66dbc5f7861dd`.

The deterministic SymPy 1.13.1 validator passes all seven gates twice. It reconstructs the quartic Newton map, the double-peak stationary set and failed pure-Newton ascent direction, the corrected modified-Cholesky factor and solves, spectral bounds, and a local Q-quadratic witness. `qa/PENN_CH05_SOLVER_RESULTS.json` is 6,242 bytes, SHA-256 `9c5905c0022a1a99f8064484cff40abff0b9435df133822b5e16fc2b0ac6401f`. No excluded Maple code is executed.

The four Penn vector figures are retained byte-exactly. Five Maple/legacy listings remain excluded because their component rights are unclear/external; their reader roles are replaced by three independently authored, separately registered pseudocode surfaces. Penn-derived text/figures remain CC BY-NC-SA 3.0 US; original bridges are separately identified inside the combined NC-SA derivative.

## Visual and accessibility QA

All 15 pages were inspected in a contact sheet; pages 4, 5, 9, 10, 11, 12, and 14 were inspected at full size. No blank content page, clipping, collision, broken figure, unreadable glyph, or stranded algorithm page remains. The exact 2,687-byte visual receipt has SHA-256 `3130aee988a10cf4fc4c2b3cfbdc494293142519c0c416d603a109704188bde4`.

The PDF is A4/PDF 1.5, unencrypted, searchable on all 15 pages, declares `/Lang` `id-ID`, exposes six outlines, has no forms or JavaScript, and all 137 font resources expose Unicode maps. It remains untagged; semantic HTML/EPUB and independent human/native-speaker Indonesian review remain open.

## Backend admission

Root independently reran `python qa/extend_backend_penn_ch05.py` and `python qa/validate_backend_penn_ch05.py` after the producing agent's clean cycles, then repeated the transaction after the authorized architecture/rights/coverage refresh. The terminal two cycles are byte-identical and validation returns `errors=[]`.

The ten-unit companion backend contains 1,283 records and 84 stable segments. Chapter 5 adds 155 records in seven contiguous source/target mappings and has terminal record-set SHA-256 `979ec311c13ac368e7950bb734d4240310dec154d3e8151b042ed82333cb78c8`. The 1,128-record incoming baseline is unchanged after the three enumerated live-control refreshes and has record-set SHA-256 `23ffc42f0fa6b19a828154db74bdda2a0fa99e860f7615c918f4c7a3787f2edb`; its 999 semantic records have SHA-256 `971333c796eeb036b59cc1ff5ce6c0ce5bfa2836e5ab4d7f4176d4aeea0b5d97` and its 126 immutable artifact records have SHA-256 `68c89eb4dd196935f8b60d9f3eccc32a4ae61530503d189bb4ca3903bd9061c0`.

Final JSONL: 942,447 bytes, SHA-256 `e57a457d20edfcf772f38f7dd9dfdd3368530d785bbf5b71179b90784b8130f9`. Final lossless CSV: 1,129,757 bytes, SHA-256 `e2ca8f3b58dc74e208a579ff1b55997d0e5e202f49c2b018edce6358b7492c2f`. The 67,831-byte extension script has SHA-256 `d06a5149cdf6e08588cf20a586b7418e7244c189f2f4e8c06e8082cc75b1f1b9`; the 38,114-byte validator has SHA-256 `f89dfcb19a2febc15d44b75ed9894ed348861632db35b66a371843457e5e0ab6`.

---

# Habring Chapters 3--9 combined reader and resumable-source QA

As of: 2026-08-22  
Artifact: `output/pdf/D90-HAB-03-09-modul-pendamping-id.pdf`  
Disposition: PASS for reader-first public checkpoint; coherent partial companion module, not the complete D90 course

The deterministic builder `qa/build_habring_companion_reader.py` is 9,325 bytes, SHA-256 `288df54ace12fe45b7a3735b54f710878078fdbcbd5a293752520b780dc864de`. It combines a one-page Indonesian scope/rights/accessibility cover with the seven already admitted Habring Chapter 3--9 readers and removes ReportLab's unused default Helvetica selection without removing any painted text. Two final builds are byte-identical.

The combined reader is 3,090,098 bytes / 103 A4 pages, SHA-256 `6cd291cc447999b7cd72622e8c2003b837cf4f21ea5de0fcb7094913e20acd87`. It is unencrypted and searchable on all 103 pages, declares `/Lang id-ID`, exposes eight correct outline destinations, preserves all 127 source link annotations, and has no form or JavaScript. All 121 reachable painted font objects are embedded and expose Unicode maps. The 102 component pages preserve byte-identical decoded content streams and identical extracted text relative to their standalone readers. TeX math extraction retains inherited control/private-use delimiter glyphs; the merge introduced none. The PDF remains untagged and independent human/native-speaker Indonesian review remains unrecorded.

All 103 final pages were rendered at 80 dpi and inspected across five contact sheets; the cover was inspected full size. No blank page, clipping, collision, broken figure, malformed transition, or unreadable glyph was found.

The compact source release `release/figshare/2026-08-22-reader/D90-HAB-03-09-sumber-id.zip` is 160,908 bytes, SHA-256 `be06ba070d97506970378cea801c2525abc69bb305c3770b59186a6e212a645f`, with 29 unique entries. It includes all seven wrappers and chapter bodies, class, macros, both figures, complete bibliography closure, exact CC BY 4.0 legal code, Habring-only corrections/rights/source authority, pinned Python requirements, the combined-reader builder, and `BUILD_MODULE.ps1`. A fresh extraction built all seven standalone PDFs and the combined reader successfully; the clean combined output was byte-identical at SHA-256 `6cd291cc447999b7cd72622e8c2003b837cf4f21ea5de0fcb7094913e20acd87`. No Penn, Griffin, Maple, `.mpl`, Git, credential/token, cache, or temporary entry is present.

---

# MIT OCW 6.253 first-topic semantic-source build and QA

As of: 2026-08-23  
Unit: complete-notes pages 2--5 — The Role of Convexity in Optimization / Peran Kekonveksan dalam Optimisasi  
Admission: PASS

## Exact inputs and outputs

- Authority PDF: 8,030,116 bytes / 340 pages / SHA-256 `41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181`.
- English semantic witness: `source/en/mit-01-role-of-convexity-semantic-witness.md`, 5,752 bytes, SHA-256 `a18aefa9e1ffa29d0a3cea21d0df34f05025cb7c2008ae57b5db44730c9d1f58`.
- Indonesian semantic source: `source/id-ID/mit-01-peran-kekonveksan-id.md`, 8,641 bytes, SHA-256 `2170dec12e707782c7677647f77ad8ee3360b282a8dbb9fb5620170106004bf3`.
- Semantic HTML: `output/html/D90-MIT-01-peran-kekonveksan-id.html`, 20,613 bytes, SHA-256 `fff4de952dd2cb208208e1cfb3bbc8fe8a64936ff5fdb532a23a92fb0dc6af8b`.
- Reflowed PDF: `output/pdf/D90-MIT-01-peran-kekonveksan-id.pdf`, 53,370 bytes / 3 A4 pages, SHA-256 `bd03912f9d3fe6dbe7376577c7ca6e7ab5aee007dd33b51669cde1792644df58`.

The exact source boundary is four PDF pages with 21 top-level items distributed 4/3/5/9, 12 nested bullets distributed 0/8/4/0, and two freestanding display formulas. There are no source figures, theorem statements, learner exercises, hints, answers, solutions, or interactivities in this block. Corrections `O015-MIT-SEM-0001`--`0003` disclose the discrete-dual scope, self-dual/involution meaning, and normalization of a source function-type arrow.

## Deterministic and semantic validation

`qa/build_mit_pilot.py`, 3,025 bytes, SHA-256 `b109c24f01feb1f57193a05b56ae662902078c5fd63f457084379f7db66dac74`, builds HTML5/MathML and LuaLaTeX output. Two clean bounded-output builds reproduce the admitted HTML/PDF hashes exactly. `qa/validate_mit_pilot.py`, 19,571 bytes, SHA-256 `16dacd29912fd8b749f8d6ae8d44b716f814111c0a40eed27799e64fe6bf1108`, reparses both semantic sources, verifies exact page/item anchors, recomputes list/math topology and all three corrections, rebuilds twice, rerenders the PDF, and checks document metadata/font maps. Its passing 4,167-byte report has SHA-256 `1e11642f8c1ab1ade013c4377f4dc0bc119ec0e89e6073eec787c7c341de0970`.

The actual HTML passes browser measurement at 1280-by-720 and 390-by-844 with zero horizontal or display-math overflow, one main landmark, semantic heading/TOC/skip-link structure, 14 MathML nodes including two displays, no images, no duplicate IDs, no unresolved fragments, and no console warning/error. `qa/MIT_L01_BROWSER_QA.json` is 1,757 bytes, SHA-256 `2d5c90b3343040c4ed3dfbdb3714737dfba8317d1781c1e5c27145f5afbbb76d`.

All three PDF pages were rendered at 160 dpi and inspected individually; there is no clipping, overlap, unreadable formula, broken heading, blank page, or stranded correction. The PDF is searchable, unencrypted, declares `/Lang id-ID`, and all six font resources expose ToUnicode maps. It is not tagged. Independent semantic/math rereview is P1=0/P2=0/P3=0 at `qa/MIT_L01_INDEPENDENT_REREVIEW.md`, 2,691 bytes, SHA-256 `8259c6631c1c8645684c75a0244feedfc7289023d13e909cfdc73941eed35e50`. Independent human/native-speaker Indonesian review remains unrecorded.

## Backend and next source boundary

`qa/extend_backend_mit_l01.py`, 62,794 bytes, SHA-256 `b206d3e64628ed8a98ba7a776bcc34c1d6bec19175ec59082950fe6d2e63cf79`, and `qa/validate_backend_mit_l01.py`, 39,185 bytes, SHA-256 `be59f34bc8aa083f31a7f2a62a72aa20ab264167f6288d03b04247c8ef54d19e`, add and validate 130 exact MIT/Royer/pilot records over the 1,300-record incoming baseline. The resulting backend contains 1,430 records; the added-ID set has SHA-256 `fa0e7d763e2c3eab68ac32fe935d777f3c688c5d59cc509d93416608726cfaf5`. JSONL is 1,036,556 bytes, SHA-256 `ebf44ca94323584e40b548ce36da560899e39a1e76ed2c993a0786b4ee7c4a2b`; lossless CSV is 1,244,072 bytes, SHA-256 `bc73abb3457cacc10423c1785a0db70a9007fdef8ac0a2be1de48d25d389fdf5`. Two terminal generation/validation cycles are byte-identical and return `errors=[]`.

The next coherent source-order block is complete-notes pages 6--13, from “Duality” through “Exceptional Behavior”; page 14 begins “Modern View of Convex Optimization.” Its exact topology and material Athena-figure risk are frozen in `MIT_L02_BOUNDARY_CENSUS.md`.

## Current descendant byte note

The historical ten-unit Zenodo release preserves the Penn Chapter 4 and 5
reader bytes recorded in its public receipt. The current working-tree
descendants include the later bounded terminology normalization and therefore
have distinct identities: Penn Chapter 4 is 847,337 bytes,
`18e7162f8d1e55a050ee96a6ba05a2ffaa0d5cb578f96e264152666a79dc83a8`; Penn
Chapter 5 is 2,691,773 bytes,
`dad34c7cb363197da1ae87117b22b2dde21d6d183997745cd3ffff62245c0b96`, with
wrapper SHA-256 `7de8bc61dc3f59999ac6414df90ef6925d5a7d4665f79d71998c8f0e45839c14`.
They are not substituted into the immutable historical release.

The preceding next-block note is historical now that the pages 6--13 boundary
has passed; the next executable source cursor is page 14.

# MIT OCW 6.253 pages 6--13 semantic-source build and QA

As of: 2026-08-23  
Unit: complete-notes pages 6--13 — Duality through Exceptional Behavior /
Dualitas sampai Perilaku Pengecualian  
Admission: PASS for this bounded semantic reader boundary; not a complete-course claim

## Exact inputs and outputs

- Authority PDF: `authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf` — 8,030,116 bytes / 340 pages / SHA-256 `41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181`.
- English semantic witness: `source/en/mit-02-duality-semantic-witness.md` — 11,539 bytes / SHA-256 `6fc62cd32c9231c7f4b254ee2f0c46dbe2d4f19bcb23b5523c0aaaedb4762dde`.
- Indonesian semantic source: `source/id-ID/mit-02-dualitas-dan-perilaku-pengecualian-id.md` — 12,895 bytes / SHA-256 `b3e26c12a934b023b7b7ad4933082e6b50d68cd09c948d079a6a01df6b478917`.
- HTML: `output/html/D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.html` — 38,196 bytes / SHA-256 `d722e7bebc5b5f1c0a9d4c1980b747564897521ea7632be0ab0e3433b26ec007`.
- PDF: `output/pdf/D90-MIT-02-dualitas-dan-perilaku-pengecualian-id.pdf` — 67,749 bytes / 5 A4 pages / SHA-256 `06b9c6ce9eaac8f78149e7a881ebdff6ef5c8692d9040c5dec8929a2e646d89b`.
- Validation report: `qa/MIT_L02_VALIDATION.json` — 3,076 bytes / SHA-256 `59047c4b9185e56e9f68791a12c70099d3652e42ae04ca064d0ebeaf01e2fe95`.
- Browser receipt: `qa/MIT_L02_BROWSER_QA.json` — 2,004 bytes / SHA-256 `a8f1e3fab187a21a1eee0a4362add3855648ccd3d0f249ec08216936db6dd6d1`.
- Independent rereview: `qa/MIT_L02_INDEPENDENT_REREVIEW.md` — 2,850 bytes / SHA-256 `67e20f5dc42afadb52d8cf299b6a7a8891286d1aa70b9972a17c70b407ac4e2e`.

## Topology, rights, and gates

The source closure is exactly pages 6, 7, 8, 9, 10, 11, 12, and 13: 19
top-level items, 7 nested lists, 4 freestanding display formulas, 2 explicit
examples, 1 answered didactic prompt, 1 source-display, and 61 target MathML
nodes. Seven of eight pages contain Athena Scientific permission-gated
graphics. No source image byte, crop, or copied layout is redistributed; each
surface is an exact-locator semantic description retaining labels and
mathematical relationships. No exercises, hints, solutions, or interactive
surface exists in this source boundary, and none is invented in the target.

`qa/validate_mit_l02.py` reports `errors=[]` and `result=pass`; two deterministic
HTML/PDF rebuilds are byte-identical. Browser evidence at 1280x720 and 390x844
records zero horizontal overflow, duplicate IDs, bad overflow elements, or
console warnings/errors. The PDF is searchable, A4, unencrypted, declares
`/Lang id-ID`, and is explicitly untagged. The target carries the MIT CC
BY-NC-SA 4.0 attribution, change marking, NC/SA obligations, and
non-endorsement. No human/native-speaker Indonesian review is represented.

## Continuation

The preceding page-14 continuation wording is historical now that L03 is
admitted. The next source cursor is complete-notes page 15. The additive backend
extension is also admitted and idempotent:
it adds 65 records (8 segments) to the protected 1,430-record baseline, for
1,495 total records / 92 stable segments. `backend/records.jsonl` is 1,076,672
bytes, SHA-256 `61422fc3d0a1dfa3fed57f3710ae0ffbefb48b8b45957c25ed7455d3a9bd05e7`;
`backend/records.csv` is 1,293,072 bytes, SHA-256
`146f9a251bcd6b7c9938debc5e9b3f8d680cb51b6d6309bc9a85c90269d22f82`; the
65-ID set is `1436ab92aa0c80e1aedaf5ae1dce1b2ba28b31a9a88695d6f6d2803bc41789c4`.
The extension script is 27,926 bytes, SHA-256
`9c13a77eb1bd6a4d440bd4f765099201ccf1e1bba611423a9689853cac1d8368`; the
validator is 15,089 bytes, SHA-256
`5b0999b563b7dd3afa199bd8d89d391772b026035b836d448f2cef418576811a`, and its
passing receipt is 7,985 bytes, SHA-256
`6a325456a0591b6fe17704b7d0139247bbed8d1a622a18702f86048b45939005`.
Only these final frozen backend identities are controlling; earlier
intermediate L02 hash blocks (`b3f5...`, `2e2e...`, and related CSV/receipt
values) are superseded and noncanonical. The remaining full-course bridges, labs, mastery/solution layer, capstone,
semantic EPUB, tagged PDF, and human review remain open. Automatic Penn
expansion remains stopped; page 14 is the next executable source cursor.

# MIT OCW 6.253 page 14 semantic-source build and QA

As of: 2026-08-23  
Unit: complete-notes page 14 — Modern View of Convex Optimization /
Pandangan Modern tentang Optimisasi Konveks  
Admission: PASS for this bounded semantic reader boundary; not a complete-course claim

## Exact inputs and outputs

- Authority PDF: `authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf` — 8,030,116 bytes / 340 pages / SHA-256 `41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181`.
- English semantic witness: `source/en/mit-03-modern-view-semantic-witness.md` — 3,961 bytes / SHA-256 `ba74c799dfd1dfe87fc7be0695fd12d1780dadbff44d86f8ad6b7fc015171605`.
- Indonesian semantic source: `source/id-ID/mit-03-pandangan-modern-optimisasi-konveks-id.md` — 4,758 bytes / SHA-256 `24599f175ae5a40246d9677042a5c3d191802900562467d94eede8ef72837060`.
- HTML: `output/html/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.html` — 9,762 bytes / SHA-256 `01785166246be0f1187353c64f228f341626951e7d20fef127a4b92ab7e96d90`.
- PDF: `output/pdf/D90-MIT-03-pandangan-modern-optimisasi-konveks-id.pdf` — 34,550 bytes / 2 A4 pages / SHA-256 `3cc20409b71331564cbc5429ce72cd27ebe3cbdb072910d2483e0bdeee54a136`.
- Validation: `qa/MIT_L03_VALIDATION.json` — 2,836 bytes / SHA-256 `fd92d811343e22192573293745c2f11175ba493f44bc5eb39801dfa6c47daff6`.
- Browser QA: `qa/MIT_L03_BROWSER_QA.json` — 1,396 bytes / SHA-256 `3455de5d1e4edfbc236d0684c252e254bb7a29a54f5519306e0c24c27ac6cb5e`.
- Independent rereview: `qa/MIT_L03_INDEPENDENT_REREVIEW.md` — 2,163 bytes / SHA-256 `daba4cbafe99d3fa47c8a9a9b9959ed8860b7bde442e5dc94a126171ca8227b1`.

## Topology, rights, and gates

The source closure is exactly complete-notes page 14: 2 top-level items, 6
nested bullets, 2 source-figure surfaces, zero display formulas, and zero image
bytes in the derivative. The two Athena Scientific permission-only graphics are
omitted as bytes, crops, and layout and replaced with exact-locator semantic
descriptions retaining labels and mathematical relationships. The target keeps
MIT CC BY-NC-SA 4.0 attribution, change marking, NC/SA obligations, and
non-endorsement. The source has no learner exercises, hints, solutions, code, or
interactive surface; none is invented or claimed.

`qa/MIT_L03_VALIDATION.json` reports `errors=[]` and `result=pass`; two
deterministic HTML/PDF rebuilds are byte-identical. Browser evidence at
1280x720 and 390x844 records no horizontal overflow, duplicate IDs, unresolved
fragments, images, or console warnings/errors. The PDF is searchable, A4,
unencrypted, declares `/Lang id-ID`, and is explicitly untagged. No
human/native-speaker Indonesian review is represented.

The current public preservation baseline is corrected Zenodo record
`10.5281/zenodo.22071030`; its sanitized readback is 9,338 bytes, SHA-256
`4d1ec4e50c2428a6c0cbad1e8e530892f1bc0b6c6eeb7da89b48e987932c6dbb`. That
record is the corrected L02 lineage and is not a claim that L03 files are
already public. The next source cursor is complete-notes page 15.

# MIT OCW 6.253 page 15 semantic-source build and QA

As of: 2026-08-23  
Unit: complete-notes page 15 — The Rise of the Algorithmic Era /
Kebangkitan Era Algoritmik  
Admission: PASS after live browser QA for this bounded semantic reader boundary; not a complete-course claim

## Exact inputs and outputs

- Authority PDF: `authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf` — 8,030,116 bytes / 340 pages / SHA-256 `41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181`.
- English semantic witness: `source/en/mit-04-rise-algorithmic-era-semantic-witness.md` — 3,225 bytes / SHA-256 `1c6afe0318471c2680291c2968a348ff84ad3dbeb702218d1496412b3871c5f8`.
- Indonesian semantic source: `source/id-ID/mit-04-kebangkitan-era-algoritmik-id.md` — 4,081 bytes / SHA-256 `98d4a0d31241e626e96b7929cb2cda135c8559d829326711f7dff436b8cdab0d`.
- HTML: `output/html/D90-MIT-04-kebangkitan-era-algoritmik-id.html` — 9,975 bytes / SHA-256 `c7ee3ace683dd854ce99259536b58bc802cb17fdd189a32b403f9e87521ea81e`.
- PDF: `output/pdf/D90-MIT-04-kebangkitan-era-algoritmik-id.pdf` — 36,971 bytes / 2 A4 pages / SHA-256 `9056c6ba9fa3996f907d1dfd6147ef219aa7c88941582c78d01977e60ce8ef5f`.
- Validation: `qa/MIT_L04_VALIDATION.json` — 3,400 bytes / SHA-256 `891dc5639a16099b81667fa2101df0992cf4d4c83654f44a2921ba12831717cd`.
- Builder: `qa/build_mit_l04.py` — 3,614 bytes / SHA-256 `733a186a8eb98bc418926ac2642b4e2b6093ef6432ba3471f4df9b9ffe00f9e7`.
- Validator: `qa/validate_mit_l04.py` — 18,735 bytes / SHA-256 `b2b5f289b35e4dadc2a49fb367b1373094789061aab31bf2b99056541052ab17`.
- Browser QA: `qa/MIT_L04_BROWSER_QA.json` — 1,125 bytes / SHA-256 `87a619e7df2a4226fe6f27307659b049e2176795b11488401dc05a6a34c86e56`.
- Visual QA: `qa/MIT_L04_VISUAL_QA.json` — 1,275 bytes / SHA-256 `6da40ec0179d47143a4f99bea9a8e3e899d776773de6580afb1417085e8ff1bf`.
- Independent rereview: `qa/MIT_L04_INDEPENDENT_REREVIEW.md` — 1,906 bytes / SHA-256 `39dc3005a3f16445eccdb73363719b3b03224efc573f7c8a45f9c73bc8a3b7d4`.

## Topology, rights, and gates

The source closure is exactly complete-notes page 15: 6 top-level items, 12
nested bullets, 1 inline math surface, zero display formulas, zero figures, and
zero image bytes. The MIT component remains CC BY-NC-SA 4.0 with attribution,
change marking, NC/SA obligations, and non-endorsement. The source has no
learner exercises, hints, solutions, code, or interactive surface, and none is
invented in the target.

`qa/MIT_L04_VALIDATION.json` reports `errors=[]` and `result=pass`; two
deterministic HTML/PDF rebuilds are byte-identical. Its live browser QA reports
`result=pass` at desktop 1280×720 and mobile 390×844, with no horizontal
overflow or console findings and zero duplicate IDs, unresolved fragments, or
images. The PDF is searchable, A4, unencrypted, declares `/Lang id-ID`, and is
explicitly untagged. No human/native-speaker Indonesian review is represented.

## Publication and continuation

Zenodo publication for L04 is pending after an HTTP 504; no L04 DOI or public
byte identity is claimed. The corrected L02 record remains the last verified
public checkpoint. The next source cursor is complete-notes page 16; automatic
Penn expansion remains stopped.

## 2026-08-23 final L04 gate refresh and consolidated continuation

The earlier `pass_with_limitation` browser wording in this L04 record is
superseded. Live browser QA now reports `result=pass` in
`qa/MIT_L04_BROWSER_QA.json` (1,125 bytes; SHA-256
`87a619e7df2a4226fe6f27307659b049e2176795b11488401dc05a6a34c86e56`).
At 1280×720 and 390×844 the DOM has no horizontal overflow, console findings,
duplicate IDs, unresolved fragments, or images. Final validation reports
`errors=[]`, `result=pass`: `qa/MIT_L04_VALIDATION.json` is 3,400 bytes,
SHA-256 `891dc5639a16099b81667fa2101df0992cf4d4c83654f44a2921ba12831717cd`;
`qa/validate_mit_l04.py` is 18,735 bytes, SHA-256
`b2b5f289b35e4dadc2a49fb367b1373094789061aab31bf2b99056541052ab17`.
The reader PDF remains untagged and human/native-speaker Indonesian review is
still unrecorded; those limitations are unchanged.

The additive L04 backend gate passes over the byte-preserved 1,495-record L02
baseline. It adds 48 records (17 artifacts, 1 learning surface, 14 QA events,
14 relations, 1 segment, and 1 unit), yielding 1,543 total. Exact frozen
identities are:

- `backend/records.jsonl`: 1,102,706 bytes; SHA-256 `92f6b805a83361f29a830b8c37b1c52f3468cb420d10b9a3a810cf0f8ac20645`.
- `backend/records.csv`: 1,325,476 bytes; SHA-256 `fedc1855df37e006e52ba76d99af2ee132accfa3b416519c39c036454f378a7d`.
- New-ID set: SHA-256 `8216b6f6713c519699e42923138a3f5e1f374000f3a494ececc646b9819dbb2d`.
- `qa/extend_backend_mit_l04.py`: 26,315 bytes; SHA-256 `19d315c38d77691b067050e6a09ffb411767008a41582b1674c90d37087f7272`.
- `qa/validate_backend_mit_l04.py`: 14,123 bytes; SHA-256 `d218daa09e803be9dd9c6401a5aace85f5340a88dbb7cf53b3563728bbb79c46`.
- `qa/MIT_L04_BACKEND_VALIDATION.json`: 7,178 bytes; SHA-256 `59277c7f61b350625d829b079b8800343489a97591c7f4cbf56d01e2c82c1204`; `result=pass`, `errors=[]`.

L03 publication is now verified at DOI `10.5281/zenodo.22071175`: 40 public
files (32 inherited plus 8 additions), a 484,193-byte delta ZIP SHA-256
`16116f249ffd4fc731a01de8f748b13c9e32c6734ca60c035098420e40b2909f`,
and an 11,373-byte anonymous readback SHA-256
`3d3a22a371eb267915f19773e8d4fc94b482840d808a46b0b376e98518ad8822`.
The L04 HTTP 504 attempt published nothing, so no standalone L04 release or DOI
is claimed or planned. Page 16 begins the next coherent multi-page source
section/batch; it receives one consolidated semantic, build, browser, visual,
backend, rights, and preservation gate at the batch boundary rather than a
page-level project/release cycle.

# MIT OCW 6.253 pages 16–19 semantic-source build and QA (L05)

As of: 2026-08-23
Unit: complete-notes pages 16–19 — closing course-orientation block
Admission: PASS; one coherent four-page boundary, not a complete-course claim

## Exact inputs, outputs, and QA evidence

- Authority PDF: `authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf` — 8,030,116 bytes / 340 pages / SHA-256 `41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181`.
- English semantic witness: `source/en/mit-05-course-orientation-semantic-witness.md` — 7,120 bytes / SHA-256 `3acbde47074da0429419e5c702785ee0490efa5e43f2b07cbac497f0d480492f`.
- Indonesian semantic source: `source/id-ID/mit-05-orientasi-kursus-id.md` — 8,702 bytes / SHA-256 `65cb7fec2d6b1aeda69837e10568f2410a9f4bded2b835b8dac59a9b516444cc`.
- HTML: `output/html/D90-MIT-05-orientasi-kursus-id.html` — 16,029 bytes / SHA-256 `424d854bb1e83e841a15d0073aad3db6bab0585ca6d587fd14a3b5cfb4274d83`.
- PDF: `output/pdf/D90-MIT-05-orientasi-kursus-id.pdf` — 46,785 bytes / 3 A4 pages / SHA-256 `2af9e4dc8e999969f03817350451c4b21f3c764564eee64327d15b48483313c0`.
- CSS: `source/id-ID/mit-l05.css` — 2,636 bytes / SHA-256 `d8d8417c4d2f9e01852cd30bc97552f377da3a6d1f9bbee25c25d47e16ce9645`.
- Validation: `qa/MIT_L05_VALIDATION.json` — 4,195 bytes / SHA-256 `2ef09a674c6bcc586cd13dd513a2f0f24aade6d10d2d11ccdfe317b7307dc3aa`.
- Live browser QA: `qa/MIT_L05_BROWSER_QA.json` — 1,271 bytes / SHA-256 `24b775fb6afc271a16a62097151175852a4a01eb1c41605a196258e19f01d342`.
- Visual QA: `qa/MIT_L05_VISUAL_QA.json` — 1,544 bytes / SHA-256 `d32b4e66cf7c1fd4f9fa06c75f88bfb80404caeefe894ba92396c548d126af04`.
- Independent rereview: `qa/MIT_L05_INDEPENDENT_REREVIEW.md` — 3,066 bytes / SHA-256 `c1c358c32f245ca4ef1c15efe3ed4d319f9bdef758319bce04f501bb525f7fb9`.
- Immutable correction snapshot: `00_control/MIT_L05_CORRECTION_SNAPSHOT.jsonl` — 642 bytes / SHA-256 `c701e631c4839aa07a2f8a4b8e8f026394c66bd709ffa37318431bbc461e1595`.

## Topology, rights, and reader gates

The boundary is exactly four source pages with four ordered source headings,
16 top-level items, 26 nested bullets, two unique live source URIs, zero
mathematical formula surfaces, zero figures, and zero image bytes. It contains
no table, worked example, exercise, hint, solution, code, or interactive
surface. MIT CC BY-NC-SA 4.0 attribution, change marking, NC/SA obligations,
and non-endorsement remain explicit. `O015-MIT-SEM-0004` is admitted as a
determined name correction: the witness preserves the printed “Vanderbergue,”
and the learner-facing target uses and discloses “Vandenberghe.”

Two deterministic builds are byte-identical. Validation reports `errors=[]`
and `result=pass`. Live browser QA at 1280×720 and 390×844 reports no horizontal
overflow or console findings, with zero duplicate IDs and unresolved
fragments. All three A4 PDF pages pass 160-dpi visual inspection without
clipping, overlap, missing glyphs, black boxes, or malformed lists. The PDF is
searchable, unencrypted, `/Lang id-ID`, and untagged. Independent rereview
closes P1=0/P2=0/P3=0; human/native-speaker Indonesian review is unrecorded.

## Backend and continuation gates

The final additive L05 backend has 1,605 records, adding 62 records to the
exactly reconstructed, byte-preserved 1,543-record L04 baseline. The protected
baseline is JSONL 1,102,706 bytes /
`92f6b805a83361f29a830b8c37b1c52f3468cb420d10b9a3a810cf0f8ac20645`
and CSV 1,325,476 bytes /
`fedc1855df37e006e52ba76d99af2ee132accfa3b416519c39c036454f378a7d`.
Final L05 identities are:

- `backend/records.jsonl`: 1,142,443 bytes; SHA-256 `30c6f3257d481136995acd7947a725da003c4ab2ea2e9049de53a23fa681658b`.
- `backend/records.csv`: 1,373,874 bytes; SHA-256 `f66227edc14e953b44d833b87b0373f76d87bf04fdd32d2f50552597915746e3`.
- `qa/extend_backend_mit_l05.py`: 35,174 bytes; SHA-256 `6a1b0c319e3a59820bcd18b257b9d160d0c39ae21f1dcf772df9bb8a61c7b36c`.
- `qa/validate_backend_mit_l05.py`: 27,004 bytes; SHA-256 `d4572ac9c0924459beebb225f8184b60b8e6a022fe1bdcccba2a6409a4f6fbab`.
- `qa/MIT_L05_BACKEND_VALIDATION.json`: 5,108 bytes; SHA-256 `7e653889523fdf6da918a0403e230b7f3a185107ed87ca22cc6936f37db57afc`; `result=pass`, `errors=[]`.

No standalone L04 Zenodo version exists. A combined L04+L05 Zenodo checkpoint
and the GitHub push containing L05 remain pending. The active production batch
is complete Lecture 2, pages 20–28: its 9,962-byte census has SHA-256
`fc0cb5b863652aa810ed765f247a248be1510cd61f240277b896e605a41b3ea4`.
Its witness and target are drafted but unadmitted, and build/QA is in progress.
Page 29 begins Lecture 3 and is the next-after-batch cursor.

## 2026-08-23 — Consolidated L04+L05 release gate

`release/zenodo/2026-08-23-mit-l04-l05/build_l04_l05.py` passed twice with
byte-identical outputs before publication. The frozen delta ZIP is 482,954
bytes / SHA-256
`96e323fb190462747a3e4b97c21211fc63f7e555ae029c7b683078ac28ac8c17`;
the archive reopens with 53 entries, all 52 manifest-bound payloads match, and
the forbidden-entry count is zero. Publication and credential-free readback
then passed for 50 public files (40 inherited unchanged, 10 additions). The
public bound manifest is 4,486 bytes / SHA-256
`437179a80f28091b0351172d8b56a0c46d945efe292da6e63c28b62b0da96b9a`;
the public checksum file is 5,039 bytes / SHA-256
`59c26562dd44d2ed4333ff21c674daccbea8077a0f8220a1c3564524ceba57cb`.
The public receipt is 14,060 bytes / SHA-256
`89266a7b3a332081aaef9d591eb1df449c6b0a1ab0a8526a1b91f27b8be01cd5`.

## 2026-08-23 — L05 GitHub public-byte gate

After pushing content commit `e18454bcb72251c3cc65a522046e6ed572792f7b`,
the anonymous commit API returned HTTP 200 with exact tree
`5a2841879dcc0122ad3e2243637cc5e257ee4a88`. Every one of the 42 paths
changed from parent `c944f218ec6d806bbc0dd12623275819bdb022a3` was then downloaded from
the immutable raw-commit surface; every response was HTTP 200 and matched the
corresponding Git blob byte-for-byte and by SHA-256. Receipt:
`release/github/2026-08-23-mit-l05/github-public-readback.json`, 10,947 bytes,
SHA-256 `1ecd35857a60b122d925b4ac53dca185cfae337b89f0552713167a8902595b7c`.

# MIT OCW 6.253 Lecture 2 pages 20–28 consolidated build and QA (L06)

As of: 2026-08-23  
Admission: PASS; complete Lecture 2, not a complete-course claim

Exact witness, target, HTML, and PDF identities are respectively 15,594 bytes /
`a8094ad892a90a20d271e961504fb418b1ea241859b072cf5ba56317783b809a`,
17,772 /
`a9e8b353adddc4919b6244e27df4365a33e74d4b034b9d99fff6eb3f93e0b23e`,
70,446 /
`94275af59592c64e7c8ae55fc384b721b2863a22ee328c33dc3b1d5a1e0af9a6`,
and 74,235 /
`84ce42542ed58e102c736dacc02b69cf16ab264a577d689d2fe5f7a24ba37d75`.
The boundary census is 9,962 bytes /
`fc0cb5b863652aa810ed765f247a248be1510cd61f240277b896e605a41b3ea4`.

The 6,086-byte fail-closed reader receipt has SHA-256
`6a8eab2cb69bf1403a8da3f9fbcc40f482c4b9a18e3ebbba24ac82ccee989257`
and reproduced unchanged after another full run. It verifies nine source
pages, 32 top-level items, 17 nested items, 12 display formulas, five semantic
figure descriptions, source-page 29 as the clean delimiter, exact rights and
correction bindings, two deterministic builds, searchable A4 PDF, and zero
copied image surfaces. Browser QA at desktop 1280×720 and mobile 390×844 has
no horizontal/formula overflow, duplicate IDs, unresolved fragments, or
console findings. Four-page 160-dpi visual inspection is clean. Rereview closes
P1=0/P2=0/P3=0. The PDF remains untagged; missing human review is recorded but
is not a gate.

The backend extension and independent validator pass two successive cycles
with identical output. They add 109 records with new-ID-set SHA-256
`756dced298991b810b3d153159379728f714beee2bbe188ab07c004bdbed7b82`,
yielding 1,714 records. JSONL is 1,231,983 bytes /
`9ad375756d2ee3159acf760f5d68084d2921e665cf993e2aaa6514f1e710337e`;
CSV is 1,480,312 bytes /
`f5c81e38ee9d1b4e9d2bcc7632603266fcf271b9b8c6454e99ba3e4b0041f72f`.
Generator, validator, and receipt identities are
`33fe4df3d268cf6a4e2656befe66d517e35634c6c1387244762da524df8c1df0`,
`565f600cc936ecbbf60eaa9a9d80ea535f5b4b49934418f8a22e0571af26f5b5`,
and `247fd848a4b4d0c3960ee82d48b7648304215ca69dddf1736305734106615c4c`.
The backend binds corrections through
`00_control/MIT_L06_CORRECTION_SNAPSHOT.jsonl` (1,406 bytes /
`4049f5ed333489bc0b8942e91ae3ab05f43677f13de1e532d544d7691724737f`)
so later append-only ledger growth cannot invalidate this unit.

Next: publish this admitted boundary once in the existing GitHub/Zenodo
lineages, then build Lecture 3 pages 29–38 as one consolidated L07 batch.

## 2026-08-24 — L06 publication and public-byte gates

GitHub content commit `283998197adeccbc1cf731f8cd4748295e5ba171` / tree
`c95e59cdce36c5942e8e1cf97c78a7c4f7bcc7bc` is public. The anonymous
commit API returned HTTP 200, and all 41 changed paths were downloaded from
the immutable raw-commit surface and matched local bytes and SHA-256 values.
Receipt: `release/github/2026-08-24-mit-l06/github-public-readback.json`,
10,580 bytes / SHA-256
`f0ca9b3edead3308793daf9f1b2f60dc1019def0cdf59e54f0e483d630db64e4`.

The repaired Zenodo release gate proved the exact latest parent, concept
lineage, PDF default preview, ambiguous-publish recovery path, 50 inherited
files, and 8 additions. The local package reproduced byte-identically twice
before mutation. Public record `22073743` / DOI `10.5281/zenodo.22073743`
then passed anonymous inventory and full-byte readback for all 58 files. The
523,322-byte delta ZIP remains
`2e8806904a65e3f09143c0f7a0b5371b009b7b54f50392d21079907261d15fd1`;
its 40 entries and 39 manifest-bound payloads pass with zero forbidden
entries. Public receipt: 16,084 bytes / SHA-256
`083df9f3bcef845e8eb55b6a99e8e51b6cd8d3294e9f5818e6abbf684f31986e`.

Next: close the existing L07 pages 29–38 reader/build/visual/browser gate,
admit it once into the stable backend, and advance to page 39.

# MIT OCW 6.253 Lecture 3 pages 29–38 consolidated build and QA (L07)

As of: 2026-08-24
Admission: PASS; complete Lecture 3, not a complete-course claim

The boundary census, witness, target, HTML, and PDF are respectively 11,013 /
13,879 / 16,518 / 77,399 / 75,885 bytes with SHA-256 values
`3c7400bdd092cffe358e852e5304091bfd53b10fb36d366f558e1b0f9c8bee2f`,
`ab9fb12728b53c0369094a347827aa40d74332b811976b8e0733caf245bce18b`,
`b1554fcb455bb43ecd72aa4c4e0f70d6d502c885009ba5e6a799e639e69441dd`,
`cc3b4f665d5f0b4cb9e26245ec0cce71658c6c0b3e5e07cee3fcabfb43df5e13`,
and `2c7b4defaa56578f628c048dc4f17ee06b61f2bc33122b172af5539a5dae2eec`.
The validator is 28,883 bytes /
`9dd39156c3591c0a771cc894ac5085fb5c787b5a472b722be24eb4d84c2d16ca`;
its rereview-bound receipt reproduced unchanged at 8,176 bytes /
`c076f79323c21186ceab5cbb56a128c71a31c67aa55b635f1eeebe313b4bd7e1`.

The gate verifies ten source pages, 16 top-level items, 14 nested items, 13
display formulas, four text-only figure blocks / six panels, and source page
39 as the clean Lecture 4 delimiter. Two deterministic HTML/PDF builds match
the canonical bytes. Desktop 1280×720 and mobile 390×844 have no horizontal
or formula overflow, duplicate IDs, unresolved fragments, or console
findings. All four PDF pages pass 160-dpi visual inspection. Independent
rereview is 4,136 bytes /
`d5f0bfc23b7a9b74d30570de9b2bd058c0ded84b51414b7b0b929349764ea86d`
and closes P1=0/P2=0/P3=0. The searchable A4 PDF is `/Lang id-ID` and untagged.

The immutable correction snapshot is 1,490 bytes /
`eba6c2039e1f893287921d72f5169e14861d95955acd7c6682e59cabcd030084`.
Two root-repeated backend generator/validator cycles are identical. They add
106 records with new-ID-set SHA-256
`a7ff4f1545568ab41e9e47fade09c80258750639781f5724d3e2a0792e7c2e66`
and yield 1,820 records. JSONL and CSV identities are 1,321,559 bytes /
`1f6384b25937765bdd32e9ae59d68ac11772c15ddd250861d7d051742ad43843`
and 1,586,211 /
`a6986c21e9757dd1750dd5e515e9038a973ecbeeae22db07d99ff81ea3f92985`.
Generator, validator, and passing receipt hashes are
`f2e6bdc042bfd1fe39e902aa4c413b6d421e7bf0ce491cf805dd4a709922c993`,
`7d9a47c70186e456b3281230223a89e1e8af9382509125e8de2d55af0386e867`,
and `37ddb31f13788e7e0ae6622304b38ec456693b78726bdf2625c5a7797be9d948`.
Next: preserve L07 once in the existing public lineages, then freeze the
coherent Lecture 4 batch beginning on page 39.

## 2026-08-24 — L07 local preservation package gate

`release/zenodo/2026-08-24-mit-l07/build_l07.py` was repeated twice after
backend admission and reproduced the same release bytes. The delta ZIP is
410,297 bytes / SHA-256
`767d3d21dd587f328c6c631ff9ba1febca6e3168474c2d264d90fa0b040bea40`;
it reopens with 27 unique entries, all 26 manifest-bound payloads pass exact
size/hash checks, and forbidden, credential-shaped, and mutable-global-control
entry counts are zero. The manifest and checksum file are 5,396 and 6,723
bytes / SHA-256
`3465065b4062a7cfe9361b4efc20f60930e2584c496bd8651f50365266a5139e`
and `de5ef346e2a00cdd6dd62b392af1e1e9010e458c8361e6037e990bf660ff8910`.
The intended public inventory is 58 inherited files plus eight additions,
with the L07 PDF as default preview. This is preparation evidence only until
the existing-lineage publication and anonymous readback close.

## 2026-08-24 — L07 public preservation and bound-manifest gate

GitHub content commit `c9cbd848a97b535049355d756de5e53d650fa25d` / tree
`4345de52cea5c3d5d0665484faff3b9ff8c84eef` passed anonymous immutable-patch
and exact-byte readback for all 40 changed paths. Receipt: 10,827 bytes /
SHA-256
`d3596d7f91afebced0fa1ba5ab85d99b09d10ba5549b57d7660bd41b9b98e0b5`.

The local release builder was extended fail-closed so draft creation binds the
manifest to record `22074102` / DOI `10.5281/zenodo.22074102` before upload.
The final bound manifest and checksum file supersede their pre-draft hashes:
5,423 bytes /
`743fec5b9dce1e7464af5c8d31c755e6cc04f37e1f0fdb91f827ca3feaddfe07`
and 6,723 bytes /
`9f0ca3ccf05b91917267fc54b35d0e4bc8aa3c3b2bbf7abeb2623283bf53ecaa`.
The ZIP remains 410,297 bytes /
`767d3d21dd587f328c6c631ff9ba1febca6e3168474c2d264d90fa0b040bea40`
and passes 27-entry / 26-bound-payload verification. All 66 public files—58
inherited and eight additions—passed anonymous byte/SHA-256 readback, with
the L07 PDF as default preview. The public receipt is 18,225 bytes /
`cc2681664e065d897e104218a086e9f113e8149ac474eedd026dcf51d28bfc81`.
No L07 preservation action remains; page 39 is next.

# MIT OCW 6.253 Lecture 4 pages 39–49 consolidated build and QA (L08)

As of: 2026-08-24
Admission: PASS; complete Lecture 4, not a complete-course claim

The boundary census, witness, target, HTML, and six-page PDF are respectively
11,700 / 22,457 / 24,496 / 113,898 / 91,293 bytes with SHA-256 values
`20ef255184a6e31476b368bd8b1ad08c39ea2ab9f6fdc1fa2c53574471a95055`,
`db45c443fb4e978b6bb4681a228a279f83048b8210530f77ed772a82c5f324a4`,
`b0c8b0418db9029441db23ad7deac1bed8a187ef9ae5ecd61ccfb56ce2a78758`,
`b084dd10113b55e7789885d0ec303376c0bca58fdbb960b428ce1feac9e30c0a`,
and `b01517ee401e0b9f069e4f121f57e1bc3a482b9ceb69cba067c4371f11a47e62`.
The validator is 33,409 bytes /
`48d83f7bb0b4cb115ea91ccc9e98daf5c88e86faaedc425adccfeea20ea040e0`;
its receipt reproduced unchanged at 10,509 bytes /
`da2448349a7075fe20008df94f2f3a45d472df5ab1d3631a43a3f12f6352c745`.

The gate proves pages 39-49, page 50 as the clean delimiter, 27 top-level
items, 16 nested items, 26 display formulas, and five semantic figure
descriptions. Corrections `0009`-`0011` are bound. Two deterministic builds
match canonical bytes. Desktop 1280×720 and mobile 390×844 have no horizontal
or formula overflow, duplicate IDs, broken fragments, or console findings.
All six A4 pages pass 160-dpi visual inspection. Independent rereview closes
P1=0/P2=0/P3=0. The PDF is searchable, `/Lang id-ID`, and untagged.

The immutable correction snapshot is 2,347 bytes /
`d99f8df4e722a9c98368bb169df17aa41d21754766b9ee19747a52569b40cb17`.
Two further root-repeated backend generator/validator cycles are identical.
They add 137 records with new-ID-set SHA-256
`407216b4f4337bb2c55716c81cad231ca596d65df250297fbaff57e1f295db59`
and yield 1,957 records. JSONL and CSV identities are 1,441,643 bytes /
`0779f8bc03d437da72adafe2daf99c820d5849f0e14b630a0c3bd6f512b10085`
and 1,727,978 /
`ed209ae9325d27b5e1360b59804833e91ab014c821741f2f52badfc5f0eda836`.
Generator, validator, and passing receipt hashes are
`6920fe6c673fddb80d018ea29814c26ed64741d0241a7ce73ea9580c760262d0`,
`9e884f1dcc4d71ff149468ffaa0804deb0b772ff93a923ad6468777b970e0be8`,
and `98a726263b5ec30a3fbadc6080afc38472338831f7a176aa0e81c1bad8635d4a`.
Next: preserve L08 once in the existing GitHub/Zenodo lineages, then advance
to complete Lecture 5 beginning on page 50.
