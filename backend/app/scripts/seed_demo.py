# -*- coding: utf-8 -*-
"""
MediSync AI — Full Demo Seed Script
======================================
Seeds the database with rich dummy data so every dashboard shows populated content.

Data created:
  - 1 Admin user
  - 3 Doctors (different specializations)
  - 6 Patients (varied demographics and medical histories)
  - 12 Queue entries (across multiple polis)
  - 9 Medical Encounters (with vitals, complaints, image keys)
  - 9 AI Predictions (tabular + NLP + vision per encounter)
  - 9 Treatment Plans (with EWS levels, prescriptions, behavioral advice)
  - 6 Clinical Reports (mix of draft and approved)

Usage:
    cd backend
    python -m app.scripts.seed_demo
"""
import asyncio
import sys
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models.models import (
    AIPrediction,
    Base,
    ClinicalReport,
    Doctor,
    MedicalEncounter,
    Patient,
    Queue,
    TreatmentPlan,
    User,
)


# ── Helper ────────────────────────────────────────────────────────────────────

async def _user_exists(db, email: str) -> bool:
    r = await db.execute(select(User).where(User.email == email))
    return r.scalar_one_or_none() is not None


# ── Seed data definitions ─────────────────────────────────────────────────────

DOCTORS_DATA = [
    {
        "email": "doctor@demo.com",
        "password": "demo1234",
        "specialization": "General Practitioner",
        "license_number": "STR-GP-2024-001",
        "room_number": "101",
        "status": "available",
    },
    {
        "email": "dr.kardio@demo.com",
        "password": "demo1234",
        "specialization": "Cardiologist",
        "license_number": "STR-CARD-2024-002",
        "room_number": "205",
        "status": "busy",
    },
    {
        "email": "dr.neuro@demo.com",
        "password": "demo1234",
        "specialization": "Neurologist",
        "license_number": "STR-NEURO-2024-003",
        "room_number": "312",
        "status": "available",
    },
]

PATIENTS_DATA = [
    {
        "email": "patient@demo.com",
        "password": "demo1234",
        "nik": "3201234567890001",
        "full_name": "Budi Santoso",
        "dob": date(1985, 3, 20),
        "gender": "male",
        "phone": "081234567890",
        "medical_history_json": {
            "allergies": ["penicillin"],
            "chronic_conditions": ["hypertension"],
            "blood_type": "O+",
        },
    },
    {
        "email": "patient2@demo.com",
        "password": "demo1234",
        "nik": "3201234567890002",
        "full_name": "Siti Rahayu",
        "dob": date(1992, 7, 11),
        "gender": "female",
        "phone": "082345678901",
        "medical_history_json": {
            "allergies": [],
            "chronic_conditions": ["type2_diabetes"],
            "blood_type": "A+",
        },
    },
    {
        "email": "patient3@demo.com",
        "password": "demo1234",
        "nik": "3201234567890003",
        "full_name": "Ahmad Fauzi",
        "dob": date(1978, 11, 5),
        "gender": "male",
        "phone": "083456789012",
        "medical_history_json": {
            "allergies": ["aspirin"],
            "chronic_conditions": ["COPD"],
            "blood_type": "B-",
        },
    },
    {
        "email": "patient4@demo.com",
        "password": "demo1234",
        "nik": "3201234567890004",
        "full_name": "Dewi Lestari",
        "dob": date(2000, 1, 30),
        "gender": "female",
        "phone": "084567890123",
        "medical_history_json": {
            "allergies": [],
            "chronic_conditions": [],
            "blood_type": "AB+",
        },
    },
    {
        "email": "patient5@demo.com",
        "password": "demo1234",
        "nik": "3201234567890005",
        "full_name": "Hendra Gunawan",
        "dob": date(1960, 9, 14),
        "gender": "male",
        "phone": "085678901234",
        "medical_history_json": {
            "allergies": [],
            "chronic_conditions": ["coronary_artery_disease", "hypertension"],
            "blood_type": "O-",
        },
    },
    {
        "email": "patient6@demo.com",
        "password": "demo1234",
        "nik": "3201234567890006",
        "full_name": "Rina Wijaya",
        "dob": date(1995, 5, 22),
        "gender": "female",
        "phone": "086789012345",
        "medical_history_json": {
            "allergies": ["sulfa"],
            "chronic_conditions": ["migraine"],
            "blood_type": "A-",
        },
    },
]

