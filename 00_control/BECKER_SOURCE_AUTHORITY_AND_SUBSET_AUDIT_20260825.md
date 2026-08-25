# Becker source authority and bounded-subset audit - 2026-08-25

## Decision

GO, narrowly: freeze `TypedNotes/APPM5720Notes.tex` plus `TypedNotes/notes.sty` as the only proven lawful, source-closed Becker donor root, and admit only four nonduplicative source slices after a new wrapper passes a byte-deterministic build gate.

NO-GO for `TypedNotes/lecture_notes_tex/master.tex` and all 39 standalone lecture modules at this boundary. Their relative preamble reference is wrong, and 24 referenced figures are absent from the exact official archive. The existing 143-page PDF is a visual witness only. Missing figures must not be invented, substituted, or reverse-engineered.

This audit does not translate or admit the four slices yet. It freezes exact candidates and the remaining gates.

## Authority basis

The official, active default-branch tip on 2026-08-25 is commit `98ed6930084c435ba0f675f7646ced1f2fd8729e`, tree `f04670e3f7be3d4836c380fd8bd31883e0b992c9`. The codeload archive is 164,525,001 bytes, SHA-256 `52ec99acf2bfb7f4db308a7b0988ef9cfd28404a822c5cf0ac922d7f43c41821`. All 180 extracted files and 168,574,596 bytes match the official API tree's blob IDs and sizes. The root MIT license witness is 1,071 bytes, SHA-256 `c026320fa977e084507f66ce2d4de70f3955b39a590f5cdd6e10e690e7a13cac`.

Full authority and build evidence is under `authority/becker/`, especially `BECKER_AUTHORITY_FREEZE.md`, `BECKER_FILE_INVENTORY.csv`, `BECKER_ARCHIVE_TREE_VERIFICATION.json`, `BECKER_TEX_CLOSURE.json`, and `BECKER_BUILD_PROBE.json`.

## Why the APPM5720 root is the bounded donor

`TypedNotes/APPM5720Notes.tex` is a single 130,911-byte, LF-delimited TeX source with SHA-256 `dd2e209a05a6f993ccac3b7c32e464005466b45c93237e96c85da56147466cb8`. Its only local support file is co-located `TypedNotes/notes.sty`. An unmodified isolated build succeeds without fetching anything and renders the stochastic/variance-reduction endpoint legibly. It is credited to Mitchell Krock and is covered by the repository's MIT license; both attribution and license notice must travel with any derivative.

The whole 2,989-line document is not admitted wholesale because much of it duplicates the complete Habring v1 spine and the preserved MIT/Penn companions. The source instead acts as a lawful donor for exact missing topics.

## Exact nonduplicative candidate slices

Line numbers are one-based in the exact frozen `TypedNotes/APPM5720Notes.tex`. Slice hashes are SHA-256 of the exact selected lines encoded as UTF-8, joined with LF, and terminated by one LF.

| Stable candidate | Exact lines | Lines / bytes | Slice SHA-256 | Function |
|---|---:|---:|---|---|
| `BECKER-LAGRANGE-CORE` | 1263-1499 | 237 / 10,237 | `8a93db6ea1b01bbda86b8004848797862f47257136bf2ee5a002f96a83caf7eb` | Lagrange dual function/problem, weak and strong duality, Slater condition, and saddle-point interpretation. |
| `BECKER-KKT-CORE` | 1652-1743 | 92 / 4,585 | `9b9aee9dfcc0273330f61126e14fa5ee958dec02ed34784b434b09cfb0a5b1ee` | KKT conditions, necessity/sufficiency under convexity and Slater, complementary conditions, and worked examples. |
| `BECKER-DOUGLAS-RACHFORD` | 2750-2797 | 48 / 1,285 | `386f1f0f94f6433eebdd6d07e10f3ffe28ffa8650e392cb0158a389e01452cf2` | Douglas-Rachford iteration and its relationship to ADMM. |
| `BECKER-VARIANCE-REDUCTION` | 2971-2988 | 18 / 900 | `b81634bf07565fcf8d2774bea7b96e565e5fdd76cf5e782c5e4eb6fb3268c5ed` | SAA variance reduction, SAGA update, and SAG/SVRG orientation. |

These are candidate boundaries, not permission to copy adjacent overlapping sections. A later source extraction must preserve the upstream line map and slice hash, introduce only the minimum connective definitions needed for a coherent unit, and use new stable identifiers without renumbering accepted Habring/MIT/Royer/Penn material.

## Coverage and overlap against complete Habring v1

Habring already supplies the structured foundations, convexity, subgradients, projected subgradient descent, proximal gradient, acceleration, Fenchel duality, primal-dual optimization, ADMM, basic stochastic gradient descent, and optimal transport. Repeating those Becker sections would add little curricular value and create terminology/maintenance duplication.

The exact Habring TeX has zero occurrences of KKT or Slater, no minibatch, no SAG/SAGA/SVRG, no mirror descent, no variational-inequality section, no maximal-monotone or resolvent development, and no Douglas-Rachford treatment. Its three exercise environments have no hint or solution environments. This supports the four narrow candidates above while rejecting most of the Becker text as duplicative.

The Becker candidates remain limited:

- The Lagrange and KKT slices materially close the unified KKT/Slater/Lagrangian-duality gap.
- The Douglas-Rachford slice adds a missing splitting algorithm, but it does not develop maximal monotone operators or resolvents and cannot close that theory by itself.
- The variance-reduction slice adds SAGA/SAG/SVRG orientation, but only as a short treatment. It does not supply stochastic proximal or mirror methods, a minibatch analysis, or complete proofs.
- Becker contains only brief variational-inequality mentions, no maximal-monotone framework, no resolvent theory, and no mirror-descent module. Those mentions are too thin to admit as independent reader units.

