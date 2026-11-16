/**
 * MediSync AI — Shared Navigation Sidebar
 * Renders role-specific navigation links.
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import {
  LayoutDashboard,
  Users,
  Stethoscope,
  ClipboardList,
  FileText,
  Activity,
  LogOut,
  Zap,
} from "lucide-react";
import { removeToken, getCurrentRole } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { type UserRole } from "@/types";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  admin: [
    { label: "Dashboard", href: "/admin", icon: LayoutDashboard },
    { label: "Doctors", href: "/admin/doctors", icon: Stethoscope },
    { label: "Patients", href: "/admin/patients", icon: Users },
    { label: "Queue Monitor", href: "/admin/queues", icon: ClipboardList },
  ],
  doctor: [
    { label: "Dashboard", href: "/doctor", icon: LayoutDashboard },
    { label: "Encounters", href: "/doctor/encounters", icon: Activity },
    { label: "AI Insights", href: "/doctor/ai", icon: Zap },
    { label: "Reports", href: "/doctor/reports", icon: FileText },
  ],
  patient: [
    { label: "My Queue", href: "/patient", icon: ClipboardList },
    { label: "My Health", href: "/patient/encounters", icon: Activity },
    { label: "My Reports", href: "/patient/reports", icon: FileText },
  ],
};

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const role = getCurrentRole() ?? "patient";
  const navItems = NAV_ITEMS[role] ?? NAV_ITEMS.patient;

  const handleLogout = () => {
    removeToken();
    router.push("/login");
  };

  return (
    <aside className="w-60 min-h-screen bg-slate-900 flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-700">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
            <Activity size={16} className="text-white" />
          </div>
          <span className="font-bold text-white text-base tracking-tight">
            MediSync AI
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-1 capitalize">{role} Portal</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== `/${role}` && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              <item.icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-slate-700">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm
                     font-medium text-slate-400 hover:bg-slate-800 hover:text-white
                     transition-colors"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
