---
title: "MIT 6.253 Lecture 5 semantic transcription witness"
subtitle: "Complete-notes PDF pages 50-63"
author: "Dimitri P. Bertsekas (source author)"
lang: en
date: "2026-08-24"
rights: "CC BY-NC-SA 4.0"
---

This project-made semantic witness transcribes Lecture 5 from pages 50-63 of Dimitri P. Bertsekas's *Convex Analysis and Optimization: Complete Lecture Notes* for MIT OpenCourseWare 6.253. Page 64 begins Lecture 6 and is the excluded delimiter. This witness is not an official editable source. Its new lineation, stable identifiers, source-page fences, accessibility prose, and defect notices are project additions.

The source PDF contains selectable, tagged text but no page annotations, widgets, media, code cells, or other interactive exercise surfaces on this boundary. Permission-restricted source figure pixels and layout are omitted. Seven figure blocks containing twelve panels are represented instead by precise, independently worded semantic descriptions. Mathematical notation below was checked visually against the rendered source pages because text extraction corrupts several glyphs, including membership signs, real-number symbols, infinity signs, intersections, norms, and mapsto arrows.

This transcription was produced with **OpenAI Codex gpt-5.6-sol, Ultra**, at the repository user's direction. It has not received human review and implies no endorsement by the source author, MIT, or MIT OpenCourseWare.

