# Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia

Edisi Bahasa Indonesia yang lengkap tentang optimisasi lanjut, analisis konveks, dan metode nonsmooth: terjemahan
*Lecture Notes: Convex Optimization* karya Andreas Habring (prakata dan Bab 1–9) sebagai tulang punggung, tiga suplemen
terbatas dari catatan kuliah Stephen Becker, dan tiga bagian asli (metode stokastik komposit, cermin, dan minibatch;
ketaksamaan variasional, operator monoton maksimal, resolven, dan pemisahan; asesmen kumulatif dengan solusi lengkap,
tujuh rubrik pembuktian, empat laboratorium, dan capstone). Tersedia sebagai PDF terintegrasi 141 halaman, HTML, EPUB 3,
sumber TeX semantik, dan backend modular (4.877 rekaman).

[Baca daring](https://kokunoyumeto.github.io/advanced-optimization-convex-analysis-id/) · [PDF terintegrasi](output/pdf/D90-O015-optimisasi-lanjut-analisis-konveks-id.pdf) · [HTML](output/html/D90-O015-optimisasi-lanjut-analisis-konveks-id.html) ·
[EPUB](output/epub/D90-O015-optimisasi-lanjut-analisis-konveks-id.epub)

English: *Advanced Optimization and Convex Analysis*, Indonesian (id-ID) edition.

## Cara pembuatan

Terjemahan, rekonstruksi sumber semantik, penulisan bagian asli, asesmen, pembuatan backend, serta pemeriksaan
matematika dan komputasi dikerjakan oleh AI: OpenAI Codex gpt-5.6-sol, Ultra. Koreksi sumber dicatat terpisah. PDF
terintegrasi dapat dicari, mendeklarasikan `id-ID`, dan memiliki pohon struktur, urutan baca, bookmark, dan tautan pada
seluruh 141 halaman; semua halaman dirender dan diperiksa. HTML diperiksa di peramban pada lebar 1.440, 768, dan 390
piksel; EPUB 3 lulus validasi. Belum ada tinjauan bahasa oleh manusia.

## Status

Edisi terintegrasi lengkap. Tidak ada klaim PDF/UA. Masih mungkin ada kesalahan.

## Isi

- [Halaman pembaca](https://kokunoyumeto.github.io/advanced-optimization-convex-analysis-id/): 17 pembaca HTML (modul Habring, Becker, bagian asli, dan pendamping), dengan identitas
  sumber dan SHA-256 di `docs/reader-manifest.json`; cermin itu dibangun ulang dengan
  `python -B tools/build_github_pages.py --sync` dan diperiksa tanpa jaringan dengan
  `python -B tools/build_github_pages.py`.
- `output/pdf/`, `output/html/`, `output/epub/`: pembaca terintegrasi serta pembaca per komponen (Habring Bab 1–9,
  bagian asli, dan pendamping).
- `source/`: sumber TeX semantik; `labs/`: laboratorium komputasi; `backend/`: rekaman dengan pengenal stabil;
  `authority/` dan `00_control/`: sumber yang dibekukan, hak komponen, dan koreksi; `qa/`: skrip build dan pemeriksaan.

## Sumber dan atribusi

- Andreas Habring, *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1 (prakata dan Bab 1–9), CC BY 4.0. Sumber itu
  menyebut Thomas Pock sebagai asal slide kuliah dan memakai templat Christian Clason.
- Stephen Becker, `convex-optimization-class` (commit `98ed6930084c435ba0f675f7646ced1f2fd8729e`), dengan catatan yang
  diketik Mitchell Krock: hanya rentang baris yang tercatat di [PROVENANCE.md](PROVENANCE.md), MIT.
- Pendamping berlisensi terpisah, bukan masukan pembaca terintegrasi: MIT OpenCourseWare 6.253 karya Dimitri P.
  Bertsekas; materi gradien stokastik Clément W. Royer (dengan kredit notebook A. Gramfort dan Robert Gower); Penn State
  MATH 555 karya Christopher Griffin (dengan kontribusi Simon Miller dan Douglas Mercer).
- Edisi ini independen dan tidak didukung oleh para penulis atau lembaga sumber.

## Lisensi

Tidak ada lisensi menyeluruh: terjemahan tulang punggung Habring CC BY 4.0; teks donor Becker/Krock MIT; terjemahan,
koreksi, prosa penghubung, latihan, dan bagian asli CC BY-SA 4.0; pendamping mempertahankan lisensinya sendiri. Lihat
[RIGHTS.md](RIGHTS.md) dan `00_control/COMPONENT_RIGHTS.csv`.
