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
