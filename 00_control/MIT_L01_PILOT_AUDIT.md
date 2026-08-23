# MIT 6.253 first-topic semantic-source pilot audit

As of: 2026-08-22  
Lane: O015 / D90 Advanced Optimization and Convex Analysis  
Locale: id-ID  
Disposition: **PASS and admitted as the first selected-primary reader unit**

## Authority and exact boundary

The source authority is Dimitri P. Bertsekas, *Convex Analysis and
Optimization*, MIT OpenCourseWare 6.253, Spring 2012. The complete-notes PDF is
`authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf`,
8,030,116 bytes / 340 pages / SHA-256
`41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181`.

This pilot covers exactly complete-notes PDF pages 2--5, the first topic of
Lecture 1, “The Role of Convexity in Optimization.” Page 6 begins the distinct
topic “Duality.” The admitted boundary contains four source pages, 21
top-level source items distributed 4/3/5/9, 12 nested bullets distributed
0/8/4/0, two display formulas, and zero figures. It contains no exercise,
hint, answer, solution, code, or interactive-computation prompt; those zero
inventories are recorded rather than silently omitted.

The official repository commit
`58d7c86195f09dd8708b84dde28205d3199207dd` / tree
`26d3136df9d5d7f564f0b1d068ec8d7a7c8818d6` is OCW/Hugo metadata, not
mathematical TeX. The authority PDF therefore remains the controlling source.
The project-made English semantic witness is a line-addressable transcription,
not a claim of official editable MIT source.

## Rights and excluded figure surface

The MIT-derived source witness, Indonesian semantic source, HTML, and PDF are
handled under CC BY-NC-SA 4.0 with source/MIT OCW attribution, change notice,
noncommercial use, ShareAlike, license link, no additional restrictions, MIT
name/logo restrictions, and non-endorsement. The source title page states that
figures are courtesy of Athena Scientific and used with permission. That
statement is not treated as a sublicensable adaptation grant. This boundary
contains zero figures and copies no Athena byte or layout. Later required
diagrams must be independently redrawn from mathematical primitives under a
separate rights record or omitted with an exact source locator.

The live component ledger has 80 rows and records MIT, Athena, Royer notes,
Royer laboratories, and pilot surfaces separately:
`00_control/COMPONENT_RIGHTS.csv`, 27,523 bytes, SHA-256
`2faf499071f954f2cef8ba6d1a7a8a47e9a08794fb066874bb7809bfb732da80`.

## Semantic reconstruction and corrections

- English witness: `source/en/mit-01-role-of-convexity-semantic-witness.md`,
  5,752 bytes, SHA-256
  `a18aefa9e1ffa29d0a3cea21d0df34f05025cb7c2008ae57b5db44730c9d1f58`.
- Indonesian target: `source/id-ID/mit-01-peran-kekonveksan-id.md`,
  8,641 bytes, SHA-256
  `2170dec12e707782c7677647f77ad8ee3360b282a8dbb9fb5620170106004bf3`.

The witness and target preserve exact one-to-one page and item anchors. The
source prefix `src-mit-` maps mechanically to target prefix `d90-mit-`; source
page order and within-page item order are exact. Three disclosed events are
integrated:

1. `O015-MIT-SEM-0001` scopes the source's broad discrete-dual claim to the
   duality framework intended in the lecture.
2. `O015-MIT-SEM-0002` makes the intended involutive meaning of “self-dual”
   explicit as `K^{\circ\circ}=K` and `f^{**}=f`, rather than the stronger
   unintended equalities with one polar/conjugate.
3. `O015-MIT-SEM-0003` records normalization of the source's function-type
   `\mapsto` to `\to`, while preserving the source notation in the English
   witness and explaining the difference in a labelled edition note.

The live adverse ledger contains 148 unique records including these three:
`00_control/ADVERSE_LEDGER.jsonl`, 95,476 bytes, SHA-256
`98d54f7b849456231e035f0d451c9f597a77b01aa9667718fbc720e7b39dabbb`.
Independent semantic rereview is frozen in
`qa/MIT_L01_INDEPENDENT_REREVIEW.md`, 2,691 bytes, SHA-256
`8259c6631c1c8645684c75a0244feedfc7289023d13e909cfdc73941eed35e50`;
after the third correction it closes at P1=0, P2=0, P3=0.

