# Rights and provenance — integrated O015/D90 edition

This release has no blanket license. The following two controlling records are reproduced verbatim from the release candidate.

# Component rights and attribution

This mixed-source repository has **no blanket license**. Rights attach to each source relationship and file as recorded in `00_control/COMPONENT_RIGHTS.csv`; inclusion in one reader or release does not relicense another component.

## Canonical Habring spine

The canonical structured-source spine is the complete preface and Chapters 1--9 of Andreas Habring, *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1. The frozen source tar is 230,116 bytes, SHA-256 `d9a22d09d0245bd7bfe4d162dab6ea4bb77552c6cec9e41820db7861b45b6748`. The source and the Indonesian translation/adaptation are handled under Creative Commons Attribution 4.0 International (CC BY 4.0). Attribution, source and license links, translation/change notices, and non-endorsement are retained. The Habring source's ShinyBook/template and macro scaffolding remains under that same source license.

License: https://creativecommons.org/licenses/by/4.0/

## Bounded Becker/Krock supplements

The only admitted Becker donor is Stephen Becker's `convex-optimization-class` repository at commit `98ed6930084c435ba0f675f7646ced1f2fd8729e`, tree `f04670e3f7be3d4836c380fd8bd31883e0b992c9`, specifically Mitchell Krock's typed `TypedNotes/APPM5720Notes.tex`. The exact admitted donor ranges are Becker-01 lines 1263--1321, 1398--1405, 1414--1499, 1652--1726, and 1731--1743; Becker-02 lines 2750--2797; and Becker-03 lines 2971--2988. Donor text and its source witnesses retain the MIT License and the Becker/Krock attribution plus inherited source credits.

LP-specific ranges 1322--1397, 1406--1413, and 1727--1730, adjacent material, the broken alternate master, unavailable Canvas-only solutions, and archive-absent figures are excluded. The Indonesian translation, disclosed corrections, connective prose, independently written exercises, hints, and solutions are a separate CC BY-SA 4.0 layer. The MIT donor license is not represented as licensing that independent wording, and CC BY-SA 4.0 is not represented as relicensing the donor.

MIT License: https://opensource.org/license/mit/

Independent layer: https://creativecommons.org/licenses/by-sa/4.0/

## Independently authored Original-01, Original-02, and Original-03

Original-01, Original-02, and Original-03 are independently authored course-completion layers under CC BY-SA 4.0. They cover the stochastic-composite/mirror/minibatch bridge; variational inequalities, maximal monotonicity, resolvents, and splitting; and the cumulative assessment, proof rubrics, complete solutions, two further laboratories, and capstone. The corresponding deterministic code and generated result surfaces are identified separately in the component ledger. Mathematical references used as verification witnesses do not contribute copied prose, layout, exercises, figures, solutions, or code.

The Habring-derived scaffold embedded around an original unit remains CC BY 4.0. The original substantive wording does not change the rights of Habring or Becker source material. Exact changes and mathematical corrections are disclosed in `00_control/ADVERSE_LEDGER.jsonl`.

License: https://creativecommons.org/licenses/by-sa/4.0/

## Separately licensed companions

MIT OpenCourseWare 6.253, Clément W. Royer's stochastic-gradient notes/labs, and Christopher Griffin's Penn State MATH 555 material remain separate companion readers or witnesses and are not inputs to the integrated book.

- MIT OCW 6.253 / Dimitri P. Bertsekas: CC BY-NC-SA 4.0. The source title page's Athena Scientific figure-permission statement is not treated as a sublicensable adaptation grant; no Athena figure byte or copied layout is admitted.
- Royer: CC BY-NC 4.0. The notebooks retain their embedded A. Gramfort and Robert Gower credits; independently authored completions are not imputed to the source.
- Penn State MATH 555 / Christopher Griffin: CC BY-NC-SA 3.0 United States. Excluded Maple and legacy-code text is not redistributed; independent pseudocode replacements retain their own provenance.

Companion rights never flow into the Habring/Becker/Original integrated reader, and the integrated reader's licenses never overwrite companion rights.

## Scope and non-endorsement

O018 material on LP/MIP, simplex/tableau mechanics, finite-LP duality/complementary slackness/sensitivity, network/discrete optimization, and general operations-research workflow/tooling is excluded from O015. Probability-simplex constraints, general KKT conditions, and value sensitivity remain admissible continuous-convex topics. Comparator sources are evidence only. No endorsement, review, approval, sponsorship, or institutional representation by any source author, publisher, university, arXiv, or other source organization is implied.

---

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
