# SYSTEM SPECIFICATION DOCUMENT: MediSync AI

## 1. Ikhtisar Proyek & Ruang Lingkup (*Project Overview & Scope*)
* **Nama Sistem:** **MediSync AI - Integrated Hospital Intelligence Platform**
* **Tujuan Utama:** Menyediakan platform manajemen rumah sakit cerdas yang mengintegrasikan alur operasional klinis, manajemen antrian, pemantauan *real-time*, analisis multi-modal berbasis AI untuk diagnosis dini, sistem peringatan dini (*Early Warning System*), serta otomatisasi pelaporan medis yang ramah pasien.
* **Peran Pengguna (*User Roles*):**
  1. **Hospital Admin:** Mengelola data master (dokter, poli, ruangan), konfigurasi jadwal, pemantauan operasional rumah sakit secara keseluruhan, dan manajemen antrian global.
  2. **Doctor:** Mengelola rekam medis pasien, memantau tanda vital secara *real-time*, menerima hasil prediksi AI multi-modal (tabular, teks, gambar medis), menetapkan diagnosis/resep, dan menyetujui draf laporan medis dari LLM.
  3. **Patient:** Mengakses nomor antrian digital, melihat jadwal konsultasi, menerima hasil laporan medis yang disederhanakan oleh LLM, serta memantau rekomendasi perilaku/gaya hidup sehat.

---

## 2. Arsitektur Sistem & Tumpukan Teknologi (*Tech Stack*)
* **Backend:** Python 3.11+, **FastAPI** (asynchronous API, WebSockets untuk *live monitoring* dan antrian).
* **Frontend:** **Next.js (App Router)** + **React**, TypeScript, Tailwind CSS, Shadcn UI / Tabler Icons untuk antarmuka yang bersih dan responsif.
* **Database & Penyimpanan:**
  * **PostgreSQL:** Penyimpanan relasional utama (data pengguna, profil pasien, rekam medis, penjadwalan, transaksi).
  * **Redis:** Manajemen *in-memory cache*, *message broker* untuk sistem antrian (*real-time queue sync*), dan manajemen sesi WebSocket.
  * **Object Storage (MinIO / AWS S3 compatible):** Penyimpanan berkas gambar medis (DICOM, X-Ray, MRI, CT-Scan) dan lampiran dokumen.
* **AI & Machine Learning Pipeline:**
  * **PyTorch / Hugging Face Transformers:** Untuk pemrosesan model LLM lokal/API (analisis teks keluhan, ekstraksi entitas klinis, penyusunan draf laporan).
  * **Ultralytics YOLO / Torchvision:** Untuk segmentasi/klasifikasi gambar medis (deteksi anomali pada pemindaian citra).
  * **Scikit-Learn / Gradient Boosting (XGBoost):** Untuk model prediktif data tabular (risiko penyakit, skor EWS).

---

## 3. Skema Basis Data Utama (`PostgreSQL`)

| Tabel | Kolom Utama | Deskripsi |
| :--- | :--- | :--- |
| `users` | `id`, `email`, `password_hash`, `role` (admin/doctor/patient), `created_at` | Autentikasi dan kontrol akses berbasis peran (RBAC). |
| `patients` | `id`, `user_id`, `nik`, `full_name`, `dob`, `gender`, `phone`, `medical_history_json` | Profil detail pasien dan riwayat ringkas. |
| `doctors` | `id`, `user_id`, `specialization`, `license_number`, `room_number`, `status` | Informasi spesialisasi dan status ketersediaan dokter. |
| `queues` | `id`, `patient_id`, `doctor_id`, `poli_name`, `queue_number`, `status` (waiting/serving/done/cancelled) | Sistem antrian real-time berbasis poling/WebSocket. |
| `medical_encounters`| `id`, `patient_id`, `doctor_id`, `complaint_text`, `tabular_metrics_json`, `status` | Sesi pemeriksaan medis, keluhan mentah, dan metrik vital. |
| `ai_predictions` | `id`, `encounter_id`, `model_name`, `prediction_result_json`, `confidence_score` | Hasil inferensi AI (multi-modal: tabular, teks, gambar). |
| `treatment_plans` | `id`, `encounter_id`, `diagnosis`, `prescription_drugs`, `behavioral_advice`, `ews_level` | Rencana pengobatan (obat oleh dokter, saran perilaku oleh LLM/dokter). |
| `clinical_reports` | `id`, `encounter_id`, `raw_notes`, `patient_friendly_report`, `status` (draft/approved) | Draf laporan medis yang dirapikan oleh LLM untuk pasien. |

---

## 4. Spesifikasi Modul Fungsional & Fitur AI

### A. Modul Antrian & Pemantauan Real-Time (`Queue & Monitoring`)
* Integrasi Redis dan WebSocket untuk memperbarui nomor antrian secara langsung di layar tunggu admin, poli, dan perangkat pasien tanpa *refresh* halaman.
* Dasbor pemantauan bagi dokter untuk melihat daftar pasien aktif dan status tanda vital darurat (*Early Warning System / EWS*).

### B. Analisis Multi-Modal & Prediksi Penyakit Berbasis AI
* **Input Tabular:** Data tekanan darah, detak jantung, kadar gula darah, suhu tubuh, dll. Diproses melalui model klasifikasi risiko (*XGBoost/Random Forest*).
* **Input Teks (Keluhan):** Menggunakan NLP (LLM Embedding/Extraction) untuk mengekstrak gejala utama dari narasi keluhan pasien.
* **Input Gambar Medis:** Pemrosesan citra (X-Ray/MRI) melalui model *Computer Vision* (PyTorch/CNN) untuk mendeteksi indikasi awal kelainan atau lesi.
* **Agregator Keputusan:** Menggabungkan skor dari ketiga modalitas untuk menghasilkan probabilitas diagnosis banding bagi dokter.

### C. Early Warning System (EWS) & Sistem Rekomendasi
* Algoritma *rule-based* + AI yang memantau fluktuasi vital sign secara kontinu. Jika EWS mencapai ambang batas kritis, sistem memicu notifikasi darurat ke perawat/dokter penanggung jawab.
* **Rekomendasi Pengobatan & Perilaku:** Dokter menetapkan resep farmakologis, sementara LLM menghasilkan panduan gaya hidup/perilaku harian (*behavioral lifestyle advice*) yang dipersonalisasi untuk pasien.

### D. Generator Laporan Medis Ramah Pasien (`LLM Report Generation`)
* Menerjemahkan catatan klinis dokter yang penuh istilah medis teknis menjadi laporan naratif yang terstruktur, rapi, empatik, dan mudah dipahami oleh orang awam. Laporan ini memerlukan tinjauan (*approval*) dari dokter sebelum dapat diakses oleh pasien.

---

## 5. Struktur Direktori Proyek yang Direkomendasikan
```text
medisync-ai/
├── spec.md
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/ (config, security, database)
│   │   ├── models/ (SQLAlchemy models)
│   │   ├── schemas/ (Pydantic schemas)
│   │   ├── api/ (routes untuk auth, admin, doctor, patient, queue)
│   │   ├── services/ (queue_service, ews_service, llm_report_service)
│   │   └── ai_pipeline/ (tabular_predictor.py, nlp_extractor.py, vision_analyzer.py)
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── app/ (admin/, doctor/, patient/, login/)
    │   ├── components/ (ui/, charts/, queue-board/, ai-insights/)
    │   ├── lib/ (api.ts, websocket.ts)
    │   └── types/
    └── package.json
```