## Deterministic build

Canonical command:

```text
python qa/build_mit_pilot.py --output-root <bounded-output-root>
```

The builder uses Pandoc HTML5 with embedded CSS and MathML for the semantic
surface, and Pandoc plus LuaLaTeX for the reflowed A4 PDF. `SOURCE_DATE_EPOCH`,
`FORCE_SOURCE_DATE`, and `TZ=UTC` are fixed. Two clean output roots produce
byte-identical outputs:

- HTML: `output/html/D90-MIT-01-peran-kekonveksan-id.html`, 20,613 bytes,
  SHA-256 `fff4de952dd2cb208208e1cfb3bbc8fe8a64936ff5fdb532a23a92fb0dc6af8b`.
- PDF: `output/pdf/D90-MIT-01-peran-kekonveksan-id.pdf`, 53,370 bytes / three
  A4 pages, SHA-256
  `bd03912f9d3fe6dbe7376577c7ca6e7ab5aee007dd33b51669cde1792644df58`.

The builder is `qa/build_mit_pilot.py`, 3,025 bytes, SHA-256
`b109c24f01feb1f57193a05b56ae662902078c5fd63f457084379f7db66dac74`.
Its CSS, LaTeX preamble, Lua filter, and before/after-body fragments are bound
by exact artifact records; no network resource is required at read time.

## Fail-closed validation and visual/accessibility QA

`qa/validate_mit_pilot.py`, 19,571 bytes, SHA-256
`16dacd29912fd8b749f8d6ae8d44b716f814111c0a40eed27799e64fe6bf1108`,
binds the exact authority PDF, English witness, Indonesian target, browser
evidence, rereview, HTML, and PDF. It reparses both Markdown files through
Pandoc, verifies the exact page/item IDs and one-to-one mapping, recomputes the
12 nested bullets and math topology, checks all three correction surfaces,
rebuilds both outputs twice, rerenders the PDF, and checks PDF metadata and
font Unicode maps. The deterministic report passes twice byte-identically:
`qa/MIT_L01_PILOT_VALIDATION.json`, 4,167 bytes, SHA-256
`1e11642f8c1ab1ade013c4377f4dc0bc119ec0e89e6073eec787c7c341de0970`.

All three final PDF pages were rendered at 160 dpi and inspected individually.
There is no clipping, overlap, unreadable formula, broken heading, stranded
correction, or blank page. The PDF is searchable, unencrypted, A4, declares
`/Lang id-ID`, and all six font resources expose ToUnicode maps. It is not a
tagged PDF; the semantic HTML is the accessible primary surface at this
boundary.

The actual HTML was loaded in the in-app browser at 1280x720 and 390x844.
Both widths have zero horizontal or display-math overflow. The page has one
main landmark, heading topology 1/6/1, `lang=id-ID`, a `doc-toc` navigation,
an exact skip link to the first lecture page, 14 MathML nodes including two
display nodes, zero images, zero duplicate IDs, zero unresolved fragments,
and zero console warnings/errors. Durable measured evidence is
`qa/MIT_L01_BROWSER_QA.json`, 1,757 bytes, SHA-256
`2d5c90b3343040c4ed3dfbdb3714737dfba8317d1781c1e5c27145f5afbbb76d`.

The terminology QA uses an official Indonesian university publication as a
bounded fallback because no suitable Indonesian-language arXiv TeX source was
located. That fallback is terminology evidence only and is not redistributed;
its lack of an open license is respected. Independent human/native-speaker
review remains honestly unrecorded.

## Admission and next executable action

The semantic-source pilot passes the controlling PDF-to-semantic-source gate.
Bulk MIT production may now proceed, but only through the same page-addressed,
rights-aware, deterministic, fail-closed workflow. The next source-order cursor
is the complete-notes PDF page block 6--13, from “Duality” through
“Exceptional Behavior,” frozen in `MIT_L02_BOUNDARY_CENSUS.md`. Page 14,
“Modern View of Convex Optimization,” is the excluded successor.
No Penn Chapter 6 expansion is resumed, no Athena figure is copied, and no
final-course or human-review claim is made.

Production and QA assistance: **OpenAI Codex gpt-5.6-sol, Ultra**, at the
repository user's direction. This does not imply endorsement by MIT, Athena
Scientific, the source author, or any other institution.
