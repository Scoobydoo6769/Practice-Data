"""⑤ Strategic Action Plan: Finding → Root cause → Action → Expected impact, plus user-added cards."""
import pandas as pd
import streamlit as st

import data as D
import theme as T

df, _, _ = D.get_clean()
y = D.yearly(df).sort_values(D.YEAR)
last_year = int(y[D.YEAR].iloc[-1])
lv = D.yearly(df, D.LEVEL)
last_lv = lv[lv[D.YEAR] == last_year].set_index(D.LEVEL)[D.TOTAL]
r = D.retention(df)
s12 = r[r["ขั้น"] == "ปวช.1→ปวช.2"].sort_values("ปีเริ่ม")
ret, ret_year = float(s12["อัตรา"].iloc[-1]), int(s12["ปีเริ่ม"].iloc[-1])
pvc1 = float(last_lv.get("ปวช.1", 0))  # newest cohort, for the forward-looking impact
pvc1_cohort = float(lv[(lv[D.YEAR] == ret_year) & (lv[D.LEVEL] == "ปวช.1")][D.TOTAL].sum())
rem = float(last_lv.get("ตกค้าง", 0))
tot = float(y[D.TOTAL].iloc[-1])
share = float(y[D.FEMALE].iloc[-1] / tot)
fy, fv, _, _ = D.linear_forecast(y[D.YEAR], y[D.TOTAL], 3)

plans = [
    dict(title="ลดการหลุดออกช่วง ปวช.1 → ปวช.2", priority="สูง",
         finding=f"รุ่นปี {ret_year} ไปต่อ ปวช.2 ได้ {ret:.1%} คือหายไปราว {pvc1_cohort * (1 - ret):,.0f} คน "
                 "เป็นขั้นที่หลุดมากที่สุดในบันไดการศึกษา",
         cause="นักเรียนปรับตัวกับการเรียนสายปฏิบัติในปีแรกไม่ได้ เลือกแผนกไม่ตรงความถนัด หรือมีภาระค่าใช้จ่าย",
         action="ตั้งระบบครูที่ปรึกษาติดตามรายบุคคลในภาคเรียนแรก และจัดแนะแนวทดลองเรียนก่อนเลือกแผนก",
         impact=f"ถ้ายกอัตราไปต่อเป็น 90% รุ่นปี {last_year} ({pvc1:,.0f} คน) จะอยู่ต่อเพิ่มอีกราว "
                f"{max(0, pvc1 * (0.90 - ret)):,.0f} คน"),
    dict(title="ลดจำนวนนักเรียนตกค้าง", priority="สูง",
         finding=f"ปี {last_year} มีนักเรียนตกค้าง {rem:,.0f} คน ({rem / tot:.1%} ของทั้งหมด)",
         cause="ไม่ผ่านรายวิชาหลักหรือฝึกประสบการณ์วิชาชีพไม่ครบ และติดตามช้าจนสะสมถึงปีสุดท้าย",
         action="ระบบเตือนล่วงหน้า (Early Warning) จากผลการเรียนกลางภาค พร้อมสอนซ่อมเสริมและจัดรอบฝึกงานเพิ่ม",
         impact=f"ลดตกค้าง 30% เท่ากับนักเรียนจบตามเวลาเพิ่มขึ้นราว {rem * 0.3:,.0f} คนต่อปี"),
    dict(title="เพิ่มความหลากหลายทางเพศในสายช่าง", priority="กลาง",
         finding=f"สัดส่วนนักเรียนหญิงอยู่ที่ {share:.1%} และแทบไม่เปลี่ยนตลอด 10 ปี ทุกแผนกมีลักษณะเดียวกัน",
         cause="ภาพจำว่าสายช่างเป็นอาชีพของผู้ชาย และขาดต้นแบบศิษย์เก่าหญิงที่ประสบความสำเร็จ",
         action="แนะแนวเชิงรุกร่วมกับโรงเรียนมัธยม นำเสนอศิษย์เก่าหญิงเป็นต้นแบบ เริ่มจากแผนก IT สถาปัตย์ และเมคคาทรอนิกส์",
         impact=f"ถ้าสัดส่วนเพิ่ม 5 จุด จะมีนักเรียนหญิงเพิ่มราว {tot * 0.05:,.0f} คน (คิดจากฐานปี {last_year})"),
    dict(title="เตรียมทรัพยากรรองรับการเติบโต", priority="กลาง",
         finding=(f"แนวโน้มคาดว่าปี {int(fy[-1])} จะมีนักเรียนราว {fv[-1]:,.0f} คน "
                  f"({D.pct_change(fv[-1], tot):+.1%} จากปี {last_year})") if len(fv) else "ข้อมูลไม่พอสำหรับคาดการณ์",
         cause="ความต้องการแรงงานสายอาชีพสูงขึ้น และการเปิดระดับ ป.ตรี ตั้งแต่ปี 2567 ช่วยดึงนักเรียน ปวส. ให้เรียนต่อ",
         action="วางแผนห้องเรียน ครู และเครื่องมือฝึกล่วงหน้า 2–3 ปี โดยทบทวนตัวเลขคาดการณ์ทุกปีการศึกษา",
         impact=(f"ต้องรองรับนักเรียนเพิ่มราว {max(0, fv[-1] - tot):,.0f} คน โดยไม่ให้ห้องเรียนแออัด"
                 if len(fv) else "-")),
]

