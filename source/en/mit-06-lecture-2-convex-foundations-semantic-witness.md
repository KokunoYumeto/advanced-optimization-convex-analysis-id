---
title: "MIT 6.253 Lecture 2 convex-foundations semantic transcription witness"
subtitle: "Complete-notes PDF pages 20-28"
author: "Dimitri P. Bertsekas (source author)"
lang: en
date: "2026-08-23"
rights: "CC BY-NC-SA 4.0"
---

This is a project-made semantic transcription witness for the MIT OpenCourseWare
6.253 complete-notes PDF, *Convex Analysis and Optimization*, Spring 2012. It is
bound to complete-notes PDF pages 20-28, the complete **LECTURE 2** sequence.
Page 29 begins **LECTURE 3** and is excluded. This witness is not official
editable MIT source. New lineation, identifiers, and explanatory figure
descriptions are project additions; the wording, mathematics, order, and
diagram relationships transcribe the source.

The five source figure blocks are intentionally not copied. The frozen course
archive identifies the lecture-note graphics as permission-restricted Athena
Scientific material. Each figure is represented by an exact page locator,
semantic description, and retained mathematical labels, without source image
bytes, crops, or layout. Production and QA assistance: **OpenAI Codex
gpt-5.6-sol, Ultra**, at the repository user's direction. No endorsement by MIT,
Athena Scientific, or the source author is implied.

