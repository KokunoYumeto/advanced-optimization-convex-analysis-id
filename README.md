# Optimisasi Lanjut dan Analisis Konveks — Edisi Bahasa Indonesia

Edisi pembaca bahasa Indonesia yang sedang dikembangkan untuk materi optimisasi lanjut, analisis konveks, dan metode nonsmooth. Repositori ini memuat sumber TeX yang dapat disunting, PDF yang telah diverifikasi, pemeriksaan matematika dan komputasi yang dapat diulang, serta backend modular dengan pengenal stabil.

**Status:** karya dalam proses. Unit Habring Bab 3 (*Subgradien*), Bab 4 (*Metode subgradien terproyeksi*), dan Bab 5 (*Metode gradien proksimal*) telah diterjemahkan serta lolos audit struktural, matematika, komputasi, pembangunan deterministik, dan pemeriksaan visual. Bab 6 adalah kursor produksi berikutnya. Status ini bukan klaim bahwa keseluruhan korpus telah selesai.

English discovery label: **Advanced Optimization and Convex Analysis — Indonesian (id-ID) Edition**.

## Pembaca yang tersedia

- `output/pdf/D90-HAB-03-subgradien-id.pdf` — 15 halaman; SHA-256 `45f7bc24ff46079881e42be9aa6f1b508c324a208f2b4dd82e35e7e3a6d544b4`.
- `output/pdf/D90-HAB-04-metode-subgradien-terproyeksi-id.pdf` — 13 halaman; SHA-256 `5c9991af837995b2e24f4a9060eb3b0efe7b2d71a9bbde01948eeb81ebfd63b7`.
- `output/pdf/D90-HAB-05-metode-gradien-proksimal-id.pdf` — 15 halaman; SHA-256 `6f8aa99f6d0395f3c732ed64d2b5cadd5d95ff2195e2504e959d31a3c010731d`.

Sumber Indonesia berada di `source/id-ID`; rekaman audit dan pemeriksaan ada di `qa`; backend mesin-baca berada di `backend`; keputusan, otoritas sumber, hak komponen, dan kursor ada di `00_control`.

## Otoritas dan perubahan

Unit yang tersedia saat ini merupakan terjemahan independen dari Andreas Habring, *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1. Sumber Habring dan terjemahan unit ini berada di bawah [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Terjemahan, penataan pembaca, dan koreksi yang ditentukan secara matematis adalah perubahan terhadap sumber. Daftar koreksi yang transparan ada di `00_control/ADVERSE_LEDGER.jsonl`. Andreas Habring tidak mengesahkan edisi ini.

Korpus lengkap nantinya juga akan memakai bagian terpilih dan tidak tumpang tindih dari Christopher Griffin, *Nonlinear Programming* / Penn State MATH 555, yang berlisensi CC BY-NC-SA 3.0 US. Bagian itu belum menjadi pembaca terbitan pada titik ini dan akan tetap dipisahkan haknya. Tidak ada satu lisensi menyeluruh untuk semua isi repositori; lihat `RIGHTS.md` dan `00_control/COMPONENT_RIGHTS.csv`.

## Membangun ulang

Prasyarat yang telah diverifikasi: MiKTeX/pdfTeX, `latexmk`, dan Biber. Dari `source/id-ID`, bangun unit Bab 5 dengan:

```powershell
$env:SOURCE_DATE_EPOCH='1786665600'
$env:TZ='UTC'
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir='..\..\build\habring-unit-05-id' 'D90-HAB-05-metode-gradien-proksimal-id.tex'
```

Jalankan audit dan pemeriksaan numerik dari akar repositori:

```powershell
python qa/audit_proximal_gradient_unit.py
python qa/validate_proximal_gradient_unit.py
python qa/validate_backend.py
```

Rekaman pembangunan lengkap ada di `00_control/BUILD_AND_QA.md`.

## Aksesibilitas dan batas saat ini

PDF bersifat dapat dicari dan mendeklarasikan bahasa `id-ID`; ilustrasi pada Bab 3 memiliki deskripsi bahasa Indonesia. PDF belum bertanda semantik. Pembaca HTML/EPUB yang semantik, lapisan latihan/solusi tambahan, peninjauan bahasa independen, bagian Habring yang tersisa, dan modul Penn masih harus diselesaikan.
