---
title: "Kuliah 2: Landasan Himpunan dan Fungsi Konveks"
subtitle: "MIT 6.253 - Edisi Indonesia, halaman sumber 20-28"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
lang: id-ID
date: "2026-08-23"
rights: "Terjemahan MIT OCW 6.253, CC BY-NC-SA 4.0"
description: "Rekonstruksi semantik yang dapat mengalir ulang dari Kuliah 2 lengkap, dengan pengenal stabil, formula, proposisi, bukti, dan deskripsi grafik yang dapat diakses."
keywords:
  - himpunan konveks
  - fungsi konveks
  - epigraf
  - semikontinuitas bawah
  - id-ID
---

::: {.edition-notice #d90-mit-l06-edition-notice}
## Tentang batas ini

Ini adalah rekonstruksi sumber semantik dan terjemahan bahasa Indonesia dari
Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare
6.253, Spring 2012, halaman PDF sumber 20-28. Kesembilan halaman ini membentuk
**Kuliah 2** lengkap: konvensi matematika, himpunan dan fungsi konveks, epigraf,
fungsi bernilai real diperluas, ketertutupan dan semikontinuitas, serta cara
mengenali fungsi konveks. Halaman 29 memulai **Kuliah 3** dan tidak termasuk.
Materi sumber berada di bawah [CC BY-NC-SA
4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Lima blok grafik sumber sengaja tidak disalin karena rantai hak catatan
menyatakan grafik digunakan atas izin Athena Scientific. Setiap grafik diwakili
oleh lokator halaman yang tepat, deskripsi semantik, dan hubungan matematika
yang dipertahankan. Tidak ada byte, potongan, atau tata letak grafik sumber
dalam edisi ini.

Dua normalisasi notasi ditandai secara terbuka. Tanda $\mapsto$ yang dicetak
dalam beberapa deklarasi tipe fungsi diganti dengan $\to$ karena deklarasi
tersebut menyatakan domain dan kodomain, bukan pemetaan unsur
(O015-MIT-SEM-0005). Pada definisi konveks ketat, parameter $a$ yang tercetak
diganti dengan $\alpha$ agar sama dengan parameter ketaksamaan yang baru saja
didefinisikan (O015-MIT-SEM-0006). Saksi bahasa Inggris mempertahankan kedua
bentuk sumber.

Istilah teknis konsisten dengan bagian sebelumnya: *epigraph* menjadi
“epigraf”, *effective domain* menjadi “domain efektif”, *lower
semicontinuous* menjadi “semikontinu bawah”, *affine* menjadi “afin”, dan
*positive semidefinite* menjadi “semidefinit positif”. Istilah **proper** dan
**tak proper** dipertahankan sebagai istilah teknis dan langsung didefinisikan.

Bantuan produksi dan QA: **OpenAI Codex gpt-5.6-sol, Ultra**, atas arahan
pengguna repositori. Sistem tersebut bukan penulis sumber atau pemberi lisensi.
Tidak ada dukungan oleh MIT, Athena Scientific, atau penulis sumber yang
tersirat. Tinjauan bahasa manusia/penutur asli belum tercatat.

Pengenal stabil tetap melekat pada sembilan halaman, tiga puluh dua butir
tingkat atas, dua belas blok formula, dan lima deskripsi grafik meskipun HTML
atau PDF mengalir ulang. Tujuh belas butir bersarang mempertahankan urutan dan
hubungannya di dalam butir induk, tetapi tidak diklaim memiliki pengenal
tersendiri.
:::

::: {.source-page #d90-mit-l06-p020 data-source-page="20" data-source-order="1"}
## Kuliah 2 - Garis Besar Kuliah

::: {.source-item #d90-mit-l06-p020-i001 data-source-page="20" data-source-order="1"}
- Himpunan dan fungsi konveks
:::

::: {.source-item #d90-mit-l06-p020-i002 data-source-page="20" data-source-order="2"}
- Epigraf
:::

::: {.source-item #d90-mit-l06-p020-i003 data-source-page="20" data-source-order="3"}
- Fungsi konveks tertutup
:::

::: {.source-item #d90-mit-l06-p020-i004 data-source-page="20" data-source-order="4"}
- Mengenali fungsi konveks
:::

**Bacaan:** Bagian 1.1.

*[Halaman sumber 20.]{.source-locator}*
:::

::: {.source-page #d90-mit-l06-p021 data-source-page="21" data-source-order="2"}
## Beberapa Konvensi Matematika

::: {.source-item #d90-mit-l06-p021-i001 data-source-page="21" data-source-order="1"}
- Seluruh pembahasan kita berlangsung di $\mathbb{R}^n$, yaitu ruang semua
  $n$-tupel.

  ::: {.source-display #d90-mit-l06-p021-d001 data-source-page="21" data-display-order="1"}
  $$
  x=(x_1,\ldots,x_n).
  $$
  :::
:::

::: {.source-item #d90-mit-l06-p021-i002 data-source-page="21" data-source-order="2"}
- Semua vektor dianggap sebagai vektor kolom.
:::

::: {.source-item #d90-mit-l06-p021-i003 data-source-page="21" data-source-order="3"}
- Tanda “$'$” menyatakan transpos, sehingga $x'$ menyatakan vektor baris.
:::

::: {.source-item #d90-mit-l06-p021-i004 data-source-page="21" data-source-order="4"}
- $x'y$ adalah hasil kali dalam $\sum_{i=1}^n x_i y_i$ dari vektor $x$ dan
  $y$.
:::

::: {.source-item #d90-mit-l06-p021-i005 data-source-page="21" data-source-order="5"}
- $\lVert x\rVert=\sqrt{x'x}$ adalah norma (Euclid) dari $x$. Kita hampir
  selalu memakai norma ini.
:::

::: {.source-item #d90-mit-l06-p021-i006 data-source-page="21" data-source-order="6"}
- Lihat buku teks untuk ikhtisar latar belakang aljabar linear dan analisis real
  yang akan kita gunakan, khususnya:

  - Definisi $\sup$ dan $\inf$ dari suatu himpunan bilangan real
  - Kekonvergenan barisan (definisi $\liminf$ dan $\limsup$ untuk barisan
    bilangan real, serta definisi limit barisan vektor)
  - Himpunan terbuka, tertutup, dan kompak beserta sifat-sifatnya
  - Definisi dan sifat diferensiasi
:::

*[Halaman sumber 21.]{.source-locator}*
:::

::: {.source-page #d90-mit-l06-p022 data-source-page="22" data-source-order="3"}
## Himpunan Konveks

::: {.source-figure #d90-mit-l06-p022-f001 data-source-page="22" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 22, himpunan konveks dan
nonkonveks).** Komposit empat panel membandingkan ruas garis antara titik
berlabel $x$ dan $y$. Pada daerah konveks kiri atas, setiap titik
$\alpha x+(1-\alpha)y$, $0\leq\alpha\leq1$, tetap berada di dalam daerah.
Pada daerah berlekuk kanan atas, sebagian ruas keluar dari himpunan. Poligon
konveks kiri bawah memuat seluruh ruas. Dua oval terpisah di kanan bawah
menempatkan $x$ dan $y$ pada komponen berbeda, sehingga ruas penghubung keluar
dari himpunan. Grafik sumber dihilangkan karena batas hak di atas.
:::

::: {.source-item #d90-mit-l06-p022-i001 data-source-page="22" data-source-order="1"}
- Subhimpunan $C$ dari $\mathbb{R}^n$ disebut konveks jika

  ::: {.source-display #d90-mit-l06-p022-d001 data-source-page="22" data-display-order="1"}
  $$
  \alpha x+(1-\alpha)y\in C,
  \qquad
  \forall x,y\in C,\quad \forall\alpha\in[0,1].
  $$
  :::
:::

::: {.source-item #d90-mit-l06-p022-i002 data-source-page="22" data-source-order="2"}
- Operasi yang mempertahankan kekonveksan

  - Irisan, perkalian skalar, penjumlahan vektor, penutupan, interior, dan
    transformasi linear
:::

::: {.source-item #d90-mit-l06-p022-i003 data-source-page="22" data-source-order="3"}
- Himpunan konveks khusus:

  - **Himpunan polihedral:** himpunan tak kosong berbentuk

    ::: {.source-display #d90-mit-l06-p022-d002 data-source-page="22" data-display-order="2"}
    $$
    \{x\mid a_j'x\leq b_j, j=1,\ldots,r\}
    $$
    :::

    (selalu konveks dan tertutup, tetapi tidak selalu terbatas)
  - **Kerucut:** himpunan $C$ sedemikian sehingga $\lambda x\in C$ untuk
    setiap $\lambda>0$ dan $x\in C$ (tidak selalu konveks atau tertutup)
:::

*[Halaman sumber 22.]{.source-locator}*
:::

::: {.source-page #d90-mit-l06-p023 data-source-page="23" data-source-order="4"}
## Fungsi Konveks

::: {.source-figure #d90-mit-l06-p023-f001 data-source-page="23" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 23, uji tali busur).** Di atas
interval $C$, grafik menandai $x$, $y$, dan $\alpha x+(1-\alpha)y$. Tali
busur menghubungkan $(x,f(x))$ dan $(y,f(y))$. Pada titik interpolasi, nilai
kurva $f(\alpha x+(1-\alpha)y)$ berada pada atau di bawah tinggi tali busur
$\alpha f(x)+(1-\alpha)f(y)$.
:::

::: {.source-item #d90-mit-l06-p023-i001 data-source-page="23" data-source-order="1"}
- Misalkan $C$ adalah subhimpunan konveks dari $\mathbb{R}^n$. Fungsi
  $f:C\to\mathbb{R}$ disebut konveks jika, untuk setiap $\alpha\in[0,1]$,

  ::: {.source-display #d90-mit-l06-p023-d001 data-source-page="23" data-display-order="1"}
  $$
  f\bigl(\alpha x+(1-\alpha)y\bigr)
  \leq \alpha f(x)+(1-\alpha)f(y),
  \qquad \forall x,y\in C.
  $$
  :::

  Jika ketaksamaan itu ketat untuk setiap $\alpha\in(0,1)$ dan $x\neq y$,
  maka $f$ disebut konveks ketat pada $C$.
:::

::: {.source-item #d90-mit-l06-p023-i002 data-source-page="23" data-source-order="2"}
- Jika $f$ adalah fungsi konveks, semua himpunan subarasnya
  $\{x\in C\mid f(x)\leq\gamma\}$ dan
  $\{x\in C\mid f(x)<\gamma\}$, dengan $\gamma$ suatu skalar, bersifat
  konveks.
:::

*[Halaman sumber 23.]{.source-locator}*
:::

::: {.source-page #d90-mit-l06-p024 data-source-page="24" data-source-order="5"}
## Fungsi Bernilai Real Diperluas

::: {.source-figure #d90-mit-l06-p024-f001 data-source-page="24" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 24, perbandingan epigraf).** Panel
kiri menampilkan fungsi konveks pada satu interval domain efektif; epigraf
berarsir di atas grafiknya bersifat konveks. Panel kanan menampilkan fungsi
nonkonveks pada dua interval domain efektif yang terpisah; epigraf berarsirnya
tidak konveks. Kedua panel mempertahankan label $f(x)$, $x$,
$\operatorname{dom}(f)$, dan **Epigraf**.
:::

::: {.source-item #d90-mit-l06-p024-i001 data-source-page="24" data-source-order="1"}
- Epigraf fungsi $f:X\to[-\infty,\infty]$ adalah subhimpunan
  $\mathbb{R}^{n+1}$ yang diberikan oleh

  ::: {.source-display #d90-mit-l06-p024-d001 data-source-page="24" data-display-order="1"}
  $$
  \operatorname{epi}(f)
  =
  \{(x,w)\mid x\in X,\ w\in\mathbb{R},\ f(x)\leq w\}.
  $$
  :::
:::

::: {.source-item #d90-mit-l06-p024-i002 data-source-page="24" data-source-order="2"}
- Domain efektif $f$ adalah himpunan

  ::: {.source-display #d90-mit-l06-p024-d002 data-source-page="24" data-display-order="2"}
  $$
  \operatorname{dom}(f)=\{x\in X\mid f(x)<\infty\}.
  $$
  :::
:::

::: {.source-item #d90-mit-l06-p024-i003 data-source-page="24" data-source-order="3"}
- Kita menyebut $f$ konveks jika $\operatorname{epi}(f)$ merupakan himpunan
  konveks. Jika $f(x)\in\mathbb{R}$ untuk setiap $x\in X$ dan $X$ konveks,
  definisi ini “berimpit” dengan definisi sebelumnya.
:::

::: {.source-item #d90-mit-l06-p024-i004 data-source-page="24" data-source-order="4"}
- Kita menyebut $f$ tertutup jika $\operatorname{epi}(f)$ merupakan himpunan
  tertutup.
:::

::: {.source-item #d90-mit-l06-p024-i005 data-source-page="24" data-source-order="5"}
- Kita menyebut $f$ semikontinu bawah pada vektor $x\in X$ jika
  $f(x)\leq\liminf_{k\to\infty}f(x_k)$ untuk setiap barisan
  $\{x_k\}\subset X$ dengan $x_k\to x$.
:::

*[Halaman sumber 24.]{.source-locator}*
:::

::: {.source-page #d90-mit-l06-p025 data-source-page="25" data-source-order="6"}
## Ketertutupan dan Semikontinuitas I

::: {.source-item #d90-mit-l06-p025-i001 data-source-page="25" data-source-order="1"}
- **Proposisi:** Untuk fungsi
  $f:\mathbb{R}^n\to[-\infty,\infty]$, pernyataan berikut ekuivalen:

  (i) $V_\gamma=\{x\mid f(x)\leq\gamma\}$ tertutup untuk setiap
  $\gamma\in\mathbb{R}$.

  (ii) $f$ semikontinu bawah pada setiap $x\in\mathbb{R}^n$.

  (iii) $f$ tertutup.

  ::: {.source-figure #d90-mit-l06-p025-f001 data-source-page="25" data-figure-disposition="omitted-source-graphic"}
  **Deskripsi grafik sumber (halaman sumber 25, epigraf dan himpunan
  subaras).** Epigraf berarsir berada di atas grafik fungsi. Garis horizontal
  pada tinggi $\gamma$ memotong grafik, dan proyeksi vertikal putus-putus
  menandai himpunan subaras $\{x\mid f(x)\leq\gamma\}$ pada sumbu $x$.
  Label yang dipertahankan adalah $f(x)$, $\operatorname{epi}(f)$,
  $\gamma$, $x$, dan himpunan subaras tersebut.
  :::
:::

::: {.source-item #d90-mit-l06-p025-i002 data-source-page="25" data-source-order="2"}
- **(ii) $\Rightarrow$ (iii):** Misalkan
  $\{(x_k,w_k)\}\subset\operatorname{epi}(f)$ dengan
  $(x_k,w_k)\to(\bar{x},\bar{w})$. Maka $f(x_k)\leq w_k$, dan

  ::: {.source-display #d90-mit-l06-p025-d001 data-source-page="25" data-display-order="1"}
  $$
  f(\bar{x})
  \leq\liminf_{k\to\infty}f(x_k)
  \leq\bar{w},
  $$
  :::

  sehingga $(\bar{x},\bar{w})\in\operatorname{epi}(f)$.
:::

::: {.source-item #d90-mit-l06-p025-i003 data-source-page="25" data-source-order="3"}
- **(iii) $\Rightarrow$ (i):** Misalkan
  $\{x_k\}\subset V_\gamma$ dan $x_k\to\bar{x}$. Maka
  $(x_k,\gamma)\in\operatorname{epi}(f)$ dan
  $(x_k,\gamma)\to(\bar{x},\gamma)$, sehingga
  $(\bar{x},\gamma)\in\operatorname{epi}(f)$ dan
  $\bar{x}\in V_\gamma$.
:::

::: {.source-item #d90-mit-l06-p025-i004 data-source-page="25" data-source-order="4"}
- **(i) $\Rightarrow$ (ii):** Jika $x_k\to\bar{x}$ dan
  $f(\bar{x})>\gamma>\liminf_{k\to\infty}f(x_k)$, ambil subbarisan
  $\{x_k\}_{\mathcal K}\to\bar{x}$ dengan $f(x_k)\leq\gamma$; ini
  bertentangan dengan ketertutupan $V_\gamma$.
:::

*[Halaman sumber 25.]{.source-locator}*
:::

::: {.source-page #d90-mit-l06-p026 data-source-page="26" data-source-order="7"}
## Ketertutupan dan Semikontinuitas II

::: {.source-item #d90-mit-l06-p026-i001 data-source-page="26" data-source-order="1"}
- Semikontinuitas bawah suatu fungsi merupakan sifat yang “bergantung pada
  domain”, sedangkan ketertutupan bukan:

  - Jika domain fungsi diubah tanpa mengubah epigrafnya, sifat semikontinuitas
    bawahnya dapat berubah.
  - **Contoh:** Definisikan $f:(0,1)\to[-\infty,\infty]$ dan
    $\hat f:[0,1]\to[-\infty,\infty]$ melalui

    ::: {.source-display #d90-mit-l06-p026-d001 data-source-page="26" data-display-order="1"}
    $$
    f(x)=0,\qquad \forall x\in(0,1),
    $$
    :::

    ::: {.source-display #d90-mit-l06-p026-d002 data-source-page="26" data-display-order="2"}
    $$
    \hat f(x)=
    \begin{cases}
    0,&x\in(0,1),\\
    \infty,&x=0\text{ atau }x=1.
    \end{cases}
    $$
    :::

    Maka $f$ dan $\hat f$ mempunyai epigraf yang sama, dan keduanya tidak
    tertutup. Namun, $f$ semikontinu bawah sedangkan $\hat f$ tidak.
:::

::: {.source-item #d90-mit-l06-p026-i002 data-source-page="26" data-source-order="2"}
- Perhatikan bahwa:

  - Jika $f$ semikontinu bawah pada setiap
    $x\in\operatorname{dom}(f)$, $f$ belum tentu tertutup.
  - Jika $f$ tertutup, $\operatorname{dom}(f)$ belum tentu tertutup.
:::

::: {.source-item #d90-mit-l06-p026-i003 data-source-page="26" data-source-order="3"}
- **Proposisi:** Misalkan $f:X\to[-\infty,\infty]$ adalah suatu fungsi.
  Jika $\operatorname{dom}(f)$ tertutup dan $f$ semikontinu bawah pada setiap
  $x\in\operatorname{dom}(f)$, maka $f$ tertutup.
:::

*[Halaman sumber 26.]{.source-locator}*
:::

::: {.source-page #d90-mit-l06-p027 data-source-page="27" data-source-order="8"}
## Fungsi Konveks Proper dan Tak Proper

::: {.source-figure #d90-mit-l06-p027-f001 data-source-page="27" data-figure-disposition="omitted-source-graphic"}
**Deskripsi grafik sumber (halaman sumber 27, fungsi tak proper).** Dua panel
mengarsir epigraf di atas domain efektif berbentuk interval. Epigraf kiri
menghilangkan satu batas vertikal, yang ditandai garis putus-putus, dan diberi
label **Fungsi Tak Proper yang Tidak Tertutup**. Epigraf kanan menyertakan batas
vertikalnya dan diberi label **Fungsi Tak Proper yang Tertutup**. Kedua panel
mempertahankan $f(x)$, $x$, $\operatorname{epi}(f)$, dan
$\operatorname{dom}(f)$.
:::

::: {.source-item #d90-mit-l06-p027-i001 data-source-page="27" data-source-order="1"}
- Kita menyebut $f$ **proper** jika $f(x)<\infty$ untuk setidaknya satu
  $x\in X$ dan $f(x)>-\infty$ untuk setiap $x\in X$; $f$ disebut **tak
  proper** jika tidak proper.
:::

::: {.source-item #d90-mit-l06-p027-i002 data-source-page="27" data-source-order="2"}
- Perhatikan bahwa $f$ proper jika dan hanya jika epigrafnya tak kosong dan
  tidak memuat sebuah “garis vertikal”.
:::

::: {.source-item #d90-mit-l06-p027-i003 data-source-page="27" data-source-order="3"}
- Fungsi konveks tertutup yang tak proper mempunyai sifat sangat khusus: pada
  setiap titik nilainya tak hingga ($\infty$ atau $-\infty$).
:::

*[Halaman sumber 27.]{.source-locator}*
:::

::: {.source-page #d90-mit-l06-p028 data-source-page="28" data-source-order="9"}
## Mengenali Fungsi Konveks

::: {.source-item #d90-mit-l06-p028-i001 data-source-page="28" data-source-order="1"}
- Beberapa kelas penting fungsi konveks elementer: fungsi afin, fungsi kuadratik
  semidefinit positif, fungsi norma, dan sebagainya.
:::

::: {.source-item #d90-mit-l06-p028-i002 data-source-page="28" data-source-order="2"}
- **Proposisi:**

  (a) Fungsi $g:\mathbb{R}^n\to(-\infty,\infty]$ yang diberikan oleh

      ::: {.source-display #d90-mit-l06-p028-d001 data-source-page="28" data-display-order="1"}
      $$
      g(x)=\lambda_1f_1(x)+\cdots+\lambda_mf_m(x),
      \qquad \lambda_i>0,
      $$
      :::

      bersifat konveks jika $f_1,\ldots,f_m$ masing-masing bersifat konveks,
      dan bersifat tertutup jika semuanya tertutup.

  (b) Fungsi $g:\mathbb{R}^n\to(-\infty,\infty]$ yang diberikan oleh

      ::: {.source-display #d90-mit-l06-p028-d002 data-source-page="28" data-display-order="2"}
      $$
      g(x)=f(Ax),
      $$
      :::

      dengan $A$ matriks berukuran $m\times n$, bersifat konveks jika $f$
      konveks, dan bersifat tertutup jika $f$ tertutup.

  (c) Misalkan $f_i:\mathbb{R}^n\to(-\infty,\infty]$, $i\in I$, dengan
  $I$ sembarang himpunan indeks. Fungsi
  $g:\mathbb{R}^n\to(-\infty,\infty]$ yang diberikan oleh

      ::: {.source-display #d90-mit-l06-p028-d003 data-source-page="28" data-display-order="3"}
      $$
      g(x)=\sup_{i\in I}f_i(x)
      $$
      :::

      bersifat konveks jika semua $f_i$ konveks, dan bersifat tertutup jika
      semua $f_i$ tertutup.
:::

*[Halaman sumber 28.]{.source-locator}*
:::
