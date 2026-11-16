/**
 * MediSync AI — Doctor: Encounters Page
 * Full encounter management — create, view vitals, change status.
 */
"use client";

import { useEffect, useState } from "react";
import { Activity, Plus, ChevronDown, ChevronUp } from "lucide-react";
import toast from "react-hot-toast";
import { doctorApi } from "@/lib/api";
import { type Encounter, type Patient } from "@/types";
import { Sidebar } from "@/components/ui/Sidebar";
import {
  LoadingSpinner,
  EmptyState,
  SectionHeader,
  Badge,
} from "@/components/ui";
import { format, parseISO } from "date-fns";
import { apiClient } from "@/lib/api";

export default function DoctorEncountersPage() {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  // New encounter form state
  const [selectedPatient, setSelectedPatient] = useState("");
  const [complaint, setComplaint] = useState("");
  const [vitals, setVitals] = useState({
    bp_systolic: "",
    bp_diastolic: "",
    heart_rate: "",
    temperature: "",
    spo2: "",
    glucose: "",
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([doctorApi.getMyEncounters(), doctorApi.listPatients()])
      .then(([encs, pats]) => {
        setEncounters(encs);
        setPatients(pats);
      })
      .catch(() => toast.error("Failed to load data."))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPatient) {
      toast.error("Please select a patient.");
      return;
    }
    setSubmitting(true);
    try {
      // Build vitals JSON — only include non-empty numeric fields
      const tabularMetrics: Record<string, number> = {};
      for (const [key, val] of Object.entries(vitals)) {
        if (val !== "") tabularMetrics[key] = parseFloat(val);
      }

      const enc = await doctorApi.createEncounter({
        patient_id: selectedPatient,
        complaint_text: complaint || undefined,
        tabular_metrics_json:
          Object.keys(tabularMetrics).length > 0 ? tabularMetrics : undefined,
      });

      setEncounters((prev) => [enc, ...prev]);
      setShowForm(false);
      setComplaint("");
      setSelectedPatient("");
      setVitals({ bp_systolic: "", bp_diastolic: "", heart_rate: "", temperature: "", spo2: "", glucose: "" });
      toast.success("Encounter created!");
    } catch {
      toast.error("Failed to create encounter.");
    } finally {
      setSubmitting(false);
    }
  };

  const toggleExpand = (id: string) =>
    setExpanded((prev) => (prev === id ? null : id));

  const statusVariant = (s: string) =>
    s === "open" ? "blue" : s === "closed" ? "green" : "yellow";

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Encounters</h1>
            <p className="text-sm text-slate-500 mt-1">
              Patient examination sessions
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={() => setShowForm((v) => !v)}
          >
            <Plus size={16} />
            New Encounter
          </button>
        </div>

        {/* New Encounter Form */}
        {showForm && (
          <div className="card p-6 mb-6">
            <h3 className="font-bold text-slate-900 mb-4">Create New Encounter</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Patient
                </label>
                <select
                  className="form-input"
                  value={selectedPatient}
                  onChange={(e) => setSelectedPatient(e.target.value)}
                  required
                >
                  <option value="">Select a patient…</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name} — {p.nik}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  Chief Complaint
                </label>
                <textarea
                  className="form-input resize-none"
                  rows={3}
                  placeholder="Describe the patient's main complaint…"
                  value={complaint}
                  onChange={(e) => setComplaint(e.target.value)}
                />
              </div>

              {/* Vital Signs */}
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">
                  Vital Signs (optional)
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {[
                    { key: "bp_systolic", label: "BP Systolic (mmHg)" },
                    { key: "bp_diastolic", label: "BP Diastolic (mmHg)" },
                    { key: "heart_rate", label: "Heart Rate (bpm)" },
                    { key: "temperature", label: "Temperature (°C)" },
                    { key: "spo2", label: "SpO₂ (%)" },
                    { key: "glucose", label: "Glucose (mg/dL)" },
                  ].map(({ key, label }) => (
                    <div key={key}>
                      <label className="block text-xs text-slate-500 mb-1">
                        {label}
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        className="form-input"
                        placeholder="—"
                        value={vitals[key as keyof typeof vitals]}
                        onChange={(e) =>
                          setVitals((v) => ({ ...v, [key]: e.target.value }))
                        }
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? "Creating…" : "Create Encounter"}
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowForm(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Encounters List */}
        <div className="card p-5">
          <SectionHeader
            title="All Encounters"
            subtitle={`${encounters.length} total`}
          />

          {loading ? (
            <div className="flex justify-center py-16">
              <LoadingSpinner />
            </div>
          ) : encounters.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No encounters yet"
              description="Create your first encounter using the button above."
            />
          ) : (
            <div className="space-y-2">
              {encounters.map((enc) => (
                <div key={enc.id} className="rounded-xl border border-slate-200 overflow-hidden">
                  {/* Row header */}
                  <button
                    className="w-full flex items-center gap-3 p-4 hover:bg-slate-50 text-left transition-colors"
                    onClick={() => toggleExpand(enc.id)}
                  >
                    <Activity size={16} className="text-slate-400 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800 line-clamp-1">
                        {enc.complaint_text ?? "No complaint recorded"}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {format(parseISO(enc.created_at), "PPPp")}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant={statusVariant(enc.status)}>
                        {enc.status}
                      </Badge>
                      {expanded === enc.id ? (
                        <ChevronUp size={16} className="text-slate-400" />
                      ) : (
                        <ChevronDown size={16} className="text-slate-400" />
                      )}
                    </div>
                  </button>

                  {/* Expanded details */}
                  {expanded === enc.id && (
                    <div className="border-t border-slate-100 p-4 bg-slate-50">
                      <div className="grid sm:grid-cols-2 gap-4">
                        {/* Vitals */}
                        <div>
                          <p className="text-xs font-semibold text-slate-500 uppercase mb-2">
                            Vital Signs
                          </p>
                          {enc.tabular_metrics_json ? (
                            <div className="grid grid-cols-2 gap-1.5">
                              {Object.entries(enc.tabular_metrics_json).map(
                                ([k, v]) => (
                                  <div
                                    key={k}
                                    className="bg-white rounded-lg px-3 py-2 border border-slate-200"
                                  >
                                    <p className="text-xs text-slate-400 capitalize">
                                      {k.replace(/_/g, " ")}
                                    </p>
                                    <p className="font-mono font-bold text-slate-800">
                                      {v}
                                    </p>
                                  </div>
                                )
                              )}
                            </div>
                          ) : (
                            <p className="text-sm text-slate-400">
                              No vitals recorded.
                            </p>
                          )}
                        </div>
                        {/* Meta */}
                        <div>
                          <p className="text-xs font-semibold text-slate-500 uppercase mb-2">
                            Details
                          </p>
                          <dl className="space-y-1.5 text-sm">
                            <div className="flex gap-2">
                              <dt className="text-slate-400 w-28 shrink-0">Encounter ID</dt>
                              <dd className="font-mono text-xs text-slate-600 break-all">
                                {enc.id}
                              </dd>
                            </div>
                            <div className="flex gap-2">
                              <dt className="text-slate-400 w-28 shrink-0">Image Key</dt>
                              <dd className="text-slate-600 text-xs">
                                {enc.medical_image_key ?? "—"}
                              </dd>
                            </div>
                          </dl>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
