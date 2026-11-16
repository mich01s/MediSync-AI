/**
 * MediSync AI — Admin: Doctors Management Page
 * Lists all doctors with status control and registration form.
 */
"use client";

import { useEffect, useState } from "react";
import { Stethoscope, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";
import { adminApi } from "@/lib/api";
import { type Doctor } from "@/types";
import { Sidebar } from "@/components/ui/Sidebar";
import { LoadingSpinner, EmptyState, Badge, SectionHeader } from "@/components/ui";

const STATUS_VARIANT: Record<string, "green" | "yellow" | "gray"> = {
  available: "green",
  busy: "yellow",
  off: "gray",
};

export default function AdminDoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDoctors = () => {
    setLoading(true);
    adminApi
      .listDoctors()
      .then(setDoctors)
      .catch(() => toast.error("Failed to load doctors."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDoctors();
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Doctors</h1>
            <p className="text-sm text-slate-500 mt-1">
              All registered doctors and their availability
            </p>
          </div>
          <button className="btn-secondary" onClick={fetchDoctors}>
            <RefreshCw size={15} />
            Refresh
          </button>
        </div>

        <div className="card p-5">
          <SectionHeader
            title="Registered Doctors"
            subtitle={`${doctors.length} total`}
          />

          {loading ? (
            <div className="flex justify-center py-16">
              <LoadingSpinner />
            </div>
          ) : doctors.length === 0 ? (
            <EmptyState
              icon={Stethoscope}
              title="No doctors registered"
              description="Add a doctor account from the registration form below."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    {[
                      "Doctor ID",
                      "Specialization",
                      "License No.",
                      "Room",
                      "Status",
                    ].map((h) => (
                      <th
                        key={h}
                        className="text-left py-3 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {doctors.map((doc) => (
                    <tr
                      key={doc.id}
                      className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors"
                    >
                      <td className="py-3 px-3 font-mono text-xs text-slate-500">
                        {doc.id.slice(0, 12)}…
                      </td>
                      <td className="py-3 px-3 font-medium text-slate-800">
                        {doc.specialization}
                      </td>
                      <td className="py-3 px-3 font-mono text-xs text-slate-600">
                        {doc.license_number}
                      </td>
                      <td className="py-3 px-3 text-slate-600">
                        {doc.room_number ?? (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant={STATUS_VARIANT[doc.status] ?? "gray"}>
                          {doc.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Info callout */}
        <div className="mt-6 p-4 rounded-xl bg-blue-50 border border-blue-100 text-sm text-blue-700">
          <strong>Tip:</strong> To register a new doctor, use the{" "}
          <code className="font-mono bg-blue-100 px-1 rounded">
            POST /api/admin/doctors
          </code>{" "}
          endpoint via the API (accessible at{" "}
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="underline"
          >
            localhost:8000/docs
          </a>
          ).
        </div>
      </main>
    </div>
  );
}
