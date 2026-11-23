"""Data layer: load the 10 yearly Excel files, re-validate them, and compute analytics.

Every page reads from `get_clean()`; nothing else touches the files.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
FILE_GLOB = "Competition_Dataset_*.xlsx"

# Column names used across the app (short Thai labels)
YEAR, LEVEL, DEPT = "ปีการศึกษา", "ระดับชั้น", "แผนกวิชา"
MALE, FEMALE, TOTAL = "ชาย", "หญิง", "รวม"
PROGRAM, FEMALE_PCT = "หลักสูตร", "สัดส่วนหญิง (%)"

RAW_TO_CLEAN = {
    "ปีการศึกษา": YEAR, "ระดับชั้น": LEVEL, "แผนกวิชา": DEPT,
    "เพศชาย (คน)": MALE, "เพศหญิง (คน)": FEMALE, "รวมทั้งหมด (คน)": TOTAL,
}
LEVEL_ORDER = ["ปวช.1", "ปวช.2", "ปวช.3", "ปวส.1", "ปวส.2", "ป.ตรี", "ตกค้าง"]
PROGRAM_ORDER = ["ปวช.", "ปวส.", "ป.ตรี", "ตกค้าง"]
LADDER = ["ปวช.1", "ปวช.2", "ปวช.3", "ปวส.1", "ปวส.2"]


# ------------------------------------------------------------------ loading --
def _files() -> list[Path]:
    return sorted(DATA_DIR.glob(FILE_GLOB))


@st.cache_data(show_spinner="กำลังโหลดข้อมูล…")
def _read_all(signature: tuple) -> dict[str, pd.DataFrame]:
    return {name: pd.read_excel(DATA_DIR / name) for name, _ in signature}


def load_raw() -> dict[str, pd.DataFrame]:
    """Raw frames keyed by file name. Cache is keyed on mtime, so replacing a file reloads it."""
    sig = tuple((p.name, p.stat().st_mtime) for p in _files())
    return _read_all(sig)


# ----------------------------------------------------------------- cleaning --
def _norm_level(v: str) -> str:
    v = re.sub(r"\s+", "", str(v))
    return v.replace("ปริญญาตรี", "ป.ตรี")


def clean(raw: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, list[dict], dict]:
    """Return (clean_df, audit_log, pipeline_counts). Each rule counts what it touched."""
    log: list[dict] = []
    frames, schema_bad, year_fix = [], 0, 0
    for name, d in raw.items():
        d = d.copy()
        if set(d.columns) != set(RAW_TO_CLEAN):
            schema_bad += 1
        d = d.rename(columns=lambda c: RAW_TO_CLEAN.get(str(c).strip(), str(c).strip()))
        m = re.search(r"(\d{4})", name)
        if m:
            file_year = int(m.group(1))
            year_fix += int((pd.to_numeric(d[YEAR], errors="coerce") != file_year).sum())
            d[YEAR] = file_year
        d["ไฟล์ต้นทาง"] = name
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    raw_rows = len(df)

    log.append(dict(คอลัมน์="ทุกคอลัมน์", สิ่งที่ตรวจ="โครงสร้างคอลัมน์ตรงกันทั้ง 10 ไฟล์",
                    วิธีจัดการ="ตั้งชื่อคอลัมน์มาตรฐานเดียว แล้วรวมเป็นตารางเดียว", พบ=schema_bad))
    log.append(dict(คอลัมน์=YEAR, สิ่งที่ตรวจ="ปีในข้อมูลตรงกับปีในชื่อไฟล์",
                    วิธีจัดการ="ใช้ปีจากชื่อไฟล์เป็นค่าอ้างอิง", พบ=year_fix))

    ws = 0
    for c in (LEVEL, DEPT):
        s = df[c].astype(str)
        stripped = s.str.strip().str.replace(r"\s+", " ", regex=True)
        ws += int((s != stripped).sum())
        df[c] = stripped
    log.append(dict(คอลัมน์=f"{LEVEL}, {DEPT}", สิ่งที่ตรวจ="ช่องว่างเกิน / ช่องว่างหัวท้าย",
                    วิธีจัดการ="ตัดช่องว่างหัวท้ายและช่องว่างซ้อน", พบ=ws))

    lv = df[LEVEL].map(_norm_level)
    lv_fix = int((lv != df[LEVEL]).sum())
    df[LEVEL] = lv
    unknown = int((~df[LEVEL].isin(LEVEL_ORDER)).sum())
    log.append(dict(คอลัมน์=LEVEL, สิ่งที่ตรวจ="รูปแบบชื่อระดับชั้นไม่สม่ำเสมอ / ค่านอกรายการ",
                    วิธีจัดการ="แปลงเป็นรูปแบบมาตรฐาน (เช่น 'ปวช. 1' → 'ปวช.1')", พบ=lv_fix + unknown))

    bad_num = 0
    for c in (MALE, FEMALE, TOTAL):
        num = pd.to_numeric(df[c].astype(str).str.replace(",", "").str.strip(), errors="coerce")
        bad_num += int(num.isna().sum() - df[c].isna().sum())
        df[c] = num
    log.append(dict(คอลัมน์=f"{MALE}, {FEMALE}, {TOTAL}", สิ่งที่ตรวจ="ตัวอักษรปนในช่องตัวเลข",
                    วิธีจัดการ="ลบจุลภาค/ช่องว่าง แล้วแปลงเป็นจำนวนเต็ม", พบ=bad_num))

    missing = int(df[[YEAR, LEVEL, DEPT, MALE, FEMALE, TOTAL]].isna().sum().sum())
    df[MALE] = df[MALE].fillna(df[TOTAL] - df[FEMALE])
    df[FEMALE] = df[FEMALE].fillna(df[TOTAL] - df[MALE])
    df[TOTAL] = df[TOTAL].fillna(df[MALE] + df[FEMALE])
    df = df.dropna(subset=[YEAR, LEVEL, DEPT, MALE, FEMALE, TOTAL])
    log.append(dict(คอลัมน์="ทุกคอลัมน์", สิ่งที่ตรวจ="ค่าว่าง (Missing values)",
                    วิธีจัดการ="เติมจากความสัมพันธ์ ชาย + หญิง = รวม; ถ้าเติมไม่ได้จึงตัดแถว", พบ=missing))

    neg = int((df[[MALE, FEMALE, TOTAL]] < 0).any(axis=1).sum())
    df = df[(df[[MALE, FEMALE, TOTAL]] >= 0).all(axis=1)]
    log.append(dict(คอลัมน์=f"{MALE}, {FEMALE}, {TOTAL}", สิ่งที่ตรวจ="ค่าติดลบ (เป็นไปไม่ได้)",
                    วิธีจัดการ="ตัดแถวที่มีจำนวนคนติดลบ", พบ=neg))

    mismatch = int((df[MALE] + df[FEMALE] != df[TOTAL]).sum())
    df[TOTAL] = df[MALE] + df[FEMALE]
    log.append(dict(คอลัมน์=TOTAL, สิ่งที่ตรวจ="ผลรวมไม่ตรง (ชาย + หญิง ≠ รวม)",
                    วิธีจัดการ="คำนวณคอลัมน์รวมใหม่จาก ชาย + หญิง", พบ=mismatch))

    dups = int(df.duplicated([YEAR, LEVEL, DEPT]).sum())
    df = df.drop_duplicates([YEAR, LEVEL, DEPT])
    log.append(dict(คอลัมน์=f"{YEAR} + {LEVEL} + {DEPT}", สิ่งที่ตรวจ="แถวซ้ำ (Duplicates)",
                    วิธีจัดการ="เก็บแถวแรก ตัดแถวซ้ำ", พบ=dups))

    df = df.astype({YEAR: int, MALE: int, FEMALE: int, TOTAL: int})
    df[PROGRAM] = df[LEVEL].map(lambda v: next((p for p in PROGRAM_ORDER if v.startswith(p)), v))
    df[FEMALE_PCT] = (df[FEMALE] / df[TOTAL].where(df[TOTAL] > 0) * 100).round(1).fillna(0)
    order = {v: i for i, v in enumerate(LEVEL_ORDER)}
    df = (df.assign(_o=df[LEVEL].map(order).fillna(len(order)))
            .sort_values([YEAR, "_o", DEPT]).drop(columns="_o").reset_index(drop=True))
    log.append(dict(คอลัมน์=f"{PROGRAM}, {FEMALE_PCT}", สิ่งที่ตรวจ="คอลัมน์ช่วยวิเคราะห์",
                    วิธีจัดการ="สร้างใหม่: กลุ่มหลักสูตรจากระดับชั้น และ % นักเรียนหญิง", พบ=0))

    counts = dict(files=len(raw), raw_rows=raw_rows, dups=dups, missing=missing,
                  fixed=ws + lv_fix + bad_num + mismatch + year_fix, dropped=raw_rows - len(df),
                  final_rows=len(df))
    return df[[YEAR, LEVEL, PROGRAM, DEPT, MALE, FEMALE, TOTAL, FEMALE_PCT, "ไฟล์ต้นทาง"]], log, counts


@st.cache_data(show_spinner=False)
def _clean_cached(signature: tuple):
    return clean(load_raw())


def get_clean() -> tuple[pd.DataFrame, list[dict], dict]:
    sig = tuple((p.name, p.stat().st_mtime) for p in _files())
    df, log, counts = _clean_cached(sig)
    return df.copy(), log, counts


# ---------------------------------------------------------------- analytics --
def yearly(df: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    keys = [YEAR] + ([by] if by else [])
    return df.groupby(keys, as_index=False)[[MALE, FEMALE, TOTAL]].sum()


def pct_change(new: float, old: float) -> float | None:
    return None if not old else (new - old) / old


def retention(df: pd.DataFrame) -> pd.DataFrame:
    """Cohort pass-through: students in level B at year t+1 / level A at year t."""
    p = df.pivot_table(index=YEAR, columns=LEVEL, values=TOTAL, aggfunc="sum")
    rows = []
    for a, b in zip(LADDER, LADDER[1:]):
        if a in p and b in p:
            r = p[b].shift(-1) / p[a]
            for y, v in r.dropna().items():
                rows.append({"จาก": a, "ไป": b, "ขั้น": f"{a}→{b}", "ปีเริ่ม": int(y), "อัตรา": float(v)})
    return pd.DataFrame(rows, columns=["จาก", "ไป", "ขั้น", "ปีเริ่ม", "อัตรา"])


def linear_forecast(years, values, horizon: int = 3):
    """Least-squares line. Returns (future_years, forecast, fitted, resid_std)."""
    x, y = np.asarray(years, float), np.asarray(values, float)
    if len(x) < 2:
        return np.array([]), np.array([]), y, 0.0
    slope, icpt = np.polyfit(x, y, 1)
    fitted = slope * x + icpt
    fut = np.arange(x.max() + 1, x.max() + 1 + horizon)
    resid = float(np.std(y - fitted, ddof=1)) if len(x) > 2 else 0.0
    return fut, slope * fut + icpt, fitted, resid


def moving_avg_forecast(years, values, window: int = 3, horizon: int = 3):
    hist = list(map(float, values))
    fut_years = np.arange(max(years) + 1, max(years) + 1 + horizon)
    out = []
    for _ in range(horizon):
        nxt = float(np.mean(hist[-window:]))
        out.append(nxt)
        hist.append(nxt)
    ma = pd.Series(values, dtype=float).rolling(window).mean().to_numpy()
    return fut_years, np.array(out), ma


def insights(df: pd.DataFrame) -> list[dict]:
    """Key findings computed from the data. Each: {value, title, body, tone}."""
    out: list[dict] = []
    y = yearly(df).sort_values(YEAR)
    if len(y) >= 2:
        first, last = y.iloc[0], y.iloc[-1]
        g = pct_change(last[TOTAL], first[TOTAL])
        dips = y.assign(ch=y[TOTAL].pct_change()).dropna()
        worst = dips.loc[dips["ch"].idxmin()] if not dips.empty else None
        body = f"จาก {first[TOTAL]:,.0f} คน (ปี {first[YEAR]}) เป็น {last[TOTAL]:,.0f} คน (ปี {last[YEAR]})"
        if worst is not None and worst["ch"] < 0:
            body += f" — ปีเดียวที่ลดลงคือ {int(worst[YEAR])} ({worst['ch']:+.1%})"
        out.append(dict(value=f"{g:+.1%}", title="นักเรียนรวมเติบโตต่อเนื่อง", body=body,
                        tone="pos" if g >= 0 else "neg"))
    r = retention(df)
    step = r[r["ขั้น"] == "ปวช.1→ปวช.2"].sort_values("ปีเริ่ม")
    if len(step) >= 2:
        a, b = step.iloc[0], step.iloc[-1]
        out.append(dict(value=f"{a['อัตรา']:.0%} → {b['อัตรา']:.0%}",
                        title="นักเรียนเลื่อนจาก ปวช.1 ขึ้น ปวช.2 ได้มากขึ้น",
                        body=f"อัตราคงอยู่รุ่นปี {a['ปีเริ่ม']} เทียบรุ่นปี {b['ปีเริ่ม']}"
                             + (" แต่ยังเป็นช่วงที่หลุดออกมากที่สุดในบันไดการศึกษา"
                                if r[r["ปีเริ่ม"] == b["ปีเริ่ม"]]["อัตรา"].min() == b["อัตรา"] else ""),
                        tone="pos" if b["อัตรา"] >= a["อัตรา"] else "neg"))
    if len(y) >= 1:
        share = y[FEMALE] / y[TOTAL]
        out.append(dict(value=f"{share.iloc[-1]:.1%}", title="สัดส่วนนักเรียนหญิงไม่ขยับมา 10 ปี",
                        body=f"อยู่ในช่วง {share.min():.1%}–{share.max():.1%} ทุกปี "
                             f"แม้จำนวนนักเรียนรวมจะเพิ่มขึ้น",
                        tone="neu"))
    lv = yearly(df, LEVEL)
    rem = lv[lv[LEVEL] == "ตกค้าง"].sort_values(YEAR)
    if len(rem) >= 2:
        peak = rem.loc[rem[TOTAL].idxmax()]
        last = rem.iloc[-1]
        tot_last = y.loc[y[YEAR] == last[YEAR], TOTAL].iloc[0]
        out.append(dict(value=f"{last[TOTAL]:,.0f} คน",
                        title="นักเรียนตกค้างปีล่าสุด" + ("สูงที่สุดในรอบ 10 ปี" if peak[YEAR] == last[YEAR] else ""),
                        body=f"คิดเป็น {last[TOTAL] / tot_last:.1%} ของนักเรียนทั้งหมดในปี {last[YEAR]} "
                             f"(ปีก่อน {rem.iloc[-2][TOTAL]:,.0f} คน)",
                        tone="neg" if last[TOTAL] > rem.iloc[-2][TOTAL] else "pos"))
    return out
