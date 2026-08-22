# Penn Chapter 4 source audit — Pencarian Garis Hampiran dan Konvergensi

Status: ADMITTED — complete contiguous translation, independent rereview,
deterministic standalone build, visual/accessibility QA, correction-ledger
integration, and rights closure pass.

Course role: O015 / D90 Advanced Optimization and Convex Analysis  
Unit: Penn State MATH 555 Chapter 4, “Approximate Line Search and Convergence
of Gradient Ascent” / “Pencarian Garis Hampiran dan Konvergensi Pendakian
Gradien”

## Authority, rights, and overlap

The editable authority is Christopher Griffin’s *Nonlinear Programming*, Penn
State MATH 555 source distribution v1.0, frozen lane authority
`o015-penn-math555-v1.0-source`. The exact chapter source is
`authority/penn-state/source/ClassNotes/Section4.tex`: 34,684 bytes, 469
physical lines, 433 nonblank lines, SHA-256
`76113034709b5914fa920076f2e882ccf30157e78ce5bdf4593a5d39af1886d5`.
It is genuine LaTeX source included by `Math555.tex`, not a reconstruction from
PDF. The public v1.0.1 PDF remains the frozen correction witness; no exact
editable v1.0.1 source is claimed.

The text/source-archive component is CC BY-NC-SA 3.0 US. An Indonesian
derivative is permitted subject to attribution, identification of changes,
noncommercial use, ShareAlike under the same license, a license link, and no
implied endorsement. The three Maple listings remain excluded because their
component rights are unclear or external. Their reader roles are replaced by
separately authored pseudocode, recorded as a lane-authored component in
`00_control/COMPONENT_RIGHTS.csv`.

The unit covers Wolfe/Armijo inexact line search, gradient-related directions,
stationarity, exact-gradient convergence rates, conditioning, and eventual
unit steps/superlinear convergence. It does not translate LP/IP modeling,
simplex, LP duality, sensitivity, graph/network/discrete algorithms, generic OR
case studies, or introductory solver workflows. It therefore does not overlap
the O018 boundary documented in `00_control/COVERAGE_OVERLAP.md`.

## Exact source surface and dependency closure

The live source contains 112 ordered environments. Its exact count vector is:

- algorithm 1; bmatrix 1; cases 1; cgalgorithm 2; corollary 2;
- definition 3; displaymath 12; enumerate-star 1; equation 49;
- example 3; exercise 4; figure 5; gather-star 1; lemma 2;
- multline 4; proof 4; remark 13; theorem 4.

It contains 32 labels, 52 reference calls, four citations (all `Bert99`), five
figure calls, four exercises, and three `lstinputlisting` calls. The 49
equations, 12 displaymath blocks, one gather-star block, and four multlines form
66 ordered displayed-formula surfaces.

The five figures are present in the authority closure and copied exactly into
the Indonesian figure directory:

| Figure | Bytes | SHA-256 |
|---|---:|---|
| `ThreeDCos.pdf` | 234,150 | `e14dc949d3fd7cd7d0593f0352567aa9ac6e66423886113929df9c7feb2eace5` |
| `WolfePhiOfT.pdf` | 16,923 | `221447efe0da804b341570bf3877c842199dd6052b7029eb70cf2edf1aab9a09` |
| `WolfeConditionsIllustrated.pdf` | 163,565 | `b3d2c7c62a79e6bf74ec62089afc773f631f1c62d67e2f8bfd58fb4a078796ec` |
| `ConvergenceFailure.pdf` | 11,302 | `fc5f89515414dcbc704e718e6de62b0bb15785b645bd669c98254dd058a16836` |
| `GradientAscentOut.pdf` | 110,472 | `31cdba8ed1818564289fba9c2c279b48cd0bddc347097261ae8df572953eecc4` |

