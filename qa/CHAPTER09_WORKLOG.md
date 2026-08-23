# Chapter 9 worklog — Transportasi Optimal

Date: 2026-08-22  
Disposition: complete and admitted  
Next cursor: Penn State Math 555 Chapter 3

This worklog is the execution record for the complete Indonesian edition of Habring Chapter 9. It is sufficient to resume without conversation history. All identities were recomputed from the final live artifacts before this file was written.

## Final artifact ledger

| Role | Path | Bytes | Lines/pages | SHA-256 |
|---|---|---:|---:|---|
| Frozen authority | authority/habring/source-v1/optimal_transport.tex | 15,378 | 264 | 719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba |
| Indonesian target | source/id-ID/habring-09-transportasi-optimal-id.tex | 21,252 | 352 | 45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd |
| Standalone wrapper | source/id-ID/D90-HAB-09-transportasi-optimal-id.tex | 6,822 | 87 | 1e308a2bed0d1a6f5cdcff09cce932674cf32842a135bc88a5a34bc96c483ff6 |
| Corrected local bibliography | source/id-ID/references-ot-id.bib | 306 | 9 | 93611c4b6a753478c51c601e59ef6cd3e290677e2e2d25b104d5d3b74df03126 |
| Content correction proposal | qa/CHAPTER09_PROPOSED_LEDGER.jsonl | 8,840 | 12 | 643fde3fbe1409732ef2df8fdef52465e4df7a583fd9bbeb2137a6122f548add |
| Structural audit script | qa/audit_optimal_transport_unit.py | 44,280 | 1,223 | 5c4c030ac4512a0b0785053c19b5ed2eb1a6d35bb4147cac6fe8842807c43a5c |
| Strict structural report | qa/OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json | 19,924 | 826 | eb8b194c01dd7610dcdb7325322765ab16b3ec9cf907d28f9463fa11692767aa |
| Formula-delta manifest | qa/OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json | 79,141 | 2,508 | 796e13fbf1f221139f0233d30b2464dfb026027eb5b9ce44b66b58c2f2e169ef |
| Solver validator | qa/validate_optimal_transport_unit.py | 26,029 | 630 | e574ea3e7f924a3d1becb148162faec27ae715040665b06def284f11990500c0 |
| Solver receipt | qa/OPTIMAL_TRANSPORT_SOLVER_RESULTS.json | 16,970 | 698 | 4f751c615f2d7f03622b1447b3985ad1d660bd4f758cf4c4fb61d4d384b4e7a0 |
| Final extracted text | qa/D90-HAB-09-transportasi-optimal-id.txt | 30,053 | 549 | 283864c3fc84d414ff721f128a0f10e4b61b4646c0f5edcd53551ee13f911859 |
| Canonical build PDF | build/habring-unit-09-id/D90-HAB-09-transportasi-optimal-id.pdf | 498,244 | 15 pages | edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214 |
| Reproducibility PDF | build/habring-unit-09-id-repro/D90-HAB-09-transportasi-optimal-id.pdf | 498,244 | 15 pages | edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214 |
| Output PDF | output/pdf/D90-HAB-09-transportasi-optimal-id.pdf | 498,244 | 15 pages | edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214 |
| Canonical build log | build/habring-unit-09-id/D90-HAB-09-transportasi-optimal-id.log | 103,255 | 2,456 | 2b083221c49f6fbdede8f541e68cd9129632a74168d7855c1ddc14c1bf48b3a4 |
| Reproducibility build log | build/habring-unit-09-id-repro/D90-HAB-09-transportasi-optimal-id.log | 103,297 | 2,456 | 42e765bd3c94d9ac91b3c88974ecf093d18d027eae41ff08e7b8c4fe2085629d |

At this boundary, 00_control/ADVERSE_LEDGER.jsonl contains 99 records/lines, 58,370 bytes, SHA-256 09a982c3e91f83655150f7ae29a6351cb071558ed14a36cbb3701d7f43e9d824. Events O015-HAB-ADV-0084 through O015-HAB-ADV-0096 are present; 0084–0095 exactly match the proposal, and the separate wrapper bibliography event 0096 matches its audited record.

## Work completed

1. Froze arXiv:2607.11664v1 and the complete editable optimal_transport.tex authority under CC BY 4.0.
2. Translated the chapter contiguously into nine stable segments while preserving the native TikZ figure, definitions, theorems, proofs, note, quote, citations, footnotes, glossary surfaces, labels, and reference order.
3. Corrected and disclosed the thirteen determined source/reader defects recorded as O015-HAB-ADV-0084 through O015-HAB-ADV-0096.
4. Added a standalone Indonesian wrapper with source identity, prerequisites, correction appendix, attribution, license, and nonendorsement.
5. Replaced only the unit-local Villani bibliography metadata. The frozen source references.bib remains unchanged. Springer’s official record at https://link.springer.com/book/10.1007/978-3-540-71050-9 confirms Cédric Villani as sole author and DOI 10.1007/978-3-540-71050-9.
6. Completed strict structural/formula admission, deterministic solver validation, two byte-reproducible builds, text extraction, font/Lang inspection, and all-page visual QA.
7. Completed the final independent mathematical and linguistic rereview. Three P3 observations were repaired; the final changed-surface and full-scope disposition is P1=0, P2=0, P3=0.

