"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/app/demo", label: "Demo" },
  { href: "/app/dashboard", label: "Dashboard" },
  { href: "/app/upload", label: "Upload" },
  { href: "/app/cameras", label: "Cameras" },
  { href: "/app/library", label: "Library" },
  { href: "/app/events", label: "Events" },
  { href: "/app/alerts", label: "Alerts" },
  { href: "/app/summaries", label: "Summaries" },
];

export default function TopNav() {
  const pathname = usePathname();

  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-8 py-4 flex flex-col gap-3 sm:flex-row sm:justify-between sm:items-center">
        <Link href="/app/dashboard" className="text-2xl font-bold text-gray-900">
          Safety Sentinel
        </Link>
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/app/dashboard" && pathname.startsWith(`${item.href}/`));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  isActive
                    ? "font-semibold text-blue-700"
                    : "text-gray-600 hover:text-gray-900"
                }
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
