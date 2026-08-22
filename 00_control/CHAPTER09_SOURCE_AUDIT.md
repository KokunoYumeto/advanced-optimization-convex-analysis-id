# Chapter 9 source audit — Transportasi Optimal

Status: PASS  
Frozen on: 2026-08-22  
Course role: O015 / D90 Advanced Optimization and Convex Analysis  
Unit: Habring Chapter 9, “Excursion on Optimal Transport” / “Selingan tentang Transportasi Optimal”

This record is the durable authority, rights, closure, and admission audit for the complete Indonesian Chapter 9 unit. All byte counts, line counts, and SHA-256 values below were recomputed from the live files immediately before this record was written.

## Authority and rights

The authority is Andreas Habring, Lecture Notes: Convex Optimization, arXiv:2607.11664v1, published 2026-07-13. The canonical public landing page is https://arxiv.org/abs/2607.11664v1. The archived arXiv abstract page identifies CC BY 4.0 at http://creativecommons.org/licenses/by/4.0/. The Indonesian unit is a marked derivative, preserves attribution, links the license, identifies its corrections, and expressly disclaims endorsement by Andreas Habring and TU Graz.

| Authority witness | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| authority/habring/source-v1/optimal_transport.tex | 15,378 | 264 | 719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba |
| authority/habring/2607.11664v1-source.tar | 230,116 | — | d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748 |
| authority/habring/2607.11664v1.pdf | 836,977 | — | d2914c741214312d02dc160c5b294eb65a8ac13e484dd9e33aa7ae151f97331d |
| authority/habring/2607.11664v1-api.xml | 1,737 | — | c59dd51fda285214335e2ec00e53f967be44fddca2394ca690c00da70c9dd1d3 |
| authority/habring/arxiv-2607.11664v1-abs.html | 38,042 | 624 | 606022f0531509d4aaab191504c023c9d5c09afac615401f0009f4cc0d33e11b |
| authority/habring/CC-BY-4.0-legalcode.txt | 18,657 | — | 9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411 |

The arXiv API witness names Andreas Habring, title Lecture Notes: Convex Optimization, version 1, category math.OC, and publication timestamp 2026-07-13T15:08:35Z. The extracted source manifest names Convopt_notes.tex as the top-level pdflatex input. Chapter 9 is the complete file optimal_transport.tex, not a reconstruction from the PDF.

## Frozen Indonesian reader components

| Component | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| source/id-ID/habring-09-transportasi-optimal-id.tex | 21,252 | 352 | 45c0eef50b535ffb8722ad74caf4df0bf014f5eebb43d13b24f00639018ca3bd |
| source/id-ID/D90-HAB-09-transportasi-optimal-id.tex | 6,822 | 87 | 1e308a2bed0d1a6f5cdcff09cce932674cf32842a135bc88a5a34bc96c483ff6 |
| source/id-ID/references-ot-id.bib | 306 | 9 | 93611c4b6a753478c51c601e59ef6cd3e290677e2e2d25b104d5d3b74df03126 |
| output/pdf/D90-HAB-09-transportasi-optimal-id.pdf | 498,244 | 15 pages | edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214 |
| qa/D90-HAB-09-transportasi-optimal-id.txt | 30,053 | 549 | 283864c3fc84d414ff721f128a0f10e4b61b4646c0f5edcd53551ee13f911859 |

The wrapper contains the source identity, attribution, CC BY 4.0 notice, change notice, correction appendix, and nonendorsement statement. It includes the target once, supplies the standalone Chapter 7 cross-reference anchor, and binds the unit-local corrected bibliography.

## Reader closure

The strict structural audit proves exact ordered preservation of all 47 source environments:

- aligned 7; cases 3; defn 4; enumerate 1; equation 22;
- figure 1; tikzpicture 1; lemma 1; theorem 2; proof 3;
- quote 1; rem 1.

The five labels are preserved uniquely and in authority order:

1. ot:fig:ot
2. ot:eq:monge
3. ot:eq:K_ot
4. ot:eq:duality
5. ot:eq:disc_entropic

Nine stable segments cover every nonblank authority line exactly once:

| Segment | Authority lines |
|---|---:|
| d90.hab.v1.ch09.seg0001 | 1–15 |
| d90.hab.v1.ch09.seg0002 | 16–75 |
| d90.hab.v1.ch09.seg0003 | 77–110 |
| d90.hab.v1.ch09.seg0004 | 112–130 |
| d90.hab.v1.ch09.seg0005 | 131–141 |
| d90.hab.v1.ch09.seg0006 | 142–190 |
| d90.hab.v1.ch09.seg0007 | 192–226 |
| d90.hab.v1.ch09.seg0008 | 229–256 |
| d90.hab.v1.ch09.seg0009 | 257–264 |

