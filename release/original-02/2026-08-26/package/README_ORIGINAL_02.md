# Optimisasi Lanjut dan Analisis Konveks — Tranche Asli 2

**Ketaksamaan Variasional, Operator Monoton, Resolven, dan Pemisahan — Edisi Bahasa Indonesia**

Status paket ini: **lengkap pada batas tranche Original-02; edisi kursus O015/D90 yang lebih besar masih parsial**. PDF adalah pembaca utama; HTML semantik responsif dan EPUB reflow adalah permukaan pembaca tambahan. Laboratorium menyertakan kode serta hasil JSON, CSV, dan SVG, sehingga nilai numerik dapat diperiksa tanpa bergantung pada grafik.

Tranche ini merupakan lapisan penghubung yang ditulis mandiri. Cakupannya adalah ketaksamaan variasional bentuk Stampacchia sebagai inklusi kerucut-normal, operator monoton dan monoton maksimal, kriteria rentang Minty dan resolven, metode titik proksimal, pemisahan maju–mundur, ekstragradien Korpelevich untuk operator monoton Lipschitz, pemisahan Douglas–Rachford, serta contoh skew yang menunjukkan mengapa kemonotonan saja tidak cukup bagi langkah maju. Paket mempertahankan delapan segmen, 53 label sumber, 45 permukaan matematika display, enam latihan, enam petunjuk bertahap, enam solusi lengkap, hubungan rujuk silang, dan keluaran laboratorium yang dapat direproduksi.

## Provenans dan hak

Uraian, definisi, bukti penghubung, algoritme, latihan, petunjuk, solusi, laboratorium, dan dokumentasi baru tranche ini ditulis untuk edisi ini dan dilisensikan **CC BY-SA 4.0**. Infrastruktur `shinybook.cls` adalah salinan persis dari paket sumber Andreas Habring, *Lecture Notes: Convex Optimization*, arXiv:2607.11664v1; `macros-id.tex` adalah adaptasi lokal dari `macros.tex`. Bukti tingkat kiriman arXiv untuk scaffold tersebut adalah CC BY 4.0; komponen itu tidak diubah menjadi CC BY-SA. Batas komponen dan kewajibannya dirinci dalam `RIGHTS_AND_PROVENANCE_ORIGINAL_02.md` serta dua catatan lisensi yang disertakan.

Karya Andreas Habring, Christian Clason, Stephen Becker, Mitchell Krock, George J. Minty, R. Tyrrell Rockafellar, Pierre-Louis Lions, dan Bertrand Mercier disebut sebagai atribusi matematika, prasyarat, atau saksi verifikasi. Tidak ada prosa, tata letak, gambar, latihan, solusi, atau kode mereka yang didistribusikan sebagai materi baru tranche ini. Tidak ada penulis, institusi, penerbit, repositori, atau sumber yang disebut menyusun, memeriksa, menyetujui, mensponsori, atau mendukung edisi ini.

## QA, backend, dan kelanjutan

Paket memuat receipt final untuk matematika, build dan visual PDF, build dan browser HTML, build dan konformansi EPUB/EPUBCheck, admission backend stable-ID, hak/non-overlap O018, serta rereview independen. Builder dan validator O2 yang terpisah ikut disertakan. `release-manifest-original-02.json` mencatat byte dan SHA-256 setiap anggota; `SHA256SUMS` memverifikasi semua anggota selain dirinya sendiri.

Backend lengkap tetap berada di repositori agar payload ini ringkas. Paket hanya memuat skema, script extension/validation, dan receipt yang membuktikan baseline terlindungi, namespace O2, ID set/order, serta rekonstruksi byte yang tepat. Materi saksi, arsip sumber resmi, legal-code witness, cache, render QA sementara, dan kredensial juga tidak dibundel.

Batas kursus berikutnya mencakup penutupan asesmen kumulatif, laboratorium tambahan, capstone, dan permukaan aksesibilitas edisi penuh. Paket ini tidak mengklaim bahwa pekerjaan kursus tersebut telah selesai.

Provenans produksi: **OpenAI Codex gpt-5.6-sol, Ultra**, atas instruksi pengguna repositori. Penanda ini tidak menggantikan kredit penulis atau kontributor manusia.
