# O015 Indonesian terminology QA

Date: 2026-08-22  
Gate: passed with an openly reported non-arXiv fallback  
Scope: terminology for convex analysis and continuous optimization before the MIT semantic-source pilot

## Search result and fallback

A bounded search was run on the official arXiv search surface for the exact Indonesian expressions `"optimisasi konveks"`, `"optimasi konveks"`, and `subgradien`. Each query returned zero records. A broader web query restricted to `arxiv.org` returned English-language convex-optimization material and unrelated Indonesian-language-processing work, but no reasonably representative Indonesian-language convex-analysis or optimization source with downloadable TeX. The arXiv API was also attempted and returned HTTP 429; that failed API attempt is not treated as evidence. No claim is made that arXiv contains no Indonesian mathematics at all--only that this finite same-field search found no admissible comparator.

The required fallback is therefore:

- Caturiyati and Himmawati Puji Lestari, “Optimisasi Konveks: Konsep-Konsep,” *Prosiding Seminar Nasional Penelitian, Pendidikan dan Penerapan MIPA*, Universitas Negeri Yogyakarta, 14 May 2011.
- Official repository record: <https://eprints.uny.ac.id/7164/>.
- Official PDF URL: <https://eprints.uny.ac.id/7164/1/M-45%20-%20Caturiyati.pdf>.
- Frozen landing-page witness: 21,286 bytes; SHA-256 `088f79135da630d7230e7e7d656163bd4e47d4aff1a569235e10532b8d9bd620`.
- Frozen PDF witness: 204,675 bytes; 8 PDF pages; SHA-256 `02055e84a12d3179e0fe845ce8f0a38ca7c09fc0159781136642a668ca5df73c`.
- Inspection: all eight rendered pages and the complete extracted text were checked. The eighth page contains only the running header/page number.

The UNY record identifies the work, authors, year, proceedings, and Mathematics Education division. No open-content license for the PDF was found on the record or in the PDF. It is retained only as a local terminology witness and is not admitted, copied into the edition, committed, or redistributed.

## Terminology comparison and decisions

| Mathematical meaning | UNY usage observed in the actual PDF | Existing O015 usage | Decision for the O015 glossary |
|---|---|---|---|
| convex optimization | `optimisasi konveks` | `optimisasi konveks`; variant `optimasi konveks` | Keep `optimisasi konveks` preferred; keep `optimasi konveks` as an accepted variant; keep `optimalisasi konveks` rejected. |
| convex set/function; quasiconvex | `himpunan konveks`, `fungsi konveks`, `fungsi kuasikonveks` | `konveks`; `kuasikonveks` where needed | Keep. |
| affine | `affine` | `afin` | Keep normalized Indonesian `afin` preferred; register `affine` as an observed source-language/legacy variant. |
| supporting hyperplane | `bidang hiper penyokong` | `hiperbidang pendukung` | Keep `hiperbidang pendukung` preferred for compact morphology and established corpus consistency; register `bidang hiper penyokong` and `bidang hiper pendukung` as accepted variants. |
| objective function | `fungsi tujuan` or `fungsi biaya` | `fungsi objektif`, `objektif`, `nilai objektif`; `fungsi biaya` for transport cost | Register generic `fungsi tujuan` as the didactic preferred form, with `fungsi objektif` and compact `objektif` as accepted variants. Use `fungsi biaya` only when the mathematical objective is specifically a cost. Existing compact usages are precise and need no semantic rewrite. |
| feasible point/set | `titik layak`, `himpunan layak` | `layak` | Keep `layak` preferred; reject no existing text. |
| inequality | `ketaksamaan` | overwhelmingly `ketaksamaan`, with a few explanatory uses of `pertidaksamaan` | Keep `ketaksamaan` preferred; register `pertidaksamaan` as an accepted regional/register variant rather than treating it as an error. |
| domain | `domain` | `domain` | Keep. |
| epigraph | `epigraf` | `epigraf` | Keep. |
| sublevel set | `himpunan sublevel` | not yet glossary-registered | Prefer `himpunan sublevel`; register `himpunan subaras` only as a possible explanatory variant if later evidence supports it. |
| polyhedron/polytope | `polihedron`, `politop` | `politop` | Prefer `polihedron` and `politop` for the distinct objects. |
| positive semidefinite | `semidefinit positif` | `semidefinit` with sign adjective | Keep. |
| range/null space | `jangkauan matriks`, `ruang null matriks` | not yet glossary-registered | Prefer `jangkauan` and normalized `ruang nul`; register `ruang null` as the observed variant. |
| gradient/Hessian | `gradien`, `Hessian` | `gradien`, `Hessian` | Keep. |

