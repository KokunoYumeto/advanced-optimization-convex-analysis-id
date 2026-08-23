---
title: "Dualitas dan Perilaku Pengecualian"
subtitle: "MIT 6.253 - Edisi Indonesia, halaman sumber 6-13"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
lang: id-ID
date: "2026-08-23"
rights: "Terjemahan MIT OCW 6.253, CC BY-NC-SA 4.0"
description: "Terjemahan Indonesia yang dapat mengalir ulang dari halaman sumber 6-13, dengan pengenal stabil, formula, label diagram, dan deskripsi semantik yang dapat diakses."
keywords:
  - dualitas
  - analisis konveks
  - fungsi konjugat
  - optimisasi Fenchel
  - id-ID
---

::: {.edition-notice #d90-mit-l02-edition-notice}
## Tentang batas ini

Ini adalah rekonstruksi sumber semantik dan terjemahan bahasa Indonesia dari
Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare
6.253, Spring 2012, halaman PDF sumber 6-13. Batas ini dimulai pada **Dualitas**
dan berakhir pada **Perilaku Pengecualian**; halaman 14, **Pandangan Modern
tentang Optimisasi Konveks**, adalah topik berikutnya dan tidak disertakan.
Materi sumber berada di bawah
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Tujuh permukaan grafik sumber sengaja tidak disalin karena catatan menyatakan
bahwa grafik tersebut digunakan atas izin Athena Scientific. Tidak ada byte,
potongan, atau tata letak grafik sumber yang masuk ke edisi ini. Sebagai gantinya,
setiap grafik mempunyai lokator halaman yang tepat, deskripsi semantik yang
rinci, serta semua label dan formula matematika yang dipertahankan. Ini menjaga
aksesibilitas tanpa mengklaim hak untuk mendistribusikan grafik izin tersebut.

Istilah teknis *primal* dan *dual* dipertahankan sebagai label standar; istilah
lain yang dipakai konsisten di seluruh batas ini meliputi **epigraf**,
**hiperbidang**, **fungsi konjugat**, **titik persekutuan minimum**, dan **titik
perpotongan maksimum**. Bantuan produksi dan QA: **OpenAI Codex gpt-5.6-sol,
Ultra**, atas arahan pengguna repositori. Sistem tersebut bukan penulis sumber
atau pemberi lisensi. Tidak ada dukungan oleh MIT, Athena Scientific, atau
penulis sumber yang tersirat. Tinjauan bahasa manusia/penutur asli belum
tercatat.

Setiap bagian bertanda "Halaman sumber" memetakan tepat satu halaman PDF.
Pengenal stabil tetap melekat pada halaman, butir, dan deskripsi grafik,
meskipun HTML atau PDF mengalir ulang ke ukuran layar atau halaman yang
berbeda.
:::

::: {.source-page #d90-mit-l02-p006 data-source-page="6" data-source-order="1"}
## Dualitas

::: {.source-item #d90-mit-l02-p006-i001 data-source-page="6" data-source-order="1"}
- Dua pandangan berbeda atas objek yang sama.
:::

::: {.source-item #d90-mit-l02-p006-i002 data-source-page="6" data-source-order="2"}
- **Contoh: deskripsi dual sinyal.**

::: {.source-figure #d90-mit-l02-p006-f001 data-source-page="6" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 6, contoh sinyal).** Dua persegi
panjang berlabel **Ranah waktu** dan **Ranah frekuensi** dihubungkan oleh panah
dua arah. Intinya adalah bahwa sinyal yang sama dapat direpresentasikan pada
kedua ranah; halaman ini tidak menyatakan formula transformasi tertentu. Grafik
sumber dihilangkan karena batas hak yang dijelaskan di atas.

**Deskripsi grafik sumber (halaman sumber 6, himpunan konveks tertutup).**
Pandangan kiri adalah gabungan titik-titik yang mengisi suatu daerah konveks
tertutup. Pandangan kanan adalah irisan setengah-ruang yang garis batasnya
menopang daerah yang sama. Kedua pandangan itu merupakan deskripsi alternatif
untuk satu himpunan konveks tertutup.
:::
:::

::: {.source-item #d90-mit-l02-p006-i003 data-source-page="6" data-source-order="3"}
- **Deskripsi dual himpunan konveks tertutup.**

:::

*[Halaman sumber 6]{.source-locator}*
:::

::: {.source-page #d90-mit-l02-p007 data-source-page="7" data-source-order="2"}
## Deskripsi Dual Fungsi Konveks

::: {.source-item #d90-mit-l02-p007-i001 data-source-page="7" data-source-order="1"}
- Definisikan fungsi konveks tertutup melalui epigrafnya.
:::

::: {.source-item #d90-mit-l02-p007-i002 data-source-page="7" data-source-order="2"}
- Deskripsikan epigraf itu melalui hiperbidang.
:::

::: {.source-item #d90-mit-l02-p007-i003 data-source-page="7" data-source-order="3"}
- Kaitkan hiperbidang dengan titik perpotongan (fungsi konjugat).

::: {.source-figure #d90-mit-l02-p007-f001 data-source-page="7" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 7, epigraf dan konjugat).** Dalam
koordinat $(x,f(x))$, suatu kurva konveks tertutup disentuh oleh garis dengan
kemiringan $y$. Garis tersebut diberi label titik $(-y,1)$; label yang
dipertahankan adalah $f(x)$, **Kemiringan = $y$**, sumbu $x$ dan titik asal $0$,
serta pembedaan antara **Deskripsi Primal: Nilai $f(x)$** dan **Deskripsi Dual:
Titik perpotongan $f^*(y)$**. Sumber juga mencetak identitas berikut:

$$
\inf_{x\in\mathbb{R}^n}\{f(x)-x^\mathsf{T}y\}=-f^*(y).
$$
:::
:::

*[Halaman sumber 7]{.source-locator}*
:::

::: {.source-page #d90-mit-l02-p008 data-source-page="8" data-source-order="3"}
## Masalah Primal dan Dual Fenchel

::: {.source-item #d90-mit-l02-p008-i001 data-source-page="8" data-source-order="1"}
- **Masalah primal:**

  $$
  \min_x\{f_1(x)+f_2(x)\}.
  $$
:::

::: {.source-item #d90-mit-l02-p008-i002 data-source-page="8" data-source-order="2"}
- **Masalah dual:**

  $$
  \max_y\{-f_1^*(y)-f_2^*(-y)\}.
  $$

  Di sini $f_1^*$ dan $f_2^*$ adalah fungsi konjugat.

::: {.source-figure #d90-mit-l02-p008-f001 data-source-page="8" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 8, geometri primal/dual Fenchel).**
Panel primal membandingkan jarak vertikal antara grafik $f_1(x)$ dan
$-f_2(x)$ pada $x^*$. Panel dual membandingkan perbedaan titik perpotongan dua
garis sejajar dengan kemiringan $y$. Label yang dipertahankan meliputi
$f_1(x)$, $-f_2(x)$, $f_1^*(y)$, $f_2^*(-y)$, **Kemiringan $y$**, $x^*$,
serta deskripsi primal/dual **Jarak Vertikal** dan **Perbedaan Titik
Perpotongan**.
:::
:::

*[Halaman sumber 8]{.source-locator}*
:::

::: {.source-page #d90-mit-l02-p009 data-source-page="9" data-source-order="4"}
## Dualitas Fenchel

::: {.source-display #d90-mit-l02-p009-d001 data-source-page="9" data-display-order="1"}
Kesetaraan Fenchel adalah

  $$
  \min_x\{f_1(x)+f_2(x)\}
  =
  \max_y\{-f_1^*(y)-f_2^*(-y)\}.
  $$

::: {.source-figure #d90-mit-l02-p009-f001 data-source-page="9" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 9, geometri Fenchel yang
menguntungkan).** Konstruksi dua kurva yang sama ditampilkan dengan satu garis
berkemiringan $y^*$ pada perpotongan optimal dan garis lain berkemiringan $y$.
Labelnya mencakup $f_1(x)$, $-f_2(x)$, $f_1^*(y)$, $f_2^*(-y)$, $x^*$,
**Kemiringan $y^*$**, dan **Kemiringan $y$**. Kesetaraan di atas dicetak di
bawah gambar sumber.
:::
:::

::: {.source-item #d90-mit-l02-p009-i001 data-source-page="9" data-source-order="1"}
- Dalam kondisi yang menguntungkan (kekonveksan):

  - Nilai optimal primal dan dual sama.
  - Solusi optimal primal dan dual saling berkaitan.
:::

*[Halaman sumber 9]{.source-locator}*
:::

::: {.source-page #d90-mit-l02-p010 data-source-page="10" data-source-order="5"}
## Pandangan yang Lebih Abstrak tentang Dualitas

::: {.source-item #d90-mit-l02-p010-i001 data-source-page="10" data-source-order="1"}
- Walaupun elegan, kerangka Fenchel agak tidak langsung.
:::

::: {.source-item #d90-mit-l02-p010-i002 data-source-page="10" data-source-order="2"}
- Dari dualitas deskripsi himpunan, menuju

  - dualitas deskripsi fungsional, lalu
  - dualitas deskripsi masalah.
:::

::: {.source-item #d90-mit-l02-p010-i003 data-source-page="10" data-source-order="3"}
- Pendekatan yang lebih langsung:

  - Mulai dari suatu himpunan, lalu
  - Definisikan dua masalah prototipe yang saling dual.
:::

::: {.source-item #d90-mit-l02-p010-i004 data-source-page="10" data-source-order="4"}
- Hindari deskripsi fungsional (kerangka yang lebih sederhana dan lebih sedikit
  kendalanya).
:::

*[Halaman sumber 10]{.source-locator}*
:::

::: {.source-page #d90-mit-l02-p011 data-source-page="11" data-source-order="6"}
## Dualitas Titik Persekutuan Minimum/Titik Perpotongan Maksimum

::: {.source-figure #d90-mit-l02-p011-f001 data-source-page="11" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 11, panel (a)-(c)).** Setiap panel
menggunakan koordinat $(u,w)$ dan menandai himpunan $M$, kadang-kadang bersama
penutupnya $\overline{M}$. Sebuah garis pendukung mengidentifikasi **Titik
Persekutuan Minimum $w^*$**, sedangkan konstruksi pendukung kedua
mengidentifikasi **Titik Perpotongan Maksimum $q^*$**. Panel (a) dan (b)
menunjukkan konfigurasi geometris yang teratur; panel (c) menunjukkan
konfigurasi pengecualian/patologis ketika kedua titik itu tidak harus berperilaku
teratur. Label $M$, $\overline M$, $u$, $w$, $0$, $w^*$, dan $q^*$
dipertahankan dalam deskripsi semantik ini.
:::

::: {.source-item #d90-mit-l02-p011-i001 data-source-page="11" data-source-order="1"}
- Seluruh teori dualitas dan seluruh teori minimaks (konveks/konkaf) dapat
  dikembangkan/dijelaskan dalam kerangka satu gambar ini.
:::

::: {.source-item #d90-mit-l02-p011-i002 data-source-page="11" data-source-order="2"}
- Perangkat analisis konveks diperlukan untuk menguraikan gambar ini dan untuk
  menyingkirkan perilaku pengecualian/patologis yang ditunjukkan pada (c).
:::

*[Halaman sumber 11]{.source-locator}*
:::

::: {.source-page #d90-mit-l02-p012 data-source-page="12" data-source-order="7"}
## Analisis Dualitas Abstrak/Umum

::: {.source-figure #d90-mit-l02-p012-f001 data-source-page="12" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 12, alur analisis).** Alur dimulai
dari **Kerangka Geometris Abstrak (Himpunan $M$)** dan menunjuk ke **Teorema
Titik Persekutuan Minimum/Titik Perpotongan Maksimum**. Pilihan khusus $M$
bercabang menjadi **Dualitas Minimax
($\operatorname{MinMax}=\operatorname{MaxMin}$)**, **Dualitas Optimisasi
Berkendala**, dan **Teorema Alternatif, dll.** Label **Pilihan khusus $M$**
berada di titik percabangan. Halaman ini tidak memuat butir prosa tambahan di
luar diagram alur.
:::

*[Halaman sumber 12]{.source-locator}*
:::

::: {.source-page #d90-mit-l02-p013 data-source-page="13" data-source-order="8"}
## Perilaku Pengecualian

::: {.source-item #d90-mit-l02-p013-i001 data-source-page="13" data-source-order="1"}
- Jika struktur konveks begitu menguntungkan, apa sumber perilaku
  pengecualian/patologis?
:::

::: {.source-item #d90-mit-l02-p013-i002 data-source-page="13" data-source-order="2"}
- **Jawaban:** Beberapa operasi umum pada himpunan konveks tidak
  mempertahankan beberapa sifat dasar.
:::

::: {.source-item #d90-mit-l02-p013-i003 data-source-page="13" data-source-order="3"}
- **Contoh:** Himpunan konveks tertutup hasil transformasi linear tidak harus
  tertutup (berbeda dari himpunan kompak dan polihedral).

  - Selain itu, jumlah vektor dua himpunan konveks tertutup tidak harus tertutup.

::: {.source-figure #d90-mit-l02-p013-f001 data-source-page="13" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 13, $C_1$ dan $C_2$).** Pada bidang
$(x_1,x_2)$, $C_1$ adalah daerah di kuadran positif yang berada pada atau di
atas kurva $x_1x_2=1$, sedangkan $C_2$ adalah garis vertikal $x_1=0$. Sumbu
horizontal diberi label $x_1$, sumbu vertikal $x_2$, dan kedua himpunan diberi
definisi tepat berikut:

$$
C_1=\{(x_1,x_2)\mid x_1>0,\ x_2>0,\ x_1x_2\ge 1\},
$$

$$
C_2=\{(x_1,x_2)\mid x_1=0\}.
$$
:::
:::

::: {.source-item #d90-mit-l02-p013-i004 data-source-page="13" data-source-order="4"}
- Ini adalah salah satu alasan utama bagi kesulitan analitis dalam analisis
  konveks dan perilaku patologis dalam optimisasi konveks (serta karakter yang
  menguntungkan dari himpunan polihedral).
:::

*[Halaman sumber 13]{.source-locator}*
:::

::: {.edition-backmatter #d90-mit-l02-backmatter}
## Identitas sumber dan batas edisi

- Sumber: Dimitri P. Bertsekas, *Lecture Slides on Convex Analysis and
  Optimization*, berdasarkan MIT 6.253, Spring 2012.
- Batas tepat: PDF lengkap halaman 6-13; halaman 14 memulai topik terpisah
  **Pandangan Modern tentang Optimisasi Konveks** dan dikecualikan.
- Grafik: tujuh grafik sumber yang digunakan atas izin dihilangkan. Lokator
  halaman, label, formula, dan deskripsi semantik dipertahankan; tidak ada byte,
  potongan, atau tata letak Athena Scientific yang disalin.
- Hak: komponen turunan ini tetap CC BY-NC-SA 4.0, dengan kewajiban atribusi,
  penandaan perubahan, penggunaan nonkomersial, ShareAlike, dan nondukungan
  tetap berlaku.
- Batas ini tidak memuat latihan pembelajar, petunjuk, solusi, atau permukaan
  komputasi interaktif. Ini bukan keseluruhan kuliah MIT atau keseluruhan mata
  kuliah.
:::

*[Halaman sumber 6-13]{.source-locator}*
