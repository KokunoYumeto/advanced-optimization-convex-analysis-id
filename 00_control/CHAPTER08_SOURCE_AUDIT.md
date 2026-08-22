# Habring Chapter 8 source audit

As of: 2026-08-22  
Authority: `authority/habring/source-v1/stochastic.tex`  
Identity: 4,665 bytes; 107 lines; SHA-256 `610d11b59d8dfabbbbe6fbc509a0f9ac1727540458c67f8cd3b7bab49566a07d`

## Closure and topology

The authority is one compact editable TeX chapter on stochastic gradient descent. It has exactly 24 ordered environments: 15 `equation`, 5 `aligned`, 2 `cases`, 1 `theorem`, and 1 `proof`. Its sole label, `stochastic:eq:gradient`, has one matching `eqref`. There are no figures, external assets, citations, bibliography dependencies, footnotes, list items, formal exercises, hints, answers, solutions, code, or included-file surfaces.

The conceptual dependencies are convex subgradients and their norm bound for globally Lipschitz convex functions; metric projection onto a nonempty closed convex set; filtrations and conditional expectation/variance; and elementary telescoping and weighted-best-iterate estimates.

## Determined correction disposition

Eight exact events, `O015-HAB-ADV-0076` through `O015-HAB-ADV-0083`, are integrated in `ADVERSE_LEDGER.jsonl`:

1. normalize the finite-sum and least-squares objectives by `1/N`, so a uniformly sampled component gradient is actually unbiased;
2. state convexity, global Lipschitzness, the nonempty closed convex set, attained minimizer, initial point, positive steps, and the projected stochastic iteration used by the proof;
3. formulate oracle unbiasedness and variance conditionally with respect to the pre-sample filtration;
4. define the best-iterate value and use one consistent `K`, `0,...,K-1` indexing convention;
5. replace the invalid unconditional random-iterate variance manipulation by the exact conditional second-moment identity;
6. restore the missing factor `1/2` after summing the one-step recurrence;
7. replace the inconsistent `sigma_n` algebra by `S_K=sum tau_k`, `Q_K=sum tau_k^2`, the sharp direct bound, and the sufficient limits `S_K -> infinity`, `Q_K/S_K -> 0`; and
8. normalize the malformed expectation/alignment notation and determined prose typo.

An independent source audit confirms that the repaired result proves expected convergence of the best objective value only; it does not claim last-iterate or almost-sure convergence.

## Stable contiguous partition

- `d90.hab.v1.ch08.seg0001` — source lines 1--34: motivation, normalized finite-sum model, component sampling, and unbiasedness.
- `d90.hab.v1.ch08.seg0002` — lines 36--50: projected-SGD theorem and stochastic/stepsize assumptions.
- `d90.hab.v1.ch08.seg0003` — lines 51--107: projection recursion, conditional estimates, telescoping, and best-iterate convergence.

## Admission outcome

The complete target is `source/id-ID/habring-08-penurunan-gradien-stokastik-id.tex`, 6,378 bytes, SHA-256 `f610aaec91aa9b76582f251458da65d25cc37a933a51da478cad13ee16e5a344`. The 5,129-byte standalone wrapper has SHA-256 `d00ea41830af388c227a1054025f049a9315da6f41675573965042d320eb7428` and records exact authority, attribution, CC BY 4.0, changes, corrections, prerequisites, and non-endorsement.

The independent structural/formula audit passes twice with P1=0, P2=0, P3=0 and preserves all 24 ordered environments, the label/reference pair, all nonblank source-line closure, and three stable segments. It aligns 38 source and 61 target formula surfaces into seven substantive delta blocks, every one bound to the integrated events above. The 24,702-byte formula manifest has SHA-256 `2f9632d02071ded0c84d54ca17af019137cecfe18245d94a7e9243449c0e9fe9`.

The deterministic validator passes 24/24 gates twice with byte-identical output. It checks the finite-sum normalization and missing-factor negative control, three exact conditional-oracle states, the conditional second-moment identity, projection and the one-step recurrence, ten exact-enumeration best-iterate cases, and the source's failing extra-`Q_K` asymptotic algebra. Its 21,107-byte receipt has SHA-256 `3b78aa1140a08cf811493f37496b10c2955f02bec570385dcde6480f37578f22`.

Two fixed-epoch builds produce the same 346,785-byte, 8-page A4 PDF, SHA-256 `c1ed028667c5df3fd0a837807e2a17bf7a9e1fa3170938853c9a96b9670fa86a`. Every page was rendered and inspected; no clipping, collision, broken glyph, blank content page, or unreadable formula was found. The log has no error, unresolved reference, missing glyph, or box warning. The PDF is searchable, unencrypted, declares `/Lang` `id-ID`, and embeds fonts with Unicode mappings. It remains untagged and independent Indonesian language review remains unrecorded.

Chapter 8 is admitted. The next source-order cursor is `authority/habring/source-v1/optimal_transport.tex` (Chapter 9; 15,378 bytes; SHA-256 `719df724b368126cc7540dffd461dc33aba7d5b5b6060132181086dfa17649ba`).