# Encounter scenarios: each maps to one doctor + one patient (by index)
ENCOUNTERS_DATA = [
    {
        "doctor_idx": 0,  # General Practitioner
        "patient_idx": 0,  # Budi Santoso
        "complaint": "Pasien mengeluhkan sakit kepala berdenyut yang sudah berlangsung 3 hari, disertai mual dan pandangan kabur. Tekanan darah tinggi berulang.",
        "vitals": {"bp_systolic": 158, "bp_diastolic": 98, "heart_rate": 88, "temperature": 36.9, "spo2": 97, "glucose": 145},
        "status": "pending_report",
        "ews_level": 2,
        "diagnosis": "Hipertensi Grade II dengan gejala sefalgia",
        "prescription": [
            {"drug": "Amlodipine", "dose": "5mg", "frequency": "1x sehari pagi"},
            {"drug": "Paracetamol", "dose": "500mg", "frequency": "3x sehari jika nyeri"},
        ],
        "behavioral_advice": "Kurangi konsumsi garam dan makanan berlemak. Olahraga ringan 30 menit setiap hari. Pantau tekanan darah secara rutin setiap pagi. Hindari stres berlebihan dan tidur cukup 7-8 jam.",
        "report_status": "approved",
    },
    {
        "doctor_idx": 0,
        "patient_idx": 1,  # Siti Rahayu
        "complaint": "Pasien datang dengan keluhan sering buang air kecil, mudah lelah, dan pandangan buram sejak 2 minggu lalu. Riwayat diabetes tipe 2.",
        "vitals": {"bp_systolic": 135, "bp_diastolic": 85, "heart_rate": 82, "temperature": 37.1, "spo2": 98, "glucose": 285},
        "status": "pending_report",
        "ews_level": 2,
        "diagnosis": "Hiperglikemia pada Diabetes Mellitus Tipe 2 tidak terkontrol",
        "prescription": [
            {"drug": "Metformin", "dose": "500mg", "frequency": "2x sehari bersama makan"},
            {"drug": "Glibenclamide", "dose": "2.5mg", "frequency": "1x sehari pagi"},
        ],
        "behavioral_advice": "Ikuti diet rendah karbohidrat dan rendah gula. Olahraga aerobik ringan 150 menit per minggu. Pantau gula darah mandiri setiap pagi sebelum makan. Hindari makanan dan minuman manis.",
        "report_status": "approved",
    },
    {
        "doctor_idx": 1,  # Cardiologist
        "patient_idx": 4,  # Hendra Gunawan
        "complaint": "Pasien pria 65 tahun mengeluhkan nyeri dada kiri yang menjalar ke lengan kiri sejak 2 jam yang lalu. Disertai keringat dingin dan sesak napas.",
        "vitals": {"bp_systolic": 95, "bp_diastolic": 60, "heart_rate": 115, "temperature": 36.5, "spo2": 92, "glucose": 110},
        "status": "open",
        "ews_level": 3,
        "diagnosis": "Suspek Sindrom Koroner Akut (NSTEMI)",
        "prescription": [
            {"drug": "Aspirin", "dose": "160mg", "frequency": "1x segera (loading dose)"},
            {"drug": "Clopidogrel", "dose": "300mg", "frequency": "1x segera (loading dose)"},
            {"drug": "Nitrogliserin", "dose": "0.5mg", "frequency": "sublingual setiap 5 menit jika nyeri, max 3x"},
        ],
        "behavioral_advice": "PRIORITAS: Rawat inap segera untuk observasi dan monitoring jantung. Istirahat total. Hindari aktivitas fisik sampai kondisi stabil.",
        "report_status": "draft",
    },
    {
        "doctor_idx": 0,
        "patient_idx": 2,  # Ahmad Fauzi
        "complaint": "Batuk berdahak sudah 2 minggu, sesak napas terutama saat aktivitas, dan dada terasa berat. Riwayat PPOK.",
        "vitals": {"bp_systolic": 128, "bp_diastolic": 80, "heart_rate": 94, "temperature": 37.4, "spo2": 93, "glucose": 95},
        "status": "pending_report",
        "ews_level": 2,
        "diagnosis": "Eksaserbasi PPOK (Penyakit Paru Obstruktif Kronik)",
        "prescription": [
            {"drug": "Salbutamol inhaler", "dose": "100mcg", "frequency": "2 puff tiap 4-6 jam"},
            {"drug": "Prednisone", "dose": "30mg", "frequency": "1x sehari selama 5 hari"},
            {"drug": "Amoxicillin", "dose": "500mg", "frequency": "3x sehari selama 7 hari"},
        ],
        "behavioral_advice": "Hentikan merokok segera — ini prioritas utama untuk PPOK. Latihan pernapasan pursed-lip breathing. Hindari polusi udara dan debu. Gunakan inhaler dengan teknik yang benar.",
        "report_status": "approved",
    },
    {
        "doctor_idx": 2,  # Neurologist
        "patient_idx": 5,  # Rina Wijaya
        "complaint": "Sakit kepala sebelah kiri berdenyut hebat disertai mual muntah, fotofobia, dan fonofobia. Sudah 6 jam tidak membaik.",
        "vitals": {"bp_systolic": 122, "bp_diastolic": 76, "heart_rate": 76, "temperature": 36.7, "spo2": 99, "glucose": 88},
        "status": "pending_report",
        "ews_level": 1,
        "diagnosis": "Migrain dengan aura",
        "prescription": [
            {"drug": "Sumatriptan", "dose": "50mg", "frequency": "1x saat serangan, bisa diulang setelah 2 jam"},
            {"drug": "Metoclopramide", "dose": "10mg", "frequency": "3x sehari untuk mual"},
        ],
        "behavioral_advice": "Identifikasi dan hindari pemicu migrain (makanan tertentu, kurang tidur, stres). Tidur teratur 7-8 jam di lingkungan gelap dan tenang. Olahraga aerobik rutin dapat mengurangi frekuensi serangan.",
        "report_status": "approved",
    },
    {
        "doctor_idx": 0,
        "patient_idx": 3,  # Dewi Lestari
        "complaint": "Demam tinggi 3 hari, nyeri sendi dan otot, bintik merah di kulit, dan trombosit menurun menurut hasil lab kemarin.",
        "vitals": {"bp_systolic": 110, "bp_diastolic": 70, "heart_rate": 102, "temperature": 38.9, "spo2": 97, "glucose": 90},
        "status": "pending_report",
        "ews_level": 2,
        "diagnosis": "Demam Berdarah Dengue (DBD) fase kritis",
        "prescription": [
            {"drug": "Paracetamol", "dose": "500mg", "frequency": "3x sehari jika demam > 38.5°C"},
            {"drug": "Oralit", "dose": "200ml", "frequency": "setiap kali BAB cair atau berkeringat banyak"},
        ],
        "behavioral_advice": "Perbanyak minum air putih minimal 2 liter per hari. Istirahat total. Pantau tanda bahaya: muntah terus menerus, perdarahan, atau kesadaran menurun → segera ke IGD.",
        "report_status": "approved",
    },
    {
        "doctor_idx": 1,
        "patient_idx": 0,  # Budi Santoso (follow-up)
        "complaint": "Kontrol hipertensi. Pasien melaporkan tekanan darah masih sering tinggi meski sudah minum obat. Pusing sesekali.",
        "vitals": {"bp_systolic": 148, "bp_diastolic": 92, "heart_rate": 80, "temperature": 36.6, "spo2": 98, "glucose": 120},
        "status": "open",
        "ews_level": 1,
        "diagnosis": "Hipertensi tidak terkontrol — perlu titrasi obat",
        "prescription": [
            {"drug": "Amlodipine", "dose": "10mg", "frequency": "1x sehari pagi (dosis ditingkatkan)"},
            {"drug": "Valsartan", "dose": "80mg", "frequency": "1x sehari"},
        ],
        "behavioral_advice": "Lanjutkan diet DASH (rendah sodium). Target tekanan darah < 130/80 mmHg. Ukur tekanan darah 2x sehari dan catat hasilnya. Kurangi kafein.",
        "report_status": "draft",
    },
    {
        "doctor_idx": 2,
        "patient_idx": 1,  # Siti Rahayu (neurology consult)
        "complaint": "Kesemutan dan mati rasa di kedua kaki yang makin parah dalam 1 bulan terakhir, terutama malam hari.",
        "vitals": {"bp_systolic": 130, "bp_diastolic": 82, "heart_rate": 78, "temperature": 36.8, "spo2": 98, "glucose": 198},
        "status": "pending_report",
        "ews_level": 1,
        "diagnosis": "Neuropati Diabetik Perifer",
        "prescription": [
            {"drug": "Mecobalamin", "dose": "500mcg", "frequency": "3x sehari"},
            {"drug": "Alpha Lipoic Acid", "dose": "600mg", "frequency": "1x sehari"},
            {"drug": "Pregabalin", "dose": "75mg", "frequency": "2x sehari untuk nyeri neuropatik"},
        ],
        "behavioral_advice": "Kontrol gula darah ketat adalah kunci utama. Periksa kaki setiap hari untuk luka atau lecet. Gunakan alas kaki yang nyaman. Hindari posisi kaki menyilang terlalu lama.",
        "report_status": "approved",
    },
    {
        "doctor_idx": 0,
        "patient_idx": 5,  # Rina Wijaya (GP follow-up)
        "complaint": "Nyeri tenggorokan, demam ringan, hidung tersumbat, dan batuk kering sejak 2 hari. Tidak ada sesak napas.",
        "vitals": {"bp_systolic": 118, "bp_diastolic": 74, "heart_rate": 86, "temperature": 37.8, "spo2": 99, "glucose": 92},
        "status": "closed",
        "ews_level": 0,
        "diagnosis": "Infeksi Saluran Pernapasan Atas (ISPA) viral",
        "prescription": [
            {"drug": "Paracetamol", "dose": "500mg", "frequency": "3x sehari jika demam/nyeri"},
            {"drug": "Cetirizine", "dose": "10mg", "frequency": "1x sehari malam untuk hidung tersumbat"},
            {"drug": "Vit C", "dose": "500mg", "frequency": "1x sehari"},
        ],
        "behavioral_advice": "Istirahat cukup dan perbanyak minum air hangat. Makan bergizi untuk memperkuat imun. ISPA viral biasanya sembuh sendiri dalam 7-10 hari. Tidak perlu antibiotik.",
        "report_status": "approved",
    },
]