::: {.source-page #src-mit-l06-p020 data-source-page="20" data-source-order="1"}
## LECTURE 2 - LECTURE OUTLINE

::: {.source-item #src-mit-l06-p020-i001 data-source-page="20" data-source-order="1"}
- Convex sets and functions
:::

::: {.source-item #src-mit-l06-p020-i002 data-source-page="20" data-source-order="2"}
- Epigraphs
:::

::: {.source-item #src-mit-l06-p020-i003 data-source-page="20" data-source-order="3"}
- Closed convex functions
:::

::: {.source-item #src-mit-l06-p020-i004 data-source-page="20" data-source-order="4"}
- Recognizing convex functions
:::

**Reading:** Section 1.1.

*[Source page 20.]{.source-locator}*
:::

::: {.source-page #src-mit-l06-p021 data-source-page="21" data-source-order="2"}
## SOME MATH CONVENTIONS

::: {.source-item #src-mit-l06-p021-i001 data-source-page="21" data-source-order="1"}
- All of our work is done in $\mathbb{R}^n$: the space of $n$-tuples.

  ::: {.source-display #src-mit-l06-p021-d001 data-source-page="21" data-display-order="1"}
  $$
  x=(x_1,\ldots,x_n).
  $$
  :::
:::

::: {.source-item #src-mit-l06-p021-i002 data-source-page="21" data-source-order="2"}
- All vectors are assumed column vectors.
:::

::: {.source-item #src-mit-l06-p021-i003 data-source-page="21" data-source-order="3"}
- “$'$” denotes transpose, so we use $x'$ to denote a row vector.
:::

::: {.source-item #src-mit-l06-p021-i004 data-source-page="21" data-source-order="4"}
- $x'y$ is the inner product $\sum_{i=1}^n x_i y_i$ of vectors $x$ and $y$.
:::

::: {.source-item #src-mit-l06-p021-i005 data-source-page="21" data-source-order="5"}
- $\lVert x\rVert=\sqrt{x'x}$ is the (Euclidean) norm of $x$. We use this
  norm almost exclusively.
:::

::: {.source-item #src-mit-l06-p021-i006 data-source-page="21" data-source-order="6"}
- See the textbook for an overview of the linear algebra and real analysis
  background that we will use. Particularly the following:

  - Definition of $\sup$ and $\inf$ of a set of real numbers
  - Convergence of sequences (definitions of $\liminf$, $\limsup$ of a
    sequence of real numbers, and definition of the limit of a sequence of
    vectors)
  - Open, closed, and compact sets and their properties
  - Definition and properties of differentiation
:::

*[Source page 21.]{.source-locator}*
:::

::: {.source-page #src-mit-l06-p022 data-source-page="22" data-source-order="3"}
## CONVEX SETS

::: {.source-figure #src-mit-l06-p022-f001 data-source-page="22" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 22, convex and nonconvex sets).** A
four-panel composite compares line segments between labeled points $x$ and
$y$. In the upper-left convex region, every point
$\alpha x+(1-\alpha)y$, $0\leq\alpha\leq1$, remains inside. The upper-right
indented region lets part of the segment leave the set. The lower-left convex
polygon contains the whole segment. The lower-right pair of disjoint ovals
places $x$ and $y$ in different components, so the connecting segment leaves
the set.
:::

::: {.source-item #src-mit-l06-p022-i001 data-source-page="22" data-source-order="1"}
- A subset $C$ of $\mathbb{R}^n$ is called convex if

  ::: {.source-display #src-mit-l06-p022-d001 data-source-page="22" data-display-order="1"}
  $$
  \alpha x+(1-\alpha)y\in C,
  \qquad
  \forall x,y\in C,\quad \forall\alpha\in[0,1].
  $$
  :::
:::

::: {.source-item #src-mit-l06-p022-i002 data-source-page="22" data-source-order="2"}
- Operations that preserve convexity

  - Intersection, scalar multiplication, vector sum, closure, interior, and
    linear transformations
:::

::: {.source-item #src-mit-l06-p022-i003 data-source-page="22" data-source-order="3"}
- Special convex sets:

  - **Polyhedral sets:** Nonempty sets of the form

    ::: {.source-display #src-mit-l06-p022-d002 data-source-page="22" data-display-order="2"}
    $$
    \{x\mid a_j'x\leq b_j, j=1,\ldots,r\}
    $$
    :::

    (always convex, closed, not always bounded)
  - **Cones:** Sets $C$ such that $\lambda x\in C$ for all $\lambda>0$ and
    $x\in C$ (not always convex or closed)
:::

*[Source page 22.]{.source-locator}*
:::

::: {.source-page #src-mit-l06-p023 data-source-page="23" data-source-order="4"}
## CONVEX FUNCTIONS

::: {.source-figure #src-mit-l06-p023-f001 data-source-page="23" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 23, chord test).** Above an interval
$C$, the graph marks $x$, $y$, and $\alpha x+(1-\alpha)y$. A chord joins
$(x,f(x))$ to $(y,f(y))$. At the interpolated point, the curve value
$f(\alpha x+(1-\alpha)y)$ lies at or below the chord height
$\alpha f(x)+(1-\alpha)f(y)$.
:::

::: {.source-item #src-mit-l06-p023-i001 data-source-page="23" data-source-order="1"}
- Let $C$ be a convex subset of $\mathbb{R}^n$. A function
  $f:C\mapsto\mathbb{R}$ is called convex if, for all $\alpha\in[0,1]$,

  ::: {.source-display #src-mit-l06-p023-d001 data-source-page="23" data-display-order="1"}
  $$
  f\bigl(\alpha x+(1-\alpha)y\bigr)
  \leq \alpha f(x)+(1-\alpha)f(y),
  \qquad \forall x,y\in C.
  $$
  :::

  If the inequality is strict whenever $a\in(0,1)$ and $x\neq y$, then $f$
  is called strictly convex over $C$.
:::

::: {.source-item #src-mit-l06-p023-i002 data-source-page="23" data-source-order="2"}
- If $f$ is a convex function, then all its level sets
  $\{x\in C\mid f(x)\leq\gamma\}$ and
  $\{x\in C\mid f(x)<\gamma\}$, where $\gamma$ is a scalar, are convex.
:::

*[Source page 23.]{.source-locator}*
:::

::: {.source-page #src-mit-l06-p024 data-source-page="24" data-source-order="5"}
## EXTENDED REAL-VALUED FUNCTIONS

::: {.source-figure #src-mit-l06-p024-f001 data-source-page="24" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 24, epigraph comparison).** The left
panel shows a convex function over one effective-domain interval; the shaded
epigraph above its graph is convex. The right panel shows a nonconvex function
on two separated effective-domain intervals; its shaded epigraph is not
convex. Both panels retain the labels $f(x)$, $x$, $\operatorname{dom}(f)$,
and **Epigraph**.
:::

::: {.source-item #src-mit-l06-p024-i001 data-source-page="24" data-source-order="1"}
- The epigraph of a function $f:X\mapsto[-\infty,\infty]$ is the subset of
  $\mathbb{R}^{n+1}$ given by

  ::: {.source-display #src-mit-l06-p024-d001 data-source-page="24" data-display-order="1"}
  $$
  \operatorname{epi}(f)
  =
  \{(x,w)\mid x\in X,\ w\in\mathbb{R},\ f(x)\leq w\}.
  $$
  :::
:::

::: {.source-item #src-mit-l06-p024-i002 data-source-page="24" data-source-order="2"}
- The effective domain of $f$ is the set

  ::: {.source-display #src-mit-l06-p024-d002 data-source-page="24" data-display-order="2"}
  $$
  \operatorname{dom}(f)=\{x\in X\mid f(x)<\infty\}.
  $$
  :::
:::

::: {.source-item #src-mit-l06-p024-i003 data-source-page="24" data-source-order="3"}
- We say that $f$ is convex if $\operatorname{epi}(f)$ is a convex set. If
  $f(x)\in\mathbb{R}$ for all $x\in X$ and $X$ is convex, the definition
  “coincides” with the earlier one.
:::

::: {.source-item #src-mit-l06-p024-i004 data-source-page="24" data-source-order="4"}
- We say that $f$ is closed if $\operatorname{epi}(f)$ is a closed set.
:::

::: {.source-item #src-mit-l06-p024-i005 data-source-page="24" data-source-order="5"}
- We say that $f$ is lower semicontinuous at a vector $x\in X$ if
  $f(x)\leq\liminf_{k\to\infty}f(x_k)$ for every sequence
  $\{x_k\}\subset X$ with $x_k\to x$.
:::

*[Source page 24.]{.source-locator}*
:::

::: {.source-page #src-mit-l06-p025 data-source-page="25" data-source-order="6"}
## CLOSEDNESS AND SEMICONTINUITY I

::: {.source-item #src-mit-l06-p025-i001 data-source-page="25" data-source-order="1"}
- **Proposition:** For a function
  $f:\mathbb{R}^n\mapsto[-\infty,\infty]$, the following are equivalent:

  (i) $V_\gamma=\{x\mid f(x)\leq\gamma\}$ is closed for all
  $\gamma\in\mathbb{R}$.

  (ii) $f$ is lower semicontinuous at all $x\in\mathbb{R}^n$.

  (iii) $f$ is closed.

  ::: {.source-figure #src-mit-l06-p025-f001 data-source-page="25" data-figure-disposition="omitted-source-graphic"}
  **Source-figure description (source page 25, epigraph and sublevel set).** A
  shaded epigraph lies above a function graph. A horizontal line at height
  $\gamma$ meets the graph, and dashed vertical projections identify the
  sublevel set $\{x\mid f(x)\leq\gamma\}$ on the $x$-axis. Retained labels
  are $f(x)$, $\operatorname{epi}(f)$, $\gamma$, $x$, and the sublevel set.
  :::
:::

::: {.source-item #src-mit-l06-p025-i002 data-source-page="25" data-source-order="2"}
- **(ii) $\Rightarrow$ (iii):** Let
  $\{(x_k,w_k)\}\subset\operatorname{epi}(f)$ with
  $(x_k,w_k)\to(\bar{x},\bar{w})$. Then $f(x_k)\leq w_k$, and

  ::: {.source-display #src-mit-l06-p025-d001 data-source-page="25" data-display-order="1"}
  $$
  f(\bar{x})
  \leq\liminf_{k\to\infty}f(x_k)
  \leq\bar{w},
  $$
  :::

  so $(\bar{x},\bar{w})\in\operatorname{epi}(f)$.
:::

::: {.source-item #src-mit-l06-p025-i003 data-source-page="25" data-source-order="3"}
- **(iii) $\Rightarrow$ (i):** Let
  $\{x_k\}\subset V_\gamma$ and $x_k\to\bar{x}$. Then
  $(x_k,\gamma)\in\operatorname{epi}(f)$ and
  $(x_k,\gamma)\to(\bar{x},\gamma)$, so
  $(\bar{x},\gamma)\in\operatorname{epi}(f)$ and
  $\bar{x}\in V_\gamma$.
:::

::: {.source-item #src-mit-l06-p025-i004 data-source-page="25" data-source-order="4"}
- **(i) $\Rightarrow$ (ii):** If $x_k\to\bar{x}$ and
  $f(\bar{x})>\gamma>\liminf_{k\to\infty}f(x_k)$, consider a subsequence
  $\{x_k\}_{\mathcal K}\to\bar{x}$ with $f(x_k)\leq\gamma$; this
  contradicts closedness of $V_\gamma$.
:::

*[Source page 25.]{.source-locator}*
:::

::: {.source-page #src-mit-l06-p026 data-source-page="26" data-source-order="7"}
## CLOSEDNESS AND SEMICONTINUITY II

::: {.source-item #src-mit-l06-p026-i001 data-source-page="26" data-source-order="1"}
- Lower semicontinuity of a function is a “domain-specific” property, but
  closedness is not:

  - If we change the domain of the function without changing its epigraph, its
    lower-semicontinuity properties may be affected.
  - **Example:** Define $f:(0,1)\to[-\infty,\infty]$ and
    $\hat f:[0,1]\to[-\infty,\infty]$ by

    ::: {.source-display #src-mit-l06-p026-d001 data-source-page="26" data-display-order="1"}
    $$
    f(x)=0,\qquad \forall x\in(0,1),
    $$
    :::

    ::: {.source-display #src-mit-l06-p026-d002 data-source-page="26" data-display-order="2"}
    $$
    \hat f(x)=
    \begin{cases}
    0,&x\in(0,1),\\
    \infty,&x=0\text{ or }x=1.
    \end{cases}
    $$
    :::

    Then $f$ and $\hat f$ have the same epigraph, and both are not closed.
    But $f$ is lower semicontinuous while $\hat f$ is not.
:::

::: {.source-item #src-mit-l06-p026-i002 data-source-page="26" data-source-order="2"}
- Note that:

  - If $f$ is lower semicontinuous at all
    $x\in\operatorname{dom}(f)$, it is not necessarily closed.
  - If $f$ is closed, $\operatorname{dom}(f)$ is not necessarily closed.
:::

::: {.source-item #src-mit-l06-p026-i003 data-source-page="26" data-source-order="3"}
- **Proposition:** Let $f:X\mapsto[-\infty,\infty]$ be a function. If
  $\operatorname{dom}(f)$ is closed and $f$ is lower semicontinuous at all
  $x\in\operatorname{dom}(f)$, then $f$ is closed.
:::

*[Source page 26.]{.source-locator}*
:::

::: {.source-page #src-mit-l06-p027 data-source-page="27" data-source-order="8"}
## PROPER AND IMPROPER CONVEX FUNCTIONS

::: {.source-figure #src-mit-l06-p027-f001 data-source-page="27" data-figure-disposition="omitted-source-graphic"}
**Source-figure description (source page 27, improper functions).** Two panels
shade epigraphs over interval-like effective domains. The left epigraph omits a
vertical boundary, with a dashed line marking the missing edge, and is labeled
**Not Closed Improper Function**. The right epigraph includes its vertical
boundary and is labeled **Closed Improper Function**. Both panels retain
$f(x)$, $x$, $\operatorname{epi}(f)$, and $\operatorname{dom}(f)$.
:::

::: {.source-item #src-mit-l06-p027-i001 data-source-page="27" data-source-order="1"}
- We say that $f$ is proper if $f(x)<\infty$ for at least one $x\in X$ and
  $f(x)>-\infty$ for all $x\in X$, and we call $f$ improper if it is not
  proper.
:::

::: {.source-item #src-mit-l06-p027-i002 data-source-page="27" data-source-order="2"}
- Note that $f$ is proper if and only if its epigraph is nonempty and does not
  contain a “vertical line.”
:::

::: {.source-item #src-mit-l06-p027-i003 data-source-page="27" data-source-order="3"}
- An improper closed convex function is very peculiar: it takes an infinite
  value ($\infty$ or $-\infty$) at every point.
:::

*[Source page 27.]{.source-locator}*
:::

::: {.source-page #src-mit-l06-p028 data-source-page="28" data-source-order="9"}
## RECOGNIZING CONVEX FUNCTIONS

::: {.source-item #src-mit-l06-p028-i001 data-source-page="28" data-source-order="1"}
- Some important classes of elementary convex functions: affine functions,
  positive-semidefinite quadratic functions, norm functions, etc.
:::

::: {.source-item #src-mit-l06-p028-i002 data-source-page="28" data-source-order="2"}
- **Proposition:**

  (a) The function $g:\mathbb{R}^n\mapsto(-\infty,\infty]$ given by

      ::: {.source-display #src-mit-l06-p028-d001 data-source-page="28" data-display-order="1"}
      $$
      g(x)=\lambda_1f_1(x)+\cdots+\lambda_mf_m(x),
      \qquad \lambda_i>0,
      $$
      :::

      is convex (or closed) if $f_1,\ldots,f_m$ are convex (respectively,
      closed).

  (b) The function $g:\mathbb{R}^n\mapsto(-\infty,\infty]$ given by

      ::: {.source-display #src-mit-l06-p028-d002 data-source-page="28" data-display-order="2"}
      $$
      g(x)=f(Ax),
      $$
      :::

      where $A$ is an $m\times n$ matrix, is convex (or closed) if $f$ is
      convex (respectively, closed).

  (c) Consider $f_i:\mathbb{R}^n\mapsto(-\infty,\infty]$, $i\in I$,
  where $I$ is any index set. The function
  $g:\mathbb{R}^n\mapsto(-\infty,\infty]$ given by

      ::: {.source-display #src-mit-l06-p028-d003 data-source-page="28" data-display-order="3"}
      $$
      g(x)=\sup_{i\in I}f_i(x)
      $$
      :::

      is convex (or closed) if the $f_i$ are convex (respectively, closed).
:::

*[Source page 28.]{.source-locator}*
:::
