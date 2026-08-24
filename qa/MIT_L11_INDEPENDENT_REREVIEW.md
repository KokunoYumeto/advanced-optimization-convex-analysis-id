# MIT L11 Independent Mathematical Rereview

Date: 2026-08-24  
Scope: MIT 6.253 complete-notes printed/PDF pages 86-97 (all of Lecture 7); printed/PDF page 98 is the independently confirmed Lecture 8 delimiter and is excluded.  
Mode: independent, read-only adversarial comparison of the final Indonesian semantic reader against the frozen PDF and the live English semantic witness.

## Exact reviewed inputs

| Role | Path relative to repository root | Bytes | SHA-256 |
|---|---|---:|---|
| Frozen authority | `authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf` | 8,030,116 | `41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181` |
| English semantic witness | `source/en/mit-11-lecture-7-separation-conjugacy-semantic-witness.md` | 23,801 | `625efb8801d24c270d2bf851bf1c7fb27cb307146742d7cbddc00b5cb5873c8c` |
| Final Indonesian target | `source/id-ID/mit-11-kuliah-7-pemisahan-dan-konjugasi-id.md` | 25,023 | `f908901609e1a1e6091734b55ba63b980f491dd5a5e4e813621816cbceb1c32b` |

These are the byte identities to which this rereview applies. The final target includes the `.keep-proof-conclusion` class on `d90-mit-l11-p096-i003`; I reread the target after that class was added. The class preserves the repaired proof conclusion during rendering and does not change the item's mathematical or Indonesian prose.

## Coverage and topology check

Every source page was inspected visually in the frozen PDF and compared with the corresponding witness and target page fence. The stable-ID sets are exactly identical between witness and target, with no missing, target-only, or duplicate IDs. Source-page and within-page order attributes are contiguous.

| Page | Subject checked | Items | Displays | Figures | Panels |
|---:|---|---:|---:|---:|---:|
| 86 | Lecture outline and reading boundary | 6 | 0 | 0 | 0 |
| 87 | Fundamental characterization and proper separation | 3 | 1 | 1 | 3 |
| 88 | Proper polyhedral separation | 3 | 2 | 1 | 2 |
| 89 | Nonvertical hyperplanes and intercept geometry | 4 | 0 | 1 | 2 |
| 90 | Nonvertical hyperplane theorem and proof | 4 | 1 | 0 | 0 |
| 91 | Convex conjugate definition and lower-bound geometry | 2 | 2 | 1 | 1 |
| 92 | Affine, absolute-value, and quadratic examples | 1 | 1 | 1 | 6 |
| 93 | Biconjugate definition, convexity, and closedness | 5 | 3 | 0 | 0 |
| 94 | Conjugacy visualization and envelope interpretation | 1 | 2 | 1 | 1 |
| 95 | Four-part conjugacy theorem | 1 | 4 | 0 | 0 |
| 96 | Proof of parts (a) and (c) | 3 | 1 | 1 | 1 |
| 97 | Improper-function counterexample | 3 | 4 | 0 | 0 |
| **Total** |  | **36** | **21** | **7** | **16** |

The twelve page fences are `d90-mit-l11-p086` through `d90-mit-l11-p097`. The seven semantic figure descriptions preserve all sixteen separately meaningful source panels without copying the source pixels. Their stated set positions, normals, tangent/separator relationships, vertical intercepts, conjugate pairs, envelope geometry, and repaired page-96 sign convention agree with the rendered authority.

## Mathematical and language rereview

The rereview covered every theorem, proof step, display, example, counterexample, and figure-dependent claim, not only the disclosed defects. In particular:

- The relative-interior criteria on pages 87-88, the nonvertical intercept formula on page 89, and the nonvertical-halfspace statement on page 90 retain the source hypotheses, quantifiers, and inequality directions.
- The page-90 perturbation proof now supplies a consistently oriented vertical separator, a nonvertical halfspace functional nonnegative on (C), and the sufficiently-small positive-epsilon margin. Its conclusion follows without an omitted sign step.
- All occurrences of the conjugate and biconjugate definitions use the correct variables, domains, transpose products, suprema, and extended-real values. The three examples on page 92 were recomputed; the affine and absolute-value conjugates are correct, and the quadratic formula is correct with the added hypothesis (c>0).
- The page-95 theorem preserves parts (a)-(d), including the condition on the convex closure in part (d). The repaired page-96 proof is valid: strict separation gives (f(u)\ge y'u-c) and \(\gamma<y'x-c\), hence (f^*(y)\le c) and (f^{**}(x)>\gamma), contradicting epigraph membership. The final target's keep-proof-conclusion class leaves this content unchanged.
- The page-97 scalar counterexample was recomputed in the stated extended-real convention: (f^*\equiv+\infty), (f^{**}\equiv-\infty), and the stated convex closure comparison follows. Its scalar domain and broadened codomain are explicit.
- Indonesian mathematical meaning is faithful and internally consistent: *himpunan konveks*, *selubung konveks*, *setengah ruang*, *hiperbidang*, *pemisahan proper/ketat*, *interior relatif*, *kerucut resesi*, *epigraf*, *konjugat/bikonjugat*, *fungsi afin*, *batas bawah*, and *ketercapaian* are used with their correct mathematical roles. I found no mistranslated negation, quantifier, condition, implication, comparison, or proof dependency.

## Disclosed correction audit

All ten correction events occur exactly once in each witness and target and are applied in the target. Their numeric identifiers are not page order; the actual page-order sequence is:

1. Page 88 - `O015-MIT-SEM-0034`: remove the unwarranted claim that (C) itself is nonpolyhedral; state that (C) need not be polyhedral.
2. Page 89 - `O015-MIT-SEM-0035`: clarify that the prohibited object is a complete two-sided vertical line, not an upward vertical ray.
3. Page 90 - `O015-MIT-SEM-0036`: supply the suppressed orientation, sign-preservation, and small-positive-epsilon argument.
4. Page 91 - `O015-MIT-SEM-0037`: call the affine hyperplanes lower-bounding in general and supporting only when the supremum is attained.
5. Pages 91 and 95 - `O015-MIT-SEM-0040`: replace the printed function-type `\mapsto` with `\to`, retaining `\mapsto` only for element-to-value mappings.
6. Page 92 - `O015-MIT-SEM-0031`: add (c>0) to the quadratic-conjugate example.
7. Page 93 - `O015-MIT-SEM-0038`: replace “linear” with “affine” for (y\mapsto x'y-f(x)).
8. Page 94 - `O015-MIT-SEM-0039`: distinguish the general envelope (f^{**}\le f) from equality under the closed-proper-convex hypotheses.
9. Page 96 - `O015-MIT-SEM-0032`: replace the sign-defective intercept argument with the valid direct separator inequality proof and correct the semantic figure's intercept signs.
10. Page 97 - `O015-MIT-SEM-0033`: make the example scalar, quantify over \(\mathbb R\), and state the codomain that permits \(-\infty\).

`O015-MIT-SEM-0040` is therefore the fifth correction in page order even though it has the largest event number. No correction disclosure changes an unrelated source claim, and no source defect remains silently embedded in the learner-facing mathematics.

## Result

- **P1: 0** - no mathematical invalidity, missing substantive source unit, or learner-dangerous semantic change.
- **P2: 0** - no theorem/proof/example defect, correction failure, topology mismatch, or material Indonesian meaning error.
- **P3: 0** - no minor notation, locator, identifier, figure-description, terminology, or disclosure defect requiring action.

**Independent rereview result: PASS.** No actionable findings remain for the exact target bytes bound above.