QUEUE_DATA = [
    {"poli": "General", "queue_number": 1, "status": "serving"},
    {"poli": "General", "queue_number": 2, "status": "waiting"},
    {"poli": "General", "queue_number": 3, "status": "waiting"},
    {"poli": "Cardiology", "queue_number": 1, "status": "serving"},
    {"poli": "Cardiology", "queue_number": 2, "status": "waiting"},
    {"poli": "Neurology", "queue_number": 1, "status": "waiting"},
    {"poli": "Pediatrics", "queue_number": 1, "status": "done"},
    {"poli": "Pediatrics", "queue_number": 2, "status": "waiting"},
    {"poli": "Orthopedics", "queue_number": 1, "status": "waiting"},
    {"poli": "General", "queue_number": 4, "status": "done"},
    {"poli": "General", "queue_number": 5, "status": "done"},
    {"poli": "Cardiology", "queue_number": 3, "status": "cancelled"},
]


# ── Seed function ─────────────────────────────────────────────────────────────

async def seed() -> None:
    """Create all tables and populate with rich demo data."""
    # Force UTF-8 output on Windows so emoji/special chars don't crash
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("MediSync AI -- Starting demo seed...\n")

    # Ensure all tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  [DB]  Tables created/verified.")

    async with AsyncSessionLocal() as db:

        # ── 1. Admin ──────────────────────────────────────────────────────────
        print("\n── Admin ──────────────────────────")
        if not await _user_exists(db, "admin@demo.com"):
            admin_user = User(
                email="admin@demo.com",
                password_hash=hash_password("demo1234"),
                role="admin",
            )
            db.add(admin_user)
            await db.flush()
            print("  [OK]  Created admin: admin@demo.com")
        else:
            print("  [--]  admin@demo.com already exists")

        # ── 2. Doctors ────────────────────────────────────────────────────────
        print("\n── Doctors ────────────────────────")
        doctor_records: list[Doctor] = []
        for d_data in DOCTORS_DATA:
            if await _user_exists(db, d_data["email"]):
                # Fetch existing doctor profile
                r = await db.execute(
                    select(Doctor).join(User).where(User.email == d_data["email"])
                )
                existing = r.scalar_one_or_none()
                if existing:
                    doctor_records.append(existing)
                    print(f"  [--]  {d_data['email']} already exists")
                    continue

            user = User(
                email=d_data["email"],
                password_hash=hash_password(d_data["password"]),
                role="doctor",
            )
            db.add(user)
            await db.flush()

            doctor = Doctor(
                user_id=user.id,
                specialization=d_data["specialization"],
                license_number=d_data["license_number"],
                room_number=d_data["room_number"],
                status=d_data["status"],
            )
            db.add(doctor)
            await db.flush()
            doctor_records.append(doctor)
            print(f"  [OK]  Created doctor: {d_data['email']} ({d_data['specialization']})")

        await db.commit()

        # ── 3. Patients ───────────────────────────────────────────────────────
        print("\n── Patients ───────────────────────")
        patient_records: list[Patient] = []
        for p_data in PATIENTS_DATA:
            if await _user_exists(db, p_data["email"]):
                r = await db.execute(
                    select(Patient).join(User).where(User.email == p_data["email"])
                )
                existing = r.scalar_one_or_none()
                if existing:
                    patient_records.append(existing)
                    print(f"  [--]  {p_data['full_name']} already exists")
                    continue

            user = User(
                email=p_data["email"],
                password_hash=hash_password(p_data["password"]),
                role="patient",
            )
            db.add(user)
            await db.flush()

            patient = Patient(
                user_id=user.id,
                nik=p_data["nik"],
                full_name=p_data["full_name"],
                dob=p_data["dob"],
                gender=p_data["gender"],
                phone=p_data["phone"],
                medical_history_json=p_data["medical_history_json"],
            )
            db.add(patient)
            await db.flush()
            patient_records.append(patient)
            print(f"  [OK]  Created patient: {p_data['full_name']} ({p_data['email']})")

        await db.commit()

        # Reload fresh records to get correct IDs
        for i, d_data in enumerate(DOCTORS_DATA):
            if i >= len(doctor_records) or doctor_records[i] is None:
                continue
            await db.refresh(doctor_records[i])
        for i in range(len(patient_records)):
            await db.refresh(patient_records[i])

        # ── 4. Queues ─────────────────────────────────────────────────────────
        print("\n── Queues ─────────────────────────")
        existing_queues = (await db.execute(select(Queue))).scalars().all()
        if existing_queues:
            print(f"  [--]  {len(existing_queues)} queues already exist, skipping.")
        else:
            # Assign patients round-robin to queue entries
            for i, q_data in enumerate(QUEUE_DATA):
                p_idx = i % len(patient_records)
                d_idx = i % len(doctor_records)
                entry = Queue(
                    patient_id=patient_records[p_idx].id,
                    doctor_id=doctor_records[d_idx].id,
                    poli_name=q_data["poli"],
                    queue_number=q_data["queue_number"],
                    status=q_data["status"],
                )
                db.add(entry)
            await db.commit()
            print(f"  [OK]  Created {len(QUEUE_DATA)} queue entries")

        # ── 5. Encounters + Plans + Predictions + Reports ─────────────────────
        print("\n── Encounters + AI + Plans + Reports ──")
        existing_encs = (await db.execute(select(MedicalEncounter))).scalars().all()
        if existing_encs:
            print(f"  [--]  {len(existing_encs)} encounters already exist, skipping.")
        else:
            for i, enc_data in enumerate(ENCOUNTERS_DATA):
                d_idx = enc_data["doctor_idx"]
                p_idx = enc_data["patient_idx"]

                if d_idx >= len(doctor_records) or p_idx >= len(patient_records):
                    continue

                # ── Encounter ─────────────────────────────────────────────────
                encounter = MedicalEncounter(
                    patient_id=patient_records[p_idx].id,
                    doctor_id=doctor_records[d_idx].id,
                    complaint_text=enc_data["complaint"],
                    tabular_metrics_json=enc_data["vitals"],
                    status=enc_data["status"],
                )
                db.add(encounter)
                await db.flush()

                # ── AI Prediction (tabular) ───────────────────────────────────
                vitals = enc_data["vitals"]
                score = 0
                flags = []
                if vitals.get("bp_systolic", 120) > 150: score += 2; flags.append("high_bp")
                if vitals.get("heart_rate", 72) > 100: score += 1; flags.append("tachycardia")
                if vitals.get("temperature", 36.8) > 38: score += 1; flags.append("fever")
                if vitals.get("spo2", 98) < 95: score += 2; flags.append("low_spo2")
                if vitals.get("glucose", 100) > 200: score += 1; flags.append("hyperglycemia")

                risk_labels = ["normal", "low_risk", "medium_risk", "high_risk"]
                label = risk_labels[min(score, 3)]

                tabular_pred = AIPrediction(
                    encounter_id=encounter.id,
                    model_name="tabular_xgboost",
                    prediction_result_json={
                        "predicted_label": label,
                        "risk_score": score,
                        "triggered_flags": flags,
                        "mode": "heuristic_simulation",
                    },
                    confidence_score=round(max(0.60, 1.0 - score * 0.08), 2),
                )
                db.add(tabular_pred)

                # ── AI Prediction (NLP) ──────────────────────────────────────
                complaint_lower = enc_data["complaint"].lower()
                matched_syms = []
                candidates = set()
                symptom_map = {
                    "sakit kepala": ["tension_headache", "migraine", "hypertension"],
                    "nyeri dada": ["angina", "myocardial_infarction"],
                    "sesak napas": ["asthma", "heart_failure", "COPD"],
                    "demam": ["infection", "dengue", "typhoid"],
                    "batuk": ["URTI", "pneumonia", "COPD"],
                    "pusing": ["hypotension", "anemia"],
                    "mual": ["gastritis", "dengue"],
                    "kesemutan": ["neuropathy", "diabetes"],
                    "nyeri sendi": ["dengue", "arthritis"],
                }
                for sym, conds in symptom_map.items():
                    if sym in complaint_lower:
                        matched_syms.append(sym)
                        candidates.update(conds)

                nlp_pred = AIPrediction(
                    encounter_id=encounter.id,
                    model_name="nlp_extractor",
                    prediction_result_json={
                        "matched_symptoms": matched_syms[:5],
                        "candidate_diagnoses": sorted(candidates)[:6],
                        "word_count": len(enc_data["complaint"].split()),
                        "mode": "keyword_heuristic",
                    },
                    confidence_score=round(min(0.9, 0.5 + len(matched_syms) * 0.1), 2),
                )
                db.add(nlp_pred)

                # ── AI Prediction (vision — simulated) ───────────────────────
                findings = ["normal", "pneumonia", "pleural_effusion", "cardiomegaly", "atelectasis"]
                finding = findings[i % len(findings)]
                vision_pred = AIPrediction(
                    encounter_id=encounter.id,
                    model_name="vision_cnn",
                    prediction_result_json={
                        "predicted_finding": finding,
                        "probabilities": {
                            f: round(0.80 if f == finding else 0.05, 2)
                            for f in findings
                        },
                        "mode": "simulation",
                        "note": "Simulated result — no trained model loaded.",
                    },
                    confidence_score=round(0.72 + (i * 3 % 20) / 100, 2),
                )
                db.add(vision_pred)

                # ── Treatment Plan ────────────────────────────────────────────
                plan = TreatmentPlan(
                    encounter_id=encounter.id,
                    diagnosis=enc_data["diagnosis"],
                    prescription_drugs=enc_data["prescription"],
                    behavioral_advice=enc_data["behavioral_advice"],
                    ews_level=enc_data["ews_level"],
                )
                db.add(plan)

                # ── Clinical Report ───────────────────────────────────────────
                raw_notes = (
                    f"Keluhan: {enc_data['complaint']}\n"
                    f"Tanda Vital: {enc_data['vitals']}\n"
                    f"Diagnosis: {enc_data['diagnosis']}\n"
                    f"Resep: {enc_data['prescription']}"
                )
                friendly = _build_friendly_report(enc_data, patient_records[p_idx].full_name)

                report = ClinicalReport(
                    encounter_id=encounter.id,
                    raw_notes=raw_notes,
                    patient_friendly_report=friendly,
                    status=enc_data["report_status"],
                )
                db.add(report)

                await db.flush()
                print(f"  [OK]  Encounter {i+1}: {patient_records[p_idx].full_name} -> {enc_data['diagnosis'][:50]}")

            await db.commit()

        print("\n[DONE] Demo seed completed successfully!")
        print("\nLogin credentials:")
        print("   admin@demo.com        / demo1234  (Admin)")
        print("   doctor@demo.com       / demo1234  (General Practitioner)")
        print("   dr.kardio@demo.com    / demo1234  (Cardiologist)")
        print("   dr.neuro@demo.com     / demo1234  (Neurologist)")
        print("   patient@demo.com      / demo1234  (Patient - Budi Santoso)")
        print("   patient2@demo.com     / demo1234  (Patient - Siti Rahayu)")
        print("   ...and 4 more patients (patient3-6@demo.com)")


