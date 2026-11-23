"""④ Predictive & What-If: trend forecast with dashed projection, scenario simulator."""
import numpy as np
import pandas as pd
import streamlit as st

import charts as C
import data as D
import theme as T

df, _, _ = D.get_clean()
HORIZON = 3

T.page_header("คาดการณ์ & จำลองสถานการณ์ (What-If)",
              "เส้นประคือการคาดการณ์ 3 ปีข้างหน้าจากสมการพื้นฐาน เป็นการคาดการณ์อย่างง่าย "
              "ใช้ประกอบการวางแผน ไม่ใช่ตัวเลขยืนยัน")

# ------------------------------------------------------------ forecasting --
with st.container(key="card-forecast"):
    a, b = st.columns([1.2, 1], vertical_alignment="bottom")
    series = a.segmented_control("ข้อมูลที่คาดการณ์", ["รวมทั้งหมด", *D.PROGRAM_ORDER[:3], "ตกค้าง"],
                                 default="รวมทั้งหมด", key="fc_series") or "รวมทั้งหมด"
    method = b.segmented_control("วิธีคาดการณ์", ["Linear Regression", "Moving Average 3 ปี"],
                                 default="Linear Regression", key="fc_method") or "Linear Regression"
    src = df if series == "รวมทั้งหมด" else df[df[D.PROGRAM] == series]
    y = D.yearly(src).sort_values(D.YEAR)
    yrs, vals = y[D.YEAR].to_numpy(), y[D.TOTAL].to_numpy(float)
    if len(yrs) < 3:
        st.info(f"ข้อมูล {series} มีเพียง {len(yrs)} ปี น้อยเกินไปสำหรับการคาดการณ์ที่น่าเชื่อถือ")
    if method.startswith("Linear"):
        fy, fv, fitted, band = D.linear_forecast(yrs, vals, HORIZON)
        r2 = 1 - np.sum((vals - fitted) ** 2) / np.sum((vals - vals.mean()) ** 2) if len(vals) > 2 else float("nan")
        sub = f"{series} · เส้นแนวโน้มเพิ่ม {np.polyfit(yrs, vals, 1)[0]:+,.0f} คน/ปี · R² = {r2:.2f}" \
            if len(yrs) >= 2 else series
    else:
        fy, fv, fitted = D.moving_avg_forecast(yrs, vals, 3, HORIZON)
        band = float(np.nanstd(vals[-3:], ddof=1)) if len(vals) >= 3 else 0.0
        sub = f"{series} · ค่าเฉลี่ยเคลื่อนที่ 3 ปีล่าสุดต่อเนื่องไปข้างหน้า"
    if len(fv):
        title = (f"ปี {int(fy[-1])} คาดว่าจะมี{'นักเรียน' if series == 'รวมทั้งหมด' else ' ' + series} "
                 f"≈ {fv[-1]:,.0f} คน ({D.pct_change(fv[-1], vals[-1]):+.1%} จากปี {int(yrs[-1])})")
    else:
        title = f"ข้อมูล {series}"
    C.show(C.forecast_chart(yrs, vals, fy, fv, band, method, title, sub, fitted=fitted), key="fc_chart")
    if len(fv):
        tbl = pd.DataFrame({"คาดการณ์ (คน)": fv, "ต่ำสุด ~95%": fv - 1.96 * band, "สูงสุด ~95%": fv + 1.96 * band},
                           index=[f"ปี {int(v)}" for v in fy]).T
        st.dataframe(tbl.style.format("{:,.0f}"), width="stretch", key="fc_table")

# --------------------------------------------------------------- what-if --
lv = D.yearly(df, D.LEVEL)
last_year = int(df[D.YEAR].max())
target = last_year + 1
base = {}
for level, s in lv.groupby(D.LEVEL):
    s = s.sort_values(D.YEAR)
    _, f, _, _ = D.linear_forecast(s[D.YEAR], s[D.TOTAL], 1)
    base[level] = max(0.0, float(f[0])) if len(f) else float(s[D.TOTAL].iloc[-1])
r = D.retention(df)
cur_ret = r[r["ขั้น"] == "ปวช.1→ปวช.2"].sort_values("ปีเริ่ม")["อัตรา"].iloc[-1]
last_lv = lv[lv[D.YEAR] == last_year].set_index(D.LEVEL)[D.TOTAL]
tot_hist = D.yearly(df).sort_values(D.YEAR)
cur_share = float(tot_hist[D.FEMALE].iloc[-1] / tot_hist[D.TOTAL].iloc[-1])


def _reset_sim():
    for k in [k for k in st.session_state if k.startswith("wi_")]:
        del st.session_state[k]


