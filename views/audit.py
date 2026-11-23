"""② Data Cleansing & Audit Log: health scorecard, methodology table, raw vs cleaned preview."""
import pandas as pd
import streamlit as st

import data as D
import theme as T

df, log, n = D.get_clean()
raw = D.load_raw()

T.page_header("คุณภาพข้อมูล & Audit Log",
              "ทุกครั้งที่เปิดเว็บ ระบบจะตรวจไฟล์ Excel ทั้ง 10 ไฟล์ซ้ำด้วยกฎชุดเดียวกัน "
              "เพื่อยืนยันว่าข้อมูลที่ใช้วิเคราะห์สะอาดจริง")

issues = sum(r["พบ"] for r in log)
completeness = n["final_rows"] / n["raw_rows"] if n["raw_rows"] else 0
cells = n["final_rows"] * 6
with st.container(key="card-health"):
    T.card_title(f"ข้อมูลพร้อมใช้ {completeness:.0%}: {n['final_rows']:,} จาก {n['raw_rows']:,} แถว "
                 f"ผ่านการตรวจ {len(log) - 1} กฎ", "Data Health Scorecard · ก่อน → หลังตรวจสอบ")
    st.html(T.pipeline([
        (f"{n['files']}", "ไฟล์ Excel (ปี 2560–2569)", ""),
        (f"{n['raw_rows']:,}", "แถวข้อมูลดิบรวม", ""),
        (f"{n['dups']:,}", "แถวซ้ำที่ตัดออก", "ไม่พบ" if n["dups"] == 0 else ""),
        (f"{n['missing']:,}", "ค่าว่างที่จัดการ", "ไม่พบ" if n["missing"] == 0 else ""),
        (f"{n['fixed']:,}", "จุดที่แก้รูปแบบ/ผลรวม", "ไม่พบ" if n["fixed"] == 0 else ""),
        (f"{n['final_rows']:,}", f"แถวพร้อมใช้ · {cells:,} เซลล์", f"สมบูรณ์ {completeness:.0%}"),
    ]))
    if issues == 0:
        st.caption("ไฟล์ที่ได้รับผ่านการคลีนมาแล้ว ทุกกฎจึงไม่พบปัญหา แต่ระบบยังตรวจซ้ำทุกครั้ง "
                   "ถ้ามีการแทนที่ไฟล์ในโฟลเดอร์ data/ ด้วยข้อมูลดิบ ตัวเลขในหน้านี้จะอัปเดตเอง")

with st.container(key="card-method"):
    T.card_title("วิธีตรวจและแก้ไขข้อมูลรายคอลัมน์", "Cleansing Methodology · ผลจากการรันจริงครั้งล่าสุด")
    tbl = pd.DataFrame(log)
    tbl["สถานะ"] = tbl["พบ"].map(lambda v: "ผ่าน" if v == 0 else "แก้ไขแล้ว")
    tbl.loc[tbl["สิ่งที่ตรวจ"] == "คอลัมน์ช่วยวิเคราะห์", "สถานะ"] = "เพิ่มใหม่"
    st.dataframe(tbl, hide_index=True, width="stretch", height=36 * (len(tbl) + 1) + 4, key="au_method",
                 column_config={
                     "คอลัมน์": st.column_config.TextColumn(width="small"),
                     "สิ่งที่ตรวจ": st.column_config.TextColumn(width="medium"),
                     "วิธีจัดการ": st.column_config.TextColumn(width="large"),
                     "พบ": st.column_config.NumberColumn("พบ (จุด)", format="%d", width="small"),
                     "สถานะ": st.column_config.TextColumn(width="small"),
                 })

with st.container(key="card-preview"):
    T.card_title("ตัวอย่างข้อมูล: ไฟล์ต้นฉบับ เทียบกับ ข้อมูลหลังรวมและตรวจแล้ว",
                 "Raw vs. Cleaned Preview · คอลัมน์สีเขียว = ถูกปรับชื่อให้สั้นลงหรือสร้างเพิ่ม")
    name = st.selectbox("เลือกไฟล์ต้นฉบับ", list(raw), index=len(raw) - 1, key="au_file")
    raw_df = raw[name].head(8)
    st.markdown(f"**ก่อน** · `{name}` (ตามไฟล์ Excel)")
    st.dataframe(raw_df, hide_index=True, width="stretch", key="au_raw")
    year = int("".join(ch for ch in name if ch.isdigit())[:4])
    keys = pd.DataFrame({D.LEVEL: raw_df["ระดับชั้น"].astype(str).str.strip(),
                         D.DEPT: raw_df["แผนกวิชา"].astype(str).str.strip()})
    clean_df = keys.merge(df[df[D.YEAR] == year].drop(columns="ไฟล์ต้นทาง"), on=[D.LEVEL, D.DEPT], how="left")
    clean_df = clean_df[[c for c in df.columns if c != "ไฟล์ต้นทาง"]]
    changed = [D.MALE, D.FEMALE, D.TOTAL, D.PROGRAM, D.FEMALE_PCT]
    st.markdown("**หลัง** · แถวเดียวกันในตารางรวม 10 ปีที่แอปใช้")
    st.dataframe(clean_df.style.set_properties(subset=changed, **{"background-color": "#E6F4EA"})
                 .format({D.FEMALE_PCT: "{:.1f}"}),
                 hide_index=True, width="stretch", key="au_clean")

with st.container(key="card-files"):
    T.card_title("จำนวนแถวต่อไฟล์", "ปี 2567 เป็นต้นไปมี 70 แถว เพราะเพิ่มระดับ ป.ตรี (7 ระดับ × 10 แผนก)")
    files = pd.DataFrame([{"ไฟล์": k, "แถว": len(v), "คอลัมน์": v.shape[1],
                           "ค่าว่าง": int(v.isna().sum().sum())} for k, v in raw.items()])
    st.dataframe(files, hide_index=True, width="stretch", height=36 * (len(files) + 1) + 4, key="au_files",
                 column_config={"แถว": st.column_config.ProgressColumn(
                     "แถว", format="%d", min_value=0, max_value=int(files["แถว"].max()))})
