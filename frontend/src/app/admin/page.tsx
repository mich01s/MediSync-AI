/**
 * MediSync AI — Admin Dashboard
 * Operational overview: stats, doctors list, queue monitor.
 */
"use client";

import { useEffect, useState } from "react";
import {
  Users,
  Stethoscope,
  ClipboardList,
  Activity,
} from "lucide-react";
import { adminApi } from "@/lib/api";
import { type AdminStats, type Doctor, type Queue } from "@/types";
import {
  StatCard,
  LoadingSpinner,
  SectionHeader,
  QueueStatusBadge,
} from "@/components/ui";
import { QueueBoard } from "@/components/queue-board/QueueBoard";
import { Sidebar } from "@/components/ui/Sidebar";

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([adminApi.getStats(), adminApi.listDoctors()])
      .then(([s, d]) => {
        setStats(s);
        setDoctors(d);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 p-8 max-w-6xl">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Hospital-wide operational overview
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-24">
            <LoadingSpinner size={36} />
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard
                title="Total Patients"
                value={stats?.total_patients ?? 0}
                icon={Users}
                iconColor="text-blue-600"
              />
              <StatCard
                title="Total Doctors"
                value={stats?.total_doctors ?? 0}
                icon={Stethoscope}
                iconColor="text-purple-600"
              />
              <StatCard
                title="Waiting"
                value={stats?.waiting_queues ?? 0}
                icon={ClipboardList}
                iconColor="text-yellow-600"
              />
              <StatCard
                title="In Service"
                value={stats?.serving_queues ?? 0}
                icon={Activity}
                iconColor="text-green-600"
              />
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Doctors Table */}
              <div className="card p-5">
                <SectionHeader
                  title="Doctors"
                  subtitle={`${doctors.length} registered`}
                />
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200">
                        {["Name / Email", "Specialization", "Room", "Status"].map(
                          (h) => (
                            <th
                              key={h}
                              className="text-left py-2 px-2 text-xs font-semibold text-slate-400 uppercase"
                            >
                              {h}
                            </th>
                          )
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {doctors.map((d) => (
                        <tr
                          key={d.id}
                          className="border-b border-slate-100 last:border-0 hover:bg-slate-50"
                        >
                          <td className="py-2.5 px-2 font-medium text-slate-800">
                            {d.user_id.slice(0, 8)}…
                          </td>
                          <td className="py-2.5 px-2 text-slate-600">
                            {d.specialization}
                          </td>
                          <td className="py-2.5 px-2 text-slate-500 font-mono text-xs">
                            {d.room_number ?? "—"}
                          </td>
                          <td className="py-2.5 px-2">
                            <span
                              className={`badge ${
                                d.status === "available"
                                  ? "badge-green"
                                  : d.status === "busy"
                                  ? "badge-yellow"
                                  : "badge-gray"
                              }`}
                            >
                              {d.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                      {doctors.length === 0 && (
                        <tr>
                          <td
                            colSpan={4}
                            className="py-6 text-center text-slate-400 text-sm"
                          >
                            No doctors registered yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Live Queue Board */}
              <div className="card p-5">
                <SectionHeader
                  title="Live Queue Monitor"
                  subtitle="Real-time • General Poli"
                />
                <QueueBoard poliName="General" compact />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
