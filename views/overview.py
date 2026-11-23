"""① Executive Overview: KPI cards, key insights, trend, education ladder, cross-filtered charts."""
import streamlit as st

import charts as C
import data as D
import theme as T

df_all, _, _ = D.get_clean()
years = sorted(df_all[D.YEAR].unique())


def _reset():
    for k in [k for k in st.session_state if k.startswith("ov_")]:
        del st.session_state[k]


# ---------------------------------------------------------------- sidebar --
with st.sidebar:
    st.subheader("ตัวกรอง")
    y0, y1 = st.select_slider("ช่วงปีการศึกษา", options=years, value=(years[0], years[-1]), key="ov_years")
    st.button("ล้างตัวกรองทั้งหมด", key="reset_filters", on_click=_reset, icon=":material/restart_alt:",
              width="stretch")

df = df_all[df_all[D.YEAR].between(y0, y1)]

# Cross-filter: a click on the department bar chart narrows everything above it.
sel_state = st.session_state.get("ov_dept_chart")
selected = []
try:
    selected = sorted({p.get("customdata") if isinstance(p.get("customdata"), str) else p.get("y")
                       for p in sel_state["selection"]["points"]} - {None})
except (TypeError, KeyError, AttributeError):
    selected = []
dff = df[df[D.DEPT].isin(selected)] if selected else df

T.page_header("ภาพรวมสำหรับผู้บริหาร",
              f"สถิตินักเรียนนักศึกษา ปีการศึกษา {y0}–{y1} · 10 แผนกวิชา · ระดับ ปวช. ปวส. ป.ตรี"
              + (f" · กรองเฉพาะ: {', '.join(selected)}" if selected else ""))

if dff.empty:
    st.info("ไม่มีข้อมูลตามตัวกรองที่เลือก ลองขยายช่วงปี หรือกด 'ล้างตัวกรองทั้งหมด'")
    st.stop()

# ------------------------------------------------------------ key insights --
with st.container(key="card-insights"):
    T.card_title("ข้อค้นพบสำคัญ", "สรุปจากข้อมูลจริงในช่วงที่เลือก อ่านจบใน 10 วินาที")
    st.html(T.insight_panel(D.insights(dff)))

# ----------------------------------------------------- trend + KPI column --
yr = D.yearly(dff).sort_values(D.YEAR)
last, prev = yr.iloc[-1], (yr.iloc[-2] if len(yr) > 1 else None)
g_all = D.pct_change(last[D.TOTAL], yr.iloc[0][D.TOTAL]) if len(yr) > 1 else None

left, right = st.columns([2.15, 1], gap="medium")
with left:
    with st.container(key="card-trend"):
        view = st.segmented_control("มุมมอง", ["รวม", "แยกเพศ", "แยกหลักสูตร"], default="รวม",
                                    key="ov_view", label_visibility="collapsed") or "รวม"
        if g_all is not None:
            title = f"นักเรียนเพิ่มขึ้น {g_all:+.1%} ใน {len(yr)} ปี จาก {yr.iloc[0][D.TOTAL]:,} เป็น {last[D.TOTAL]:,} คน"
        else:
            title = f"จำนวนนักเรียนปี {int(last[D.YEAR])}: {last[D.TOTAL]:,} คน"
        C.show(C.trend(dff, view, title, "จำนวนนักเรียนรายปีการศึกษา (คน)"), key="ov_trend")

with right:
    hist = lambda col: yr[col].tolist()
    share = yr[D.FEMALE] / yr[D.TOTAL]
    lv = D.yearly(dff, D.LEVEL)
    intake = lv[lv[D.LEVEL] == "ปวช.1"].set_index(D.YEAR)[D.TOTAL].reindex(yr[D.YEAR]).fillna(0)
    rem = lv[lv[D.LEVEL] == "ตกค้าง"].set_index(D.YEAR)[D.TOTAL].reindex(yr[D.YEAR]).fillna(0)
    ly = int(last[D.YEAR])
    p = lambda s: D.pct_change(s.iloc[-1], s.iloc[-2]) if len(s) > 1 else None
    cards = [
        T.kpi_card(f"นักเรียนทั้งหมด ปี {ly}", f"{last[D.TOTAL]:,}", T.delta_badge(p(yr[D.TOTAL])),
                   hist(D.TOTAL), "คน"),
        T.kpi_card("รับเข้าใหม่ ปวช.1", f"{intake.iloc[-1]:,.0f}", T.delta_badge(p(intake)),
                   intake.tolist(), "คน"),
        T.kpi_card("สัดส่วนนักเรียนหญิง", f"{share.iloc[-1]:.1%}",
                   T.delta_badge((share.iloc[-1] - share.iloc[-2]) * 100 if len(share) > 1 else None,
                                 unit="จุด"), share.tolist()),
        T.kpi_card("นักเรียนตกค้าง", f"{rem.iloc[-1]:,.0f}",
                   T.delta_badge(p(rem), higher_is_better=False), rem.tolist(), "คน"),
    ]
    st.html("".join(cards))

