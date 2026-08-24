---
title: "MIT 6.253 Lecture 7 semantic transcription witness"
subtitle: "Complete-notes PDF pages 86-97"
author: "Dimitri P. Bertsekas (source author)"
lang: en
date: "2026-08-24"
rights: "CC BY-NC-SA 4.0"
---

This project-made semantic witness transcribes the complete Lecture 7 sequence from pages 86-97 of Dimitri P. Bertsekas's *Convex Analysis and Optimization: Complete Lecture Notes* for MIT OpenCourseWare 6.253. Page 98 begins Lecture 8 and is the excluded delimiter. This witness is not an official editable source. Its lineation, stable identifiers, source-page fences, accessibility prose, and defect notices are project additions.

The source PDF is selectable and tagged, but the selected boundary has no annotations, widgets, media, links, code cells, or interactive exercise surfaces. Permission-restricted source figure pixels and layouts are omitted. Seven figure blocks containing sixteen separately meaningful panels are represented by independently worded semantic descriptions. Mathematical notation was checked visually against rendered source pages because text extraction corrupts blackboard-bold real-number symbols, membership and intersection signs, infinity and empty-set signs, inequalities, transpose marks, and mapsto arrows.

This transcription was produced with **OpenAI Codex gpt-5.6-sol, Ultra**, at the repository user's direction. It has not received human review and implies no endorsement by the source author, MIT, or MIT OpenCourseWare.

