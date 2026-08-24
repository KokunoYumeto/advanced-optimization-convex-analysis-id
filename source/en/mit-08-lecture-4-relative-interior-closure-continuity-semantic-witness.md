---
title: "MIT 6.253 Lecture 4 semantic transcription witness"
subtitle: "Complete-notes PDF pages 39-49"
author: "Dimitri P. Bertsekas (source author)"
lang: en
date: "2026-08-24"
rights: "CC BY-NC-SA 4.0"
---

This is a project-made semantic transcription witness for the MIT
OpenCourseWare 6.253 complete-notes PDF, *Convex Analysis and Optimization*,
Spring 2012. It is bound to complete-notes PDF pages 39-49, the complete
**LECTURE 4** sequence. Page 50 begins **LECTURE 5** and is excluded. This
witness is not official editable MIT source. New lineation, stable identifiers,
and explanatory figure descriptions are project additions; the wording,
mathematics, order, proof dependencies, and diagram relationships transcribe
the source.

The five source figure blocks are intentionally not copied. The frozen course
archive identifies the lecture-note graphics as permission-restricted Athena
Scientific material. Each figure is represented by an exact page locator,
independently worded semantic description, and retained mathematical labels,
without source image bytes, crops, or layout. The frozen PDF has tagged,
selectable text; pages 39-49 contain no annotations, widgets, form fields,
JavaScript, exercises, hints, answers, solutions, code cells, or interactive
controls. Production and QA assistance: **OpenAI Codex gpt-5.6-sol, Ultra**,
at the repository user's direction. No human review is claimed. No endorsement
by MIT, Athena Scientific, or the source author is implied.

