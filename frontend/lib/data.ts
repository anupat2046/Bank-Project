"use client";

import { useEffect, useState } from "react";

export type Row = Record<string, string | number | null>;
export type Meta = { periods: string[]; provinces: Row[]; rows: number };
export type Overview = { period: string; latest_period: string; totals: Row; changes: Row; trend: Row[]; provinces: Row[]; concentration: Row };
export type Question = { id: string; title: string; sources: string; fields: string; caveat: string; view: string };
export type QuestionResult = Question & { rows: Row[]; sql: string; period: string; sql_scope: string; parameters: Record<string, string> };
export type ChatReply = { answer: string; error: string | null; mode: string; routing_mode?: string; choices?: string[]; result: { rows: Row[]; metric_label: string; unit: string; metrics?: { key: string; label: string; unit: string; formula: string }[]; chart?: { kind: string; notice: string }; scope?: string; period?: string; eligible_count?: number; sources: string[]; caveat: string; sql: string; parameters: Record<string, unknown>; plan: { group_by: string; metric: string; provinces?: string[]; province?: string; exclude_bangkok?: boolean; include_yoy?: boolean; min_population?: number; min_credits?: number; min_gpp?: number; max_branch_density?: number; start_period?: string; end_period?: string } } | null };

export function useApi<T>(path: string | null) {
  const [state, setState] = useState<{ path: string | null; data: T | null; error: string | null }>({ path: null, data: null, error: null });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!path) return;
    const abort = new AbortController();
    setState({ path, data: null, error: null });
    fetch("/api/" + path, { signal: abort.signal, cache: "no-store" })
      .then(async response => {
        const data = await response.json();
        if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "ไม่สามารถโหลดข้อมูลได้");
        return data as T;
      })
      .then(data => setState({ path, data, error: null }))
      .catch(error => { if (!abort.signal.aborted) setState({ path, data: null, error: error.message }); });
    return () => abort.abort();
  }, [path, attempt]);
  return { data: state.path === path ? state.data : null, error: state.path === path ? state.error : null, retry: () => setAttempt(n => n + 1) };
}

export const months = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"];
const shortMonths = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."];
export function month(value: unknown, short = false) {
  if (!value) return "ไม่มีงวดข้อมูล";
  const parts = String(value).slice(0, 10).split("-").map(Number);
  return `${short ? shortMonths[parts[1]] : months[parts[1]]} ${parts[0] + 543}`;
}
export function number(value: unknown, decimals = 0) {
  if (value === null || value === undefined || value === "") return "ไม่มีข้อมูล";
  return new Intl.NumberFormat("th-TH", { maximumFractionDigits: decimals, minimumFractionDigits: decimals }).format(Number(value));
}
export const metricDefs: Record<string, { label: string; unit: string }> = {
  credits_million_baht: { label: "สินเชื่อ", unit: "ล้านบาท" }, deposits_million_baht: { label: "เงินฝาก", unit: "ล้านบาท" },
  credits: { label: "สินเชื่อรวม", unit: "ล้านบาท" }, deposits: { label: "เงินฝากรวม", unit: "ล้านบาท" },
  branches: { label: "สาขา", unit: "แห่ง" }, credit_deposit_ratio_pct: { label: "สินเชื่อ/เงินฝาก", unit: "%" },
  branches_per_100k: { label: "สาขาต่อประชากรแสนคน", unit: "แห่ง/แสนคน" }, deposits_baht_per_person: { label: "เงินฝากต่อผู้มีชื่อในทะเบียน", unit: "บาท/คน" },
  gpp_million_baht: { label: "GPP", unit: "ล้านบาท" }, population: { label: "ประชากรตามทะเบียน", unit: "คน" },
  population_reference_year: { label: "ปีประชากร (ค.ศ.)", unit: "" }, gpp_reference_year: { label: "ปี GPP (ค.ศ.)", unit: "" },
  positive_months: { label: "เดือนที่เติบโต YoY เป็นบวก", unit: "เดือน" }, observed_months: { label: "เดือนที่มีคู่ข้อมูล", unit: "เดือน" },
  average_yoy_pct: { label: "YoY เฉลี่ย", unit: "%" }, deposit_yoy_pct: { label: "เงินฝาก YoY", unit: "%" },
  credit_yoy_pct: { label: "สินเชื่อ YoY", unit: "%" }, growth_gap_pp: { label: "ส่วนต่างการเติบโต", unit: "จุดเปอร์เซ็นต์" },
  gpp_a_million: { label: "GPP จังหวัด A", unit: "ล้านบาท" }, gpp_b_million: { label: "GPP จังหวัด B", unit: "ล้านบาท" },
  credits_a_million: { label: "สินเชื่อจังหวัด A", unit: "ล้านบาท" }, credits_b_million: { label: "สินเชื่อจังหวัด B", unit: "ล้านบาท" },
  gpp_gap_pct: { label: "ส่วนต่าง GPP", unit: "%" }, credit_size_ratio: { label: "อัตราส่วนขนาดสินเชื่อ", unit: "เท่า" },
  policy_rate_pct: { label: "ดอกเบี้ยนโยบาย", unit: "%" }, branch_change: { label: "สาขาเปลี่ยนจากปีก่อน", unit: "แห่ง" },
  credits_million: { label: "สินเชื่อรวม", unit: "ล้านบาท" }, deposits_million: { label: "เงินฝากรวม", unit: "ล้านบาท" },
  national_credits_million: { label: "สินเชื่อทั่วประเทศ", unit: "ล้านบาท" }, bangkok_share_pct: { label: "สัดส่วนกรุงเทพฯ", unit: "%" }, top5_share_pct: { label: "สัดส่วน 5 จังหวัดแรก", unit: "%" },
};
export function label(key: string) {
  if (key === "name_th") return "จังหวัด";
  if (key === "province_a") return "จังหวัด A";
  if (key === "province_b") return "จังหวัด B";
  if (key === "name_en") return "จังหวัด (อังกฤษ)";
  if (key === "province_code") return "รหัสจังหวัด";
  if (key === "value") return "ค่าตัวชี้วัด";
  if (key === "period") return "งวดข้อมูล";
  const m = metricDefs[key];
  return m ? `${m.label}${m.unit ? ` (${m.unit})` : ""}` : key;
}

export function downloadCsv(rows: Row[], name: string, columns = Object.keys(rows[0] || {}), columnLabels: Record<string, string> = {}) {
  const escape = (value: unknown) => {
    let s = value == null ? "" : String(value);
    if (/^[=+@\t\r]/.test(s) || /^-[^\d]/.test(s)) s = "'" + s;
    return '"' + s.replaceAll('"', '""') + '"';
  };
  const csv = "\uFEFF" + [columns.map(k => columnLabels[k] || label(k)), ...rows.map(r => columns.map(k => r[k]))].map(r => r.map(escape).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a"); a.href = url; a.download = name + ".csv"; a.click(); URL.revokeObjectURL(url);
}
