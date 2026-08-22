# Penn Chapter 5 source and reader admission audit

As of: 2026-08-22  
Unit: Penn Chapter 5 — Newton's Method and Corrections / Metode Newton dan Koreksinya  
Reader admission: PASS  
Backend status: recorded separately in the live backend validator and `BUILD_AND_QA.md`

## Authority and lawful boundary

The editable authority is Christopher Griffin's *Nonlinear Programming*, with
Simon Miller and Douglas Mercer, Penn State MATH 555 source distribution v1.0,
frozen as `o015-penn-math555-v1.0-source`. The exact source is
`authority/penn-state/source/ClassNotes/Section5.tex`: 22,371 bytes / 317
physical lines / SHA-256
`15186b99be0913d83046e3e32eaf7a378d3a4fccd222219984b091ddf7f9a428`.
It is genuine LaTeX included by `Math555.tex`; the public v1.0.1 PDF is only a
correction witness, and no editable v1.0.1 source is claimed.

The Penn source and derivative are handled under CC BY-NC-SA 3.0 United
States: attribution, change identification, noncommercial use, ShareAlike,
license link, and non-endorsement are retained. Five Maple/legacy listing
inputs are excluded because their reusable component rights are unclear or
external. No source listing syntax or text is copied. Their reader roles are
replaced by three independently authored, locale-neutral algorithm surfaces
for variable-step Newton, modified Cholesky, and corrected Newton; these are
separately registered in `COMPONENT_RIGHTS.csv` as original components inside
the combined NC-SA derivative.

This chapter supplies pure and variable-step Newton, local convergence,
globalization, gradient--Newton switching, modified-Cholesky correction,
stationarity, and eventual superlinear behavior. It does not duplicate O018's
LP/IP modeling, simplex, LP duality, sensitivity, graph/network algorithms,
or general operations-research workflow. The source-order cursor after this
unit is `authority/penn-state/source/ClassNotes/Section6.tex`.

## Exact reader closure

- Indonesian target: `source/id-ID/penn-05-metode-newton-dan-koreksi-id.tex`
  — 27,317 bytes / 400 lines — SHA-256
  `0f6afd7da2268661124f967f299ac9df89bb6a8f5683b3e4e8fea32718a8549a`.
- Standalone wrapper:
  `source/id-ID/D90-PENN-05-metode-newton-dan-koreksi-id.tex` — 7,230
  bytes / 175 lines — SHA-256
  `82450c4cdbe6de904c7cba1ee22922869f5d2e2caf19be69285092a5ea987e55`.
- Essential bounded bibliography excerpt:
  `source/id-ID/references-penn-ch05-id.bbl` — 625 bytes / 16 lines —
  SHA-256
  `037e62878f1a562314a33054da8f4df4e49c029bbad31c2ec75066cd3e1a99f3`.
- Final reader PDF:
  `output/pdf/D90-PENN-05-metode-newton-dan-koreksi-id.pdf` — 2,691,780
  bytes / 15 A4 pages — SHA-256
  `427db2c5a4428dfbe222d7e1d4f5c5349d4f78484a8593c412328fe94a7353c6`.
- Canonical build log: 27,062 bytes / 700 lines — SHA-256
  `bb3e9416233d14400ced235b69eeb95f76e6347dfeabbfd2c06727b543aed8be`.
- Extracted text: 29,195 bytes / 541 lines — SHA-256
  `78fc7ecf877b7707c6c33736210449d502bbc148b84994b65b0d2fc4791365d3`.

The target preserves all 84 ordered environments: eight `array`, three
`bmatrix`, five `cgalgorithm`, one `definition`, twelve `displaymath`, one
`enumerate*`, sixteen `equation`, five `example`, five `exercise`, four
`figure`, two `gather*`, five `multline`, three `proof`, eleven `remark`, and
three `theorem`. It preserves the exact ordered 35 displayed-formula surfaces,
all ten labels, all five exercises, the citation and external-reference
closure, and a gap-free seven-segment partition of source lines 1--317.

The four exact Penn-derived vector figures are:

