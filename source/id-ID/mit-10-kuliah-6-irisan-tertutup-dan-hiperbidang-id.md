---
title: "Kuliah 6: Irisan Himpunan Tertutup, Ketertutupan, dan Hiperbidang"
subtitle: "Edisi semantik Bahasa Indonesia - MIT OpenCourseWare 6.253, halaman sumber 64-85"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
  - "Edisi Bahasa Indonesia (terjemahan dan rekonstruksi semantik)"
lang: id-ID
date: "2026-08-24"
rights: "CC BY-NC-SA 4.0"
---

::: {.edition-notice}
**Tentang edisi ini.** Unit ini menerjemahkan seluruh Kuliah 6 pada halaman PDF sumber 64-85. Halaman 86 memulai Kuliah 7 dan tidak termasuk. Saksi Inggris yang dapat dialamatkan baris berada di `source/en/mit-10-lecture-6-closed-intersections-hyperplanes-semantic-witness.md`; saksi tersebut adalah transkripsi proyek, bukan sumber sunting resmi MIT.

Materi turunan MIT tetap berada di bawah **CC BY-NC-SA 4.0** dengan atribusi, penandaan perubahan, kewajiban nonkomersial dan BerbagiSerupa, serta tanpa dukungan tersirat. Tidak ada byte, potongan, atau tata letak gambar Athena Scientific yang disalin. Enam belas blok gambar dengan dua puluh empat panel diganti oleh deskripsi semantik mandiri yang mempertahankan label dan hubungan matematisnya.

Batas sumber ini tidak mempunyai latihan, petunjuk, jawaban, solusi latihan, kode, tautan, atau permukaan interaktif. Tidak ada yang diada-adakan. Rumus diketik ulang dan diperiksa terhadap render karena pemetaan glif sumber merusak beberapa simbol ketika diekstrak sebagai teks. Koreksi yang dapat ditentukan secara matematis diungkapkan di dekat lokatornya dan dicatat dalam ledger proyek.

Terjemahan, rekonstruksi semantik, pembangunan pembaca, dan QA dibantu oleh **OpenAI Codex gpt-5.6-sol, Ultra** atas arahan pengguna repositori. Sistem tersebut bukan penulis sumber, pemberi lisensi, atau wakil MIT. Tinjauan manusia/penutur asli belum tercatat dan bukan penahan penerbitan.
:::

