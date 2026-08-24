---
title: "Kuliah 7: Pemisahan, Hiperbidang Nonvertikal, dan Konjugasi"
subtitle: "Edisi semantik Bahasa Indonesia - MIT OpenCourseWare 6.253, halaman sumber 86-97"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
  - "Edisi Bahasa Indonesia (terjemahan dan rekonstruksi semantik)"
lang: id-ID
date: "2026-08-24"
rights: "CC BY-NC-SA 4.0"
---

::: {.edition-notice}
**Tentang edisi ini.** Unit ini menerjemahkan seluruh Kuliah 7 pada halaman PDF sumber 86-97. Halaman 98 memulai Kuliah 8 dan tidak termasuk. Saksi Inggris yang dapat dialamatkan baris berada di `source/en/mit-11-lecture-7-separation-conjugacy-semantic-witness.md`; saksi tersebut adalah transkripsi proyek, bukan sumber sunting resmi MIT.

Materi turunan MIT tetap berada di bawah **CC BY-NC-SA 4.0** dengan atribusi, penandaan perubahan, kewajiban nonkomersial dan BerbagiSerupa, serta tanpa dukungan tersirat. Tidak ada byte, potongan, atau tata letak gambar Athena Scientific yang disalin. Tujuh blok gambar dengan enam belas panel diganti oleh deskripsi semantik mandiri yang mempertahankan label dan hubungan matematisnya.

Batas sumber ini tidak mempunyai latihan peserta didik, petunjuk, jawaban, solusi latihan, kode, data, tautan, anotasi, widget, media, atau permukaan interaktif. Tiga contoh dan satu kontra-contoh ekspositori dipertahankan. Tidak ada isi yang diada-adakan. Rumus diketik ulang dan diperiksa terhadap render karena pemetaan glif sumber merusak beberapa simbol ketika diekstrak sebagai teks. Sepuluh koreksi yang dapat ditentukan secara matematis diungkapkan di dekat lokatornya dan dicatat dalam ledger proyek.

Terjemahan, rekonstruksi semantik, pembangunan pembaca, dan QA dibantu oleh **OpenAI Codex gpt-5.6-sol, Ultra** atas arahan pengguna repositori. Sistem tersebut bukan penulis sumber, pemberi lisensi, atau wakil MIT. Tinjauan manusia/penutur asli belum tercatat dan bukan penahan penerbitan.
:::

