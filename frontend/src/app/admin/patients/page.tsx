/**
 * MediSync AI — Admin: Patients Management Page
 * Paginated list of all registered patients.
 */
"use client";

import { useEffect, useState } from "react";
import { Users, ChevronLeft, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import { adminApi } from "@/lib/api";
import { type Patient } from "@/types";
import { Sidebar } from "@/components/ui/Sidebar";
import { LoadingSpinner, EmptyState, SectionHeader, Badge } from "@/components/ui";
import { format, parseISO } from "date-fns";

const PAGE_SIZE = 20;

export default function AdminPatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);

  useEffect(() => {
    setLoading(true);
    adminApi
      .listPatients(page * PAGE_SIZE, PAGE_SIZE)
      .then(setPatients)
      .catch(() => toast.error("Failed to load patients."))
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Patients</h1>
          <p className="text-sm text-slate-500 mt-1">
            All registered patient profiles
          </p>
        </div>

        <div className="card p-5">
          <SectionHeader
            title="Patient Registry"
            subtitle={`Page ${page + 1} · ${patients.length} records shown`}
          />

          {loading ? (
            <div className="flex justify-center py-16">
              <LoadingSpinner />
            </div>
          ) : patients.length === 0 ? (
            <EmptyState
              icon={Users}
              title="No patients found"
              description="Patient records will appear here once accounts are registered."
            />
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200">
                      {["Full Name", "NIK", "DOB", "Gender", "Phone"].map(
                        (h) => (
                          <th
                            key={h}
                            className="text-left py-3 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wider"
                          >
                            {h}
                          </th>
                        )
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {patients.map((p) => (
                      <tr
                        key={p.id}
                        className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors"
                      >
                        <td className="py-3 px-3 font-medium text-slate-800">
                          {p.full_name}
                        </td>
                        <td className="py-3 px-3 font-mono text-xs text-slate-600">
                          {p.nik}
                        </td>
                        <td className="py-3 px-3 text-slate-600">
                          {format(parseISO(p.dob), "dd MMM yyyy")}
                        </td>
                        <td className="py-3 px-3">
                          <Badge variant={p.gender === "male" ? "blue" : "purple"}>
                            {p.gender}
                          </Badge>
                        </td>
                        <td className="py-3 px-3 text-slate-600">
                          {p.phone ?? <span className="text-slate-300">—</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                <button
                  className="btn-secondary disabled:opacity-40"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft size={15} />
                  Previous
                </button>
                <span className="text-sm text-slate-500">Page {page + 1}</span>
                <button
                  className="btn-secondary disabled:opacity-40"
                  disabled={patients.length < PAGE_SIZE}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                  <ChevronRight size={15} />
                </button>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
