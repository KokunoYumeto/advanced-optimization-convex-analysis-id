# O015 current state

As of: 2026-08-21  
Lane: D90 — Advanced Optimization and Convex Analysis  
Locale: id-ID  
Status: two bounded reader units admitted; Chapter 5 is active; corpus is incomplete

## Ownership and scope

This is the sole active O015 production lane. It owns one Indonesian reader corpus, one locale-neutral modular backend, and one corpus-specific GitHub repository. O018 is adjacent but disjoint: it owns LP/IP modeling, simplex, finite-dimensional LP duality, sensitivity, graph/network algorithms, and general OR solver workflows. The curriculum coordinator owns the later global hub; this lane does not.

## Frozen authority

- Andreas Habring, *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1, CC BY 4.0: immutable PDF, source tar, API record, legal code, and 22-file editable closure are bound in `SOURCE_AUTHORITY.json`.
- Christopher Griffin, *Nonlinear Programming* / Penn State MATH 555, CC BY-NC-SA 3.0 US: editable v1.0 source plus the public v1.0.1 PDF correction witness are frozen. Penn is admitted only for the later non-overlapping smooth numerical sequence.
- The bounded comparator pass found no stronger source that simultaneously provides editable closure, derivative permission, modern nonsmooth coverage, and solutions.

## Admitted reader units

Habring Chapter 3, “Subgradients,” has been translated contiguously as `source/id-ID/habring-03-subgradien-id.tex` and wrapped by `source/id-ID/D90-HAB-03-subgradien-id.tex`.

- Authority source: 16,939 bytes; SHA-256 `c3b447ee9ea5d8dbf98333b927ad5b7408d1d66884c3b7d5590251dfc47c5405`.
- Indonesian unit: 19,266 bytes; SHA-256 `d04ff82898c157f56924c6c08fd204bcd97625f060847fd8a0b6f7a2b90b0a5c`.
- Reader PDF: 15 A4 pages; 516,084 bytes; SHA-256 `45f7bc24ff46079881e42be9aa6f1b508c324a208f2b4dd82e35e7e3a6d544b4`.
- Habring Chapter 4, “Projected subgradient descent,” is translated contiguously as `source/id-ID/habring-04-metode-subgradien-terproyeksi-id.tex` and wrapped by `source/id-ID/D90-HAB-04-metode-subgradien-terproyeksi-id.tex`.
- Chapter 4 authority source: 14,391 bytes; SHA-256 `44ac28a0f0b67fed4855f7ed91089fab52f77804115f2a06201bff98437bd8da`.
- Chapter 4 Indonesian unit: 16,612 bytes; SHA-256 `29fdc330007009bd765a17ca1dcd0cf130ff802312ebb402bf03413da5f96a7d`.
- Chapter 4 reader PDF: 13 A4 pages; 370,824 bytes; SHA-256 `5c9991af837995b2e24f4a9060eb3b0efe7b2d71a9bbde01948eeb81ebfd63b7`.
- Stable backend: 238 two-unit records, including 19 source-linked translation segments; the deterministic JSONL and lossless CSV projection are validated by `qa/validate_backend.py`.

Chapter 3 preserves all 61 source environments and eleven stable segments. Chapter 4 preserves all 67 source environments, four authority labels, and eight stable segments. Twenty-seven mathematically determined source corrections across the two units are explicit in `ADVERSE_LEDGER.jsonl`; no correction was reported upstream during production.

## Admission evidence

- Structural/formula audits: PASS for both units; Chapter 3 has 46 dispositioned formula-delta blocks (manifest `c979be4e…`), and Chapter 4 has 40 (manifest `d0453330…`).
- Independent mathematical rereviews: PASS for both units, each with P1=0, P2=0, P3=0.
- Open computation checks: PASS with Python 3.13.9, NumPy 2.4.4, SciPy 1.17.1, HiGHS, and SLSQP.
- PDF builds: forced final rebuilds produced byte-identical artifacts; no overfull/underfull boxes, unresolved references, or TeX errors.
- Visual review: all 28 physical pages across both PDFs inspected; selected mathematical and correction surfaces inspected at full size; no clipping, collision, or unreadable page found.
- Accessibility: searchable text, `/Lang` set to `id-ID`, Indonesian descriptions for both figures. The PDF is untagged; semantic HTML/EPUB remains required before final corpus publication.

## Known incomplete surfaces

The authority supplies sparse informal exercises and no systematic hints, answers, or solutions in the admitted units. Independent Indonesian language review has not yet been recorded. The full Habring module, Penn module, authored assessment layer, semantic HTML/EPUB reader, and final corpus publication remain incomplete.

## Public corpus checkpoint

The discoverable public corpus repository is `https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id`. Its first `main` checkpoint contains the verified Chapter 3 and Chapter 4 Indonesian TeX/PDF readers, frozen Habring authority closure, QA, per-component rights controls, and the 238-record backend. Public-byte readback matched the local README, both PDFs, and backend exactly. Details are in `PUBLICATION_RECEIPTS.md`. No upstream contact has occurred.

## Exact continuation

Continue with `authority/habring/source-v1/proximal_gradient.tex` (Chapter 5, proximal-gradient methods; 18,464 bytes; SHA-256 `59d5694742f0e2f9f46da0c1418b5fe0ff18521c49078ed29c843b6e8c701f6e`). Correct only independently determined source defects with ledger entries, preserve source topology and identifiers, and add open numerical checks for proximal mappings and forward–backward iteration. Translation remains the dominant activity. Completion of this edition remains independent of the curriculum root's later admission decision.
