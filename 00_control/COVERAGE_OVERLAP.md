# O015 coverage and overlap boundary

Date: 2026-08-21  
Role: D90 — Advanced Optimization and Convex Analysis

## Admitted composite

No single candidate passed editable-source, derivative-rights, build-closure, modern-coverage, and solution-surface requirements. The admitted spine is therefore deliberately composite:

- Penn State MATH 555 supplies mature smooth numerical optimization and constrained numerical methods. It is a static LaTeX archive under CC BY-NC-SA 3.0 US.
- Andreas Habring's arXiv:2607.11664v1 supplies the modern convex/nonsmooth module under CC BY 4.0.
- MIT OCW 6.253 may later supply a separately attributed CC BY-NC-SA 4.0 solved-assessment component. It is not the editable spine.
- Any genuinely missing exercises, solutions, accessibility descriptions, or connective bridge prose must be independently authored and separately identified.

## O018 exclusion boundary

Open Optimization Book 1 already owns LP/IP modeling, simplex and tableau mechanics, LP duality and complementary slackness, sensitivity analysis, graph/network/discrete algorithms, operations-research case studies, and introductory Excel/Python solver workflows. The O015 reader cross-references that lane instead of retranslating it.

Consequences:

- Penn Chapter 9 is excluded from O015.
- Penn's general preliminaries are not repeated unless a narrow local prerequisite is indispensable.
- Habring's Fenchel duality remains admitted because it is not the same surface as finite-dimensional LP duality.
- MO-book application notebooks remain reference material, not a source whose printed Cambridge book rights are inferred from the repository license.

## Penn State admission boundary

Admit: line search, gradient methods, Newton and corrected Newton, conjugate directions/CG, DFP/BFGS, numerical differentiation, derivative-free methods, feasible directions/Frank--Wolfe, nonlinear KKT/Fritz John, active-set quadratic programming, and the written penalty-method material.

Do not claim:

- exact editable source for public version 1.0.1;
- complete interior-point coverage—the SQP, barrier, interior-point simplex, and interior-point QP headings in Chapter 11 are empty;
- an open, reproducible Maple/C++ computational closure;
- hints/answers/solutions beyond the exact counts in `SOURCE_AUTHORITY.json`.

## Habring admission boundary

Chapters 1 and the elementary part of Chapter 2 are prerequisite/overlap material. The first genuinely non-overlapping unit is Chapter 3, “Subgradients,” printed pages 30–37. It establishes the convex subdifferential, normal cones, calculus rules, the Fermat condition, and constrained optimality required by later projected/proximal methods. Chapter 4, “Projected subgradient descent,” is the next source-order cursor.

Habring is not a complete mastery text by itself: it has only three formal exercises, no hints/answers/solutions, no code, untagged PDF output, raster-only figure assets, and author-declared nonfinal prose.

## Bounded comparator stop

Exactly three alternatives were assessed and the search stopped:

1. Clason–Valkonen, arXiv:2001.00216v7 / SIAM MO38: strongest modern LaTeX benchmark (514 pages), but the arXiv record grants only nonexclusive distribution and the SIAM book is copyrighted; translation rights are absent and no exercise/solution system was found.
2. MIT OCW 6.253: lawful CC BY-NC-SA 4.0 course with five solved homework sets and solved exams, but only PDF/HTML mathematical artifacts and an older classical emphasis.
3. Durea–Strugariu (2014): substantial 73-page exercises-and-solutions chapter, but CC BY-NC-ND 3.0 expressly blocks translation and no editable source is public.

No candidate met all three mandatory properties: editable closure, derivative permission, and meaningful solutions. The Penn + Habring composite remains the strongest lawful production choice.