The intervals cover 259 distinct lines. The remaining five authority lines are blank. There are no uncovered nonblank lines, multiply covered lines, or out-of-bounds markers. The figure remains native TikZ; the sole target-only resizebox is a disclosed layout wrapper and does not alter the figure content.

Reference topology is preserved. The target adds one deliberate reference to ot:eq:disc_entropic when stating Sinkhorn convergence and one deliberate Villani Theorem 5.10 citation when disclosing the nonformal strong-duality step. Three footnotes and fourteen OT glossary surfaces are retained.

## Corrections and adverse ledger

The exact twelve-record content proposal is qa/CHAPTER09_PROPOSED_LEDGER.jsonl: 8,840 bytes, 12 lines, SHA-256 643fde3fbe1409732ef2df8fdef52465e4df7a583fd9bbeb2137a6122f548add. All thirteen events below are present byte-exactly in 00_control/ADVERSE_LEDGER.jsonl, whose live identity at this boundary is 58,370 bytes, 99 records/lines, SHA-256 09a982c3e91f83655150f7ae29a6351cb071558ed14a36cbb3701d7f43e9d824.

| Event | Audited surface |
|---|---|
| O015-HAB-ADV-0084 | Measurable spaces, push-forward, Monge, and coupling domains |
| O015-HAB-ADV-0085 | Signed, finite, and nonnegative measure definitions and notation |
| O015-HAB-ADV-0086 | Monge objective, measurability, feasibility, infimum, and empty-feasible-set convention |
| O015-HAB-ADV-0087 | Euclidean scope and one-way atomlessness implication in the Monge example |
| O015-HAB-ADV-0088 | Polish/Borel hypotheses, tightness, Prokhorov compactness, and existence |
| O015-HAB-ADV-0089 | Metric-space and finite-moment scope of Wasserstein-p |
| O015-HAB-ADV-0090 | Bounded-continuous Kantorovich dual classes and pointwise constraint |
| O015-HAB-ADV-0091 | Marginal separation, correct nonnegative-measure domain, and strong-duality justification |
| O015-HAB-ADV-0092 | Vector simplex types and dimensioned rectangular matrix marginals |
| O015-HAB-ADV-0093 | Finite costs, epsilon positivity, entropy domain, and zero-log-zero convention |
| O015-HAB-ADV-0094 | Existence, strict convexity, interior positivity, KKT factorization, and scaling uniqueness |
| O015-HAB-ADV-0095 | Positive initialization, complete indexing, well-defined Sinkhorn updates, plan convergence, and gauge ambiguity |
| O015-HAB-ADV-0096 | Villani bibliography author metadata and rendered name |

Event 0096 is wrapper-only and therefore is not a formula-delta event. The frozen upstream bibliography is authority/habring/source-v1/references.bib: 614 bytes, SHA-256 e334d49a9df665d3cb5902f8874a24e44be601f26fafb07fa21406690e473f20. Its Villani record says “Villani, Cédric and others”, although the book is sole-authored. The source file remains unchanged. The unit-local bibliography names Cédric Villani alone and adds DOI 10.1007/978-3-540-71050-9. Springer’s official record confirms the sole author, title, series volume 338, publisher, and DOI: https://link.springer.com/book/10.1007/978-3-540-71050-9.

## Structural, formula, mathematical, and solver admission

| QA artifact | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| qa/audit_optimal_transport_unit.py | 44,280 | 1,223 | 5c4c030ac4512a0b0785053c19b5ed2eb1a6d35bb4147cac6fe8842807c43a5c |
| qa/OPTIMAL_TRANSPORT_STRUCTURE_REPORT.json | 19,924 | 826 | eb8b194c01dd7610dcdb7325322765ab16b3ec9cf907d28f9463fa11692767aa |
| qa/OPTIMAL_TRANSPORT_FORMULA_DELTA_MANIFEST.json | 79,141 | 2,508 | 796e13fbf1f221139f0233d30b2464dfb026027eb5b9ce44b66b58c2f2e169ef |
| qa/validate_optimal_transport_unit.py | 26,029 | 630 | e574ea3e7f924a3d1becb148162faec27ae715040665b06def284f11990500c0 |
| qa/OPTIMAL_TRANSPORT_SOLVER_RESULTS.json | 16,970 | 698 | 4f751c615f2d7f03622b1447b3985ad1d660bd4f758cf4c4fb61d4d384b4e7a0 |

The strict audit passes twice byte-identically with zero failures. It inventories 162 authority and 232 target formula surfaces in 35 delta blocks, 34 substantive. Every substantive delta is bound to the exact proposed and integrated event set O015-HAB-ADV-0084 through O015-HAB-ADV-0095; there are no unused required events, unbound blocks, or incomplete proposal/integration bindings.

The deterministic solver receipt is PASS, 41/41 gates, with four negative controls. It verifies:

