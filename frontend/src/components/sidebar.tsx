"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  Activity,
  Radio,
  FileText,
  Mail,
  LayoutGrid,
  Newspaper,
  ShieldCheck,
  SlidersHorizontal,
  Users as UsersIcon,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Logo } from "./logo";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; strokeWidth?: number }>;
  adminOnly?: boolean;
}

const OPERATIONS: NavItem[] = [
  { href: "/", label: "Incident Console", icon: Activity },
  { href: "/network", label: "Network", icon: Radio },
  { href: "/contracts", label: "Contracts", icon: FileText },
  { href: "/commercial", label: "Commercial", icon: Mail },
];

const STRATEGY: NavItem[] = [
  { href: "/portfolio", label: "Portfolio", icon: LayoutGrid },
  { href: "/market", label: "Market", icon: Newspaper },
];

const ADMIN: NavItem[] = [
  { href: "/audit", label: "Audit log", icon: ShieldCheck, adminOnly: true },
  { href: "/settings", label: "Settings", icon: SlidersHorizontal, adminOnly: true },
  { href: "/users", label: "Users", icon: UsersIcon, adminOnly: true },
];

function NavGroup({ title, items, pathname }: { title: string; items: NavItem[]; pathname: string }) {
  const { user } = useAuth();
  const visible = items.filter((item) => !item.adminOnly || user?.role === "admin");
  if (visible.length === 0) return null;

  return (
    <div className="flex flex-col gap-0.5">
      <div className="label px-2.5 pb-1.5">{title}</div>
      {visible.map((item) => {
        const active = pathname === item.href;
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] font-medium transition-colors",
              active
                ? "bg-accent-soft text-accent-strong"
                : "text-muted hover:bg-surface-raised hover:text-ink",
            )}
          >
            {active && (
              <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-accent" />
            )}
            <Icon
              size={16}
              strokeWidth={2}
            />
            {item.label}
          </Link>
        );
      })}
    </div>
  );
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="flex w-60 shrink-0 flex-col gap-6 border-r border-line bg-surface/60 px-3.5 py-5">
      <div className="flex items-center gap-2.5 px-1.5">
        <Logo size={30} />
        <div>
          <div className="wordmark text-[16px] text-ink">
            signos<span className="text-accent">.</span>
          </div>
          <div className="text-[11px] text-muted-2">Network operations</div>
        </div>
      </div>

      <NavGroup title="Operations" items={OPERATIONS} pathname={pathname} />
      <NavGroup title="Strategy" items={STRATEGY} pathname={pathname} />
      <NavGroup title="Admin" items={ADMIN} pathname={pathname} />
    </nav>
  );
}
