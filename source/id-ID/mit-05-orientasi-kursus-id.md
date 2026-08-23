---
title: "Tren Metodologis dan Orientasi Kursus"
subtitle: "MIT 6.253 - Edisi Indonesia, halaman sumber 16-19"
author:
  - "Dimitri P. Bertsekas (penulis sumber)"
lang: id-ID
date: "2026-08-23"
rights: "Terjemahan MIT OCW 6.253, CC BY-NC-SA 4.0"
description: "Rekonstruksi semantik yang dapat mengalir ulang dari blok orientasi kursus empat halaman, dengan pengenal stabil, referensi, dan tautan yang dapat diakses."
keywords:
  - tren metodologis
  - garis besar kursus
  - analisis kompleksitas
  - optimisasi konveks
  - id-ID
---

::: {.edition-notice #d90-mit-l05-edition-notice}
## Tentang batas ini

Ini adalah rekonstruksi sumber semantik dan terjemahan bahasa Indonesia dari
Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare
6.253, Spring 2012, halaman PDF sumber 16-19. Keempat halaman ini membentuk blok
orientasi kursus penutup yang utuh: tren metodologis, garis besar kursus,
harapan dan persyaratan kursus, serta catatan tentang fungsi slide. Halaman 20
memulai **Kuliah 2** dan tidak termasuk. Materi sumber berada di bawah [CC
BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

Keempat halaman sumber hanya berupa teks dan daftar; tidak ada grafik atau aset
gambar yang disalin. Dua URI hidup pada halaman sumber 17 dipertahankan sebagai
tautan semantik. Bantuan produksi dan QA: **OpenAI Codex gpt-5.6-sol, Ultra**,
atas arahan pengguna repositori. Sistem tersebut bukan penulis sumber atau
pemberi lisensi. Tidak ada dukungan oleh MIT atau penulis sumber yang tersirat.
Tinjauan bahasa manusia/penutur asli belum tercatat.

Istilah teknis dipertahankan secara konsisten: *interior point* menjadi “titik
interior”, *subgradient* menjadi “subgradien”, *proximal* menjadi “proksimal”,
dan *polyhedral* menjadi “polihedral”. Istilah *incremental* diterjemahkan
sebagai “inkremental”; pengulangan istilah pada sumber sengaja dipertahankan.
Halaman 17 mencetak nama “Vanderbergue”, sedangkan halaman 18 mencetak
“Vandenberghe”. Edisi pembelajar memakai ejaan penulis yang benar,
“Vandenberghe”, dan mencatat koreksi nama sumber ini sebagai
`O015-MIT-SEM-0004`.

Pengenal stabil tetap melekat pada keempat halaman dan keenam belas butirnya,
meskipun HTML atau PDF mengalir ulang ke ukuran layar atau halaman yang berbeda.
:::

::: {.source-page #d90-mit-l05-p016 data-source-page="16" data-source-order="1"}
## Tren Metodologis

::: {.source-item #d90-mit-l05-p016-i001 data-source-page="16" data-source-order="1"}
- **Metode baru, minat yang diperbarui pada metode lama.**

  - Metode titik interior
  - Metode subgradien/inkremental
  - Aproksimasi polihedral/metode bidang potong
  - Metode regularisasi/proksimal
  - Metode inkremental
:::

::: {.source-item #d90-mit-l05-p016-i002 data-source-page="16" data-source-order="2"}
- **Penekanan kembali pada analisis kompleksitas**

  - Nesterov, Nemirovski, dan lain-lain ...
  - “Algoritme optimal” (misalnya, metode gradien terekstrapolasi)
:::

::: {.source-item #d90-mit-l05-p016-i003 data-source-page="16" data-source-order="3"}
- **Penekanan pada struktur khusus berskala besar yang menarik (sering kali berkaitan dengan dualitas)**
:::

*[Halaman sumber 16.]{.source-locator}*
:::

::: {.source-page #d90-mit-l05-p017 data-source-page="17" data-source-order="2"}
## Garis Besar Kursus

::: {.source-item #d90-mit-l05-p017-i001 data-source-page="17" data-source-order="1"}
- **Kita akan mengikuti dengan saksama buku teks**

  - Bertsekas, *Convex Optimization Theory*, Athena Scientific, 2009, termasuk
    Bab 6 daring dan materi pelengkap di
    <http://www.athenasc.com/convexduality.html>
:::

::: {.source-item #d90-mit-l05-p017-i002 data-source-page="17" data-source-order="2"}
- **Referensi buku tambahan:**

  - Rockafellar, *Convex Analysis*, 1970.
  - Boyd dan Vandenberghe, *Convex Optimization*, Cambridge U. Press, 2004.
    (Daring di <http://www.stanford.edu/~boyd/cvxbook/>.)
  - Bertsekas, Nedic, dan Ozdaglar, *Convex Analysis and Optimization*, Ath.
    Scientific, 2003.
:::

::: {.source-item #d90-mit-l05-p017-i003 data-source-page="17" data-source-order="3"}
- **Topik** (rancangan teks bersifat modular, dan urutan berikut tidak
  menghilangkan kesinambungan):

  - **Konsep Dasar Kekonveksan:** Bag. 1.1-1.4.
  - **Kekonveksan dan Optimisasi:** Bab 3.
  - **Hiperbidang dan Konjugasi:** Bag. 1.5, 1.6.
  - **Kekonveksan Polihedral:** Bab 2.
  - **Kerangka Dualitas Geometris:** Bab 4.
  - **Teori Dualitas:** Bag. 5.1-5.3.
  - **Subgradien:** Bag. 5.4.
  - **Algoritme:** Bab 6.
:::

*[Halaman sumber 17.]{.source-locator}*
:::

::: {.source-page #d90-mit-l05-p018 data-source-page="18" data-source-order="3"}
## Apa yang Dapat Diharapkan dari Kursus Ini

::: {.source-item #d90-mit-l05-p018-i001 data-source-page="18" data-source-order="1"}
- **Persyaratan:** tugas rumah (25%), ujian tengah semester (25%), dan makalah
  akhir (50%)
:::

::: {.source-item #d90-mit-l05-p018-i002 data-source-page="18" data-source-order="2"}
- **Tujuan kita:**

  - Mengembangkan wawasan dan pemahaman mendalam tentang suatu topik
    optimisasi yang fundamental
  - Membahas dengan ketelitian matematis suatu cabang penting penelitian
    metodologis dan memberikan gambaran tentang keadaan mutakhir bidang ini
  - Memahami keunggulan, keterbatasan, dan karakteristik dari beragam algoritme
    yang tersedia
:::

::: {.source-item #d90-mit-l05-p018-i003 data-source-page="18" data-source-order="3"}
- **Tingkat matematis:**

  - Prasyaratnya adalah aljabar linear (sebaiknya abstrak) dan analisis real
    (masing-masing satu mata kuliah)
  - Bukti akan penting ... tetapi geometri subjek yang kaya membantu memandu
    matematikanya
:::

::: {.source-item #d90-mit-l05-p018-i004 data-source-page="18" data-source-order="4"}
- **Aplikasi:**

  - Aplikasinya banyak dan tersebar luas ... tetapi jangan mengharapkan banyak
    aplikasi dalam kursus ini. Buku Boyd dan Vandenberghe menjelaskan banyak
    model praktis optimisasi konveks
  - Makalah akhir dapat dikerjakan mengenai suatu bidang aplikasi
:::

*[Halaman sumber 18.]{.source-locator}*
:::

::: {.source-page #d90-mit-l05-p019 data-source-page="19" data-source-order="4"}
## Catatan tentang Slide Ini

::: {.source-item #d90-mit-l05-p019-i001 data-source-page="19" data-source-order="1"}
- Slide ini merupakan alat bantu pengajaran, bukan buku teks
:::

::: {.source-item #d90-mit-l05-p019-i002 data-source-page="19" data-source-order="2"}
- Jangan mengharapkan pengembangan matematis yang ketat
:::

::: {.source-item #d90-mit-l05-p019-i003 data-source-page="19" data-source-order="3"}
- Pernyataan teorema cukup presisi, tetapi buktinya tidak
:::

::: {.source-item #d90-mit-l05-p019-i004 data-source-page="19" data-source-order="4"}
- Banyak bukti telah dihilangkan atau sangat dipersingkat
:::

::: {.source-item #d90-mit-l05-p019-i005 data-source-page="19" data-source-order="5"}
- Gambar dimaksudkan untuk menyampaikan dan meningkatkan pemahaman gagasan,
  bukan untuk mengungkapkannya secara presisi
:::

::: {.source-item #d90-mit-l05-p019-i006 data-source-page="19" data-source-order="6"}
- Bukti yang dihilangkan dan pembahasan yang lebih lengkap dapat ditemukan
  dalam buku teks *Convex Optimization Theory* dan materi pelengkapnya
:::

*[Halaman sumber 19.]{.source-locator}*
:::

::: {.edition-backmatter #d90-mit-l05-backmatter}
## Identitas Sumber dan Batas Edisi

- Sumber: Dimitri P. Bertsekas, *Lecture Slides on Convex Analysis and
  Optimization*, berdasarkan MIT 6.253, Spring 2012.
- Batas tepat: halaman PDF lengkap 16-19. Halaman 20 memulai **Kuliah 2** dan
  merupakan penerus bersih dalam urutan sumber.
- Topologi: empat halaman sumber, empat judul, enam belas butir tingkat atas,
  dan dua puluh enam butir bertingkat. Halaman 17 membawa dua anotasi URI hidup;
  keduanya dipertahankan sebagai tautan semantik.
- Permukaan: keempat halaman ini tidak memuat rumus matematika, grafik sumber,
  tabel, contoh yang dikerjakan, latihan pembelajar, petunjuk, solusi, kode, atau
  komputasi interaktif. Halaman 19 membahas peran gambar dalam rangkaian slide,
  tetapi tidak memuat gambar. Tidak ada byte gambar, potongan, atau tata letak
  sumber yang disalin.
- Koreksi nama sumber `O015-MIT-SEM-0004`: halaman 17 mencetak
  “Vanderbergue”, sedangkan halaman 18 mencetak “Vandenberghe”. Edisi
  pembelajar menggunakan ejaan penulis yang benar, “Vandenberghe”, dan
  mengungkapkan perubahan tersebut alih-alih memperbaikinya secara diam-diam.
- Hak: komponen turunan ini tetap CC BY-NC-SA 4.0, dengan kewajiban atribusi,
  penandaan perubahan, penggunaan nonkomersial, ShareAlike, dan nondukungan.
:::

*[Halaman sumber 16-19.]{.source-locator}*