## Structural and formula result

Admission result: PASS, strict-ready, zero failures.

- 47 source environments occur in exactly the same begin/end order in the target.
- All five labels are retained uniquely.
- Nine stable segments cover 259 authority lines, every nonblank line exactly once.
- No nonblank source line is uncovered, duplicated, or out of bounds.
- Reference, citation, footnote, glossary, figure, and TikZ topology closes.
- Formula inventory: 162 authority, 232 target.
- Delta topology: 35 blocks, 34 substantive.
- Every substantive formula delta is bound to exact proposed and integrated records O015-HAB-ADV-0084 through O015-HAB-ADV-0095.
- Event 0096 is an exact integrated wrapper/bibliography correction and is intentionally outside formula-delta scope.

The strict audit was run twice after the final target freeze and produced byte-identical report and formula-manifest files.

## Mathematical/computation result

The solver receipt is deterministic PASS with 41/41 gates and four source-defect negative controls. Runtime: Python 3.13.9, NumPy 2.4.4, SciPy 1.17.1, scipy.optimize.linprog(method="highs").

- Rectangular finite OT: shape 3 by 4, primal objective 0.575, dual objective 0.575, absolute duality gap zero, exact row/column residuals.
- Wasserstein-2 witness: squared distance 3.0, distance 1.7320508075688772, identity/symmetry/finite-moment checks pass.
- Entropic Sinkhorn: epsilon 0.6, 27 iterations, maximum row residual 3.608224830031759e-15, column residual zero, factorization residual zero, KKT residual zero, minimum plan entry 0.005299916588628498.
- Strict-convexity cycle witness and scaling-gauge invariance pass.
- Negative controls prove the source’s scalar-simplex type error, undimensioned rectangular ones vectors, malformed transposed marginal, and unrestricted logarithmic entropy domain fail as recorded.

The final review confirms correct measurable-space/Monge domains, Kantorovich existence hypotheses, Wasserstein moment scope, bounded-continuous dual class, marginal-separation and strong-duality disclosure, discrete dimensions, entropy extension, strict positivity before KKT, scaling uniqueness, and well-posed Sinkhorn convergence.

## Deterministic build receipt

Working directory:

    <repository-root>\source\id-ID

Environment:

    SOURCE_DATE_EPOCH=1783900800
    FORCE_SOURCE_DATE=1
    TZ=UTC

The epoch is 2026-07-13T00:00:00Z. Canonical command:

    latexmk -gg -pdf -interaction=nonstopmode -halt-on-error -file-line-error "-outdir=<repository-root>\build\habring-unit-09-id" D90-HAB-09-transportasi-optimal-id.tex

The second command changed only the output directory to build/habring-unit-09-id-repro. Both PDFs are byte-identical. Toolchain: pdfTeX 1.40.29 / MiKTeX 26.5; LaTeX2e 2025-11-01; latexmk 4.88; Biber 2.21. The final log has no TeX error, undefined control sequence, unresolved citation/reference, missing glyph, overfull/underfull box, or rerun request.

## Visual, text, fonts, and language metadata

- Final PDF: 15 A4 pages, PDF 1.5, unencrypted, no form or JavaScript.
- All 15 pages have extractable text.
- The retained 30,053-byte text file is byte-identical to a fresh in-memory pdftotext -layout -enc UTF-8 extraction from the final PDF.
- Catalog /Lang is id-ID; PageMode is UseOutlines; three outline entries are present.
- All 19 font resources are embedded, subset, and have Unicode mappings.
- The document is untagged and has no MarkInfo.
- Fifteen 120-dpi page images were inspected through a complete contact sheet; duality page 8, entropic/KKT page 10, and correction page 13 were also inspected at full size.
- No clipping, collision, blank content page, broken glyph, unreadable formula, bibliography-name defect, or running-header defect remains.

## Explicit remaining work

The Chapter 9 source/PDF unit itself is complete. Remaining edition-level work is:

- tagged-PDF accessibility or an equivalent accessible reader surface;
- independent human/native-speaker Indonesian language review;
- reflowable HTML and EPUB production;
- browser-native interactive or computation surfaces where additive;
- publication/public-byte readback under the controlling release workflow.

These gaps do not reopen the mathematical or structural admission of Chapter 9.

## Resume cursor

Do not return to Chapter 9 unless a live artifact identity changes or a new defect is demonstrated.

Continue in source order at Penn State Math 555 Chapter 3:

- authority/penn-state/source/ClassNotes/Section3.tex
- title: Introduction to Gradient Ascent and Line Search Methods
- 41,715 bytes
- 608 lines
- SHA-256 d4ae6142e2366b12575eafddc833df067518af114e9816187668cc367be43010

Preserve the established non-overlap boundary: do not import Penn Chapter 9 or the LP/IP modeling, simplex, LP duality/sensitivity, network, and general OR material assigned elsewhere.