## Propagation decision

No admitted mathematical statement has a meaning error. The differences involving `objektif`, `afin`, and `hiperbidang pendukung` are legitimate register variants; mechanically replacing them would reduce internal consistency without improving mathematical meaning. One narrow consistency correction is justified: the four isolated occurrences of `pertidaksamaan` were normalized to the established preferred form `ketaksamaan` in the Penn Chapter 4 wrapper (two occurrences), Penn Chapter 5 wrapper (one occurrence), and preserved unadmitted Penn Chapter 6 candidate (one occurrence). This is supported by 61 pre-existing `ketaksamaan` occurrences in the translated lane and exclusive `ketaksamaan` usage in the UNY comparator. The affected admitted wrappers/readers are rebuilt and revalidated rather than silently changing source bytes only.

The machine glossary is refined with the evidence-backed preferred/variant distinctions, and the MIT pilot introduces a generic objective as `fungsi tujuan` while retaining compact variants where context makes them unambiguous.

The one consistency rule that is enforced going forward is semantic rather than cosmetic: `fungsi biaya` is reserved for a cost objective, while `fungsi tujuan` is the neutral generic term. The frozen UNY PDF supplies terminology evidence only; none of its prose, formulas, or layout enters the derivative.

## L03 page-14 terminology extension (2026-08-23)

The bounded page-14 unit adds only standard method labels and the LP/NLP
abbreviations. `optimisasi konveks`, `program/pemrograman linear`, and
`pemrograman nonlinier` remain the preferred Indonesian forms. `simpleks` is
retained as the established Indonesian spelling of *simplex*; `nonsimpleks`
is used as the compact contrastive adjective in the source sentence.
`bidang potong`, `titik interior`, and `subgradien` are retained as the
standard method names already compatible with the lane glossary. `dualitas`
remains the source label; no alternative `dualisme` term is introduced. No
L03 term required propagation into earlier units.

## Becker-01 terminology extension (2026-08-25)

The Becker Lagrange-Slater-KKT unit was checked against the same frozen UNY
terminology witness and the admitted lane glossary. It retains
`optimisasi konveks`, `dualitas`, `pengali Lagrange`, `kondisi Slater`,
`titik pelana`, `semidefinit positif`, `gradien`, `proyeksi`, and
`Karush-Kuhn-Tucker`. The unit uses `kendala pertidaksamaan` for the constraint
type and `ketaksamaan` for an inequality relation or inequality direction.
This is a deliberate semantic/register distinction within the previously
accepted `pertidaksamaan` variant, not an accidental terminology fork. No term
required propagation into Habring or the preserved companion readers.

## Becker-02 terminology extension (2026-08-25)

The bounded Douglas--Rachford unit retains `pemisahan Douglas--Rachford`,
`operator proksimal`, `subdiferensial`, `aturan jumlah`, `titik tetap`,
`konjugat Fenchel`, `parameter relaksasi`, and `solusi optimal`. These choices
are mathematically precise and consistent with the admitted Habring vocabulary.
In particular, the source category `proper` remains `proper`, rather than the
less stable literal alternative `sejati`, and the subdifferential identity is
called an `aturan jumlah`, not a parallel `kaidah jumlah`. The frozen UNY
witness does not cover these narrow monotone-operator terms, so it supplies no
contrary evidence and no new external comparator was sought. The two internal
consistency fixes were propagated through the complete Becker-02 body before
PDF, HTML, open-math, and browser QA. No earlier admitted unit requires a
terminology rewrite.
