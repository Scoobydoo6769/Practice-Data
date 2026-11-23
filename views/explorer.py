"""③ Deep-Dive Explorer: multi-dimension filters, charts, smart table, CSV/XLSX export."""
import io

import pandas as pd
import streamlit as st

import charts as C
import data as D
import theme as T

df_all, _, _ = D.get_clean()
years = sorted(df_all[D.YEAR].unique())
levels = [v for v in D.LEVEL_ORDER if v in set(df_all[D.LEVEL])]
depts = sorted(df_all[D.DEPT].unique())
tmin, tmax = int(df_all[D.TOTAL].min()), int(df_all[D.TOTAL].max())


def _reset():
    for k in [k for k in st.session_state if k.startswith("f_")]:
        del st.session_state[k]


with st.sidebar:
    st.subheader("ตัวกรอง")
    y0, y1 = st.select_slider("ช่วงปีการศึกษา", options=years, value=(years[0], years[-1]), key="f_years")
    sel_lv = st.multiselect("ระดับชั้น", levels, key="f_levels", placeholder="ทุกระดับชั้น")
    sel_dp = st.multiselect("แผนกวิชา", depts, key="f_depts", placeholder="ทุกแผนก")
    lo, hi = st.slider("จำนวนนักเรียนต่อแถว (คน)", tmin, tmax, (tmin, tmax), key="f_total")
    st.button("ล้างตัวกรองทั้งหมด", key="reset_filters", on_click=_reset, icon=":material/restart_alt:",
              width="stretch")

df = df_all[df_all[D.YEAR].between(y0, y1) & df_all[D.TOTAL].between(lo, hi)]
if sel_lv and len(sel_lv) < len(levels):
    df = df[df[D.LEVEL].isin(sel_lv)]
if sel_dp and len(sel_dp) < len(depts):
    df = df[df[D.DEPT].isin(sel_dp)]

T.page_header("สำรวจข้อมูลเชิงลึก",
              "กรองหลายมิติจากแถบซ้าย กราฟ ตัวเลข และตารางในหน้านี้จะอัปเดตทันที")

if df.empty:
    st.info("ไม่มีข้อมูลตามตัวกรองที่เลือก ลองเพิ่มระดับชั้น/แผนก หรือกด 'ล้างตัวกรองทั้งหมด'")
    st.stop()

tot = int(df[D.TOTAL].sum())
fem = int(df[D.FEMALE].sum())
nyears = df[D.YEAR].nunique()
st.html("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.75rem'>"
        + T.kpi_card("นักเรียนรวม (ตามตัวกรอง)", f"{tot:,}", unit="คน")
        + T.kpi_card("เฉลี่ยต่อปีการศึกษา", f"{tot / nyears:,.0f}", unit="คน")
        + T.kpi_card("นักเรียนหญิง", f"{fem:,}", f"<span class='delta'>{fem / tot:.1%} ของทั้งหมด</span>"
                     if tot else "", unit="คน")
        + T.kpi_card("จำนวนแถวข้อมูล", f"{len(df):,}", f"<span class='delta'>จาก {len(df_all):,} แถว</span>")
        + "</div>")

c1, c2 = st.columns(2, gap="medium")
with c1:
    with st.container(key="card-stack"):
        y = D.yearly(df, D.PROGRAM)
        lastyr = y[y[D.YEAR] == y[D.YEAR].max()]
        lead = lastyr.loc[lastyr[D.TOTAL].idxmax(), D.PROGRAM] if not lastyr.empty else "-"
        C.show(C.level_stack(df, f"{lead} เป็นกลุ่มใหญ่ที่สุดทุกปี",
                             "จำนวนนักเรียนรายปี แยกตามหลักสูตร (คน)"), key="ex_stack")
