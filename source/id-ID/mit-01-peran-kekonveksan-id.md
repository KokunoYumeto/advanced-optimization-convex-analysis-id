---
title: "Peran Kekonveksan dalam Optimisasi"
subtitle: "Pilot sumber semantik - Kuliah 1, halaman sumber 2-5"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
lang: id-ID
date: "2026-08-22"
rights: "Terjemahan MIT OCW 6.253, CC BY-NC-SA 4.0"
description: "Terjemahan Indonesia yang dapat mengalir ulang dari topik pertama Kuliah 1 MIT OCW 6.253, dengan pengenal stabil dan peta halaman sumber."
keywords:
  - optimisasi konveks
  - analisis konveks
  - dualitas
  - id-ID
---

::: {.edition-notice #d90-mit-l01-edition-notice}
## Tentang pilot ini

Ini adalah rekonstruksi sumber semantik dan terjemahan bahasa Indonesia dari
Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare
6.253, Spring 2012, topik pertama Kuliah 1 pada halaman PDF sumber 2--5.
Materi sumber tersedia di bawah
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Edisi ini mengubah bahasa, tata letak slide menjadi pembaca yang dapat mengalir
ulang, hierarki semantik, dan penandaan sumber. Tidak ada dukungan oleh MIT,
Athena Scientific, atau penulis sumber yang tersirat.

Halaman judul sumber menyatakan bahwa semua gambar digunakan atas izin Athena
Scientific. Batas pilot ini tidak memuat gambar; tidak ada byte atau tata letak
gambar Athena yang disalin. Bantuan produksi dan QA: **OpenAI Codex
gpt-5.6-sol, Ultra**, atas arahan pengguna repositori. Sistem tersebut bukan
penulis sumber atau pemberi lisensi. Tinjauan bahasa manusia/penutur asli belum
tercatat.

Setiap bagian bertanda “Halaman sumber” memetakan tepat satu halaman PDF.
Pengenal stabil tetap melekat pada bagian dan butir, meskipun HTML atau PDF
mengalir ulang ke ukuran layar atau halaman yang berbeda.
:::

::: {.source-page #d90-mit-l01-p002 data-source-page="2" data-source-order="1"}
## Kuliah 1: Pengantar Mata Kuliah

### Garis Besar Kuliah

::: {.source-item #d90-mit-l01-p002-i001 data-source-page="2" data-source-order="1"}
- Peran kekonveksan dalam optimisasi
:::

::: {.source-item #d90-mit-l01-p002-i002 data-source-page="2" data-source-order="2"}
- Teori dualitas
:::

::: {.source-item #d90-mit-l01-p002-i003 data-source-page="2" data-source-order="3"}
- Algoritma dan dualitas
:::

::: {.source-item #d90-mit-l01-p002-i004 data-source-page="2" data-source-order="4"}
- Organisasi mata kuliah
:::

*[Halaman sumber 2]{.source-locator}*
:::

::: {.source-page #d90-mit-l01-p003 data-source-page="3" data-source-order="2"}
## Sejarah dan Prasejarah

::: {.source-item #d90-mit-l01-p003-i001 data-source-page="3" data-source-order="1"}
- **Prasejarah: awal 1900-an--1949.**

  - Caratheodory, Minkowski, Steinitz, Farkas.
  - Sifat-sifat himpunan dan fungsi konveks.
:::

::: {.source-item #d90-mit-l01-p003-i002 data-source-page="3" data-source-order="2"}
- **Era Fenchel--Rockafellar: 1949--pertengahan 1980-an.**

  - Teori dualitas.
  - Teori minimaks/permainan (von Neumann).
  - (Sub)diferensiabilitas, syarat optimalitas, sensitivitas.
:::

::: {.source-item #d90-mit-l01-p003-i003 data-source-page="3" data-source-order="3"}
- **Era modern--pergeseran paradigma: pertengahan 1980-an--sekarang.**

  - Analisis nonsmooth (arah teoretis/esoteris).
  - Algoritma (arah praktis/berdampak tinggi).
  - Perubahan asumsi yang mendasari bidang ini.
:::

*[Halaman sumber 3]{.source-locator}*
:::

::: {.source-page #d90-mit-l01-p004 data-source-page="4" data-source-order="3"}
## Masalah Optimisasi

::: {.source-item #d90-mit-l01-p004-i001 data-source-page="4" data-source-order="1"}
- **Bentuk umum:**

  $$
  \begin{aligned}
  \text{minimalkan}\quad & f(x) \\
  \text{dengan syarat}\quad & x\in C.
  \end{aligned}
  $$

  Fungsi biaya $f:\mathbb{R}^n\to\mathbb{R}$ dan himpunan kendala $C$;
  misalnya,

  $$
  \begin{aligned}
  C ={}& X\cap\{x\mid h_1(x)=0,\ldots,h_m(x)=0\}\\
       & {}\cap\{x\mid g_1(x)\leq 0,\ldots,g_r(x)\leq 0\}.
  \end{aligned}
  $$
:::

::: {.edition-note #d90-mit-l01-note-function-arrow data-correction-id="O015-MIT-SEM-0003"}
**Catatan edisi.** Sumber menulis $f:\mathbb{R}^n\mapsto\mathbb{R}$.
Edisi menormalkan panah itu menjadi $\to$ untuk notasi tipe fungsi; simbol
$\mapsto$ lazimnya dipakai antara suatu argumen dan nilainya, misalnya
$x\mapsto f(x)$.
:::

::: {.source-item #d90-mit-l01-p004-i002 data-source-page="4" data-source-order="2"}
- Pembedaan antara masalah kontinu dan masalah diskret.
:::

::: {.source-item #d90-mit-l01-p004-i003 data-source-page="4" data-source-order="3"}
- Masalah pemrograman konveks adalah masalah dengan $f$ dan $C$ konveks.

  - Masalah tersebut bersifat kontinu.
  - Masalah tersebut tertata baik, dengan struktur yang indah dan intuitif.
:::

::: {.source-item #d90-mit-l01-p004-i004 data-source-page="4" data-source-order="4"}
- Namun, kekonveksan meresap ke seluruh optimisasi, termasuk masalah diskret.
:::

::: {.source-item #d90-mit-l01-p004-i005 data-source-page="4" data-source-order="5"}
- Sarana utama yang menghubungkan masalah kontinu dan diskret adalah dualitas:

  - Dalam kerangka dualitas yang dimaksud di sini, masalah dual dari masalah
    diskret bersifat kontinu/konveks.
  - Masalah dual memberikan informasi penting untuk menyelesaikan primal
    diskret, misalnya batas bawah.
:::

::: {.edition-note #d90-mit-l01-note-dual-discrete data-correction-id="O015-MIT-SEM-0001"}
**Catatan edisi.** Sumber menyatakan klaim kontinu/konveks di atas tanpa
membatasi pengertian dual. Edisi menambahkan frasa “dalam kerangka dualitas yang
dimaksud di sini”: untuk masalah diskret secara umum, sifat dual bergantung pada
formulasi, relaksasi, dan konstruksi dual yang dipilih.
:::

*[Halaman sumber 4]{.source-locator}*
:::

::: {.source-page #d90-mit-l01-p005 data-source-page="5" data-source-order="4"}
## Mengapa Kekonveksan Begitu Istimewa?

::: {.source-item #d90-mit-l01-p005-i001 data-source-page="5" data-source-order="1"}
- Fungsi konveks tidak mempunyai minimum lokal yang bukan minimum global.
:::

::: {.source-item #d90-mit-l01-p005-i002 data-source-page="5" data-source-order="2"}
- Fungsi nonkonveks dapat “dikonvekskan” sambil mempertahankan optimalitas
  minimum globalnya.
:::

::: {.source-item #d90-mit-l01-p005-i003 data-source-page="5" data-source-order="3"}
- Himpunan konveks mempunyai interior relatif yang tak kosong.
:::

::: {.source-item #d90-mit-l01-p005-i004 data-source-page="5" data-source-order="4"}
- Himpunan konveks terhubung dan mempunyai arah layak pada setiap titik.
:::

::: {.source-item #d90-mit-l01-p005-i005 data-source-page="5" data-source-order="5"}
- Keberadaan minimum global suatu fungsi konveks pada himpunan konveks dapat
  dicirikan dengan mudah melalui arah resesi.
:::

::: {.source-item #d90-mit-l01-p005-i006 data-source-page="5" data-source-order="6"}
- Himpunan konveks polihedral dicirikan oleh suatu himpunan hingga yang terdiri
  dari titik ekstrem dan arah ekstrem.
:::

::: {.source-item #d90-mit-l01-p005-i007 data-source-page="5" data-source-order="7"}
- Fungsi konveks bernilai real bersifat kontinu dan mempunyai sifat
  diferensiabilitas yang baik.
:::

::: {.source-item #d90-mit-l01-p005-i008 data-source-page="5" data-source-order="8"}
- Kerucut konveks tertutup pulih kembali melalui bipolaritas:
  $K^{\circ\circ}=K$.
:::

::: {.source-item #d90-mit-l01-p005-i009 data-source-page="5" data-source-order="9"}
- Fungsi konveks semikontinu bawah pulih kembali melalui bikonjugasi:
  $f^{**}=f$.
:::

::: {.edition-note #d90-mit-l01-note-self-dual data-correction-id="O015-MIT-SEM-0002"}
**Catatan edisi.** Dua butir terakhir membuat makna istilah *self-dual* pada
sumber menjadi eksplisit. Yang dimaksud adalah pemulihan setelah operasi dual
diterapkan dua kali, bukan klaim $K=K^\circ$ atau $f=f^*$.
:::

*[Halaman sumber 5]{.source-locator}*
:::

::: {.edition-backmatter #d90-mit-l01-edition-backmatter}
## Identitas sumber dan perubahan

- Sumber: Dimitri P. Bertsekas, *Lecture Slides on Convex Analysis and
  Optimization*, berdasarkan kuliah MIT 6.253, Spring 2012.
- Batas: PDF lengkap halaman 2--5; halaman 6 memulai topik “Duality”.
- Perubahan: terjemahan bahasa Indonesia, reflow slide menjadi pembaca,
  hierarki semantik, pengenal stabil, peta halaman, serta tiga klarifikasi atau
  koreksi matematika berlabel `O015-MIT-SEM-0001`, `O015-MIT-SEM-0002`, dan
  `O015-MIT-SEM-0003`.
- Hak: komponen turunan MIT tetap CC BY-NC-SA 4.0. Tidak ada gambar dalam
  batas ini dan tidak ada komponen Athena Scientific yang disalin.
- Keterbatasan: pilot ini belum merupakan keseluruhan Kuliah 1 atau keseluruhan
  mata kuliah; PDF belum bertanda semantik dan tinjauan bahasa manusia belum
  tercatat. HTML adalah permukaan semantik utama pada batas ini.
:::
