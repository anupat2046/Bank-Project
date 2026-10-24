"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowDownUp, Download, Search } from "lucide-react";
import { Row, downloadCsv, label, month, number } from "@/lib/data";

export function TableScroll({ children, name = "ตารางข้อมูล" }: { children: React.ReactNode; name?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [overflow, setOverflow] = useState(false);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const update = () => setOverflow(node.scrollWidth > node.clientWidth + 1);
    const observer = new ResizeObserver(update); observer.observe(node);
    const mutation = new MutationObserver(update); mutation.observe(node, { childList: true, subtree: true, characterData: true });
    update(); return () => { observer.disconnect(); mutation.disconnect(); };
  }, []);
  return <>{overflow && <p className="scroll-hint">เลื่อนตารางซ้าย–ขวาเพื่อดูข้อมูลเพิ่มเติม</p>}<div ref={ref} className="table-scroll" tabIndex={0} role="region" aria-label={name}>{children}</div></>;
}

export function ComparisonTable({ rows, columns, filename }: { rows: Row[]; columns: string[]; filename: string }) {
  return <div className="data-table"><div className="table-toolbar"><p className="muted">เปรียบเทียบ {rows.length} จังหวัด · ปีอ้างอิงระบุเป็น ค.ศ.</p><button className="button subtle" onClick={() => downloadCsv(rows, filename, ["name_th", ...columns])}><Download size={16} />ดาวน์โหลด CSV</button></div><TableScroll name="ตารางเปรียบเทียบจังหวัด"><table className="comparison-table"><thead><tr><th scope="col">ตัวชี้วัด</th>{rows.map(row => <th scope="col" key={String(row.province_code)}>{row.name_th}</th>)}</tr></thead><tbody>{columns.map(key => <tr key={key}><th scope="row">{label(key)}</th>{rows.map(row => <td key={String(row.province_code)} className="numeric">{row[key] == null ? "ไม่มีข้อมูล" : /year$/.test(key) ? String(row[key]) : number(row[key], /pct|ratio|per_100k|person|yoy/.test(key) ? 2 : 0)}</td>)}</tr>)}</tbody></table></TableScroll></div>;
}

export function DataTable({ rows, columns, filename, search = false, initialSort, onProvince, selected = [], onSelect, columnLabels = {} }: {
  rows: Row[]; columns?: string[]; filename: string; search?: boolean; initialSort?: string;
  onProvince?: (row: Row) => void; selected?: number[]; onSelect?: (row: Row) => void;
  columnLabels?: Record<string, string>;
}) {
  const keys = columns || Object.keys(rows[0] || {});
  // Reference years are identifiers, not quantities with thousands separators.
  const displayRows = rows.map(row => Object.fromEntries(Object.entries(row).map(([key, value]) => [key, /year$/.test(key) && typeof value === "number" ? String(value) : value])) as Row);
  const [term, setTerm] = useState("");
  const [sort, setSort] = useState({ key: initialSort || "", asc: false });
  const filtered = useMemo(() => {
    const data = displayRows.filter(r => !term || keys.some(k => typeof r[k] === "string" && String(r[k]).toLowerCase().includes(term.toLowerCase())));
    if (sort.key) data.sort((a, b) => {
      const av = a[sort.key], bv = b[sort.key];
      if (av == null) return bv == null ? 0 : 1; if (bv == null) return -1;
      const cmp = typeof av === "number" && typeof bv === "number" ? av - bv : String(av).localeCompare(String(bv), "th");
      return sort.asc ? cmp : -cmp;
    });
    return data;
  }, [displayRows, term, keys, sort]);
  return <div className="data-table">
    <div className="table-toolbar">{search ? <label className="search"><Search size={16} /><input aria-label="ค้นหาจังหวัด" placeholder="ค้นหาจังหวัด…" value={term} onChange={e => setTerm(e.target.value)} /></label> : <span className="muted">{number(filtered.length)} แถวผลลัพธ์</span>}<button className="button subtle" disabled={!filtered.length} onClick={() => downloadCsv(filtered, filename, keys, columnLabels)}><Download size={16} />ดาวน์โหลด CSV</button></div>
    {!filtered.length ? <div className="empty">ไม่มีข้อมูลตรงเงื่อนไข ลองเปลี่ยนงวดหรือปรับตัวกรอง</div> : <TableScroll><table><thead><tr>{onSelect && <th className="check-col">เลือก</th>}{keys.map(k => <th key={k} aria-sort={sort.key === k ? sort.asc ? "ascending" : "descending" : "none"}><button onClick={() => setSort({ key: k, asc: sort.key === k ? !sort.asc : true })}>{columnLabels[k] || label(k)}<ArrowDownUp size={12} /></button></th>)}</tr></thead><tbody>{filtered.map((row, i) => <tr key={String(row.province_code ?? row.name_th ?? row.period ?? i)}>{onSelect && <td className="check-col"><label className="table-checkbox"><input type="checkbox" aria-label={`เลือก ${row.name_th}`} checked={selected.includes(Number(row.province_code))} onChange={() => onSelect(row)} /></label></td>}{keys.map(k => <td key={k} className={typeof row[k] === "number" ? "numeric" : ""}>{k === "name_th" && onProvince ? <button className="text-button" onClick={() => onProvince(row)}>{row[k]}</button> : k === "period" ? month(row[k]) : typeof row[k] === "number" ? number(row[k], k === "value" || /pct|ratio|per_100k|person|yoy|gap/.test(k) ? 2 : 0) : row[k] ?? <span className="muted">ไม่มีข้อมูล</span>}</td>)}</tr>)}</tbody></table></TableScroll>}
    {search && <div className="table-count">แสดง {number(filtered.length)} จาก {number(rows.length)} จังหวัด</div>}
  </div>;
}
