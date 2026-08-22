# Penn Chapter 5 independent rereview

Date: 2026-08-22  
Disposition: **PASS — frozen target is ready for root build/admission gates**

This rereview was independent of the earlier candidate PASS. It reread the
complete Penn `Section5.tex`, the complete Indonesian Chapter 5 target, all
twelve proposed ledger records, both generated reports and their generators,
the five excluded Maple inputs, the exact Chapter 2/3/4 theorem prerequisites,
the current external-reference anchors, and the bounded `Bert99` bibliography
surface. It did not edit the wrapper, shared controls, backend, publication
state, or Git.

## Finding counts

| State | P1 | P2 | P3 |
|---|---:|---:|---:|
| Raised during independent rereview | 0 | 1 | 3 |
| Remaining after the narrow corrections below | 0 | 0 | 0 |

The resolved P2 was a single scope defect repeated across the local Newton,
hybrid, fixed-threshold, and dynamic-threshold superlinear surfaces: the
candidate used asymptotic Q-rate language without separating exact finite
termination, even though the Chapter 3 rate definition excludes finite
attainment and Chapter 4 Theorem `thm:Superlinear` assumes nonzero gradients.
The theorem statements, exercises, and proof now state the finite-termination
alternative explicitly.

The three resolved P3 findings were:

1. `NewtonTerkoreksi` assigned the three-result
   `CholeskyTermodifikasi` contract to `L` alone; it now destructures
   `(L,B,C)` explicitly.
2. The indefinite-Hessian example inferred an unbounded backtracking outcome
   too directly from a negative directional derivative. It now identifies the
   violated ascent-direction precondition, requires rejection before the line
   search, and retains a bounded defensive failure contract.
3. “Open pseudocode/reference” wording could be read as a license claim. It
   now says “explicit, independently written” and “independent reference
   implementation,” consistent with the component-rights record. The raw
   Newton failure message was also clarified to say that correction is needed.

The existing proposal IDs remain consecutive and unchanged. Their action
descriptions were narrowed in events `O015-PENN-ADV-0040`, `0042`, `0043`,
`0047`, and `0049`; no new adverse event was invented for corrections to the
candidate's own wording.

## Mathematical and language disposition

The Newton sign convention is correct for maximization:
`B_k=-H(x_k)` and `p_k=-H(x_k)^{-1} grad f(x_k)`. The quartic example has the
exact pure-Newton map `(x,y) -> (0,2y/3)`, so the target appropriately treats
the source's eleven-step statement as an implementation-tolerance witness.

For the double-peak function, the target correctly uses
`p_N=(66/127,-79/127)` at `(1,1/2)` and the exact negative directional product
`-791 exp(-1/4)/508`. The Hessian determinant is negative, `(1,1)` is not
stationary, and the positive-y global maximizer is `(0,1)`. The corrected
modified-Cholesky calculation consistently factors `-H`, corrects only the
second Schur pivot for `mu_1=0.1`, `mu_2=1`, and gives the positive product
`9 alpha/10 + 6241 alpha^2/400`, approximately `10.164315323`.

The local convergence proof now has the required invariant compact ball,
bounded inverse Hessian, integral mean-value identity, norm inequalities,
continuity modulus, and Lipschitz-Hessian quadratic upper estimate. It does
not claim an exact positive quadratic-order ratio from an upper bound alone.
The global stationarity result assumes the uniform spectral bounds needed to
make the directions gradient-related. The eventual-superlinear result uses
Schur pivots of `-H`, Hessian/pivot continuity, `t_0=1`, and
`0<sigma_1<1/2`, and now handles finite termination separately.

The Indonesian text is faithful wherever the Penn source is mathematically
sound and openly identifies every determined correction where it is not.
No exercise, figure, theorem, proof, example, citation, formula environment,
label, or unique source reference target is lost. Terminology is consistent
with Chapters 3 and 4 (`arah naik`, `berkaitan dengan gradien`, `pelacakan
mundur Armijo`, `Q-superlinear`, and `taksiran Q-kuadratik`).

## Topology, references, figures, and rights

The final structural receipt verifies the exact ordered 84-environment
topology, including 5 exercises, 4 figures, 5 algorithm environments, 3
theorems, 3 proofs, and the exact ordered 35-entry displayed-formula
environment sequence. All ten labels remain in source order. All sixteen
source reference calls remain covered; the target has nineteen calls but no
new unique target and no missing source target. The sole citation remains
`Bert99`. All four figure call strings and all four figure byte identities are
unchanged.

The five Maple inputs were read only to check the replacement boundary. None
is imported, executed, transliterated, or copied into the target. The three
replacement algorithms are short, locale-neutral pseudocode with independently
worded inputs, stopping behavior, ascent checks, line-search contracts,
iteration/shrink limits, return values, and failure states. Their mathematical
ideas are necessary method interfaces; their Maple syntax, comments, variable
layout, and implementation text are absent. The revised wording makes no
unsupported open-license claim.

Exact external prerequisites were checked as follows:

- `cor:MVT-Vec`: Penn `Section2.tex` lines 45–50, external anchor 2.7;
- `thm:NMConvergeRate`: Indonesian Chapter 3 lines 586–589, anchor 3.53;
- `thm:GenConverge`: Indonesian Chapter 4 lines 150–157, anchor 4.12;
- `thm:Superlinear`: Indonesian Chapter 4 lines 471–488, anchor 4.25;
- Armijo input contract: Indonesian Chapter 4 lines 126–134;
- `Bert99`: the exact bounded entry in `references-penn-ch05-id.bbl`.

The current Chapter 5 wrapper contains all four frozen anchors, includes the
Chapter 5 target, and inputs the Chapter 5 bibliography excerpt. Those files
were inspected read-only and remain root-owned build surfaces.

## Repeated deterministic audits

Two fresh final-state executions of each relevant audit passed. The first and
second receipt hashes were byte-identical:

| Audit | Run 1 SHA-256 | Run 2 SHA-256 | Result |
|---|---|---|---|
| Structural report | `89757169df04a17c4e19bb72469aa6cd5ebb094e4c1298e3b8b78b44b3d9146a` | `89757169df04a17c4e19bb72469aa6cd5ebb094e4c1298e3b8b78b44b3d9146a` | PASS |
| SymPy solver report | `9c5905c0022a1a99f8064484cff40abff0b9435df133822b5e16fc2b0ac6401f` | `9c5905c0022a1a99f8064484cff40abff0b9435df133822b5e16fc2b0ac6401f` | PASS |

The structural report has 17 passing gates and zero failures. The SymPy
1.13.1 report has 7 passing gates and zero failures. No excluded Maple code
was executed.

## Frozen core identities

| Artifact | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| `authority/penn-state/source/ClassNotes/Section5.tex` | 22,371 | 317 | `15186b99be0913d83046e3e32eaf7a378d3a4fccd222219984b091ddf7f9a428` |
| `source/id-ID/penn-05-metode-newton-dan-koreksi-id.tex` | 27,317 | 400 | `0f6afd7da2268661124f967f299ac9df89bb6a8f5683b3e4e8fea32718a8549a` |
| `qa/PENN_CH05_PROPOSED_LEDGER.jsonl` | 10,242 | 12 | `823ba2913a44c88d39c062f9fab847720e5637fd9dca75e4532de806bcd02d67` |
| `qa/audit_penn_ch05_candidate.py` | 14,118 | 320 | `6964f467ee85f856fe0c28ef5628dc8c83f1140b764dfe4a03c95a84d28c6af4` |
| `qa/PENN_CH05_STRUCTURE_REPORT.json` | 26,392 | 861 | `89757169df04a17c4e19bb72469aa6cd5ebb094e4c1298e3b8b78b44b3d9146a` |
| `qa/validate_penn_ch05_math.py` | 11,053 | 297 | `c1362699da1bfe8fc5ce791556c84255ba05049ab3506fc1891643ff8eb98af9` |
| `qa/PENN_CH05_SOLVER_RESULTS.json` | 6,242 | 258 | `9c5905c0022a1a99f8064484cff40abff0b9435df133822b5e16fc2b0ac6401f` |

Prerequisite identities used for this rereview:

| Artifact | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| `authority/penn-state/source/ClassNotes/Section2.tex` | 28,822 | 423 | `1e1a4d9ed1f7b54ab141fc964efaedd7b731e6f1f7a2132098ea2b7cbe55809c` |
| `authority/penn-state/source/ClassNotes/Section3.tex` | 41,715 | 608 | `d4ae6142e2366b12575eafddc833df067518af114e9816187668cc367be43010` |
| `authority/penn-state/source/ClassNotes/Section4.tex` | 34,684 | 469 | `76113034709b5914fa920076f2e882ccf30157e78ce5bdf4593a5d39af1886d5` |
| `source/id-ID/penn-03-pendakian-gradien-dan-pencarian-garis-id.tex` | 44,364 | 646 | `7c75d0ae56a5a912d561d91ece607f088a4ff4f3de4dbc3396ce40d6d7d6a229` |
| `source/id-ID/penn-04-pencarian-garis-hampiran-dan-konvergensi-id.tex` | 33,313 | 613 | `c5c0f09d38454177e61c2a97c9beef07771d5f4f715cc7a4a81a871ff54ced8f` |
| `authority/penn-state/source/ClassNotes/Math555.aux` | 62,603 | 601 | `a809aa76c780221a8c03a271c790b21529fe4bb49b4860cfe8c22ab593a71b16` |
| `source/id-ID/references-penn-ch05-id.bbl` | 625 | 16 | `037e62878f1a562314a33054da8f4df4e49c029bbad31c2ec75066cd3e1a99f3` |
| `source/id-ID/D90-PENN-05-metode-newton-dan-koreksi-id.tex` (read only) | 7,230 | 175 | `82450c4cdbe6de904c7cba1ee22922869f5d2e2caf19be69285092a5ea987e55` |

## Admission handoff

The Chapter 5 fragment and proposed ledger are ready for root build/admission.
The remaining gates are root-owned: admit the selected proposal records and
original pseudocode component, compile twice, inspect logs and extracted text,
perform all-page visual/accessibility QA, then update shared controls/backend.
This report does not claim those later gates have passed.