| Figure | Bytes | SHA-256 |
|---|---:|---|
| `NewtonsMethod.pdf` | 123,281 | `94c86e8eaf669f51dfe4d63f3b6799c84fb7b2d4fc781c304541aa40bc0442b6` |
| `DoublePeak.pdf` | 2,138,564 | `0091677ffedeaed91d4746edd03439ebb586a02900c86b9d7b9693205019e6fa` |
| `GaussModifiedNewtonsMethod.pdf` | 56,347 | `d59d49782969f5c55a49fde4ffc65e919019e5df06ebd70009457a1b508422c2` |
| `ModifiedNewton.pdf` | 56,339 | `7b5a76196e5b535447bc39162d1f11d63e65a021381108f06ac85ab7738bc28f` |

## Determinations and computation evidence

Twelve exact records `O015-PENN-ADV-0038` through
`O015-PENN-ADV-0049` are integrated byte-for-byte from
`qa/PENN_CH05_PROPOSED_LEDGER.jsonl` into `ADVERSE_LEDGER.jsonl`. They close
the maximization Newton sign, variable-step failure contract, indefinite
Hessian example, induced norm, local convergence proof, hybrid endpoint and
hypotheses, modified-Cholesky factorization, surrogate notation and solves,
the numerical example, corrected-Newton executable surface, stationarity
hypotheses, and eventual-superlinear threshold conditions.

The structural audit source `qa/audit_penn_ch05_candidate.py` is 14,118 bytes,
SHA-256
`6964f467ee85f856fe0c28ef5628dc8c83f1140b764dfe4a03c95a84d28c6af4`;
its passing report is 26,392 bytes, SHA-256
`89757169df04a17c4e19bb72469aa6cd5ebb094e4c1298e3b8b78b44b3d9146a`.
The open SymPy validator `qa/validate_penn_ch05_math.py` is 11,053 bytes,
SHA-256
`c1362699da1bfe8fc5ce791556c84255ba05049ab3506fc1891643ff8eb98af9`;
its passing result is 6,242 bytes, SHA-256
`9c5905c0022a1a99f8064484cff40abff0b9435df133822b5e16fc2b0ac6401f`.
Both audits pass on repeated final-state execution.

The numerical checks independently reconstruct the quartic Newton map; the
double-peak gradient, Hessian, stationary set, and failed pure-Newton ascent
direction; the corrected modified-Cholesky factor and triangular solves; the
surrogate spectral bounds; and a local quadratic-convergence witness. No
excluded Maple component is executed.

## Independent and visual QA

The frozen-target independent mathematical rereview is
`qa/PENN_CH05_INDEPENDENT_REREVIEW.md`: 9,373 bytes / 157 lines / SHA-256
`239e4d79f90c570ac95ceb22cab097b41980c308abb39f940fe66dbc5f7861dd`.
It raised and resolved one P2 and three P3 findings; the final disposition is
P1=0, P2=0, P3=0.

Two complete fixed-epoch builds produced byte-identical PDFs. The canonical
log has no TeX error, undefined reference or citation, overfull box, missing
glyph, or rerun request; one contained underfull caption warning is accepted.
All 15 pages were inspected in a contact sheet and pages 4, 5, 9, 10, 11, 12,
and 14 were inspected full size. There is no blank content page, clipping,
collision, broken figure, unreadable glyph, or stranded algorithm-only page.
Exact visual evidence is `qa/PENN_CH05_VISUAL_QA.json`: 2,687 bytes / 81 lines
/ SHA-256
`3130aee988a10cf4fc4c2b3cfbdc494293142519c0c416d603a109704188bde4`.

The PDF is A4/PDF 1.5, unencrypted, searchable on all 15 pages, declares
`/Lang` `id-ID`, exposes six outlines, has no forms or JavaScript, and all 137
font resources expose Unicode maps. It remains untagged. Semantic HTML/EPUB
and independent human/native-speaker Indonesian review remain open; this file
does not claim either.

## Admission result

The lawful complete Chapter 5 reader passes source, topology, formula,
reference, exercise, asset, rights, mathematical, computation, deterministic
build, text, visual, and bounded accessibility gates. Reader admission is
PASS. Backend identities are intentionally recorded in the live backend
validator and `BUILD_AND_QA.md`, so this frozen source audit does not create a
self-referential backend-hash dependency.
