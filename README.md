# Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia

Edisi pembaca bahasa Indonesia yang sedang dikembangkan untuk materi optimisasi lanjut, analisis konveks, dan metode nonsmooth. Repositori ini memuat sumber TeX dan Markdown semantik yang dapat disunting, HTML yang dapat mengalir ulang, PDF yang telah diverifikasi, pemeriksaan matematika dan komputasi yang dapat diulang, serta backend modular dengan pengenal stabil.

**Status:** karya dalam proses. Unit Habring Bab 3–9 dan Penn Bab 3–5 telah diterjemahkan serta lolos audit struktural, matematika, komputasi, pembangunan deterministik, dan pemeriksaan visual sebagai pendamping opsional sepuluh unit. Korpus utama D90 yang dipilih adalah MIT OpenCourseWare 6.253 ditambah materi gradien stokastik Clément Royer. Pilot sumber semantik MIT pertama, yang mencakup tepat halaman sumber 2–5, telah lolos dan diterima. Batas produksi berikutnya sudah dibekukan sebagai halaman 6–13, dari “Duality” sampai “Exceptional Behavior”; halaman 14 memulai topik berikutnya. Status ini bukan klaim bahwa keseluruhan korpus telah selesai.

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

Akses GitHub telah dipulihkan oleh penyedia pada 22 Agustus 2026. Checkpoint ini
telah disinkronkan ke [repositori yang sama](https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id)
pada [commit konten `6900a39`](https://github.com/KokunoYumeto/advanced-optimization-convex-analysis-id/commit/6900a39ce579ba5ca464fecc00b4575139fbc3ea);
identitas commit/tree dan berkas pembaca, sumber, backend, serta resi publik
telah dibaca kembali secara anonim dan cocok byte demi byte. Tidak dibuat
repositori pengganti.

## Pembaca yang tersedia

- `output/html/D90-MIT-01-peran-kekonveksan-id.html` — permukaan semantik utama pilot MIT halaman sumber 2–5; 20.613 byte; SHA-256 `fff4de952dd2cb208208e1cfb3bbc8fe8a64936ff5fdb532a23a92fb0dc6af8b`.
- `output/pdf/D90-MIT-01-peran-kekonveksan-id.pdf` — pembaca A4 pilot MIT halaman sumber 2–5, 3 halaman; SHA-256 `bd03912f9d3fe6dbe7376577c7ca6e7ab5aee007dd33b51669cde1792644df58`.
- `output/pdf/D90-HAB-03-09-modul-pendamping-id.pdf` — modul Habring Bab 3–9 gabungan, 103 halaman; SHA-256 `6cd291cc447999b7cd72622e8c2003b837cf4f21ea5de0fcb7094913e20acd87`.
- `output/pdf/D90-HAB-03-subgradien-id.pdf` — 15 halaman; SHA-256 `45f7bc24ff46079881e42be9aa6f1b508c324a208f2b4dd82e35e7e3a6d544b4`.
- `output/pdf/D90-HAB-04-metode-subgradien-terproyeksi-id.pdf` — 13 halaman; SHA-256 `5c9991af837995b2e24f4a9060eb3b0efe7b2d71a9bbde01948eeb81ebfd63b7`.
- `output/pdf/D90-HAB-05-metode-gradien-proksimal-id.pdf` — 15 halaman; SHA-256 `6f8aa99f6d0395f3c732ed64d2b5cadd5d95ff2195e2504e959d31a3c010731d`.
- `output/pdf/D90-HAB-06-akselerasi-id.pdf` — 15 halaman; SHA-256 `cb9edf46d8d2582591ad3114f9a2b316073825dfd48079d12560793ad4bca0a0`.
- `output/pdf/D90-HAB-07-dualitas-id.pdf` — 21 halaman; SHA-256 `c4354e1e1366bdb20cebb9c6eca26fba172d6d82a6ad22dd9e2e470da2baeb6e`.
- `output/pdf/D90-HAB-08-penurunan-gradien-stokastik-id.pdf` — 8 halaman; SHA-256 `c1ed028667c5df3fd0a837807e2a17bf7a9e1fa3170938853c9a96b9670fa86a`.
- `output/pdf/D90-HAB-09-transportasi-optimal-id.pdf` — 15 halaman; SHA-256 `edc8e17fd43d17a0dd7811879dfbedaab9ac226c291ed5558ca0bfbb3ce10214`.
- `output/pdf/D90-PENN-03-pendakian-gradien-dan-pencarian-garis-id.pdf` — 20 halaman; SHA-256 `e1be82d06572c51b403608cd9595cc5adf2dc64cfa93f53001eba94e48f77e3e`.
- `output/pdf/D90-PENN-04-pencarian-garis-hampiran-dan-konvergensi-id.pdf` — 17 halaman; current working-tree SHA-256 `18e7162f8d1e55a050ee96a6ba05a2ffaa0d5cb578f96e264152666a79dc83a8` (the previously published Zenodo bytes remain `c0f283aa7d70eba05de6a35c98bc0aa55f3177ab40702bf7eed5de45a7b6ab8a`).
- `output/pdf/D90-PENN-05-metode-newton-dan-koreksi-id.pdf` — 15 halaman; current working-tree SHA-256 `dad34c7cb363197da1ae87117b22b2dde21d6d183997745cd3ffff62245c0b96` (the previously published Zenodo bytes remain `427db2c5a4428dfbe222d7e1d4f5c5349d4f78484a8593c412328fe94a7353c6`).

Sumber Indonesia berada di `source/id-ID`; rekaman audit dan pemeriksaan ada di `qa`; backend mesin-baca 1.430-rekaman berada di `backend`; keputusan, otoritas sumber, hak komponen, dan kursor ada di `00_control`.

## Provenans produksi

Terjemahan, rekonstruksi sumber semantik, pembuatan backend, serta QA matematika dan komputasi dalam edisi ini dibantu oleh **OpenAI Codex gpt-5.6-sol, Ultra** atas arahan pengguna repositori. Sistem tersebut bukan penulis sumber, pemberi lisensi, atau wakil institusi mana pun. Semua kredit penulis dan kontributor manusia tetap dipertahankan; rincian peran, hak per komponen, nondukungan, dan batas tinjauan manusia dicatat dalam `PROVENANCE.md` dan `RIGHTS.md`.

## Otoritas dan perubahan

Korpus utama MIT merupakan rekonstruksi semantik dan terjemahan independen dari Dimitri P. Bertsekas, *Convex Analysis and Optimization*, MIT OpenCourseWare 6.253, di bawah [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Gambar yang dinyatakan digunakan atas izin Athena Scientific tidak disalin; gambar yang diperlukan harus digambar ulang secara independen dengan rekaman hak terpisah atau dihilangkan dengan lokator sumber. Komponen stokastik Clément Royer berada di bawah [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/). Unit Habring merupakan terjemahan independen dari Andreas Habring, *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1, di bawah [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Unit Penn merupakan terjemahan independen dari Christopher Griffin, *Nonlinear Programming* / Penn State MATH 555, di bawah [CC BY-NC-SA 3.0 US](https://creativecommons.org/licenses/by-nc-sa/3.0/us/). Setiap komponen mempertahankan lisensi, atribusi, penandaan perubahan, dan nondukungan sendiri; tidak ada lisensi menyeluruh untuk seluruh repositori. Daftar koreksi yang transparan ada di `00_control/ADVERSE_LEDGER.jsonl`.

Empat belas masukan listing Maple yang ditemui pada Penn Bab 3–5 tidak disalin atau diterjemahkan sebagai kode. Permukaan itu diganti dengan pseudokode mandiri yang tidak bergantung pada Maple atau bahasa pemrograman tertentu dan diungkapkan sebagai perubahan. Lihat `RIGHTS.md`, `00_control/COMPONENT_RIGHTS.csv`, dan audit sumber Penn Bab 3–5 di `00_control`.

## Membangun ulang

Prasyarat yang telah diverifikasi: Pandoc, LuaLaTeX, MiKTeX/pdfTeX, `latexmk`, dan Biber. Bangun dua permukaan pilot MIT dari akar repositori:

```powershell
python qa/build_mit_pilot.py --output-root output/mit-pilot-rebuild
python qa/validate_mit_pilot.py
```

Dari `source/id-ID`, bangun unit Penn Bab 3–5 dengan pola berikut:

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
python qa/extend_backend_mit_l01.py
python qa/validate_backend_mit_l01.py
```

Generator Penn/Habring terdahulu tetap disimpan sebagai bukti transaksi historis, tetapi tidak dijalankan setelah ekstensi MIT; pintu masuk backend hidup adalah pasangan `extend_backend_mit_l01.py` / `validate_backend_mit_l01.py`.

Rekaman pembangunan lengkap ada di `00_control/BUILD_AND_QA.md`.

## Aksesibilitas dan batas saat ini

Semua PDF bersifat dapat dicari dan mendeklarasikan bahasa `id-ID`, tetapi belum bertanda semantik. Sebagian font internal pada gambar vektor Penn Bab 3–4 tidak memiliki peta Unicode lengkap; Penn Bab 5 dan pilot MIT memetakan seluruh fontnya. Pilot MIT mempunyai HTML semantik yang dapat mengalir ulang, dengan struktur heading, MathML, navigasi, tautan lompat, dan pengenal halaman/butir yang telah diuji pada lebar desktop dan ponsel tanpa luapan horizontal. HTML/EPUB semantik untuk korpus lengkap, permukaan komputasi interaktif, lapisan latihan/hint/solusi lengkap, dan peninjauan bahasa independen masih harus diselesaikan. Penn Bab 6 yang sudah diterjemahkan disimpan sebagai kandidat pendamping yang belum diterima; produksi utama tidak berlanjut otomatis ke bab tersebut.
