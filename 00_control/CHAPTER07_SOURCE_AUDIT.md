# Habring Chapter 7 source audit

As of: 2026-08-22  
Authority: `authority/habring/source-v1/duality.tex`  
Identity: 30,761 bytes; 597 lines; SHA-256 `0b112dee2582813cec5629c02df1dda329f690f944b60f4694b1c5762129bea9`

## Closure and topology

The authority is a single editable TeX chapter with three sections: Fenchel duality (source lines 4--247), primal--dual optimization/PDHG (248--396), and ADMM (397--597). It has no figure, external asset, table, URL, or included-file surface. Its bibliography dependencies are the frozen `beck2017first` and `chambolle2011first` entries in `authority/habring/source-v1/references.bib`; one footnote and all five visible informal learner prompts are retained.

The exact ordered topology is 148 environments: 79 `equation`, 27 `aligned`, 12 `proof`, 8 `lemma`, 7 `cases`, 4 `bmatrix`, 4 `theorem`, 3 `enumerate`, 2 `rem`, 1 `defn`, and 1 `example`. The source has 24 label occurrences but only 23 distinct labels because its final `duality:eq:proof_admm6` is duplicated. The target keeps the first occurrence and remaps only the second to `duality:eq:proof_admm7`, with the intended final reference remapped in lockstep. The complete internal-reference surface is 21 `eqref`, 3 `cref`, 1 `Cref`, and 9 `ref` calls.

Hard conceptual dependencies are Chapters 3--5 for subdifferentials, subdifferential calculus, proximal maps, and composite convex optimization, plus finite-dimensional real Hilbert-space duality, adjoints, lower semicontinuity, separation, and elementary telescoping/Jensen arguments. The standalone derivative makes the finite-dimensional real-Hilbert convention explicit rather than leaving the authority's mixed general-space typing implicit.

## Determined correction disposition

Twenty-six exact correction events, `O015-HAB-ADV-0050` through `O015-HAB-ADV-0075`, are integrated in `ADVERSE_LEDGER.jsonl`. They cover:

1. the conjugate example's reversed dual pairing and wrong norm, the indicator conjugate's typing, and the properness/subgradient-existence argument;
2. the ill-typed `f^*(\hat x)`, the free variable and missing inequalities in biconjugation, and the precise Fenchel--Moreau minorant/empty-family scope;
3. coherent finite-dimensional Hilbert/continuous-dual/Riesz conventions, proper extended-real codomains, and the complete hypotheses for Moreau and Fenchel--Rockafellar calculus;
4. the primal--dual gap's type/sign, strong-duality/attainment context, and scaled Moreau formula;
5. PDHG's conjugate proximal, minimization variable, metric coefficient, iteration ranges, ergodic averages, local hypotheses, and zero-operator branch;
6. ADMM's minimization variable, nonsmooth stationarity, actual alternating-triple stationarity limit, operator/subproblem hypotheses, residual algebra, cross-term sign, Lyapunov factors and index range, and final objective sandwich; and
7. the duplicate label plus determined notation, terminology, and proof-transition defects.

The reader's correction appendix discloses every event. The proof-heading/list paragraph break is layout-only and is not represented as a mathematical correction.

## Stable contiguous partition

- `d90.hab.v1.ch07.seg0001` — source lines 1--24: chapter setup and conjugate definition/example.
- `d90.hab.v1.ch07.seg0002` — lines 25--60: properness, lower semicontinuity, Fenchel inequality, and biconjugate introduction.
- `d90.hab.v1.ch07.seg0003` — lines 61--141: biconjugate inequality and Fenchel--Moreau proof/remark.
- `d90.hab.v1.ch07.seg0004` — lines 142--186: conjugate subdifferential and Moreau identity.
- `d90.hab.v1.ch07.seg0005` — lines 187--247: Fenchel--Rockafellar theorem and proof.
- `d90.hab.v1.ch07.seg0006` — lines 248--277: primal, dual, saddle, and gap formulations.
- `d90.hab.v1.ch07.seg0007` — lines 278--335: Arrow--Hurwicz and PDHG derivation.
- `d90.hab.v1.ch07.seg0008` — lines 336--394: PDHG estimate and ergodic convergence.
- `d90.hab.v1.ch07.seg0009` — lines 395--432: ADMM formulation and algorithm.
- `d90.hab.v1.ch07.seg0010` — lines 433--502: ADMM convergence proof steps 1--2.
- `d90.hab.v1.ch07.seg0011` — lines 503--597: ADMM Lyapunov algebra and conclusion.

## Admission outcome

All eleven segments are translated contiguously in `source/id-ID/habring-07-dualitas-id.tex`, 35,428 bytes, SHA-256 `11e9ad614f7ac4e3107e78bc3bed03a6d4acfe22f2a65fca26433b0ae3209fd9`. The 8,615-byte standalone wrapper has SHA-256 `3b6e710e37c07cc9ec82ca919451c313c52fa762d58c7b01c6792a78a0098797` and records attribution, CC BY 4.0, changes, corrections, and non-endorsement.

The structural/formula audit passes twice with zero failures. It preserves all 148 ordered environments, the complete reference/citation/footnote/prompt surfaces, and 11 stable segment IDs; 254 source and 296 target formula surfaces align into 49 explicit delta blocks, of which all 43 substantive blocks are ledger-bound. The final manifest is 81,046 bytes with SHA-256 `fe72e72d0223117a0b34727d235ced9b6bf2af17cf48154e6b670d2ce75d89fb`.

The open numerical validator passes twice with byte-identical output and checks Fenchel/subdifferential and scaled-Moreau identities, an independent SciPy Fenchel--Rockafellar witness, PDHG descent/convergence, and ADMM residual/Lyapunov/objective behavior with negative controls. Its 10,830-byte result has SHA-256 `9ceeadd90b4868f600241301813a8f24c1d1279690abc8cbf96baa3faf62f3c3`.

Two fixed-epoch full builds produce the same 445,733-byte, 21-page A4 PDF, SHA-256 `c4354e1e1366bdb20cebb9c6eca26fba172d6d82a6ad22dd9e2e470da2baeb6e`. All pages were rendered and inspected; the only layout finding, a proof-heading/list near-collision, was repaired and rechecked at full size. The final log has no error, unresolved reference/citation, missing glyph, or box warning. The PDF is searchable, unencrypted, declares `/Lang` `id-ID`, and embeds all fonts with Unicode mappings. It remains untagged and independent Indonesian language review remains unrecorded.

Chapter 7 is admitted. The next source-order cursor is `authority/habring/source-v1/stochastic.tex` (Chapter 8; 4,665 bytes; SHA-256 `610d11b59d8dfabbbbe6fbc509a0f9ac1727540458c67f8cd3b7bab49566a07d`).