st.session_state.setdefault("ap_custom", [])

T.page_header("แผนปฏิบัติเชิงกลยุทธ์",
              "เปลี่ยนข้อค้นพบให้เป็นการลงมือทำ ตัวเลขทุกตัวคำนวณจากข้อมูลจริง ส่วนสาเหตุเป็นสมมติฐานที่ควรตรวจสอบต่อ")

for i, p in enumerate(plans + st.session_state["ap_custom"], start=1):
    with st.container(key=f"card-plan-{i}"):
        st.html(T.plan_card(i, p["title"], p["finding"], p["cause"], p["action"], p["impact"], p.get("priority", "")))

with st.container(key="card-add"):
    T.card_title("เพิ่มข้อเสนอแนะใหม่", "เพิ่มการ์ดหน้างานได้ทันที (เก็บไว้จนกว่าจะปิดหน้าเว็บ)")
    with st.form("ap_form", clear_on_submit=True, border=False):
        t = st.text_input("หัวข้อ", key="ap_title")
        a, b = st.columns(2)
        f = a.text_area("ปัญหาที่พบจากข้อมูล", key="ap_finding", height=90)
        c = b.text_area("สาเหตุที่เป็นไปได้", key="ap_cause", height=90)
        ac = a.text_area("สิ่งที่ควรทำ", key="ap_action", height=90)
        im = b.text_area("ผลลัพธ์ที่คาดว่าจะได้", key="ap_impact", height=90)
        pr = st.radio("ความสำคัญ", ["สูง", "กลาง", "ต่ำ"], index=1, horizontal=True, key="ap_priority")
        if st.form_submit_button("เพิ่มการ์ด", icon=":material/add:", type="primary"):
            if t.strip() and f.strip() and ac.strip():
                st.session_state["ap_custom"].append(dict(title=t.strip(), finding=f.strip(), cause=c.strip() or "-",
                                                          action=ac.strip(), impact=im.strip() or "-", priority=pr))
                st.rerun()
            else:
                st.warning("กรอกอย่างน้อย หัวข้อ, ปัญหาที่พบ และสิ่งที่ควรทำ")

out = pd.DataFrame(plans + st.session_state["ap_custom"]).rename(columns={
    "title": "หัวข้อ", "priority": "ความสำคัญ", "finding": "ปัญหาที่พบ", "cause": "สาเหตุ (สมมติฐาน)",
    "action": "สิ่งที่ควรทำ", "impact": "ผลลัพธ์ที่คาดหวัง"})
st.download_button("ดาวน์โหลดแผนปฏิบัติ (CSV)", out.to_csv(index=False).encode("utf-8-sig"),
                   file_name="action_plan.csv", mime="text/csv", icon=":material/download:", key="ap_dl")
