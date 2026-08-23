---
title: "MIT 6.253 Duality semantic transcription witness"
subtitle: "Complete-notes PDF pages 6-13"
author: "Dimitri P. Bertsekas (source author)"
lang: en
date: "2026-08-23"
rights: "CC BY-NC-SA 4.0"
---

This is a project-made semantic transcription witness for the MIT OpenCourseWare
6.253 complete-notes PDF, *Convex Analysis and Optimization*, Spring 2012. It is
bound to complete-notes PDF pages 6-13, from **Duality** through
**Exceptional Behavior**, and is not official editable MIT source. New lineation,
identifiers, and explanatory figure descriptions are project additions; the
wording, mathematics, order, and diagram labels transcribe the source.

The seven source figure surfaces in this boundary are intentionally not copied:
the notes identify their graphics as used by permission of Athena Scientific.
Each is represented below by an exact page locator, a semantic description, and
all retained mathematical labels. No source image byte, crop, or layout is
included. Production and QA assistance: **OpenAI Codex gpt-5.6-sol, Ultra**, at
the repository user's direction. No endorsement by MIT, Athena Scientific, or
the source author is implied.

::: {.source-page #src-mit-l02-p006 data-source-page="6" data-source-order="1"}
## Duality

::: {.source-item #src-mit-l02-p006-i001 data-source-page="6" data-source-order="1"}
- Two different views of the same object.
:::

::: {.source-item #src-mit-l02-p006-i002 data-source-page="6" data-source-order="2"}
- **Example: Dual description of signals.**

::: {.source-figure #src-mit-l02-p006-f001 data-source-page="6" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 6, signal example).** Two labeled
rectangles, **Time domain** and **Frequency domain**, are connected by a
two-headed arrow. The point is that the same signal can be represented in either
domain; no particular transform formula is asserted on this page.

**Source-figure description (source page 6, closed convex sets).** The left
view is a union of points filling a closed convex region. The right view is an
intersection of halfspaces whose boundary lines support the same region. The
two views are alternative descriptions of one closed convex set.

:::

::: {.source-item #src-mit-l02-p006-i003 data-source-page="6" data-source-order="3"}
- **Dual description of closed convex sets.**
:::
:::

*[Source page 6.]{.source-locator}
:::

::: {.source-page #src-mit-l02-p007 data-source-page="7" data-source-order="2"}
## Dual Description of Convex Functions

::: {.source-item #src-mit-l02-p007-i001 data-source-page="7" data-source-order="1"}
- Define a closed convex function by its epigraph.
:::

::: {.source-item #src-mit-l02-p007-i002 data-source-page="7" data-source-order="2"}
- Describe the epigraph by hyperplanes.
:::

::: {.source-item #src-mit-l02-p007-i003 data-source-page="7" data-source-order="3"}
- Associate hyperplanes with crossing points (the conjugate function).

::: {.source-figure #src-mit-l02-p007-f001 data-source-page="7" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 7, epigraph and conjugate).** In
coordinates $(x,f(x))$, a closed convex curve is touched by a line of slope
$y$. The line is labeled by the point $(-y,1)$; the retained labels are
$f(x)$, **Slope = $y$**, the axes $x$ and $0$, and the distinction between
**Primal Description: Values $f(x)$** and **Dual Description: Crossing points
$f^*(y)$**. The source also prints the following identity:

$$
\inf_{x\in\mathbb{R}^n}\{f(x)-x^\mathsf{T}y\}=-f^*(y).
$$
:::
:::

*[Source page 7.]{.source-locator}
:::

::: {.source-page #src-mit-l02-p008 data-source-page="8" data-source-order="3"}
## Fenchel Primal and Dual Problems

::: {.source-item #src-mit-l02-p008-i001 data-source-page="8" data-source-order="1"}
- **Primal problem:**

  $$
  \min_x\{f_1(x)+f_2(x)\}.
  $$
:::

::: {.source-item #src-mit-l02-p008-i002 data-source-page="8" data-source-order="2"}
- **Dual problem:**

  $$
  \max_y\{-f_1^*(y)-f_2^*(-y)\}.
  $$

  Here $f_1^*$ and $f_2^*$ are the conjugates.

::: {.source-figure #src-mit-l02-p008-f001 data-source-page="8" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 8, Fenchel primal/dual geometry).**
The primal panel compares the vertical distance between the graphs of $f_1(x)$
and $-f_2(x)$ at $x^*$. The dual panel compares the crossing-point
differentials of two parallel lines of slope $y$. Retained labels include
$f_1(x)$, $-f_2(x)$, $f_1^*(y)$, $f_2^*(-y)$, **Slope $y$**, $x^*$, and the
primal/dual descriptions **Vertical Distances** and **Crossing Point
Differentials**.
:::
:::

*[Source page 8.]{.source-locator}
:::

::: {.source-page #src-mit-l02-p009 data-source-page="9" data-source-order="4"}
## Fenchel Duality

::: {.source-display #src-mit-l02-p009-d001 data-source-page="9" data-display-order="1"}
The Fenchel equality is

  $$
  \min_x\{f_1(x)+f_2(x)\}
  =
  \max_y\{-f_1^*(y)-f_2^*(-y)\}.
  $$

::: {.source-figure #src-mit-l02-p009-f001 data-source-page="9" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 9, favorable Fenchel geometry).**
The same two-curve construction is shown with a line of slope $y^*$ at the
optimal crossing and another line of slope $y$. Labels include $f_1(x)$,
$-f_2(x)$, $f_1^*(y)$, $f_2^*(-y)$, $x^*$, **Slope $y^*$**, and **Slope $y$**.
The equality above is printed below the drawing.
:::
:::

::: {.source-item #src-mit-l02-p009-i001 data-source-page="9" data-source-order="1"}
- Under favorable conditions (convexity):

  - The optimal primal and dual values are equal.
  - The optimal primal and dual solutions are related.
:::

*[Source page 9.]{.source-locator}
:::

::: {.source-page #src-mit-l02-p010 data-source-page="10" data-source-order="5"}
## A More Abstract View of Duality

::: {.source-item #src-mit-l02-p010-i001 data-source-page="10" data-source-order="1"}
- Despite its elegance, the Fenchel framework is somewhat indirect.
:::

::: {.source-item #src-mit-l02-p010-i002 data-source-page="10" data-source-order="2"}
- From duality of set descriptions, to

  - duality of functional descriptions, to
  - duality of problem descriptions.
:::

::: {.source-item #src-mit-l02-p010-i003 data-source-page="10" data-source-order="3"}
- A more direct approach:

  - Start with a set, then
  - Define two simple prototype problems dual to each other.
:::

::: {.source-item #src-mit-l02-p010-i004 data-source-page="10" data-source-order="4"}
- Avoid functional descriptions (a simpler, less constrained framework).
:::

*[Source page 10.]{.source-locator}
:::

::: {.source-page #src-mit-l02-p011 data-source-page="11" data-source-order="6"}
## Min Common/Max Crossing Duality

::: {.source-figure #src-mit-l02-p011-f001 data-source-page="11" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 11, panels (a)-(c)).** Each panel is
drawn in $(u,w)$ coordinates and marks a set $M$, sometimes together with its
closure $\overline{M}$. A supporting line identifies a **Min Common Point
$w^*$** and a second supporting construction identifies a **Max Crossing Point
$q^*$**. Panels (a) and (b) show the regular geometric configurations; panel
(c) shows the exceptional/pathological configuration in which the two points
need not behave regularly. The labels $M$, $\overline M$, $u$, $w$, $0$,
$w^*$, and $q^*$ are retained in this semantic description.
:::

::: {.source-item #src-mit-l02-p011-i001 data-source-page="11" data-source-order="1"}
- All of duality theory and all of (convex/concave) minimax theory can be
  developed/explained in terms of this one figure.
:::

::: {.source-item #src-mit-l02-p011-i002 data-source-page="11" data-source-order="2"}
- The machinery of convex analysis is needed to flesh out this figure, and to
  rule out the exceptional/pathological behavior shown in (c).
:::

*[Source page 11.]{.source-locator}
:::

::: {.source-page #src-mit-l02-p012 data-source-page="12" data-source-order="7"}
## Abstract/General Duality Analysis

::: {.source-figure #src-mit-l02-p012-f001 data-source-page="12" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 12, analysis flow).** The flow starts
with **Abstract Geometric Framework (Set $M$)** and points to **Min-Common/Max-
Crossing Theorems**. Special choices of $M$ branch to **Minimax Duality
($\operatorname{MinMax}=\operatorname{MaxMin}$)**, **Constrained Optimization
Duality**, and **Theorems of the Alternative etc**. The label **Special choices
of $M$** sits at the branching point. This page contains no additional prose
item beyond the flowchart.
:::

*[Source page 12.]{.source-locator}
:::

::: {.source-page #src-mit-l02-p013 data-source-page="13" data-source-order="8"}
## Exceptional Behavior

::: {.source-item #src-mit-l02-p013-i001 data-source-page="13" data-source-order="1"}
- If convex structure is so favorable, what is the source of
  exceptional/pathological behavior?
:::

::: {.source-item #src-mit-l02-p013-i002 data-source-page="13" data-source-order="2"}
- **Answer:** Some common operations on convex sets do not preserve some basic
  properties.
:::

::: {.source-item #src-mit-l02-p013-i003 data-source-page="13" data-source-order="3"}
- **Example:** A linearly transformed closed convex set need not be closed
  (contrary to compact and polyhedral sets).

  - Also the vector sum of two closed convex sets need not be closed.

::: {.source-figure #src-mit-l02-p013-f001 data-source-page="13" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 13, $C_1$ and $C_2$).** In the
$(x_1,x_2)$ plane, $C_1$ is the region in the positive quadrant on or above
the curve $x_1x_2=1$, while $C_2$ is the vertical line $x_1=0$. The source
labels the horizontal axis $x_1$, the vertical axis $x_2$, and the two sets by
the exact definitions

$$
C_1=\{(x_1,x_2)\mid x_1>0,\ x_2>0,\ x_1x_2\ge 1\},
$$

$$
C_2=\{(x_1,x_2)\mid x_1=0\}.
$$
:::
:::

::: {.source-item #src-mit-l02-p013-i004 data-source-page="13" data-source-order="4"}
- This is a major reason for the analytical difficulties in convex analysis and
  pathological behavior in convex optimization (and the favorable character of
  polyhedral sets).
:::

*[Source page 13.]{.source-locator}
:::

::: {.edition-backmatter #src-mit-l02-backmatter}
## Source identity and boundary notes

- Source: Dimitri P. Bertsekas, *Lecture Slides on Convex Analysis and
  Optimization*, based on MIT 6.253, Spring 2012.
- Exact boundary: complete-notes PDF pages 6-13; page 14 begins the separate
  topic **Modern View of Convex Optimization** and is excluded.
- Figures: seven permission-only source graphics are omitted. Their page
  locators, labels, formulas, and semantic descriptions above are retained;
  no Athena Scientific byte, crop, or layout is copied.
- Rights: this derivative component remains CC BY-NC-SA 4.0, with attribution,
  change identification, noncommercial use, ShareAlike, and non-endorsement
  obligations preserved.
- This block contains no learner exercises, hints, solutions, or interactive
  computational surfaces. It is not a complete MIT lecture or complete course.
:::

Source: Dimitri P. Bertsekas, *Lecture Slides on Convex Analysis and
Optimization*, MIT OpenCourseWare 6.253, Spring 2012, complete-notes PDF pages
6-13. This semantic witness is distributed with the derivative under
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