::: {.source-page #d90-mit-l10-p064 data-source-page="64" data-source-order="1"}
## Kuliah 6 - Garis Besar Kuliah

::: {.source-item #d90-mit-l10-p064-i001 data-source-page="64" data-source-order="1"}
- Ketakkosongan irisan himpunan tertutup

  - Versi sederhana
  - Versi yang lebih kompleks
:::

::: {.source-item #d90-mit-l10-p064-i002 data-source-page="64" data-source-order="2"}
- Keberadaan solusi optimal
:::

::: {.source-item #d90-mit-l10-p064-i003 data-source-page="64" data-source-order="3"}
- Pelestarian ketertutupan di bawah transformasi linear
:::

::: {.source-item #d90-mit-l10-p064-i004 data-source-page="64" data-source-order="4"}
- Hiperbidang
:::

*[Halaman sumber 64.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l10-p065-n001 data-source-pages="65,68,70" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0020"}
**Koreksi notasi yang ditentukan.** Pada deklarasi tipe fungsi di halaman
sumber 65, 68, dan 70, sumber mencetak tanda $\mapsto$ di antara domain dan
kodomain. Edisi pembaca memakai tanda tipe fungsi $\to$; PDF sumber tetap
menjadi saksi bagi bentuk tercetak.
:::

::: {.source-page #d90-mit-l10-p065 data-source-page="65" data-source-order="2"}
## Peran Irisan Himpunan Tertutup I

::: {.source-item #d90-mit-l10-p065-i001 data-source-page="65" data-source-order="1"}
**Pertanyaan mendasar:** Diberikan barisan himpunan tertutup tak kosong
$\{C_k\}$ di $\mathbb R^n$ dengan $C_{k+1}\subset C_k$ untuk setiap $k$,
kapan

::: {.source-display #d90-mit-l10-p065-d001 data-source-page="65" data-display-order="1"}
$$
\bigcap_{k=0}^{\infty}C_k
$$
:::

tak kosong?
:::

::: {.source-item #d90-mit-l10-p065-i002 data-source-page="65" data-source-order="2"}
- Teorema irisan himpunan penting setidaknya dalam tiga konteks utama yang
  akan dibahas berikut ini:

  **Apakah fungsi $f:\mathbb R^n\to(-\infty,\infty]$ mencapai nilai minimum
  pada suatu himpunan $X$?**

  Hal ini benar jika dan hanya jika

::: {.source-display #d90-mit-l10-p065-d002 data-source-page="65" data-display-order="2"}
$$
\text{irisan himpunan tak kosong }
\{x\in X\mid f(x)\leq\gamma_k\}
\text{ tak kosong.}
$$
:::
:::

::: {.edition-ambiguity-note #d90-mit-l10-p065-n002 data-source-page="65"}
**Pemadatan sumber dipertahankan.** Slide menyebut irisan secara verbal dan
menampilkan keluarga $\{x\in X\mid f(x)\leq\gamma_k\}$, tetapi tidak
menyatakan rentang indeks atau asumsi pada $\{\gamma_k\}$. Edisi ini tidak
mengarang keduanya.
:::

::: {.source-figure #d90-mit-l10-p065-f001 data-source-page="65" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Deskripsi gambar sumber (halaman 65, himpunan sublevel dan solusi optimal).**
Beberapa kontur sublevel $f$ berbentuk oval dan tersarang beririsan dengan
himpunan layak $X$ yang diarsir. Sebuah titik ditandai pada tempat kontur
relevan terdalam pertama kali menyentuh $X$ dan diberi label solusi optimal.
Gambar menghubungkan ketercapaian minimum pada $X$ dengan ketakkosongan
irisan $X$ dan himpunan-himpunan sublevel yang makin rendah.
:::

*[Halaman sumber 65.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p066 data-source-page="66" data-source-order="3"}
## Peran Irisan Himpunan Tertutup II

::: {.source-item #d90-mit-l10-p066-i001 data-source-page="66" data-source-order="1"}
Jika $C$ tertutup dan $A$ sebuah matriks, apakah $AC$ tertutup?
:::

::: {.source-figure #d90-mit-l10-p066-f001 data-source-page="66" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Deskripsi gambar sumber (halaman 66, irisan praimaji).** Di ruang asal,
himpunan melengkung tertutup $C$ bertumpang tindih dengan pita praimaji
vertikal $N_k$; irisannya diberi label $C_k$, dan $\bar{x}$ terletak di dalam
irisan itu. Pada sumbu citra di bawahnya, $\bar{y}$, $y_{k+1}$, dan $y_k$
berada di dalam citra linear $AC$. Garis putus-putus dari $\bar{x}$ ke
$\bar{y}$ serta lingkungan citra yang tersarang menunjukkan bagaimana titik
bersama irisan praimaji dapat menghasilkan praimaji bagi titik limit.
:::

::: {.source-item #d90-mit-l10-p066-i002 data-source-page="66" data-source-order="2"}
- Jika $C_1$ dan $C_2$ tertutup, apakah $C_1+C_2$ tertutup?

  - Ini merupakan kasus khusus.
  - Tuliskan

::: {.source-display #d90-mit-l10-p066-d001 data-source-page="66" data-display-order="1"}
$$
C_1+C_2=A(C_1\times C_2),
\qquad
A(x_1,x_2)=x_1+x_2.
$$
:::
:::

*[Halaman sumber 66.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l10-p067-n001 data-source-page="67" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0021"}
**Koreksi tata bahasa yang ditentukan.** Kalimat pembuka sumber menyebut $C$
sebagai “a nonempty closed convex” tanpa kata benda *set*. Terjemahan
melengkapinya menjadi “himpunan konveks tertutup tak kosong”; tidak ada isi
matematika yang berubah.
:::

::: {.edition-correction #d90-mit-l10-p067-n002 data-source-pages="67,78" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0023"}
**Perbaikan langkah bukti yang ditentukan.** Pada halaman 67 dan 78, sumber
menyebut $C_k=C\cap N_k$ bersarang, tetapi jari-jari
$\lVert y_k-\bar y\rVert$ belum tentu menurun. Edisi ini memakai jari-jari
ekor $r_k=\sup_{j\geq k}\lVert y_j-\bar y\rVert$. Dengan demikian
$r_k\downarrow0$, setiap $y_k\in W_k$, dan $W_{k+1}\subset W_k$ sebagaimana
diperlukan oleh argumen irisan.
:::

::: {.source-page #d90-mit-l10-p067 data-source-page="67" data-source-order="4"}
## Ketertutupan di Bawah Transformasi Linear

::: {.source-item #d90-mit-l10-p067-i001 data-source-page="67" data-source-order="1"}
- Misalkan $C$ adalah himpunan konveks tertutup tak kosong dan $A$ adalah
  matriks dengan ruang nol $N(A)$. Maka $AC$ tertutup jika
  $R_C\cap N(A)=\{0\}$.

  **Bukti (langkah bersarang diperbaiki):** Misalkan
  $\{y_k\}\subset AC$ dan $y_k\to\bar y$. Ambil
  $r_k=\sup_{j\geq k}\lVert y_j-\bar y\rVert$, lalu definisikan
  $C_k=C\cap N_k$, dengan

::: {.source-display #d90-mit-l10-p067-d001 data-source-page="67" data-display-order="1"}
$$
N_k=\{x\mid Ax\in W_k\},
\qquad
W_k=\{z\mid\lVert z-\bar y\rVert\leq r_k\}.
$$
:::

  Karena $y_k\in W_k$, setiap $C_k$ tak kosong; karena
  $W_{k+1}\subset W_k$, barisan $\{C_k\}$ bersarang. Selain itu,
  $R_{N_k}=N(A)$, sehingga $R_{C_k}=R_C\cap N(A)=\{0\}$ dan $C_k$ kompak.
  Teorema irisan memberi $\bar x\in\bigcap_k C_k$; karena $r_k\to0$, berlaku
  $A\bar x=\bar y$. Jadi $\bar y\in AC$. **Terbukti.**
:::

::: {.source-figure #d90-mit-l10-p067-f001 data-source-page="67" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Deskripsi gambar sumber (halaman 67, bukti ketertutupan citra linear).**
Konstruksi praimaji dari halaman 66 ditampilkan kembali dalam ukuran lebih
kecil. Pita vertikal $N_k$ memotong himpunan melengkung $C$ menjadi $C_k$ di
sekitar $\bar{x}$; pada sumbu citranya terdapat $\bar{y}$ dan titik-titik
mendekat $y_{k+1},y_k$ di dalam $AC$. Gambar mendukung langkah bukti bahwa
titik bersama dari $C_k$ yang tersarang dipetakan ke limit $\bar{y}$.
:::

::: {.source-item #d90-mit-l10-p067-i002 data-source-page="67" data-source-order="2"}
- **Kasus khusus:** $C_1+C_2$ tertutup jika $C_1,C_2$ tertutup dan salah satu
  di antaranya kompak. [Tuliskan $C_1+C_2=A(C_1\times C_2)$, dengan
  $A(x_1,x_2)=x_1+x_2$.]
:::

::: {.source-item #d90-mit-l10-p067-i003 data-source-page="67" data-source-order="3"}
- **Teorema terkait:** $AX$ tertutup jika $X$ polihedral. Hal ini akan
  ditunjukkan kemudian dengan metode yang lebih halus.
:::

*[Halaman sumber 67.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l10-p068-n001 data-source-page="68" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0030"}
**Koreksi peubah terikat yang ditentukan.** Definisi proyeksi tercetak memuat
$(x,z,w)\in S$ tanpa mengikat $z$. Karena proyeksi ke ruang $(x,w)$ berarti
ada suatu $z\in\mathbb R^m$, edisi ini menuliskan pengikat eksistensial itu
secara eksplisit.
:::

::: {.source-page #d90-mit-l10-p068 data-source-page="68" data-source-order="5"}
## Peran Irisan Himpunan Tertutup III

::: {.source-item #d90-mit-l10-p068-i001 data-source-page="68" data-source-order="1"}
- Misalkan $F:\mathbb R^{n+m}\to(-\infty,\infty]$ adalah fungsi konveks
  tertutup proper, dan tinjau

::: {.source-display #d90-mit-l10-p068-d001 data-source-page="68" data-display-order="1"}
$$
f(x)=\inf_{z\in\mathbb R^m}F(x,z).
$$
:::
:::

::: {.source-item #d90-mit-l10-p068-i002 data-source-page="68" data-source-order="2"}
- **Jika $F(x,z)$ tertutup, apakah $f(x)$ tertutup?**

  - Pertanyaan penting dalam teori dualitas.
:::

::: {.source-item #d90-mit-l10-p068-i003 data-source-page="68" data-source-order="3"}
- **Fakta pertama:** Jika $F$ konveks, maka $f$ juga konveks.
:::

::: {.source-item #d90-mit-l10-p068-i004 data-source-page="68" data-source-order="4"}
- **Fakta kedua:**

::: {.source-display #d90-mit-l10-p068-d002 data-source-page="68" data-display-order="2"}
$$
P\bigl(\operatorname{epi}(F)\bigr)
\subset
\operatorname{epi}(f)
\subset
\operatorname{cl}\!\left(P\bigl(\operatorname{epi}(F)\bigr)\right),
$$
:::

  dengan $P(\cdot)$ menyatakan proyeksi ke ruang $(x,w)$; yaitu, untuk
  sebarang subhimpunan $S$ dari $\mathbb R^{n+m+1}$,
  $P(S)=\{(x,w)\mid\exists z\in\mathbb R^m:\ (x,z,w)\in S\}$.
:::

::: {.source-item #d90-mit-l10-p068-i005 data-source-page="68" data-source-order="5"}
- Jadi, jika $F$ tertutup dan terdapat struktur yang menjamin bahwa proyeksi
  mempertahankan ketertutupan, maka $f$ tertutup.
:::

::: {.source-item #d90-mit-l10-p068-i006 data-source-page="68" data-source-order="6"}
- ... tetapi kekonveksan dan ketertutupan $F$ tidak menjamin ketertutupan
  $f$.
:::

*[Halaman sumber 68.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p069 data-source-page="69" data-source-order="6"}
## Minimisasi Parsial: Visualisasi

::: {.source-item #d90-mit-l10-p069-i001 data-source-page="69" data-source-order="1"}
- Hubungan antara pelestarian ketertutupan di bawah minimisasi parsial dan
  ketercapaian infimum atas $z$ untuk $x$ tetap.
:::

::: {.source-figure #d90-mit-l10-p069-f001 data-source-page="69" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Deskripsi gambar sumber (halaman 69, selubung bawah minimisasi parsial).**
Kedua panel memakai koordinat $(x,z,w)$ dan menampilkan permukaan konveks
$F(x,z)$ di atas bidang $(x,z)$. Selubung bawah ketika bergerak dalam arah
$z$ ditandai sebagai $f(x)=\inf_zF(x,z)$, dan epigraf vertikalnya tampak pada
bidang $(x,w)$. Pada panel pertama, jejak permukaan turun menuju selubung
bawah sepanjang $z$ tanpa tampak berbalik naik; pada panel kedua, jejaknya
melengkung melalui titik rendah yang tercapai. Kedua panel membandingkan batas
epigraf terproyeksi yang hanya didekati secara asimtotik dengan batas yang
dihasilkan oleh titik peminimum parsial yang tercapai.
:::

::: {.source-item #d90-mit-l10-p069-i002 .source-example data-source-page="69" data-source-order="2"}
- **Contoh tandingan:** Misalkan

::: {.source-display #d90-mit-l10-p069-d001 data-source-page="69" data-display-order="1"}
$$
F(x,z)=
\begin{cases}
e^{-\sqrt{xz}}, & \text{jika }x\geq0, z\geq0,\\
\infty, & \text{selainnya.}
\end{cases}
$$
:::
:::

::: {.source-item #d90-mit-l10-p069-i003 data-source-page="69" data-source-order="3"}
- $F$ konveks dan tertutup, tetapi

::: {.source-display #d90-mit-l10-p069-d002 data-source-page="69" data-display-order="2"}
$$
f(x)=\inf_{z\in\mathbb R}F(x,z)=
\begin{cases}
0, & \text{jika }x>0,\\
1, & \text{jika }x=0,\\
\infty, & \text{jika }x<0,
\end{cases}
$$
:::

  tidak tertutup.
:::

*[Halaman sumber 69.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l10-p070-n001 data-source-pages="70,77" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0022"}
**Koreksi istilah yang ditentukan.** Halaman 70 dan 77 memakai
*minimum/minima* untuk titik yang mencapai nilai objektif terkecil. Edisi ini
membedakan “titik peminimum” dari “nilai minimum” skalar; PDF sumber tetap
menjadi saksi bagi istilah tercetak.
:::

::: {.source-page #d90-mit-l10-p070 data-source-page="70" data-source-order="7"}
## Teorema Minimisasi Parsial

::: {.source-item #d90-mit-l10-p070-i001 data-source-page="70" data-source-order="1"}
Misalkan $F:\mathbb R^{n+m}\to(-\infty,\infty]$ adalah fungsi konveks tertutup
proper, dan tinjau $f(x)=\inf_{z\in\mathbb R^m}F(x,z)$.
:::

::: {.source-item #d90-mit-l10-p070-i002 data-source-page="70" data-source-order="2"}
- Setiap teorema irisan himpunan menghasilkan suatu hasil ketertutupan. Kasus
  paling sederhana adalah sebagai berikut:
:::

::: {.source-item #d90-mit-l10-p070-i003 data-source-page="70" data-source-order="3"}
- **Pelestarian Ketertutupan di Bawah Kekompakan:** Jika terdapat
  $\bar{x}\in\mathbb R^n$ dan $\bar{\gamma}\in\mathbb R$ sedemikian sehingga
  himpunan

::: {.source-display #d90-mit-l10-p070-d001 data-source-page="70" data-display-order="1"}
$$
\{z\mid F(\bar{x},z)\leq\bar{\gamma}\}
$$
:::

  tak kosong dan kompak, maka $f$ konveks, tertutup, dan proper. Selain itu,
  untuk setiap $x\in\operatorname{dom}(f)$, himpunan titik peminimum
  $F(x,\cdot)$ tak kosong dan kompak.
:::

::: {.source-figure #d90-mit-l10-p070-f001 data-source-page="70" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Deskripsi gambar sumber (halaman 70, teorema minimisasi parsial).** Setiap
panel menampilkan permukaan konveks $F(x,z)$ dalam koordinat $(x,z,w)$ dan
selubung bawah $f(x)=\inf_zF(x,z)$ yang diproyeksikan ke bidang $(x,w)$ sebagai
batas $\operatorname{epi}(f)$. Satu panel menggambarkan profil yang dapat
melaju tanpa batas dalam arah $z$ menuju selubung, sedangkan panel lain
menggambarkan profil dengan palung yang tercapai. Hipotesis sublevel kompak
meniadakan perilaku lari-tak-terbatas yang relevan bagi teorema, sehingga titik
peminimum parsial ada dan selubung bawah dipertahankan sebagai batas tertutup.
:::

*[Halaman sumber 70.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p071 data-source-page="71" data-source-order="8"}
## Analisis yang Lebih Tajam - Ringkasan

::: {.edition-correction #d90-mit-l10-p071-n001 data-source-page="71" data-correction-event="O015-MIT-SEM-0024"}
**Koreksi edisi.** Frasa tercetak “Existence of of solutions” memuat kata
*of* dua kali. Duplikasi itu dihapus dalam terjemahan menjadi “keberadaan
solusi”; tidak ada isi matematis yang diubah.
:::

::: {.source-item #d90-mit-l10-p071-i001 data-source-page="71" data-source-order="1"}
- Kita telah mencatat bahwa tiga pertanyaan dasar berikut mempunyai akar
  matematis yang sama:

  - Keberadaan solusi masalah optimisasi konveks

  - Terpeliharanya ketertutupan himpunan konveks di bawah transformasi linear

  - Terpeliharanya ketertutupan fungsi konveks di bawah minimisasi parsial
:::

::: {.source-item #d90-mit-l10-p071-i002 data-source-page="71" data-source-order="2"}
- Akar bersama itu adalah pertanyaan tentang ketakkosongan irisan suatu
  barisan bersarang himpunan tertutup.
:::

::: {.source-item #d90-mit-l10-p071-i003 data-source-page="71" data-source-order="3"}
- Pembahasan sebelumnya dalam kuliah ini menyelesaikan pertanyaan tersebut
  dengan mengasumsikan bahwa semua himpunan dalam barisan itu kompak.
:::

::: {.source-item #d90-mit-l10-p071-i004 data-source-page="71" data-source-order="4"}
- Pembahasan yang lebih tajam sebagai gantinya membuat berbagai asumsi tentang
  arah resesi dan ruang kelinieran himpunan-himpunan dalam barisan tersebut.
:::

::: {.source-item #d90-mit-l10-p071-i005 data-source-page="71" data-source-order="5"}
- Setelah teori irisan himpunan yang cukup tajam dikembangkan, dapat diperoleh
  hasil-hasil yang lebih kuat mengenai ketiga pertanyaan itu.
:::

::: {.source-item #d90-mit-l10-p071-i006 data-source-page="71" data-source-order="6"}
- Slide-slide selanjutnya hingga pembahasan hiperbidang merangkum pengembangan
  ini sebagai bantuan belajar mandiri dengan menggunakan Bagian 1.4.2, 1.4.3,
  3.2, dan 3.3.
:::

*[Halaman sumber 71.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p072 data-source-page="72" data-source-order="9"}
## Barisan Asimtotik

::: {.edition-correction #d90-mit-l10-p072-n001 data-source-page="72" data-correction-event="O015-MIT-SEM-0025"}
**Koreksi edisi.** Definisi sumber dimulai dengan “Given nested sequence,”
tanpa artikel *a*. Terjemahan memakai konstruksi lengkap “Diberikan suatu
barisan bersarang”; isi definisi tidak berubah.
:::

::: {.source-item #d90-mit-l10-p072-i001 data-source-page="72" data-source-order="1"}
- Diberikan suatu barisan bersarang $\{C_k\}$ dari himpunan-himpunan konveks
  tertutup. Barisan $\{x_k\}$ disebut **barisan asimtotik** jika

  ::: {.source-display #d90-mit-l10-p072-d001 data-source-page="72" data-display-order="1"}
  $$
  x_k\in C_k,
  \qquad x_k\neq0,
  \qquad k=0,1,\ldots
  $$
  :::

  dan

  ::: {.source-display #d90-mit-l10-p072-d002 data-source-page="72" data-display-order="2"}
  $$
  \lVert x_k\rVert\to\infty,
  \qquad
  \frac{x_k}{\lVert x_k\rVert}\to\frac{d}{\lVert d\rVert},
  $$
  :::

  dengan $d$ suatu arah resesi bersama tak nol dari himpunan-himpunan $C_k$.
:::

::: {.source-item #d90-mit-l10-p072-i002 data-source-page="72" data-source-order="2"}
- Sebagai kasus khusus, kita mendefinisikan barisan asimtotik dari suatu
  himpunan konveks tertutup $C$ dengan memakai $C_k\equiv C$.
:::

::: {.source-item #d90-mit-l10-p072-i003 data-source-page="72" data-source-order="3"}
- Setiap barisan tak terbatas $\{x_k\}$ dengan $x_k\in C_k$ mempunyai
  subbarisan asimtotik.
:::

::: {.source-item #d90-mit-l10-p072-i004 data-source-page="72" data-source-order="4"}
- Barisan $\{x_k\}$ disebut **retraktif** jika untuk suatu $\bar{k}$ berlaku

  ::: {.source-display #d90-mit-l10-p072-d003 data-source-page="72" data-display-order="3"}
  $$
  x_k-d\in C_k,
  \qquad \forall k\geq\bar{k}.
  $$
  :::
:::

::: {.source-figure #d90-mit-l10-p072-f001 data-source-page="72" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber (halaman 72, barisan dan arah
asimtotik).** Titik-titik berlabel $x_0,x_1,\ldots,x_5$ bergerak semakin jauh
dari titik asal, sedangkan arah vektor posisinya semakin mendekati satu arah
bersama. Vektor $d$ yang berpangkal di titik asal menandai arah limit itu.
Hubungan tersebut memperlihatkan bahwa normalisasi barisan tak terbatas
menghasilkan arah asimtotiknya.
:::

*[Halaman sumber 72.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p073 data-source-page="73" data-source-order="10"}
## Barisan Retraktif

::: {.source-item #d90-mit-l10-p073-i001 data-source-page="73" data-source-order="1"}
- Barisan bersarang $\{C_k\}$ dari himpunan-himpunan konveks tertutup disebut
  **retraktif** jika semua barisan asimtotiknya retraktif.
:::

::: {.source-figure #d90-mit-l10-p073-f001 data-source-page="73" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Deskripsi semantik gambar sumber (halaman 73, dua contoh barisan
himpunan).**

- **Panel (a), barisan himpunan retraktif:** Tiga himpunan konveks tertutup
  bersarang $C_0,C_1,C_2$ menyempit di sekitar irisan bersama yang tak kosong.
  Titik-titik $x_0,x_1,x_2,x_3$ menjauh sepanjang arah $d$, tetapi translasi
  titik yang cukup lanjut sebesar $-d$ tetap berada di himpunan pasangannya.
- **Panel (b), barisan himpunan tak retraktif:** Himpunan-himpunan konveks
  melengkung $C_0,C_1,C_2$ saling bersarang dan meruncing menuju irisan
  limitnya. Titik-titik $x_0,x_1,x_2$ mempunyai arah asimtotik $d$, tetapi
  translasi satu langkah berlawanan dengan $d$ akhirnya keluar dari himpunan
  melengkung yang bersesuaian. Perbandingan ini membedakan sifat retraktif dari
  sekadar sifat bersarang dan ketakkosongan irisan.
:::

::: {.source-item #d90-mit-l10-p073-i002 data-source-page="73" data-source-order="2"}
- Setengah-ruang tertutup, jika dipandang sebagai barisan dengan semua komponen
  identik, bersifat retraktif.
:::

::: {.source-item #d90-mit-l10-p073-i003 data-source-page="73" data-source-order="3"}
- Irisan dan hasil kali Kartesius dari barisan-barisan himpunan retraktif
  bersifat retraktif.
:::

::: {.source-item #d90-mit-l10-p073-i004 data-source-page="73" data-source-order="4"}
- Himpunan polihedral bersifat retraktif. Selain itu, jumlah vektor dari suatu
  himpunan konveks kompak dan suatu himpunan konveks retraktif juga retraktif.
:::

::: {.source-item #d90-mit-l10-p073-i005 data-source-page="73" data-source-order="5"}
- Kerucut nonpolihedral dan himpunan sublevel fungsi kuadratik belum tentu
  retraktif.
:::

*[Halaman sumber 73.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p074 data-source-page="74" data-source-order="11"}
## Teorema Irisan Himpunan I

::: {.source-item #d90-mit-l10-p074-i001 data-source-page="74" data-source-order="1"}
- **Proposisi.** Jika $\{C_k\}$ retraktif, maka
  $\bigcap_{k=0}^{\infty}C_k$ tak kosong.
:::

::: {.source-item #d90-mit-l10-p074-i002 data-source-page="74" data-source-order="2"}
- Gagasan utama bukti:

  (a) Irisan $\bigcap_{k=0}^{\infty}C_k$ kosong jika dan hanya jika barisan
  $\{x_k\}$ yang terdiri atas vektor bernorma minimum di $C_k$ tak terbatas
  (sehingga suatu subbarisannya asimtotik).

  (b) Barisan asimtotik $\{x_k\}$ yang terdiri atas vektor bernorma minimum
  tidak mungkin retraktif, sebab pergeseran berlawanan dengan arah asimtotik
  pada akhirnya menghasilkan titik yang lebih dekat ke $0$.
:::

::: {.source-figure #d90-mit-l10-p074-f001 data-source-page="74" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber (halaman 74, geometri gagasan bukti).**
Titik-titik $x_0,x_1,\ldots,x_5$ membentuk barisan tak terbatas yang arah
vektornya dari titik asal menuju $d$. Karena $x_k$ adalah titik terdekat dari
$C_k$ ke titik asal, sifat retraktif yang mempertahankan $x_k-d$ di dalam
$C_k$ akan bertentangan dengan norma minimum untuk $k$ cukup besar: titik
hasil pergeseran itu lebih dekat ke titik asal. Relasi geometris inilah yang
dipakai pada langkah bukti (b).
:::

*[Halaman sumber 74.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p075 data-source-page="75" data-source-order="12"}
## Teorema Irisan Himpunan II

::: {.source-item #d90-mit-l10-p075-i001 data-source-page="75" data-source-order="1"}
- **Proposisi.** Misalkan $\{C_k\}$ adalah barisan bersarang dari
  himpunan-himpunan konveks tertutup tak kosong, dan $X$ adalah himpunan
  retraktif sedemikian sehingga semua himpunan $\bar C_k=X\cap C_k$ tak kosong.
  Andaikan

  ::: {.source-display #d90-mit-l10-p075-d001 data-source-page="75" data-display-order="1"}
  $$
  R_X\cap R\subset L,
  $$
  :::

  dengan

  ::: {.source-display #d90-mit-l10-p075-d002 data-source-page="75" data-display-order="2"}
  $$
  R=\bigcap_{k=0}^{\infty}R_{C_k},
  \qquad
  L=\bigcap_{k=0}^{\infty}L_{C_k}.
  $$
  :::

  Maka

  ::: {.source-display #d90-mit-l10-p075-d003 data-source-page="75" data-display-order="3"}
  $$
  \{\bar C_k\}\text{ retraktif},
  \qquad
  \bigcap_{k=0}^{\infty}\bar C_k\neq\varnothing.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p075-i002 data-source-page="75" data-source-order="2"}
- Kasus-kasus khusus:

  - $X=\mathbb R^n$ dan $R=L$ (himpunan-himpunan $C_k$ “silindris”)

  - $R_X\cap R=\{0\}$ (tidak ada arah resesi bersama tak nol dari $X$ dan
    $\bigcap_k C_k$)
:::

::: {.source-item #d90-mit-l10-p075-i003 data-source-page="75" data-source-order="3"}
**Bukti.** Himpunan arah resesi bersama dari $\bar C_k$ adalah
$R_X\cap R$. Untuk sebarang barisan asimtotik $\{x_k\}$ yang bersesuaian
dengan $d\in R_X\cap R$:

**(1)**

::: {.source-display #d90-mit-l10-p075-d004 data-source-page="75" data-display-order="4"}
$$
x_k-d\in C_k
\qquad\text{(karena }d\in L\text{)}.
$$
:::

**(2)**

::: {.source-display #d90-mit-l10-p075-d005 data-source-page="75" data-display-order="5"}
$$
x_k-d\in X
\qquad\text{(karena }X\text{ retraktif)}.
$$
:::

Jadi $\{\bar C_k\}$ retraktif.
:::

*[Halaman sumber 75.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p076 data-source-page="76" data-source-order="13"}
## Perlu Mengasumsikan bahwa X Retraktif

::: {.source-figure #d90-mit-l10-p076-f001 data-source-page="76" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Deskripsi semantik gambar sumber (halaman 76, peran sifat retraktif
$X$).** Kedua panel mengiris daerah-daerah konveks tertutup vertikal yang
bersarang, $C_{k+1}\subset C_k$, dengan suatu himpunan $X$.

- **Panel kiri:** Himpunan $X$ yang polihedral dan berbentuk V memotong setiap
  daerah bersarang; himpunan-himpunan $\bar C_k=X\cap C_k$ yang dihasilkan
  tetap mempunyai titik bersama.
- **Panel kanan:** Himpunan $X$ yang melengkung dan nonpolihedral mendekati
  daerah-daerah yang menyempit tanpa mencapai lokasi limitnya. Setiap
  $\bar C_k=X\cap C_k$ tak kosong, tetapi irisan tak hingganya kosong. Perbedaan
  geometri ini menunjukkan bahwa inklusi arah resesi saja tidak menggantikan
  sifat retraktif $X$.
:::

::: {.source-item #d90-mit-l10-p076-i001 data-source-page="76" data-source-order="1"}
- Tinjau

  ::: {.source-display #d90-mit-l10-p076-d001 data-source-page="76" data-display-order="1"}
  $$
  \bigcap_{k=0}^{\infty}\bar C_k,
  \qquad
  \bar C_k=X\cap C_k.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p076-i002 data-source-page="76" data-source-order="2"}
- Syarat $R_X\cap R\subset L$ terpenuhi.
:::

::: {.source-item #d90-mit-l10-p076-i003 data-source-page="76" data-source-order="3"}
- Pada gambar kiri, $X$ bersifat polihedral.
:::

::: {.source-item #d90-mit-l10-p076-i004 data-source-page="76" data-source-order="4"}
- Pada gambar kanan, $X$ bersifat nonpolihedral dan tak retraktif, serta

  ::: {.source-display #d90-mit-l10-p076-d002 data-source-page="76" data-display-order="2"}
  $$
  \bigcap_{k=0}^{\infty}\bar C_k=\varnothing.
  $$
  :::
:::

::: {.edition-correction #d90-mit-l10-p076-n001 data-source-page="76" data-correction-event="O015-MIT-SEM-0026"}
**Koreksi edisi.** Sumber mencetak “nonretrative,” tanpa huruf *c* dalam
*nonretractive*. Terjemahan memakai istilah yang terbentuk dengan benar,
“tak retraktif”; makna matematis tidak berubah.
:::

*[Halaman sumber 76.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p077 data-source-page="77" data-source-order="14"}
## Pemrograman Linear dan Kuadratik

::: {.source-item #d90-mit-l10-p077-i001 data-source-page="77" data-source-order="1"}
- **Teorema.** Misalkan

  ::: {.source-display #d90-mit-l10-p077-d001 data-source-page="77" data-display-order="1"}
  $$
  f(x)=x'Qx+c'x,
  \qquad
  X=\{x\mid a_j'x+b_j\leq0,\ j=1,\ldots,r\},
  $$
  :::

  dengan $Q$ simetris semidefinit positif. Jika nilai minimum $f$ pada $X$
  berhingga, terdapat titik peminimum $f$ pada $X$.
:::

::: {.source-item #d90-mit-l10-p077-i002 data-source-page="77" data-source-order="2"}
- **Bukti (garis besar).** Tuliskan

  ::: {.source-display #d90-mit-l10-p077-d002 data-source-page="77" data-display-order="2"}
  $$
  \text{Himpunan Titik Peminimum}
  =\bigcap_{k=0}^{\infty}
  \left(X\cap\{x\mid x'Qx+c'x\leq\gamma_k\}\right)
  $$
  :::

  dengan

  ::: {.source-display #d90-mit-l10-p077-d003 data-source-page="77" data-display-order="3"}
  $$
  \gamma_k\downarrow f^*=\inf_{x\in X}f(x).
  $$
  :::

  Verifikasikan syarat $R_X\cap R\subset L$ dari teorema irisan himpunan
  sebelumnya, dengan $R$ dan $L$ masing-masing merupakan himpunan arah resesi
  bersama dan arah kelinieran bersama dari himpunan-himpunan

  ::: {.source-display #d90-mit-l10-p077-d004 data-source-page="77" data-display-order="4"}
  $$
  \{x\mid x'Qx+c'x\leq\gamma_k\}.
  $$
  :::

  **Terbukti.**
:::

::: {.edition-note #d90-mit-l10-p077-n001 data-source-page="77" data-correction-event="O015-MIT-SEM-0022"}
**Catatan istilah.** Frasa sumber *a minimum* dan *Set of Minima* pada halaman
ini menunjuk titik-titik yang mencapai nilai objektif terkecil. Karena itu,
terjemahan memakai “titik peminimum” dan “Himpunan Titik Peminimum”; istilah
“nilai minimum” dicadangkan untuk skalar $f^*$.
:::

*[Halaman sumber 77.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p078 data-source-page="78" data-source-order="15"}
## Ketertutupan di Bawah Transformasi Linear

::: {.edition-correction #d90-mit-l10-p078-n001 data-source-page="78" data-correction-event="O015-MIT-SEM-0021"}
**Koreksi edisi.** Sumber menyebut $C$ sebagai “a nonempty closed convex,”
tanpa nomina *set*. Terjemahan melengkapinya menjadi “himpunan konveks
tertutup tak kosong”; isi matematis tidak berubah.
:::

::: {.edition-correction #d90-mit-l10-p078-n002 data-source-page="78" data-correction-event="O015-MIT-SEM-0027"}
**Perbaikan cakupan bukti yang ditentukan.** Teorema sumber memuat bagian (a)
dan (b), tetapi garis besar tercetak hanya memakai $\{y_k\}\subset AC$ dan
$C_k=C\cap N_k$. Untuk bagian (b), edisi ini secara eksplisit memakai
$\{y_k\}\subset A(X\cap C)$ dan $\bar C_k=X\cap C\cap N_k$; ini adalah
konstruksi yang diperlukan agar sifat retraktif $X$ benar-benar digunakan.
:::

::: {.source-item #d90-mit-l10-p078-i001 data-source-page="78" data-source-order="1"}
- Misalkan $C$ adalah himpunan konveks tertutup tak kosong dan $A$ adalah
  matriks dengan ruang nol $N(A)$.

  (a) $AC$ tertutup jika $R_C\cap N(A)\subset L_C$.

  (b) $A(X\cap C)$ tertutup jika $X$ adalah himpunan retraktif dan

  ::: {.source-display #d90-mit-l10-p078-d001 data-source-page="78" data-display-order="1"}
  $$
  R_X\cap R_C\cap N(A)\subset L_C.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p078-i002 data-source-page="78" data-source-order="2"}
- **Bukti (garis besar yang dilengkapi).** Untuk bagian (a), misalkan
  $\{y_k\}\subset AC$ dan $y_k\to\bar y$. Tetapkan
  $r_k=\sup_{j\geq k}\lVert y_j-\bar y\rVert$, lalu definisikan
  $C_k=C\cap N_k$ dan

  ::: {.source-display #d90-mit-l10-p078-d002 data-source-page="78" data-display-order="2"}
  $$
  N_k=\{x\mid Ax\in W_k\},
  \qquad
  W_k=\{z\mid\lVert z-\bar y\rVert\leq r_k\}.
  $$
  :::

  Barisan $\{C_k\}$ kini tak kosong, tertutup, dan bersarang. Syarat
  $R_C\cap N(A)\subset L_C$ membuatnya retraktif melalui teorema irisan
  sebelumnya, sehingga $\bigcap_k C_k\neq\varnothing$ dan setiap titik
  irisannya dipetakan ke $\bar y$.

  Untuk bagian (b), mulai dengan $\{y_k\}\subset A(X\cap C)$ dan gunakan
  $\bar C_k=X\cap C\cap N_k$. Syarat
  $R_X\cap R_C\cap N(A)\subset L_C$ bersama sifat retraktif $X$ memberi
  $\bigcap_k\bar C_k\neq\varnothing$, sehingga lagi-lagi $\bar y$ mempunyai
  praimaji dalam $X\cap C$.
:::

::: {.source-figure #d90-mit-l10-p078-f001 data-source-page="78" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber (halaman 78, praimaji limit).** Himpunan
konveks tertutup $C$ dipotong oleh himpunan-himpunan praimaji bersarang
$N_k$, sehingga terbentuk irisan layak $C_k=C\cap N_k$ dan suatu titik limit
$\bar x$ dalam irisan bersama. Di bawah pemetaan linear $A$, citra $AC$ memuat
titik-titik $y_k$ dan $y_{k+1}$ yang menuju $\bar y$. Relasi
$Ax_k\in W_k$ bersama $y_k\to\bar y$ menunjukkan bagaimana ketakkosongan
irisan praimaji bersarang menghasilkan praimaji bagi limit, sehingga
menjamin ketertutupan $AC$.
:::

::: {.source-item #d90-mit-l10-p078-i003 data-source-page="78" data-source-order="3"}
- **Kasus khusus.** $AX$ tertutup jika $X$ polihedral.
:::

*[Halaman sumber 78.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p079 data-source-page="79" data-source-order="16"}
## Perlu Mengasumsikan bahwa $X$ Retraktif

::: {.source-figure #d90-mit-l10-p079-f001 data-source-page="79" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber.** Dua sketsa koordinat membandingkan proyeksi $X\cap C$ oleh $A$. Pada keduanya, arah vertikal adalah $N(A)$, $C$ berupa pita vertikal, dan citra $A(X\cap C)$ ditandai pada sumbu horizontal. Di kiri, batas poligonal $X$ memotong pita dan kedua ujung pembatas citranya tercapai. Di kanan, batas melengkung $X$ mendekati sebuah garis vertikal putus-putus di dalam pita tanpa mencapainya, sehingga citra proyeksi kehilangan titik ujung limitnya. Perbandingan ini mempertahankan syarat kerucut resesi yang sama, tetapi memperlihatkan akibat kegagalan sifat retraktif pada ketertutupan citra.
:::

::: {.source-item #d90-mit-l10-p079-i001 data-source-page="79" data-source-order="1"}
Perhatikan ketertutupan $A(X\cap C)$.
:::

::: {.source-item #d90-mit-l10-p079-i002 data-source-page="79" data-source-order="2"}
- Dalam kedua contoh, syarat

  ::: {.source-display #d90-mit-l10-p079-d001 data-source-page="79" data-display-order="1"}
  $$
  R_X\cap R_C\cap N(A)\subset L_C
  $$
  :::

  dipenuhi.
:::

::: {.source-item #d90-mit-l10-p079-i003 data-source-page="79" data-source-order="3"}
- Namun, pada contoh di kanan, $X$ tidak retraktif dan himpunan $A(X\cap C)$ tidak tertutup.
:::

*[Halaman sumber 79.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p080 data-source-page="80" data-source-order="17"}
## Ketertutupan Jumlah Vektor

::: {.source-item #d90-mit-l10-p080-i001 data-source-page="80" data-source-order="1"}
- Misalkan $C_1,\ldots,C_m$ adalah himpunan bagian konveks tertutup tak kosong dari $\mathbb R^n$. Andaikan persamaan $d_1+\cdots+d_m=0$ untuk vektor-vektor $d_i\in R_{C_i}$ mengakibatkan $d_i=0$ bagi semua $i=1,\ldots,m$. Maka $C_1+\cdots+C_m$ adalah himpunan tertutup.
:::

::: {.source-item #d90-mit-l10-p080-i002 data-source-page="80" data-source-order="2"}
- **Kasus Khusus:** Jika $C_1$ dan $-C_2$ adalah himpunan konveks tertutup, maka $C_1-C_2$ tertutup jika $R_{C_1}\cap R_{C_2}=\{0\}$.
:::

::: {.source-item #d90-mit-l10-p080-i003 data-source-page="80" data-source-order="3"}
**Bukti:** Produk Kartesius

::: {.source-display #d90-mit-l10-p080-d001 data-source-page="80" data-display-order="1"}
$$
C=C_1\times\cdots\times C_m
$$
:::

adalah himpunan konveks tertutup, dan kerucut resesinya adalah

::: {.source-display #d90-mit-l10-p080-d002 data-source-page="80" data-display-order="2"}
$$
R_C=R_{C_1}\times\cdots\times R_{C_m}.
$$
:::

Definisikan $A$ dengan

::: {.source-display #d90-mit-l10-p080-d003 data-source-page="80" data-display-order="3"}
$$
A(x_1,\ldots,x_m)=x_1+\cdots+x_m.
$$
:::

Maka

::: {.source-display #d90-mit-l10-p080-d004 data-source-page="80" data-display-order="4"}
$$
AC=C_1+\cdots+C_m,
$$
:::

dan

::: {.source-display #d90-mit-l10-p080-d005 data-source-page="80" data-display-order="5"}
$$
N(A)=\bigl\{(d_1,\ldots,d_m)\mid d_1+\cdots+d_m=0\bigr\},
$$
:::

::: {.source-display #d90-mit-l10-p080-d006 data-source-page="80" data-display-order="6"}
$$
R_C\cap N(A)
=\bigl\{(d_1,\ldots,d_m)\mid d_1+\cdots+d_m=0,
\ d_i\in R_{C_i},\ \forall i\bigr\}.
$$
:::

Berdasarkan syarat yang diberikan, $R_C\cap N(A)=\{0\}$, sehingga $AC$ tertutup. **Q.E.D.**
:::

*[Halaman sumber 80.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l10-p081-n001 data-source-page="81" data-correction-event="O015-MIT-SEM-0028"}
**Koreksi tata bahasa yang ditentukan.** Sumber menghilangkan artikel dalam
“where $a$ is nonzero vector” dan kata *to* dalam “is said be supporting.”
Edisi ini melengkapi kedua relasi gramatikal tanpa mengubah definisi.
:::

::: {.source-page #d90-mit-l10-p081 data-source-page="81" data-source-order="18"}
## Hiperbidang

::: {.source-figure #d90-mit-l10-p081-f001 data-source-page="81" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber.** Sebuah garis miring yang melalui $\bar{x}$ tegak lurus terhadap panah $a$. Garis itu dinyatakan sebagai $\{x\mid a'x=b\}=\{x\mid a'x=a'\bar{x}\}$. Sisi yang ditunjuk oleh $a$ adalah setengah-ruang positif $\{x\mid a'x\geq b\}$, sedangkan sisi lawannya adalah setengah-ruang negatif $\{x\mid a'x\leq b\}$. Dengan demikian, gambar menghubungkan vektor normal, hiperbidang batas, dan kedua setengah-ruang tertutupnya.
:::

::: {.source-item #d90-mit-l10-p081-i001 data-source-page="81" data-source-order="1"}
- **Hiperbidang** adalah himpunan berbentuk $\{x\mid a'x=b\}$, dengan $a$ suatu vektor tak nol di $\mathbb R^n$ dan $b$ suatu skalar.
:::

::: {.source-item #d90-mit-l10-p081-i002 data-source-page="81" data-source-order="2"}
- Dua himpunan $C_1$ dan $C_2$ dikatakan **dipisahkan** oleh hiperbidang $H=\{x\mid a'x=b\}$ jika masing-masing terletak di setengah-ruang tertutup berbeda yang terkait dengan $H$, yaitu

  salah satu dari

  ::: {.source-display #d90-mit-l10-p081-d001 data-source-page="81" data-display-order="1"}
  $$
  a'x_1\leq b\leq a'x_2,
  \qquad \forall x_1\in C_1,\quad \forall x_2\in C_2,
  $$
  :::

  atau

  ::: {.source-display #d90-mit-l10-p081-d002 data-source-page="81" data-display-order="2"}
  $$
  a'x_2\leq b\leq a'x_1,
  \qquad \forall x_1\in C_1,\quad \forall x_2\in C_2.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p081-i003 data-source-page="81" data-source-order="3"}
- Jika $\bar{x}$ termasuk dalam penutupan suatu himpunan $C$, hiperbidang
  yang memisahkan $C$ dan himpunan singleton $\{\bar{x}\}$ disebut
  **hiperbidang pendukung bagi $C$ di $\bar{x}$**.
:::

*[Halaman sumber 81.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p082 data-source-page="82" data-source-order="19"}
## Visualisasi

::: {.source-item #d90-mit-l10-p082-i001 data-source-page="82" data-source-order="1"}
- Hiperbidang pemisah dan pendukung:
:::

::: {.source-figure #d90-mit-l10-p082-f001 data-source-page="82" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber pertama.** Panel (a) menempatkan daerah konveks $C_1$ dan $C_2$ pada sisi berlawanan dari sebuah garis miring; panah pendek $a$ tegak lurus terhadap garis itu. Pada panel (b), garis lain hanya menyentuh daerah konveks $C$ di titik batas $\bar{x}$, dengan $a$ sebagai normalnya. Pasangan panel membedakan pemisahan dua himpunan dari dukungan terhadap satu himpunan pada titik batas.
:::

::: {.source-item #d90-mit-l10-p082-i002 data-source-page="82" data-source-order="2"}
- Hiperbidang pemisah $\{x\mid a'x=b\}$ yang tidak beririsan dengan $C_1$ maupun $C_2$ disebut **memisahkan secara ketat** jika

  ::: {.source-display #d90-mit-l10-p082-d001 data-source-page="82" data-display-order="1"}
  $$
  a'x_1<b<a'x_2,
  \qquad \forall x_1\in C_1,\quad \forall x_2\in C_2.
  $$
  :::
:::

::: {.source-figure #d90-mit-l10-p082-f002 data-source-page="82" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber kedua.** Panel (a) memperlihatkan $C_1$ di samping batas vertikal dan $C_2$ sebagai daerah tak terbatas dengan batas melengkung. Pada panel (b), daerah melengkung $C_1$ terpisah dari daerah oval $C_2$. Ruas yang menghubungkan $\bar{x}_1\in C_1$ dengan $\bar{x}_2\in C_2$ melalui $\bar{x}$, sedangkan garis melalui $\bar{x}$ berarah tegak lurus terhadap normal $a$. Panel kanan menampilkan celah ketat dan orientasi pemisah secara geometris.
:::

*[Halaman sumber 82.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p083 data-source-page="83" data-source-order="20"}
## Teorema Hiperbidang Pendukung

::: {.source-item #d90-mit-l10-p083-i001 data-source-page="83" data-source-order="1"}
- Misalkan $C$ konveks dan $\bar{x}$ suatu vektor yang bukan titik interior $C$. Maka terdapat hiperbidang yang melalui $\bar{x}$ dan memuat $C$ di salah satu setengah-ruang tertutupnya.
:::

::: {.source-figure #d90-mit-l10-p083-f001 data-source-page="83" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber.** Di luar daerah konveks $C$, titik-titik $x_0,x_1,x_2,x_3$ bergerak menuju titik batas $\bar{x}$. Untuk setiap $k$, titik $x_k$ dihubungkan ke proyeksi terdekatnya $\hat{x}_k$ pada $\operatorname{cl}(C)$, dan vektor satuan $a_k$ mengarah dari $x_k$ ke $\hat{x}_k$. Proyeksi-proyeksi tersebut juga mendekati $\bar{x}$. Pada limit, garis melalui $\bar{x}$ dengan normal $a$ menempatkan seluruh $C$ pada satu sisi tertutup.
:::

::: {.source-item #d90-mit-l10-p083-i002 data-source-page="83" data-source-order="2"}
**Bukti:** Ambil barisan $\{x_k\}$ di luar $\operatorname{cl}(C)$ yang konvergen ke $\bar{x}$. Misalkan $\hat{x}_k$ adalah proyeksi $x_k$ pada $\operatorname{cl}(C)$. Untuk semua $x\in\operatorname{cl}(C)$ berlaku

::: {.source-display #d90-mit-l10-p083-d001 data-source-page="83" data-display-order="1"}
$$
a_k'x\geq a_k'x_k,
\qquad \forall x\in\operatorname{cl}(C),
\quad \forall k=0,1,\ldots,
$$
:::

dengan

::: {.source-display #d90-mit-l10-p083-d002 data-source-page="83" data-display-order="2"}
$$
a_k=\frac{\hat{x}_k-x_k}{\lVert\hat{x}_k-x_k\rVert}.
$$
:::

Misalkan $a$ suatu titik limit dari $\{a_k\}$, lalu ambil limit ketika $k\to\infty$. **Q.E.D.**
:::

*[Halaman sumber 83.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l10-p084-n001 data-source-page="84" data-correction-event="O015-MIT-SEM-0029"}
**Koreksi label selisih himpunan yang ditentukan.** Sumber mencetak label
$C_1-C_2$ untuk himpunan $\{x_2-x_1\}$. Dengan konvensi selisih standar dan
konsisten dengan halaman 85, himpunan itu adalah $C_2-C_1$. Edisi ini
memperbaiki label; orientasi ketaksamaan dan simpulan teorema tidak berubah.
:::

::: {.source-page #d90-mit-l10-p084 data-source-page="84" data-source-order="21"}
## Teorema Hiperbidang Pemisah

::: {.source-item #d90-mit-l10-p084-i001 data-source-page="84" data-source-order="1"}
- Misalkan $C_1$ dan $C_2$ adalah dua himpunan bagian konveks tak kosong dari $\mathbb R^n$. Jika $C_1$ dan $C_2$ saling lepas, terdapat hiperbidang yang memisahkan keduanya; dengan kata lain, terdapat vektor $a\neq0$ sedemikian sehingga

  ::: {.source-display #d90-mit-l10-p084-d001 data-source-page="84" data-display-order="1"}
  $$
  a'x_1\leq a'x_2,
  \qquad \forall x_1\in C_1,\quad \forall x_2\in C_2.
  $$
  :::
:::

::: {.source-item #d90-mit-l10-p084-i002 data-source-page="84" data-source-order="2"}
**Bukti:** Perhatikan himpunan konveks

::: {.source-display #d90-mit-l10-p084-d002 data-source-page="84" data-display-order="2"}
$$
C_2-C_1=\{x_2-x_1\mid x_1\in C_1,\ x_2\in C_2\}.
$$
:::

Karena $C_1$ dan $C_2$ saling lepas, titik asal tidak termasuk dalam $C_2-C_1$. Menurut Teorema Hiperbidang Pendukung, terdapat vektor $a\neq0$ sedemikian sehingga

::: {.source-display #d90-mit-l10-p084-d003 data-source-page="84" data-display-order="3"}
$$
0\leq a'x,
\qquad \forall x\in C_2-C_1,
$$
:::

yang ekuivalen dengan relasi yang diinginkan. **Q.E.D.**
:::

*[Halaman sumber 84.]{.source-locator}*
:::

::: {.source-page #d90-mit-l10-p085 data-source-page="85" data-source-order="22"}
## Teorema Pemisahan Ketat

::: {.source-item #d90-mit-l10-p085-i001 data-source-page="85" data-source-order="1"}
- **Teorema Pemisahan Ketat:** Misalkan $C_1$ dan $C_2$ dua himpunan konveks tak kosong yang saling lepas. Jika $C_1$ tertutup dan $C_2$ kompak, terdapat hiperbidang yang memisahkan keduanya secara ketat.
:::

::: {.source-figure #d90-mit-l10-p085-f001 data-source-page="85" data-figure-disposition="omitted-source-graphic"}
**Deskripsi semantik gambar sumber.** Panel (a) menempatkan $C_1$ di sisi sebuah batas vertikal dan $C_2$ sebagai himpunan tak terbatas dengan batas melengkung. Panel (b) menunjukkan $C_1$ yang melengkung dan $C_2$ yang berbentuk oval, beserta titik terdekat $\bar{x}_1$ dan $\bar{x}_2$. Ruas antara kedua titik itu melewati $\bar{x}$ dan memotong garis pemisah secara tegak lurus; panah $a$ menyatakan normal garis. Konstruksi bukti merujuk khusus pada geometri titik terdekat di panel (b).
:::

::: {.source-item #d90-mit-l10-p085-i002 data-source-page="85" data-source-order="2"}
**Bukti:** (Garis besar) Perhatikan himpunan $C_1-C_2$. Karena $C_1$ tertutup dan $C_2$ kompak, $C_1-C_2$ tertutup. Karena

::: {.source-display #d90-mit-l10-p085-d001 data-source-page="85" data-display-order="1"}
$$
C_1\cap C_2=\varnothing,
\qquad 0\notin C_1-C_2,
$$
:::

misalkan $\bar{x}_1-\bar{x}_2$ adalah proyeksi $0$ pada $C_1-C_2$. Hiperbidang pemisah ketat dikonstruksi seperti pada panel (b).
:::

::: {.source-item #d90-mit-l10-p085-i003 data-source-page="85" data-source-order="3"}
- **Catatan:** Sebarang syarat yang menjamin ketertutupan $C_1-C_2$ menjamin keberadaan hiperbidang pemisah ketat. Namun, hiperbidang pemisah ketat dapat saja ada meskipun $C_1-C_2$ tidak tertutup.
:::

*[Halaman sumber 85.]{.source-locator}*
:::
