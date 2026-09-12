"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Chat" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function TopNav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border">
      <div className="mx-auto max-w-5xl flex items-center justify-between px-6 h-14">
        <div className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-teal" />
          <span className="text-sm tracking-tight text-text-primary">router</span>
        </div>
        <nav className="flex items-center gap-6">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm transition-colors ${
                  active ? "text-teal" : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