def _build_friendly_report(enc_data: dict, patient_name: str) -> str:
    """Generate a structured patient-friendly report from encounter data."""
    vitals = enc_data["vitals"]
    bp = f"{vitals.get('bp_systolic', '-')}/{vitals.get('bp_diastolic', '-')} mmHg"
    hr = f"{vitals.get('heart_rate', '-')} bpm"
    temp = f"{vitals.get('temperature', '-')} C"
    spo2 = f"{vitals.get('spo2', '-')} %"
    glucose = f"{vitals.get('glucose', '-')} mg/dL"

    drugs_text = "\n".join(
        f"  - {d['drug']} {d['dose']} - {d['frequency']}"
        for d in enc_data["prescription"]
    )

    ews_msg = {
        0: "Kondisi Anda saat ini **normal** dan tidak memerlukan tindakan darurat.",
        1: "Kondisi Anda memerlukan **pemantauan ringan** dan kontrol rutin.",
        2: "Kondisi Anda memerlukan **perhatian lebih** - mohon ikuti saran dokter dengan disiplin.",
        3: "Kondisi Anda **memerlukan perhatian segera** - pastikan Anda dalam pengawasan medis.",
    }.get(enc_data["ews_level"], "")

    return (
        "## Ringkasan Kesehatan Anda\n"
        "*Laporan dari MediSync AI - Disetujui oleh Dokter*\n\n"
        "---\n\n"
        f"Yth. {patient_name},\n\n"
        "Terima kasih telah mempercayakan kesehatan Anda kepada kami. "
        "Berikut adalah ringkasan hasil pemeriksaan Anda dalam bahasa yang mudah dipahami.\n\n"
        "---\n\n"
        "### Ringkasan Pemeriksaan\n\n"
        f"{ews_msg}\n\n"
        "**Keluhan Utama:**\n"
        f"{enc_data['complaint'][:200]}\n\n"
        "---\n\n"
        "### Hasil Tanda Vital Anda\n\n"
        "| Parameter | Hasil |\n"
        "|-----------|-------|\n"
        f"| Tekanan Darah | {bp} |\n"
        f"| Detak Jantung | {hr} |\n"
        f"| Suhu Tubuh | {temp} |\n"
        f"| Saturasi Oksigen | {spo2} |\n"
        f"| Gula Darah | {glucose} |\n\n"
        "---\n\n"
        "### Apa yang Ditemukan Dokter\n\n"
        f"Berdasarkan hasil pemeriksaan, dokter menetapkan diagnosis: **{enc_data['diagnosis']}**\n\n"
        "---\n\n"
        "### Obat yang Diresepkan\n\n"
        f"{drugs_text}\n\n"
        "> Penting: Minum obat sesuai aturan. Jangan menghentikan obat tanpa berkonsultasi dengan dokter.\n\n"
        "---\n\n"
        "### Saran Gaya Hidup untuk Anda\n\n"
        f"{enc_data['behavioral_advice']}\n\n"
        "---\n\n"
        "### Tindak Lanjut\n\n"
        "Mohon lakukan kontrol ulang sesuai jadwal yang ditetapkan dokter. "
        "Jika gejala memburuk atau muncul keluhan baru sebelum jadwal kontrol, "
        "segera hubungi klinik atau datang ke IGD.\n\n"
        "---\n\n"
        "*Laporan ini dibuat oleh MediSync AI dan telah disetujui oleh dokter Anda.*\n"
        "*Untuk pertanyaan, hubungi tim layanan kesehatan kami.*\n"
    )


if __name__ == "__main__":
    asyncio.run(seed())
