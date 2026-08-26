# Optimisasi Lanjut dan Analisis Konveks — Tranche Asli 1

**Metode Stokastik Komposit, Cermin, dan Minibatch — Edisi Bahasa Indonesia**

Status paket ini: **lengkap pada batas tranche Original-01; edisi kursus O015/D90 yang lebih besar masih parsial**. PDF adalah pembaca utama; HTML semantik responsif dan EPUB reflow adalah permukaan pembaca tambahan. Laboratorium disertakan dalam JSON, CSV, dan SVG sehingga angka dapat dibaca tanpa bergantung pada grafik.

Tranche ini adalah materi penghubung yang ditulis mandiri. Ia menutup hubungan antara operator proksimal, oracle stokastik, sampling minibatch dengan dan tanpa penggantian, geometri Bregman/cermin, dan integrasi Prox-SAGA yang dibatasi secara eksplisit. Paket mempertahankan enam latihan, petunjuk bertahap, solusi lengkap, identitas segmen, label formula, dan stable-ID backend yang menjadi sumber resumable di repositori.

## Provenans dan hak

Uraian, definisi, bukti penghubung, algoritme, latihan, petunjuk, solusi, laboratorium, dan dokumentasi baru tranche ini ditulis untuk edisi ini dan dilisensikan **CC BY-SA 4.0**. Infrastruktur `shinybook.cls` adalah salinan persis dari paket sumber Andreas Habring, *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1; `macros-id.tex` adalah adaptasi lokal dari `macros.tex`. Bukti tingkat kiriman arXiv untuk kedua komponen tersebut adalah CC BY 4.0; komponen itu tidak diubah menjadi CC BY-SA. Pemberitahuan hak rinci dan batas lisensi ada di `RIGHTS_AND_PROVENANCE_ORIGINAL_01.md`, `LICENSE_ORIGINAL_CC_BY-SA-4.0.md`, dan `LICENSE_HABRING_SCAFFOLD_CC_BY-4.0.md`.

Kredit sumber matematis dan templat (termasuk Andreas Habring, Christian Clason, Clément W. Royer, Stephen Becker, Mitchell Krock, Aaron Defazio, Francis Bach, dan Simon Lacoste-Julien) dipertahankan sebagai atribusi dan saksi verifikasi. Tidak ada pihak atau institusi yang disebut menyusun, memeriksa, menyetujui, mensponsori, atau mendukung edisi ini. Rujukan verifikasi tidak memberi hak untuk menyalin prosa, tata letak, gambar, latihan, solusi, atau kode pihak ketiga.

## QA dan kelanjutan

Paket memuat receipt deterministik untuk matematika, PDF, visual PDF, HTML, browser desktop/tablet/ponsel, EPUB/EPUBCheck, backend stable-ID, hak/non-overlap, dan rereview independen. `release-manifest-original-01.json` adalah indeks byte/SHA-256 untuk setiap anggota paket; `SHA256SUMS` memverifikasi semua anggota selain dirinya sendiri. Backend lengkap tetap dipelihara di repositori karena terlalu besar untuk payload ringkas ini; receipt backend memuat baseline terlindungi, ID set/order, dan hash lengkap.

Batas berikutnya yang belum ditutup adalah variational inequalities, operator monoton maksimal, resolvent, dan splitting, lalu asesmen kumulatif/lab/capstone edisi penuh. Paket ini tidak mengklaim bahwa pekerjaan tersebut selesai.

Provenans produksi: **OpenAI Codex gpt-5.6-sol, Ultra**, atas instruksi pengguna repositori. Kredit penulis dan kontributor manusia tidak digantikan oleh penanda model ini.

