"use client";

import { useEffect, useRef, useState } from "react";
import { ResponsiveContainer, CartesianGrid, XAxis, YAxis, Tooltip, Line, LineChart, ScatterChart, Scatter, Cell } from "recharts";
import { Row, month, number } from "@/lib/data";

export const colors = ["#102f60", "#087d65", "#aa6b24", "#7654a1"];
function Ready({ children }: { children: React.ReactNode }) {
  const anchor = useRef<HTMLSpanElement>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const parent = anchor.current?.parentElement;
    if (!parent) return;
    const observer = new ResizeObserver(() => setReady(parent.clientWidth > 0 && parent.clientHeight > 0));
    observer.observe(parent);
    return () => observer.disconnect();
  }, []);
  return <><span ref={anchor} hidden />{ready ? children : <div className="chart-loading" />}</>;
}
const axis = { fontSize: 12, fill: "#60718b" };
const compact = (v: number) => new Intl.NumberFormat("th-TH", { notation: "compact", maximumFractionDigits: 1 }).format(v);
export function TrendChart({ rows, series, unit, height = 300, policy = false }: { rows: Row[]; series: { key: string; name: string; color?: string }[]; unit: string; height?: number; policy?: boolean }) {
  const [hidden, setHidden] = useState<string[]>([]);
  const plotHeight = Math.max(policy ? 100 : 180, height - 50);
  return <div className="chart-block"><p className="chart-unit">หน่วย: {unit}</p><div className="chart" style={{ minHeight: plotHeight + 50 }} aria-label={`กราฟแนวโน้ม ${series.map(s => s.name).join(" และ ")} หน่วย ${unit}`} role="group"><Ready><div style={{ height: plotHeight }}><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{ top: 15, right: 20, bottom: 0, left: 5 }} accessibilityLayer>
    <CartesianGrid stroke="#e8edf2" vertical={false} /><XAxis dataKey="period" tickFormatter={p => month(p, true)} tick={axis} minTickGap={40} axisLine={false} tickLine={false} />
    <YAxis tick={axis} tickFormatter={compact} axisLine={false} tickLine={false} width={65} domain={policy ? [0, "auto"] : ["auto", "auto"]} />
    <Tooltip labelFormatter={p => month(p)} formatter={(v, name) => [number(v, 2) + " " + unit, name]} contentStyle={{ border: "1px solid #e2e8ef", borderRadius: 8 }} />
    {series.map((s, i) => <Line key={s.key} name={s.name} dataKey={s.key} type={policy ? "stepAfter" : "linear"} stroke={s.color || colors[i % colors.length]} strokeDasharray={i ? `${8 - i} ${3 + i}` : undefined} strokeWidth={2.5} dot={rows.length === 1 ? { r: 3 } : false} activeDot={{ r: 4 }} connectNulls={false} hide={hidden.includes(s.key)} isAnimationActive={false} />)}
  </LineChart></ResponsiveContainer></div></Ready><div className="chart-legend">{series.map((s, i) => <button key={s.key} className={`legend-toggle ${hidden.includes(s.key) ? "is-hidden" : ""}`} aria-pressed={!hidden.includes(s.key)} aria-label={`${hidden.includes(s.key) ? "แสดง" : "ซ่อน"} ${s.name}`} onClick={() => setHidden(h => h.includes(s.key) ? h.filter(k => k !== s.key) : [...h, s.key])}><span aria-hidden="true" style={{ borderTop: `3px ${i ? "dashed" : "solid"} ${s.color || colors[i % colors.length]}` }} />{s.name}{hidden.includes(s.key) && " (ซ่อนอยู่)"}</button>)}</div></div></div>;
}
export function Bars({ rows, valueKey, nameKey = "name_th", unit }: { rows: Row[]; valueKey: string; nameKey?: string; unit: string }) {
  const values = rows.flatMap(row => row[valueKey] == null ? [] : [Number(row[valueKey])]).filter(Number.isFinite);
  const low = Math.min(0, ...values), high = Math.max(0, ...values), span = high - low || 1;
  return <div className="bar-chart"><p className="chart-unit">หน่วย: {unit || "ค่าตัวชี้วัด"}</p><ul className="bar-list" aria-label={`กราฟเปรียบเทียบค่า หน่วย ${unit}`}>
    {rows.map((row, index) => { const value = row[valueKey] == null ? null : Number(row[valueKey]); return <li key={index}>
      <div className="bar-label"><span>{row[nameKey]}</span><strong className="numeric">{number(value, value != null && Number.isInteger(value) ? 0 : 2)}</strong></div>
      <div className="bar-track" aria-hidden="true"><span className="bar-zero" style={{ left: `${-low / span * 100}%` }} />{value != null && <span className="bar-fill" style={{ left: `${(Math.min(0, value) - low) / span * 100}%`, width: `${Math.abs(value) / span * 100}%` }} />}</div>
    </li>; })}
  </ul></div>;
}
export function GppScatter({ rows, onProvince, selected = [] }: { rows: Row[]; onProvince?: (row: Row) => void; selected?: number[] }) {
  return <div className="chart" style={{ height: 320 }} role="group" aria-label="กราฟ GPP เทียบสินเชื่อ หน่วยล้านบาท"><Ready><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{ top: 15, left: 10, right: 25, bottom: 25 }} accessibilityLayer><CartesianGrid stroke="#e8edf2" /><XAxis type="number" dataKey="gpp_million_baht" name="GPP" tick={axis} tickFormatter={compact} label={{ value: "GPP (ล้านบาท)", position: "bottom", fill: "#60718b", fontSize: 12 }} /><YAxis type="number" dataKey="credits_million_baht" name="สินเชื่อ" tick={axis} tickFormatter={compact} width={70} />
    <Tooltip content={({ active, payload }) => { if (!active || !payload?.length) return null; const r = payload[0].payload as Row; return <div className="chart-tooltip"><strong>{r.name_th}</strong><div>GPP {number(r.gpp_million_baht)} ล้านบาท · ปี {r.gpp_reference_year}</div><div>สินเชื่อ {number(r.credits_million_baht)} ล้านบาท</div><div>งวด {month(r.period)}</div></div>; }} />
    <Scatter data={rows} fill="#087d65" isAnimationActive={false} onClick={p => onProvince?.(p as unknown as Row)}>{rows.map((r, i) => <Cell key={i} fill={selected.length && !selected.includes(Number(r.province_code)) ? "#62718a" : "#087d65"} stroke={selected.includes(Number(r.province_code)) ? "#10244b" : undefined} strokeWidth={3} cursor={onProvince ? "pointer" : undefined} />)}</Scatter>
  </ScatterChart></ResponsiveContainer></Ready></div>;
}
