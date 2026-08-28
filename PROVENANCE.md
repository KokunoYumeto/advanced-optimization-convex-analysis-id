# Provenance and contributor roles

This repository contains an independent Bahasa Indonesia translation/edition, bounded source-derived supplements, independently authored connective and assessment material, computational checks, stable-record exports, and reader builds. It does not replace or obscure source authorship. There is **no blanket license** for the repository; `RIGHTS.md` and `00_control/COMPONENT_RIGHTS.csv` control rights per component.

## Canonical source spine

The canonical editable spine is Andreas Habring's complete preface and Chapters 1--9 of *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1, under CC BY 4.0. The frozen source tar and its exact identity are recorded in `00_control/SOURCE_AUTHORITY.json`. The source acknowledges Thomas Pock as the antecedent for the lecture slides and uses Christian Clason's template/scaffolding; those relationships remain credited. The Indonesian files are disclosed translations/adaptations with separately logged corrections.

## Bounded structured supplements

Stephen Becker is the source author/copyright holder for the admitted material from `convex-optimization-class`; Mitchell Krock is credited for the typed `TypedNotes/APPM5720Notes.tex`. Only commit `98ed6930084c435ba0f675f7646ced1f2fd8729e` and the exact audited ranges are used: Becker-01 lines 1263--1321, 1398--1405, 1414--1499, 1652--1726, and 1731--1743; Becker-02 lines 2750--2797; Becker-03 lines 2971--2988. The MIT-licensed donor wording and source witnesses remain distinct from the independent Indonesian translation, corrections, connective prose, exercises, hints, and solutions under CC BY-SA 4.0. Inherited Boyd/Vandenberghe, Bertsekas, Bauschke/Combettes, Lions/Mercier, and other mathematical attributions are retained where applicable.

## Independent completion layer

Original-01, Original-02, and Original-03 are independently authored CC BY-SA 4.0 components. Original-03 provides the prerequisite diagnostic, six problem sets, solved midterm and final, staged hints and full solutions, seven proof rubrics, two additional deterministic laboratories, and the seven-milestone composite inverse-problem capstone. Mathematical publications and source books consulted as checking witnesses are not edition sources unless a component record explicitly says otherwise; no witness prose, layout, exercise, figure, solution, or code is silently imported.

## Separate companion corpus

Dimitri P. Bertsekas's MIT OpenCourseWare 6.253 material, Clément W. Royer's stochastic-gradient material (including retained A. Gramfort and Robert Gower notebook credits), and Christopher Griffin's Penn State MATH 555 material (including credited Simon Miller and Douglas Mercer contributions) are preserved as separately licensed companions. They are not inputs to the canonical integrated reader. Athena Scientific figure bytes/layouts are excluded absent a separate reusable grant.

## Production, correction, and verification record

Translation, semantic reconstruction, independent connective writing, assessment authoring, backend generation, and mathematical/computational QA were assisted by **OpenAI Codex gpt-5.6-sol, Ultra**, acting at the repository user's direction. The system is not a source author, licensor, institutional representative, or substitute for the credited human authors and contributors. Exact source locators, changes, corrections, and independent-authorship boundaries are recorded in `00_control/SOURCE_AUTHORITY.json`, `00_control/COMPONENT_RIGHTS.csv`, and `00_control/ADVERSE_LEDGER.jsonl`.

Independent human/native-speaker review has not been recorded. That fact is disclosed as a quality limitation, not used as a publication hold. No endorsement, review, approval, sponsorship, or affiliation by Habring, Becker, Krock, MIT, Penn State, Université Paris Dauphine-PSL, arXiv, Athena Scientific, or any other source author or institution is implied.

## Curriculum boundary

O018 retains LP/MIP, simplex/tableau mechanics, finite-LP duality/complementary slackness/sensitivity, network/discrete optimization, and general operations-research workflow/tooling. O015 admits probability-simplex constraints, general KKT conditions, and value sensitivity only as continuous-convex topics. No O018 prose, exercise, solution, code, or stable ID is imported.
