# Modul Becker 3: Reduksi Varians untuk SAA

Ini adalah edisi kerja bahasa Indonesia yang mandiri atas satu rentang terbatas
dari catatan *Advanced Convex Optimization* milik Stephen Becker, dengan
catatan ketik `APPM5720Notes.tex` dikreditkan kepada Mitchell Krock. Modul ini
lengkap pada batas sumber yang dipilih, tetapi buku kuliah O015/D90 yang lebih
besar masih berstatus parsial.

Mulailah dari `D90-BECKER-03-reduksi-varians-id.pdf`. Berkas HTML dengan nama
dasar yang sama adalah pembaca semantik responsif. Sumber TeX, saksi bahasa
Inggris, kuitansi batas sumber, pemeriksaan matematika terbuka, build
deterministik, QA PDF/HTML, dan bukti backend ID stabil disertakan agar modul
dapat dibangun dan diperiksa kembali.

PDF dapat dicari tetapi belum bertag. HTML menyediakan struktur semantik dan
memakai URL CDN MathJax 3 yang dipatok; pemuatan rumus HTML memerlukan akses
jaringan, sedangkan teks dan struktur dokumen tetap terbaca tanpa skrip itu.

## Batas sumber

- Repositori resmi: <https://github.com/stephenbeckr/convex-optimization-class>
- Commit: `98ed6930084c435ba0f675f7646ced1f2fd8729e`
- Berkas donor: `TypedNotes/APPM5720Notes.tex`
- Rentang tepat: baris 2971--2988, 18 baris, 900 byte
- SHA-256 irisan: `b81634bf07565fcf8d2774bea7b96e565e5fdd76cf5e782c5e4eb6fb3268c5ed`
- Baris sebelum 2971 dan terminator dokumen mulai baris 2989 tidak diimpor.
  Algoritma lengkap SAG dan SVRG tidak diimpor dari bagian lain.

Edisi ini membedakan notasi fungsi kerugian dari konstanta Lipschitz,
menetapkan inisialisasi dan urutan pembaruan tabel secara eksplisit,
memperbaiki lingkup klaim konvergensi linear dan iterat rata-rata, serta
menambahkan bukti ketakbiasan, identitas varians, dua latihan, petunjuk, dan
solusi. Konstanta laju diperiksa terhadap hasil primer SAGA oleh Aaron Defazio,
Francis Bach, dan Simon Lacoste-Julien, arXiv:1407.0202v3. Makalah itu hanya
menjadi saksi lokal untuk hasil matematika dan tidak disertakan dalam paket.
Semua perubahan dinyatakan terbuka dalam pembaca dan `ADVERSE_LEDGER` proyek;
tidak disajikan sebagai perubahan yang disahkan pihak sumber.

## Hak dan kredit

Materi donor dan saksi bahasa Inggris tetap berada di bawah Lisensi MIT;
pemberitahuan lengkap ada di `LICENSE_BECKER_MIT.txt`. Terjemahan bahasa
Indonesia, koreksi, penghubung, latihan, solusi, dan dokumentasi baru tersedia
berdasarkan CC BY-SA 4.0 dengan cakupan yang dijelaskan di
`LICENSE_TRANSLATION_CC_BY-SA-4.0.md`. Kedua lapisan hak tetap terpisah.

Stephen Becker, Mitchell Krock, Aaron Defazio, Francis Bach, Simon
Lacoste-Julien, dan University of Colorado Boulder tidak menyusun, memeriksa,
menyetujui, atau mendukung edisi mandiri ini. Kredit kepada mereka
dipertahankan semata-mata untuk atribusi sumber atau hasil matematis terkait.

Provenans produksi edisi: OpenAI Codex gpt-5.6-sol, Ultra, atas instruksi
pengguna repositori. Tidak ada kontak hulu yang dilakukan selama produksi.