::: {.source-defect-notice #d90-mit-l09-notice-mapsto data-source-pages="56,58,59,60,61,62,63" data-correction-event="O015-MIT-SEM-0012"}
**Printed notation preserved.** In the function declarations on source pages 56, 58, 59, 60, 61, 62, and 63, the source prints a mapsto arrow (`\mapsto`) between the domain and codomain. The witness retains that printed symbol rather than silently replacing it with a function-type arrow.
:::

::: {.source-page #d90-mit-l09-p050 data-source-page="50" data-source-order="1"}
## Lecture 5 - Lecture outline

::: {.source-item #d90-mit-l09-p050-i001 data-source-page="50" data-source-order="1"}
- Recession cones and lineality space
:::

::: {.source-item #d90-mit-l09-p050-i002 data-source-page="50" data-source-order="2"}
- Directions of recession of convex functions
:::

::: {.source-item #d90-mit-l09-p050-i003 data-source-page="50" data-source-order="3"}
- Local and global minima
:::

::: {.source-item #d90-mit-l09-p050-i004 data-source-page="50" data-source-order="4"}
- Existence of optimal solutions
:::

Reading: Sections 1.4, 3.1, 3.2.

*[Source page 50.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p051 data-source-page="51" data-source-order="2"}
## Recession cone of a convex set

::: {.source-item #d90-mit-l09-p051-i001 data-source-page="51" data-source-order="1"}
- Given a nonempty convex set $C$, a vector $d$ is a direction of recession if, starting at any $x$ in $C$ and going indefinitely along $d$, we never cross the relative boundary of $C$ to points outside $C$:

::: {.source-display #d90-mit-l09-p051-d001 data-source-page="51" data-display-order="1"}
$$
x+\alpha d\in C,\qquad \forall x\in C,\quad \forall\alpha\geq 0.
$$
:::
:::

::: {.source-figure #d90-mit-l09-p051-f001 data-source-page="51" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** An unbounded convex set $C$ is outlined around a point $x$. A ray begins at $x$ and runs in the direction $d$ to the labeled point $x+\alpha d$, remaining inside $C$. Beside the set, a shaded pointed cone with apex at the origin $0$ is labeled the recession cone $R_C$; the arrow $d$ lies inside that cone. The parallel ray and cone arrow convey that every nonnegative displacement along $d$ stays feasible from every point of $C$.
:::

::: {.source-item #d90-mit-l09-p051-i002 data-source-page="51" data-source-order="2"}
- Recession cone of $C$ (denoted by $R_C$): The set of all directions of recession.
:::

::: {.source-item #d90-mit-l09-p051-i003 data-source-page="51" data-source-order="3"}
- $R_C$ is a cone containing the origin.
:::

*[Source page 51.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p052 data-source-page="52" data-source-order="3"}
## Recession cone theorem

::: {.source-item #d90-mit-l09-p052-i001 data-source-page="52" data-source-order="1"}
- Let $C$ be a nonempty closed convex set.

  (a) The recession cone $R_C$ is a closed convex cone.

  (b) A vector $d$ belongs to $R_C$ if and only if there exists some vector $x\in C$ such that $x+\alpha d\in C$ for all $\alpha\geq 0$.

  (c) $R_C$ contains a nonzero direction if and only if $C$ is unbounded.

  (d) The recession cones of $C$ and $\operatorname{ri}(C)$ are equal.

  (e) If $D$ is another closed convex set such that $C\cap D\neq\varnothing$, we have

::: {.source-display #d90-mit-l09-p052-d001 data-source-page="52" data-display-order="1"}
$$
R_{C\cap D}=R_C\cap R_D.
$$
:::

  More generally, for any collection of closed convex sets $C_i$, $i\in I$, where $I$ is an arbitrary index set and $\bigcap_{i\in I}C_i$ is nonempty, we have

::: {.source-display #d90-mit-l09-p052-d002 data-source-page="52" data-display-order="2"}
$$
R_{\bigcap_{i\in I}C_i}=\bigcap_{i\in I}R_{C_i}.
$$
:::
:::

*[Source page 52.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p053 data-source-page="53" data-source-order="4"}
## Proof of part (b)

::: {.source-figure #d90-mit-l09-p053-f001 data-source-page="53" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** Inside the outlined convex set $C$, a ray from $x$ in direction $d$ carries the sequence $z_1=x+d,z_2,z_3,\ldots$. A second point $\bar{x}$ lies elsewhere in $C$. Points $\bar{x}+d_1$, $\bar{x}+d_2$, and $\bar{x}+d_3$ lie on a small circle centered at $\bar{x}$, and their directions converge around the circle toward the labeled limit $\bar{x}+d$. Line segments from $\bar{x}$ toward the distant $z_k$ illustrate how convexity puts each $\bar{x}+d_k$ in $C$ and closedness admits the limit.
:::

::: {.source-item #d90-mit-l09-p053-i001 data-source-page="53" data-source-order="1"}
- Let $d\neq 0$ be such that there exists a vector $x\in C$ with $x+\alpha d\in C$ for all $\alpha\geq 0$. We fix $\bar{x}\in C$ and $\alpha>0$, and we show that $\bar{x}+\alpha d\in C$. By scaling $d$, it is enough to show that $\bar{x}+d\in C$. For $k=1,2,\ldots$, let

::: {.source-display #d90-mit-l09-p053-d001 data-source-page="53" data-display-order="1"}
$$
z_k=x+kd,\qquad
d_k=\frac{z_k-\bar{x}}{\lVert z_k-\bar{x}\rVert}\lVert d\rVert.
$$
:::

  We have

::: {.source-display #d90-mit-l09-p053-d002 data-source-page="53" data-display-order="2"}
$$
\frac{d_k}{\lVert d\rVert}
=\frac{\lVert z_k-x\rVert}{\lVert z_k-\bar{x}\rVert}\frac{d}{\lVert d\rVert}
+\frac{x-\bar{x}}{\lVert z_k-\bar{x}\rVert},\qquad
\frac{\lVert z_k-x\rVert}{\lVert z_k-\bar{x}\rVert}\to 1,\qquad
\frac{x-\bar{x}}{\lVert z_k-\bar{x}\rVert}\to 0,
$$
:::

  so $d_k\to d$ and $\bar{x}+d_k\to\bar{x}+d$. Use the convexity and closedness of $C$ to conclude that $\bar{x}+d\in C$.
:::

*[Source page 53.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p054 data-source-page="54" data-source-order="5"}
## Lineality space

::: {.source-item #d90-mit-l09-p054-i001 data-source-page="54" data-source-order="1"}
- The lineality space of a convex set $C$, denoted by $L_C$, is the subspace of vectors $d$ such that $d\in R_C$ and $-d\in R_C$:

::: {.source-display #d90-mit-l09-p054-d001 data-source-page="54" data-display-order="1"}
$$
L_C=R_C\cap(-R_C).
$$
:::
:::

::: {.source-item #d90-mit-l09-p054-i002 data-source-page="54" data-source-order="2"}
- If $d\in L_C$, the entire line defined by $d$ is contained in $C$, starting at any point of $C$.
:::

::: {.source-item #d90-mit-l09-p054-i003 data-source-page="54" data-source-order="3"}
- Decomposition of a Convex Set: Let $C$ be a nonempty convex subset of $\mathbb R^n$. Then,

::: {.source-display #d90-mit-l09-p054-d002 data-source-page="54" data-display-order="2"}
$$
C=L_C+(C\cap L_C^\perp).
$$
:::
:::

::: {.source-item #d90-mit-l09-p054-i004 data-source-page="54" data-source-order="4"}
- Allows us to prove properties of $C$ on $C\cap L_C^\perp$ and extend them to $C$.
:::

::: {.source-item #d90-mit-l09-p054-i005 data-source-page="54" data-source-order="5"}
- True also if $L_C$ is replaced by a subspace $S\subset L_C$.
:::

::: {.source-figure #d90-mit-l09-p054-f001 data-source-page="54" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** A gray, strip-like convex set $C$ extends parallel to a subspace $S$. The line $S$ passes through the origin $0$ and contains the direction $d$; the perpendicular subspace $S^\perp$ also passes through $0$. A point $x$ in $C$ is projected parallel to $S$ onto a point $z$ in $C\cap S^\perp$. The labels and parallel directions depict the decomposition of every point into a component in $S$ and a component in the transverse slice.
:::

*[Source page 54.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l09-p055-n001 data-source-page="55" data-correction-event="O015-MIT-SEM-0013"}
**Printed wording preserved.** The second subitem on source page 55 says that $f$ is "monotonically nondecreasing" along the horizontal recession directions. This conflicts with the slide's stated aim of characterizing monotonic decrease and with the descent cases on source page 57. The witness retains "nondecreasing" exactly and does not silently repair it.
:::

::: {.source-page #d90-mit-l09-p055 data-source-page="55" data-source-order="6"}
## Directions of recession of a function

::: {.source-item #d90-mit-l09-p055-i001 data-source-page="55" data-source-order="1"}
- We aim to characterize directions of monotonic decrease of convex functions.
:::

::: {.source-item #d90-mit-l09-p055-i002 data-source-page="55" data-source-order="2"}
- Some basic geometric observations:

  - The "horizontal directions" in the recession cone of the epigraph of a convex function $f$ are directions along which the level sets are unbounded.

  - Along these directions the level sets $\{x\mid f(x)\leq\gamma\}$ are unbounded and $f$ is monotonically nondecreasing.
:::

::: {.source-item #d90-mit-l09-p055-i003 data-source-page="55" data-source-order="3"}
- These are the directions of recession of $f$.
:::

::: {.source-figure #d90-mit-l09-p055-f001 data-source-page="55" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** A three-dimensional sketch places the epigraph $\operatorname{epi}(f)$ above a horizontal plane. A horizontal slice at height $\gamma$ is labeled $\{(x,\gamma)\mid f(x)\leq\gamma\}$, and its projection is the level set $V_\gamma=\{x\mid f(x)\leq\gamma\}$. At the origin $0$ in that plane, a shaded horizontal cone is labeled the recession cone of $f$, indicating the directions in which the level set continues without bound.
:::

*[Source page 55.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p056 data-source-page="56" data-source-order="7"}
## Recession cone of level sets

::: {.source-item #d90-mit-l09-p056-i001 data-source-page="56" data-source-order="1"}
- Proposition: Let $f:\mathbb R^n\mapsto(-\infty,\infty]$ be a closed proper convex function and consider the level sets $V_\gamma=\{x\mid f(x)\leq\gamma\}$, where $\gamma$ is a scalar. Then:

  (a) All the nonempty level sets $V_\gamma$ have the same recession cone:

::: {.source-display #d90-mit-l09-p056-d001 data-source-page="56" data-display-order="1"}
$$
R_{V_\gamma}=\{d\mid(d,0)\in R_{\operatorname{epi}(f)}\}.
$$
:::

  (b) If one nonempty level set $V_\gamma$ is compact, then all level sets are compact.
:::

Proof: (a) Just translate to math the fact that

::: {.source-display #d90-mit-l09-p056-d002 data-source-page="56" data-display-order="2"}
$$
R_{V_\gamma}=\text{the "horizontal" directions of recession of }\operatorname{epi}(f).
$$
:::

Part (b) follows from (a).

*[Source page 56.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l09-p057-n001 data-source-page="57" data-correction-event="O015-MIT-SEM-0014"}
**Printed symbol preserved.** The source-page sentence below names $y$ as the recession direction although every panel labels the varying direction $d$ and the surrounding discussion also uses $d$. The witness retains the printed $y$ and records the inconsistency here.
:::

::: {.source-page #d90-mit-l09-p057 data-source-page="57" data-source-order="8"}
## Descent behavior of a convex function

::: {.source-figure #d90-mit-l09-p057-f001 data-source-page="57" data-figure-disposition="omitted-source-graphic" data-panel-count="6"}
**Semantic description of the omitted six-panel source figure.** Each panel graphs the one-dimensional profile $f(x+\alpha d)$ against the nonnegative parameter $\alpha$, with the starting height $f(x)$ marked on the vertical axis.

- **Panel (a):** The profile decreases convexly from $f(x)$ and flattens to zero asymptotic slope; the panel states $r_f(d)=0$.
- **Panel (b):** The profile decreases without flattening, with a negative asymptotic slope; the panel states $r_f(d)<0$.
- **Panel (c):** The profile decreases from $f(x)$ toward a lower constant level; the panel states $r_f(d)=0$.
- **Panel (d):** The profile remains horizontal at $f(x)$ for every $\alpha$; the panel states $r_f(d)=0$.
- **Panel (e):** The profile rises convexly from $f(x)$; the panel states $r_f(d)>0$.
- **Panel (f):** The profile first falls below $f(x)$ and then rises with positive asymptotic slope; the panel states $r_f(d)>0$.
:::

::: {.source-item #d90-mit-l09-p057-i001 data-source-page="57" data-source-order="1"}
- $y$ is a direction of recession in (a)-(d).
:::

::: {.source-item #d90-mit-l09-p057-i002 data-source-page="57" data-source-order="2"}
- This behavior is independent of the starting point $x$, as long as $x\in\operatorname{dom}(f)$.
:::

*[Source page 57.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p058 data-source-page="58" data-source-order="9"}
## Recession cone of a convex function

::: {.source-item #d90-mit-l09-p058-i001 data-source-page="58" data-source-order="1"}
- For a closed proper convex function $f:\mathbb R^n\mapsto(-\infty,\infty]$, the (common) recession cone of the nonempty level sets $V_\gamma=\{x\mid f(x)\leq\gamma\}$, $\gamma\in\mathbb R$, is the recession cone of $f$, and is denoted by $R_f$.
:::

::: {.source-figure #d90-mit-l09-p058-f001 data-source-page="58" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** Several nested, unbounded level-set contours of $f$ surround and extend away from the origin $0$. From the origin, a shaded wedge labeled recession cone $R_f$ points in their shared unbounded direction. The construction emphasizes that every nonempty level set has the same recession cone.
:::

::: {.source-item #d90-mit-l09-p058-i002 data-source-page="58" data-source-order="2"}
- Terminology:

  - $d\in R_f$: a direction of recession of $f$.

  - $L_f=R_f\cap(-R_f)$: the lineality space of $f$.

  - $d\in L_f$: a direction of constancy of $f$.
:::

::: {.source-item #d90-mit-l09-p058-i003 data-source-page="58" data-source-order="3"}
- Example: For the positive semidefinite quadratic

::: {.source-display #d90-mit-l09-p058-d001 data-source-page="58" data-display-order="1"}
$$
f(x)=x'Qx+a'x+b,
$$
:::

  the recession cone and constancy space are

::: {.source-display #d90-mit-l09-p058-d002 data-source-page="58" data-display-order="2"}
$$
R_f=\{d\mid Qd=0,\ a'd\leq 0\},\qquad
L_f=\{d\mid Qd=0,\ a'd=0\}.
$$
:::
:::

*[Source page 58.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l09-p059-n001 data-source-page="59" data-correction-event="O015-MIT-SEM-0015"}
**Printed set expression preserved.** In its explanation of the characterization, the source prints $R_f=\{(d,0)\in R_{\operatorname{epi}(f)}\}$, omitting an explicit set-builder variable and condition. The witness reproduces that expression literally and does not silently rewrite it as $\{d\mid(d,0)\in R_{\operatorname{epi}(f)}\}$.
:::

::: {.source-page #d90-mit-l09-p059 data-source-page="59" data-source-order="10"}
## Recession function

::: {.source-item #d90-mit-l09-p059-i001 data-source-page="59" data-source-order="1"}
- Function $r_f:\mathbb R^n\mapsto(-\infty,\infty]$ whose epigraph is $R_{\operatorname{epi}(f)}$ is the recession function of $f$.
:::

::: {.source-item #d90-mit-l09-p059-i002 data-source-page="59" data-source-order="2"}
- Characterizes the recession cone:

::: {.source-display #d90-mit-l09-p059-d001 data-source-page="59" data-display-order="1"}
$$
\begin{gathered}
R_f=\{d\mid r_f(d)\leq 0\},\qquad
L_f=\{d\mid r_f(d)=r_f(-d)=0\},\\
\text{since }R_f=\{(d,0)\in R_{\operatorname{epi}(f)}\}.
\end{gathered}
$$
:::
:::

::: {.source-item #d90-mit-l09-p059-i003 data-source-page="59" data-source-order="3"}
- Can be shown that

::: {.source-display #d90-mit-l09-p059-d002 data-source-page="59" data-display-order="2"}
$$
r_f(d)=\sup_{\alpha>0}\frac{f(x+\alpha d)-f(x)}{\alpha}
=\lim_{\alpha\to\infty}\frac{f(x+\alpha d)-f(x)}{\alpha}.
$$
:::
:::

::: {.source-item #d90-mit-l09-p059-i004 data-source-page="59" data-source-order="4"}
- Thus $r_f(d)$ is the "asymptotic slope" of $f$ in the direction $d$. In fact,

::: {.source-display #d90-mit-l09-p059-d003 data-source-page="59" data-display-order="3"}
$$
r_f(d)=\lim_{\alpha\to\infty}\nabla f(x+\alpha d)'d,\qquad
\forall x,d\in\mathbb R^n
$$
:::

  if $f$ is differentiable.
:::

::: {.source-item #d90-mit-l09-p059-i005 data-source-page="59" data-source-order="5"}
- Calculus of recession functions:

::: {.source-display #d90-mit-l09-p059-d004 data-source-page="59" data-display-order="4"}
$$
\begin{aligned}
r_{f_1+\cdots+f_m}(d)&=r_{f_1}(d)+\cdots+r_{f_m}(d),\\
r_{\sup_{i\in I}f_i}(d)&=\sup_{i\in I}r_{f_i}(d).
\end{aligned}
$$
:::
:::

*[Source page 59.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l09-p060-n001 data-source-page="60" data-correction-event="O015-MIT-SEM-0016"}
**Printed quantification gap preserved.** The source introduces $\epsilon$ in the definition of a local minimum without stating that there exists some $\epsilon>0$. The witness leaves that quantifier absent exactly as printed and does not silently complete the definition.
:::

::: {.source-defect-notice #d90-mit-l09-notice-minimum-terminology data-source-pages="60,61,62,63" data-correction-event="O015-MIT-SEM-0019"}
**Printed minimum/minimizer terminology preserved.** On source pages 60-63, the source calls a minimizing point $x^*$ a "minimum," calls collections of minimizing points "sets of minima," and ends by asserting a "unique minimum." The witness retains those printed expressions. A derivative should distinguish a minimizing point or set of minimizers from the minimum value; the page-63 uniqueness claim concerns the minimizer.
:::

::: {.source-page #d90-mit-l09-p060 data-source-page="60" data-source-order="11"}
## Local and global minima

::: {.source-item #d90-mit-l09-p060-i001 data-source-page="60" data-source-order="1"}
- Consider minimizing $f:\mathbb R^n\mapsto(-\infty,\infty]$ over a set $X\subset\mathbb R^n$.
:::

::: {.source-item #d90-mit-l09-p060-i002 data-source-page="60" data-source-order="2"}
- $x$ is feasible if $x\in X\cap\operatorname{dom}(f)$.
:::

::: {.source-item #d90-mit-l09-p060-i003 data-source-page="60" data-source-order="3"}
- $x^*$ is a (global) minimum of $f$ over $X$ if $x^*$ is feasible and $f(x^*)=\inf_{x\in X}f(x)$.
:::

::: {.source-item #d90-mit-l09-p060-i004 data-source-page="60" data-source-order="4"}
- $x^*$ is a local minimum of $f$ over $X$ if $x^*$ is a minimum of $f$ over a set $X\cap\{x\mid\lVert x-x^*\rVert\leq\epsilon\}$.
:::

Proposition: If $X$ is convex and $f$ is convex, then:

  (a) A local minimum of $f$ over $X$ is also a global minimum of $f$ over $X$.

  (b) If $f$ is strictly convex, then there exists at most one global minimum of $f$ over $X$.

::: {.source-figure #d90-mit-l09-p060-f001 data-source-page="60" data-figure-disposition="omitted-source-graphic"}
**Semantic description of the omitted source figure.** A convex graph of $f$ is drawn above a horizontal axis. Two graph points correspond to $\bar{x}$ and $x^*$, and a chord joins their function values. An intermediate argument $\alpha x^*+(1-\alpha)\bar{x}$ is marked below the graph; the graph value $f(\alpha x^*+(1-\alpha)\bar{x})$ is shown beneath the chord value $\alpha f(x^*)+(1-\alpha)f(\bar{x})$. A further point $x$ is marked to the right. The geometry illustrates the convexity inequality used to rule out a merely local, nonglobal minimum.
:::

*[Source page 60.]{.source-locator}*
:::

::: {.source-defect-notice #d90-mit-l09-p061-n001 data-source-page="61" data-correction-event="O015-MIT-SEM-0018"}
**Printed operation preserved.** The proof on source page 61 says that the level sets of $f\cap X$ are compact. Intersection between a function and a set is not defined in the surrounding notation; the likely intended construction is a restriction or an extended-real objective encoding the constraint. The witness retains $f\cap X$ exactly and does not choose a correction.
:::

::: {.source-defect-notice #d90-mit-l09-p061-n002 data-source-page="61" data-correction-event="O015-MIT-SEM-0017"}
**Printed missing hypothesis preserved.** In the extended Weierstrass theorem, the alternative that $X$ is bounded does not require $X\cap\operatorname{dom}(f)\neq\varnothing$. Without feasibility, the stated nonempty set of minima need not exist. The witness leaves the theorem unchanged as printed; a derivative should add the feasibility hypothesis.
:::

::: {.source-page #d90-mit-l09-p061 data-source-page="61" data-source-order="12"}
## Existence of optimal solutions

::: {.source-item #d90-mit-l09-p061-i001 data-source-page="61" data-source-order="1"}
- The set of minima of a proper $f:\mathbb R^n\mapsto(-\infty,\infty]$ is the intersection of its nonempty level sets.
:::

::: {.source-item #d90-mit-l09-p061-i002 data-source-page="61" data-source-order="2"}
- The set of minima of $f$ is nonempty and compact if the level sets of $f$ are compact.
:::

::: {.source-item #d90-mit-l09-p061-i003 data-source-page="61" data-source-order="3"}
- (An Extension of the) Weierstrass' Theorem: The set of minima of $f$ over $X$ is nonempty and compact if $X$ is closed, $f$ is lower semicontinuous over $X$, and one of the following conditions holds:

  (1) $X$ is bounded.

  (2) Some set $\{x\in X\mid f(x)\leq\gamma\}$ is nonempty and bounded.

  (3) For every sequence $\{x_k\}\subset X$ such that $\lVert x_k\rVert\to\infty$, we have $\lim_{k\to\infty}f(x_k)=\infty$. (Coercivity property.)

  Proof: In all cases the level sets of $f\cap X$ are compact. Q.E.D.
:::

*[Source page 61.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p062 data-source-page="62" data-source-order="13"}
## Existence of solutions - convex case

::: {.source-item #d90-mit-l09-p062-i001 data-source-page="62" data-source-order="1"}
- Weierstrass' Theorem specialized to convex functions: Let $X$ be a closed convex subset of $\mathbb R^n$, and let $f:\mathbb R^n\mapsto(-\infty,\infty]$ be closed convex with $X\cap\operatorname{dom}(f)\neq\varnothing$. The set of minima of $f$ over $X$ is nonempty and compact if and only if $X$ and $f$ have no common nonzero direction of recession.

  Proof: Let $f^*=\inf_{x\in X}f(x)$ and note that $f^*<\infty$ since $X\cap\operatorname{dom}(f)\neq\varnothing$. Let $\{\gamma_k\}$ be a scalar sequence with $\gamma_k\downarrow f^*$, and consider the sets

::: {.source-display #d90-mit-l09-p062-d001 data-source-page="62" data-display-order="1"}
$$
V_k=\{x\mid f(x)\leq\gamma_k\}.
$$
:::

  Then the set of minima of $f$ over $X$ is

::: {.source-display #d90-mit-l09-p062-d002 data-source-page="62" data-display-order="2"}
$$
X^*=\bigcap_{k=1}^{\infty}(X\cap V_k).
$$
:::

  The sets $X\cap V_k$ are nonempty and have $R_X\cap R_f$ as their common recession cone, which is also the recession cone of $X^*$, when $X^*\neq\varnothing$. It follows that $X^*$ is nonempty and compact if and only if

::: {.source-display #d90-mit-l09-p062-d003 data-source-page="62" data-display-order="3"}
$$
R_X\cap R_f=\{0\}.
$$
:::

  Q.E.D.
:::

*[Source page 62.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p063 data-source-page="63" data-source-order="14"}
## Existence of solution, sum of functions

::: {.source-item #d90-mit-l09-p063-i001 data-source-page="63" data-source-order="1"}
- Let $f_i:\mathbb R^n\mapsto(-\infty,\infty]$, $i=1,\ldots,m$, be closed proper convex functions such that the function

::: {.source-display #d90-mit-l09-p063-d001 data-source-page="63" data-display-order="1"}
$$
f=f_1+\cdots+f_m
$$
:::

  is proper. Assume that a single function $f_i$ satisfies $r_{f_i}(d)=\infty$ for all $d\neq 0$. Then the set of minima of $f$ is nonempty and compact.
:::

::: {.source-item #d90-mit-l09-p063-i002 data-source-page="63" data-source-order="2"}
- Proof: We have $r_f(d)=\infty$ for all $d\neq 0$ since $r_f(d)=\sum_{i=1}^m r_{f_i}(d)$. Hence $f$ has no nonzero directions of recession. Q.E.D.
:::

::: {.source-item #d90-mit-l09-p063-i003 data-source-page="63" data-source-order="3"}
- True also for $f=\max\{f_1,\ldots,f_m\}$.
:::

::: {.source-item #d90-mit-l09-p063-i004 data-source-page="63" data-source-order="4"}
- Example of application: If one of the $f_i$ is positive definite quadratic, the set of minima of the sum $f$ is nonempty and compact.
:::

::: {.source-item #d90-mit-l09-p063-i005 data-source-page="63" data-source-order="5"}
- Also $f$ has a unique minimum because the positive definite quadratic is strictly convex, which makes $f$ strictly convex.
:::

*[Source page 63.]{.source-locator}*
:::
