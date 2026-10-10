"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { createContext, useContext, useEffect, useRef, useState } from "react";
import { BarChart3, MapPin, MessageSquare, ListChecks, Database, Menu, X, ArrowUpRight } from "lucide-react";
import { Meta, month, useApi } from "@/lib/data";

const nav = [
  { path: "/", title: "ภาพรวมตลาด", icon: BarChart3 },
  { path: "/provinces", title: "วิเคราะห์จังหวัด", icon: MapPin },
  { path: "/assistant", title: "ผู้ช่วยวิเคราะห์", icon: MessageSquare },
  { path: "/questions", title: "คำถามธุรกิจ", icon: ListChecks },
  { path: "/sources", title: "แหล่งข้อมูล", icon: Database },
];
type Context = { meta: Meta | null; period: string; href: (path: string, params?: Record<string, string>) => string; setParams: (params: Record<string, string | null>) => void };
const Workspace = createContext<Context | null>(null);
export function useWorkspace() { const c = useContext(Workspace); if (!c) throw new Error("Missing workspace"); return c; }

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname(), router = useRouter(), params = useSearchParams();
  const { data: meta, error, retry } = useApi<Meta>("metadata");
  const period = params.get("period") || meta?.periods[0] || "";
  const [open, setOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const closeMenu = () => { setOpen(false); menuButton.current?.focus(); };
  useEffect(() => { setOpen(false); }, [pathname]);
  useEffect(() => {
    if (!open) return;
    const elements = () => Array.from(document.querySelectorAll<HTMLButtonElement | HTMLAnchorElement>(".sidebar button, .sidebar a"));
    elements()[0]?.focus();
    const keys = (e: KeyboardEvent) => {
      if (e.key === "Escape") { setOpen(false); menuButton.current?.focus(); }
      if (e.key === "Tab") {
        const items = elements(), first = items[0], last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
        if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
      }
    };
    window.addEventListener("keydown", keys); return () => window.removeEventListener("keydown", keys);
  }, [open]);
  const setParams = (values: Record<string, string | null>) => {
    const next = new URLSearchParams(params.toString());
    Object.entries(values).forEach(([key, value]) => value === null ? next.delete(key) : next.set(key, value));
    router.replace(`${pathname}?${next}`, { scroll: false });
  };
  const href = (path: string, values: Record<string, string> = {}) => {
    const next = new URLSearchParams();
    if (period) next.set("period", period);
    const comparison = params.get("compare"); if (comparison) next.set("compare", comparison);
    Object.entries(values).forEach(([k, v]) => next.set(k, v));
    return `${path}?${next}`;
  };
  return <Workspace.Provider value={{ meta, period, href, setParams }}>
    <a href="#main" className="skip-link">ข้ามไปเนื้อหา</a>
    {open && <button className="nav-backdrop" aria-label="ปิดเมนูด้านข้าง" onClick={closeMenu} />}
    <aside id="app-navigation" className={`sidebar ${open ? "is-open" : ""}`} role={open ? "dialog" : undefined} aria-modal={open ? true : undefined} aria-label="เมนูนำทาง">
      <div className="brand">Bank Intelligence<button className="mobile-only icon-button" aria-label="ปิดเมนู" onClick={closeMenu}><X size={20} /></button></div>
      <nav aria-label="เมนูหลัก">{nav.map(({ path, title, icon: Icon }) => <Link key={path} href={href(path)} className={`nav-link ${pathname === path ? "active" : ""}`} aria-current={pathname === path ? "page" : undefined}><Icon size={19} strokeWidth={1.8} />{title}</Link>)}</nav>
      <div className="sidebar-bottom"><p>Thailand Regional<br />Banking Intelligence</p><Link href={href("/sources")}>ตรวจที่มาของข้อมูล <ArrowUpRight size={14} /></Link></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="topbar-left"><button ref={menuButton} className="mobile-only icon-button" aria-label="เปิดเมนู" aria-controls="app-navigation" aria-expanded={open} onClick={() => setOpen(true)}><Menu size={22} /></button><span>{nav.find(n => n.path === pathname)?.title || "Bank Intelligence"}</span></div>
        {pathname !== "/assistant" && pathname !== "/sources" ? <label className="period-select"><span>งวดข้อมูล</span><select aria-label="งวดข้อมูล" value={period} disabled={!meta?.periods.length} onChange={e => setParams({ period: e.target.value })}>{meta?.periods.map(p => <option key={p} value={p}>{month(p)}</option>)}</select></label> : <span className="header-note">ข้อมูลสาธารณะ · ไม่มีข้อมูลลูกค้า</span>}
      </header>
      <main id="main" tabIndex={-1}>{error ? <div className="state error" role="alert"><h2>เชื่อมต่อคลังข้อมูลไม่ได้</h2><p>{error}</p><button onClick={retry}>ลองใหม่</button></div> : !meta ? <div className="state loading" role="status">กำลังเตรียมพื้นที่วิเคราะห์…</div> : !meta.periods.length ? <div className="state"><h2>ยังไม่มีข้อมูลในคลัง</h2><p>กรุณานำเข้าข้อมูลด้วย ETL ก่อนเริ่มวิเคราะห์</p></div> : children}</main>
    </div>
  </Workspace.Provider>;
}

export function PageHeading({ title, description, children }: { title: string; description: string; children?: React.ReactNode }) {
  return <div className="page-heading"><div><h1>{title}</h1><p>{description}</p></div>{children}</div>;
}
export function DataState({ error, retry }: { error: string | null; retry: () => void }) {
  return <div className={`state ${error ? "error" : "loading"}`} role={error ? "alert" : "status"}>{error ? <><h2>โหลดข้อมูลไม่ได้</h2><p>{error}</p><button onClick={retry}>ลองใหม่</button></> : "กำลังโหลดข้อมูลจริงจากคลัง…"}</div>;
}
export function Footer({ period }: { period?: string }) {
  return <footer className="data-footer"><span>ที่มา: ธปท. · DOPA · สศช. · World Bank</span><span>{period ? `${month(period)} · ` : ""}ยอดคงค้าง ไม่ใช่ยอดธุรกรรมรายเดือน</span></footer>;
}
