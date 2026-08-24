---
title: "MIT 6.253 Lecture 6 semantic transcription witness"
subtitle: "Complete-notes PDF pages 64-85"
author: "Dimitri P. Bertsekas (source author)"
lang: en
date: "2026-08-24"
rights: "CC BY-NC-SA 4.0"
---

This project-made semantic witness transcribes the complete Lecture 6 sequence from pages 64-85 of Dimitri P. Bertsekas's *Convex Analysis and Optimization: Complete Lecture Notes* for MIT OpenCourseWare 6.253. Page 86 begins Lecture 7 and is the excluded delimiter. This witness is not an official editable source. Its lineation, stable identifiers, source-page fences, accessibility prose, and defect notices are project additions.

The source PDF is selectable and tagged, but the selected boundary has no annotations, widgets, media, links, code cells, or interactive exercise surfaces. Permission-restricted source figure pixels and layouts are omitted. Sixteen figure blocks containing twenty-four separately meaningful panels are represented by independently worded semantic descriptions. Mathematical notation was checked visually against rendered source pages because text extraction corrupts blackboard-bold real-number symbols, membership and intersection signs, infinity and empty-set signs, inequalities, transpose marks, norms, and mapsto arrows.

This transcription was produced with **OpenAI Codex gpt-5.6-sol, Ultra**, at the repository user's direction. It has not received human review and implies no endorsement by the source author, MIT, or MIT OpenCourseWare.