with c2:
    with st.container(key="card-scatter"):
        corr = df[D.MALE].corr(df[D.FEMALE]) if len(df) > 2 else float("nan")
        title = (f"ชายและหญิงเพิ่ม-ลดไปด้วยกัน (r = {corr:.2f})" if pd.notna(corr)
                 else "ความสัมพันธ์ของจำนวนนักเรียนชายและหญิง")
        C.show(C.gender_scatter(df, title, "แต่ละจุด = 1 แผนก × 1 ระดับชั้น × 1 ปี"), key="ex_scatter")

with st.container(key="card-heat"):
    p = df.pivot_table(index=D.DEPT, columns=D.YEAR, values=D.TOTAL, aggfunc="sum")
    if p.shape[1] >= 2:
        g = (p.iloc[:, -1] / p.iloc[:, 0] - 1).sort_values()
        title = f"{g.index[-1]} โตเร็วที่สุด {g.iloc[-1]:+.1%} · {g.index[0]} โตช้าที่สุด {g.iloc[0]:+.1%}"
    else:
        title = "จำนวนนักเรียนรายแผนก"
    C.show(C.heatmap(df, title, f"จำนวนนักเรียนรายแผนก × ปีการศึกษา {y0}–{y1} (คน) · สีเข้ม = มาก"),
           key="ex_heat")

# ------------------------------------------------------------- smart table --
with st.container(key="card-table"):
    T.card_title("ตารางข้อมูลที่คลีนแล้ว", "ค้นหา · เรียงลำดับ (คลิกหัวคอลัมน์) · แบ่งหน้า · แถบสีแดงอ่อน = ต่ำกว่าเกณฑ์")
    s1, s2, s3 = st.columns([2, 1, 1], vertical_alignment="bottom")
    q = s1.text_input("ค้นหา", placeholder="พิมพ์ชื่อแผนก ระดับชั้น หรือปี เช่น ช่างยนต์ 2569", key="f_search")
    threshold = s2.number_input("เกณฑ์ต่ำ (คนต่อแถว)", 0, tmax, 30, step=5, key="f_threshold")
    page_size = s3.selectbox("แถวต่อหน้า", [10, 25, 50, 100], index=1, key="f_page_size")

    view = df.drop(columns="ไฟล์ต้นทาง")
    if q.strip():
        hay = view.astype(str).agg(" ".join, axis=1)
        for term in q.split():
            view = view[hay.loc[view.index].str.contains(term, case=False, regex=False)]
    pages = max(1, -(-len(view) // page_size))
    if st.session_state.get("f_page", 1) > pages:  # filters shrank the result
        st.session_state["f_page"] = 1
    pg =st.number_input(f"หน้า (ทั้งหมด {pages} หน้า · {len(view):,} แถว)", 1, pages, 1, key="f_page") \
        if pages > 1 else 1
    chunk = view.iloc[(pg - 1) * page_size: pg * page_size]

    def _low(row):
        bad = row[D.TOTAL] < threshold
        return ["background-color:#FDECEC" if bad else "" for _ in row]

    if chunk.empty:
        st.info("ไม่พบแถวที่ตรงกับคำค้นหา")
    else:
        st.dataframe(chunk.style.apply(_low, axis=1).format({D.FEMALE_PCT: "{:.1f}"}),
                     hide_index=True, width="stretch", key="ex_table",
                     column_config={
                         D.YEAR: st.column_config.NumberColumn(format="%d"),
                         D.TOTAL: st.column_config.ProgressColumn(D.TOTAL, format="%d", min_value=0, max_value=tmax),
                     })

    e1, e2, _ = st.columns([1, 1, 2])
    e1.download_button("ดาวน์โหลด CSV", view.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"student_stats_{y0}-{y1}.csv", mime="text/csv",
                       icon=":material/download:", key="dl_csv", width="stretch")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        view.to_excel(xw, index=False, sheet_name="cleaned")
    e2.download_button("ดาวน์โหลด Excel", buf.getvalue(), file_name=f"student_stats_{y0}-{y1}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       icon=":material/table_view:", key="dl_xlsx", width="stretch")