with st.container(key="card-whatif"):
    T.card_title(f"ตัวจำลองสถานการณ์ ปีการศึกษา {target}",
                 "ปรับแถบเลื่อนเพื่อดูผลต่อจำนวนนักเรียนรวมและนักเรียนหญิง เทียบกับฐานคาดการณ์ (Linear ราย ระดับชั้น)")
    s1, s2 = st.columns(2, gap="large")
    intake = s1.slider("เปลี่ยนจำนวนรับ ปวช.1 (%)", -20, 30, 0, 1, key="wi_intake", format="%d%%",
                       help="เช่น เพิ่มการประชาสัมพันธ์ หรือเปิดห้องเรียนเพิ่ม")
    ret = s1.slider("อัตราคงอยู่ ปวช.1 → ปวช.2 (%)", 60.0, 100.0, round(cur_ret * 100, 1), 0.1, key="wi_ret",
                    format="%.1f%%", help=f"ค่าเริ่มต้น = ค่าจริงรุ่นล่าสุด {cur_ret:.1%}")
    rem_cut = s2.slider("ลดนักเรียนตกค้าง (%)", 0, 60, 0, 5, key="wi_rem", format="%d%%",
                        help="เช่น ระบบติดตามนักเรียนกลุ่มเสี่ยงและสอนซ่อมเสริม")
    fem = s2.slider("สัดส่วนนักเรียนหญิงเป้าหมาย (%)", 10.0, 40.0, round(cur_share * 100, 1), 0.1, key="wi_fem",
                    format="%.1f%%", help=f"ค่าเริ่มต้น = ปีล่าสุด {cur_share:.1%}")
    st.button("คืนค่าเริ่มต้น", key="wi_reset", on_click=_reset_sim, icon=":material/restart_alt:")

    base_total = sum(base.values())
    d_intake = base.get("ปวช.1", 0) * intake / 100
    # Retention effect relative to today's rate, applied to the latest ปวช.1 cohort
    d_ret = float(last_lv.get("ปวช.1", 0)) * (ret / 100 - round(cur_ret * 100, 1) / 100)
    d_rem = -base.get("ตกค้าง", 0) * rem_cut / 100
    scen_total = base_total + d_intake + d_ret + d_rem
    base_female = base_total * cur_share
    scen_female = scen_total * fem / 100
    if abs(fem - round(cur_share * 100, 1)) < 1e-9:  # untouched slider = baseline share
        scen_female = scen_total * cur_share

    k1, k2, k3 = st.columns(3)
    k1.html(T.kpi_card(f"นักเรียนรวมปี {target} (จำลอง)", f"{scen_total:,.0f}",
                       T.delta_badge(D.pct_change(scen_total, base_total), suffix="เทียบฐานคาดการณ์"), unit="คน"))
    k2.html(T.kpi_card("นักเรียนหญิง (จำลอง)", f"{scen_female:,.0f}",
                       T.delta_badge(D.pct_change(scen_female, base_female), suffix="เทียบฐานคาดการณ์"), unit="คน"))
    k3.html(T.kpi_card(f"เทียบปีจริงล่าสุด {last_year}", f"{scen_total - tot_hist[D.TOTAL].iloc[-1]:+,.0f}",
                       T.delta_badge(D.pct_change(scen_total, tot_hist[D.TOTAL].iloc[-1]), suffix=f"จากปี {last_year}"),
                       unit="คน"))
    C.show(C.waterfall(base_total, [("รับ ปวช.1", d_intake), ("อัตราคงอยู่ ปวช.2", d_ret), ("ลดตกค้าง", d_rem)],
                       scen_total,
                       f"สถานการณ์นี้ทำให้นักเรียนปี {target} {'เพิ่มขึ้น' if scen_total >= base_total else 'ลดลง'} "
                       f"{abs(scen_total - base_total):,.0f} คน จากฐานคาดการณ์",
                       "ผลของแต่ละตัวแปร (คน) · เขียว = เพิ่ม · แดง = ลด"), key="wi_chart")
    st.caption("วิธีคำนวณ: ฐาน = ผลรวมการคาดการณ์ Linear ของแต่ละระดับชั้น · ผลของอัตราคงอยู่ = ปวช.1 ปีล่าสุด × (อัตราใหม่ − อัตราปัจจุบัน) · "
               "สัดส่วนหญิงใช้กับนักเรียนรวมทั้งหมด")

with st.container(key="card-retention"):
    rr = D.retention(df)
    worst = rr[rr["ปีเริ่ม"] == rr["ปีเริ่ม"].max()].sort_values("อัตรา").iloc[0] if not rr.empty else None
    title = (f"จุดที่นักเรียนหลุดมากที่สุดคือ {worst['ขั้น']} (ไปต่อ {worst['อัตรา']:.0%} รุ่น {worst['ปีเริ่ม']})"
             if worst is not None else "อัตราการไปต่อระดับถัดไป")
    C.show(C.retention_lines(rr, title, "สัดส่วนนักเรียนรุ่นเดียวกันที่ขึ้นระดับถัดไปในปีต่อมา แยกตามรุ่นปีที่เริ่ม"),
           key="fc_ret")
