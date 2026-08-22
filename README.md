# Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia

Edisi pembaca bahasa Indonesia yang sedang dikembangkan untuk materi optimisasi lanjut, analisis konveks, dan metode nonsmooth. Repositori ini memuat sumber TeX yang dapat disunting, PDF yang telah diverifikasi, pemeriksaan matematika dan komputasi yang dapat diulang, serta backend modular dengan pengenal stabil.

**Status:** karya dalam proses. Unit Habring Bab 3–9 dan Penn Bab 3–5 telah diterjemahkan serta lolos audit struktural, matematika, komputasi, pembangunan deterministik, dan pemeriksaan visual sebagai pendamping opsional sepuluh unit. Korpus utama D90 yang dipilih adalah MIT OpenCourseWare 6.253 ditambah materi gradien stokastik Clément Royer; pilot sumber semantiknya belum dimulai. Status ini bukan klaim bahwa keseluruhan korpus telah selesai.

English discovery label: **Advanced Optimization and Convex Analysis — Indonesian (id-ID) Edition**.

## Preservasi dan mirror

Checkpoint publik sepuluh unit yang belum lengkap dipreservasi dalam garis keturunan
Zenodo yang sama: [DOI versi 10.5281/zenodo.22060447](https://doi.org/10.5281/zenodo.22060447)
dan [DOI konsep 10.5281/zenodo.22059741](https://doi.org/10.5281/zenodo.22059741).
Rekaman tersebut menyertakan sepuluh PDF pembaca secara terpisah serta bundel
sumber, backend, hak per komponen, manifest, dan checksum. Unduhan anonim cocok
byte demi byte untuk seluruh 16 berkas dan seluruh 150 muatan yang terikat manifest.

Modul Habring Bab 3–9 yang murni CC BY 4.0 juga tersedia sebagai permukaan pembaca
utama di [Figshare versi 2](https://doi.org/10.6084/m9.figshare.33314733.v2),
dengan PDF gabungan 103 halaman sebagai berkas pertama, paket sumber yang dapat
dibangun ulang, lisensi, manifest, dan checksum. Komponen Penn berlisensi campuran
tidak ditempatkan pada item Figshare tersebut dan tetap berada di Zenodo.

Akses GitHub telah dipulihkan oleh penyedia pada 22 Agustus 2026. Sinkronisasi
checkpoint terverifikasi kembali menggunakan repositori yang sama; tidak dibuat
repositori pengganti.

## Pembaca yang tersedia

- `output/pdf/D90-HAB-03-09-modul-pendamping-id.pdf` — modul Habring Bab 3–9 gabungan, 103 halaman; SHA-256 `6cd291cc447999b7cd72622e8c2003b837cf4f21ea5de0fcb7094913e20acd87`.
- `output/pdf/D90-HAB-03-subgradien-id.pdf` — 15 halaman; SHA-256 `45f7bc24ff46079881e42be9aa6f1b508c324a208f2b4dd82e35e7e3a6d544b4`.
- `output/pdf/D90-HAB-04-metode-subgradien-terproyeksi-id.pdf` — 13 halaman; SHA-256 `5c9991af837995b2e24f4a9060eb3b0efe7b2d71a9bbde01948eeb81ebfd63b7`.
- `output/pdf/D90-HAB-05-metode-gradien-proksimal-id.pdf` — 15 halaman; SHA-256 `6f8aa99f6d0395f3c732ed64d2b5cadd5d95ff2195e2504e959d31a3c010731d`.
- `output/pdf/D90-HAB-06-akselerasi-id.pdf` — 15 halaman; SHA-256 `cb9edf46d8d2582591ad3114f9a2b316073825dfd48079d12560793ad4bca0a0`.
- `output/pdf/D90-HAB-07-dualitas-id.pdf` — 21 halaman; SHA-256 `c4354e1e1366bdb20cebb9c6eca26fba172d6d82a6ad22dd9e2e470da2baeb6e`.
- `output/pdf/D90-HAB-08-penurunan-gradien-stokastik-id.pdf` — 8 halaman; SHA-256 `c1ed028667c5df3fd0a837807e2a17bf7a9e1fa3170938853c9a96b9670fa86a`.
- `output/pdf/D90-HAB-09-transportasi-optimal-id.pdf` — 15 halaman; SHA-256 `edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214`.
- `output/pdf/D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.pdf` — 20 halaman; SHA-256 `e1be82d06572c51b403608cd9595cc5adf2dc64cfa93f53001eba94e48f77e3e`.
- `output/pdf/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf` — 17 halaman; SHA-256 `c0f283aa7d70eba05de6a35c98bc0aa55f3177ab40702bf7eed5de45a7b6ab8a`.
- `output/pdf/D90-PENN-05-metode-newton-dan-koreksi-id.pdf` — 15 halaman; SHA-256 `427db2c5a4428dfbe222d7e1d4f5c5349d4f78484a8593c412328fe94a7353c6`.

Sumber Indonesia berada di `source/id-ID`; rekaman audit dan pemeriksaan ada di `qa`; backend mesin-baca berada di `backend`; keputusan, otoritas sumber, hak komponen, dan kursor ada di `00_control`.

## Otoritas dan perubahan

Unit Habring merupakan terjemahan independen dari Andreas Habring, *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1, di bawah [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Unit Penn merupakan terjemahan independen dari Christopher Griffin, *Nonlinear Programming* / Penn State MATH 555, di bawah [CC BY-NC-SA 3.0 US](https://creativecommons.org/licenses/by-nc-sa/3.0/us/). Setiap komponen mempertahankan lisensi, atribusi, penandaan perubahan, dan nondukungan sendiri; tidak ada lisensi menyeluruh untuk seluruh repositori. Daftar koreksi yang transparan ada di `00_control/ADVERSE_LEDGER.jsonl`.

Empat belas masukan listing Maple yang ditemui pada Penn Bab 3–5 tidak disalin atau diterjemahkan sebagai kode. Permukaan itu diganti dengan pseudokode mandiri yang tidak bergantung pada Maple atau bahasa pemrograman tertentu dan diungkapkan sebagai perubahan. Lihat `RIGHTS.md`, `00_control/COMPONENT_RIGHTS.csv`, dan audit sumber Penn Bab 3–5 di `00_control`.

## Membangun ulang

Prasyarat yang telah diverifikasi: MiKTeX/pdfTeX, `latexmk`, dan Biber. Dari `source/id-ID`, bangun unit Penn Bab 3–5 dengan pola berikut:

```powershell
$env:SOURCE_DATE_EPOCH='1783900800'
$env:FORCE_SOURCE_DATE='1'
$env:TZ='UTC'
latexmk -gg -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir='..\..\build\penn-unit-03-id' 'D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.tex'
latexmk -gg -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir='..\..\build\penn-unit-04-id' 'D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.tex'
latexmk -gg -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir='..\..\build\penn-unit-05-id' 'D90-PENN-05-metode-newton-dan-koreksi-id.tex'
```

Jalankan audit dan pemeriksaan numerik dari akar repositori:

```powershell
python qa/audit_penn_ch03_unit.py
python qa/validate_penn_ch03_unit.py
python qa/audit_penn_ch04_candidate.py
python qa/validate_penn_ch04_math.py
python qa/audit_penn_ch05_candidate.py
python qa/validate_penn_ch05_math.py
python qa/extend_backend_penn_ch05.py
python qa/validate_backend_penn_ch05.py
```

Rekaman pembangunan lengkap ada di `00_control/BUILD_AND_QA.md`.

## Aksesibilitas dan batas saat ini

Semua PDF bersifat dapat dicari dan mendeklarasikan bahasa `id-ID`, tetapi belum bertanda semantik. Sebagian font internal pada gambar vektor Penn Bab 3–4 tidak memiliki peta Unicode lengkap; Penn Bab 5 memetakan seluruh fontnya. Pembaca HTML/EPUB yang semantik, pilot MIT/Royer, permukaan komputasi interaktif, lapisan latihan/hint/solusi lengkap, dan peninjauan bahasa independen masih harus diselesaikan. Penn Bab 6 yang sudah diterjemahkan disimpan sebagai kandidat pendamping yang belum diterima; produksi utama tidak berlanjut otomatis ke bab tersebut.
