# O015 coverage and overlap boundary

Date: 2026-08-22  
Role: D90 — Advanced Optimization and Convex Analysis  
Current architecture: MIT OCW 6.253 + Royer stochastic-gradient core; Penn/Habring preserved companion

## Selected D90 primary architecture

The primary course spine is the complete MIT OpenCourseWare 6.253 *Convex Analysis and Optimization* teaching package under CC BY-NC-SA 4.0. It supplies convex geometry and functions, separation, conjugacy, convex/Fenchel/conic duality, optimality, subgradient calculus, conic and semidefinite programming, descent, cutting-plane, bundle, proximal, augmented-Lagrangian, interior-point, incremental/randomized, projection, and complexity material. The selected stochastic component is Clément Royer's complete 45-page *Optimization for Machine Learning -- Stochastic Gradient* notes plus both public notebook laboratories under CC BY-NC 4.0.

Four independently authored bridge units close the documented gaps: nonlinear KKT/constraint qualifications/sensitivity; variational inequalities and monotone inclusions; stochastic approximation beyond basic SGD; and modern open-solver certificates, diagnostics, failure modes, and reproducibility. Four reproducible open-source laboratories, 36 new route-mastery problems with hints and complete solutions, published-solution repairs, and a cumulative capstone provide the required self-study closure. Component rights remain distinct.

The exact controlling architecture and learner route are frozen in `O015_PRIMARY_ARCHITECTURE_PIVOT_20260822.md` and its verified upstream handoff. The complete first-topic pilot for source pages 2--5 now passes the fail-closed PDF-to-semantic-source gate: complete page/item mapping, exact formula/list topology, stable IDs, two byte-identical HTML/PDF builds, measured desktop/mobile reflow and accessibility, terminology QA, independent rereview, and zero admitted Athena figure bytes. MIT translation may therefore continue in source order under the same per-boundary gate; this is not permission for lossy OCR or weaker later reconstruction.

## Preserved Penn/Habring companion

Habring Chapters 3--9 and Penn Chapters 3--5 form an admitted optional numerical/modern-algorithm companion. They retain every existing file, stable ID, correction event, attribution, component license, QA receipt, and public-history identity. They are not deleted, renumbered, silently merged into the selected primary spine, or counted in the selected D90 core-page total.

The companion supplies subgradients, projected subgradient descent, proximal methods, acceleration, Fenchel duality/primal--dual methods/ADMM, stochastic gradient descent, optimal transport, smooth line search, convergence, Newton, globalization, and modified-Cholesky correction. Habring remains CC BY 4.0. Penn-derived text and figures remain CC BY-NC-SA 3.0 United States. Fourteen Penn Maple/legacy listing inputs encountered through Chapter 5 remain excluded because their reusable rights are unclear/external; reader roles are replaced by independently authored pseudocode registered separately inside the combined derivative.

The completed Penn Chapter 6 candidate is preserved but unadmitted. No automatic Penn source-order expansion continues after the Chapter 5 preservation boundary. Further companion admission requires an explicit later decision and is not a prerequisite for D90.

## O018 exclusion boundary

O018 / D130 owns LP/MIP modelling, simplex and tableau mechanics, finite-dimensional LP duality and complementary slackness, LP sensitivity, network/discrete optimization, general operations-research workflows, and introductory solver tooling. D90 may use open solvers to study convex, nonsmooth, variational, and stochastic behavior but does not retranslate O018's course.

Consequences:

- Penn Chapter 9 remains excluded.
- Penn's general preliminaries are not repeated unless a narrow local prerequisite is indispensable.
- MIT conic/Fenchel duality, KKT-equivalent optimality, nonsmooth methods, and variational bridges remain in D90 because they are materially distinct from O018's LP/MIP curriculum.
- General solver usage is not a second OR course; D90 laboratories are restricted to certificates, convex/nonsmooth/stochastic diagnostics, and reproducible failure analysis.
- MO-book application notebooks remain reference material; no printed-book rights are inferred from a repository license.

## Exact selected-source accounting

- MIT external teaching package: 395 pages across 13 PDFs: 340 lecture-note pages, 16 homework-question pages, 33 homework-solution pages, and six midterm/solution pages.
- Royer external component: 45 note pages plus two public notebook-source laboratories.
- Selected D90 external source count: 440 pages.
- Penn/Habring companion: preserved but contributes zero pages to the selected D90 core count.

MIT has 27 numbered homework problems with paired solutions and four top-level midterm problems; one published solution contains a literal incomplete placeholder and must be repaired in a separately authored layer. Royer has three formal solved exercises. Every prompt, subpart, solution, omission, and new mastery item must receive stable problem/solution and source-page identities.

## Nonclaims and stop rules

Do not claim editable mathematical TeX for MIT or Royer: both selected mathematical surfaces are currently PDF-derived, while the MIT repository is OCW/Hugo metadata rather than the mathematical source. Do not use lossy OCR, Athena figure bytes/layout, a blanket repository license, systematic solutions not actually present, complete human Indonesian review, tagged PDF, or completed semantic HTML/EPUB unless separately proved.

