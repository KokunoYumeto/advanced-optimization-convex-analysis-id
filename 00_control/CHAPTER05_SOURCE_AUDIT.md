# Habring Chapter 5 source audit

As of: 2026-08-21  
Authority: `authority/habring/source-v1/proximal_gradient.tex`  
Identity: 18,464 bytes; 336 lines; SHA-256 `59d5694742f0e2f9f46da0c1418b5fe0ff18521c49078ed29c843b6e8c701f6e`

## Closure and topology

The file has 78 balanced, correctly nested environments: 42 `equation`, 13 `aligned`, 6 `lemma`, 6 `proof`, 2 `defn`, 2 `enumerate`, 2 `example`, 2 `rem`, 2 `cases`, and 1 `theorem`. It also has one `\[...\]` display. There are nine label occurrences but only eight unique labels because `proximal:eq:moreau_diff2` is duplicated. The sole citation is `beck2017first`. There are no figures, input dependencies, or footnotes. Informal learner prompts are “(why?)”, “Exercise.”, and the unfinished placeholder “Projection, 1 norm, 2 norm”.

Backward references are `preliminaries:thm:direct_method` and `convexity:thm:minimum`; the latter does not by itself cover the extended-valued objective used here. Conceptual prerequisites are proper/lower-semicontinuous/coercive functions, subgradients and their sum/scaling rules, monotonicity, projection, convexity, and Lipschitz gradients. There are no forward chapter references.

## Determined correction plan

1. Qualify the opening as the basic/worst-case subgradient rate. Before converting the implicit inclusion to an optimality condition, state that `f` is proper, lower semicontinuous, convex and that `tau_k>0`.
2. Repair the prox-uniqueness display: it repeats `y_1`, then equates a scalar objective value with `argmin`. Define the scalar objective and write strict midpoint inequality against its minimum.
3. In the stationary-point lemma, fix a step `tau>0`; state and prove the equivalence with `0 in partial(f+g)(x)`. The authority statement is false at zero step.
4. In the Moreau envelope, require `tau>0`, use `inf` before attainment is known, and restore the missing square on the prox-distance term.
5. Require a nonempty set in the projection example and repair `x_t` to `x_i` in soft thresholding.
6. State proper/lower-semicontinuous/convex assumptions for single-valued prox; repair malformed vector/scalar domains and require `gamma>=0` in the scaling rule.
7. Repair the Moreau proof: supply a valid extended-valued convexity argument, replace `p(y)` by `p(x)`, define the differentiability residual correctly, move the subgradient from `partial f(x)` to `partial f(p(x))`, and remove or rename the duplicate label.
8. Complete the unfinished example with projection, soft-thresholding, and Euclidean shrinkage formulas, including the zero convention.
9. Repair the convergence theorem: assume `L>0`, a nonempty minimizer set, and `0<tau_min<=tau_k<=1/L`; restore the missing factor 2 in the polarization step; sum over `k=0,...,n-1`; state convergence to some minimizer; and remove the stray parenthesis. Also correct the authority typo `tau_k<=L` to `tau_k<=1/L`.

Every implemented substantive repair must receive a new event after `O015-HAB-ADV-0027`; optional exposition and ordinary Indonesian translation do not.

## Stable contiguous partition

- `d90.hab.v1.ch05.seg0001` — lines 1–34: implicit step and proximal-map definition.
- `d90.hab.v1.ch05.seg0002` — lines 36–62: prox existence, uniqueness, and characterization.
- `d90.hab.v1.ch05.seg0003` — lines 64–94: composite problem, algorithm, stationary points.
- `d90.hab.v1.ch05.seg0004` — lines 96–143: Moreau definition, identity, and core examples.
- `d90.hab.v1.ch05.seg0005` — lines 145–155: prox computation rules.
- `d90.hab.v1.ch05.seg0006` — lines 157–236: Moreau smoothing theorem, gradient identity, and interpretation.
- `d90.hab.v1.ch05.seg0007` — lines 238–267: descent lemma and gradient-mapping notation.
- `d90.hab.v1.ch05.seg0008` — lines 269–336: proximal-gradient convergence theorem and proof.

## Immediate production cursor

Translate `seg0001` through `seg0008` contiguously in source order into `source/id-ID/habring-05-metode-gradien-proksimal-id.tex`. Preserve all 78 ordered environments, the unique source labels, the Beck citation, and learner prompts; replace the duplicate label with an explicitly mapped unique target label. Build a standalone id-ID wrapper, add open proximal/forward–backward numerical checks, expose all corrections in the reader and adverse ledger, and do not claim language review or tagged-PDF accessibility before they exist.