The excluded listing inputs are `Code/BackTrace.mpl`,
`Code/GradientAscent-1.mpl`, and `Code/GradientAscent-2.mpl`; they are not
required by the Indonesian fragment. The sole bibliography key `Bert99` is
resolved by the exact bundled `Math555.bbl`; the existing bounded Penn Chapter
3 excerpt already contains that entry. Bibliography databases are absent, so
the `.bbl` remains an opaque build input rather than a basis for invented
metadata.

Chapter-external label dependencies and their bundled `Math555.aux` display
numbers are: Proposition 1.20 `prop:DirecDeriv`; Theorem 1.22 `thm:DirDeriv`;
Theorems 2.2 and 2.4 `thm:MVT`, `thm:MVT2`; Definition 3.2
`def:AscentDir`; Lemma 3.8 `lem:AscentDirection`; and Algorithms 2, 3, and 5
`alg:ModifiedGradientAscent`, `alg:Bracket`, `alg:GoldenSearch`. The standalone
wrapper binds these labels to their official numbers and explains the omitted
prerequisites without retranslating the earlier chapters.

## Complete Indonesian unit

The complete target is
`source/id-ID/penn-04-pencarian-garis-hampiran-dan-konvergensi-id.tex`:
33,313 bytes, 613 physical lines, SHA-256
`c5c0f09d38454177e61c2a97c9beef07771d5f4f715cc7a4a81a871ff54ced8f`.
Seven stable markers partition source lines 1–469 exactly once:

| Segment | Source lines |
|---|---:|
| `d90.penn.v1.ch04.seg0001` | 1–74 |
| `d90.penn.v1.ch04.seg0002` | 75–124 |
| `d90.penn.v1.ch04.seg0003` | 125–206 |
| `d90.penn.v1.ch04.seg0004` | 207–243 |
| `d90.penn.v1.ch04.seg0005` | 244–331 |
| `d90.penn.v1.ch04.seg0006` | 332–363 |
| `d90.penn.v1.ch04.seg0007` | 364–469 |

The target has the exact ordered environment topology and formula-environment
sequence, all 32 source label strings once, all unique source reference
targets, the exact citation and figure sequences, and all four exercises. The
only added reference target is a deliberate local citation of
`thm:GenConverge` from its corrected corollary. Repeated references inside
rewritten proofs are not forced to remain numerically identical when a
determined proof repair changes the prose, but no source reference target is
lost.

## Integrated corrections

`qa/PENN_CH04_PROPOSED_LEDGER.jsonl` contains 13 valid proposed records,
10,055 bytes, SHA-256
`fa9c5c0b097b7349a959ca6c1c9c797fc0ed2ea61e91148badec62bb239b7bbd`.
IDs are consecutively `O015-PENN-ADV-0025` through
`O015-PENN-ADV-0037`; they do not reuse Chapter 3 IDs. All 13 are appended
verbatim as the final tail of `00_control/ADVERSE_LEDGER.jsonl`, whose admitted
identity is 83,238 bytes / 133 unique records / SHA-256
`333f870c4383532fcf01a390c8b2321fca2e8b54d5ca6fa857d5d028ce65f8c0`.

| Event | Audited surface |
|---|---|
| 0025 | shifted-gradient chain rule and ascent curvature inequality |
| 0026 | vector path typing and accepted curvature region |
| 0027 | Wolfe hypotheses and Armijo backtracking termination |
| 0028 | independent backtracking pseudocode replacing excluded Maple |
| 0029 | valid backtracking stationarity theorem and proof |
| 0030 | exact-search/scaled-gradient scope and undefined Armijo symbol |
| 0031 | fixed-step recurrence indexing and alternating limits |
| 0032 | v1.0 capture-theorem closing norm delimiter |
| 0033 | convergence factor, condition number, endpoint, and lambda algebra |
| 0034 | independent gradient-ascent pseudocode replacing excluded Maple |
| 0035 | quadratic example matrix scaling and metrics |
| 0036 | complete Newton direction and uniform eventual-unit-step proof |
| 0037 | owning-environment label binding |

## Independent QA result

The deterministic structural/formula/residue audit passes twice with no
failures:

| Artifact | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| `qa/audit_penn_ch04_candidate.py` | 33,499 | 694 | `aec0ca750c3de504f5c6f8b9a95217c1d5cda2111a5a697442caadaae952c256` |
| `qa/PENN_CH04_STRUCTURE_REPORT.json` | 39,127 | 1,216 | `c43e0195fc7da99590efd17b83ace3ca6a5721bc5156e86d2121a877b85e2c0a` |
| `qa/PENN_CH04_FORMULA_DELTA_MANIFEST.json` | 65,651 | 1,487 | `fe7aa0bbd5cab4ff50cdf855a3bcf3c73f6ad0e007e2ce2033369cf54ed4a65e` |
| `qa/validate_penn_ch04_math.py` | 13,339 | 365 | `6f2ebf4a462043d327b5eb8c7e238808b6098aea2c193eab66cfa43794cd4bc4` |
| `qa/PENN_CH04_SOLVER_RESULTS.json` | 5,523 | 207 | `44c2b1a2509775e182e38b125f6c25ca49eb2f7e23e68ec2fce6878bf7704dd2` |
| `qa/PENN_CH04_VISUAL_QA.json` | 1,808 | 48 | `e700d08476f7aaa018ca31687d2eea2e8a50729599f760d300dd5b6f89211e70` |

The structural report validates source identity, balanced nesting/braces,
exact ordered topology, labels, unique reference closure, citation/figure
sequences, exercises, source-line partition, 66 formula pairs, all 13 event
bindings, required correction witnesses, excluded-code residue, ledger
schema/IDs, and all asset hashes. The numerical report passes 12 fail-closed
gates covering Wolfe signs and negative controls, Armijo termination, the
recurrence, deterministic Kantorovich/exact-ascent witnesses, quadratic scaling
and conditioning, and eventual unit-step/superlinear Newton behavior. The
independent reread found one P3 wording defect in the capture theorem, repaired
it, and finished with P1=0, P2=0, P3=0.

## Build, visual QA, and admission disposition

The source is lawful, complete for this chapter, editable, build-dependent only
on admitted Penn text/assets and the bounded bibliography input, and genuinely
non-overlapping with O018. The standalone wrapper
`source/id-ID/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex` is
8,018 bytes / SHA-256
`b40ac7e4e1ee69afd0f7f82dbfc9042c6df79c1aaf2ccca78ec9e639b2030edc`;
the exact one-entry `.bbl` is 625 bytes / SHA-256
`037e62878f1a562314a33054da8f4df4e49c029bbad31c2ec75066cd3e1a99f3`.

Two fixed-epoch forced builds produced byte-identical 17-page A4 PDFs. The
admitted reader is 847,350 bytes / SHA-256
`c0f283aa7d70eba05de6a35c98bc0aa55f3177ab40702bf7eed5de45a7b6ab8a`;
the canonical log is 27,564 bytes / SHA-256
`f247633a55e47a6fc002899bc9dbd24128f0949e39cc2954f78164411c301174`
with no TeX error, unresolved reference/citation, box warning, missing glyph,
or rerun request. All 17 rendered pages were inspected; a forced float-only
algorithm page was removed by changing only two placement specifiers from
`[p]` to `[htbp]`. The final reader has no blank page, clipping, collision, or
broken figure. It is searchable on every page, declares `/Lang id-ID`, has six
outlines and no forms or JavaScript. It remains untagged, and ten inherited
vector-figure font resources lack ToUnicode maps. Semantic HTML/EPUB remains a
corpus-level completion gate rather than a hidden claim here.

Penn Chapter 4 is therefore admitted as the ninth bounded reader unit. This
edition decision remains independent of later curriculum admission and is not
a publication claim.

Exact next cursor after admission: `Section5.tex:1`, 22,371 bytes, 317 lines,
SHA-256 `15186b99be0913d83046e3e32eaf7a378d3a4fccd222219984b091ddf7f9a428`.