::: {.source-page #d90-mit-l11-p086 data-source-page="86" data-source-order="1"}
## Kuliah 7 - Garis Besar Kuliah

::: {.source-item #d90-mit-l11-p086-i001 data-source-page="86" data-source-order="1"}
- Tinjauan pemisahan hiperbidang
:::

::: {.source-item #d90-mit-l11-p086-i002 data-source-page="86" data-source-order="2"}
- Hiperbidang nonvertikal
:::

::: {.source-item #d90-mit-l11-p086-i003 data-source-page="86" data-source-order="3"}
- Fungsi konjugat konveks
:::

::: {.source-item #d90-mit-l11-p086-i004 data-source-page="86" data-source-order="4"}
- Teorema konjugasi
:::

::: {.source-item #d90-mit-l11-p086-i005 data-source-page="86" data-source-order="5"}
- Contoh
:::

::: {.source-item #d90-mit-l11-p086-i006 data-source-page="86" data-source-order="6"}
**Bacaan:** Bagian 1.5 dan 1.6.
:::

*[Halaman sumber 86.]{.source-locator}*
:::

::: {.source-page #d90-mit-l11-p087 data-source-page="87" data-source-order="2"}
## Teorema Tambahan

::: {.source-item #d90-mit-l11-p087-i001 data-source-page="87" data-source-order="1"}
- **Karakterisasi fundamental:** Tutupan selubung konveks suatu himpunan
  $C\subset\mathbb R^n$ adalah irisan semua setengah ruang tertutup yang
  memuat $C$. (Buktinya memakai teorema pemisahan ketat.)
:::

::: {.source-item #d90-mit-l11-p087-i002 data-source-page="87" data-source-order="2"}
- Suatu hiperbidang *memisahkan $C_1$ dan $C_2$ secara proper* jika
  hiperbidang itu memisahkan $C_1$ dan $C_2$ serta tidak sepenuhnya memuat
  keduanya.
:::

::: {.source-figure #d90-mit-l11-p087-f001 data-source-page="87" data-figure-disposition="omitted-source-graphic" data-panel-count="3"}
**Deskripsi semantik gambar sumber.** Tiga panel membandingkan geometri
pemisahan proper. Panel (a) memperlihatkan dua himpunan konveks yang bertemu
garis pemisah pada bagian berbeda, tanpa keduanya termuat di dalam garis itu.
Panel (b) memperlihatkan dua himpunan konveks tipis pada sisi berlawanan suatu
pemisah miring dan menyentuhnya di lokasi berbeda. Panel (c) menempatkan kedua
himpunan tipis pada garis miring yang sama; inilah kasus yang dikecualikan,
karena hiperbidang memuat keduanya sepenuhnya. Setiap panel menandai vektor
normal $a$.
:::

::: {.source-item #d90-mit-l11-p087-i003 data-source-page="87" data-source-order="3"}
- **Teorema pemisahan proper:** Misalkan $C_1$ dan $C_2$ dua himpunan bagian
  konveks tak kosong dari $\mathbb R^n$. Ada hiperbidang yang memisahkan
  $C_1$ dan $C_2$ secara proper jika dan hanya jika

::: {.source-display #d90-mit-l11-p087-d001 data-source-page="87" data-display-order="1"}
$$
\operatorname{ri}(C_1)\cap\operatorname{ri}(C_2)=\varnothing.
$$
:::
:::

*[Halaman sumber 87.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p088-n001 data-source-page="88" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0034"}
**Koreksi cakupan yang ditentukan.** Teorema tidak mengasumsikan bahwa $C$
nonpolihedral, walaupun sumber menyebut “the nonpolyhedral set $C$.” Edisi ini
memakai cakupan sebenarnya: $C$ tidak harus polihedral.
:::

::: {.source-page #d90-mit-l11-p088 data-source-page="88" data-source-order="3"}
## Pemisahan Polihedral Proper

::: {.source-item #d90-mit-l11-p088-i001 data-source-page="88" data-source-order="1"}
- Ingat bahwa dua himpunan konveks $C$ dan $P$ yang memenuhi

::: {.source-display #d90-mit-l11-p088-d001 data-source-page="88" data-display-order="1"}
$$
\operatorname{ri}(C)\cap\operatorname{ri}(P)=\varnothing
$$
:::

  dapat dipisahkan secara proper, yaitu oleh hiperbidang yang tidak memuat
  $C$ dan $P$ sekaligus.
:::

::: {.source-item #d90-mit-l11-p088-i002 data-source-page="88" data-source-order="2"}
- Jika $P$ polihedral dan syarat yang sedikit lebih kuat

::: {.source-display #d90-mit-l11-p088-d002 data-source-page="88" data-display-order="2"}
$$
\operatorname{ri}(C)\cap P=\varnothing
$$
:::

  berlaku, hiperbidang pemisah proper dapat dipilih agar tidak memuat $C$,
  yang tidak harus polihedral, sedangkan hiperbidang itu boleh memuat $P$.
:::

::: {.source-figure #d90-mit-l11-p088-f001 data-source-page="88" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Deskripsi semantik gambar sumber.** Panel (a) memperlihatkan himpunan
polihedral $P$ yang bertemu himpunan konveks tipis $C$ pada garis pemisah.
Pemisah miring kedua dengan normal $a$ dapat diputar sehingga tidak memuat
$C$. Panel (b) mengganti $P$ dengan oval mulus yang menyinggung himpunan tipis
$C$; satu-satunya pemisah yang ditampilkan adalah garis singgung bersama dan
karena itu memuat $C$. Perbandingan tersebut mengisolasi peran
polihedralitas.
:::

::: {.source-item #d90-mit-l11-p088-i003 data-source-page="88" data-source-order="3"}
Di sebelah kiri, hiperbidang pemisah dapat dipilih agar tidak memuat $C$. Di
sebelah kanan, ketika $P$ tidak polihedral, pilihan semacam itu tidak mungkin.
:::

*[Halaman sumber 88.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p089-n001 data-source-page="89" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0035"}
**Klarifikasi geometri yang ditentukan.** Setiap epigraf memuat sinar vertikal
ke atas, sehingga frasa sumber “vertical line” dapat menyesatkan. Pernyataan
yang diperlukan adalah tidak adanya garis vertikal dua arah yang lengkap;
edisi ini menyatakannya secara eksplisit.
:::

::: {.source-page #d90-mit-l11-p089 data-source-page="89" data-source-order="4"}
## Hiperbidang Nonvertikal

::: {.source-item #d90-mit-l11-p089-i001 data-source-page="89" data-source-order="1"}
Hiperbidang di $\mathbb R^{n+1}$ dengan normal $(\mu,\beta)$ disebut
nonvertikal jika $\beta\neq0$.
:::

::: {.source-item #d90-mit-l11-p089-i002 data-source-page="89" data-source-order="2"}
- Hiperbidang itu memotong sumbu ke-$(n+1)$ pada
  $\xi=(\mu/\beta)'\bar u+\bar w$, dengan $(\bar u,\bar w)$ sebarang vektor
  pada hiperbidang tersebut.
:::

::: {.source-figure #d90-mit-l11-p089-f001 data-source-page="89" data-figure-disposition="omitted-source-graphic" data-panel-count="2"}
**Deskripsi semantik gambar sumber.** Pada sistem sumbu $(u,w)$ yang sama
terdapat dua konstruksi yang terpisah secara visual. Di kiri, hiperbidang
nonvertikal miring melalui $(\bar u,\bar w)$ dan memotong sumbu vertikal pada
$(\mu/\beta)'\bar u+\bar w$; normalnya ialah $(\mu,\beta)$. Di kanan,
hiperbidang vertikal digambar pada $u$ tetap dengan normal $(\mu,0)$.
Perbandingan itu membuat perbedaan kedua jenis hiperbidang menjadi eksplisit.
:::

::: {.source-item #d90-mit-l11-p089-i003 data-source-page="89" data-source-order="3"}
- Hiperbidang nonvertikal yang menempatkan epigraf suatu fungsi di setengah
  ruang “atas” memberikan batas bawah bagi nilai fungsi tersebut.
:::

::: {.source-item #d90-mit-l11-p089-i004 data-source-page="89" data-source-order="4"}
- Epigraf fungsi konveks proper tidak memuat garis vertikal dua arah yang
  lengkap. Karena itu, masuk akal bahwa epigraf tersebut termuat dalam
  setengah ruang “atas” suatu hiperbidang nonvertikal.
:::

*[Halaman sumber 89.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p090-n001 data-source-page="90" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0036"}
**Perincian langkah bukti yang ditentukan.** Sumber hanya menyuruh
“menambahkan” kelipatan-$\epsilon$ kecil dari suatu hiperbidang nonvertikal.
Edisi ini menyatakan orientasi, pelestarian tanda pada $C$, dan margin positif
kecil yang membuat perturbasi itu sah.
:::

::: {.source-page #d90-mit-l11-p090 data-source-page="90" data-source-order="5"}
## Teorema Hiperbidang Nonvertikal

::: {.source-item #d90-mit-l11-p090-i001 data-source-page="90" data-source-order="1"}
- Misalkan $C$ himpunan bagian konveks tak kosong dari $\mathbb R^{n+1}$ yang
  tidak memuat garis vertikal dua arah. Maka:

  (a) $C$ termuat dalam setengah ruang tertutup suatu hiperbidang
  nonvertikal. Dengan kata lain, terdapat $\mu\in\mathbb R^n$,
  $\beta\in\mathbb R$ dengan $\beta\neq0$, dan $\gamma\in\mathbb R$
  sedemikian sehingga

::: {.source-display #d90-mit-l11-p090-d001 data-source-page="90" data-display-order="1"}
$$
\mu'u+\beta w\geq\gamma
\qquad\text{untuk semua }(u,w)\in C.
$$
:::

  (b) Jika $(\bar u,\bar w)\notin\operatorname{cl}(C)$, terdapat hiperbidang
  nonvertikal yang memisahkan $(\bar u,\bar w)$ dan $C$ secara ketat.
:::

::: {.source-item #d90-mit-l11-p090-i002 data-source-page="90" data-source-order="2"}
**Bukti:** Perhatikan bahwa $\operatorname{cl}(C)$ tidak memuat garis vertikal
dua arah. Memang, $C$ tidak memuat garis demikian, $\operatorname{ri}(C)$
juga tidak, sedangkan $\operatorname{ri}(C)$ dan $\operatorname{cl}(C)$
mempunyai kerucut resesi yang sama. Jadi cukup ditinjau kasus ketika $C$
tertutup.
:::

::: {.source-item #d90-mit-l11-p090-i003 data-source-page="90" data-source-order="3"}
**(a)** Himpunan $C$ adalah irisan semua setengah ruang tertutup yang memuat
$C$. Jika semuanya bersesuaian dengan hiperbidang vertikal, $C$ akan memuat
garis vertikal dua arah.
:::

::: {.source-item #d90-mit-l11-p090-i004 data-source-page="90" data-source-order="4"}
**(b)** Ada hiperbidang yang memisahkan $(\bar u,\bar w)$ dan $C$ secara
ketat. Jika hiperbidang itu nonvertikal, hasilnya langsung diperoleh. Jika
vertikal, orientasikan fungsi afin pemisahnya $g_0$ sehingga
$g_0\geq0$ pada $C$ dan $g_0(\bar u,\bar w)<0$. Dari bagian (a), orientasikan
fungsi setengah ruang nonvertikal $h$ sehingga $h\geq0$ pada $C$. Untuk
$\epsilon>0$, fungsi $g_\epsilon=g_0+\epsilon h$ tetap tak negatif pada $C$
dan nonvertikal. Karena $g_0(\bar u,\bar w)<0$ dan
$h(\bar u,\bar w)$ berhingga, $g_\epsilon(\bar u,\bar w)<0$ tetap berlaku
untuk $\epsilon>0$ yang cukup kecil. Jadi hiperbidang $g_\epsilon=0$
memberikan pemisahan ketat yang diminta.
:::

*[Halaman sumber 90.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p091-n001 data-source-page="91" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0037"}
**Koreksi syarat ketercapaian yang ditentukan.** Batas bawah afin nonvertikal
tidak harus menyentuh $\operatorname{epi}(f)$ ketika supremum yang
mendefinisikan $f^*(y)$ tidak tercapai. Edisi ini menyebutnya hiperbidang
pemberi batas bawah; hiperbidang tersebut disebut pendukung hanya jika
supremumnya tercapai.
:::

::: {.edition-correction #d90-mit-l11-p091-n002 data-source-pages="91,95" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0040"}
**Koreksi tanda tipe fungsi yang ditentukan.** Sumber memakai $\mapsto$ di
antara domain dan kodomain pada halaman 91 dan 95. Edisi ini memakai tanda
tipe fungsi $\to$; tanda $\mapsto$ dicadangkan untuk pemetaan unsur ke nilai.
:::

::: {.source-page #d90-mit-l11-p091 data-source-page="91" data-source-order="6"}
## Fungsi Konjugat Konveks

::: {.source-item #d90-mit-l11-p091-i001 data-source-page="91" data-source-order="1"}
Perhatikan fungsi $f$ dan epigrafnya. Hiperbidang nonvertikal yang memberi
batas bawah pada $\operatorname{epi}(f)$ bersesuaian dengan titik potong pada
sumbu vertikal; bila supremum berikut tercapai, hiperbidangnya benar-benar
pendukung:

::: {.source-display #d90-mit-l11-p091-d001 data-source-page="91" data-display-order="1"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n.
$$
:::
:::

::: {.source-figure #d90-mit-l11-p091-f001 data-source-page="91" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Deskripsi semantik gambar sumber.** Kurva $f(x)$ diberi batas bawah oleh
garis berkemiringan $y$ dan bernormal $(-y,1)$. Garis tersebut menjadi garis
pendukung ketika menyentuh grafik pada suatu pemaksimum. Titik potongnya pada
sumbu vertikal berlabel
$\inf_{x\in\mathbb R^n}\{f(x)-x'y\}=-f^*(y)$. Geometri itu menghubungkan
parameter kemiringan $y$ dengan nilai konjugat konveks.
:::

::: {.source-item #d90-mit-l11-p091-i002 data-source-page="91" data-source-order="2"}
- Untuk sebarang $f:\mathbb R^n\to[-\infty,+\infty]$, fungsi konjugat
  konveksnya didefinisikan oleh

::: {.source-display #d90-mit-l11-p091-d002 data-source-page="91" data-display-order="2"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n.
$$
:::
:::

*[Halaman sumber 91.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p092-n001 data-source-page="92" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0031"}
**Koreksi asumsi yang ditentukan.** Contoh kuadratik sumber tidak menyatakan
$c>0$. Positivitas diperlukan agar fungsi yang ditampilkan proper dan konveks
serta agar rumus konjugat berhingga yang dicetak berlaku; edisi ini
menambahkannya.
:::

::: {.source-page #d90-mit-l11-p092 data-source-page="92" data-source-order="7"}
## Contoh

::: {.source-item #d90-mit-l11-p092-i001 data-source-page="92" data-source-order="1"}
Ketiga contoh memakai definisi

::: {.source-display #d90-mit-l11-p092-d001 data-source-page="92" data-display-order="1"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n.
$$
:::
:::

::: {.source-figure #d90-mit-l11-p092-f001 data-source-page="92" data-figure-disposition="omitted-source-graphic" data-panel-count="6"}
**Deskripsi semantik gambar sumber.** Enam panel sumber direka ulang secara
semantik sebagai tiga pasangan yang ditumpuk agar terbaca pada layar sempit:

1. **Fungsi afin.** Jika $f(x)=\alpha x-\beta$, maka
   $f^*(y)=\beta$ untuk $y=\alpha$ dan $f^*(y)=+\infty$ untuk
   $y\neq\alpha$. Grafik memasangkan sebuah garis dengan satu titik konjugat
   berhingga.
2. **Nilai mutlak.** Jika $f(x)=|x|$, maka $f^*(y)=0$ untuk $|y|\leq1$ dan
   $f^*(y)=+\infty$ untuk $|y|>1$. Grafik memasangkan bentuk V dengan
   indikator konveks interval $[-1,1]$.
3. **Kuadratik.** Jika $f(x)=(c/2)x^2$ dengan $c>0$, maka
   $f^*(y)=(1/2c)y^2$. Grafik memasangkan dua parabola dengan kelengkungan
   resiprokal.
:::

*[Halaman sumber 92.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p093-n001 data-source-page="93" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0038"}
**Koreksi istilah yang ditentukan.** Untuk $x$ tetap, fungsi
$y\mapsto x'y-f(x)$ bersifat afin dan hanya linear ketika $f(x)=0$. Edisi ini
memakai istilah “fungsi afin.”
:::

::: {.source-page #d90-mit-l11-p093 data-source-page="93" data-source-order="8"}
## Konjugat dari Konjugat

::: {.source-item #d90-mit-l11-p093-i001 data-source-page="93" data-source-order="1"}
- Dari definisi

::: {.source-display #d90-mit-l11-p093-d001 data-source-page="93" data-display-order="1"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n,
$$
:::

  tampak bahwa $f^*$ konveks dan tertutup.
:::

::: {.source-item #d90-mit-l11-p093-i002 data-source-page="93" data-source-order="2"}
- **Alasan:** $\operatorname{epi}(f^*)$ adalah irisan epigraf fungsi-fungsi
  afin terhadap $y$,

::: {.source-display #d90-mit-l11-p093-d002 data-source-page="93" data-display-order="2"}
$$
x'y-f(x),
$$
:::

  ketika $x$ merentang $\mathbb R^n$.
:::

::: {.source-item #d90-mit-l11-p093-i003 data-source-page="93" data-source-order="3"}
- Perhatikan konjugat dari konjugat:

::: {.source-display #d90-mit-l11-p093-d003 data-source-page="93" data-display-order="3"}
$$
f^{**}(x)=\sup_{y\in\mathbb R^n}\{y'x-f^*(y)\},
\qquad x\in\mathbb R^n.
$$
:::
:::

::: {.source-item #d90-mit-l11-p093-i004 data-source-page="93" data-source-order="4"}
- Fungsi $f^{**}$ konveks dan tertutup.
:::

::: {.source-item #d90-mit-l11-p093-i005 data-source-page="93" data-source-order="5"}
- **Fakta penting / teorema konjugasi:** Jika $f$ tertutup, proper, dan
  konveks, maka $f^{**}=f$.
:::

*[Halaman sumber 93.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p094-n001 data-source-page="94" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0039"}
**Klarifikasi visual yang ditentukan.** Gambar sumber tampak memakai $f$ yang
nonkonveks, tepat setelah pernyataan kesamaan untuk $f$ tertutup, proper, dan
konveks. Edisi ini menyatakan bahwa gambar memperlihatkan hubungan amplop
umum $f^{**}\leq f$; kesamaan adalah kasus khusus di bawah hipotesis teorema.
:::

::: {.source-page #d90-mit-l11-p094 data-source-page="94" data-source-order="9"}
## Teorema Konjugasi - Visualisasi

::: {.source-item #d90-mit-l11-p094-i001 data-source-page="94" data-source-order="1"}
Visualisasi mengulangi

::: {.source-display #d90-mit-l11-p094-d001 data-source-page="94" data-display-order="1"}
$$
f^*(y)=\sup_{x\in\mathbb R^n}\{x'y-f(x)\},
\qquad y\in\mathbb R^n,
$$
:::

dan

::: {.source-display #d90-mit-l11-p094-d002 data-source-page="94" data-display-order="2"}
$$
f^{**}(x)=\sup_{y\in\mathbb R^n}\{y'x-f^*(y)\},
\qquad x\in\mathbb R^n.
$$
:::

- Jika $f$ tertutup, konveks, dan proper, maka $f^{**}=f$.
:::

::: {.source-figure #d90-mit-l11-p094-f001 data-source-page="94" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Deskripsi semantik gambar sumber.** Grafik $f$ yang mungkin nonkonveks
dibandingkan dengan amplop bawah yang direkonstruksi oleh bikonjugatnya,
sehingga secara umum $f^{**}\leq f$. Garis berkemiringan $y$ dan bernormal
$(-y,1)$ memberi batas bawah; titik potong vertikalnya ialah $-f^*(y)$. Pada
koordinat horizontal $x$ yang tetap, supremum $y'x-f^*(y)$ ditandai pada
kurva rekonstruksi. Sumber memberi label hiperbidang
$H=\{(x,w)\mid w-x'y=-f^*(y)\}$ dan menghubungkan titik potongnya dengan dua
rumus konjugasi. Jika $f$ tertutup, proper, dan konveks, amplop ini sama
dengan $f$.
:::

*[Halaman sumber 94.]{.source-locator}*
:::

::: {.source-page #d90-mit-l11-p095 data-source-page="95" data-source-order="10"}
## Teorema Konjugasi

::: {.source-item #d90-mit-l11-p095-i001 data-source-page="95" data-source-order="1"}
- Misalkan $f:\mathbb R^n\to(-\infty,+\infty]$ suatu fungsi, misalkan
  $\check{\operatorname{cl}}f$ tutupan konveksnya, misalkan $f^*$ konjugat
  konveksnya, dan perhatikan konjugat dari $f^*$,

::: {.source-display #d90-mit-l11-p095-d001 data-source-page="95" data-display-order="1"}
$$
f^{**}(x)=\sup_{y\in\mathbb R^n}\{y'x-f^*(y)\},
\qquad x\in\mathbb R^n.
$$
:::

  (a) Kita mempunyai

::: {.source-display #d90-mit-l11-p095-d002 data-source-page="95" data-display-order="2"}
$$
f(x)\geq f^{**}(x),
\qquad\forall x\in\mathbb R^n.
$$
:::

  (b) Jika $f$ konveks, keproperan salah satu dari $f$, $f^*$, dan $f^{**}$
  mengakibatkan keproperan dua yang lain.

  (c) Jika $f$ tertutup, proper, dan konveks, maka

::: {.source-display #d90-mit-l11-p095-d003 data-source-page="95" data-display-order="3"}
$$
f(x)=f^{**}(x),
\qquad\forall x\in\mathbb R^n.
$$
:::

  (d) Jika $\check{\operatorname{cl}}f(x)>-\infty$ untuk semua
  $x\in\mathbb R^n$, maka

::: {.source-display #d90-mit-l11-p095-d004 data-source-page="95" data-display-order="4"}
$$
\check{\operatorname{cl}}f(x)=f^{**}(x),
\qquad\forall x\in\mathbb R^n.
$$
:::
:::

*[Halaman sumber 95.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p096-n001 data-source-page="96" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0032"}
**Perbaikan bukti yang ditentukan.** Label titik potong vertikal sumber
$x'y-f(x)$ dan $x'y-f^{**}(x)$ mempunyai tanda berlawanan dari titik potong
sebenarnya untuk hiperbidang bernormal $(y,-1)$, dan baris akhir tidak
menyatakan kontradiksinya. Edisi ini mengganti simpulan geometris yang cacat
dengan argumen ketaksamaan langsung dari pemisah ketat yang sama.
:::

::: {.source-page #d90-mit-l11-p096 data-source-page="96" data-source-order="11"}
## Bukti Teorema Konjugasi (a), (c)

::: {.source-item #d90-mit-l11-p096-i001 data-source-page="96" data-source-order="1"}
- **(a)** Untuk semua $x,y$, berlaku $f^*(y)\geq y'x-f(x)$. Akibatnya,
  $f(x)\geq\sup_y\{y'x-f^*(y)\}=f^{**}(x)$.
:::

::: {.source-item #d90-mit-l11-p096-i002 data-source-page="96" data-source-order="2"}
- **(c)** Dengan kontradiksi, andaikan ada
  $(x,\gamma)\in\operatorname{epi}(f^{**})$ tetapi
  $(x,\gamma)\notin\operatorname{epi}(f)$. Ada hiperbidang nonvertikal
  bernormal $(y,-1)$ yang memisahkan $(x,\gamma)$ dari
  $\operatorname{epi}(f)$ secara ketat. (Komponen vertikal vektor normal
  dinormalkan menjadi $-1$.)
:::

::: {.source-figure #d90-mit-l11-p096-f001 data-source-page="96" data-figure-disposition="omitted-source-graphic" data-panel-count="1"}
**Deskripsi semantik gambar sumber dengan tanda yang diperbaiki.** Epigraf
$f$ berada di atas epigraf $f^{**}$. Pada koordinat horizontal $x$ yang sama,
titik $(x,f(x))$, $(x,\gamma)$, dan $(x,f^{**}(x))$ segaris vertikal.
Hiperbidang bernormal $(y,-1)$ memisahkan titik tengah dari
$\operatorname{epi}(f)$, sedangkan dua translasi sejajar melalui titik grafik
atas dan bawah. Untuk normal $(y,-1)$, titik potong vertikal kedua translasi
yang benar ialah $f(x)-x'y$ dan $f^{**}(x)-x'y$.
:::

::: {.source-item #d90-mit-l11-p096-i003 .keep-proof-conclusion data-source-page="96" data-source-order="3"}
- Orientasikan pemisah ketat sebagai
  $f(u)\geq y'u-c$ untuk semua $u$, dengan
  $\gamma<y'x-c$. Ketaksamaan pertama memberi
  $f^*(y)=\sup_u\{y'u-f(u)\}\leq c$. Karena itu,

::: {.source-display #d90-mit-l11-p096-d001 data-source-page="96" data-display-order="1"}
$$
f^{**}(x)
\geq y'x-f^*(y)
\geq y'x-c
>\gamma.
$$
:::

  Akan tetapi, $(x,\gamma)\in\operatorname{epi}(f^{**})$ berarti
  $\gamma\geq f^{**}(x)$. Ini kontradiksi. **Terbukti.**
:::

*[Halaman sumber 96.]{.source-locator}*
:::

::: {.edition-correction #d90-mit-l11-p097-n001 data-source-page="97" data-correction-status="determined" data-correction-event="O015-MIT-SEM-0033"}
**Koreksi dimensi dan kodomain yang ditentukan.** Kontra-contoh membandingkan
$x$ dengan $0$ sehingga bersifat skalar, tetapi dua kuantor sumber memakai
$\mathbb R^n$. Contoh ini juga mengizinkan nilai $-\infty$, berbeda dari
kodomain pada halaman 95. Edisi ini menyatakan
$f:\mathbb R\to[-\infty,+\infty]$ dan memakai kuantor pada $\mathbb R$
secara konsisten.
:::

::: {.source-page #d90-mit-l11-p097 data-source-page="97" data-source-order="12"}
## Sebuah Kontra-Contoh

::: {.source-item #d90-mit-l11-p097-i001 data-source-page="97" data-source-order="1"}
Sebuah kontra-contoh dengan fungsi $f:\mathbb R\to[-\infty,+\infty]$ yang
tertutup dan konveks tetapi tak proper menunjukkan perlunya asumsi proper agar
$f=f^{**}$:

::: {.source-display #d90-mit-l11-p097-d001 data-source-page="97" data-display-order="1"}
$$
f(x)=
\begin{cases}
+\infty,&x>0,\\
-\infty,&x\leq0.
\end{cases}
$$
:::
:::

::: {.source-item #d90-mit-l11-p097-i002 data-source-page="97" data-source-order="2"}
Kita mempunyai

::: {.source-display #d90-mit-l11-p097-d002 data-source-page="97" data-display-order="2"}
$$
f^*(y)=+\infty,
\qquad\forall y\in\mathbb R,
$$
:::

dan

::: {.source-display #d90-mit-l11-p097-d003 data-source-page="97" data-display-order="3"}
$$
f^{**}(x)=-\infty,
\qquad\forall x\in\mathbb R.
$$
:::
:::

::: {.source-item #d90-mit-l11-p097-i003 data-source-page="97" data-source-order="3"}
Namun,

::: {.source-display #d90-mit-l11-p097-d004 data-source-page="97" data-display-order="4"}
$$
\check{\operatorname{cl}}f=f,
\qquad\text{sehingga}\qquad
\check{\operatorname{cl}}f\neq f^{**}.
$$
:::
:::

*[Halaman sumber 97.]{.source-locator}*
:::
