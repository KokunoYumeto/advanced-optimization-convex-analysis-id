# MIT 6.253 pages 16-19 boundary census

Date frozen: 2026-08-23  
Disposition: exact next coherent source-order batch; untranslated at census creation

## Authority and boundary

- Authority: Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare 6.253, Spring 2012.
- Official record: `https://ocw.mit.edu/courses/6-253-convex-analysis-and-optimization-spring-2012/`.
- Controlling source: `authority/mit-ocw-6.253/course-archive/static_resources/6c63c6219c60378bc27d5b4a9167f1bc_MIT6_253S12_lec_comp.pdf`.
- Identity: 8,030,116 bytes / 340 A4 pages / SHA-256 `41afb47e0f6ce328298d386d16c15defa1d98c88802175a22ba80b619bd18181`.
- Exact included boundary: physical PDF pages 16-19; the printed footer numbers are also 16-19.
- Coherence: page 16 closes Lecture 1's historical/methodological orientation; pages 17-19 give the course outline, expectations, and a note on the slides. Page 20 is the clean transition to Lecture 2.

The official repository is metadata rather than mathematical TeX; this PDF remains the controlling mathematical source. The census was checked against rendered pages, `pdftotext -layout`, Poppler XML, page dictionaries/annotations, and `pdfimages -list`.

## Exact topology and surface census

| PDF page | Exact heading | Top-level items | Nested items | Formula surfaces | Image/figure surfaces | Active URI links |
|---:|---|---:|---:|---:|---:|---:|
| 16 | `METHODOLOGICAL TRENDS` | 3 | 7 | 0 | 0 | 0 |
| 17 | `COURSE OUTLINE` | 3 | 12 | 0 | 0 | 2 |
| 18 | `WHAT TO EXPECT FROM THIS COURSE` | 4 | 7 | 0 | 0 | 0 |
| 19 | `A NOTE ON THESE SLIDES` | 6 | 0 | 0 | 0 | 0 |
| **Total** | **4 headings** | **16** | **26** | **0** | **0** | **2** |

The percentages on page 18 and the section/chapter designators on page 17 are prose numerals, not mathematical formula surfaces. There are no inline or display equations. There are no examples, definitions, theorem statements, proofs, tables, footnotes, citations with separate bibliography objects, or page-level figure captions.

Page 17 contains two `/Link` annotations, with URI targets `http://www.athenasc.com/convexduality.html` and `http://www.stanford.edu/~boyd/cvxbook/`. Poppler emits three XML anchor fragments because the second link is split across two text nodes; the PDF contains two actual link annotations. Pages 16, 18, and 19 contain no annotations.

`pdfimages -list` reports no images on pages 16-19. Page-dictionary inspection likewise finds zero `/Image` XObjects. Each page has one internal `/Form` XObject named `/Fm0`; this is a content wrapper, not a raster image or an external asset. Font-resource counts are 4/5/4/3 by page. No asset file needs extraction or carry-through for this batch.

## Learning and interactive surfaces

- Exercises: 0.
- Hints: 0.
- Answers: 0.
- Solutions: 0.
- Code, pseudocode, solver prompts, or computational notebooks: 0.
- Computational interactivity: 0.
- Ordinary navigation interactivity: two external hyperlinks on page 17 only.
- Form fields/widgets: 0 on these pages and 0 fields in the document AcroForm; JavaScript: none.

Page 18 mentions homework, a midterm, and a term paper as administrative course requirements, but it does not contain an exercise or assignment prompt. Page 19 discusses figures and omitted proofs in general, but contains neither a figure nor a proof surface.

## Extraction identities

The following hashes bind the exact UTF-8 layout-text and page-specific Poppler XML witnesses generated directly from the controlling PDF. XML was generated with Poppler 24.04.0.

| Page | Layout text bytes / SHA-256 | XML bytes / SHA-256 | XML text nodes |
|---:|---|---|---:|
| 16 | 568 / `5192187d4f6f53dfcbe2e0d79beff210f965b12d37cf494a8ceb26ce56ca2383` | 2,760 / `7d2d063bcb27d56c89cadc23c2cd012014c03eb3b6b14f75ab2af95c424ff8bf` | 25 |
| 17 | 1,062 / `7b90f697624e842c3f211d24bee9c1f22c8dc5925163425d400eec49ebbf8f94` | 5,209 / `5b5905569c3b1099350fd4f105011a2a1e996f44d7d00375e465d213f2367c85` | 48 |
| 18 | 1,061 / `389f37d1667406925e647eb187a2bb1a41607870490b0c1826f9e63ec47d8a58` | 4,020 / `1904ed7b9d87b329aedb7d71d2dfa294a000bce178d3840242d96d348c6f1528` | 37 |
| 19 | 560 / `400b53bb05d046cc9d8f8608ee761dc1b26851bff312ff36b54b2192fa6fd38e` | 2,412 / `950f3ad82e1334cc28599de0c80d4490081c2eb0944ada20e256a6053efe7433` | 20 |

## Rights and fidelity risks

The MIT-derived translation and reader surfaces must remain under CC BY-NC-SA 4.0 with source and MIT OpenCourseWare attribution, change notice, noncommercial use, ShareAlike, license link, no additional restrictions, MIT name/logo restrictions, and non-endorsement.

The complete-notes title page says Athena Scientific figures are used with permission; that statement is not a sublicensable adaptation grant. This batch has zero figure/image surfaces and therefore requires no Athena byte, crop, layout, redraw, or permission-dependent description. Page 17's two book/resource references and external links are citations only; they do not authorize importing third-party book or website content.

Two source-text details require deliberate fidelity handling rather than silent normalization: page 16 lists both `Subgradient/incremental methods` and a later `Incremental methods`; page 17 prints `Boyd and Vanderbergue`, while page 18 prints `Boyd and Vandenberghe`. Preserve the source witness exactly and disclose any correction or normalization in the derivative's adverse/change ledger.

## Exact next cursor

After this batch, resume at physical/printed PDF page 20. It begins `LECTURE 2`, then `LECTURE OUTLINE`; its first topic is `Convex sets and functions`, followed by `Epigraphs`, `Closed convex functions`, and `Recognizing convex functions`, with `Reading: Section 1.1`. Page 20 is excluded from this batch.