::: {.source-defect-notice #d90-mit-l08-notice-mapsto}
**Printed-notation notice.** The source uses the mapsto symbol in function
declarations on pages 42, 48, and 49. This witness preserves the printed
$\mapsto$ rather than silently normalizing it to $\to$.
:::

::: {.source-page #d90-mit-l08-p039 data-source-page="39" data-source-order="1"}
## LECTURE 4 - LECTURE OUTLINE

::: {.source-item #d90-mit-l08-p039-i001 data-source-page="39" data-source-order="1"}
- Relative interior and closure
:::

::: {.source-item #d90-mit-l08-p039-i002 data-source-page="39" data-source-order="2"}
- Algebra of relative interiors and closures
:::

::: {.source-item #d90-mit-l08-p039-i003 data-source-page="39" data-source-order="3"}
- Continuity of convex functions
:::

::: {.source-item #d90-mit-l08-p039-i004 data-source-page="39" data-source-order="4"}
- Closures of functions
:::

**Reading:** Section 1.3.

*[Source page 39.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p040 data-source-page="40" data-source-order="2"}
## RELATIVE INTERIOR

::: {.source-item #d90-mit-l08-p040-i001 data-source-page="40" data-source-order="1"}
- $x$ is a *relative interior point* of $C$, if $x$ is an interior point of
  $C$ relative to $\operatorname{aff}(C)$.
:::

::: {.source-item #d90-mit-l08-p040-i002 data-source-page="40" data-source-order="2"}
- $\operatorname{ri}(C)$ denotes the *relative interior of $C$*, i.e., the set
  of all relative interior points of $C$.
:::

::: {.source-item #d90-mit-l08-p040-i003 data-source-page="40" data-source-order="3"}
- **Line Segment Principle:** If $C$ is a convex set,
  $x\in\operatorname{ri}(C)$ and $\bar{x}\in\operatorname{cl}(C)$, then all
  points on the line segment connecting $x$ and $\bar{x}$, except possibly
  $\bar{x}$, belong to $\operatorname{ri}(C)$.
:::

::: {.source-figure #d90-mit-l08-p040-f001 data-source-page="40" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 40, Line Segment Principle).** A
shaded convex set $C$ contains a point $x$ and a circular neighborhood $S$ of
radius $\epsilon$ around it. A boundary point $\bar{x}$ is joined to $x$ by a
line segment. An intermediate point on that segment is labeled
$x_\alpha=\alpha x+(1-\alpha)\bar{x}$ and has a smaller circular neighborhood
$S_\alpha$ of radius $\alpha\epsilon$. Two rays from $\bar{x}$ are tangent to
the two circles, showing the homothetic containment relationship. Retained
labels are $C$, $x$, $\bar{x}$, $x_\alpha$, $S$, $S_\alpha$, $\epsilon$, and
$\alpha\epsilon$.
:::

::: {.source-item #d90-mit-l08-p040-i004 data-source-page="40" data-source-order="4"}
- Proof of case where $\bar{x}\in C$: See the figure.
:::

::: {.source-item #d90-mit-l08-p040-i005 data-source-page="40" data-source-order="5"}
- Proof of case where $\bar{x}\notin C$: Take sequence $\{x_k\}\subset C$ with
  $x_k\to\bar{x}$. Argue as in the figure.
:::

*[Source page 40.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p041 data-source-page="41" data-source-order="3"}
## ADDITIONAL MAJOR RESULTS

::: {.source-item #d90-mit-l08-p041-i001 data-source-page="41" data-source-order="1"}
- Let $C$ be a nonempty convex set.

  (a) $\operatorname{ri}(C)$ is a nonempty convex set, and has the same affine
      hull as $C$.

  (b) **Prolongation Lemma:** $x\in\operatorname{ri}(C)$ if and only if every
      line segment in $C$ having $x$ as one endpoint can be prolonged beyond
      $x$ without leaving $C$.
:::

::: {.source-figure #d90-mit-l08-p041-f001 data-source-page="41" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 41, construction inside $C$).** A
shaded convex set $C$ has the origin $0$ on its curved right boundary. Vectors
$z_1$ and $z_2$ point from $0$ to two boundary points and delimit a triangular
region labeled $X$ inside $C$. A callout states that $z_1$ and $z_2$ are
linearly independent, belong to $C$, and span $\operatorname{aff}(C)$.
:::

**Proof:** (a) Assume that $0\in C$. We choose $m$ linearly independent
vectors $z_1,\ldots,z_m\in C$, where $m$ is the dimension of
$\operatorname{aff}(C)$, and we let

::: {.source-display #d90-mit-l08-p041-d001 data-source-page="41" data-display-order="1"}
$$
X=\left\{
\sum_{i=1}^m\alpha_i z_i
\mathrel{\Bigg|}
\sum_{i=1}^m\alpha_i<1,
\ \alpha_i>0,
\ i=1,\ldots,m
\right\}.
$$
:::

(b) => is clear by the def. of rel. interior. Reverse: take any
$\bar{x}\in\operatorname{ri}(C)$; use Line Segment Principle.

::: {.source-defect-notice #d90-mit-l08-p041-n001 data-source-page="41"}
**Possible omitted connective step (preserved).** The result is stated for an
arbitrary nonempty convex set, while the proof begins "Assume that $0\in C$"
without explicitly invoking translation. A derivative may state the
translation reduction, but this witness does not insert it into the source
proof.
:::

*[Source page 41.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p042 data-source-page="42" data-source-order="4"}
## OPTIMIZATION APPLICATION

::: {.source-item #d90-mit-l08-p042-i001 data-source-page="42" data-source-order="1"}
- A concave function $f:\mathbb{R}^n\mapsto\mathbb{R}$ that attains its minimum
  over a convex set $X$ at an $x^*\in\operatorname{ri}(X)$ must be constant
  over $X$.
:::

::: {.source-figure #d90-mit-l08-p042-f001 data-source-page="42" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 42, prolongation in an affine hull).**
A rectangular region labeled $\operatorname{aff}(X)$ contains an oval convex
set $X$. Three collinear points lie in $X$: $x$, then $x^*$, then $\bar{x}$.
The segment from $x$ through $x^*$ is prolonged to $\bar{x}$, with $x^*$
strictly between the other two points.
:::

**Proof:** (By contradiction) Let $x\in X$ be such that $f(x)>f(x^*)$.
Prolong beyond $x^*$ the line segment $x$-to-$x^*$ to a point $\bar{x}\in X$.
By concavity of $f$, we have for some $\alpha\in(0,1)$

::: {.source-display #d90-mit-l08-p042-d001 data-source-page="42" data-display-order="1"}
$$
f(x^*)\geq\alpha f(x)+(1-\alpha)f(\bar{x}),
$$
:::

and since $f(x)>f(x^*)$, we must have $f(x^*)>f(\bar{x})$ - a contradiction.
**Q.E.D.**

::: {.source-item #d90-mit-l08-p042-i002 data-source-page="42" data-source-order="2"}
- **Corollary:** A nonconstant linear function cannot attain a minimum at an
  interior point of a convex set.
:::

*[Source page 42.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p043 data-source-page="43" data-source-order="5"}
## CALCULUS OF REL. INTERIORS: SUMMARY

::: {.source-item #d90-mit-l08-p043-i001 data-source-page="43" data-source-order="1"}
- The $\operatorname{ri}(C)$ and $\operatorname{cl}(C)$ of a convex set $C$
  "differ very little."

  - Any set "between" $\operatorname{ri}(C)$ and $\operatorname{cl}(C)$ has
    the same relative interior and closure.
  - The relative interior of a convex set is equal to the relative interior of
    its closure.
  - The closure of the relative interior of a convex set is equal to its
    closure.
:::

::: {.source-item #d90-mit-l08-p043-i002 data-source-page="43" data-source-order="2"}
- Relative interior and closure commute with Cartesian product and inverse
  image under a linear transformation.
:::

::: {.source-item #d90-mit-l08-p043-i003 data-source-page="43" data-source-order="3"}
- Relative interior commutes with image under a linear transformation and
  vector sum, but closure does not.
:::

::: {.source-item #d90-mit-l08-p043-i004 data-source-page="43" data-source-order="4"}
- Neither relative interior nor closure commute with set intersection.
:::

::: {.source-defect-notice #d90-mit-l08-p043-n001 data-source-page="43"}
**Possible missing qualification (preserved).** The source's inverse-image
summary is printed without the standard condition that the range of the linear
map meet $\operatorname{ri}(C)$, equivalently that the inverse image of
$\operatorname{ri}(C)$ be nonempty. Without such a qualification, the stated
inverse-image commutation can fail. The source item above remains unchanged.
:::

*[Source page 43.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p044 data-source-page="44" data-source-order="6"}
## CLOSURE VS RELATIVE INTERIOR

::: {.source-item #d90-mit-l08-p044-i001 data-source-page="44" data-source-order="1"}
- *Proposition:*

  (a) We have
      $\operatorname{cl}(C)=\operatorname{cl}(\operatorname{ri}(C))$ and
      $\operatorname{ri}(C)=\operatorname{ri}(\operatorname{cl}(C))$.

  (b) Let $\overline{C}$ be another nonempty convex set. Then the following
      three conditions are equivalent:

      (i) $C$ and $\overline{C}$ have the same rel. interior.

      (ii) $C$ and $\overline{C}$ have the same closure.

      (iii) $\operatorname{ri}(C)\subset\overline{C}\subset
      \operatorname{cl}(C)$.
:::

**Proof:** (a) Since $\operatorname{ri}(C)\subset C$, we have
$\operatorname{cl}(\operatorname{ri}(C))\subset\operatorname{cl}(C)$.
Conversely, let $\bar{x}\in\operatorname{cl}(C)$. Let
$x\in\operatorname{ri}(C)$. By the Line Segment Principle, we have

::: {.source-display #d90-mit-l08-p044-d001 data-source-page="44" data-display-order="1"}
$$
\alpha x+(1-\alpha)\bar{x}\in\operatorname{ri}(C),
\qquad \forall\alpha\in(0,1].
$$
:::

Thus, $\bar{x}$ is the limit of a sequence that lies in
$\operatorname{ri}(C)$, so
$\bar{x}\in\operatorname{cl}(\operatorname{ri}(C))$.

::: {.source-figure #d90-mit-l08-p044-f001 data-source-page="44" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 44, approach from relative
interior).** An oval set labeled $C$ contains a point $x$. A second point
$\bar{x}$ lies on the left boundary. A straight segment joins $\bar{x}$ to
$x$, depicting the sequence of convex combinations that approaches
$\bar{x}$ from inside $C$.
:::

The proof of
$\operatorname{ri}(C)=\operatorname{ri}(\operatorname{cl}(C))$ is similar.

*[Source page 44.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p045 data-source-page="45" data-source-order="7"}
## LINEAR TRANSFORMATIONS

::: {.source-item #d90-mit-l08-p045-i001 data-source-page="45" data-source-order="1"}
- Let $C$ be a nonempty convex subset of $\mathbb{R}^n$ and let $A$ be an
  $m\times n$ matrix.

  (a) We have
      $A\cdot\operatorname{ri}(C)=\operatorname{ri}(A\cdot C)$.

  (b) We have
      $A\cdot\operatorname{cl}(C)\subset\operatorname{cl}(A\cdot C)$.
      Furthermore, if $C$ is bounded, then
      $A\cdot\operatorname{cl}(C)=\operatorname{cl}(A\cdot C)$.
:::

**Proof:** (a) Intuition: Spheres within $C$ are mapped onto spheres within
$A\cdot C$ (relative to the affine hull).

(b) We have
$A\cdot\operatorname{cl}(C)\subset\operatorname{cl}(A\cdot C)$, since if a
sequence $\{x_k\}\subset C$ converges to some $x\in\operatorname{cl}(C)$ then
the sequence $\{Ax_k\}$, which belongs to $A\cdot C$, converges to $Ax$,
implying that $Ax\in\operatorname{cl}(A\cdot C)$.

To show the converse, assuming that $C$ is bounded, choose any
$z\in\operatorname{cl}(A\cdot C)$. Then, there exists $\{x_k\}\subset C$ such
that $Ax_k\to z$. Since $C$ is bounded, $\{x_k\}$ has a subsequence that
converges to some $x\in\operatorname{cl}(C)$, and we must have $Ax=z$. It
follows that $z\in A\cdot\operatorname{cl}(C)$. **Q.E.D.**

Note that in general, we may have

::: {.source-display #d90-mit-l08-p045-d001 data-source-page="45" data-display-order="1"}
$$
A\cdot\operatorname{int}(C)\neq\operatorname{int}(A\cdot C),
\qquad
A\cdot\operatorname{cl}(C)\neq\operatorname{cl}(A\cdot C).
$$
:::

::: {.source-defect-notice #d90-mit-l08-p045-n001 data-source-page="45"}
**Possible source issue (preserved).** The intuition sentence says that a
linear transformation maps spheres onto spheres. For a general linear map,
the image of a sphere need not itself be a sphere. The source wording is
retained here without silent repair.
:::

*[Source page 45.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p046 data-source-page="46" data-source-order="8"}
## INTERSECTIONS AND VECTOR SUMS

::: {.source-item #d90-mit-l08-p046-i001 data-source-page="46" data-source-order="1"}
- Let $C_1$ and $C_2$ be nonempty convex sets.

  (a) We have

      ::: {.source-display #d90-mit-l08-p046-d001 data-source-page="46" data-display-order="1"}
      $$
      \operatorname{ri}(C_1+C_2)
      =\operatorname{ri}(C_1)+\operatorname{ri}(C_2),
      $$
      :::

      ::: {.source-display #d90-mit-l08-p046-d002 data-source-page="46" data-display-order="2"}
      $$
      \operatorname{cl}(C_1)+\operatorname{cl}(C_2)
      \subset\operatorname{cl}(C_1+C_2).
      $$
      :::

      If one of $C_1$ and $C_2$ is bounded, then

      ::: {.source-display #d90-mit-l08-p046-d003 data-source-page="46" data-display-order="3"}
      $$
      \operatorname{cl}(C_1)+\operatorname{cl}(C_2)
      =\operatorname{cl}(C_1+C_2).
      $$
      :::

  (b) We have

      ::: {.source-display #d90-mit-l08-p046-d004 data-source-page="46" data-display-order="4"}
      $$
      \operatorname{ri}(C_1)\cap\operatorname{ri}(C_2)
      \subset\operatorname{ri}(C_1\cap C_2),
      \qquad
      \operatorname{cl}(C_1\cap C_2)
      \subset\operatorname{cl}(C_1)\cap\operatorname{cl}(C_2).
      $$
      :::

      If
      $\operatorname{ri}(C_1)\cap\operatorname{ri}(C_2)\neq\varnothing$, then

      ::: {.source-display #d90-mit-l08-p046-d005 data-source-page="46" data-display-order="5"}
      $$
      \operatorname{ri}(C_1\cap C_2)
      =\operatorname{ri}(C_1)\cap\operatorname{ri}(C_2),
      \qquad
      \operatorname{cl}(C_1\cap C_2)
      =\operatorname{cl}(C_1)\cap\operatorname{cl}(C_2).
      $$
      :::
:::

**Proof of (a):** $C_1+C_2$ is the result of the linear transformation
$(x_1,x_2)\mapsto x_1+x_2$.

::: {.source-item #d90-mit-l08-p046-i002 data-source-page="46" data-source-order="2"}
- Counterexample for (b):

  ::: {.source-display #d90-mit-l08-p046-d006 data-source-page="46" data-display-order="6"}
  $$
  C_1=\{x\mid x\leq0\},
  \qquad
  C_2=\{x\mid x\geq0\}.
  $$
  :::

  ::: {.source-display #d90-mit-l08-p046-d007 data-source-page="46" data-display-order="7"}
  $$
  C_1=\{x\mid x<0\},
  \qquad
  C_2=\{x\mid x>0\}.
  $$
  :::
:::

*[Source page 46.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p047 data-source-page="47" data-source-order="9"}
## CARTESIAN PRODUCT - GENERALIZATION

::: {.source-item #d90-mit-l08-p047-i001 data-source-page="47" data-source-order="1"}
- Let $C$ be convex set in $\mathbb{R}^{n+m}$. For $x\in\mathbb{R}^n$, let

  ::: {.source-display #d90-mit-l08-p047-d001 data-source-page="47" data-display-order="1"}
  $$
  C_x=\{y\mid(x,y)\in C\},
  $$
  :::

  and let

  ::: {.source-display #d90-mit-l08-p047-d002 data-source-page="47" data-display-order="2"}
  $$
  D=\{x\mid C_x\neq\varnothing\}.
  $$
  :::

  Then

  ::: {.source-display #d90-mit-l08-p047-d003 data-source-page="47" data-display-order="3"}
  $$
  \operatorname{ri}(C)
  =\{(x,y)\mid x\in\operatorname{ri}(D),\ y\in\operatorname{ri}(C_x)\}.
  $$
  :::
:::

**Proof:** Since $D$ is projection of $C$ on $x$-axis,

::: {.source-display #d90-mit-l08-p047-d004 data-source-page="47" data-display-order="4"}
$$
\operatorname{ri}(D)
=\{x\mid\text{there exists }y\in\mathbb{R}^m
\text{ with }(x,y)\in\operatorname{ri}(C)\},
$$
:::

so that

::: {.source-display #d90-mit-l08-p047-d005 data-source-page="47" data-display-order="5"}
$$
\operatorname{ri}(C)
=\bigcup_{x\in\operatorname{ri}(D)}
\bigl(M_x\cap\operatorname{ri}(C)\bigr),
$$
:::

where $M_x=\{(x,y)\mid y\in\mathbb{R}^m\}$. For every
$x\in\operatorname{ri}(D)$, we have

::: {.source-display #d90-mit-l08-p047-d006 data-source-page="47" data-display-order="6"}
$$
M_x\cap\operatorname{ri}(C)
=\operatorname{ri}(M_x\cap C)
=\{(x,y)\mid y\in\operatorname{ri}(C_x)\}.
$$
:::

Combine the preceding two equations. **Q.E.D.**

*[Source page 47.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p048 data-source-page="48" data-source-order="10"}
## CONTINUITY OF CONVEX FUNCTIONS

::: {.source-item #d90-mit-l08-p048-i001 data-source-page="48" data-source-order="1"}
- If $f:\mathbb{R}^n\mapsto\mathbb{R}$ is convex, then it is continuous.
:::

::: {.source-figure #d90-mit-l08-p048-f001 data-source-page="48" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 48, unit-square continuity
construction).** A square has corners
$e_1=(1,1)$, $e_2=(1,-1)$, $e_3=(-1,-1)$, and $e_4=(-1,1)$. A diagonal joins
the top-left point $y_k$ to the bottom-right point $z_k$ and passes through the
origin $0$. The point $x_k$ lies on this diagonal between $y_k$ and $0$.
$x_{k+1}$ and two additional sequence points are shown approaching $0$ from
nearby directions.
:::

**Proof:** We will show that $f$ is continuous at $0$. By convexity, $f$ is
bounded within the unit cube by the max value of $f$ over the corners of the
cube.

Consider sequence $x_k\to0$ and the sequences

::: {.source-display #d90-mit-l08-p048-d001 data-source-page="48" data-display-order="1"}
$$
y_k=\frac{x_k}{\lVert x_k\rVert_\infty},
\qquad
z_k=-\frac{x_k}{\lVert x_k\rVert_\infty}.
$$
:::

Then

::: {.source-display #d90-mit-l08-p048-d002 data-source-page="48" data-display-order="2"}
$$
f(x_k)\leq
\bigl(1-\lVert x_k\rVert_\infty\bigr)f(0)
+\lVert x_k\rVert_\infty f(y_k),
$$
:::

::: {.source-display #d90-mit-l08-p048-d003 data-source-page="48" data-display-order="3"}
$$
f(0)\leq
\frac{\lVert x_k\rVert_\infty}{\lVert x_k\rVert_\infty+1}f(z_k)
+\frac{1}{\lVert x_k\rVert_\infty+1}f(x_k).
$$
:::

Take limit as $k\to\infty$. Since $\lVert x_k\rVert_\infty\to0$, we have

::: {.source-display #d90-mit-l08-p048-d004 data-source-page="48" data-display-order="4"}
$$
\limsup_{k\to\infty}\lVert x_k\rVert_\infty f(y_k)\leq0,
\qquad
\limsup_{k\to\infty}
\frac{\lVert x_k\rVert_\infty}{\lVert x_k\rVert_\infty+1}f(z_k)\leq0,
$$
:::

so $f(x_k)\to f(0)$. **Q.E.D.**

::: {.source-defect-notice #d90-mit-l08-p048-n001 data-source-page="48"}
**Possible omitted edge case (preserved).** The proof defines $y_k$ and $z_k$
by dividing by $\lVert x_k\rVert_\infty$ without separately treating indices
for which $x_k=0$. Those indices already satisfy the desired conclusion; a
derivative may split them off, but this witness does not silently alter the
printed proof.
:::

::: {.source-item #d90-mit-l08-p048-i002 data-source-page="48" data-source-order="2"}
- Extension to continuity over $\operatorname{ri}(\operatorname{dom}(f))$.
:::

*[Source page 48.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p049 data-source-page="49" data-source-order="11"}
## CLOSURES OF FUNCTIONS

::: {.source-item #d90-mit-l08-p049-i001 data-source-page="49" data-source-order="1"}
- The *closure* of a function $f:X\mapsto[-\infty,\infty]$ is the function
  $\operatorname{cl}f:\mathbb{R}^n\mapsto[-\infty,\infty]$ with

  ::: {.source-display #d90-mit-l08-p049-d001 data-source-page="49" data-display-order="1"}
  $$
  \operatorname{epi}(\operatorname{cl}f)
  =\operatorname{cl}(\operatorname{epi}(f)).
  $$
  :::
:::

::: {.source-item #d90-mit-l08-p049-i002 data-source-page="49" data-source-order="2"}
- The *convex closure of $f$* is the function
  $\check{\operatorname{cl}}f$ with

  ::: {.source-display #d90-mit-l08-p049-d002 data-source-page="49" data-display-order="2"}
  $$
  \operatorname{epi}(\check{\operatorname{cl}}f)
  =\operatorname{cl}(\operatorname{conv}(\operatorname{epi}(f))).
  $$
  :::
:::

::: {.source-item #d90-mit-l08-p049-i003 data-source-page="49" data-source-order="3"}
- *Proposition:* For any $f:X\mapsto[-\infty,\infty]$

  ::: {.source-display #d90-mit-l08-p049-d003 data-source-page="49" data-display-order="3"}
  $$
  \inf_{x\in X}f(x)
  =\inf_{x\in\mathbb{R}^n}(\operatorname{cl}f)(x)
  =\inf_{x\in\mathbb{R}^n}(\check{\operatorname{cl}}f)(x).
  $$
  :::

  Also, any vector that attains the infimum of $f$ over $X$ also attains the
  infimum of $\operatorname{cl}f$ and $\check{\operatorname{cl}}f$.
:::

::: {.source-item #d90-mit-l08-p049-i004 data-source-page="49" data-source-order="4"}
- *Proposition:* For any $f:X\mapsto[-\infty,\infty]$:

  (a) $\operatorname{cl}f$ (or $\check{\operatorname{cl}}f$) is the greatest
      closed (or closed convex, resp.) function majorized by $f$.

  (b) If $f$ is convex, then $\operatorname{cl}f$ is convex, and it is proper
      if and only if $f$ is proper. Also,

      ::: {.source-display #d90-mit-l08-p049-d004 data-source-page="49" data-display-order="4"}
      $$
      (\operatorname{cl}f)(x)=f(x),
      \qquad
      \forall x\in\operatorname{ri}(\operatorname{dom}(f)),
      $$
      :::

      and if $x\in\operatorname{ri}(\operatorname{dom}(f))$ and
      $y\in\operatorname{dom}(\operatorname{cl}f)$,

      ::: {.source-display #d90-mit-l08-p049-d005 data-source-page="49" data-display-order="5"}
      $$
      (\operatorname{cl}f)(y)
      =\lim_{\alpha\downarrow0}f\bigl(y+\alpha(x-y)\bigr).
      $$
      :::
:::

*[Source page 49.]{.source-locator}*
:::