# ------------------------------------------------------- education ladder --
r = D.retention(df_all)
cohort_years = sorted(r["ปีเริ่ม"].unique()) if not r.empty else []
with st.container(key="card-ladder"):
    a, b = st.columns([3, 1.2], vertical_alignment="bottom")
    opts = [y for y in years if y0 <= y <= y1][::-1]
    with_next = [i for i, y in enumerate(opts) if y < years[-1]]  # latest year has no "next year" yet
    ladder_year = b.selectbox("ปีการศึกษาที่แสดง", opts, index=with_next[0] if with_next else 0,
                              key="ov_ladder_year")
    step12 = r[(r["ขั้น"] == "ปวช.1→ปวช.2")].sort_values("ปีเริ่ม")
    with a:
        if len(step12) >= 2:
            T.card_title(f"บันไดการศึกษา: นักเรียน ปวช.1 ไปต่อ ปวช.2 ได้ {step12.iloc[-1]['อัตรา']:.0%} "
                         f"(รุ่น {step12.iloc[-1]['ปีเริ่ม']}) จากเดิม {step12.iloc[0]['อัตรา']:.0%}",
                         "แท่ง = จำนวนนักเรียนแต่ละระดับในปีที่เลือก · ตัวเลขระหว่างขั้น = สัดส่วนรุ่นเดียวกันที่ขึ้นระดับถัดไปในปีต่อมา "
                         "(เขียว ≥ 90%, แดง < 90%)")
        else:
            T.card_title("บันไดการศึกษา")
    src = df_all[df_all[D.DEPT].isin(selected)] if selected else df_all
    cnt = src[src[D.YEAR] == ladder_year].groupby(D.LEVEL)[D.TOTAL].sum()
    rr = D.retention(src)
    levels = [(lv_, int(cnt.get(lv_, 0))) for lv_ in D.LADDER]
    rates = []
    for a_, b_ in zip(D.LADDER, D.LADDER[1:]):
        m = rr[(rr["จาก"] == a_) & (rr["ปีเริ่ม"] == ladder_year)]
        rates.append(float(m["อัตรา"].iloc[0]) if not m.empty else None)
    st.html(T.ladder(levels, rates))
    if all(x is None for x in rates):
        st.caption(f"ปี {ladder_year} เป็นปีล่าสุด จึงยังไม่มีข้อมูลปีถัดไปให้คำนวณอัตราการไปต่อ")

# ------------------------------------------------ department + programme --
c1, c2 = st.columns([1.35, 1], gap="medium")
with c1:
    with st.container(key="card-dept"):
        d = df.groupby(D.DEPT)[D.TOTAL].sum()
        spread = (d.max() - d.min()) / d.mean() if len(d) > 1 else 0
        top = d.idxmax()
        C.show(C.dept_bar(df, selected,
                          f"ทุกแผนกมีนักเรียนใกล้เคียงกัน ต่างกันไม่เกิน {spread:.1%} · สูงสุด {top}",
                          f"รวมปี {y0}–{y1} (คน) · คลิกแท่งเพื่อกรองทั้งหน้า ดับเบิลคลิกเพื่อยกเลิก"),
               key="ov_dept_chart", on_select="rerun", selection_mode="points")
with c2:
    with st.container(key="card-program"):
        pg = dff.groupby(D.PROGRAM)[D.TOTAL].sum()
        share_pvc = pg.get("ปวช.", 0) / pg.sum() if pg.sum() else 0
        C.show(C.program_donut(dff, f"ปวช. คิดเป็น {share_pvc:.0%} ของนักเรียนทั้งหมด",
                               f"สัดส่วนตามหลักสูตร ปี {y0}–{y1}"), key="ov_donut")