- a rectangular 3 by 4 finite OT primal/dual pair with objective 0.575 and zero duality gap;
- the Wasserstein-2 special case W2 squared = 3 and W2 = 1.7320508075688772;
- a positive entropic 3 by 4 Sinkhorn plan in 27 iterations, maximum row residual 3.608224830031759e-15, column residual zero, factorization residual zero, and KKT stationarity residual zero;
- strict-convexity and scaling-ambiguity witnesses;
- failures of the source’s scalar-simplex typing, undimensioned rectangular ones vectors, malformed transposed marginal, and unrestricted logarithmic entropy domain.

The final independent source/target and changed-surface rereview has P1=0, P2=0, P3=0. It specifically reconfirmed the clarified minimizing-sequence wording, the exact indicator-supremum explanation, and the completed ratio proof for uniqueness of the Sinkhorn scaling pair.

## Build, visual, text, and accessibility evidence

Two fixed-epoch builds produced identical PDF bytes:

| Build artifact | Bytes | Lines/pages | SHA-256 |
|---|---:|---:|---|
| build/habring-unit-09-id/D90-HAB-09-transportasi-optimal-id.pdf | 498,244 | 15 pages | edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214 |
| build/habring-unit-09-id-repro/D90-HAB-09-transportasi-optimal-id.pdf | 498,244 | 15 pages | edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214 |
| build/habring-unit-09-id/D90-HAB-09-transportasi-optimal-id.log | 103,255 | 2,456 | 2b083221c49f6fbdede8f541e68cd9129632a74168d7855c1ddc14c1bf48b3a4 |
| build/habring-unit-09-id-repro/D90-HAB-09-transportasi-optimal-id.log | 103,297 | 2,456 | 42e765bd3c94d9ac91b3c88974ecf093d18d027eae41ff08e7b8c4fe2085629d |

The deterministic epoch is SOURCE_DATE_EPOCH=1783900800, equal to 2026-07-13T00:00:00Z; FORCE_SOURCE_DATE=1 and TZ=UTC were also set. The retained build used pdfTeX 1.40.29 / MiKTeX 26.5, LaTeX2e 2025-11-01, latexmk 4.88, and Biber 2.21. The exact command, run from source/id-ID, was:

    latexmk -gg -pdf -interaction=nonstopmode -halt-on-error -file-line-error "-outdir=C:\Users\Floris\Documents\interlanguage\04_mirrors\id\advanced-optimization-convex-analysis-id\build\habring-unit-09-id" D90-HAB-09-transportasi-optimal-id.tex

The reproducibility run differed only by the output directory habring-unit-09-id-repro. The final logs contain no TeX error, undefined control sequence, unresolved citation/reference, missing glyph, overfull/underfull box, or rerun request. Remaining notices are inherited Indonesian locale/bibliography fallbacks.

All 15 final pages were rendered at 120 dpi to 993 by 1,404 pixel PNGs and inspected in the 1,332 by 3,090 contact sheet tmp/pdfs/ch09-final-edc8e17f/contact.png: 3,150,077 bytes, SHA-256 b0df2bf4db063d84dc370767b999a3eca2e250360f258d37d395eec2e531b93b. Formula-heavy duality page 8, entropic/KKT page 10, and correction page 13 were inspected full size. No clipping, collision, blank content page, broken glyph, unreadable formula, or running-header defect remains.

The PDF is A4, PDF 1.5, unencrypted, searchable on every page, and declares catalog /Lang id-ID. All 19 font resources are embedded, subset, and expose Unicode mappings. Regenerating text in memory with:

    pdftotext -layout -enc UTF-8 output/pdf/D90-HAB-09-transportasi-optimal-id.pdf -

produced 30,053 bytes with SHA-256 283864c3fc84d414ff721f128a0f10e4b61b4646c0f5edcd53551ee13f911859, exactly equal to the retained QA text file.

## Admission and remaining gaps

Chapter 9 is admitted as a complete, contiguous Indonesian reader unit. Mathematical, structural, formula, computation, build, visual, text, attribution, license, and nonendorsement gates pass.

Remaining limitations are explicit:

- the PDF is untagged and has no MarkInfo structure tree, so PDF accessibility is pass-with-limitation despite searchable text, Unicode font mappings, and /Lang id-ID;
- no independent human/native-speaker Indonesian language review is recorded; the final independent model rereview is P1=P2=P3=0 but does not replace that review;
- no HTML or EPUB reader has yet been built, so reflowable, browser-native, and interactive/accessibility surfaces remain future work;
- publication and public-byte readback are outside this admission record.

Next production cursor: Penn State Math 555 Chapter 3, authority/penn-state/source/ClassNotes/Section3.tex, 41,715 bytes, 608 lines, SHA-256 d4ae6142e2366b12575eafddc833df067518af114e9816187668cc367be43010.
