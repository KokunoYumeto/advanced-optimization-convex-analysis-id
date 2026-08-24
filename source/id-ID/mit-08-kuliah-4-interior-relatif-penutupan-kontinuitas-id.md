---
title: "Kuliah 4: Interior Relatif, Penutupan, dan Kontinuitas"
subtitle: "MIT 6.253 - Edisi Indonesia, halaman sumber 39-49"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
lang: id-ID
date: "2026-08-24"
rights: "Terjemahan MIT OCW 6.253, CC BY-NC-SA 4.0"
description: "Rekonstruksi semantik yang dapat mengalir ulang dari Kuliah 4 lengkap, dengan pengenal stabil, formula, bukti, dan deskripsi gambar yang dapat diakses."
keywords:
  - interior relatif
  - penutupan
  - transformasi linear
  - kontinuitas fungsi konveks
  - penutupan fungsi
  - id-ID
---

::: {.edition-notice #d90-mit-l08-edition-notice}
## Tentang batas ini

Ini adalah rekonstruksi sumber semantik dan terjemahan bahasa Indonesia dari
Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare
6.253, Spring 2012, halaman PDF sumber 39-49. Kesebelas halaman ini membentuk
**Kuliah 4** lengkap: interior relatif dan penutupan, kalkulus keduanya,
kontinuitas fungsi konveks, serta penutupan fungsi. Halaman 50 memulai
**Kuliah 5** dan tidak termasuk. Materi sumber berada di bawah [CC BY-NC-SA
4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Lima gambar sumber sengaja tidak disalin karena rantai hak catatan menyatakan
gambar digunakan atas izin Athena Scientific. Setiap gambar diwakili oleh
lokator halaman, deskripsi semantik yang disusun secara independen, dan
hubungan matematika yang dipertahankan. Tidak ada byte, potongan, atau tata
letak gambar sumber dalam edisi ini.

Tiga koreksi yang dapat ditentukan dinyatakan secara terbuka. Tanda
$\mapsto$ yang tercetak dalam deklarasi tipe fungsi pada halaman 42, 48, dan
49 diganti dengan $\to$ karena deklarasi itu menyatakan domain dan kodomain
(O015-MIT-SEM-0009). Klaim ringkasan pada halaman 43 bahwa interior relatif
dan penutupan berkomutasi dengan praimaji linear diberi syarat kelayakan
$A^{-1}(\operatorname{ri}C)\neq\varnothing$, atau setara dengan
$\operatorname{range}(A)\cap\operatorname{ri}(C)\neq\varnothing$
(O015-MIT-SEM-0010). Intuisi halaman 45 bahwa transformasi linear memetakan
bola menjadi bola diganti dengan pernyataan lingkungan relatif yang benar;
transformasi linear umum dapat menghasilkan elipsoid atau citra degenerat
(O015-MIT-SEM-0011). Saksi bahasa Inggris mempertahankan ketiga bentuk sumber.

Beberapa sambungan bukti ditambahkan dan ditandai sebagai penjelasan edisi:
translasi tanpa mengurangi keumuman serta simpulan konstruksi simpleks pada
halaman 41, arah-arah Lema Perpanjangan, simpulan bagian (b) halaman 44,
tujuan berbeda dari dua contoh lawan pada halaman 46, dan kasus $x_k=0$
sebelum normalisasi pada halaman 48. Tidak ada hasil baru yang diklaim sebagai
bagian dari sumber.

Istilah teknis mengikuti bagian sebelumnya: *relative interior* menjadi
“interior relatif”, *closure* menjadi “penutupan”, *affine hull* menjadi
“selubung afin”, *inverse image* menjadi “praimaji”, *fiber* menjadi “serat”,
dan *proper function* menjadi “fungsi proper”. Notasi $\operatorname{ri}$,
$\operatorname{cl}$, $\operatorname{aff}$, $\operatorname{dom}$, dan
$\check{\operatorname{cl}}$ dipertahankan.

Bantuan produksi dan QA: **OpenAI Codex gpt-5.6-sol, Ultra**, atas arahan
pengguna repositori. Sistem tersebut bukan penulis sumber atau pemberi lisensi.
Tidak ada dukungan oleh MIT, Athena Scientific, atau penulis sumber yang
tersirat. Tinjauan bahasa manusia/penutur asli belum tercatat.

Pengenal stabil tetap melekat pada sebelas halaman, dua puluh tujuh butir
tingkat atas, dua puluh enam blok formula, dan lima deskripsi gambar meskipun
HTML atau PDF mengalir ulang. Enam belas butir bersarang mempertahankan urutan
dan hubungannya di dalam butir induk, tetapi tidak diklaim memiliki pengenal
tersendiri.
:::

::: {.source-page #d90-mit-l08-p039 data-source-page="39" data-source-order="1"}
## Kuliah 4 - Garis Besar Kuliah

::: {.source-item #d90-mit-l08-p039-i001 data-source-page="39" data-source-order="1"}
- Interior relatif dan penutupan
:::

::: {.source-item #d90-mit-l08-p039-i002 data-source-page="39" data-source-order="2"}
- Aljabar interior relatif dan penutupan
:::

::: {.source-item #d90-mit-l08-p039-i003 data-source-page="39" data-source-order="3"}
- Kontinuitas fungsi konveks
:::

::: {.source-item #d90-mit-l08-p039-i004 data-source-page="39" data-source-order="4"}
- Penutupan fungsi
:::

**Bacaan:** Bagian 1.3.

*[Halaman sumber 39.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p040 data-source-page="40" data-source-order="2"}
## Interior Relatif

::: {.source-item #d90-mit-l08-p040-i001 data-source-page="40" data-source-order="1"}
- Titik $x$ adalah titik interior relatif dari $C$ jika $x$ merupakan titik
  interior dari $C$ relatif terhadap $\operatorname{aff}(C)$.
:::

::: {.source-item #d90-mit-l08-p040-i002 data-source-page="40" data-source-order="2"}
- $\operatorname{ri}(C)$ menyatakan interior relatif dari $C$, yaitu himpunan
  semua titik interior relatif dari $C$.
:::

::: {.source-item #d90-mit-l08-p040-i003 data-source-page="40" data-source-order="3"}
- **Prinsip Ruas Garis:** Jika $C$ adalah himpunan konveks,
  $x\in\operatorname{ri}(C)$, dan $\bar{x}\in\operatorname{cl}(C)$, maka
  semua titik pada ruas garis yang menghubungkan $x$ dan $\bar{x}$, kecuali
  mungkin $\bar{x}$, termasuk dalam $\operatorname{ri}(C)$.
:::

::: {.source-figure #d90-mit-l08-p040-f001 data-source-page="40" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 40, bola relatif homotetik).** Di
dalam himpunan konveks $C$, sebuah bola relatif $S$ berjari-jari $\epsilon$
berpusat di titik interior relatif $x$. Titik $\bar{x}$ berada pada penutupan
$C$. Untuk $x_\alpha=\alpha x+(1-\alpha)\bar{x}$ dengan
$\alpha\in(0,1]$, citra homotetik bola tersebut adalah bola relatif
$S_\alpha$ berjari-jari $\alpha\epsilon$ yang berpusat di $x_\alpha$ dan
tetap berada dalam $C$.
:::

::: {.source-item #d90-mit-l08-p040-i004 data-source-page="40" data-source-order="4"}
- **Bukti untuk kasus $\bar{x}\in C$:** konstruksi bola homotetik pada gambar
  menunjukkan bahwa setiap $x_\alpha$ dengan $\alpha\in(0,1]$ mempunyai
  lingkungan relatif yang berada dalam $C$.
:::

::: {.source-item #d90-mit-l08-p040-i005 data-source-page="40" data-source-order="5"}
- **Bukti untuk kasus $\bar{x}\notin C$:** ambil barisan
  $\{x_k\}\subset C$ dengan $x_k\to\bar{x}$, lalu terapkan argumen bola
  homotetik yang sama dan ambil limit.
:::

*[Halaman sumber 40.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p041 data-source-page="41" data-source-order="3"}
## Hasil-Hasil Utama Tambahan

::: {.source-item #d90-mit-l08-p041-i001 data-source-page="41" data-source-order="1"}
- Misalkan $C$ adalah himpunan konveks tak kosong.

  (a) $\operatorname{ri}(C)$ adalah himpunan konveks tak kosong dan mempunyai
  selubung afin yang sama dengan $C$.

  (b) **Lema Perpanjangan:** $x\in\operatorname{ri}(C)$ jika dan hanya jika
  setiap ruas garis di dalam $C$ yang mempunyai $x$ sebagai salah satu titik
  ujung dapat diperpanjang melewati $x$ tanpa keluar dari $C$.
:::

::: {.source-figure #d90-mit-l08-p041-f001 data-source-page="41" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 41, simpleks koordinat positif).**
Setelah asal $0$ ditempatkan dalam $C$, vektor $z_1$ dan $z_2$ yang bebas
linear terletak di $C$ dan merentang $\operatorname{aff}(C)$ dalam contoh dua
dimensi. Daerah $X$ di antara asal dan kedua vektor menggambarkan bagian
simpleks dengan koefisien positif dan jumlah koefisien kurang dari satu.
:::

**Bukti (a):** Tanpa mengurangi keumuman, translasikan $C$ sehingga $0\in C$.
Pilih $m$ vektor bebas linear $z_1,\ldots,z_m\in C$, dengan $m$ dimensi
$\operatorname{aff}(C)$, dan definisikan

::: {.source-display #d90-mit-l08-p041-d001 data-source-page="41" data-display-order="1"}
$$
X=\left\{
\sum_{i=1}^{m}\alpha_i z_i
\ \middle|\
\substack{
\sum_{i=1}^{m}\alpha_i<1,\\
\alpha_i>0,\ i=1,\ldots,m
}
\right\}.
$$
:::

Karena $0,z_1,\ldots,z_m\in C$ dan $C$ konveks, maka $X\subset C$.
Koefisien yang semuanya positif dan berjumlah kurang dari satu membentuk
himpunan terbuka relatif tak kosong di ruang yang direntang oleh
$z_1,\ldots,z_m$; jadi $\operatorname{ri}(C)$ tak kosong dan mempunyai
selubung afin yang sama dengan $C$. Kekonveksan $\operatorname{ri}(C)$
mengikuti dari Prinsip Ruas Garis.

**Bukti (b):** Jika $x\in\operatorname{ri}(C)$, lingkungan relatif di sekitar
$x$ memungkinkan setiap ruas yang berakhir di $x$ diperpanjang sedikit
melewati $x$. Sebaliknya, ambil $\bar{x}\in\operatorname{ri}(C)$ dari bagian
(a). Jika ruas dari $\bar{x}$ ke $x$ dapat diperpanjang melewati $x$ hingga
suatu titik dalam $C$, Prinsip Ruas Garis menempatkan $x$ dalam
$\operatorname{ri}(C)$.

*[Halaman sumber 41.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p042 data-source-page="42" data-source-order="4"}
## Penerapan Optimisasi

::: {.source-item #d90-mit-l08-p042-i001 data-source-page="42" data-source-order="1"}
- Fungsi konkaf $f:\mathbb{R}^n\to\mathbb{R}$ yang mencapai minimumnya pada
  himpunan konveks $X$ di suatu $x^*\in\operatorname{ri}(X)$ harus konstan
  pada $X$.
:::

::: {.source-figure #d90-mit-l08-p042-f001 data-source-page="42" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 42, perpanjangan melewati titik
minimum).** Dalam $\operatorname{aff}(X)$, titik $x$ dan $x^*$ berada di
himpunan konveks $X$. Ruas dari $x$ ke $x^*$ diperpanjang melewati $x^*$
hingga titik $\bar{x}\in X$, sehingga $x^*$ merupakan kombinasi konveks dari
$x$ dan $\bar{x}$.
:::

**Bukti (dengan kontradiksi):** Andaikan ada $x\in X$ dengan
$f(x)>f(x^*)$. Perpanjang ruas dari $x$ ke $x^*$ melewati $x^*$ hingga suatu
$\bar{x}\in X$. Dari kekonkafan $f$, untuk suatu $\alpha\in(0,1)$,

::: {.source-display #d90-mit-l08-p042-d001 data-source-page="42" data-display-order="1"}
$$
f(x^*)\geq \alpha f(x)+(1-\alpha)f(\bar{x}).
$$
:::

Karena $f(x)>f(x^*)$, ketaksamaan ini memaksa
$f(\bar{x})<f(x^*)$, bertentangan dengan minimalitas $x^*$. **Q.E.D.**

::: {.source-item #d90-mit-l08-p042-i002 data-source-page="42" data-source-order="2"}
- **Akibat:** Fungsi linear tak konstan tidak dapat mencapai minimum pada
  titik interior suatu himpunan konveks.
:::

*[Halaman sumber 42.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p043 data-source-page="43" data-source-order="5"}
## Ringkasan Kalkulus Interior Relatif

::: {.source-item #d90-mit-l08-p043-i001 data-source-page="43" data-source-order="1"}
- $\operatorname{ri}(C)$ dan $\operatorname{cl}(C)$ dari suatu himpunan
  konveks $C$ “berbeda sangat sedikit”.

  - Setiap himpunan “di antara” $\operatorname{ri}(C)$ dan
    $\operatorname{cl}(C)$ mempunyai interior relatif dan penutupan yang sama.
  - Interior relatif suatu himpunan konveks sama dengan interior relatif dari
    penutupannya.
  - Penutupan dari interior relatif suatu himpunan konveks sama dengan
    penutupan himpunan tersebut.
:::

::: {.source-item #d90-mit-l08-p043-i002 data-source-page="43" data-source-order="2"}
- Interior relatif dan penutupan berkomutasi dengan produk Kartesius. Untuk
  praimaji di bawah transformasi linear $A$, aturan komutasi berlaku dengan
  syarat kelayakan $A^{-1}(\operatorname{ri}C)\neq\varnothing$, yang setara
  dengan $\operatorname{range}(A)\cap\operatorname{ri}(C)\neq\varnothing$.
:::

::: {.source-item #d90-mit-l08-p043-i003 data-source-page="43" data-source-order="3"}
- Interior relatif berkomutasi dengan citra di bawah transformasi linear dan
  dengan jumlah vektor, tetapi penutupan tidak selalu demikian.
:::

::: {.source-item #d90-mit-l08-p043-i004 data-source-page="43" data-source-order="4"}
- Interior relatif maupun penutupan tidak berkomutasi secara umum dengan
  irisan himpunan.
:::

*[Halaman sumber 43.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p044 data-source-page="44" data-source-order="6"}
## Penutupan versus Interior Relatif

::: {.source-item #d90-mit-l08-p044-i001 data-source-page="44" data-source-order="1"}
- **Proposisi:**

  (a) Berlaku $\operatorname{cl}(C)=\operatorname{cl}(\operatorname{ri}(C))$
  dan $\operatorname{ri}(C)=\operatorname{ri}(\operatorname{cl}(C))$.

  (b) Misalkan $\bar{C}$ adalah himpunan konveks tak kosong lain. Ketiga
  syarat berikut ekuivalen:

  **(i)** $C$ dan $\bar{C}$ mempunyai interior relatif yang sama.

  **(ii)** $C$ dan $\bar{C}$ mempunyai penutupan yang sama.

  **(iii)** $\operatorname{ri}(C)\subseteq\bar{C}\subseteq\operatorname{cl}(C)$.
:::

**Bukti (a):** Karena $\operatorname{ri}(C)\subseteq C$, diperoleh
$\operatorname{cl}(\operatorname{ri}(C))\subseteq\operatorname{cl}(C)$.
Sebaliknya, ambil $\bar{x}\in\operatorname{cl}(C)$ dan
$x\in\operatorname{ri}(C)$. Menurut Prinsip Ruas Garis,

::: {.source-display #d90-mit-l08-p044-d001 data-source-page="44" data-display-order="1"}
$$
\alpha x+(1-\alpha)\bar{x}\in\operatorname{ri}(C),
\qquad \forall\alpha\in(0,1].
$$
:::

Ketika $\alpha\downarrow0$, titik-titik itu menuju $\bar{x}$; jadi
$\bar{x}\in\operatorname{cl}(\operatorname{ri}(C))$.

::: {.source-figure #d90-mit-l08-p044-f001 data-source-page="44" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 44, pendekatan dari interior
relatif).** Sebuah titik $x$ berada dalam interior relatif himpunan konveks
$C$, sedangkan $\bar{x}$ berada pada penutupannya. Titik-titik pada ruas dari
$x$ menuju $\bar{x}$ tetap berada dalam interior relatif dan mendekati
$\bar{x}$ ketika bobot $x$ menuju nol.
:::

Bukti $\operatorname{ri}(C)=\operatorname{ri}(\operatorname{cl}(C))$
serupa. **Penjelasan edisi:** Bagian (b) mengikuti dengan menerapkan kedua
identitas pada himpunan yang terletak di antara interior relatif dan penutupan
yang sama.

*[Halaman sumber 44.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p045 data-source-page="45" data-source-order="7"}
## Transformasi Linear

::: {.source-item #d90-mit-l08-p045-i001 data-source-page="45" data-source-order="1"}
- Misalkan $C$ adalah subhimpunan konveks tak kosong dari $\mathbb{R}^n$ dan
  $A$ adalah matriks berukuran $m\times n$.

  (a) Berlaku $A\,\operatorname{ri}(C)=\operatorname{ri}(A C)$.

  (b) Berlaku
  $A\,\operatorname{cl}(C)\subseteq\operatorname{cl}(A C)$. Selanjutnya,
  jika $C$ terbatas, maka
  $A\,\operatorname{cl}(C)=\operatorname{cl}(A C)$.
:::

**Bukti (a), intuisi yang dibetulkan:** Citra suatu lingkungan relatif di
$C$ merupakan lingkungan relatif di $A C$ terhadap selubung afinnya; citra
elipsoidal atau degenerat itu memuat bola relatif yang sesuai di ruang citra.

**Bukti (b):** Jika barisan $\{x_k\}\subset C$ menuju
$x\in\operatorname{cl}(C)$, maka $\{Ax_k\}\subset A C$ menuju $Ax$, sehingga
$Ax\in\operatorname{cl}(A C)$. Untuk arah sebaliknya ketika $C$ terbatas,
ambil $z\in\operatorname{cl}(A C)$ dan $\{x_k\}\subset C$ dengan
$Ax_k\to z$. Barisan terbatas $\{x_k\}$ mempunyai subbarisan yang menuju
suatu $x\in\operatorname{cl}(C)$, dan kontinuitas memberi $Ax=z$. Jadi
$z\in A\,\operatorname{cl}(C)$. **Q.E.D.**

Secara umum, dapat terjadi

::: {.source-display #d90-mit-l08-p045-d001 data-source-page="45" data-display-order="1"}
$$
A\,\operatorname{int}(C)\neq\operatorname{int}(A C),
\qquad
A\,\operatorname{cl}(C)\neq\operatorname{cl}(A C).
$$
:::

*[Halaman sumber 45.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p046 data-source-page="46" data-source-order="8"}
## Irisan dan Jumlah Vektor

::: {.source-item #d90-mit-l08-p046-i001 data-source-page="46" data-source-order="1"}
- Misalkan $C_1$ dan $C_2$ adalah himpunan konveks tak kosong.

  (a) Berlaku

  ::: {.source-display #d90-mit-l08-p046-d001 data-source-page="46" data-display-order="1"}
  $$
  \operatorname{ri}(C_1+C_2)
  =\operatorname{ri}(C_1)+\operatorname{ri}(C_2),
  $$
  :::

  ::: {.source-display #d90-mit-l08-p046-d002 data-source-page="46" data-display-order="2"}
  $$
  \operatorname{cl}(C_1)+\operatorname{cl}(C_2)
  \subseteq\operatorname{cl}(C_1+C_2).
  $$
  :::

  Jika salah satu dari $C_1$ dan $C_2$ terbatas, maka

  ::: {.source-display #d90-mit-l08-p046-d003 data-source-page="46" data-display-order="3"}
  $$
  \operatorname{cl}(C_1)+\operatorname{cl}(C_2)
  =\operatorname{cl}(C_1+C_2).
  $$
  :::

  (b) Berlaku

  ::: {.source-display #d90-mit-l08-p046-d004 data-source-page="46" data-display-order="4"}
  $$
  \begin{aligned}
  \operatorname{ri}(C_1)\cap\operatorname{ri}(C_2)
  &\subseteq\operatorname{ri}(C_1\cap C_2),\\
  \operatorname{cl}(C_1\cap C_2)
  &\subseteq\operatorname{cl}(C_1)\cap\operatorname{cl}(C_2).
  \end{aligned}
  $$
  :::

  Jika $\operatorname{ri}(C_1)\cap\operatorname{ri}(C_2)\neq\varnothing$,
  maka

  ::: {.source-display #d90-mit-l08-p046-d005 data-source-page="46" data-display-order="5"}
  $$
  \begin{aligned}
  \operatorname{ri}(C_1\cap C_2)
  &=\operatorname{ri}(C_1)\cap\operatorname{ri}(C_2),\\
  \operatorname{cl}(C_1\cap C_2)
  &=\operatorname{cl}(C_1)\cap\operatorname{cl}(C_2).
  \end{aligned}
  $$
  :::
:::

**Bukti (a):** $C_1+C_2$ adalah hasil transformasi linear
$(x_1,x_2)\mapsto x_1+x_2$.

::: {.source-item #d90-mit-l08-p046-i002 data-source-page="46" data-source-order="2"}
- **Contoh lawan untuk (b):** Dua pasangan berikut mempunyai tujuan berbeda.
  Untuk memperlihatkan bahwa syarat irisan interior relatif tidak boleh
  dihilangkan, gunakan

  ::: {.source-display #d90-mit-l08-p046-d006 data-source-page="46" data-display-order="6"}
  $$
  C_1=\{x\mid x\leq0\},
  \qquad
  C_2=\{x\mid x\geq0\}.
  $$
  :::

  Untuk memperlihatkan bahwa penutupan tidak selalu berkomutasi dengan irisan,
  gunakan

  ::: {.source-display #d90-mit-l08-p046-d007 data-source-page="46" data-display-order="7"}
  $$
  C_1=\{x\mid x<0\},
  \qquad
  C_2=\{x\mid x>0\}.
  $$
  :::
:::

*[Halaman sumber 46.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p047 data-source-page="47" data-source-order="9"}
## Produk Kartesius - Generalisasi

::: {.source-item #d90-mit-l08-p047-i001 data-source-page="47" data-source-order="1"}
- Misalkan $C$ adalah himpunan konveks dalam $\mathbb{R}^{n+m}$. Untuk
  $x\in\mathbb{R}^n$, definisikan serat

  ::: {.source-display #d90-mit-l08-p047-d001 data-source-page="47" data-display-order="1"}
  $$
  C_x=\{y\mid(x,y)\in C\},
  $$
  :::

  dan definisikan

  ::: {.source-display #d90-mit-l08-p047-d002 data-source-page="47" data-display-order="2"}
  $$
  D=\{x\mid C_x\neq\varnothing\}.
  $$
  :::

  ::: {.keep-display-intro}
  Maka

  ::: {.source-display #d90-mit-l08-p047-d003 data-source-page="47" data-display-order="3"}
  $$
  \operatorname{ri}(C)
  =\{(x,y)\mid x\in\operatorname{ri}(D),\ y\in\operatorname{ri}(C_x)\}.
  $$
  :::
  :::
:::

**Bukti:** Karena $D$ adalah proyeksi $C$ pada sumbu $x$,

::: {.source-display #d90-mit-l08-p047-d004 data-source-page="47" data-display-order="4"}
$$
\operatorname{ri}(D)
=\{x\mid \text{ada }y\in\mathbb{R}^m
\text{ dengan }(x,y)\in\operatorname{ri}(C)\},
$$
:::

sehingga

::: {.source-display #d90-mit-l08-p047-d005 data-source-page="47" data-display-order="5"}
$$
\operatorname{ri}(C)
=\bigcup_{x\in\operatorname{ri}(D)}
\bigl(M_x\cap\operatorname{ri}(C)\bigr),
$$
:::

dengan $M_x=\{(x,y)\mid y\in\mathbb{R}^m\}$. Untuk setiap
$x\in\operatorname{ri}(D)$, syarat irisan pada hasil halaman sebelumnya
terpenuhi dan

::: {.source-display #d90-mit-l08-p047-d006 data-source-page="47" data-display-order="6"}
$$
M_x\cap\operatorname{ri}(C)
=\operatorname{ri}(M_x\cap C)
=\{(x,y)\mid y\in\operatorname{ri}(C_x)\}.
$$
:::

Gabungkan dua persamaan terakhir. **Q.E.D.**

*[Halaman sumber 47.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p048 data-source-page="48" data-source-order="10"}
## Kontinuitas Fungsi Konveks

::: {.source-item #d90-mit-l08-p048-i001 data-source-page="48" data-source-order="1"}
- Jika $f:\mathbb{R}^n\to\mathbb{R}$ konveks, maka $f$ kontinu.
:::

::: {.source-figure #d90-mit-l08-p048-f001 data-source-page="48" data-figure-disposition="omitted-source-graphic"}
**Deskripsi gambar sumber (halaman sumber 48, kubus satuan dua dimensi).**
Persegi satuan dalam norma maksimum berpusat di $0$ dan mempunyai sudut
$e_1=(1,1)$, $e_2=(1,-1)$, $e_3=(-1,-1)$, dan $e_4=(-1,1)$. Titik $x_k$
menuju $0$ sepanjang sebuah sinar; normalisasinya $y_k$ berada di batas
persegi pada sinar yang sama, sedangkan $z_k=-y_k$ berada di batas yang
berlawanan.
:::

**Bukti:** Cukup ditunjukkan bahwa $f$ kontinu di $0$. Karena setiap titik
kubus satuan merupakan kombinasi konveks dari sudut-sudutnya, $f$ dibatasi
dari atas di dalam kubus oleh nilai maksimum $f$ pada sudut-sudut kubus.

Ambil barisan $x_k\to0$. Jika $x_k=0$, pernyataan untuk indeks itu langsung
benar. Untuk indeks dengan $x_k\neq0$, definisikan, dengan norma maksimum,

::: {.source-display #d90-mit-l08-p048-d001 data-source-page="48" data-display-order="1"}
$$
y_k=\frac{x_k}{\lVert x_k\rVert_\infty},
\qquad
z_k=-\frac{x_k}{\lVert x_k\rVert_\infty}.
$$
:::

Dari kekonveksan,

::: {.source-display #d90-mit-l08-p048-d002 data-source-page="48" data-display-order="2"}
$$
f(x_k)\leq
\bigl(1-\lVert x_k\rVert_\infty\bigr)f(0)
+\lVert x_k\rVert_\infty f(y_k),
$$
:::

dan

::: {.source-display #d90-mit-l08-p048-d003 data-source-page="48" data-display-order="3"}
$$
f(0)\leq
\frac{\lVert x_k\rVert_\infty}{\lVert x_k\rVert_\infty+1}f(z_k)
+\frac{1}{\lVert x_k\rVert_\infty+1}f(x_k).
$$
:::

Ambil limit ketika $k\to\infty$. Karena $\lVert x_k\rVert_\infty\to0$ dan
$f(y_k),f(z_k)$ dibatasi dari atas pada kubus satuan,

::: {.source-display #d90-mit-l08-p048-d004 data-source-page="48" data-display-order="4"}
$$
\begin{aligned}
\limsup_{k\to\infty}
\lVert x_k\rVert_\infty f(y_k)&\leq0,\\
\limsup_{k\to\infty}
\frac{\lVert x_k\rVert_\infty}{\lVert x_k\rVert_\infty+1}f(z_k)&\leq0.
\end{aligned}
$$
:::

Kedua ketaksamaan menjepit $f(x_k)$ menuju $f(0)$. **Q.E.D.**

::: {.source-item #d90-mit-l08-p048-i002 data-source-page="48" data-source-order="2"}
- Hasil ini meluas menjadi kontinuitas pada
  $\operatorname{ri}(\operatorname{dom}(f))$.
:::

*[Halaman sumber 48.]{.source-locator}*
:::

::: {.source-page #d90-mit-l08-p049 data-source-page="49" data-source-order="11"}
## Penutupan Fungsi

::: {.source-item #d90-mit-l08-p049-i001 data-source-page="49" data-source-order="1"}
- Penutupan suatu fungsi $f:X\to[-\infty,\infty]$ adalah fungsi
  $\operatorname{cl}f:\mathbb{R}^n\to[-\infty,\infty]$ dengan

  ::: {.source-display #d90-mit-l08-p049-d001 data-source-page="49" data-display-order="1"}
  $$
  \operatorname{epi}(\operatorname{cl}f)
  =\operatorname{cl}(\operatorname{epi}(f)).
  $$
  :::
:::

::: {.source-item #d90-mit-l08-p049-i002 data-source-page="49" data-source-order="2"}
- Penutupan konveks dari $f$ adalah fungsi
  $\check{\operatorname{cl}}f$ dengan

  ::: {.source-display #d90-mit-l08-p049-d002 data-source-page="49" data-display-order="2"}
  $$
  \operatorname{epi}(\check{\operatorname{cl}}f)
  =\operatorname{cl}\bigl(\operatorname{conv}(\operatorname{epi}(f))\bigr).
  $$
  :::
:::

::: {.source-item #d90-mit-l08-p049-i003 data-source-page="49" data-source-order="3"}
- **Proposisi:** Untuk setiap $f:X\to[-\infty,\infty]$,

  ::: {.source-display #d90-mit-l08-p049-d003 data-source-page="49" data-display-order="3"}
  $$
  \inf_{x\in X}f(x)
  =\inf_{x\in\mathbb{R}^n}(\operatorname{cl}f)(x)
  =\inf_{x\in\mathbb{R}^n}(\check{\operatorname{cl}}f)(x).
  $$
  :::

  Selain itu, setiap vektor yang mencapai infimum $f$ pada $X$ juga mencapai
  infimum $\operatorname{cl}f$ dan $\check{\operatorname{cl}}f$.
:::

::: {.source-item #d90-mit-l08-p049-i004 data-source-page="49" data-source-order="4"}
- **Proposisi:** Untuk setiap $f:X\to[-\infty,\infty]$:

  (a) $\operatorname{cl}f$ adalah fungsi tertutup terbesar yang tidak melebihi
  $f$; serupa, $\check{\operatorname{cl}}f$ adalah fungsi konveks tertutup
  terbesar yang tidak melebihi $f$.

  (b) Jika $f$ konveks, maka $\operatorname{cl}f$ konveks dan proper jika dan
  hanya jika $f$ proper. Selain itu,

  ::: {.source-display #d90-mit-l08-p049-d004 data-source-page="49" data-display-order="4"}
  $$
  (\operatorname{cl}f)(x)=f(x),
  \qquad
  \forall x\in\operatorname{ri}(\operatorname{dom}(f)),
  $$
  :::

  dan jika $x\in\operatorname{ri}(\operatorname{dom}(f))$ serta
  $y\in\operatorname{dom}(\operatorname{cl}f)$, maka

  ::: {.source-display #d90-mit-l08-p049-d005 data-source-page="49" data-display-order="5"}
  $$
  (\operatorname{cl}f)(y)
  =\lim_{\alpha\downarrow0}f\bigl(y+\alpha(x-y)\bigr).
  $$
  :::
:::

*[Halaman sumber 49.]{.source-locator}*
:::
