---
title: "Kuliah 5: Kerucut Resesi dan Titik Peminimum"
subtitle: "MIT 6.253 - Edisi Indonesia, halaman sumber 50-63"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
lang: id-ID
date: "2026-08-24"
rights: "Terjemahan MIT OCW 6.253, CC BY-NC-SA 4.0"
description: "Rekonstruksi semantik yang dapat mengalir ulang dari Kuliah 5 lengkap, dengan pengenal stabil, formula, bukti, dan deskripsi gambar yang dapat diakses."
keywords:
  - kerucut resesi
  - ruang kelinieran
  - fungsi resesi
  - titik peminimum lokal dan global
  - keberadaan solusi optimal
  - id-ID
---

::: {.edition-notice #d90-mit-l09-edition-notice}
## Tentang batas ini

Ini adalah rekonstruksi sumber semantik dan terjemahan bahasa Indonesia dari
Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare
6.253, Spring 2012, halaman PDF sumber 50-63. Keempat belas halaman ini
membentuk **Kuliah 5** lengkap: kerucut resesi dan ruang kelinieran, arah
resesi fungsi konveks, peminimum lokal dan global, serta keberadaan solusi
optimal. Halaman 64 memulai **Kuliah 6** dan tidak termasuk. Materi sumber
berada di bawah [CC BY-NC-SA
4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Tujuh blok gambar sumber, yang seluruhnya mencakup dua belas panel, sengaja
tidak disalin karena rantai hak catatan menyatakan gambar digunakan atas izin
Athena Scientific. Setiap gambar diwakili oleh lokator halaman, deskripsi
semantik yang disusun secara independen, dan hubungan matematika yang
dipertahankan. Tidak ada byte, potongan, atau tata letak gambar sumber dalam
edisi ini.

Koreksi yang dapat ditentukan dinyatakan secara terbuka. Tanda $\mapsto$ pada
deklarasi tipe fungsi di halaman 56 dan 58-63 diganti dengan $\to$
(O015-MIT-SEM-0012). Frasa
“monotonically nondecreasing” di halaman 55 diganti dengan “tak-menaik” agar
sesuai dengan arah penurunan, definisi kerucut resesi, dan keenam panel pada
halaman 57 (O015-MIT-SEM-0013). Huruf $y$ pada simpulan halaman 57 diganti
dengan $d$, yaitu variabel yang dipakai oleh semua panel dan definisi
(O015-MIT-SEM-0014). Bentuk tercetak
$R_f=\{(d,0)\in R_{\operatorname{epi}(f)}\}$ di halaman 59 dilengkapi menjadi
$R_f=\{d\mid(d,0)\in R_{\operatorname{epi}(f)}\}$
(O015-MIT-SEM-0015). Definisi titik peminimum lokal halaman 60 dilengkapi
dengan kuantifikasi “untuk suatu $\epsilon>0$” (O015-MIT-SEM-0016). Teorema
Weierstrass halaman 61 diberi syarat kelayakan
$X\cap\operatorname{dom}(f)\neq\varnothing$ (O015-MIT-SEM-0017), dan frasa
tercetak yang tidak terbentuk “level sets of $f\cap X$” diganti dengan
himpunan sublevel terkendala
$\{x\in X\mid f(x)\leq\gamma\}$ (O015-MIT-SEM-0018). Pada halaman 60-63,
kata sumber *minimum/minima* yang menunjuk titik dibedakan sebagai “titik
peminimum” atau “himpunan titik peminimum”; “nilai minimum” dicadangkan untuk
nilai skalar (O015-MIT-SEM-0019). PDF sumber tetap menjadi saksi bagi semua
bentuk tercetak tersebut.

Empat sambungan atau notasi yang dipadatkan sumber ditangani secara
konservatif dan diberi label penjelasan edisi. Pada halaman 53, kasus $d=0$
serta alasan
$\bar{x}+d_k\in C$ untuk $k$ cukup besar dinyatakan sebelum mengambil limit.
Pada halaman 54, tanda $+$ pada dekomposisi dijelaskan sebagai jumlah
Minkowski. Pada halaman 59, rumus kemiringan dan gradien diberi domain yang
dinyatakan dalam bacaan sumber, sedangkan aturan kalkulus dibaca hanya ketika
operasi di ruas kiri tetap proper. Pada halaman 62, barisan $\gamma_k$
dipilih ketat di atas $f^*$ agar setiap himpunan pendekatan tak kosong. Tidak
ada generalisasi baru yang diklaim sebagai bagian dari sumber.

Istilah teknis mengikuti bagian sebelumnya: *recession cone* menjadi
“kerucut resesi”, *direction of recession* menjadi “arah resesi”, *lineality
space* menjadi “ruang kelinieran”, *level set* menjadi “himpunan sublevel”,
*proper function* menjadi “fungsi proper”, *feasible* menjadi “layak”, dan
*coercivity* menjadi “koersivitas”. Titik yang mengoptimalkan disebut “titik
peminimum”, sedangkan nilai objektif skalarnya disebut “nilai minimum”.
Notasi $R_C$, $L_C$, $R_f$, $L_f$,
$r_f$, $\operatorname{epi}$, dan $\operatorname{dom}$ dipertahankan.

Bantuan produksi dan QA: **OpenAI Codex gpt-5.6-sol, Ultra**, atas arahan
pengguna repositori. Sistem tersebut bukan penulis sumber atau pemberi
lisensi. Tidak ada dukungan oleh MIT, Athena Scientific, atau penulis sumber
yang tersirat. Tinjauan bahasa manusia/penutur asli belum tercatat.

Pengenal stabil tetap melekat pada empat belas halaman, empat puluh satu butir
tingkat atas, sembilan belas blok formula, dan tujuh deskripsi gambar meskipun
HTML atau PDF mengalir ulang. Tujuh belas butir bersarang mempertahankan
urutan dan hubungannya di dalam butir induk, tetapi tidak diklaim memiliki
pengenal tersendiri. Dua contoh sumber dipertahankan.
:::

::: {.source-page #d90-mit-l09-p050 data-source-page="50" data-source-order="1"}
## Kuliah 5 - Garis Besar Kuliah

::: {.source-item #d90-mit-l09-p050-i001 data-source-page="50" data-source-order="1"}
- Kerucut resesi dan ruang kelinieran
:::

::: {.source-item #d90-mit-l09-p050-i002 data-source-page="50" data-source-order="2"}
- Arah resesi fungsi konveks
:::

::: {.source-item #d90-mit-l09-p050-i003 data-source-page="50" data-source-order="3"}
- Titik peminimum lokal dan global
:::

::: {.source-item #d90-mit-l09-p050-i004 data-source-page="50" data-source-order="4"}
- Keberadaan solusi optimal
:::

**Bacaan:** Bagian 1.4, 3.1, dan 3.2.

*[Halaman sumber 50.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p051 data-source-page="51" data-source-order="2"}
## Kerucut Resesi Himpunan Konveks

::: {.source-item #d90-mit-l09-p051-i001 data-source-page="51" data-source-order="1"}
- Diberikan himpunan konveks tak kosong $C$. Vektor $d$ adalah **arah
  resesi** jika, mulai dari sebarang $x$ di $C$ dan bergerak tanpa batas
  sepanjang $d$, kita tidak pernah melintasi batas relatif $C$ menuju titik
  di luar $C$:

  ::: {.source-display #d90-mit-l09-p051-d001 data-source-page="51" data-display-order="1"}
  $$
  x+\alpha d\in C,
  \qquad \forall x\in C,
  \quad \forall\alpha\geq0.
  $$
  :::
:::

::: {.source-figure #d90-mit-l09-p051-f001 data-source-page="51" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 51, kerucut dan sinar resesi).**
Himpunan konveks $C$ memanjang tak terbatas ke satu arah. Dari asal $0$,
daerah berbentuk kerucut yang diarsir menyatakan $R_C$ dan memuat vektor
$d$. Dari titik $x\in C$, sinar sejajar $d$ melalui titik $x+\alpha d$ tetap
berada di dalam $C$ untuk setiap $\alpha\geq0$.
:::

::: {.source-item #d90-mit-l09-p051-i002 data-source-page="51" data-source-order="2"}
- **Kerucut resesi** $C$, yang dinyatakan dengan $R_C$, adalah himpunan semua
  arah resesi.
:::

::: {.source-item #d90-mit-l09-p051-i003 data-source-page="51" data-source-order="3"}
- $R_C$ adalah kerucut yang memuat titik asal.
:::

*[Halaman sumber 51.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p052 data-source-page="52" data-source-order="3"}
## Teorema Kerucut Resesi

::: {.source-item #d90-mit-l09-p052-i001 data-source-page="52" data-source-order="1"}
- Misalkan $C$ adalah himpunan konveks tertutup tak kosong.

  (a) Kerucut resesi $R_C$ adalah kerucut konveks tertutup.

  (b) Vektor $d$ termasuk dalam $R_C$ jika dan hanya jika terdapat suatu
  vektor $x\in C$ sedemikian sehingga $x+\alpha d\in C$ untuk semua
  $\alpha\geq0$.

  (c) $R_C$ memuat arah tak nol jika dan hanya jika $C$ tak terbatas.

  (d) Kerucut resesi $C$ dan $\operatorname{ri}(C)$ sama.

  (e) Jika $D$ adalah himpunan konveks tertutup lain dengan
  $C\cap D\neq\varnothing$, maka

  ::: {.source-display #d90-mit-l09-p052-d001 data-source-page="52" data-display-order="1"}
  $$
  R_{C\cap D}=R_C\cap R_D.
  $$
  :::

  Secara lebih umum, untuk koleksi himpunan konveks tertutup
  $C_i$, $i\in I$, dengan $I$ sebarang dan
  $\bigcap_{i\in I}C_i\neq\varnothing$, berlaku

  ::: {.source-display #d90-mit-l09-p052-d002 data-source-page="52" data-display-order="2"}
  $$
  R_{\bigcap_{i\in I}C_i}
  =\bigcap_{i\in I}R_{C_i}.
  $$
  :::
:::

*[Halaman sumber 52.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p053 data-source-page="53" data-source-order="4"}
## Bukti Bagian (b)

::: {.source-figure #d90-mit-l09-p053-f001 data-source-page="53" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 53, pendekatan arah dari titik
tetap).** Di dalam $C$, titik-titik $z_1=x+d,z_2,z_3,\ldots$ bergerak
sepanjang sinar yang berawal di $x$. Dari titik tetap $\bar{x}$, vektor
$d_1,d_2,d_3,\ldots$ mengarah ke titik-titik pada ruas menuju $z_k$ dan
mempunyai panjang $\lVert d\rVert$. Titik-titik
$\bar{x}+d_k$ mendekati $\bar{x}+d$ ketika arah dari $\bar{x}$ ke $z_k$
mendekati arah $d$.
:::

::: {.source-item #d90-mit-l09-p053-i001 data-source-page="53" data-source-order="1"}
- Misalkan $d\neq0$ dan terdapat vektor $x\in C$ dengan
  $x+\alpha d\in C$ untuk semua $\alpha\geq0$. Tetapkan
  $\bar{x}\in C$ dan $\alpha>0$; akan ditunjukkan bahwa
  $\bar{x}+\alpha d\in C$. Dengan menskalakan $d$, cukup ditunjukkan bahwa
  $\bar{x}+d\in C$. Untuk $k=1,2,\ldots$, tetapkan

  ::: {.source-display #d90-mit-l09-p053-d001 data-source-page="53" data-display-order="1"}
  $$
  z_k=x+kd,
  \qquad
  d_k=\frac{z_k-\bar{x}}{\lVert z_k-\bar{x}\rVert}\,\lVert d\rVert.
  $$
  :::

  Kita mempunyai

  ::: {.source-display #d90-mit-l09-p053-d002 data-source-page="53" data-display-order="2"}
  $$
  \begin{aligned}
  \frac{d_k}{\lVert d\rVert}
  &=\frac{\lVert z_k-x\rVert}{\lVert z_k-\bar{x}\rVert}
    \frac{d}{\lVert d\rVert}
    +\frac{x-\bar{x}}{\lVert z_k-\bar{x}\rVert},\\
  \frac{\lVert z_k-x\rVert}{\lVert z_k-\bar{x}\rVert}
  &\longrightarrow1,
  \qquad
  \frac{x-\bar{x}}{\lVert z_k-\bar{x}\rVert}
  \longrightarrow0.
  \end{aligned}
  $$
  :::

  Jadi $d_k\to d$ dan $\bar{x}+d_k\to\bar{x}+d$. Gunakan kekonveksan dan
  ketertutupan $C$ untuk menyimpulkan bahwa $\bar{x}+d\in C$.
:::

**Penjelasan edisi:** Kasus $d=0$ langsung. Untuk $d\neq0$ dan $k$ cukup
besar, $\lVert z_k-\bar{x}\rVert\geq\lVert d\rVert$. Dengan
$\theta_k=\lVert d\rVert/\lVert z_k-\bar{x}\rVert\in[0,1]$, berlaku
$\bar{x}+d_k=(1-\theta_k)\bar{x}+\theta_k z_k\in C$. Inilah langkah
kekonveksan yang dipadatkan sumber; ketertutupan kemudian membolehkan
pengambilan limit.

*[Halaman sumber 53.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p054 data-source-page="54" data-source-order="5"}
## Ruang Kelinieran

::: {.source-item #d90-mit-l09-p054-i001 data-source-page="54" data-source-order="1"}
- **Ruang kelinieran** himpunan konveks $C$, yang dinyatakan dengan $L_C$,
  adalah subruang semua vektor $d$ sedemikian sehingga $d\in R_C$ dan
  $-d\in R_C$:

  ::: {.source-display #d90-mit-l09-p054-d001 data-source-page="54" data-display-order="1"}
  $$
  L_C=R_C\cap(-R_C).
  $$
  :::
:::

::: {.source-item #d90-mit-l09-p054-i002 data-source-page="54" data-source-order="2"}
- Jika $d\in L_C$, seluruh garis yang didefinisikan oleh $d$, mulai dari
  sebarang titik di $C$, termuat dalam $C$.
:::

::: {.source-item #d90-mit-l09-p054-i003 data-source-page="54" data-source-order="3"}
- **Dekomposisi Himpunan Konveks:** Misalkan $C$ adalah subhimpunan konveks
  tak kosong dari $\mathbb{R}^n$. Maka

  ::: {.source-display #d90-mit-l09-p054-d002 data-source-page="54" data-display-order="2"}
  $$
  C=L_C+\bigl(C\cap L_C^\perp\bigr).
  $$
  :::

  **Penjelasan edisi:** Tanda $+$ menyatakan jumlah Minkowski: setiap
  $x\in C$ ditulis sebagai jumlah satu vektor dalam $L_C$ dan satu vektor
  dalam $C\cap L_C^\perp$.
:::

::: {.source-item #d90-mit-l09-p054-i004 data-source-page="54" data-source-order="4"}
- Dekomposisi ini memungkinkan kita membuktikan sifat $C$ pada
  $C\cap L_C^\perp$, lalu memperluasnya ke $C$.
:::

::: {.source-item #d90-mit-l09-p054-i005 data-source-page="54" data-source-order="5"}
- Pernyataan tersebut juga benar jika $L_C$ diganti oleh subruang
  $S\subseteq L_C$.
:::

::: {.source-figure #d90-mit-l09-p054-f001 data-source-page="54" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 54, dekomposisi terhadap
subruang).** Subruang $S$ melalui asal $0$ sejajar dengan arah memanjang
himpunan $C$, sedangkan $S^\perp$ memotongnya secara transversal. Titik
$z\in C\cap S^\perp$ dan $d\in S$ menjumlah menjadi titik $x=z+d\in C$;
seluruh pita $C$ diperoleh dengan menambahkan arah-arah dalam $S$ pada
penampang $C\cap S^\perp$.
:::

*[Halaman sumber 54.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p055 data-source-page="55" data-source-order="6"}
## Arah Resesi Suatu Fungsi

::: {.source-item #d90-mit-l09-p055-i001 data-source-page="55" data-source-order="1"}
- Kita hendak mencirikan arah penurunan monoton fungsi konveks.
:::

::: {.source-item #d90-mit-l09-p055-i002 data-source-page="55" data-source-order="2"}
- Beberapa pengamatan geometri dasar:

  - “Arah horizontal” dalam kerucut resesi epigraf fungsi konveks $f$ adalah
    arah yang membuat himpunan sublevel tidak terbatas.
  - Sepanjang arah tersebut, himpunan sublevel
    $\{x\mid f(x)\leq\gamma\}$ tidak terbatas dan $f$ tak-menaik.
:::

::: {.source-item #d90-mit-l09-p055-i003 data-source-page="55" data-source-order="3"}
- Arah-arah tersebut adalah arah resesi $f$.
:::

::: {.source-figure #d90-mit-l09-p055-f001 data-source-page="55" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 55, irisan epigraf).** Epigraf
$\operatorname{epi}(f)$ berada di atas grafik $f$. Bidang horizontal pada
ketinggian $\gamma$ menghasilkan irisan
$\{(x,\gamma)\mid f(x)\leq\gamma\}$, yang proyeksinya adalah himpunan sublevel
$V_\gamma=\{x\mid f(x)\leq\gamma\}$. Sebuah arah horizontal $(d,0)$ di
kerucut resesi epigraf ditampilkan sebagai arah memanjang yang juga membuat
$V_\gamma$ tak terbatas.
:::

**Catatan koreksi edisi (O015-MIT-SEM-0013):** Sumber tercetak menyebut $f$
“monotonically nondecreasing”. Edisi ini memakai “tak-menaik” karena arah
yang sedang dicirikan adalah arah penurunan dan halaman 57 menunjukkan
$r_f(d)\leq0$ tepat pada arah resesi.

*[Halaman sumber 55.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p056 data-source-page="56" data-source-order="7"}
## Kerucut Resesi Himpunan Sublevel

::: {.source-item #d90-mit-l09-p056-i001 data-source-page="56" data-source-order="1"}
- **Proposisi:** Misalkan
  $f:\mathbb{R}^n\to(-\infty,\infty]$ adalah fungsi konveks proper tertutup,
  dan tinjau himpunan sublevel $V_\gamma=\{x\mid f(x)\leq\gamma\}$, dengan
  $\gamma$ suatu skalar. Maka:

  (a) Semua himpunan sublevel tak kosong $V_\gamma$ mempunyai kerucut resesi
  yang sama:

  ::: {.source-display #d90-mit-l09-p056-d001 data-source-page="56" data-display-order="1"}
  $$
  R_{V_\gamma}
  =\{d\mid(d,0)\in R_{\operatorname{epi}(f)}\}.
  $$
  :::

  (b) Jika satu himpunan sublevel tak kosong $V_\gamma$ kompak, maka semua
  himpunan sublevel kompak.
:::

**Bukti:** Bagian (a) menerjemahkan secara matematis fakta bahwa

::: {.source-display #d90-mit-l09-p056-d002 data-source-page="56" data-display-order="2"}
$$
R_{V_\gamma}
=\{\text{arah resesi “horizontal” dari }\operatorname{epi}(f)\}.
$$
:::

Bagian (b) mengikuti dari (a).

**Catatan koreksi edisi (O015-MIT-SEM-0012):** Deklarasi tipe fungsi pada
halaman ini dan halaman 58-63 tercetak dengan $\mapsto$; semuanya dinyatakan
dengan $\to$ dalam edisi ini.

*[Halaman sumber 56.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p057 data-source-page="57" data-source-order="8"}
## Perilaku Penurunan Fungsi Konveks

::: {.source-figure #d90-mit-l09-p057-f001 data-source-page="57" data-figure-disposition="omitted-source-graphic" data-panel-count="6"}
**Deskripsi gambar sumber (halaman sumber 57, enam panel perilaku sepanjang
sinar).** Setiap panel memplot $f(x+\alpha d)$ terhadap $\alpha\geq0$ dan
menandai nilai awal $f(x)$.

**Panel (a).** Kurva turun secara konveks dan kemiringannya menuju nol secara
asimtotik; $r_f(d)=0$.

**Panel (b).** Kurva terus turun dengan kemiringan asimtotik negatif;
$r_f(d)<0$.

**Panel (c).** Kurva turun lalu menjadi konstan; $r_f(d)=0$.

**Panel (d).** Kurva konstan pada $f(x)$; $r_f(d)=0$.

**Panel (e).** Kurva naik; $r_f(d)>0$.

**Panel (f).** Kurva mula-mula turun, mencapai lembah, lalu naik;
$r_f(d)>0$.
:::

::: {.source-item #d90-mit-l09-p057-i001 data-source-page="57" data-source-order="1"}
- $d$ adalah arah resesi pada panel (a)-(d).
:::

::: {.source-item #d90-mit-l09-p057-i002 data-source-page="57" data-source-order="2"}
- Perilaku ini tidak bergantung pada titik awal $x$, selama
  $x\in\operatorname{dom}(f)$.
:::

**Catatan koreksi edisi (O015-MIT-SEM-0014):** Kalimat sumber di bawah
gambar menyebut $y$, sedangkan keenam panel dan seluruh definisi memakai
$d$. Edisi ini mempertahankan variabel $d$.

*[Halaman sumber 57.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p058 data-source-page="58" data-source-order="9"}
## Kerucut Resesi Fungsi Konveks

::: {.source-item #d90-mit-l09-p058-i001 data-source-page="58" data-source-order="1"}
- Untuk fungsi konveks proper tertutup
  $f:\mathbb{R}^n\to(-\infty,\infty]$, kerucut resesi bersama dari semua
  himpunan sublevel tak kosong
  $V_\gamma=\{x\mid f(x)\leq\gamma\}$, $\gamma\in\mathbb{R}$, disebut
  **kerucut resesi** $f$ dan dinyatakan dengan $R_f$.
:::

::: {.source-figure #d90-mit-l09-p058-f001 data-source-page="58" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 58, kerucut bersama himpunan
sublevel).** Beberapa kontur himpunan sublevel $f$ yang bersarang memanjang tak
terbatas ke arah yang sama. Dari asal $0$, daerah kerucut $R_f$ memuat tepat arah-arah yang
dapat ditambahkan tanpa meninggalkan setiap himpunan sublevel tak kosong.
:::

::: {.source-item #d90-mit-l09-p058-i002 data-source-page="58" data-source-order="2"}
- Terminologi:

  - $d\in R_f$: arah resesi $f$.
  - $L_f=R_f\cap(-R_f)$: ruang kelinieran $f$.
  - $d\in L_f$: arah kekonstanan $f$.
:::

::: {.source-item #d90-mit-l09-p058-i003 data-source-page="58" data-source-order="3"}
- **Contoh:** Untuk fungsi kuadratik semidefinit positif

  ::: {.source-display #d90-mit-l09-p058-d001 data-source-page="58" data-display-order="1"}
  $$
  f(x)=x^\top Qx+a^\top x+b,
  $$
  :::

  kerucut resesi dan ruang kekonstanannya adalah

  ::: {.source-display #d90-mit-l09-p058-d002 data-source-page="58" data-display-order="2"}
  $$
  R_f=\{d\mid Qd=0,\ a^\top d\leq0\},
  \qquad
  L_f=\{d\mid Qd=0,\ a^\top d=0\}.
  $$
  :::
:::

*[Halaman sumber 58.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p059 data-source-page="59" data-source-order="10"}
## Fungsi Resesi

::: {.source-item #d90-mit-l09-p059-i001 data-source-page="59" data-source-order="1"}
- Fungsi $r_f:\mathbb{R}^n\to(-\infty,\infty]$ yang epigrafnya adalah
  $R_{\operatorname{epi}(f)}$ disebut **fungsi resesi** $f$.
:::

::: {.source-item #d90-mit-l09-p059-i002 data-source-page="59" data-source-order="2"}
- Fungsi ini mencirikan kerucut resesi:

  ::: {.source-display #d90-mit-l09-p059-d001 data-source-page="59" data-display-order="1"}
  $$
  \begin{aligned}
  R_f&=\{d\mid r_f(d)\leq0\},
  &L_f&=\{d\mid r_f(d)=r_f(-d)=0\},\\
  R_f&=\{d\mid(d,0)\in R_{\operatorname{epi}(f)}\}.
  \end{aligned}
  $$
  :::
:::

::: {.source-item #d90-mit-l09-p059-i003 data-source-page="59" data-source-order="3"}
- Dapat ditunjukkan bahwa, untuk setiap $x\in\operatorname{dom}(f)$ dan
  $d\in\mathbb{R}^n$,

  ::: {.source-display #d90-mit-l09-p059-d002 data-source-page="59" data-display-order="2"}
  $$
  r_f(d)
  =\sup_{\alpha>0}\frac{f(x+\alpha d)-f(x)}{\alpha}
  =\lim_{\alpha\to\infty}
   \frac{f(x+\alpha d)-f(x)}{\alpha}.
  $$
  :::
:::

::: {.source-item #d90-mit-l09-p059-i004 data-source-page="59" data-source-order="4"}
- Jadi $r_f(d)$ adalah “kemiringan asimtotik” $f$ dalam arah $d$. Bahkan,
  jika $f:\mathbb{R}^n\to\mathbb{R}$ terdiferensialkan,

  ::: {.source-display #d90-mit-l09-p059-d003 data-source-page="59" data-display-order="3"}
  $$
  r_f(d)=\lim_{\alpha\to\infty}
  \nabla f(x+\alpha d)^\top d,
  \qquad \forall x,d\in\mathbb{R}^n.
  $$
  :::
:::

::: {.source-item #d90-mit-l09-p059-i005 data-source-page="59" data-source-order="5"}
- Kalkulus fungsi resesi:

  ::: {.source-display #d90-mit-l09-p059-d004 data-source-page="59" data-display-order="4"}
  $$
  \begin{aligned}
  r_{f_1+\cdots+f_m}(d)
  &=r_{f_1}(d)+\cdots+r_{f_m}(d),\\
  r_{\sup_{i\in I}f_i}(d)
  &=\sup_{i\in I}r_{f_i}(d).
  \end{aligned}
  $$
  :::
:::

**Catatan koreksi edisi (O015-MIT-SEM-0015):** Bentuk sumber setelah
display pertama hanya menaruh pasangan $(d,0)$ di dalam kurung himpunan dan
tidak mengikat variabel $d$. Bentuk pembentuk-himpunan yang lengkap digunakan
di atas.

**Penjelasan edisi:** Bacaan sumber §1.4 menyatakan rumus kemiringan untuk
$x\in\operatorname{dom}(f)$ dan $d\in\mathbb{R}^n$, serta rumus gradien
untuk fungsi konveks terdiferensialkan bernilai real. Aturan jumlah berlaku
untuk fungsi-fungsi konveks proper tertutup ketika jumlahnya proper; aturan
supremum dibaca secara analog untuk keluarga fungsi konveks proper tertutup
ketika supremumnya proper. Kualifikasi ini mencegah rumus ringkas pada slide
dipakai di luar domainnya; tidak ada aturan yang lebih luas diklaim di sini.

*[Halaman sumber 59.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p060 data-source-page="60" data-source-order="11"}
## Titik Peminimum Lokal dan Global

::: {.source-item #d90-mit-l09-p060-i001 data-source-page="60" data-source-order="1"}
- Tinjau masalah meminimumkan
  $f:\mathbb{R}^n\to(-\infty,\infty]$ di atas himpunan
  $X\subseteq\mathbb{R}^n$.
:::

::: {.source-item #d90-mit-l09-p060-i002 data-source-page="60" data-source-order="2"}
- Titik $x$ **layak** jika $x\in X\cap\operatorname{dom}(f)$.
:::

::: {.source-item #d90-mit-l09-p060-i003 data-source-page="60" data-source-order="3"}
- Titik $x^*$ adalah **titik peminimum (global)** $f$ di atas $X$ jika $x^*$ layak
  dan $f(x^*)=\inf_{x\in X}f(x)$.
:::

::: {.source-item #d90-mit-l09-p060-i004 data-source-page="60" data-source-order="4"}
- Titik $x^*$ adalah **titik peminimum lokal** $f$ di atas $X$ jika, untuk suatu
  $\epsilon>0$, titik $x^*$ meminimumkan $f$ pada
  $X\cap\{x\mid\lVert x-x^*\rVert\leq\epsilon\}$.
:::

**Proposisi:** Jika $X$ konveks dan $f$ konveks, maka:

  (a) Titik peminimum lokal $f$ di atas $X$ juga merupakan titik peminimum
  global $f$ di atas $X$.

  (b) Jika $f$ konveks ketat, terdapat paling banyak satu titik peminimum
  global $f$ di atas $X$.

::: {.source-figure #d90-mit-l09-p060-f001 data-source-page="60" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 60, ruas tali busur
kekonveksan).** Grafik konveks $f$ memuat titik pada $\bar{x}$ dan $x^*$.
Tali busur di antara nilai $f(\bar{x})$ dan $f(x^*)$ mempunyai tinggi
$\alpha f(x^*)+(1-\alpha)f(\bar{x})$ pada titik
$\alpha x^*+(1-\alpha)\bar{x}$, sedangkan nilai grafik
$f(\alpha x^*+(1-\alpha)\bar{x})$ tidak lebih tinggi. Hubungan ini adalah
mekanisme yang mengubah minimalitas lokal menjadi global.
:::

**Catatan koreksi edisi (O015-MIT-SEM-0016):** Sumber menampilkan bola
berjari-jari $\epsilon$ tetapi tidak menyatakan kuantifikasinya. Frasa “untuk
suatu $\epsilon>0$” ditambahkan agar definisi titik peminimum lokal lengkap.

**Catatan terminologi edisi (O015-MIT-SEM-0019):** Pada halaman 60-63,
*minimum/minima* yang menunjuk titik diterjemahkan sebagai “titik peminimum”
atau “himpunan titik peminimum”. “Nilai minimum” hanya menunjuk nilai skalar.

*[Halaman sumber 60.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p061 data-source-page="61" data-source-order="12"}
## Keberadaan Solusi Optimal

::: {.source-item #d90-mit-l09-p061-i001 data-source-page="61" data-source-order="1"}
- Himpunan titik peminimum fungsi proper
  $f:\mathbb{R}^n\to(-\infty,\infty]$ adalah irisan semua himpunan sublevelnya
  yang tak kosong.
:::

::: {.source-item #d90-mit-l09-p061-i002 data-source-page="61" data-source-order="2"}
- Himpunan titik peminimum $f$ tak kosong dan kompak jika himpunan-himpunan sublevel
  $f$ kompak.
:::

::: {.source-item #d90-mit-l09-p061-i003 data-source-page="61" data-source-order="3"}
- **Perluasan Teorema Weierstrass:** Himpunan titik peminimum $f$ di atas $X$ tak
  kosong dan kompak jika $X$ tertutup, $f$ semikontinu bawah pada $X$,
  $X\cap\operatorname{dom}(f)\neq\varnothing$, dan salah satu syarat berikut
  berlaku:

  (1) $X$ terbatas.

  (2) Suatu himpunan
  $\{x\in X\mid f(x)\leq\gamma\}$ tak kosong dan terbatas.

  (3) Untuk setiap barisan $\{x_k\}\subseteq X$ dengan
  $\lVert x_k\rVert\to\infty$, berlaku
  $\lim_{k\to\infty}f(x_k)=+\infty$; ini adalah sifat koersivitas.
:::

**Bukti (notasi diperbaiki):** Dalam semua kasus, himpunan sublevel terkendala
$\{x\in X\mid f(x)\leq\gamma\}$ yang relevan tertutup dan terbatas, sehingga
kompak. **Q.E.D.**

**Catatan koreksi edisi:** Syarat kelayakan ditambahkan dalam
O015-MIT-SEM-0017; tanpa titik layak, himpunan titik peminimum tidak mungkin tak
kosong. Frasa sumber “level sets of $f\cap X$” diganti dengan himpunan
sublevel terkendala yang ditulis eksplisit (O015-MIT-SEM-0018), karena irisan
fungsi dengan himpunan bukan objek yang terdefinisi.

*[Halaman sumber 61.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p062 data-source-page="62" data-source-order="13"}
## Keberadaan Solusi - Kasus Konveks

::: {.source-item #d90-mit-l09-p062-i001 data-source-page="62" data-source-order="1"}
- **Teorema Weierstrass yang dikhususkan untuk fungsi konveks:** Misalkan
  $X$ adalah subhimpunan konveks tertutup dari $\mathbb{R}^n$, dan
  $f:\mathbb{R}^n\to(-\infty,\infty]$ adalah fungsi konveks tertutup dengan
  $X\cap\operatorname{dom}(f)\neq\varnothing$. Himpunan titik peminimum $f$ di
  atas $X$ tak kosong dan kompak jika dan hanya jika $X$ dan $f$ tidak
  mempunyai arah resesi tak nol yang sama.
:::

**Bukti:** Misalkan $f^*=\inf_{x\in X}f(x)$ dan perhatikan bahwa
$f^*<\infty$ karena $X\cap\operatorname{dom}(f)\neq\varnothing$. Ambil
barisan skalar $\{\gamma_k\}$ dengan $\gamma_k>f^*$ untuk setiap $k$ dan
$\gamma_k\downarrow f^*$, lalu tinjau himpunan

::: {.source-display #d90-mit-l09-p062-d001 data-source-page="62" data-display-order="1"}
$$
V_k=\{x\mid f(x)\leq\gamma_k\}.
$$
:::

Himpunan titik peminimum $f$ di atas $X$ adalah

::: {.source-display #d90-mit-l09-p062-d002 data-source-page="62" data-display-order="2"}
$$
X^*=\bigcap_{k=1}^{\infty}(X\cap V_k).
$$
:::

Himpunan-himpunan $X\cap V_k$ tak kosong dan mempunyai
$R_X\cap R_f$ sebagai kerucut resesi bersama; kerucut ini juga merupakan
kerucut resesi $X^*$ ketika $X^*\neq\varnothing$. Jadi $X^*$ tak kosong dan
kompak jika dan hanya jika

::: {.source-display #d90-mit-l09-p062-d003 data-source-page="62" data-display-order="3"}
$$
R_X\cap R_f=\{0\}.
$$
:::

**Q.E.D.**

**Penjelasan edisi:** Pemilihan $\gamma_k>f^*$ dinyatakan eksplisit agar
$X\cap V_k$ tak kosong untuk setiap $k$; sumber memadatkannya dalam notasi
$\gamma_k\downarrow f^*$.

*[Halaman sumber 62.]{.source-locator}*
:::

::: {.source-page #d90-mit-l09-p063 data-source-page="63" data-source-order="14"}
## Keberadaan Solusi untuk Jumlah Fungsi

::: {.source-item #d90-mit-l09-p063-i001 data-source-page="63" data-source-order="1"}
- Misalkan $f_i:\mathbb{R}^n\to(-\infty,\infty]$, $i=1,\ldots,m$, adalah
  fungsi konveks proper tertutup sedemikian sehingga fungsi

  ::: {.source-display #d90-mit-l09-p063-d001 data-source-page="63" data-display-order="1"}
  $$
  f=f_1+\cdots+f_m
  $$
  :::

  proper. Andaikan satu fungsi $f_i$ memenuhi
  $r_{f_i}(d)=+\infty$ untuk semua $d\neq0$. Maka himpunan titik peminimum $f$ tak
  kosong dan kompak.
:::

::: {.source-item #d90-mit-l09-p063-i002 data-source-page="63" data-source-order="2"}
- **Bukti:** Untuk semua $d\neq0$, berlaku
  $r_f(d)=\sum_{i=1}^{m}r_{f_i}(d)=+\infty$. Jadi $f$ tidak mempunyai arah
  resesi tak nol. **Q.E.D.**
:::

::: {.source-item #d90-mit-l09-p063-i003 data-source-page="63" data-source-order="3"}
- Pernyataan tersebut juga benar untuk $f=\max\{f_1,\ldots,f_m\}$.
:::

::: {.source-item #d90-mit-l09-p063-i004 data-source-page="63" data-source-order="4"}
- **Contoh penerapan:** Jika salah satu $f_i$ adalah fungsi kuadratik definit
  positif, himpunan titik peminimum jumlah $f$ tak kosong dan kompak.
:::

::: {.source-item #d90-mit-l09-p063-i005 data-source-page="63" data-source-order="5"}
- Selain itu, $f$ mempunyai titik peminimum tunggal karena fungsi kuadratik definit
  positif itu konveks ketat, sehingga $f$ konveks ketat.
:::

*[Halaman sumber 63.]{.source-locator}*
:::
