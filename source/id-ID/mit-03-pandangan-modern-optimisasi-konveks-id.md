---
title: "Pandangan Modern tentang Optimisasi Konveks"
subtitle: "MIT 6.253 - Edisi Indonesia, halaman sumber 14"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
lang: id-ID
date: "2026-08-23"
rights: "Terjemahan MIT OCW 6.253, CC BY-NC-SA 4.0"
description: "Rekonstruksi semantik yang dapat mengalir ulang dari satu halaman sumber, dengan pengenal stabil, label diagram, dan deskripsi aksesibel."
keywords:
  - optimisasi konveks
  - pemrograman linear
  - pemrograman nonlinier
  - dualitas
  - subgradien
  - id-ID
---

::: {.edition-notice #d90-mit-l03-edition-notice}
## Tentang batas ini

Ini adalah rekonstruksi sumber semantik dan terjemahan bahasa Indonesia dari
Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare
6.253, Spring 2012, halaman PDF sumber 14. Halaman ini membandingkan pandangan
tradisional dan modern tentang optimisasi konveks. Materi sumber berada di
bawah [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Dua permukaan grafik sumber sengaja tidak disalin karena catatan menyatakan
bahwa grafik tersebut digunakan atas izin Athena Scientific. Tidak ada byte,
potongan, atau tata letak grafik sumber yang masuk ke edisi ini. Sebagai gantinya,
setiap grafik mempunyai lokator halaman yang tepat, deskripsi semantik, semua
label, dan hubungan matematis yang dipertahankan. Bantuan produksi dan QA:
**OpenAI Codex gpt-5.6-sol, Ultra**, atas arahan pengguna repositori. Sistem
tersebut bukan penulis sumber atau pemberi lisensi. Tidak ada dukungan oleh MIT,
Athena Scientific, atau penulis sumber yang tersirat. Tinjauan bahasa
manusia/penutur asli belum tercatat.

Pengenal stabil tetap melekat pada halaman, butir, dan deskripsi grafik,
meskipun HTML atau PDF mengalir ulang ke ukuran layar atau halaman yang
berbeda.
:::

::: {.source-page #d90-mit-l03-p014 data-source-page="14" data-source-order="1"}
## Pandangan Modern tentang Optimisasi Konveks

::: {.source-item #d90-mit-l03-p014-i001 data-source-page="14" data-source-order="1"}
- **Pandangan tradisional: sebelum 1990-an**

  - LP diselesaikan dengan metode simpleks.
  - NLP diselesaikan dengan metode gradien/Newton.
  - Program konveks merupakan kasus khusus NLP.

::: {.source-figure #d90-mit-l03-p014-f001 data-source-page="14" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 14, pandangan tradisional).** Diagram
kiri berupa oval berlabel **LP**, dengan **Simpleks** di bawahnya. Di kanan,
dua oval yang saling tumpang tindih berlabel **CONVEX** dan **NLP**; label
**Dualitas** berada di bawah daerah tumpang tindih, sedangkan
**Gradien/Newton** berada di bawah sisi NLP. Diagram menempatkan program
konveks sebagai wilayah khusus dalam pemrograman nonlinier dan menempatkan
dualitas di antara pandangan LP dan konveks.
:::
:::

::: {.source-item #d90-mit-l03-p014-i002 data-source-page="14" data-source-order="2"}
- **Pandangan modern: setelah 1990-an**

  - LP sering diselesaikan dengan metode nonsimpleks/konveks.
  - Masalah konveks sering diselesaikan dengan metode yang sama seperti LP.
  - “Pembedaan kunci bukan Linear-Nonlinear, melainkan
    Konveks-Nonkonveks” (Rockafellar).

::: {.source-figure #d90-mit-l03-p014-f002 data-source-page="14" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 14, pandangan modern).** Diagram
bawah memiliki oval **LP** dan **CONVEX** yang saling tumpang tindih, dengan
**Simpleks** di bawah sisi LP. Di bawah daerah tumpang tindih tercantum
**Dualitas**, **Bidang potong**, **Titik interior**, dan **Subgradien**. Oval
terpisah berlabel **NLP** berada di kanan, dengan **Gradien/Newton** di
bawahnya. Tumpang tindih tersebut menekankan bahwa program konveks dan linear
berbagi metode penyelesaian penting, sedangkan pemrograman nonlinier umum
tetap terpisah dalam perbandingan ini.
:::
:::

*[Halaman sumber 14]{.source-locator}*

::: {.edition-backmatter #d90-mit-l03-backmatter}
## Identitas sumber dan batas edisi

- Sumber: Dimitri P. Bertsekas, *Lecture Slides on Convex Analysis and
  Optimization*, berdasarkan MIT 6.253, Spring 2012.
- Batas tepat: hanya halaman PDF lengkap 14; halaman berikutnya merupakan
  kelanjutan catatan lengkap.
- Grafik: dua grafik sumber yang digunakan atas izin dihilangkan. Lokator,
  label, hubungan, dan makna matematis dipertahankan dalam deskripsi semantik;
  tidak ada byte, potongan, atau tata letak Athena Scientific yang disalin.
- Hak: komponen turunan ini tetap CC BY-NC-SA 4.0, dengan kewajiban atribusi,
  penandaan perubahan, penggunaan nonkomersial, ShareAlike, dan nondukungan.
- Halaman ini tidak memuat latihan pembelajar, petunjuk, solusi, atau
  permukaan komputasi interaktif.
:::

*[Halaman sumber 14]{.source-locator}*