The earlier three-candidate comparator supported Penn/Habring as an editable production choice, but the later full-course curriculum decision superseded it for the primary spine because that composite lacks a complete solved KKT/variational/stochastic course arc. The bounded search is closed. The preceding sentence's production-cursor wording is historical: the exact page 6--13 block, “Duality” through “Exceptional Behavior,” is now admitted, and page 14 starts the next topic. This remains a production cursor, not another inventory loop.

## MIT L02 boundary admitted (2026-08-23)

Pages 6--13 are now a bounded admitted semantic reader unit. The block covers
Fenchel/conjugate duality, geometric min-common/max-crossing duality, the
abstract framework, and exceptional nonclosed behavior. It is additive to the
MIT pages 2--5 pilot and does not duplicate O018's LP/MIP, tableau, network, or
operations-research workflow. The preceding L02 statement that page 14 was
excluded is historical; page 14 is now admitted by the L03 section below, and
page 15 is the next source cursor.

The exact closure is 8 pages, 19 top-level items, 7 nested lists, 4 display
formulas, 2 examples, 1 answered prompt, 1 source-display, and 61 target
MathML nodes. Seven source graphics are Athena Scientific permission-gated;
none is copied as an image byte, crop, or layout. Page-addressed semantic
descriptions preserve the mathematical labels and relationships. The MIT
component remains CC BY-NC-SA 4.0 with its own attribution, change marking,
NC/SA obligations, and non-endorsement. The source boundary has no exercises,
hints, solutions, or interactives, so those remain a documented learner gap.

The unit's source, witness, HTML, PDF, and QA identities are controlled in
`CURRENT_STATE.md` and `BUILD_AND_QA.md`; validation returns `errors=[]` and
the deterministic/browser/visual/rereview gates pass. Remaining curriculum
gaps are the untranslated MIT/Royer pages, original bridges, laboratories,
mastery/solution layer, capstone, semantic EPUB, tagged PDF, and human
Indonesian review. No final-corpus or complete-course claim is permitted.

## MIT L03 page-14 boundary admitted (2026-08-23)

Page 14, “Modern View of Convex Optimization,” is now an admitted one-page
semantic reader unit following the L02 duality block. It records the source's
traditional/modern framing and remains distinct from O018's LP/MIP, tableau,
network, and operations-research workflow. Page 15 is the next source cursor.

The exact closure is 2 top-level items, 6 nested bullets, 2 source-figure
surfaces, zero display formulas, and zero copied image bytes. Both Athena
Scientific permission-only graphics are represented by page-addressed semantic
descriptions retaining labels and mathematical relationships. The MIT component
remains CC BY-NC-SA 4.0 with its own attribution, change marking, NC/SA
obligations, and non-endorsement. No exercises, hints, solutions, code, or
interactive surface occurs in this boundary, so none is claimed.

The source, witness, target, HTML, PDF, validation, browser, and rereview
identities are controlled in `CURRENT_STATE.md` and `BUILD_AND_QA.md`; all
bounded gates pass. The corrected Zenodo record `10.5281/zenodo.22071030` is
the current public L02 preservation baseline, not silent publication evidence
for L03. Remaining gaps are the untranslated source pages, original bridges,
laboratories, mastery/solution layer, capstone, semantic EPUB, tagged PDF, and
human Indonesian review.

## MIT L04 page-15 boundary admitted; live browser QA pass (2026-08-23)

Page 15, “The Rise of the Algorithmic Era,” is now an admitted local semantic
reader unit following L03. It remains distinct from O018's LP/MIP, tableau,
network, and operations-research workflow. Page 16 is the next source cursor.

The exact closure is 1 page, 6 top-level items, 12 nested bullets, 1 inline
math surface, zero display formulas, zero figures, and zero copied image bytes.
The MIT component remains CC BY-NC-SA 4.0 with attribution, change marking,
NC/SA obligations, and non-endorsement. No exercises, hints, solutions, code,
or interactive surface occurs in this boundary, so none is claimed.

The source, witness, target, HTML, PDF, validation, browser, visual, and
rereview identities are controlled in `CURRENT_STATE.md` and `BUILD_AND_QA.md`.
The validator and live browser result are `pass`; desktop 1280×720 and mobile
390×844 reflow checks report no horizontal overflow or console findings, with no
duplicate IDs, unresolved fragments, or images. Zenodo publication is pending
after HTTP 504; no L04 public DOI or public-byte claim is made. Remaining gaps
are later source pages, original bridges, laboratories, mastery/solution layer,
capstone, semantic EPUB, tagged PDF, and human Indonesian review.

## L04 final gate and page-16 batch correction (2026-08-23)

The earlier L04 browser limitation is superseded: live desktop/mobile browser
QA and the corrected validator both pass. L04's backend is frozen at 1,543
records, adding 48 to the protected 1,495-record baseline; exact bytes, hashes,
and validator receipts are bound in `CURRENT_STATE.md` and `BUILD_AND_QA.md`.
This does not change the overlap boundary: the material remains historical and
conceptual convex-optimization framing, not O018's LP/MIP, tableau, network, or
operations-research workflow.