::: {.source-page #d90-mit-l11-p086 data-source-page="86" data-source-order="1"}
## Lecture 7 - Lecture outline

::: {.source-item #d90-mit-l11-p086-i001 data-source-page="86" data-source-order="1"}
- Review of hyperplane separation
:::

::: {.source-item #d90-mit-l11-p086-i002 data-source-page="86" data-source-order="2"}
- Nonvertical hyperplanes
:::

::: {.source-item #d90-mit-l11-p086-i003 data-source-page="86" data-source-order="3"}
- Convex conjugate functions
:::

::: {.source-item #d90-mit-l11-p086-i004 data-source-page="86" data-source-order="4"}
- Conjugacy theorem
:::

::: {.source-item #d90-mit-l11-p086-i005 data-source-page="86" data-source-order="5"}
- Examples
:::

::: {.source-item #d90-mit-l11-p086-i006 data-source-page="86" data-source-order="6"}
**Reading:** Sections 1.5 and 1.6.
:::

*[Source page 86.]{.source-locator}*
:::

::: {.source-page #d90-mit-l11-p087 data-source-page="87" data-source-order="2"}
## Additional theorems

::: {.source-item #d90-mit-l11-p087-i001 data-source-page="87" data-source-order="1"}
- **Fundamental characterization:** The closure of the convex hull of a set
  $C\subset\mathbb R^n$ is the intersection of the closed halfspaces that
  contain $C$. (The proof uses the strict separation theorem.)
:::

::: {.source-item #d90-mit-l11-p087-i002 data-source-page="87" data-source-order="2"}
- A hyperplane *properly separates* $C_1$ and $C_2$ if it separates $C_1$ and
  $C_2$ and does not fully contain both $C_1$ and $C_2$.
:::

::: {.source-figure #d90-mit-l11-p087-f001 data-source-page="87" data-figure-disposition="omitted-source-graphic" data-panel-count="3"}
**Semantic description of the omitted source figure.** Three panels contrast
proper separation geometries. Panel (a) shows two convex sets meeting the
separating line in different portions while the line does not contain both
sets. Panel (b) shows two thin convex sets lying on opposite sides of an
oblique separator and touching it at different locations. Panel (c) places
both thin sets along a common slanted line, illustrating the excluded case in
which the hyperplane fully contains both. Each panel marks a normal vector
$a$.
:::

::: {.source-item #d90-mit-l11-p087-i003 data-source-page="87" data-source-order="3"}
- **Proper separation theorem:** Let $C_1$ and $C_2$ be two nonempty convex
  subsets of $\mathbb R^n$. A hyperplane properly separates $C_1$ and $C_2$
  if and only if

::: {.source-display #d90-mit-l11-p087-d001 data-source-page="87" data-display-order="1"}
$$
\operatorname{ri}(C_1)\cap\operatorname{ri}(C_2)=\varnothing.
$$
:::
:::

*[Source page 87.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p088-n001 data-source-page="88" data-defect-class="unwarranted-nonpolyhedral-description" data-correction-event="O015-MIT-SEM-0034"}
**Printed overstatement preserved.** The theorem does not assume that $C$ is
nonpolyhedral, although the source calls it “the nonpolyhedral set $C$.” The
Indonesian derivative uses the theorem's actual scope: $C$ need not be
polyhedral.
:::

::: {.source-page #d90-mit-l11-p088 data-source-page="88" data-source-order="3"}
## Proper polyhedral separation

::: {.source-item #d90-mit-l11-p088-i001 data-source-page="88" data-source-order="1"}
- Recall that two convex sets $C$ and $P$ such that

::: {.source-display #d90-mit-l11-p088-d001 data-source-page="88" data-display-order="1"}
$$
\operatorname{ri}(C)\cap\operatorname{ri}(P)=\varnothing
$$
:::

  can be properly separated, that is, by a hyperplane that does not contain
  both $C$ and $P$.
:::

::: {.source-item #d90-mit-l11-p088-i002 data-source-page="88" data-source-order="2"}
- If $P$ is polyhedral and the slightly stronger condition

::: {.source-display #d90-mit-l11-p088-d002 data-source-page="88" data-display-order="2"}
$$
\operatorname{ri}(C)\cap P=\varnothing
$$
:::

  holds, then the properly separating hyperplane can be chosen so that it does
  not contain the nonpolyhedral set $C$, while it may contain $P$.
:::

::: {.source-figure #d90-mit-l11-p088-f001 data-source-page="88" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Semantic description of the omitted source figure.** Panel (a) shows a
polyhedral set $P$ meeting a thin convex set $C$ at the separating line. A
second oblique separator with normal $a$ can be rotated so that it does not
contain $C$. Panel (b) replaces $P$ by a smooth oval tangent to the thin set
$C$; the only displayed separator is their common tangent and therefore
contains $C$. The contrast isolates the role of polyhedrality.
:::

::: {.source-item #d90-mit-l11-p088-i003 data-source-page="88" data-source-order="3"}
On the left, the separating hyperplane can be chosen so that it does not
contain $C$. On the right, where $P$ is not polyhedral, this is not possible.
:::

*[Source page 88.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p089-n001 data-source-page="89" data-defect-class="ambiguous-vertical-line-phrase" data-correction-event="O015-MIT-SEM-0035"}
**Printed shorthand preserved.** Every epigraph contains upward vertical rays,
so the bare phrase “vertical line” can be misread. The theorem needs absence
of a full two-sided vertical line; the Indonesian derivative says this
explicitly.
:::

::: {.source-page #d90-mit-l11-p089 data-source-page="89" data-source-order="4"}
## Nonvertical hyperplanes

::: {.source-item #d90-mit-l11-p089-i001 data-source-page="89" data-source-order="1"}
A hyperplane in $\mathbb R^{n+1}$ with normal $(\mu,\beta)$ is nonvertical if
$\beta\neq0$.
:::

::: {.source-item #d90-mit-l11-p089-i002 data-source-page="89" data-source-order="2"}
- It intersects the $(n+1)$st axis at
  $\xi=(\mu/\beta)'\bar u+\bar w$, where $(\bar u,\bar w)$ is any vector on
  the hyperplane.
:::

::: {.source-figure #d90-mit-l11-p089-f001 data-source-page="89" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Semantic description of the omitted source figure.** The common $(u,w)$
axes contain two visually separate constructions. On the left, an oblique
nonvertical hyperplane passes through $(\bar u,\bar w)$ and crosses the
vertical axis at $(\mu/\beta)'\bar u+\bar w$; its normal is
$(\mu,\beta)$. On the right, a vertical hyperplane is drawn at fixed $u$ with
normal $(\mu,0)$. The comparison makes the difference between the two types
explicit.
:::

::: {.source-item #d90-mit-l11-p089-i003 data-source-page="89" data-source-order="3"}
- A nonvertical hyperplane that contains the epigraph of a function in its
  "upper" halfspace provides lower bounds on the function values.
:::

::: {.source-item #d90-mit-l11-p089-i004 data-source-page="89" data-source-order="4"}
- The epigraph of a proper convex function does not contain a vertical line,
  so it appears plausible that it is contained in the "upper" halfspace of
  some nonvertical hyperplane.
:::

*[Source page 89.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p090-n001 data-source-page="90" data-defect-class="suppressed-epsilon-sign-and-margin-argument" data-correction-event="O015-MIT-SEM-0036"}
**Printed proof shorthand preserved.** Part (b) says only to “add” a small
$\epsilon$-multiple of a nonvertical hyperplane. The Indonesian derivative
states the orientations, preserved sign on $C$, and sufficiently small
positive margin needed to justify that perturbation.
:::

::: {.source-page #d90-mit-l11-p090 data-source-page="90" data-source-order="5"}
## Nonvertical hyperplane theorem

::: {.source-item #d90-mit-l11-p090-i001 data-source-page="90" data-source-order="1"}
- Let $C$ be a nonempty convex subset of $\mathbb R^{n+1}$ that contains no
  vertical lines. Then:

  (a) $C$ is contained in a closed halfspace of a nonvertical hyperplane. In
  other words, there exist $\mu\in\mathbb R^n$, $\beta\in\mathbb R$ with
  $\beta\neq0$, and $\gamma\in\mathbb R$ such that

::: {.source-display #d90-mit-l11-p090-d001 data-source-page="90" data-display-order="1"}
$$
\mu'u+\beta w\geq\gamma
\qquad\text{for all }(u,w)\in C.
$$
:::

  (b) If $(\bar u,\bar w)\notin\operatorname{cl}(C)$, there exists a
  nonvertical hyperplane strictly separating $(\bar u,\bar w)$ and $C$.
:::

::: {.source-item #d90-mit-l11-p090-i002 data-source-page="90" data-source-order="2"}
**Proof:** Note that $\operatorname{cl}(C)$ contains no vertical line. Indeed,
$C$ contains no vertical line, $\operatorname{ri}(C)$ contains no vertical
line, and $\operatorname{ri}(C)$ and $\operatorname{cl}(C)$ have the same
recession cone. Thus it is enough to consider the case in which $C$ is closed.
:::

::: {.source-item #d90-mit-l11-p090-i003 data-source-page="90" data-source-order="3"}
**(a)** The set $C$ is the intersection of the closed halfspaces containing
$C$. If all of these corresponded to vertical hyperplanes, $C$ would contain
a vertical line.
:::

::: {.source-item #d90-mit-l11-p090-i004 data-source-page="90" data-source-order="4"}
**(b)** There is a hyperplane strictly separating $(\bar u,\bar w)$ and $C$.
If it is nonvertical, the result follows. Otherwise, "add" to this vertical
hyperplane a sufficiently small $\epsilon$-multiple of a nonvertical
hyperplane that contains $C$ in one of its halfspaces, as supplied by part
(a).
:::

*[Source page 90.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p091-n001 data-source-page="91" data-defect-class="supporting-without-attainment" data-correction-event="O015-MIT-SEM-0037"}
**Printed attainment assumption gap preserved.** A nonvertical affine lower
bound need not touch $\operatorname{epi}(f)$ when the supremum defining
$f^*(y)$ is not attained. The Indonesian derivative calls these
lower-bounding hyperplanes and calls one supporting only when the supremum is
attained.
:::

::: {.source-defect-notice #d90-mit-l11-p091-n002 data-source-pages="91,95" data-defect-class="function-type-mapsto-arrow" data-correction-event="O015-MIT-SEM-0040"}
**Printed notation preserved.** The source uses $\mapsto$ between a function's
domain and codomain on pages 91 and 95. The Indonesian derivative uses the
type arrow $\to$; $\mapsto$ is reserved for an element-to-value mapping.
:::

::: {.source-page #d90-mit-l11-p091 data-source-page="91" data-source-order="6"}
## Conjugate convex functions

::: {.source-item #d90-mit-l11-p091-i001 data-source-page="91" data-source-order="1"}
Consider a function $f$ and its epigraph. Nonvertical hyperplanes supporting
$\operatorname{epi}(f)$ correspond to crossing points of the vertical axis:

::: {.source-display #d90-mit-l11-p091-d001 data-source-page="91" data-display-order="1"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n.
$$
:::
:::

::: {.source-figure #d90-mit-l11-p091-f001 data-source-page="91" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Semantic description of the omitted source figure.** A curved graph of
$f(x)$ is supported from below by a line of slope $y$ and normal $(-y,1)$.
The line's crossing point on the vertical axis is labeled
$\inf_{x\in\mathbb R^n}\{f(x)-x'y\}=-f^*(y)$. The tangent geometry links the
slope parameter $y$ with the value of the convex conjugate.
:::

::: {.source-item #d90-mit-l11-p091-i002 data-source-page="91" data-source-order="2"}
- For any $f:\mathbb R^n\mapsto[-\infty,\infty]$, its conjugate convex
  function is defined by

::: {.source-display #d90-mit-l11-p091-d002 data-source-page="91" data-display-order="2"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n.
$$
:::
:::

*[Source page 91.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p092-n001 data-source-page="92" data-defect-class="missing-positive-parameter-assumption" data-correction-event="O015-MIT-SEM-0031"}
**Printed assumption gap preserved.** The quadratic example prints
$f(x)=(c/2)x^2$ and $f^*(y)=(1/2c)y^2$ without stating $c>0$. Positivity is
needed for the displayed function to be proper convex and for the stated
finite conjugate formula to hold. The Indonesian derivative states it.
:::

::: {.source-page #d90-mit-l11-p092 data-source-page="92" data-source-order="7"}
## Examples

::: {.source-item #d90-mit-l11-p092-i001 data-source-page="92" data-source-order="1"}
The examples use the definition

::: {.source-display #d90-mit-l11-p092-d001 data-source-page="92" data-display-order="1"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n.
$$
:::
:::

::: {.source-figure #d90-mit-l11-p092-f001 data-source-page="92" data-figure-disposition="omitted-source-graphic" data-panel-count="6"}
**Semantic description of the omitted source figure.** Three input/conjugate
pairs are arranged as six panels. The first pair takes
$f(x)=\alpha x-\beta$ and gives $f^*(y)=\beta$ at $y=\alpha$ and $+\infty$
elsewhere. The second takes $f(x)=|x|$ and gives $f^*(y)=0$ for $|y|\leq1$
and $+\infty$ for $|y|>1$. The third takes $f(x)=(c/2)x^2$ and gives
$f^*(y)=(1/2c)y^2$. The graphs pair a line with a single finite conjugate
point, an absolute-value V with the indicator of $[-1,1]$, and two quadratic
parabolas of reciprocal curvature.
:::

*[Source page 92.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p093-n001 data-source-page="93" data-defect-class="affine-functions-called-linear" data-correction-event="O015-MIT-SEM-0038"}
**Printed terminology defect preserved.** For fixed $x$, the map
$y\mapsto x'y-f(x)$ is affine and is linear only when $f(x)=0$. The
Indonesian derivative uses “affine functions.”
:::

::: {.source-page #d90-mit-l11-p093 data-source-page="93" data-source-order="8"}
## Conjugate of conjugate

::: {.source-item #d90-mit-l11-p093-i001 data-source-page="93" data-source-order="1"}
- From the definition

::: {.source-display #d90-mit-l11-p093-d001 data-source-page="93" data-display-order="1"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n,
$$
:::

  note that $f^*$ is convex and closed.
:::

::: {.source-item #d90-mit-l11-p093-i002 data-source-page="93" data-source-order="2"}
- **Reason:** $\operatorname{epi}(f^*)$ is the intersection of the epigraphs
  of the linear functions of $y$

::: {.source-display #d90-mit-l11-p093-d002 data-source-page="93" data-display-order="2"}
$$
x'y-f(x)
$$
:::

  as $x$ ranges over $\mathbb R^n$.
:::

::: {.source-item #d90-mit-l11-p093-i003 data-source-page="93" data-source-order="3"}
- Consider the conjugate of the conjugate:

::: {.source-display #d90-mit-l11-p093-d003 data-source-page="93" data-display-order="3"}
$$
f^{**}(x)=\sup_{y\in\mathbb R^n}\{y'x-f^*(y)\},
\qquad x\in\mathbb R^n.
$$
:::
:::

::: {.source-item #d90-mit-l11-p093-i004 data-source-page="93" data-source-order="4"}
- The function $f^{**}$ is convex and closed.
:::

::: {.source-item #d90-mit-l11-p093-i005 data-source-page="93" data-source-order="5"}
- **Important fact / conjugacy theorem:** If $f$ is closed, proper, and
  convex, then $f^{**}=f$.
:::

*[Source page 93.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p094-n001 data-source-page="94" data-defect-class="visual-general-case-ambiguity" data-correction-event="O015-MIT-SEM-0039"}
**Printed visualization ambiguity preserved.** The pictured graph is visibly
nonconvex while the preceding equality statement assumes a closed proper
convex function. The Indonesian derivative identifies the general envelope
$f^{**}\leq f$ and states that equality is the special case under the
theorem's hypotheses.
:::

::: {.source-page #d90-mit-l11-p094 data-source-page="94" data-source-order="9"}
## Conjugacy theorem - visualization

::: {.source-item #d90-mit-l11-p094-i001 data-source-page="94" data-source-order="1"}
The visualization repeats

::: {.source-display #d90-mit-l11-p094-d001 data-source-page="94" data-display-order="1"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n,
$$
:::

and

::: {.source-display #d90-mit-l11-p094-d002 data-source-page="94" data-display-order="2"}
$$
f^{**}(x)=\sup_{y\in\mathbb R^n}\{y'x-f^*(y)\},
\qquad x\in\mathbb R^n.
$$
:::

- If $f$ is closed, convex, and proper, then $f^{**}=f$.
:::

::: {.source-figure #d90-mit-l11-p094-f001 data-source-page="94" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Semantic description of the omitted source figure.** A possibly nonconvex
graph of $f$ is compared with the lower envelope reconstructed by its
biconjugate. A line of slope $y$ and normal $(-y,1)$ supports the graph; its
vertical crossing point is $-f^*(y)$. At a fixed horizontal coordinate $x$,
the supremum of $y'x-f^*(y)$ is marked on the reconstructed curve. The source
labels the supporting hyperplane
$H=\{(x,w)\mid w-x'y=-f^*(y)\}$ and connects its intercepts to the two
conjugacy formulas.
:::

*[Source page 94.]{.source-locator}*
:::

::: {.source-page #d90-mit-l11-p095 data-source-page="95" data-source-order="10"}
## Conjugacy theorem

::: {.source-item #d90-mit-l11-p095-i001 data-source-page="95" data-source-order="1"}
- Let $f:\mathbb R^n\mapsto(-\infty,\infty]$ be a function, let
  $\check{\operatorname{cl}}f$ be its convex closure, let $f^*$ be its convex
  conjugate, and consider the conjugate of $f^*$,

::: {.source-display #d90-mit-l11-p095-d001 data-source-page="95" data-display-order="1"}
$$
f^{**}(x)=\sup_{y\in\mathbb R^n}\{y'x-f^*(y)\},
\qquad x\in\mathbb R^n.
$$
:::

  (a) We have

::: {.source-display #d90-mit-l11-p095-d002 data-source-page="95" data-display-order="2"}
$$
f(x)\geq f^{**}(x),
\qquad\forall x\in\mathbb R^n.
$$
:::

  (b) If $f$ is convex, then properness of any one of $f$, $f^*$, and
  $f^{**}$ implies properness of the other two.

  (c) If $f$ is closed, proper, and convex, then

::: {.source-display #d90-mit-l11-p095-d003 data-source-page="95" data-display-order="3"}
$$
f(x)=f^{**}(x),
\qquad\forall x\in\mathbb R^n.
$$
:::

  (d) If $\check{\operatorname{cl}}f(x)>-\infty$ for all
  $x\in\mathbb R^n$, then

::: {.source-display #d90-mit-l11-p095-d004 data-source-page="95" data-display-order="4"}
$$
\check{\operatorname{cl}}f(x)=f^{**}(x),
\qquad\forall x\in\mathbb R^n.
$$
:::
:::

*[Source page 95.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p096-n001 data-source-page="96" data-defect-class="sign-defective-geometric-proof" data-correction-event="O015-MIT-SEM-0032"}
**Printed proof defect preserved.** The source's vertical-axis labels
$x'y-f(x)$ and $x'y-f^{**}(x)$ have the opposite sign from the actual
intercepts of hyperplanes with normal $(y,-1)$, and the final line omits the
contradiction connective. The Indonesian derivative replaces this defective
geometric conclusion with a direct inequality argument from the same strict
separator.
:::

::: {.source-page #d90-mit-l11-p096 data-source-page="96" data-source-order="11"}
## Proof of conjugacy theorem (a), (c)

::: {.source-item #d90-mit-l11-p096-i001 data-source-page="96" data-source-order="1"}
- **(a)** For all $x,y$, we have $f^*(y)\geq y'x-f(x)$, implying that
  $f(x)\geq\sup_y\{y'x-f^*(y)\}=f^{**}(x)$.
:::

::: {.source-item #d90-mit-l11-p096-i002 data-source-page="96" data-source-order="2"}
- **(c)** By contradiction, assume there is
  $(x,\gamma)\in\operatorname{epi}(f^{**})$ with
  $(x,\gamma)\notin\operatorname{epi}(f)$. There exists a nonvertical
  hyperplane with normal $(y,-1)$ that strictly separates $(x,\gamma)$ and
  $\operatorname{epi}(f)$. (The vertical component of the normal vector is
  normalized to $-1$.)
:::

::: {.source-figure #d90-mit-l11-p096-f001 data-source-page="96" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Semantic description of the omitted source figure.** The epigraph of $f$
lies above the epigraph of $f^{**}$. At the same horizontal coordinate $x$,
the points $(x,f(x))$, $(x,\gamma)$, and $(x,f^{**}(x))$ are aligned
vertically. A hyperplane with normal $(y,-1)$ separates the middle point from
$\operatorname{epi}(f)$, while two parallel translates pass through the upper
and lower graph points. Their vertical intercepts are labeled
$x'y-f(x)$ and $x'y-f^{**}(x)$.
:::

::: {.source-item #d90-mit-l11-p096-i003 data-source-page="96" data-source-order="3"}
- Consider two parallel hyperplanes translated to pass through $(x,f(x))$ and
  $(x,f^{**}(x))$. Their vertical crossing points are $x'y-f(x)$ and
  $x'y-f^{**}(x)$ and lie strictly above and below the crossing point of the
  strictly separating hyperplane. Hence

::: {.source-display #d90-mit-l11-p096-d001 data-source-page="96" data-display-order="1"}
$$
x'y-f(x)>x'y-f^{**}(x),
$$
:::

  the fact $f\geq f^{**}$. Q.E.D.
:::

*[Source page 96.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l11-p097-n001 data-source-page="97" data-defect-class="scalar-vector-domain-mismatch" data-correction-event="O015-MIT-SEM-0033"}
**Printed dimension and codomain mismatch preserved.** The counterexample
compares $x$ with $0$ and is therefore scalar, but its two universal
quantifiers print $\mathbb R^n$. It also permits $-\infty$, unlike the
codomain displayed on page 95. The Indonesian derivative consistently states
the example as $f:\mathbb R\to[-\infty,+\infty]$ and quantifies over
$\mathbb R$.
:::

::: {.source-page #d90-mit-l11-p097 data-source-page="97" data-source-order="12"}
## A counterexample

::: {.source-item #d90-mit-l11-p097-i001 data-source-page="97" data-source-order="1"}
A counterexample with closed convex but improper $f$ shows the need to assume
properness in order to obtain $f=f^{**}$:

::: {.source-display #d90-mit-l11-p097-d001 data-source-page="97" data-display-order="1"}
$$
f(x)=
\begin{cases}
+\infty,&x>0,\\
-\infty,&x\leq0.
\end{cases}
$$
:::
:::

::: {.source-item #d90-mit-l11-p097-i002 data-source-page="97" data-source-order="2"}
We have

::: {.source-display #d90-mit-l11-p097-d002 data-source-page="97" data-display-order="2"}
$$
f^*(y)=+\infty,
\qquad\forall y\in\mathbb R^n,
$$
:::

and

::: {.source-display #d90-mit-l11-p097-d003 data-source-page="97" data-display-order="3"}
$$
f^{**}(x)=-\infty,
\qquad\forall x\in\mathbb R^n.
$$
:::
:::

::: {.source-item #d90-mit-l11-p097-i003 data-source-page="97" data-source-order="3"}
But

::: {.source-display #d90-mit-l11-p097-d004 data-source-page="97" data-display-order="4"}
$$
\check{\operatorname{cl}}f=f,
\qquad\text{so}\qquad
\check{\operatorname{cl}}f\neq f^{**}.
$$
:::
:::

*[Source page 97.]{.source-locator}*
:::
