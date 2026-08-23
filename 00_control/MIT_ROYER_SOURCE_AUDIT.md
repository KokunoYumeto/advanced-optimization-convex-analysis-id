# MIT OCW 6.253 and Royer source audit

Date: 2026-08-22  
Lane: O015 / D90 Advanced Optimization and Convex Analysis  
Disposition: admitted with declared conversion, figure-rights, and solution-completeness gates

## Result

The selected 440-page external core is lawfully and reproducibly frozen: 395 nonredundant MIT teaching pages plus 45 Royer note pages. The machine freeze at `MIT_ROYER_SOURCE_FREEZE.json` is 40,468 bytes, SHA-256 `a0a4c53273b9358b90289182b185aca1370d89a9388779c77413ab852fbf99c5`. Two complete reruns of `qa/freeze_mit_royer_authority.py` reproduced those bytes exactly. Admission is a qualified pass, not a claim of editable mathematical TeX or complete learner-answer closure.

## MIT OpenCourseWare 6.253

Authority is the official Spring 2012 MIT OpenCourseWare course, lecture-note, assignment, exam, download, and terms surfaces. The official metadata repository is frozen at commit `58d7c86195f09dd8708b84dde28205d3199207dd`, tree `26d3136df9d5d7f564f0b1d068ec8d7a7c8818d6`; the observed `main` branch pointed to that commit on 2026-08-22. Its 54 tree entries are six directories and 48 blobs: 46 Markdown files, one JSON file, and one YAML file. It contains no mathematical PDF, TeX, figure source, or mathematical build definition, so it must not be described as an editable mathematical-source repository.

The official offline archive is 41,452,759 bytes, SHA-256 `32e241f7101943e285c8b56ca61ae117b647d67015ff8b1048ab598319d7389f`. It has 412 entries, 344 files, 69,160,743 uncompressed bytes, no duplicate or unsafe paths, and byte-identical extracted members. Its 39 PDFs include 25 redundant per-lecture copies and the excluded 59-page Athena Scientific summary. The nonredundant teaching closure is exactly 13 PDFs / 395 pages / 10,417,664 bytes:

- complete lecture notes: 340 pages / 8,030,116 bytes / SHA-256 `41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181`;
- five homework prompt sets: 16 pages;
- five paired homework solution sets: 33 pages;
- two midterms with solutions: 6 pages.

The assignments surface states that the five homework sets are from the Spring 2010 version of the course. The Spring 2012 midterm solution contains the literal omission “(a) To be added.” Any repair is an independently authored solution component, never silently attributed to MIT.

Rights are CC BY-NC-SA 4.0: attribution, license link, change identification, noncommercial use, ShareAlike, no added restrictions, MIT name/logo restrictions, and no implied endorsement. The complete-notes title page states that every figure is courtesy of Athena Scientific and used with permission. That statement is not treated as a sublicensable adaptation grant. The 59-page *Convex Optimization Theory, Athena Scientific: A Summary* is a third-party, permission-ambiguous component and is excluded. No Athena figure byte, distinctive layout, summary page, or external chapter may enter the Indonesian derivative unless separate reusable rights are proved; necessary mathematics is independently redrawn from primitives under a separate rights record or omitted with an exact locator. This audit proves the source-side restriction and that pilot pages 2--5 contain no figures; output-side compliance is checked separately for every derivative artifact.

The first fail-closed semantic-source pilot is the complete topic “The Role of Convexity in Optimization,” complete-notes PDF pages 2--5. Page 6 cleanly begins “Duality.” The boundary contains no figures, theorem/proof/exercise split, or dangling formula. Admission of the wider source depends on page/segment completeness, stable IDs and page maps, formula/topology checks, two independent reconstructions, deterministic semantic HTML/PDF, and accessible navigation/math.

## Clément W. Royer stochastic-gradient component

Authority is Clément W. Royer's official course page and its active files. The page is 6,381 bytes, SHA-256 `7b03656d07edf4bdb7b524ff20a41d06511a23e0b75a04cdaff309ab0817f88c`. It declares materials on the page under CC BY-NC 4.0: attribution, license link, change identification, noncommercial use, no additional restrictions, and no implied endorsement; no ShareAlike condition applies to this component.

The selected notes are 684,631 bytes / 45 pages / SHA-256 `3290c61e870ef807ae92c4ace309449ee46ab3aa544e033c100f4a005311dfd3`. They are PDF-only despite LaTeX production metadata. They contain three formal exercises and three complete appendix solutions, with no hints. Exercise 3 is titled “Batch methods,” while its solution heading says “Practical stochastic gradient variants”; the solution mathematics answers the batch-method prompt, so the heading mismatch is recorded rather than treated as a missing solution.

The laboratory archives are safely extracted and byte-bound:

- Lab 1 ZIP: 382,975 bytes / SHA-256 `88e18ea096b87bd12d182072bfbf6fd12ac73d666e16911a3f015ee9a574d461`; notebook 591,695 bytes / 55 cells / SHA-256 `a40429fd34995a055bf1421cde8cc0d7c6a44bbe971107460ab16548152e847b`.
- Lab 2 ZIP: 371,793 bytes / SHA-256 `0a0a908157dcf07f0dd3874c118e416dad3033a5f04f9cb37ae248b2f8feb623`; notebook 529,952 bytes / 53 cells / SHA-256 `b9a9f791b679307f1f3c0fa77c32cd238a303ea7e36f338f4bea463e9782c319`.

Lab 1 is substantially executed: all code-cell execution counts are non-null and no error output is embedded. Lab 2 is not answer-complete: four discussion cells after Questions 1--4 are unanswered, four answer code cells are empty, and the optional Momentum/Adam section is unimplemented. Five code cells have null execution counts, but the fifth is only a version-footer cell; no error output is embedded. The notebooks have no pinned environment, and the legacy SciPy import requires modernization. Embedded credits to A. Gramfort and Robert Gower are preserved. The three virtual-board PDFs are supplementary witnesses and contribute zero pages to the selected 440-page core.

The freeze script asserts byte/archive/PDF/notebook closure mechanically. Its human-readable rights, gap, exercise, and pilot-boundary statements are constants, so those claims were also independently checked against the saved official pages and source contents rather than inferred from a successful script run.

## Production consequence

MIT supplies the primary convex-analysis, duality, conic, nonsmooth, and algorithm spine; Royer supplies the bounded stochastic-gradient arc. Their licenses and attribution stay component-distinct. The PDF-only mathematical sources make semantic reconstruction a real production cost, while the complete notes, paired assignments/solutions, official archive closure, and lawful adaptation rights make the corpus admissible. The known MIT omission, Athena figure exception, Royer lab incompleteness, unpinned notebook environment, original bridge/lab/mastery layer, tagged PDF, semantic EPUB, and independent human-language review remain explicit open gates.
