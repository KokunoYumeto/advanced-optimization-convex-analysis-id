---
title: "Kuliah 3: Fungsi Konveks Terdiferensialkan dan Teorema Caratheodory"
subtitle: "MIT 6.253 - Edisi Indonesia, halaman sumber 29-38"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
lang: id-ID
date: "2026-08-23"
rights: "Terjemahan MIT OCW 6.253, CC BY-NC-SA 4.0"
description: "Rekonstruksi semantik yang dapat mengalir ulang dari Kuliah 3 lengkap, dengan pengenal stabil, formula, bukti, serta deskripsi grafik yang dapat diakses."
keywords:
  - fungsi konveks terdiferensialkan
  - syarat optimalitas
  - proyeksi
  - selubung konveks
  - Teorema Caratheodory
  - id-ID
---

::: {.edition-notice #d90-mit-l07-edition-notice}
## Tentang batas ini

Ini adalah rekonstruksi sumber semantik dan terjemahan bahasa Indonesia dari
Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare
6.253, Spring 2012, halaman PDF sumber 29-38. Kesepuluh halaman ini membentuk
**Kuliah 3** lengkap: fungsi konveks terdiferensialkan, syarat optimalitas,
proyeksi, selubung konveks dan afin, serta Teorema Caratheodory beserta
penerapannya. Halaman 39 memulai **Kuliah 4** dan tidak termasuk. Materi sumber
berada di bawah [CC BY-NC-SA
4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Empat blok grafik sumber sengaja tidak disalin karena rantai hak catatan
menyatakan grafik digunakan atas izin Athena Scientific. Setiap grafik diwakili
oleh lokator halaman yang tepat, deskripsi semantik yang disusun secara
independen, dan hubungan matematika yang dipertahankan. Tidak ada byte,
potongan, atau tata letak grafik sumber dalam edisi ini.

Dua koreksi yang dapat ditentukan dinyatakan secara terbuka. Tanda $\mapsto$
yang tercetak dalam deklarasi tipe fungsi pada halaman 30, 32, dan 34 diganti
dengan $\to$ karena deklarasi tersebut menyatakan domain dan kodomain, bukan
pemetaan unsur (O015-MIT-SEM-0007). Pada Teorema Proyeksi, frasa sumber
“minimum tunggal” dibetulkan
menjadi “titik peminimum tunggal”: proyeksi adalah titik yang meminimumkan
fungsi jarak kuadrat, bukan nilai minimum fungsi tersebut
(O015-MIT-SEM-0008). Saksi bahasa Inggris
mempertahankan kedua bentuk sumber.

Istilah teknis mengikuti bagian sebelumnya: *differentiable* menjadi
“terdiferensialkan”, *convex hull* menjadi “selubung konveks”, *affine hull*
menjadi “selubung afin”, *positive semidefinite* menjadi “semidefinit positif”,
dan *projection* menjadi “proyeksi”. Ejaan nama **Caratheodory** dipertahankan
sebagaimana tercetak pada judul sumber.

Bantuan produksi dan QA: **OpenAI Codex gpt-5.6-sol, Ultra**, atas arahan
pengguna repositori. Sistem tersebut bukan penulis sumber atau pemberi lisensi.
Tidak ada dukungan oleh MIT, Athena Scientific, atau penulis sumber yang
tersirat. Tinjauan bahasa manusia/penutur asli belum tercatat.

Pengenal stabil tetap melekat pada sepuluh halaman, enam belas butir tingkat
atas, tiga belas blok formula, dan empat deskripsi grafik meskipun HTML atau PDF
mengalir ulang. Empat belas butir bersarang mempertahankan urutan dan
hubungannya di dalam butir induk, tetapi tidak diklaim memiliki pengenal
tersendiri.
:::

::: {.source-page #d90-mit-l07-p029 data-source-page="29" data-source-order="1"}
## Kuliah 3 - Garis Besar Kuliah

::: {.source-item #d90-mit-l07-p029-i001 data-source-page="29" data-source-order="1"}
- Fungsi konveks terdiferensialkan
:::

::: {.source-item #d90-mit-l07-p029-i002 data-source-page="29" data-source-order="2"}
- Selubung konveks dan afin
:::

::: {.source-item #d90-mit-l07-p029-i003 data-source-page="29" data-source-order="3"}
- Teorema Caratheodory
:::

**Bacaan:** Bagian 1.1 dan 1.2.

*[Halaman sumber 29.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p030 data-source-page="30" data-source-order="2"}
## Fungsi Konveks Terdiferensialkan

::: {.source-figure #d90-mit-l07-p030-f001 data-source-page="30" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 30, garis pendukung orde pertama).**
Sebuah kurva konveks tebal diberi label $f(z)$ di atas sumbu horizontal dengan
variabel berjalan $z$. Garis vertikal putus-putus menandai $x$. Garis singgung
yang melalui kurva di $x$ terletak di bawah kurva dan diberi label
$f(x)+\nabla f(x)'(z-x)$.
:::

::: {.source-item #d90-mit-l07-p030-i001 data-source-page="30" data-source-order="1"}
- Misalkan $C\subset\mathbb{R}^n$ adalah himpunan konveks dan
  $f:\mathbb{R}^n\to\mathbb{R}$ terdiferensialkan pada $\mathbb{R}^n$.

  (a) Fungsi $f$ konveks pada $C$ jika dan hanya jika

      ::: {.source-display #d90-mit-l07-p030-d001 data-source-page="30" data-display-order="1"}
      $$
      f(z)\geq f(x)+(z-x)'\nabla f(x),
      \qquad \forall x,z\in C.
      $$
      :::

  (b) Jika ketaksamaan tersebut ketat setiap kali $x\neq z$, maka $f$ konveks
  ketat pada $C$.
:::

*[Halaman sumber 30.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p031 data-source-page="31" data-source-order="3"}
## Gagasan Bukti

::: {.source-figure #d90-mit-l07-p031-f001 data-source-page="31" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 31, dua panel gagasan bukti).** Panel
(a) menandai $x$, $z=\alpha x+(1-\alpha)y$, dan $y$ di bawah suatu kurva
konveks. Tali busur dari $(x,f(x))$ ke $(y,f(y))$ mempunyai tinggi
$\alpha f(x)+(1-\alpha)f(y)$ di $z$. Garis singgung pada $z$ diberi label pada
kedua titik ujung dengan $f(z)+(x-z)'\nabla f(z)$ dan
$f(z)+(y-z)'\nabla f(z)$. Panel (b) menandai $x$,
$x+\alpha(z-x)$, dan $z$ di bawah suatu kurva konveks. Pada $z$, konstruksi
garis potong diberi label
$f(x)+\bigl(f(x+\alpha(z-x))-f(x)\bigr)/\alpha$, sedangkan konstruksi garis
singgung di bawahnya diberi label $f(x)+(z-x)'\nabla f(x)$.
:::

*[Halaman sumber 31.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p032 data-source-page="32" data-source-order="4"}
## Syarat Optimalitas

::: {.source-item #d90-mit-l07-p032-i001 data-source-page="32" data-source-order="1"}
- Misalkan $C$ adalah subhimpunan konveks tak kosong dari $\mathbb{R}^n$ dan
  $f:\mathbb{R}^n\to\mathbb{R}$ konveks serta terdiferensialkan pada suatu
  himpunan terbuka yang memuat $C$. Maka vektor $x^*\in C$ meminimumkan $f$
  pada $C$ jika dan hanya jika

  ::: {.source-display #d90-mit-l07-p032-d001 data-source-page="32" data-display-order="1"}
  $$
  \nabla f(x^*)'(x-x^*)\geq 0,
  \qquad \forall x\in C.
  $$
  :::
:::

**Bukti:** Jika syarat tersebut berlaku, maka

::: {.source-display #d90-mit-l07-p032-d002 data-source-page="32" data-display-order="2"}
$$
f(x)\geq f(x^*)+(x-x^*)'\nabla f(x^*)\geq f(x^*),
\qquad \forall x\in C,
$$
:::

sehingga $x^*$ meminimumkan $f$ pada $C$.

Sebaliknya, andaikan untuk memperoleh kontradiksi bahwa $x^*$ meminimumkan $f$
pada $C$ dan $\nabla f(x^*)'(x-x^*)<0$ untuk suatu $x\in C$. Dari
keterdiferensialan, diperoleh

::: {.source-display #d90-mit-l07-p032-d003 data-source-page="32" data-display-order="3"}
$$
\lim_{\alpha\downarrow 0}
\frac{f\bigl(x^*+\alpha(x-x^*)\bigr)-f(x^*)}{\alpha}
=\nabla f(x^*)'(x-x^*)<0,
$$
:::

sehingga $f\bigl(x^*+\alpha(x-x^*)\bigr)$ berkurang secara ketat untuk
$\alpha>0$ yang cukup kecil; hal ini bertentangan dengan optimalitas $x^*$.
**Q.E.D.**

*[Halaman sumber 32.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p033 data-source-page="33" data-source-order="5"}
## Teorema Proyeksi

::: {.source-item #d90-mit-l07-p033-i001 data-source-page="33" data-source-order="1"}
- Misalkan $C$ adalah himpunan konveks tertutup tak kosong dalam
  $\mathbb{R}^n$.

  (a) Untuk setiap $z\in\mathbb{R}^n$, terdapat titik peminimum tunggal bagi

      ::: {.source-display #d90-mit-l07-p033-d001 data-source-page="33" data-display-order="1"}
      $$
      f(x)=\lVert z-x\rVert^2
      $$
      :::

      atas semua $x\in C$ (disebut *proyeksi $z$ pada $C$*).

  (b) $x^*$ adalah proyeksi $z$ jika dan hanya jika

      ::: {.source-display #d90-mit-l07-p033-d002 data-source-page="33" data-display-order="2"}
      $$
      (x-x^*)'(z-x^*)\leq 0,
      \qquad \forall x\in C.
      $$
      :::
:::

**Bukti:** (a) $f$ konveks ketat dan mempunyai himpunan aras kompak.

**(b)** Ini hanyalah syarat optimalitas perlu dan cukup

::: {.source-display #d90-mit-l07-p033-d003 data-source-page="33" data-display-order="3"}
$$
\nabla f(x^*)'(x-x^*)\geq 0,
\qquad \forall x\in C.
$$
:::

*[Halaman sumber 33.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p034 data-source-page="34" data-source-order="6"}
## Fungsi Konveks yang Terdiferensialkan Dua Kali

::: {.source-item #d90-mit-l07-p034-i001 data-source-page="34" data-source-order="1"}
- Misalkan $C$ adalah subhimpunan konveks dari $\mathbb{R}^n$ dan
  $f:\mathbb{R}^n\to\mathbb{R}$ terdiferensialkan dua kali secara kontinu
  pada $\mathbb{R}^n$.

  (a) Jika $\nabla^2f(x)$ semidefinit positif untuk setiap $x\in C$, maka $f$
  konveks pada $C$.

  (b) Jika $\nabla^2f(x)$ definit positif untuk setiap $x\in C$, maka $f$
  konveks ketat pada $C$.

  (c) Jika $C$ terbuka dan $f$ konveks pada $C$, maka $\nabla^2f(x)$
  semidefinit positif untuk setiap $x\in C$.
:::

**Bukti:** (a) Menurut Teorema Nilai Rata-rata, untuk $x,y\in C$,

::: {.source-display #d90-mit-l07-p034-d001 data-source-page="34" data-display-order="1"}
$$
f(y)=f(x)+(y-x)'\nabla f(x)
+\frac{1}{2}(y-x)'\nabla^2f\bigl(x+\alpha(y-x)\bigr)(y-x)
$$
:::

untuk suatu $\alpha\in[0,1]$. Dengan menggunakan sifat semidefinit positif dari
$\nabla^2f$, diperoleh

::: {.source-display #d90-mit-l07-p034-d002 data-source-page="34" data-display-order="2"}
$$
f(y)\geq f(x)+(y-x)'\nabla f(x),
\qquad \forall x,y\in C.
$$
:::

Dari hasil sebelumnya, $f$ konveks.

**(b)** Serupa dengan (a), diperoleh
$f(y)>f(x)+(y-x)'\nabla f(x)$ untuk setiap $x,y\in C$ dengan $x\neq y$, lalu
kita menggunakan hasil sebelumnya.

**(c)** Dengan kontradiksi ... serupa.

*[Halaman sumber 34.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p035 data-source-page="35" data-source-order="7"}
## Selubung Konveks dan Afin

::: {.source-item #d90-mit-l07-p035-i001 data-source-page="35" data-source-order="1"}
- Diberikan suatu himpunan $X\subseteq\mathbb{R}^n$:
:::

::: {.source-item #d90-mit-l07-p035-i002 data-source-page="35" data-source-order="2"}
- *Kombinasi konveks* unsur-unsur $X$ adalah vektor berbentuk
  $\sum_{i=1}^m\alpha_i x_i$, dengan $x_i\in X$, $\alpha_i\geq0$, dan
  $\sum_{i=1}^m\alpha_i=1$.
:::

::: {.source-item #d90-mit-l07-p035-i003 data-source-page="35" data-source-order="3"}
- *Selubung konveks* $X$, yang dilambangkan dengan
  $\operatorname{conv}(X)$, adalah irisan semua himpunan konveks yang memuat
  $X$. (Dapat ditunjukkan bahwa himpunan ini sama dengan himpunan semua
  kombinasi konveks dari $X$.)
:::

::: {.source-item #d90-mit-l07-p035-i004 data-source-page="35" data-source-order="4"}
- *Selubung afin* $X$, yang dilambangkan dengan $\operatorname{aff}(X)$,
  adalah irisan semua himpunan afin yang memuat $X$ (himpunan afin adalah
  himpunan berbentuk $\bar{x}+S$, dengan $S$ suatu subruang).
:::

::: {.source-item #d90-mit-l07-p035-i005 data-source-page="35" data-source-order="5"}
- *Kombinasi nonnegatif* unsur-unsur $X$ adalah vektor berbentuk
  $\sum_{i=1}^m\alpha_i x_i$, dengan $x_i\in X$ dan $\alpha_i\geq0$ untuk
  setiap $i$.
:::

::: {.source-item #d90-mit-l07-p035-i006 data-source-page="35" data-source-order="6"}
- *Kerucut yang dibangkitkan oleh $X$*, yang dilambangkan dengan
  $\operatorname{cone}(X)$, adalah himpunan semua kombinasi nonnegatif dari
  $X$:

  - Himpunan ini merupakan kerucut konveks yang memuat titik asal.
  - Himpunan ini tidak harus tertutup!
  - Jika $X$ adalah himpunan hingga, $\operatorname{cone}(X)$ tertutup (tidak
    mudah untuk ditunjukkan!).
:::

*[Halaman sumber 35.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p036 data-source-page="36" data-source-order="8"}
## Teorema Caratheodory

::: {.source-figure #d90-mit-l07-p036-f001 data-source-page="36" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 36, panel kerucut dan selubung
konveks).** Panel (a) menempatkan himpunan tak beraturan $X$ di antara dua
sinar dari titik asal $0$, dengan titik $x_1$ dan $x_2$ pada kedua sinar serta
vektor tak nol $x$ di dalam daerah berlabel $\operatorname{cone}(X)$. Panel
(b) menggambar segiempat berlabel $\operatorname{conv}(X)$ dengan titik sudut
$x_1,x_2,x_3,x_4$ dan sebuah titik $x$ di interiornya.
:::

::: {.source-item #d90-mit-l07-p036-i001 data-source-page="36" data-source-order="1"}
- Misalkan $X$ adalah subhimpunan tak kosong dari $\mathbb{R}^n$.

  (a) Setiap $x\neq0$ dalam $\operatorname{cone}(X)$ dapat dinyatakan sebagai
  kombinasi positif dari vektor-vektor $x_1,\ldots,x_m$ dalam $X$ yang bebas
  linear (sehingga $m\leq n$).

  (b) Setiap $x\notin X$ yang termasuk dalam $\operatorname{conv}(X)$ dapat
  dinyatakan sebagai kombinasi konveks dari vektor-vektor
  $x_1,\ldots,x_m$ dalam $X$ dengan $m\leq n+1$.
:::

*[Halaman sumber 36.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p037 data-source-page="37" data-source-order="9"}
## Bukti Teorema Caratheodory

(a) Misalkan $x$ adalah vektor tak nol dalam $\operatorname{cone}(X)$, dan
misalkan $m$ adalah bilangan bulat terkecil sedemikian sehingga $x$ berbentuk
$\sum_{i=1}^m\alpha_i x_i$, dengan $\alpha_i>0$ dan $x_i\in X$ untuk setiap
$i=1,\ldots,m$. Jika vektor-vektor $x_i$ bergantung linear, akan terdapat
$\lambda_1,\ldots,\lambda_m$, dengan

::: {.source-display #d90-mit-l07-p037-d001 data-source-page="37" data-display-order="1"}
$$
\sum_{i=1}^m\lambda_i x_i=0
$$
:::

dan setidaknya satu dari $\lambda_i$ positif. Tinjau

::: {.source-display #d90-mit-l07-p037-d002 data-source-page="37" data-display-order="2"}
$$
\sum_{i=1}^m(\alpha_i-\bar{\gamma}\lambda_i)x_i,
$$
:::

dengan $\bar{\gamma}$ adalah $\gamma$ terbesar sedemikian sehingga
$\alpha_i-\gamma\lambda_i\geq0$ untuk setiap $i$. Kombinasi ini memberikan
representasi $x$ sebagai kombinasi positif yang melibatkan kurang dari $m$
vektor dari $X$—sebuah kontradiksi. Oleh karena itu, $x_1,\ldots,x_m$ bebas
linear.

(b) Gunakan argumen “pengangkatan”: terapkan bagian (a) pada
$Y=\{(x,1)\mid x\in X\}$.

::: {.source-figure #d90-mit-l07-p037-f001 data-source-page="37" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 37, argumen pengangkatan).** Titik
asal berlabel $0$ berada di salinan bawah $\mathbb{R}^n$. Himpunan melengkung
$X$ dan titik $x$ terletak di bawah himpunan melengkung terangkat $Y$ dan titik
$(x,1)$ pada aras berlabel $1$. Sinar-sinar dari titik asal membentuk kerucut
pengangkatan, dan garis bantu putus-putus menghubungkan $x$ dengan $(x,1)$
serta menandai aras satuan. Label yang dipertahankan ialah
$0$, $1$, $\mathbb{R}^n$, $X$, $Y$, $x$, dan $(x,1)$.
:::

*[Halaman sumber 37.]{.source-locator}*
:::

::: {.source-page #d90-mit-l07-p038 data-source-page="38" data-source-order="10"}
## Penerapan Teorema Caratheodory

::: {.source-item #d90-mit-l07-p038-i001 data-source-page="38" data-source-order="1"}
- Selubung konveks suatu himpunan kompak bersifat kompak.

  **Bukti:** Misalkan $X$ kompak. Kita mengambil suatu barisan dalam
  $\operatorname{conv}(X)$ dan menunjukkan bahwa barisan itu mempunyai
  subbarisan konvergen yang limitnya berada dalam $\operatorname{conv}(X)$.

  Menurut Caratheodory, suatu barisan dalam $\operatorname{conv}(X)$ dapat
  dinyatakan sebagai
  $\left\{\sum_{i=1}^{n+1}\alpha_i^k x_i^k\right\}$, dengan untuk setiap $k$
  dan $i$, $\alpha_i^k\geq0$, $x_i^k\in X$, dan
  $\sum_{i=1}^{n+1}\alpha_i^k=1$. Karena barisan

  ::: {.source-display #d90-mit-l07-p038-d001 data-source-page="38" data-display-order="1"}
  $$
  \left\{
  (\alpha_1^k,\ldots,\alpha_{n+1}^k,x_1^k,\ldots,x_{n+1}^k)
  \right\}
  $$
  :::

  terbatas, barisan tersebut mempunyai titik limit

  ::: {.source-display #d90-mit-l07-p038-d002 data-source-page="38" data-display-order="2"}
  $$
  \left\{
  (\alpha_1,\ldots,\alpha_{n+1},x_1,\ldots,x_{n+1})
  \right\},
  $$
  :::

  yang harus memenuhi $\sum_{i=1}^{n+1}\alpha_i=1$, $\alpha_i\geq0$, dan
  $x_i\in X$ untuk setiap $i$. Vektor
  $\sum_{i=1}^{n+1}\alpha_i x_i$ termasuk dalam $\operatorname{conv}(X)$ dan
  merupakan titik limit dari
  $\left\{\sum_{i=1}^{n+1}\alpha_i^k x_i^k\right\}$; ini menunjukkan bahwa
  $\operatorname{conv}(X)$ kompak. **Q.E.D.**
:::

::: {.source-item #d90-mit-l07-p038-i002 data-source-page="38" data-source-order="2"}
- Perhatikan bahwa selubung konveks suatu himpunan tertutup tidak harus
  tertutup!
:::

*[Halaman sumber 38.]{.source-locator}*
:::