::: {.source-page #d90-mit-l10-p064 data-source-page="64" data-source-order="1"}
## Lecture 6 - Lecture outline

::: {.source-item #d90-mit-l10-p064-i001 data-source-page="64" data-source-order="1"}
- Nonemptiness of closed set intersections

  - Simple version
  - More complex version
:::

::: {.source-item #d90-mit-l10-p064-i002 data-source-page="64" data-source-order="2"}
- Existence of optimal solutions
:::

::: {.source-item #d90-mit-l10-p064-i003 data-source-page="64" data-source-order="3"}
- Preservation of closure under linear transformation
:::

::: {.source-item #d90-mit-l10-p064-i004 data-source-page="64" data-source-order="4"}
- Hyperplanes
:::

*[Source page 64.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l10-p065-n001 data-source-pages="65,68,70" data-defect-class="printed-function-type-arrow" data-correction-event="O015-MIT-SEM-0020"}
**Printed notation preserved.** In the function declarations on source pages
65, 68, and 70, the source prints a mapsto arrow (`\mapsto`) between the
domain and codomain. This witness retains that printed symbol rather than
silently replacing it with the function-type arrow `\to`.
:::

::: {.source-page #d90-mit-l10-p065 data-source-page="65" data-source-order="2"}
## Role of closed set intersections I

::: {.source-item #d90-mit-l10-p065-i001 data-source-page="65" data-source-order="1"}
**A fundamental question:** Given a sequence of nonempty closed sets
$\{C_k\}$ in $\mathbb R^n$ with $C_{k+1}\subset C_k$ for all $k$, when is

::: {.source-display #d90-mit-l10-p065-d001 data-source-page="65" data-display-order="1"}
$$
\bigcap_{k=0}^{\infty}C_k
$$
:::

nonempty?
:::

::: {.source-item #d90-mit-l10-p065-i002 data-source-page="65" data-source-order="2"}
- Set intersection theorems are significant in at least three major contexts,
  which we will discuss in what follows:

  **Does a function $f:\mathbb R^n\mapsto(-\infty,\infty]$ attain a minimum
  over a set $X$?**

  This is true if and only if

::: {.source-display #d90-mit-l10-p065-d002 data-source-page="65" data-display-order="2"}
$$
\text{Intersection of nonempty }
\{x\in X\mid f(x)\leq\gamma_k\}
\text{ is nonempty.}
$$
:::
:::

::: {.source-ambiguity-note #d90-mit-l10-p065-n002 data-source-page="65"}
**Printed compression preserved.** The slide describes the intersection in
words and displays the family $\{x\in X\mid f(x)\leq\gamma_k\}$, but it does
not state the index range or the assumptions on $\{\gamma_k\}$. The witness
does not supply them.
:::

::: {.source-figure #d90-mit-l10-p065-f001 data-source-page="65" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Semantic description of the omitted source figure.** Several nested oval
sublevel contours of $f$ overlap a separate shaded feasible set $X$. A marked
point lies where the innermost relevant contour first meets $X$ and is labeled
as an optimal solution. The picture connects attainment over $X$ with the
nonempty intersection of $X$ and progressively lower sublevel sets.
:::

*[Source page 65.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p066 data-source-page="66" data-source-order="3"}
## Role of closed set intersections II

::: {.source-item #d90-mit-l10-p066-i001 data-source-page="66" data-source-order="1"}
If $C$ is closed and $A$ is a matrix, is $AC$ closed?
:::

::: {.source-figure #d90-mit-l10-p066-f001 data-source-page="66" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Semantic description of the omitted source figure.** In the domain, a
curved closed set $C$ overlaps a vertical inverse-image strip $N_k$; their
intersection is labeled $C_k$, and a point $\bar{x}$ lies in that overlap. On
the image axis below, the points $\bar{y}$, $y_{k+1}$, and $y_k$ lie in the
linear image $AC$. Dashed alignment from $\bar{x}$ to $\bar{y}$ and the nested
image neighborhoods indicate how a nonempty intersection of the preimage sets
can produce a preimage of the limit point.
:::

::: {.source-item #d90-mit-l10-p066-i002 data-source-page="66" data-source-order="2"}
- If $C_1$ and $C_2$ are closed, is $C_1+C_2$ closed?

  - This is a special case.
  - Write

::: {.source-display #d90-mit-l10-p066-d001 data-source-page="66" data-display-order="1"}
$$
C_1+C_2=A(C_1\times C_2),
\qquad
A(x_1,x_2)=x_1+x_2.
$$
:::
:::

*[Source page 66.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l10-p067-n001 data-source-page="67" data-defect-class="printed-missing-noun" data-correction-event="O015-MIT-SEM-0021"}
**Printed wording preserved.** The opening sentence calls $C$ “a nonempty
closed convex” and omits the noun *set*. The witness retains that wording.
:::

::: {.source-defect-notice #d90-mit-l10-p067-n002 data-source-pages="67,78" data-defect-class="nonnested-proof-neighborhoods" data-correction-event="O015-MIT-SEM-0023"}
**Printed proof construction preserved.** On pages 67 and 78, the source calls
the sets $C_k=C\cap N_k$ nested while defining $W_k$ with radius
$\lVert y_k-\bar y\rVert$. Convergence alone does not make those radii
nonincreasing. The Indonesian derivative uses decreasing tail-supremum radii,
which preserves every $y_k$ in its corresponding neighborhood and makes the
claimed nesting valid.
:::

::: {.source-page #d90-mit-l10-p067 data-source-page="67" data-source-order="4"}
## Closure under linear transformation

::: {.source-item #d90-mit-l10-p067-i001 data-source-page="67" data-source-order="1"}
- Let $C$ be a nonempty closed convex, and let $A$ be a matrix with nullspace
  $N(A)$. Then $AC$ is closed if $R_C\cap N(A)=\{0\}$.

  **Proof:** Let $\{y_k\}\subset AC$ with $y_k\to\bar y$. Define the nested
  sequence $C_k=C\cap N_k$, where

::: {.source-display #d90-mit-l10-p067-d001 data-source-page="67" data-display-order="1"}
$$
N_k=\{x\mid Ax\in W_k\},
\qquad
W_k=\{z\mid\lVert z-\bar y\rVert\leq\lVert y_k-\bar y\rVert\}.
$$
:::

  We have $R_{N_k}=N(A)$, so $C_k$ is compact, and $\{C_k\}$ has nonempty
  intersection. Q.E.D.
:::

::: {.source-figure #d90-mit-l10-p067-f001 data-source-page="67" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Semantic description of the omitted source figure.** The same preimage
construction used on source page 66 is shown at a smaller scale. A vertical
strip $N_k$ cuts the curved set $C$ to form $C_k$ around $\bar{x}$; its image
axis contains $\bar{y}$ and the approaching points $y_{k+1},y_k$ inside $AC$.
The diagram supports the proof that a common point of the nested $C_k$ maps to
the limit $\bar{y}$.
:::

::: {.source-item #d90-mit-l10-p067-i002 data-source-page="67" data-source-order="2"}
- **A special case:** $C_1+C_2$ is closed if $C_1,C_2$ are closed and one of
  the two is compact. [Write $C_1+C_2=A(C_1\times C_2)$, where
  $A(x_1,x_2)=x_1+x_2$.]
:::

::: {.source-item #d90-mit-l10-p067-i003 data-source-page="67" data-source-order="3"}
- **Related theorem:** $AX$ is closed if $X$ is polyhedral. To be shown later
  by a more refined method.
:::

*[Source page 67.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l10-p068-n001 data-source-page="68" data-defect-class="unbound-projection-variable" data-correction-event="O015-MIT-SEM-0030"}
**Printed set-builder preserved.** In the definition of the projection $P(S)$,
the source writes $(x,z,w)\in S$ while leaving $z$ unbound. The intended
projection requires existence of some $z\in\mathbb R^m$. The Indonesian
derivative supplies that existential binder explicitly.
:::

::: {.source-page #d90-mit-l10-p068 data-source-page="68" data-source-order="5"}
## Role of closed set intersections III

::: {.source-item #d90-mit-l10-p068-i001 data-source-page="68" data-source-order="1"}
- Let $F:\mathbb R^{n+m}\mapsto(-\infty,\infty]$ be a closed proper convex
  function, and consider

::: {.source-display #d90-mit-l10-p068-d001 data-source-page="68" data-display-order="1"}
$$
f(x)=\inf_{z\in\mathbb R^m}F(x,z).
$$
:::
:::

::: {.source-item #d90-mit-l10-p068-i002 data-source-page="68" data-source-order="2"}
- **If $F(x,z)$ is closed, is $f(x)$ closed?**

  - Critical question in duality theory.
:::

::: {.source-item #d90-mit-l10-p068-i003 data-source-page="68" data-source-order="3"}
- **1st fact:** If $F$ is convex, then $f$ is also convex.
:::

::: {.source-item #d90-mit-l10-p068-i004 data-source-page="68" data-source-order="4"}
- **2nd fact:**

::: {.source-display #d90-mit-l10-p068-d002 data-source-page="68" data-display-order="2"}
$$
P\bigl(\operatorname{epi}(F)\bigr)
\subset
\operatorname{epi}(f)
\subset
\operatorname{cl}\!\left(P\bigl(\operatorname{epi}(F)\bigr)\right),
$$
:::

  where $P(\cdot)$ denotes projection on the space of $(x,w)$, i.e., for any
  subset $S$ of $\mathbb R^{n+m+1}$,
  $P(S)=\{(x,w)\mid(x,z,w)\in S\}$.
:::

::: {.source-item #d90-mit-l10-p068-i005 data-source-page="68" data-source-order="5"}
- Thus, if $F$ is closed and there is structure guaranteeing that the
  projection preserves closedness, then $f$ is closed.
:::

::: {.source-item #d90-mit-l10-p068-i006 data-source-page="68" data-source-order="6"}
- ... but convexity and closedness of $F$ does not guarantee closedness of
  $f$.
:::

*[Source page 68.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p069 data-source-page="69" data-source-order="6"}
## Partial minimization: Visualization

::: {.source-item #d90-mit-l10-p069-i001 data-source-page="69" data-source-order="1"}
- Connection of preservation of closedness under partial minimization and
  attainment of infimum over $z$ for fixed $x$.
:::

::: {.source-figure #d90-mit-l10-p069-f001 data-source-page="69" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Semantic description of the omitted two-panel source figure.** Both panels
use coordinates $(x,z,w)$ and show a convex surface labeled $F(x,z)$ above the
$(x,z)$ plane. The lower envelope obtained by moving in the $z$ direction is
marked as $f(x)=\inf_zF(x,z)$, and its vertical epigraph is shown in the
$(x,w)$ plane. In the first panel, surface traces descend toward the lower
envelope along $z$ without visibly turning upward; in the second, the traces
curve through attained low points. Together the panels contrast a projected
epigraph boundary approached only asymptotically with one supplied by attained
partial minima.
:::

::: {.source-item #d90-mit-l10-p069-i002 .source-example data-source-page="69" data-source-order="2"}
- **Counterexample:** Let

::: {.source-display #d90-mit-l10-p069-d001 data-source-page="69" data-display-order="1"}
$$
F(x,z)=
\begin{cases}
e^{-\sqrt{xz}}, & \text{if }x\geq0, z\geq0,\\
\infty, & \text{otherwise.}
\end{cases}
$$
:::
:::

::: {.source-item #d90-mit-l10-p069-i003 data-source-page="69" data-source-order="3"}
- $F$ convex and closed, but

::: {.source-display #d90-mit-l10-p069-d002 data-source-page="69" data-display-order="2"}
$$
f(x)=\inf_{z\in\mathbb R}F(x,z)=
\begin{cases}
0, & \text{if }x>0,\\
1, & \text{if }x=0,\\
\infty, & \text{if }x<0,
\end{cases}
$$
:::

  is not closed.
:::

*[Source page 69.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l10-p070-n001 data-source-pages="70,77" data-defect-class="printed-minimum-minimizer-terminology" data-correction-event="O015-MIT-SEM-0022"}
**Printed terminology preserved.** Pages 70 and 77 use *minimum/minima* for
points that attain the objective, although those objects are minimizers rather
than scalar minimum values. The witness retains the printed terminology.
:::

::: {.source-page #d90-mit-l10-p070 data-source-page="70" data-source-order="7"}
## Partial minimization theorem

::: {.source-item #d90-mit-l10-p070-i001 data-source-page="70" data-source-order="1"}
Let $F:\mathbb R^{n+m}\mapsto(-\infty,\infty]$ be a closed proper convex
function, and consider $f(x)=\inf_{z\in\mathbb R^m}F(x,z)$.
:::

::: {.source-item #d90-mit-l10-p070-i002 data-source-page="70" data-source-order="2"}
- Every set intersection theorem yields a closedness result. The simplest case
  is the following:
:::

::: {.source-item #d90-mit-l10-p070-i003 data-source-page="70" data-source-order="3"}
- **Preservation of Closedness Under Compactness:** If there exist
  $\bar{x}\in\mathbb R^n$, $\bar{\gamma}\in\mathbb R$ such that the set

::: {.source-display #d90-mit-l10-p070-d001 data-source-page="70" data-display-order="1"}
$$
\{z\mid F(\bar{x},z)\leq\bar{\gamma}\}
$$
:::

  is nonempty and compact, then $f$ is convex, closed, and proper. Also, for
  each $x\in\operatorname{dom}(f)$, the set of minima of $F(x,\cdot)$ is
  nonempty and compact.
:::

::: {.source-figure #d90-mit-l10-p070-f001 data-source-page="70" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Semantic description of the omitted two-panel source figure.** Each panel
shows a convex surface $F(x,z)$ in $(x,z,w)$ coordinates and the lower envelope
$f(x)=\inf_zF(x,z)$ projected to the $(x,w)$ plane as the boundary of
$\operatorname{epi}(f)$. One panel depicts profiles that can run away along
the $z$ direction toward the envelope, while the other depicts profiles with
attained troughs. The compact-sublevel hypothesis rules out the runaway
behavior relevant to the theorem, so partial minimizers exist and the lower
envelope is retained as a closed boundary.
:::

*[Source page 70.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p071 data-source-page="71" data-source-order="8"}
## More refined analysis - a summary

::: {.source-defect-notice #d90-mit-l10-p071-n001 data-source-page="71" data-correction-event="O015-MIT-SEM-0024"}
**Printed wording preserved.** The first subitem on source page 71 reads
“Existence of of solutions,” with *of* repeated. This witness retains the
duplication exactly; the Indonesian edition removes the duplicate word.
:::

::: {.source-item #d90-mit-l10-p071-i001 data-source-page="71" data-source-order="1"}
- We noted that there is a common mathematical root to three basic questions:

  - Existence of of solutions of convex optimization problems

  - Preservation of closedness of convex sets under a linear transformation

  - Preservation of closedness of convex functions under partial minimization
:::

::: {.source-item #d90-mit-l10-p071-i002 data-source-page="71" data-source-order="2"}
- The common root is the question of nonemptiness of intersection of a nested
  sequence of closed sets.
:::

::: {.source-item #d90-mit-l10-p071-i003 data-source-page="71" data-source-order="3"}
- The preceding development in this lecture resolved this question by assuming
  that all the sets in the sequence are compact.
:::

::: {.source-item #d90-mit-l10-p071-i004 data-source-page="71" data-source-order="4"}
- A more refined development makes instead various assumptions about the
  directions of recession and the lineality space of the sets in the sequence.
:::

::: {.source-item #d90-mit-l10-p071-i005 data-source-page="71" data-source-order="5"}
- Once the appropriately refined set intersection theory is developed, sharper
  results relating to the three questions can be obtained.
:::

::: {.source-item #d90-mit-l10-p071-i006 data-source-page="71" data-source-order="6"}
- The remaining slides up to hyperplanes summarize this development as an aid
  for self-study using Sections 1.4.2, 1.4.3, and Sections 3.2, 3.3.
:::

*[Source page 71.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p072 data-source-page="72" data-source-order="9"}
## Asymptotic sequences

::: {.source-defect-notice #d90-mit-l10-p072-n001 data-source-page="72" data-correction-event="O015-MIT-SEM-0025"}
**Printed wording preserved.** The opening definition on source page 72 begins
“Given nested sequence,” omitting the article *a*. This witness retains that
wording; the Indonesian edition supplies a complete grammatical construction.
:::

::: {.source-item #d90-mit-l10-p072-i001 data-source-page="72" data-source-order="1"}
- Given nested sequence $\{C_k\}$ of closed convex sets, $\{x_k\}$ is an
  asymptotic sequence if

  ::: {.source-display #d90-mit-l10-p072-d001 data-source-page="72" data-display-order="1"}
  $$
  x_k\in C_k,\qquad x_k\neq 0,\qquad k=0,1,\ldots
  $$
  :::

  ::: {.source-display #d90-mit-l10-p072-d002 data-source-page="72" data-display-order="2"}
  $$
  \lVert x_k\rVert\to\infty,
  \qquad
  \frac{x_k}{\lVert x_k\rVert}\to\frac{d}{\lVert d\rVert},
  $$
  :::

  where $d$ is a nonzero common direction of recession of the sets $C_k$.
:::

::: {.source-item #d90-mit-l10-p072-i002 data-source-page="72" data-source-order="2"}
- As a special case we define asymptotic sequence of a closed convex set $C$
  (use $C_k\equiv C$).
:::

::: {.source-item #d90-mit-l10-p072-i003 data-source-page="72" data-source-order="3"}
- Every unbounded $\{x_k\}$ with $x_k\in C_k$ has an asymptotic subsequence.
:::

::: {.source-item #d90-mit-l10-p072-i004 data-source-page="72" data-source-order="4"}
- $\{x_k\}$ is called retractive if for some $\bar{k}$, we have

  ::: {.source-display #d90-mit-l10-p072-d003 data-source-page="72" data-display-order="3"}
  $$
  x_k-d\in C_k,\qquad \forall k\geq\bar{k}.
  $$
  :::
:::

::: {.source-figure #d90-mit-l10-p072-f001 data-source-page="72" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** The labeled points
$x_0,x_1,\ldots,x_5$ move progressively farther from the origin while their
directions settle toward a common orientation. A separate vector $d$ begins at
the origin and identifies that limiting orientation. The upper sequence and
the lower direction marker connect the unbounded asymptotic sequence with its
normalized asymptotic direction.
:::

*[Source page 72.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p073 data-source-page="73" data-source-order="10"}
## Retractive sequences

::: {.source-item #d90-mit-l10-p073-i001 data-source-page="73" data-source-order="1"}
- A nested sequence $\{C_k\}$ of closed convex sets is retractive if all its
  asymptotic sequences are retractive.
:::

::: {.source-figure #d90-mit-l10-p073-f001 data-source-page="73" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Semantic description of the omitted two-panel source figure.**

- **Panel (a), retractive set sequence:** Three nested closed convex sets
  $C_0,C_1,C_2$ narrow around their nonempty common intersection. Successive
  points $x_0,x_1,x_2,x_3$ escape in direction $d$, yet translating sufficiently
  late points by $-d$ keeps them in their corresponding sets.
- **Panel (b), nonretractive set sequence:** Nested curved convex sets
  $C_0,C_1,C_2$ share a limiting intersection but taper toward it. The escaping
  points $x_0,x_1,x_2$ have asymptotic direction $d$, while a unit step opposite
  $d$ eventually leaves the matching curved set. The contrast isolates the
  retraction property rather than mere nestedness or nonempty intersection.
:::

::: {.source-item #d90-mit-l10-p073-i002 data-source-page="73" data-source-order="2"}
- A closed halfspace (viewed as a sequence with identical components) is
  retractive.
:::

::: {.source-item #d90-mit-l10-p073-i003 data-source-page="73" data-source-order="3"}
- Intersections and Cartesian products of retractive set sequences are
  retractive.
:::

::: {.source-item #d90-mit-l10-p073-i004 data-source-page="73" data-source-order="4"}
- A polyhedral set is retractive. Also the vector sum of a convex compact set
  and a retractive convex set is retractive.
:::

::: {.source-item #d90-mit-l10-p073-i005 data-source-page="73" data-source-order="5"}
- Nonpolyhedral cones and level sets of quadratic functions need not be
  retractive.
:::

*[Source page 73.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p074 data-source-page="74" data-source-order="11"}
## Set intersection theorem I

::: {.source-item #d90-mit-l10-p074-i001 data-source-page="74" data-source-order="1"}
- Proposition: If $\{C_k\}$ is retractive, then
  $\bigcap_{k=0}^{\infty}C_k$ is nonempty.
:::

::: {.source-item #d90-mit-l10-p074-i002 data-source-page="74" data-source-order="2"}
- Key proof ideas:

  (a) The intersection $\bigcap_{k=0}^{\infty}C_k$ is empty iff the sequence
  $\{x_k\}$ of minimum norm vectors of $C_k$ is unbounded (so a subsequence is
  asymptotic).

  (b) An asymptotic sequence $\{x_k\}$ of minimum norm vectors cannot be
  retractive, because such a sequence eventually gets closer to $0$ when
  shifted opposite to the asymptotic direction.
:::

::: {.source-figure #d90-mit-l10-p074-f001 data-source-page="74" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** The points
$x_0,x_1,\ldots,x_5$ form an unbounded sequence whose directions from the
origin converge toward $d$. Because each $x_k$ is the closest point of $C_k$
to the origin, a retractive displacement $x_k-d$ that remains in $C_k$ would
contradict minimal norm once $k$ is large: the displacement lies closer to the
origin. The drawing supplies the geometric relation used in proof step (b).
:::

*[Source page 74.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p075 data-source-page="75" data-source-order="12"}
## Set intersection theorem II

::: {.source-item #d90-mit-l10-p075-i001 data-source-page="75" data-source-order="1"}
- Proposition: Let $\{C_k\}$ be a nested sequence of nonempty closed convex
  sets, and $X$ be a retractive set such that all the sets
  $\bar C_k=X\cap C_k$ are nonempty. Assume that

  ::: {.source-display #d90-mit-l10-p075-d001 data-source-page="75" data-display-order="1"}
  $$
  R_X\cap R\subset L,
  $$
  :::

  where

  ::: {.source-display #d90-mit-l10-p075-d002 data-source-page="75" data-display-order="2"}
  $$
  R=\bigcap_{k=0}^{\infty}R_{C_k},
  \qquad
  L=\bigcap_{k=0}^{\infty}L_{C_k}.
  $$
  :::

  Then

  ::: {.source-display #d90-mit-l10-p075-d003 data-source-page="75" data-display-order="3"}
  $$
  \{\bar C_k\}\text{ is retractive},
  \qquad
  \bigcap_{k=0}^{\infty}\bar C_k\neq\varnothing.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p075-i002 data-source-page="75" data-source-order="2"}
- Special cases:

  - $X=\mathbb R^n$, $R=L$ (“cylindrical” sets $C_k$)

  - $R_X\cap R=\{0\}$ (no nonzero common recession direction of $X$ and
    $\bigcap_k C_k$)
:::

::: {.source-item #d90-mit-l10-p075-i003 data-source-page="75" data-source-order="3"}
**Proof:** The set of common directions of recession of $\bar C_k$ is
$R_X\cap R$. For any asymptotic sequence $\{x_k\}$ corresponding to
$d\in R_X\cap R$:

**(1)**

::: {.source-display #d90-mit-l10-p075-d004 data-source-page="75" data-display-order="4"}
$$
x_k-d\in C_k\qquad\text{(because }d\in L\text{)}.
$$
:::

**(2)**

::: {.source-display #d90-mit-l10-p075-d005 data-source-page="75" data-display-order="5"}
$$
x_k-d\in X\qquad\text{(because }X\text{ is retractive)}.
$$
:::

So $\{\bar C_k\}$ is retractive.
:::

*[Source page 75.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p076 data-source-page="76" data-source-order="13"}
## Need to assume that X is retractive

::: {.source-figure #d90-mit-l10-p076-f001 data-source-page="76" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Semantic description of the omitted two-panel source figure.** Both panels
intersect the same kind of nested vertical closed convex regions
$C_{k+1}\subset C_k$ with a set $X$.

- **Left panel:** A polyhedral, V-shaped $X$ crosses every nested region, and
  the resulting sets $\bar C_k=X\cap C_k$ retain a common point.
- **Right panel:** A curved nonpolyhedral $X$ approaches the narrowing regions
  without reaching their limiting location. Every individual
  $\bar C_k=X\cap C_k$ is nonempty, but their infinite intersection is empty.
  The differing geometry shows why the recession inclusion alone does not
  replace retractivity of $X$.
:::

::: {.source-item #d90-mit-l10-p076-i001 data-source-page="76" data-source-order="1"}
- Consider

  ::: {.source-display #d90-mit-l10-p076-d001 data-source-page="76" data-display-order="1"}
  $$
  \bigcap_{k=0}^{\infty}\bar C_k,
  \qquad
  \bar C_k=X\cap C_k.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p076-i002 data-source-page="76" data-source-order="2"}
- The condition $R_X\cap R\subset L$ holds.
:::

::: {.source-item #d90-mit-l10-p076-i003 data-source-page="76" data-source-order="3"}
- In the figure on the left, $X$ is polyhedral.
:::

::: {.source-item #d90-mit-l10-p076-i004 data-source-page="76" data-source-order="4"}
- In the figure on the right, $X$ is nonpolyhedral and nonretrative, and

  ::: {.source-display #d90-mit-l10-p076-d002 data-source-page="76" data-display-order="2"}
  $$
  \bigcap_{k=0}^{\infty}\bar C_k=\varnothing.
  $$
  :::
:::

::: {.source-defect-notice #d90-mit-l10-p076-n001 data-source-page="76" data-correction-event="O015-MIT-SEM-0026"}
**Printed spelling preserved.** The last bullet on source page 76 prints
“nonretrative,” omitting the *c* in *nonretractive*. This witness keeps that
spelling; the Indonesian edition uses the correctly formed technical term.
:::

*[Source page 76.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p077 data-source-page="77" data-source-order="14"}
## Linear and quadratic programming

::: {.source-item #d90-mit-l10-p077-i001 data-source-page="77" data-source-order="1"}
- Theorem: Let

  ::: {.source-display #d90-mit-l10-p077-d001 data-source-page="77" data-display-order="1"}
  $$
  f(x)=x'Qx+c'x,
  \qquad
  X=\{x\mid a_j'x+b_j\leq 0,\ j=1,\ldots,r\},
  $$
  :::

  where $Q$ is symmetric positive semidefinite. If the minimal value of $f$
  over $X$ is finite, there exists a minimum of $f$ over $X$.
:::

::: {.source-item #d90-mit-l10-p077-i002 data-source-page="77" data-source-order="2"}
- Proof: (Outline) Write

  ::: {.source-display #d90-mit-l10-p077-d002 data-source-page="77" data-display-order="2"}
  $$
  \text{Set of Minima}
  =\bigcap_{k=0}^{\infty}
  \left(X\cap\{x\mid x'Qx+c'x\leq\gamma_k\}\right)
  $$
  :::

  with

  ::: {.source-display #d90-mit-l10-p077-d003 data-source-page="77" data-display-order="3"}
  $$
  \gamma_k\downarrow f^*=\inf_{x\in X}f(x).
  $$
  :::

  Verify the condition $R_X\cap R\subset L$ of the preceding set intersection
  theorem, where $R$ and $L$ are the sets of common recession and lineality
  directions of the sets

  ::: {.source-display #d90-mit-l10-p077-d004 data-source-page="77" data-display-order="4"}
  $$
  \{x\mid x'Qx+c'x\leq\gamma_k\}.
  $$
  :::

  Q.E.D.
:::

*[Source page 77.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p078 data-source-page="78" data-source-order="15"}
## Closure under linear transformation

::: {.source-defect-notice #d90-mit-l10-p078-n001 data-source-page="78" data-correction-event="O015-MIT-SEM-0021"}
**Printed wording preserved.** The opening sentence on source page 78 calls
$C$ “a nonempty closed convex,” omitting the noun *set*. This witness retains
that incomplete phrase; the Indonesian edition supplies the missing noun.
:::

::: {.source-defect-notice #d90-mit-l10-p078-n002 data-source-page="78" data-correction-event="O015-MIT-SEM-0027"}
**Printed proof scope preserved.** The theorem states parts (a) and (b), but
the printed outline starts only with $\{y_k\}\subset AC$ and
$C_k=C\cap N_k$. For part (b), the required sequence lies in $A(X\cap C)$
and the preimage sets are $X\cap C\cap N_k$. The Indonesian derivative makes
that second construction explicit rather than presenting the outline for
part (a) as if it proved both parts.
:::

::: {.source-item #d90-mit-l10-p078-i001 data-source-page="78" data-source-order="1"}
- Let $C$ be a nonempty closed convex, and let $A$ be a matrix with nullspace
  $N(A)$.

  (a) $AC$ is closed if $R_C\cap N(A)\subset L_C$.

  (b) $A(X\cap C)$ is closed if $X$ is a retractive set and

  ::: {.source-display #d90-mit-l10-p078-d001 data-source-page="78" data-display-order="1"}
  $$
  R_X\cap R_C\cap N(A)\subset L_C.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p078-i002 data-source-page="78" data-source-order="2"}
- Proof: (Outline) Let $\{y_k\}\subset AC$ with $y_k\to\bar y$. We prove
  $\bigcap_{k=0}^{\infty}C_k\neq\varnothing$, where
  $C_k=C\cap N_k$, and

  ::: {.source-display #d90-mit-l10-p078-d002 data-source-page="78" data-display-order="2"}
  $$
  N_k=\{x\mid Ax\in W_k\},
  \qquad
  W_k=\{z\mid\lVert z-\bar y\rVert\leq\lVert y_k-\bar y\rVert\}.
  $$
  :::
:::

::: {.source-figure #d90-mit-l10-p078-f001 data-source-page="78" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** A closed convex set
$C$ is cut by nested inverse-image sets $N_k$, producing the feasible slices
$C_k=C\cap N_k$ and a limiting point $\bar x$ in their intersection. Under
the linear map $A$, the image $AC$ contains the convergent points $y_k$ and
$y_{k+1}$ approaching $\bar y$. The paired relations $Ax_k\in W_k$ and
$y_k\to\bar y$ show how nonemptiness of the nested preimage intersection
produces a preimage of the limit, hence closedness of $AC$.
:::

::: {.source-item #d90-mit-l10-p078-i003 data-source-page="78" data-source-order="3"}
- Special Case: $AX$ is closed if $X$ is polyhedral.
:::

*[Source page 78.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p079 data-source-page="79" data-source-order="16"}
## Need to assume that $X$ is retractive

::: {.source-figure #d90-mit-l10-p079-f001 data-source-page="79" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** Two coordinate sketches compare the projection of $X\cap C$ under $A$. In each sketch, $N(A)$ is the vertical direction, $C$ is a vertical strip, and the image $A(X\cap C)$ is marked on the horizontal axis. On the left, the boundary of the polygonal set $X$ crosses the strip and the marked image has both limiting endpoints. On the right, a curved boundary of $X$ approaches a dashed vertical line inside the strip without reaching it; the corresponding projected image misses the limiting endpoint. Thus the pictures keep the recession-cone condition fixed while contrasting a retractive $X$ with a nonretractive $X$ and a closed image with a nonclosed image.
:::

::: {.source-item #d90-mit-l10-p079-i001 data-source-page="79" data-source-order="1"}
Consider closedness of $A(X\cap C)$.
:::

::: {.source-item #d90-mit-l10-p079-i002 data-source-page="79" data-source-order="2"}
- In both examples the condition

  ::: {.source-display #d90-mit-l10-p079-d001 data-source-page="79" data-display-order="1"}
  $$
  R_X\cap R_C\cap N(A)\subset L_C
  $$
  :::

  is satisfied.
:::

::: {.source-item #d90-mit-l10-p079-i003 data-source-page="79" data-source-order="3"}
- However, in the example on the right, $X$ is not retractive, and the set $A(X\cap C)$ is not closed.
:::

*[Source page 79.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p080 data-source-page="80" data-source-order="17"}
## Closedness of vector sums

::: {.source-item #d90-mit-l10-p080-i001 data-source-page="80" data-source-order="1"}
- Let $C_1,\ldots,C_m$ be nonempty closed convex subsets of $\mathbb R^n$ such that the equality $d_1+\cdots+d_m=0$ for some vectors $d_i\in R_{C_i}$ implies that $d_i=0$ for all $i=1,\ldots,m$. Then $C_1+\cdots+C_m$ is a closed set.
:::

::: {.source-item #d90-mit-l10-p080-i002 data-source-page="80" data-source-order="2"}
- **Special Case:** If $C_1$ and $-C_2$ are closed convex sets, then $C_1-C_2$ is closed if $R_{C_1}\cap R_{C_2}=\{0\}$.
:::

::: {.source-item #d90-mit-l10-p080-i003 data-source-page="80" data-source-order="3"}
**Proof:** The Cartesian product

::: {.source-display #d90-mit-l10-p080-d001 data-source-page="80" data-display-order="1"}
$$
C=C_1\times\cdots\times C_m
$$
:::

is closed convex, and its recession cone is

::: {.source-display #d90-mit-l10-p080-d002 data-source-page="80" data-display-order="2"}
$$
R_C=R_{C_1}\times\cdots\times R_{C_m}.
$$
:::

Let $A$ be defined by

::: {.source-display #d90-mit-l10-p080-d003 data-source-page="80" data-display-order="3"}
$$
A(x_1,\ldots,x_m)=x_1+\cdots+x_m.
$$
:::

Then

::: {.source-display #d90-mit-l10-p080-d004 data-source-page="80" data-display-order="4"}
$$
AC=C_1+\cdots+C_m,
$$
:::

and

::: {.source-display #d90-mit-l10-p080-d005 data-source-page="80" data-display-order="5"}
$$
N(A)=\bigl\{(d_1,\ldots,d_m)\mid d_1+\cdots+d_m=0\bigr\},
$$
:::

::: {.source-display #d90-mit-l10-p080-d006 data-source-page="80" data-display-order="6"}
$$
R_C\cap N(A)
=\bigl\{(d_1,\ldots,d_m)\mid d_1+\cdots+d_m=0,
\ d_i\in R_{C_i},\ \forall i\bigr\}.
$$
:::

By the given condition, $R_C\cap N(A)=\{0\}$, so $AC$ is closed. **Q.E.D.**
:::

*[Source page 80.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l10-p081-n001 data-source-page="81" data-correction-event="O015-MIT-SEM-0028"}
**Printed wording preserved.** The source omits the article in “where $a$ is nonzero vector” and omits “to” in “is said be supporting.” The witness retains both printed omissions; the Indonesian derivative supplies the grammatically required relations without changing the mathematics.
:::

::: {.source-page #d90-mit-l10-p081 data-source-page="81" data-source-order="18"}
## Hyperplanes

::: {.source-figure #d90-mit-l10-p081-f001 data-source-page="81" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** A slanted line through $\bar{x}$ is perpendicular to the arrow $a$. The line is labeled both $\{x\mid a'x=b\}$ and $\{x\mid a'x=a'\bar{x}\}$. The band on the side toward which $a$ points is the positive halfspace $\{x\mid a'x\geq b\}$; the band on the opposite side is the negative halfspace $\{x\mid a'x\leq b\}$. The drawing relates the normal vector, the boundary hyperplane, and its two closed halfspaces.
:::

::: {.source-item #d90-mit-l10-p081-i001 data-source-page="81" data-source-order="1"}
- A hyperplane is a set of the form $\{x\mid a'x=b\}$, where $a$ is nonzero vector in $\mathbb R^n$ and $b$ is a scalar.
:::

::: {.source-item #d90-mit-l10-p081-i002 data-source-page="81" data-source-order="2"}
- We say that two sets $C_1$ and $C_2$ are separated by a hyperplane $H=\{x\mid a'x=b\}$ if each lies in a different closed halfspace associated with $H$, i.e.,

  either

  ::: {.source-display #d90-mit-l10-p081-d001 data-source-page="81" data-display-order="1"}
  $$
  a'x_1\leq b\leq a'x_2,
  \qquad \forall x_1\in C_1,\quad \forall x_2\in C_2,
  $$
  :::

  or

  ::: {.source-display #d90-mit-l10-p081-d002 data-source-page="81" data-display-order="2"}
  $$
  a'x_2\leq b\leq a'x_1,
  \qquad \forall x_1\in C_1,\quad \forall x_2\in C_2.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p081-i003 data-source-page="81" data-source-order="3"}
- If $\bar{x}$ belongs to the closure of a set $C$, a hyperplane that separates $C$ and the singleton set $\{\bar{x}\}$ is said be supporting $C$ at $\bar{x}$.
:::

*[Source page 81.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p082 data-source-page="82" data-source-order="19"}
## Visualization

::: {.source-item #d90-mit-l10-p082-i001 data-source-page="82" data-source-order="1"}
- Separating and supporting hyperplanes:
:::

::: {.source-figure #d90-mit-l10-p082-f001 data-source-page="82" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the first omitted source figure.** Panel (a) places two disjoint convex regions $C_1$ and $C_2$ on opposite sides of an oblique line; the short arrow $a$ is normal to that line. Panel (b) shows a convex region $C$ touched at $\bar{x}$ by a line whose normal is again $a$. The panels contrast a separating hyperplane between two sets with a supporting hyperplane at a boundary point of one set.
:::

::: {.source-item #d90-mit-l10-p082-i002 data-source-page="82" data-source-order="2"}
- A separating $\{x\mid a'x=b\}$ that is disjoint from $C_1$ and $C_2$ is called strictly separating:

  ::: {.source-display #d90-mit-l10-p082-d001 data-source-page="82" data-display-order="1"}
  $$
  a'x_1<b<a'x_2,
  \qquad \forall x_1\in C_1,\quad \forall x_2\in C_2.
  $$
  :::
:::

::: {.source-figure #d90-mit-l10-p082-f002 data-source-page="82" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the second omitted source figure.** Panel (a) juxtaposes a set $C_1$ bounded by a vertical line and an unbounded curved set $C_2$. Panel (b) places curved $C_1$ and compact oval $C_2$ apart. Marked points $\bar{x}_1\in C_1$ and $\bar{x}_2\in C_2$ are joined by a segment through $\bar{x}$, while a line through $\bar{x}$ is perpendicular to the indicated normal $a$. The right panel makes the strict gap and the separator's orientation explicit.
:::

*[Source page 82.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p083 data-source-page="83" data-source-order="20"}
## Supporting hyperplane theorem

::: {.source-item #d90-mit-l10-p083-i001 data-source-page="83" data-source-order="1"}
- Let $C$ be convex and let $\bar{x}$ be a vector that is not an interior point of $C$. Then, there exists a hyperplane that passes through $\bar{x}$ and contains $C$ in one of its closed halfspaces.
:::

::: {.source-figure #d90-mit-l10-p083-f001 data-source-page="83" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** Outside a convex region $C$, points $x_0,x_1,x_2,x_3$ approach the boundary point $\bar{x}$. Each $x_k$ is joined to its nearest point $\hat{x}_k$ on $\operatorname{cl}(C)$, and the unit arrow $a_k$ runs from $x_k$ toward $\hat{x}_k$. The nearest points also converge to $\bar{x}$. A limiting line through $\bar{x}$, with normal $a$, leaves the whole region $C$ on one closed side.
:::

::: {.source-item #d90-mit-l10-p083-i002 data-source-page="83" data-source-order="2"}
**Proof:** Take a sequence $\{x_k\}$ that does not belong to $\operatorname{cl}(C)$ and converges to $\bar{x}$. Let $\hat{x}_k$ be the projection of $x_k$ on $\operatorname{cl}(C)$. We have for all $x\in\operatorname{cl}(C)$

::: {.source-display #d90-mit-l10-p083-d001 data-source-page="83" data-display-order="1"}
$$
a_k'x\geq a_k'x_k,
\qquad \forall x\in\operatorname{cl}(C),
\quad \forall k=0,1,\ldots,
$$
:::

where

::: {.source-display #d90-mit-l10-p083-d002 data-source-page="83" data-display-order="2"}
$$
a_k=\frac{\hat{x}_k-x_k}{\lVert\hat{x}_k-x_k\rVert}.
$$
:::

Let $a$ be a limit point of $\{a_k\}$, and take limit as $k\to\infty$. **Q.E.D.**
:::

*[Source page 83.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l10-p084-n001 data-source-page="84" data-correction-event="O015-MIT-SEM-0029"}
**Printed set label preserved.** The proof prints
$C_1-C_2=\{x_2-x_1\mid x_1\in C_1,x_2\in C_2\}$. The set on the right is $C_2-C_1$, not $C_1-C_2$ under the standard difference convention used again on source page 85. With the printed inequality $0\leq a'x$, the right-hand set yields the theorem's desired order $a'x_1\leq a'x_2$; therefore the determined defect is the left-hand set label. The witness retains the printed mismatch, while the Indonesian derivative relabels the set as $C_2-C_1$.
:::

::: {.source-page #d90-mit-l10-p084 data-source-page="84" data-source-order="21"}
## Separating hyperplane theorem

::: {.source-item #d90-mit-l10-p084-i001 data-source-page="84" data-source-order="1"}
- Let $C_1$ and $C_2$ be two nonempty convex subsets of $\mathbb R^n$. If $C_1$ and $C_2$ are disjoint, there exists a hyperplane that separates them, i.e., there exists a vector $a\neq0$ such that

  ::: {.source-display #d90-mit-l10-p084-d001 data-source-page="84" data-display-order="1"}
  $$
  a'x_1\leq a'x_2,
  \qquad \forall x_1\in C_1,\quad \forall x_2\in C_2.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p084-i002 data-source-page="84" data-source-order="2"}
**Proof:** Consider the convex set

::: {.source-display #d90-mit-l10-p084-d002 data-source-page="84" data-display-order="2"}
$$
C_1-C_2=\{x_2-x_1\mid x_1\in C_1,\ x_2\in C_2\}.
$$
:::

Since $C_1$ and $C_2$ are disjoint, the origin does not belong to $C_1-C_2$, so by the Supporting Hyperplane Theorem, there exists a vector $a\neq0$ such that

::: {.source-display #d90-mit-l10-p084-d003 data-source-page="84" data-display-order="3"}
$$
0\leq a'x,
\qquad \forall x\in C_1-C_2,
$$
:::

which is equivalent to the desired relation. **Q.E.D.**
:::

*[Source page 84.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p085 data-source-page="85" data-source-order="22"}
## Strict separation theorem

::: {.source-item #d90-mit-l10-p085-i001 data-source-page="85" data-source-order="1"}
- **Strict Separation Theorem:** Let $C_1$ and $C_2$ be two disjoint nonempty convex sets. If $C_1$ is closed, and $C_2$ is compact, there exists a hyperplane that strictly separates them.
:::

::: {.source-figure #d90-mit-l10-p085-f001 data-source-page="85" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** Panel (a) shows two separated sets: $C_1$ beside a vertical boundary and $C_2$ with a curved unbounded boundary. Panel (b) shows curved $C_1$ and oval $C_2$ with nearest points $\bar{x}_1$ and $\bar{x}_2$. Their connecting segment passes through $\bar{x}$ and crosses a candidate separating line orthogonally; the arrow $a$ points normal to that line. The construction in the proof refers specifically to the nearest-point geometry of panel (b).
:::

::: {.source-item #d90-mit-l10-p085-i002 data-source-page="85" data-source-order="2"}
**Proof:** (Outline) Consider the set $C_1-C_2$. Since $C_1$ is closed and $C_2$ is compact, $C_1-C_2$ is closed. Since

::: {.source-display #d90-mit-l10-p085-d001 data-source-page="85" data-display-order="1"}
$$
C_1\cap C_2=\varnothing,
\qquad 0\notin C_1-C_2,
$$
:::

let $\bar{x}_1-\bar{x}_2$ be the projection of $0$ onto $C_1-C_2$. The strictly separating hyperplane is constructed as in (b).
:::

::: {.source-item #d90-mit-l10-p085-i003 data-source-page="85" data-source-order="3"}
- **Note:** Any conditions that guarantee closedness of $C_1-C_2$ guarantee existence of a strictly separating hyperplane. However, there may exist a strictly separating hyperplane without $C_1-C_2$ being closed.
:::

*[Source page 85.]{.source-locator}*
:::
