# Habring Chapter 6 source audit

As of: 2026-08-22  
Authority: `authority/habring/source-v1/acceleration.tex`  
Identity: 18,873 bytes; 404 lines; SHA-256 `2ff1e10e9421c0fe01a09140e3e230cb2d3728c30c572bb6ca5513b229f1e605`

## Closure and topology

The file has 99 balanced `begin` tokens: 54 `equation`, 17 `aligned`, 8 `bmatrix`, 6 `pmatrix`, 2 `cases`, 3 `lemma`, 6 `proof`, 2 `theorem`, and 1 `cor`. Seven labels occur in order: `acceleration:eq:friction_ode`, `acceleration:lemma:spectral_radius`, `acceleration:cor:spectral_radius`, `acceleration:eq:heavy_ball1`, `eq:fista1`, `eq:fista2`, and `eq:fista3`. Four `cref` and four `eqref` uses are internal to the chapter. There are no citations, figures, assets, footnotes, or exercise environments. One informal exercise request is rendered near the end of the heavy-ball proof; a separate author TODO is commented out and is not reader-visible.

The hard backward dependency is Chapter 5 for the composite assumptions, proximal operator, and proximal-gradient map. Other prerequisites are convexity, strong convexity, smoothness, Hessians, Jordan form, spectral radius, and existence of a minimizer. The chapter has no hard forward source dependency.

## Determined correction plan

1. Repair the opening oracle lower bound by restoring the squared distance and stating convexity, `L`-smoothness, minimizer, and dimension qualification.
2. Replace the spectral-radius proof gaps: use a compatible operator norm and complexification; describe Jordan superdiagonal entries correctly; use the largest-block nilpotence index `m`; sum through `m-1`; handle spectral radius zero separately; correct the reversed maximizing endpoint; and take nth roots of a valid polynomial-times-exponential bound.
3. State the heavy-ball theorem for a `C^2` function near a stationary minimizer, `0<mu<=L`, and constant positive/admissible parameters. Define `q` as the spectral radius of the block linearization and qualify the optimal parameters as minimizing the worst-case spectral radius over Hessian eigenvalues in `[mu,L]`.
4. Replace the invalid placement of a nonlinear gradient inside a matrix. Write the nonlinear two-state recurrence first and then linearize the gradient difference with identity blocks.
5. Define the Hessian remainder with parentheses and use the correct perturbation `[-tau r_k;0]`.
6. Replace the invalid heavy-ball root analysis: derive the characteristic polynomial without dividing by the eigenvalue; use the Schur/Jury conditions; repair the endpoint factor; supply the equivalent-norm local-stability argument; and derive the worst-case optimal `q`, `beta`, and `tau` by equalizing endpoint roots. Preserve the source exercise request as a verification prompt only after the proof is complete.
7. Qualify heavy-ball optimality as a quadratic worst-case/local asymptotic statement rather than a global claim for every strongly convex `C^2` objective.
8. State the complete composite/FISTA assumptions, positive step, minimizer existence, initialization, update range, and theorem range. Restore the missing square in the smooth upper bound and repair malformed proof prose. The remaining FISTA energy identities and telescoping direction are retained.
9. Correct the determined source typos in the ODE indexing, spelling, grammar, and proof transitions without treating ordinary Indonesian phrasing as a mathematical correction.

Every implemented substantive repair must receive a new event after `O015-HAB-ADV-0038`. The source has no citation, so the derivative will not invent a bibliographic authority for the lower-bound statement; its hypotheses and scope will instead be made explicit and the lack of a source citation remains transparent.

## Stable contiguous partition

- `d90.hab.v1.ch06.seg0001` — lines 1–12: motivation and lower bound.
- `d90.hab.v1.ch06.seg0002` — lines 13–46: ODE derivation and heavy-ball update.
- `d90.hab.v1.ch06.seg0003` — lines 47–117: spectral-radius lemma and proof.
- `d90.hab.v1.ch06.seg0004` — lines 118–134: spectral-radius corollary and proof.
- `d90.hab.v1.ch06.seg0005` — lines 135–152: heavy-ball theorem statement.
- `d90.hab.v1.ch06.seg0006` — lines 153–224: state formulation and linearization.
- `d90.hab.v1.ch06.seg0007` — lines 225–260: eigenvalue argument, local convergence, parameter optimization, and source exercise request.
- `d90.hab.v1.ch06.seg0008` — lines 261–276: accelerated composite setup and FISTA iteration.
- `d90.hab.v1.ch06.seg0009` — lines 277–290: growth lemma for `t_k`.
- `d90.hab.v1.ch06.seg0010` — lines 291–332: fundamental proximal-gradient inequality.
- `d90.hab.v1.ch06.seg0011` — lines 333–339: FISTA theorem statement.
- `d90.hab.v1.ch06.seg0012` — lines 340–404: FISTA proof.

## Immediate production cursor

Translate all twelve segments contiguously in source order into `source/id-ID/habring-06-akselerasi-id.tex`, preserving the exact 99-environment topology and seven labels. Build a standalone id-ID wrapper, add open spectral-radius/heavy-ball/FISTA checks, expose every substantive repair in the adverse ledger and correction appendix, and do not claim independent language review or tagged-PDF accessibility before they exist.