L03 is separately public at DOI `10.5281/zenodo.22071175`, with 40 files and an
11,373-byte anonymous readback SHA-256
`3d3a22a371eb267915f19773e8d4fc94b482840d808a46b0b376e98518ad8822`.
The L04 HTTP 504 attempt produced no public L04 record, and no standalone L04
release is planned. Page 16 begins the next coherent multi-page section/batch;
coverage, overlap, rights, QA, backend, and preservation are evaluated once at
that batch boundary. Remaining gaps are later MIT/Royer material, original
bridges, laboratories, mastery/solution coverage, capstone, semantic EPUB,
tagged PDF, and human Indonesian review.

## MIT L05 pages 16–19 admitted; Lecture 2 draft remains outside coverage (2026-08-23)

Pages 16–19 close the course-orientation material as one admitted L05 boundary:
methodological trends, course outline, expectations, and the note on slide use.
This is historical and curricular framing for convex analysis and optimization,
not O018's LP/MIP modelling, simplex/tableau, finite LP duality/sensitivity,
network, discrete-optimization, or general operations-research workflow. The
closure has 16 top-level items, 26 nested bullets, two source URIs, zero formula
surfaces, zero figures, and no exercises, solutions, code, or interactivity.
`O015-MIT-SEM-0004` is admitted as a disclosed correction of the printed author
surname, with its immutable 642-byte snapshot bound to SHA-256
`c701e631c4839aa07a2f8a4b8e8f026394c66bd709ffa37318431bbc461e1595`.

All L05 reader, browser, visual, rereview, rights, and backend gates pass; the
1,605-record backend adds 62 records to the exact protected 1,543-record L04
baseline. Exact artifact identities are controlled in `CURRENT_STATE.md` and
`BUILD_AND_QA.md`. No standalone L04 Zenodo version exists. The combined
L04+L05 Zenodo checkpoint and the GitHub push containing L05 are pending, so
the local L05 bytes are not represented as public here.

The next coherent production boundary is complete Lecture 2, pages 20–28. Its
9,962-byte census (SHA-256
`fc0cb5b863652aa810ed765f247a248be1510cd61f240277b896e605a41b3ea4`)
freezes the batch and its separation from page 29, which begins Lecture 3. The
Lecture 2 witness and Indonesian target are drafts only: they are unadmitted and
their build/QA is in progress, so they do not yet enlarge admitted coverage.
Remaining gaps are later MIT/Royer material, original bridges, laboratories,
mastery/solution coverage, capstone, semantic EPUB, tagged PDF, and human
Indonesian review.

## MIT L06 complete Lecture 2 admitted; L07 remains outside coverage (2026-08-23)

Pages 20–28 now enlarge admitted primary coverage with mathematical
conventions; convex sets and functions; extended-real functions, epigraphs and
effective domains; lower semicontinuity and closedness; proper/improper convex
functions; and basic convexity-preserving constructions. This is convex-
analysis foundation, not O018's finite LP/MIP, simplex/tableaux, LP
duality/sensitivity, network, or discrete-optimization workflow.

The closure has 32 top-level items, 17 nested items, 12 display formulas, five
text-only figure descriptions, zero copied graphics, and no exercise/solution,
code, or interactive surface. All reader, rights, formula, visual, browser,
rereview, and 1,714-record backend gates pass. Exact identities are controlled
in `CURRENT_STATE.md` and `BUILD_AND_QA.md`.

Lecture 3 pages 29–38 are prepared as the next coherent batch but remain
outside admitted coverage until their Indonesian reader and consolidated gate
pass. Page 39 begins Lecture 4. Remaining gaps include later MIT/Royer
material, bridges, laboratories, mastery/solution coverage, capstone,
accessible EPUB/tagged PDF, and optional human-review evidence; the latter is
not a hold.

## MIT L07 complete Lecture 3 admitted; page 39 remains outside coverage (2026-08-24)

Pages 29–38 now add differentiable convex functions, first-order optimality,
Euclidean projection, Hessian tests, convex and affine hulls, Caratheodory's
theorem and proof, and compactness of the convex hull of a compact set. This is
advanced convex-analysis foundation and does not duplicate O018's finite
LP/MIP, simplex/tableau, LP duality/sensitivity, network, or discrete-
optimization workflow.

The admitted closure has ten pages, 16 top-level items, 14 nested items, 13
display formulas, four semantic figure descriptions / six panels, zero copied
graphics, and no exercise, solution, code, or interactive surface. Reader,
rights, formula, browser, visual, independent-rereview, and 1,820-record
backend gates all pass. Page 39 begins Lecture 4 and remains outside admitted
coverage until its coherent multi-page boundary is frozen, translated, and
validated. Remaining gaps are later MIT/Royer content, bridges, four labs,
mastery/solution coverage, capstone, semantic EPUB, tagged PDF, and optional
human-review evidence; the latter is not a hold.
