"""Streamlit front-end. All displayed measures come from the live warehouse."""
from __future__ import annotations

import uuid
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

from bank.chat import ask
from bank.db import read_engine
from bank.query import METRICS

st.set_page_config(page_title="Bank Intelligence", page_icon="🏦", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] {font-family:'Noto Sans Thai', sans-serif;}
[data-testid="stAppViewContainer"] {background:#fff;color:#10244b;}
[data-testid="stSidebar"] {background:#f5f7f8;border-right:1px solid #e3e9ee;}
[data-testid="stSidebar"] h1 {font-size:1.35rem!important;color:#10244b;white-space:nowrap;}
[data-testid="stSidebar"] label {padding:.42rem .65rem;border-radius:8px;font-size:1rem;}
[data-testid="stSidebar"] label p, [data-testid="stSidebar"] .stCaption p {color:#10244b!important;}
[data-testid="stSidebar"] label:has(input:checked) {background:#deeeeb;color:#006653;font-weight:650;}
[data-testid="stSidebar"] label:has(input:checked) p {color:#006653!important;font-weight:650;}
[data-testid="stHeader"] {background:#fff!important;}
[data-testid="stToolbar"] {display:none;}
.block-container {max-width:1450px;padding-top:2.4rem;}
h1,h2,h3 {color:#10244b;letter-spacing:-.025em;}
h1 {font-size:2.45rem!important;}
.subtle {color:#526078;font-size:1.09rem;}
.kpi-label {color:#10244b;font-size:1.06rem;font-weight:650;margin-top:.6rem;}
.kpi-value {font-size:2.85rem;color:#087d65;font-weight:700;line-height:1.15;}
.kpi-unit {font-size:.95rem;color:#465673;margin-left:.3rem;}
.source-note {color:#637188;font-size:.84rem;border-top:1px solid #dde5e9;padding-top:1rem;margin-top:1.5rem;}
[data-testid="stDataFrame"] {border:1px solid #e5ebef;border-radius:8px;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def data():
    with read_engine().connect() as conn:
        overview = pd.read_sql(text("SELECT period, SUM(credits_million_baht) AS credits, SUM(deposits_million_baht) AS deposits, SUM(branches) AS branches FROM mart_province_month GROUP BY period ORDER BY period"), conn)
        provinces = pd.read_sql(text("SELECT * FROM mart_province_month ORDER BY period, province_code"), conn)
        runs = pd.read_sql(text("SELECT source, status, rows_loaded, detail, started_at FROM etl_run ORDER BY id DESC LIMIT 20"), conn)
        manifests = pd.read_sql(text("SELECT source, url, sha256, reference, fetched_at FROM source_manifest ORDER BY id DESC LIMIT 10"), conn)
    return overview, provinces, runs, manifests


try:
    overview, provinces, runs, manifests = data()
except Exception as exc:
    st.error(f"เชื่อมต่อคลังข้อมูลไม่ได้: {exc}")
    st.stop()

if overview.empty:
    st.warning("ยังไม่มีข้อมูล กรุณาเรียก python -m bank.etl all")
    st.stop()

with st.sidebar:
    st.markdown("# Bank Intelligence")
    page = st.radio("เมนู", ["ภาพรวมตลาด", "เปรียบเทียบจังหวัด", "ถามข้อมูล", "แหล่งข้อมูล"],
                    label_visibility="collapsed")
    st.caption("Thailand Regional Banking Intelligence")

latest = pd.Timestamp(overview["period"].max())
available = sorted(pd.to_datetime(provinces["period"].unique()), reverse=True)
thai_months = ["", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]


def month_label(value):
    d = pd.Timestamp(value)
    return f"{thai_months[d.month]} {d.year + 543}"


def footer(period):
    st.markdown(f'<div class="source-note">แหล่งข้อมูล: ธปท. • DOPA • สศช. • World Bank API | งวดข้อมูล {month_label(period)} | ยอดคงค้าง ไม่ใช่ยอดธุรกรรมรายเดือน</div>', unsafe_allow_html=True)


if page == "ภาพรวมตลาด":
    head, selector = st.columns([4, 1])
    with head:
        st.title("ภาพรวมตลาดธนาคาร")
        st.markdown('<div class="subtle">สินเชื่อ เงินฝาก และสาขารายจังหวัด</div>', unsafe_allow_html=True)
    with selector:
        selected = st.selectbox("งวดข้อมูล", available, format_func=month_label, index=0)
    snapshot = provinces[pd.to_datetime(provinces["period"]) == selected]
    credit = snapshot["credits_million_baht"].sum() / 1_000_000
    deposit = snapshot["deposits_million_baht"].sum() / 1_000_000
    branches = snapshot["branches"].sum()
    st.write("")
    a, b, c = st.columns(3)
    for col, label, value, unit in [(a, "สินเชื่อรวม", f"{credit:.2f}", "ล้านล้านบาท"),
                                    (b, "เงินฝากรวม", f"{deposit:.2f}", "ล้านล้านบาท"),
                                    (c, "จำนวนสาขา", f"{branches:,.0f}", "แห่ง")]:
        col.markdown(f'<div class="kpi-label">{label}</div><div><span class="kpi-value">{value}</span><span class="kpi-unit">{unit}</span></div>', unsafe_allow_html=True)
    policy_rate = snapshot["policy_rate_pct"].dropna()
    policy_event = snapshot["policy_event_date"].dropna()
    if not policy_rate.empty:
        st.caption(f"อัตราดอกเบี้ยนโยบาย ณ สิ้นงวด: {policy_rate.iloc[0]:.2f}% (มติล่าสุดที่มีผล {pd.Timestamp(policy_event.iloc[0]).date()}) — ใช้เป็นบริบท ไม่ใช่เหตุของการเปลี่ยนแปลงสินเชื่อ")
    st.divider()
    st.subheader("แนวโน้มสินเชื่อและเงินฝาก")
    history = overview[pd.to_datetime(overview["period"]) <= selected].copy()
    fig = go.Figure()
    for name, key, color in [("สินเชื่อรวม", "credits", "#0d3470"), ("เงินฝากรวม", "deposits", "#078467")]:
        fig.add_trace(go.Scatter(x=history["period"], y=history[key] / 1_000_000,
                                 mode="lines+markers", name=name, line=dict(color=color, width=3), marker=dict(size=5)))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=5),
                      yaxis_title="ล้านล้านบาท", xaxis_title="", plot_bgcolor="white",
                      paper_bgcolor="white", legend=dict(orientation="h", y=-0.22),
                      font=dict(family="Noto Sans Thai", color="#10244b"))
    fig.update_xaxes(showgrid=True, gridcolor="#e9eef1")
    low = min(history["credits"].min(), history["deposits"].min()) / 1_000_000
    high = max(history["credits"].max(), history["deposits"].max()) / 1_000_000
    fig.update_yaxes(showgrid=True, gridcolor="#e9eef1",
                     range=[max(0, low - 1.0), high + 1.0])
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("ตลาดรายจังหวัด")
    display = snapshot[["name_th", "deposits_million_baht", "credits_million_baht", "branches"]].copy()
    display.columns = ["จังหวัด", "เงินฝาก (ล้านบาท)", "สินเชื่อ (ล้านบาท)", "สาขา"]
    st.dataframe(display.sort_values("สินเชื่อ (ล้านบาท)", ascending=False), hide_index=True,
                 use_container_width=True, height=320)
    footer(selected)

elif page == "เปรียบเทียบจังหวัด":
    st.title("เปรียบเทียบจังหวัด")
    st.markdown('<div class="subtle">สำรวจตลาด เศรษฐกิจจังหวัด และคัดพื้นที่ศึกษาเพิ่มเติม</div>', unsafe_allow_html=True)
    selected = st.selectbox("งวดข้อมูล", available, format_func=month_label)
    snapshot = provinces[pd.to_datetime(provinces["period"]) == selected].copy()
    tabs = st.tabs(["จัดอันดับ", "GPP เทียบตลาด", "คัดพื้นที่ศึกษา"])
    with tabs[0]:
        metric = st.selectbox("ตัวชี้วัด", [k for k in METRICS if k != "policy_rate"],
                              format_func=lambda k: f"{METRICS[k][1]} ({METRICS[k][2]})")
        column = {"credits": "credits_million_baht", "deposits": "deposits_million_baht",
                  "branches": "branches", "credit_deposit_ratio": "credit_deposit_ratio_pct",
                  "branches_per_100k": "branches_per_100k", "deposits_per_person": "deposits_baht_per_person",
                  "gpp": "gpp_million_baht"}[metric]
        n = st.slider("จำนวนจังหวัด", 5, 30, 15)
        ascending = st.toggle("เรียงจากน้อยไปมาก")
        subset = snapshot.dropna(subset=[column]).sort_values(column, ascending=ascending).head(n)
        fig = px.bar(subset, x=column, y="name_th", orientation="h",
                     color_discrete_sequence=["#087d65"], labels={"name_th": "จังหวัด", column: METRICS[metric][2]})
        fig.update_layout(height=max(450, 29 * n), yaxis=dict(autorange="reversed"),
                          plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Noto Sans Thai"))
        st.plotly_chart(fig, use_container_width=True)
    with tabs[1]:
        paired = snapshot.dropna(subset=["gpp_million_baht", "credits_million_baht"]).copy()
        if st.checkbox("ซ่อนกรุงเทพมหานครเพื่อดูสเกลจังหวัดอื่น", value=True):
            paired = paired[paired["province_code"] != 10]
        if paired.empty:
            st.info("ยังไม่มีกำหนดเผยแพร่ GPP ที่ใช้กับงวดนี้ กรุณาเลือกงวดตั้งแต่มีนาคม 2569")
        else:
            fig = px.scatter(paired, x="gpp_million_baht", y="credits_million_baht",
                             size="branches", hover_name="name_th", color="credit_deposit_ratio_pct",
                             labels={"gpp_million_baht": "GPP 2024p (ล้านบาท)",
                                     "credits_million_baht": "สินเชื่อ ณ งวดที่เลือก (ล้านบาท)",
                                     "credit_deposit_ratio_pct": "สินเชื่อ/เงินฝาก (%)"},
                             color_continuous_scale="Teal")
            fig.update_layout(height=550, plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("GPP 2024p เป็นข้อมูลรายปีที่เผยแพร่ภายหลัง; การกระจายนี้เป็นความสัมพันธ์ ไม่พิสูจน์เหตุและผล และไม่ได้ควบคุมขนาดจังหวัด")
    with tabs[2]:
        st.write("เกณฑ์คัดกรองที่ปรับได้ — เป็น shortlist เพื่อวิจัยต่อ ไม่ใช่คำแนะนำเปิดสาขาหรือปล่อยสินเชื่อ")
        c1, c2, c3 = st.columns(3)
        min_gpp = c1.number_input("GPP ขั้นต่ำ (ล้านบาท)", min_value=0, value=100000, step=10000)
        max_density = c2.number_input("สาขาต่อประชากรแสนคน ไม่เกิน", min_value=0.0, value=15.0, step=1.0)
        min_credit = c3.number_input("สินเชื่อขั้นต่ำ (ล้านบาท)", min_value=0, value=50000, step=10000)
        exclude_bkk = st.checkbox("ไม่นับกรุงเทพมหานคร (สำนักงานใหญ่มีผลต่อยอด)", value=True)
        candidates = snapshot.dropna(subset=["gpp_million_baht", "branches_per_100k"])
        candidates = candidates[(candidates["gpp_million_baht"] >= min_gpp) &
                                (candidates["branches_per_100k"] <= max_density) &
                                (candidates["credits_million_baht"] >= min_credit)]
        if exclude_bkk:
            candidates = candidates[candidates["province_code"] != 10]
        st.metric("จังหวัดผ่านเกณฑ์", len(candidates))
        st.dataframe(candidates[["name_th", "gpp_million_baht", "credits_million_baht", "branches_per_100k"]]
                     .sort_values("gpp_million_baht", ascending=False), hide_index=True, use_container_width=True)
        st.caption("ใช้ประชากรตามทะเบียน ไม่ใช่จำนวนลูกค้า; ต้องตรวจการแข่งขัน รายได้จริง คุณภาพสินเชื่อ และต้นทุนพื้นที่ก่อนตัดสินใจ")
    if tabs:
        st.caption("สาขาต่อประชากรใช้ snapshot ประชากรเดือนธันวาคมปีอ้างอิงล่าสุด; GPP 2024p ไม่ใช่คุณภาพสินเชื่อ")
    footer(selected)

elif page == "ถามข้อมูล":
    st.title("ถามข้อมูลด้วยภาษาธรรมชาติ")
    st.markdown('<div class="subtle">ถามภาษาไทย แล้วดูตาราง กราฟ SQL และแหล่งที่มา</div>', unsafe_allow_html=True)
    st.info("รองรับเฉพาะตัวชี้วัดในคลังข้อมูลสาธารณะ ไม่มีข้อมูลลูกค้า รายธนาคาร หรือ NPL")
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    examples = ["สินเชื่อสูงสุด 5 จังหวัด", "แนวโน้มเงินฝากย้อนหลัง", "จังหวัดที่มีสาขาต่อประชากรสูงสุด 10 อันดับ"]
    chosen = st.selectbox("ตัวอย่างคำถาม", ["พิมพ์เอง"] + examples)
    question = st.text_input("คำถาม", value=chosen if chosen != "พิมพ์เอง" else "",
                             placeholder="เช่น แนวโน้มสินเชื่อจังหวัดเชียงใหม่")
    if st.button("ถามข้อมูล", type="primary"):
        result = ask(question, st.session_state.session_id)
        st.session_state.last_answer = result
    if "last_answer" in st.session_state:
        answer = st.session_state.last_answer
        st.caption(f"โหมด: {answer['mode']}")
        if answer["error"]:
            st.warning(answer["answer"])
        else:
            st.success(answer["answer"])
            payload = answer["result"]
            frame = pd.DataFrame(payload["rows"])
            if not frame.empty:
                st.dataframe(frame, hide_index=True, use_container_width=True)
                x = "period" if "period" in frame else "name_th"
                if x in frame and "value" in frame:
                    fig = (px.line(frame, x=x, y="value", markers=True,
                                   labels={"period": "เดือน", "value": f"{payload['metric_label']} ({payload['unit']})"})
                           if x == "period" else px.bar(frame, x=x, y="value",
                                   labels={"name_th": "จังหวัด", "value": f"{payload['metric_label']} ({payload['unit']})"}))
                    if x == "period":
                        fig.update_traces(line_color="#087d65")
                    else:
                        fig.update_traces(marker_color="#087d65")
                    fig.update_layout(height=370, plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Noto Sans Thai"))
                    st.plotly_chart(fig, use_container_width=True)
            with st.expander("SQL และที่มา"):
                st.code(payload["sql"], language="sql")
                st.json(payload["parameters"])
                st.write(" / ".join(payload["sources"]))
                st.caption(payload["caveat"])
    footer(latest)

else:
    st.title("แหล่งข้อมูลและการทำงาน")
    st.markdown("คลังข้อมูลนี้ใช้ข้อมูลสาธารณะจริงจาก ธปท., DOPA, สศช. และ World Bank API โดยไม่สร้างข้อมูลธนาคารจำลอง")
    st.subheader("ข้อมูลต้นทางล่าสุด")
    st.dataframe(manifests, use_container_width=True, hide_index=True)
    st.subheader("ประวัติ ETL")
    st.dataframe(runs, use_container_width=True, hide_index=True)
    st.markdown("**กติกา join:** รหัสจังหวัด DOPA 77 จังหวัด; ประชากรใช้ snapshot เดือนธันวาคมล่าสุดที่ไม่เกินงวดข้อมูล; GPP 2024p ใช้เฉพาะงวดหลังเผยแพร่ปี 2026; เงินเฟ้อ World Bank API เป็นบริบทระดับประเทศตามปีอ้างอิง; อัตราดอกเบี้ยนโยบายใช้มติ ธปท. ล่าสุดที่ไม่เกินสิ้นงวด; ค่าที่ไม่มีข้อมูลเป็น NULL ไม่ใช่ศูนย์")
    st.markdown("**ข้อจำกัด:** ที่ตั้งการบันทึกรายการไม่เท่ากับที่อยู่ผู้กู้; จำนวนสาขาต่อประชากรเป็น proxy ไม่ใช่การวัด financial inclusion โดยตรง")
    footer(latest)