Accordingly, the finite original layer is still required for stochastic proximal/mirror/minibatch development, rigorous variance-reduction connective proofs, variational inequalities, maximal monotonicity, resolvents and operator splitting, exercises, hints, and complete solutions.

## Assessment and self-study closure

The APPM5720 TeX source has 51 example environments, 66 theorem environments, 14 proof environments, and 95 remarks, but zero exercise, hint, or solution environments. The repository separately contains five Spring 2025 homework-assignment PDFs and helper code. `Homeworks/README.md` explicitly says the homework solutions are on Canvas. Therefore:

- the homework PDFs are not a public complete-solution closure;
- they are PDF-led rather than source-editable assignments;
- they must not be counted as the required exercise/hint/answer/complete-solution layer;
- any useful problem adopted later needs its own exact rights/source audit and a complete independently authored solution.

The repository's demos are valuable optional computation witnesses, but they bring Python/NumPy/SciPy/CVXPY, MATLAB/CVX, Julia/ForwardDiff, or ADiGator dependencies and mixed component licenses. No demo is admitted automatically with the four text slices.

## Build and accessibility gate for later admission

The full APPM5720 root builds logically but not byte-deterministically in the current probe: two clean fixed-epoch runs both produce 48 pages but different PDF hashes. Before a slice becomes an edition unit, create a minimal deterministic wrapper containing only the frozen slice and required macro definitions, preserve the MIT notice and Mitchell Krock credit, build twice from clean directories, and require identical source/package manifests and canonical output hashes. Run math/reference checks and visual inspection on the resulting unit.

The upstream typed-note PDFs are untagged, and the repository has no semantic HTML/EPUB reader. Every admitted derivative therefore needs the lane's existing reflowable HTML/EPUB surfaces, explicit structure and navigation, accessible formula treatment, and text alternatives for any retained visual. The selected four slices themselves reference no missing external figure bytes; this must be rechecked after exact extraction.

## Next executable production action

Extract `BECKER-LAGRANGE-CORE` and `BECKER-KKT-CORE` together into one coherent MIT-licensed source module with a minimal audited wrapper. Preserve the two exact source slices and hashes in its manifest, add only necessary connective text, assign new Becker-specific stable IDs, and run two clean deterministic builds plus math/visual/backend QA. Then translate that module into id-ID. Treat Douglas-Rachford and variance reduction as later bounded modules. Do not touch the non-admissible Jaden Wang master, fetch missing figures, install packages to force it, contact upstream, or publish until a coherent admitted unit passes the normal release boundary.

## Shared-control deltas recommended to the primary task

The primary task should integrate, at its next safe control update:

1. Source authority: Becker commit/tree/archive/license and the fact that every extracted blob matches the official API tree.
2. Selection: `TypedNotes/APPM5720Notes.tex` is the sole source-closed donor; the four exact candidates above are the frozen nonduplicative subset.
3. Fail-closed exclusion: `lecture_notes_tex/master.tex` and its 39 modules are not admissible because of 40 wrong preamble references and 24 archive-absent figures.
4. Rights: preserve root MIT terms and Mitchell Krock credit; keep embedded BSD-3-Clause/GPLv3 code exceptions separate and outside automatic admission.
5. Build state: APPM5720 builds 48 pages but byte determinism is not yet proven; the extracted wrapper must pass the deterministic gate.
6. Remaining closure: original stochastic mirror/minibatch/proximal and VI/maximal-monotone/resolvent material plus substantive exercises and complete solutions remains required.

No existing shared control was edited by this audit.

## Superseding exact Becker-01 boundary note (2026-08-25)

The later line-addressable extraction gate supersedes two preliminary details in
this audit. `TypedNotes/APPM5720Notes.tex` has 2,992 physical lines; the final
three lines are whitespace-only, which explains the preliminary 2,989-line
count without changing any source byte. The operative Becker-01 boundary is no
longer the broad two-slice candidate: it is the five exact ranges 1263-1321,
1398-1405, 1414-1499, 1652-1726, and 1731-1743 recorded in
`qa/BECKER_01_SOURCE_BOUNDARY.json`. The LP-specific ranges 1322-1397,
1406-1413, and 1727-1730 remain explicitly excluded for O018. The combined
witness is 12,294 bytes with SHA-256
`20335c054393ea43d8912046b6dbfa07f6018f9e16b889e4cd0f66abc064d565`.
Treat the earlier broad slice hashes as historical candidate evidence only.

## Becker-01 admission closure (2026-08-25)

The audit's pre-admission wording and recommendation to repair the alternate
master are now historical. The alternate Jaden Wang master remains excluded;
no repair can close its 24 archive-absent figures. The APPM5720 donor required
no preamble repair. Becker-01's five operative ranges have been translated and
admitted after deterministic PDF/HTML, mathematical, responsive-browser,
all-page visual, independent semantic, rights, backend, and compact-release
gates. The final body/PDF/HTML SHA-256 values are
`ad656aa517ff418cc1529d2c2c62c602ea95aa2a4dbff9cf1f3f336f26e574ce`,
`c698444856fd01e1ee306d7e3dbca31992f8bb4cf7b4a4cf106ea678be83e615`,
and `b4a762b10746d394be714177669ad1d5e9903aa04933e8ff4791a179dd0377c0`.
The protected backend is 3,320 records; the 21-entry release ZIP is 511,931
bytes / SHA-256
`5d33d0cb89e1eaa96027a0b645bc54425b6008a45e7f0ae8ffed7938cc429281`.
Public preservation remains a separate pending transaction. The next source
candidate is Douglas–Rachford lines 2750–2797, then variance reduction lines
2971–2988; the original closure remains required.
