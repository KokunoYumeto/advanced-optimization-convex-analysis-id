# Modul Becker 1 — Dualitas Lagrange, Slater, dan KKT (Bahasa Indonesia)

## Mulai membaca

1. **`D90-BECKER-01-dualitas-lagrange-slater-kkt-id.pdf`** — pembaca utama, berformat A4, dapat dicari, dan berbahasa `id-ID`.
2. **`D90-BECKER-01-dualitas-lagrange-slater-kkt-id.html`** — pembaca semantik responsif yang direkomendasikan untuk layar kecil dan teknologi bantu.

Modul koheren ini membahas fungsi dual, dualitas lemah, kondisi Slater, geometri perturbasi, interpretasi titik pelana, kondisi Karush–Kuhn–Tucker, proyeksi pada bola norma satu, dan sistem KKT untuk program kuadratik dengan kendala kesamaan. Modul Becker 1 sudah lengkap pada batas sumber yang dinyatakan, tetapi edisi kursus *Optimisasi Lanjut dan Analisis Konveks* yang lebih besar masih **parsial**.

## Sumber dan kredit

Materi donor berasal dari repositori Stephen Becker, [`convex-optimization-class`](https://github.com/stephenbeckr/convex-optimization-class), commit `98ed6930084c435ba0f675f7646ced1f2fd8729e`. Catatan ketik `APPM5720Notes.tex` mengreditkan Mitchell Krock. Pembekuan otoritas dicatat dalam `authority/BECKER_AUTHORITY_FREEZE.md`; batas baris yang diterima, identitas berkas, dan pengecualian materi program-linear dicatat dalam `qa/BECKER_01_SOURCE_BOUNDARY.json`. Saksi bahasa Inggris yang diekstrak tersedia di `source/en/`.

Stephen Becker, Mitchell Krock, University of Colorado Boulder, dan pihak sumber lain tidak mendukung atau mengesahkan edisi independen ini.

## Hak dan lisensi

- Materi donor dan saksi sumber mempertahankan Lisensi MIT. Pemberitahuan akar repositori yang lengkap dan identik-byte terdapat dalam `LICENSE_BECKER_MIT.txt`.
- Terjemahan bahasa Indonesia, koreksi editorial, teks penghubung mandiri, dan dokumentasi rilis baru dilisensikan berdasarkan Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0), sebagaimana dirinci dalam `LICENSE_TRANSLATION_CC_BY-SA-4.0.md`.
- Lisensi berlaku per komponen. CC BY-SA 4.0 tidak menggantikan pemberitahuan MIT, dan paket ini tidak menyatakan lisensi payung untuk komponen kursus lain.

## Isi sumber dan bukti

`source/id-ID/` memuat tubuh terjemahan, wrapper pembaca, makro, dan kelas LaTeX minimum yang diperlukan; `source/en/` memuat saksi potongan sumber yang diterima. `qa/` memuat bukti batas sumber, rereview semantik independen, validasi matematika terbuka, build PDF/HTML deterministik, inspeksi visual PDF, QA browser responsif, dan perluasan backend ber-ID stabil. Dataset backend lengkap tidak diduplikasi di sini; repositori edisi mempertahankannya.

PDF dapat dicari dan mendeklarasikan bahasa `id-ID`, tetapi belum bertag. Gunakan HTML responsif untuk pembacaan yang dapat mengalir ulang. `release-manifest-becker-01.json` dan `SHA256SUMS` mengikat identitas setiap berkas dalam ZIP.

Bantuan produksi, terjemahan, koreksi, build, dan QA: OpenAI Codex gpt-5.6-sol, Ultra, atas instruksi pengguna repositori.
