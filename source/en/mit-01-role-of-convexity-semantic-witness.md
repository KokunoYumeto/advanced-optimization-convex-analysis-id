---
title: "MIT 6.253 Lecture 1 semantic transcription witness"
subtitle: "Complete-notes PDF pages 2-5"
author: "Dimitri P. Bertsekas (source author)"
lang: en
date: "2026-08-22"
rights: "CC BY-NC-SA 4.0"
---

This is a project-made semantic transcription witness for the first topic of
MIT OpenCourseWare 6.253, *Convex Analysis and Optimization*, Spring 2012. It
is bound to complete-notes PDF pages 2--5 and is not official editable MIT
source. Lineation and identifiers are new; wording, mathematics, and order
transcribe the source. The boundary contains no figures. Production and QA
assistance: **OpenAI Codex gpt-5.6-sol, Ultra**, at the repository user's
direction. No endorsement by MIT, Athena Scientific, or the source author is
implied.

::: {.source-page #src-mit-l01-p002 data-source-page="2" data-source-order="1"}
## Lecture 1: An Introduction to the Course

### Lecture Outline

::: {.source-item #src-mit-l01-p002-i001 data-source-page="2" data-source-order="1"}
- The Role of Convexity in Optimization
:::

::: {.source-item #src-mit-l01-p002-i002 data-source-page="2" data-source-order="2"}
- Duality Theory
:::

::: {.source-item #src-mit-l01-p002-i003 data-source-page="2" data-source-order="3"}
- Algorithms and Duality
:::

::: {.source-item #src-mit-l01-p002-i004 data-source-page="2" data-source-order="4"}
- Course Organization
:::
:::

::: {.source-page #src-mit-l01-p003 data-source-page="3" data-source-order="2"}
## History and Prehistory

::: {.source-item #src-mit-l01-p003-i001 data-source-page="3" data-source-order="1"}
- **Prehistory: Early 1900s--1949.**

  - Caratheodory, Minkowski, Steinitz, Farkas.
  - Properties of convex sets and functions.
:::

::: {.source-item #src-mit-l01-p003-i002 data-source-page="3" data-source-order="2"}
- **Fenchel--Rockafellar era: 1949--mid 1980s.**

  - Duality theory.
  - Minimax/game theory (von Neumann).
  - (Sub)differentiability, optimality conditions, sensitivity.
:::

::: {.source-item #src-mit-l01-p003-i003 data-source-page="3" data-source-order="3"}
- **Modern era--Paradigm shift: Mid 1980s--present.**

  - Nonsmooth analysis (a theoretical/esoteric direction).
  - Algorithms (a practical/high impact direction).
  - A change in the assumptions underlying the field.
:::
:::

::: {.source-page #src-mit-l01-p004 data-source-page="4" data-source-order="3"}
## Optimization Problems

::: {.source-item #src-mit-l01-p004-i001 data-source-page="4" data-source-order="1"}
- **Generic form:**

  $$
  \begin{aligned}
  \text{minimize}\quad & f(x) \\
  \text{subject to}\quad & x\in C.
  \end{aligned}
  $$

  Cost function $f:\mathbb{R}^n\mapsto\mathbb{R}$, constraint set $C$, e.g.,

  $$
  \begin{aligned}
  C ={}& X\cap\{x\mid h_1(x)=0,\ldots,h_m(x)=0\}\\
       & {}\cap\{x\mid g_1(x)\leq 0,\ldots,g_r(x)\leq 0\}.
  \end{aligned}
  $$
:::

::: {.source-item #src-mit-l01-p004-i002 data-source-page="4" data-source-order="2"}
- Continuous vs discrete problem distinction.
:::

::: {.source-item #src-mit-l01-p004-i003 data-source-page="4" data-source-order="3"}
- Convex programming problems are those for which $f$ and $C$ are convex.

  - They are continuous problems.
  - They are nice, and have beautiful and intuitive structure.
:::

::: {.source-item #src-mit-l01-p004-i004 data-source-page="4" data-source-order="4"}
- However, convexity permeates all of optimization, including discrete
  problems.
:::

::: {.source-item #src-mit-l01-p004-i005 data-source-page="4" data-source-order="5"}
- Principal vehicle for continuous-discrete connection is duality:

  - The dual problem of a discrete problem is continuous/convex.
  - The dual problem provides important information for the solution of the
    discrete primal (e.g., lower bounds, etc.).
:::
:::

::: {.source-page #src-mit-l01-p005 data-source-page="5" data-source-order="4"}
## Why Is Convexity So Special?

::: {.source-item #src-mit-l01-p005-i001 data-source-page="5" data-source-order="1"}
- A convex function has no local minima that are not global.
:::

::: {.source-item #src-mit-l01-p005-i002 data-source-page="5" data-source-order="2"}
- A nonconvex function can be “convexified” while maintaining the optimality
  of its global minima.
:::

::: {.source-item #src-mit-l01-p005-i003 data-source-page="5" data-source-order="3"}
- A convex set has a nonempty relative interior.
:::

::: {.source-item #src-mit-l01-p005-i004 data-source-page="5" data-source-order="4"}
- A convex set is connected and has feasible directions at any point.
:::

::: {.source-item #src-mit-l01-p005-i005 data-source-page="5" data-source-order="5"}
- The existence of a global minimum of a convex function over a convex set is
  conveniently characterized in terms of directions of recession.
:::

::: {.source-item #src-mit-l01-p005-i006 data-source-page="5" data-source-order="6"}
- A polyhedral convex set is characterized in terms of a finite set of extreme
  points and extreme directions.
:::

::: {.source-item #src-mit-l01-p005-i007 data-source-page="5" data-source-order="7"}
- A real-valued convex function is continuous and has nice differentiability
  properties.
:::

::: {.source-item #src-mit-l01-p005-i008 data-source-page="5" data-source-order="8"}
- Closed convex cones are self-dual with respect to polarity.
:::

::: {.source-item #src-mit-l01-p005-i009 data-source-page="5" data-source-order="9"}
- Convex, lower semicontinuous functions are self-dual with respect to
  conjugacy.
:::
:::

Source: Dimitri P. Bertsekas, *Lecture Slides on Convex Analysis and
Optimization*, MIT OpenCourseWare 6.253, Spring 2012, complete-notes PDF pages
2--5. This transcription witness is distributed with the derivative under
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
