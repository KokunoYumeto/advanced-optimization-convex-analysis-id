---
title: "MIT 6.253 Lecture 3 semantic transcription witness"
subtitle: "Complete-notes PDF pages 29-38"
author: "Dimitri P. Bertsekas (source author)"
lang: en
date: "2026-08-23"
rights: "CC BY-NC-SA 4.0"
---

This is a project-made semantic transcription witness for the MIT OpenCourseWare
6.253 complete-notes PDF, *Convex Analysis and Optimization*, Spring 2012. It is
bound to complete-notes PDF pages 29-38, the complete **LECTURE 3** sequence.
Page 39 begins **LECTURE 4** and is excluded. This witness is not official
editable MIT source. New lineation, identifiers, and explanatory figure
descriptions are project additions; the wording, mathematics, order, and
diagram relationships transcribe the source.

The four source figure blocks are intentionally not copied. The frozen course
archive identifies the lecture-note graphics as permission-restricted Athena
Scientific material. Each figure is represented by an exact page locator,
semantic description, and retained mathematical labels, without source image
bytes, crops, or layout. Production and QA assistance: **OpenAI Codex
gpt-5.6-sol, Ultra**, at the repository user's direction. No endorsement by MIT,
Athena Scientific, or the source author is implied.

::: {.source-page #src-mit-l07-p029 data-source-page="29" data-source-order="1"}
## LECTURE 3 - LECTURE OUTLINE

::: {.source-item #src-mit-l07-p029-i001 data-source-page="29" data-source-order="1"}
- Differentiable Convex Functions
:::

::: {.source-item #src-mit-l07-p029-i002 data-source-page="29" data-source-order="2"}
- Convex and Affine Hulls
:::

::: {.source-item #src-mit-l07-p029-i003 data-source-page="29" data-source-order="3"}
- Caratheodory's Theorem
:::

**Reading:** Sections 1.1, 1.2.

*[Source page 29.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p030 data-source-page="30" data-source-order="2"}
## DIFFERENTIABLE CONVEX FUNCTIONS

::: {.source-figure #src-mit-l07-p030-f001 data-source-page="30" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 30, first-order support line).** A
thick convex curve is labeled $f(z)$ above a horizontal axis whose running
variable is $z$. A dashed vertical line marks $x$. The tangent line through the
curve at $x$ lies below the curve and is labeled
$f(x)+\nabla f(x)'(z-x)$.
:::

::: {.source-item #src-mit-l07-p030-i001 data-source-page="30" data-source-order="1"}
- Let $C\subset\mathbb{R}^n$ be a convex set and let
  $f:\mathbb{R}^n\mapsto\mathbb{R}$ be differentiable over
  $\mathbb{R}^n$.

  (a) The function $f$ is convex over $C$ if and only if

      ::: {.source-display #src-mit-l07-p030-d001 data-source-page="30" data-display-order="1"}
      $$
      f(z)\geq f(x)+(z-x)'\nabla f(x),
      \qquad \forall x,z\in C.
      $$
      :::

  (b) If the inequality is strict whenever $x\neq z$, then $f$ is strictly
  convex over $C$.
:::

*[Source page 30.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p031 data-source-page="31" data-source-order="3"}
## PROOF IDEAS

::: {.source-figure #src-mit-l07-p031-f001 data-source-page="31" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 31, two proof-idea panels).** Panel
(a) marks $x$, $z=\alpha x+(1-\alpha)y$, and $y$ under a convex curve. A chord
from $(x,f(x))$ to $(y,f(y))$ has height
$\alpha f(x)+(1-\alpha)f(y)$ at $z$. The tangent at $z$ is labeled at the two
endpoints by $f(z)+(x-z)'\nabla f(z)$ and
$f(z)+(y-z)'\nabla f(z)$. Panel (b) marks $x$,
$x+\alpha(z-x)$, and $z$ under a convex curve. At $z$, the secant construction
is labeled
$f(x)+\bigl(f(x+\alpha(z-x))-f(x)\bigr)/\alpha$, while the lower tangent
construction is labeled $f(x)+(z-x)'\nabla f(x)$.
:::

*[Source page 31.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p032 data-source-page="32" data-source-order="4"}
## OPTIMALITY CONDITION

::: {.source-item #src-mit-l07-p032-i001 data-source-page="32" data-source-order="1"}
- Let $C$ be a nonempty convex subset of $\mathbb{R}^n$ and let
  $f:\mathbb{R}^n\mapsto\mathbb{R}$ be convex and differentiable over an open
  set that contains $C$. Then a vector $x^*\in C$ minimizes $f$ over $C$ if
  and only if

  ::: {.source-display #src-mit-l07-p032-d001 data-source-page="32" data-display-order="1"}
  $$
  \nabla f(x^*)'(x-x^*)\geq 0,
  \qquad \forall x\in C.
  $$
  :::
:::

**Proof:** If the condition holds, then

::: {.source-display #src-mit-l07-p032-d002 data-source-page="32" data-display-order="2"}
$$
f(x)\geq f(x^*)+(x-x^*)'\nabla f(x^*)\geq f(x^*),
\qquad \forall x\in C,
$$
:::

so $x^*$ minimizes $f$ over $C$.

Conversely, assume the contrary, i.e., $x^*$ minimizes $f$ over $C$ and
$\nabla f(x^*)'(x-x^*)<0$ for some $x\in C$. By differentiation, we have

::: {.source-display #src-mit-l07-p032-d003 data-source-page="32" data-display-order="3"}
$$
\lim_{\alpha\downarrow 0}
\frac{f\bigl(x^*+\alpha(x-x^*)\bigr)-f(x^*)}{\alpha}
=\nabla f(x^*)'(x-x^*)<0,
$$
:::

so $f\bigl(x^*+\alpha(x-x^*)\bigr)$ decreases strictly for sufficiently small
$\alpha>0$, contradicting the optimality of $x^*$. **Q.E.D.**

*[Source page 32.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p033 data-source-page="33" data-source-order="5"}
## PROJECTION THEOREM

::: {.source-item #src-mit-l07-p033-i001 data-source-page="33" data-source-order="1"}
- Let $C$ be a nonempty closed convex set in $\mathbb{R}^n$.

  (a) For every $z\in\mathbb{R}^n$, there exists a unique minimum of

      ::: {.source-display #src-mit-l07-p033-d001 data-source-page="33" data-display-order="1"}
      $$
      f(x)=\lVert z-x\rVert^2
      $$
      :::

      over all $x\in C$ (called the *projection of $z$ on $C$*).

  (b) $x^*$ is the projection of $z$ if and only if

      ::: {.source-display #src-mit-l07-p033-d002 data-source-page="33" data-display-order="2"}
      $$
      (x-x^*)'(z-x^*)\leq 0,
      \qquad \forall x\in C.
      $$
      :::
:::

**Proof:** (a) $f$ is strictly convex and has compact level sets.

(b) This is just the necessary and sufficient optimality condition

::: {.source-display #src-mit-l07-p033-d003 data-source-page="33" data-display-order="3"}
$$
\nabla f(x^*)'(x-x^*)\geq 0,
\qquad \forall x\in C.
$$
:::

*[Source page 33.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p034 data-source-page="34" data-source-order="6"}
## TWICE DIFFERENTIABLE CONVEX FNS

::: {.source-item #src-mit-l07-p034-i001 data-source-page="34" data-source-order="1"}
- Let $C$ be a convex subset of $\mathbb{R}^n$ and let
  $f:\mathbb{R}^n\mapsto\mathbb{R}$ be twice continuously differentiable over
  $\mathbb{R}^n$.

  (a) If $\nabla^2f(x)$ is positive semidefinite for all $x\in C$, then $f$ is
  convex over $C$.

  (b) If $\nabla^2f(x)$ is positive definite for all $x\in C$, then $f$ is
  strictly convex over $C$.

  (c) If $C$ is open and $f$ is convex over $C$, then $\nabla^2f(x)$ is
  positive semidefinite for all $x\in C$.
:::

**Proof:** (a) By the mean value theorem, for $x,y\in C$,

::: {.source-display #src-mit-l07-p034-d001 data-source-page="34" data-display-order="1"}
$$
f(y)=f(x)+(y-x)'\nabla f(x)
+\frac{1}{2}(y-x)'\nabla^2f\bigl(x+\alpha(y-x)\bigr)(y-x)
$$
:::

for some $\alpha\in[0,1]$. Using the positive semidefiniteness of $\nabla^2f$,
we obtain

::: {.source-display #src-mit-l07-p034-d002 data-source-page="34" data-display-order="2"}
$$
f(y)\geq f(x)+(y-x)'\nabla f(x),
\qquad \forall x,y\in C.
$$
:::

From the preceding result, $f$ is convex.

(b) Similar to (a), we have
$f(y)>f(x)+(y-x)'\nabla f(x)$ for all $x,y\in C$ with $x\neq y$, and we use
the preceding result.

(c) By contradiction ... similar.

*[Source page 34.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p035 data-source-page="35" data-source-order="7"}
## CONVEX AND AFFINE HULLS

::: {.source-item #src-mit-l07-p035-i001 data-source-page="35" data-source-order="1"}
- Given a set $X\subseteq\mathbb{R}^n$:
:::

::: {.source-item #src-mit-l07-p035-i002 data-source-page="35" data-source-order="2"}
- A *convex combination* of elements of $X$ is a vector of the form
  $\sum_{i=1}^m\alpha_i x_i$, where $x_i\in X$, $\alpha_i\geq0$, and
  $\sum_{i=1}^m\alpha_i=1$.
:::

::: {.source-item #src-mit-l07-p035-i003 data-source-page="35" data-source-order="3"}
- The *convex hull* of $X$, denoted $\operatorname{conv}(X)$, is the
  intersection of all convex sets containing $X$. (Can be shown to be equal to
  the set of all convex combinations from $X$).
:::

::: {.source-item #src-mit-l07-p035-i004 data-source-page="35" data-source-order="4"}
- The *affine hull* of $X$, denoted $\operatorname{aff}(X)$, is the intersection
  of all affine sets containing $X$ (an affine set is a set of the form
  $\bar{x}+S$, where $S$ is a subspace).
:::

::: {.source-item #src-mit-l07-p035-i005 data-source-page="35" data-source-order="5"}
- A *nonnegative combination* of elements of $X$ is a vector of the form
  $\sum_{i=1}^m\alpha_i x_i$, where $x_i\in X$ and $\alpha_i\geq0$ for all $i$.
:::

::: {.source-item #src-mit-l07-p035-i006 data-source-page="35" data-source-order="6"}
- The *cone generated by $X$*, denoted $\operatorname{cone}(X)$, is the set of
  all nonnegative combinations from $X$:

  - It is a convex cone containing the origin.
  - It need not be closed!
  - If $X$ is a finite set, $\operatorname{cone}(X)$ is closed (nontrivial to
    show!)
:::

*[Source page 35.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p036 data-source-page="36" data-source-order="8"}
## CARATHEODORY'S THEOREM

::: {.source-figure #src-mit-l07-p036-f001 data-source-page="36" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 36, cone and convex-hull panels).**
Panel (a) places an irregular set $X$ between two rays from the origin $0$,
with points $x_1$ and $x_2$ on the rays and a nonzero vector $x$ in the region
labeled $\operatorname{cone}(X)$. Panel (b) draws a quadrilateral labeled
$\operatorname{conv}(X)$ with vertices $x_1,x_2,x_3,x_4$ and a point $x$ in
its interior.
:::

::: {.source-item #src-mit-l07-p036-i001 data-source-page="36" data-source-order="1"}
- Let $X$ be a nonempty subset of $\mathbb{R}^n$.

  (a) Every $x\neq0$ in $\operatorname{cone}(X)$ can be represented as a
  positive combination of vectors $x_1,\ldots,x_m$ from $X$ that are linearly
  independent (so $m\leq n$).

  (b) Every $x\notin X$ that belongs to $\operatorname{conv}(X)$ can be
  represented as a convex combination of vectors $x_1,\ldots,x_m$ from $X$
  with $m\leq n+1$.
:::

*[Source page 36.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p037 data-source-page="37" data-source-order="9"}
## PROOF OF CARATHEODORY'S THEOREM

(a) Let $x$ be a nonzero vector in $\operatorname{cone}(X)$, and let $m$ be the
smallest integer such that $x$ has the form
$\sum_{i=1}^m\alpha_i x_i$, where $\alpha_i>0$ and $x_i\in X$ for all
$i=1,\ldots,m$. If the vectors $x_i$ were linearly dependent, there would
exist $\lambda_1,\ldots,\lambda_m$, with

::: {.source-display #src-mit-l07-p037-d001 data-source-page="37" data-display-order="1"}
$$
\sum_{i=1}^m\lambda_i x_i=0
$$
:::

and at least one of the $\lambda_i$ is positive. Consider

::: {.source-display #src-mit-l07-p037-d002 data-source-page="37" data-display-order="2"}
$$
\sum_{i=1}^m(\alpha_i-\bar{\gamma}\lambda_i)x_i,
$$
:::

where $\bar{\gamma}$ is the largest $\gamma$ such that
$\alpha_i-\gamma\lambda_i\geq0$ for all $i$. This combination provides a
representation of $x$ as a positive combination of fewer than $m$ vectors of
$X$ - a contradiction. Therefore, $x_1,\ldots,x_m$ are linearly independent.

(b) Use “lifting” argument: apply part (a) to
$Y=\{(x,1)\mid x\in X\}$.

::: {.source-figure #src-mit-l07-p037-f001 data-source-page="37" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 37, lifting argument).** An origin
labeled $0$ lies in a lower copy of $\mathbb{R}^n$. A curved set $X$ and point
$x$ lie below a lifted curved set $Y$ and point $(x,1)$ in the level labeled
$1$. Rays from the origin form the lifting cone, and dashed guides connect
$x$ with $(x,1)$ and mark the unit level. Retained labels are
$0$, $1$, $\mathbb{R}^n$, $X$, $Y$, $x$, and $(x,1)$.
:::

*[Source page 37.]{.source-locator}*
:::

::: {.source-page #src-mit-l07-p038 data-source-page="38" data-source-order="10"}
## AN APPLICATION OF CARATHEODORY

::: {.source-item #src-mit-l07-p038-i001 data-source-page="38" data-source-order="1"}
- The convex hull of a compact set is compact.

  **Proof:** Let $X$ be compact. We take a sequence in
  $\operatorname{conv}(X)$ and show that it has a convergent subsequence whose
  limit is in $\operatorname{conv}(X)$.

  By Caratheodory, a sequence in $\operatorname{conv}(X)$ can be expressed as
  $\left\{\sum_{i=1}^{n+1}\alpha_i^k x_i^k\right\}$, where for all $k$ and $i$,
  $\alpha_i^k\geq0$, $x_i^k\in X$, and
  $\sum_{i=1}^{n+1}\alpha_i^k=1$. Since the sequence

  ::: {.source-display #src-mit-l07-p038-d001 data-source-page="38" data-display-order="1"}
  $$
  \left\{
  (\alpha_1^k,\ldots,\alpha_{n+1}^k,x_1^k,\ldots,x_{n+1}^k)
  \right\}
  $$
  :::

  is bounded, it has a limit point

  ::: {.source-display #src-mit-l07-p038-d002 data-source-page="38" data-display-order="2"}
  $$
  \left\{
  (\alpha_1,\ldots,\alpha_{n+1},x_1,\ldots,x_{n+1})
  \right\},
  $$
  :::

  which must satisfy $\sum_{i=1}^{n+1}\alpha_i=1$, $\alpha_i\geq0$, and
  $x_i\in X$ for all $i$. The vector
  $\sum_{i=1}^{n+1}\alpha_i x_i$ belongs to $\operatorname{conv}(X)$ and is a
  limit point of
  $\left\{\sum_{i=1}^{n+1}\alpha_i^k x_i^k\right\}$, showing that
  $\operatorname{conv}(X)$ is compact. **Q.E.D.**
:::

::: {.source-item #src-mit-l07-p038-i002 data-source-page="38" data-source-order="2"}
- Note that the convex hull of a closed set need not be closed!
:::

*[Source page 38.]{.source-locator}*
:::

