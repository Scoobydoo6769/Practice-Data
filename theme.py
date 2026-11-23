"""Design tokens, injected CSS and small HTML components (KPI card, insights, ladder…).

A restyle is a change to TOKENS plus .streamlit/config.toml (keep both in sync).
"""
from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st

# Change this to your institution's name; it shows in the sidebar and browser tab.
INSTITUTION_NAME = "วิทยาลัยเทคนิคสุราษฎร์ธานี"
APP_TITLE = "สถิตินักเรียนนักศึกษา 2560–2569"

TOKENS = {
    "bg": "#F3F5F9",          # 60%: clean cool ground
    "surface": "#FFFFFF",
    "navy": "#0E1B33",        # 30%: theme colour (sidebar, headings)
    "text": "#16233D",
    "muted": "#56657F",
    "border": "#E2E7F0",
    "accent": "#1D6FE8",      # 10%: signal blue
    "accent_soft": "#E8F0FD",
    "positive": "#15803D",
    "negative": "#C62828",
    "radius": "14px",
    "font": "Anuphan",
    "font_url": "https://fonts.googleapis.com/css2?family=Anuphan:wght@400;500;600;700&display=swap",
    # Series colours in order of use (reference: blue, orange, purple, teal, grey)
    "palette": ["#1D6FE8", "#F08C2E", "#8B3FD9", "#14A3B8", "#94A3B8", "#0E1B33", "#E0B100"],
}
GENDER_COLORS = {"ชาย": TOKENS["palette"][0], "หญิง": TOKENS["palette"][1]}
PROGRAM_COLORS = {"ปวช.": "#1D6FE8", "ปวส.": "#8B3FD9", "ป.ตรี": "#F08C2E", "ตกค้าง": "#94A3B8"}

_CSS = """
html, body, .stApp, [class*="css"], button, input, textarea, select, .stMarkdown {
  font-family: var(--font), 'Noto Sans Thai', system-ui, sans-serif;
}
.stApp { background: var(--bg); color: var(--text); }
::selection { background: var(--accent-soft); color: var(--navy); }
* { scrollbar-color: #C3CCDA transparent; scrollbar-width: thin; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding: 1.4rem 2.2rem 3rem; max-width: 1440px; }
#MainMenu, footer { visibility: hidden; }
.num, .kpi .value, .ins .value, .step .n, .pipe .n { font-variant-numeric: tabular-nums; }

/* ---------- sidebar brand ---------- */
.brand { display:flex; align-items:center; gap:.75rem; padding:.2rem 0 1rem; }
.brand img { flex:none; }
.brand .mark { width:38px; height:38px; border-radius:50%; background:var(--accent);
  display:grid; place-items:center; flex:none; }
.brand .name { color:#fff; font-weight:700; font-size:1.02rem; line-height:1.25; }
.brand .sub { color:#9FB0CC; font-size:.78rem; }
.nav-label { color:#8EA0C0; font-size:.74rem; font-weight:600; margin:.9rem 0 .15rem .2rem; }
[data-testid="stSidebar"] [data-testid="stPageLink"] a { border-radius:10px; }
[data-testid="stSidebar"] hr { border-color:#24375C; margin:1rem 0 .6rem; }
[data-testid="stSidebar"] h3 { color:#fff; font-size:.95rem; }

/* ---------- page header ---------- */
.page-head h1 { font-size:1.65rem; font-weight:700; color:var(--navy); margin:0; padding:0;
  letter-spacing:-.01em; line-height:1.3; }
.page-head p { color:var(--muted); margin:.3rem 0 0; font-size:.95rem; max-width:75ch; }
.page-head { margin-bottom: 1.1rem; }

/* ---------- cards: any container keyed card-* ---------- */
[class*="st-key-card"] {
  background: var(--surface); border:1px solid var(--border); border-radius: var(--radius);
  box-shadow: 0 1px 2px rgba(14,27,51,.04), 0 8px 24px -14px rgba(14,27,51,.18);
  padding: 1.05rem 1.2rem 1rem;
}
.card-title { font-weight:700; color:var(--navy); font-size:1.08rem; line-height:1.4; margin:0; }
.card-sub { color:var(--muted); font-size:.85rem; margin:.15rem 0 .4rem; }
.hint { color:var(--muted); font-size:.8rem; }

/* ---------- KPI ---------- */
.kpi { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
  box-shadow: 0 1px 2px rgba(14,27,51,.04), 0 8px 24px -14px rgba(14,27,51,.18);
  padding:.85rem 1.05rem; display:flex; justify-content:space-between; align-items:flex-end;
  gap:.8rem; margin-bottom:.75rem; min-height:104px; }
.kpi > div:first-child { align-self:flex-start; }
.kpi .label { color:var(--muted); font-size:.82rem; font-weight:500; }
.kpi .value { color:var(--navy); font-size:1.75rem; font-weight:700; line-height:1.2; margin:.1rem 0 .3rem; white-space:nowrap; }
.kpi .value small { font-size:.9rem; font-weight:500; color:var(--muted); margin-left:.25rem; }
.delta { display:inline-flex; align-items:center; gap:.3rem; font-size:.78rem; color:var(--muted); }
.delta b { display:inline-flex; align-items:center; gap:.15rem; padding:.05rem .45rem; border-radius:999px;
  font-weight:600; font-size:.76rem; }
.delta b.pos { background:#E6F4EA; color:var(--positive); }
.delta b.neg { background:#FBE9E9; color:var(--negative); }
.delta b.neu { background:#EEF1F6; color:var(--muted); }
.kpi img.bars { flex:none; }

/* ---------- insights ---------- */
.ins-grid { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0; }
.ins { padding:.35rem 1.1rem .2rem; border-left:1px solid var(--border); }
.ins:first-child { border-left:none; padding-left:.1rem; }
.ins .value { font-size:1.45rem; font-weight:700; line-height:1.2; color:var(--navy); }
.ins .value.pos { color:var(--positive); } .ins .value.neg { color:var(--negative); }
.ins .t { font-weight:600; color:var(--text); margin:.25rem 0 .15rem; font-size:.92rem; line-height:1.4; }
.ins .b { color:var(--muted); font-size:.82rem; line-height:1.5; }
@media (max-width: 1100px) {
  .ins-grid { grid-template-columns: repeat(2, minmax(0,1fr)); row-gap:1rem; }
  .ins:nth-child(3) { border-left:none; padding-left:.1rem; }
}
@media (max-width: 640px) {
  .ins-grid { grid-template-columns: 1fr; }
  .ins { border-left:none; padding-left:.1rem; border-top:1px solid var(--border); padding-top:.8rem; }
  .ins:first-child { border-top:none; }
  .block-container { padding: 1rem 1rem 2rem; }
}

/* ---------- education ladder (signature) ---------- */
.ladder { display:flex; align-items:stretch; gap:0; overflow-x:auto; padding:.4rem 0 .2rem; }
.step { flex:1 1 0; min-width:110px; text-align:center; }
.step .bar { margin:0 auto; width:70%; background:var(--accent-soft); border-radius:10px 10px 4px 4px;
  position:relative; display:flex; align-items:flex-end; justify-content:center; height:120px; }
.step .fill { width:100%; background:var(--accent); border-radius:10px 10px 4px 4px; }
.step .n { font-weight:700; color:var(--navy); font-size:1.05rem; margin-top:.45rem; }
.step .lv { color:var(--muted); font-size:.82rem; }
.link { flex:0 0 92px; display:flex; flex-direction:column; justify-content:center; align-items:center; padding-bottom:2.2rem; }
.link .r { font-weight:700; font-size:.95rem; font-variant-numeric: tabular-nums; }
.link .r.pos { color:var(--positive); } .link .r.neg { color:var(--negative); } .link .r.neu { color:var(--navy); }
.link .cap { color:var(--muted); font-size:.72rem; }
.link img { margin:.15rem 0; }

/* ---------- audit pipeline ---------- */
.pipe { display:flex; align-items:center; gap:.4rem; flex-wrap:wrap; }
.pipe .s { background:var(--surface); border:1px solid var(--border); border-radius:12px;
  padding:.7rem .95rem; min-width:128px; flex:1 1 128px; }
.pipe .s.final { background:var(--navy); border-color:var(--navy); }
.pipe .s.final .n, .pipe .s.final .l { color:#fff; }
.pipe .n { font-size:1.45rem; font-weight:700; color:var(--navy); line-height:1.2; }
.pipe .l { color:var(--muted); font-size:.8rem; }
.pipe .ok { color:var(--positive); font-weight:600; font-size:.76rem; }
.pipe > img { flex:none; }

/* ---------- action plan ---------- */
.plan { display:grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap:.6rem; }
.plan .c { border-radius:12px; padding:.75rem .9rem; background:#F7F9FC; border:1px solid var(--border); }
.plan .c.impact { background:var(--accent-soft); border-color:#C9DBFA; }
.plan .k { font-size:.74rem; font-weight:600; color:var(--muted); margin-bottom:.2rem; }
.plan .v { font-size:.88rem; line-height:1.55; color:var(--text); }
.plan-title { display:flex; gap:.6rem; align-items:baseline; margin-bottom:.55rem; }
.plan-title .no { font-weight:700; color:var(--accent); font-variant-numeric: tabular-nums; }
.plan-title .h { font-weight:700; color:var(--navy); font-size:1.02rem; }
.tag { font-size:.72rem; padding:.1rem .5rem; border-radius:999px; background:#EEF1F6; color:var(--muted); font-weight:600; }
.tag.hi { background:#E6F4EA; color:var(--positive); }
.tag.mid { background:#E3F1FC; color:#1A6FA8; }
@media (max-width: 900px) { .plan { grid-template-columns: 1fr 1fr; } }
@media (max-width: 560px) { .plan { grid-template-columns: 1fr; } }

/* ---------- widgets ---------- */
[data-testid="stPlotlyChart"] { background: transparent; }
div[data-testid="stDataFrame"] { border-radius: 10px; }
.stTabs [data-baseweb="tab-list"] { gap: .25rem; }
"""


def inject_theme() -> None:
    t = TOKENS
    root = (":root{"
            f"--bg:{t['bg']};--surface:{t['surface']};--navy:{t['navy']};--text:{t['text']};"
            f"--muted:{t['muted']};--border:{t['border']};--accent:{t['accent']};"
            f"--accent-soft:{t['accent_soft']};--positive:{t['positive']};--negative:{t['negative']};"
            f"--radius:{t['radius']};--font:'{t['font']}';"
            "}")
    st.html(f"<style>@import url('{t['font_url']}');{root}{_CSS}</style>")


def esc(s) -> str:
    return html.escape(str(s))


def svg_img(svg: str, w: int, h: int, alt: str = "", cls: str = "") -> str:
    """st.html strips inline <svg>, so ship SVG as a data-URI image."""
    if "xmlns" not in svg:
        svg = svg.replace("<svg ", "<svg xmlns='http://www.w3.org/2000/svg' ", 1)
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    c = f" class='{cls}'" if cls else ""
    return f"<img{c} src='{uri}' width='{w}' height='{h}' alt='{esc(alt)}' style='display:block'>"


# ------------------------------------------------------------------ chrome --
LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"


def _logo_html(size: int = 44) -> str:
    """College emblem from assets/logo.png; falls back to a simple chart icon if the file is missing."""
    try:
        uri = "data:image/png;base64," + base64.b64encode(LOGO_PATH.read_bytes()).decode()
        return f"<img src='{uri}' width='{size}' height='{size}' alt='โลโก้{esc(INSTITUTION_NAME)}' style='display:block'>"
    except OSError:
        mark = ("<svg width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='#fff' stroke-width='2.2' "
                "stroke-linecap='round' stroke-linejoin='round'><path d='M3 20h18'/><path d='M6 20V11'/>"
                "<path d='M11 20V6'/><path d='M16 20v-6'/><path d='M21 20V9'/></svg>")
        return f"<div class='mark'>{svg_img(mark, 20, 20)}</div>"


def sidebar_brand() -> None:
    st.sidebar.html(f"<div class='brand'>{_logo_html()}<div>"
                    f"<div class='name'>{esc(INSTITUTION_NAME)}</div>"
                    f"<div class='sub'>Decision Intelligence Portal</div></div></div>")


def page_header(title: str, subtitle: str = "") -> None:
    sub = f"<p>{esc(subtitle)}</p>" if subtitle else ""
    st.html(f"<div class='page-head'><h1>{esc(title)}</h1>{sub}</div>")


def card_title(title: str, sub: str = "") -> None:
    s = f"<div class='card-sub'>{esc(sub)}</div>" if sub else ""
    st.html(f"<div class='card-title'>{esc(title)}</div>{s}")


# -------------------------------------------------------------- components --
_COLOR = {"pos": TOKENS["positive"], "neg": TOKENS["negative"], "neu": TOKENS["muted"]}


def _arrow(up: bool, cls: str) -> str:
    path = "M5 1.5 9 7.5H1z" if up else "M5 8.5 1 2.5h8z"
    return svg_img(f"<svg width='10' height='10' viewBox='0 0 10 10'><path d='{path}' fill='{_COLOR[cls]}'/></svg>",
                   10, 10, "เพิ่มขึ้น" if up else "ลดลง")


def delta_badge(delta: float | None, *, higher_is_better: bool = True, unit: str = "%",
                suffix: str = "จากปีก่อน") -> str:
    if delta is None:
        return "<span class='delta'><b class='neu'>ไม่มีปีก่อนให้เทียบ</b></span>"
    good = (delta >= 0) == higher_is_better
    cls = "neu" if abs(delta) < 1e-9 else ("pos" if good else "neg")
    arrow = _arrow(delta >= 0, cls)
    txt = f"{abs(delta):.1%}" if unit == "%" else f"{abs(delta):.1f} {unit}"
    return f"<span class='delta'><b class='{cls}'>{arrow}{txt}</b>{esc(suffix)}</span>"


def mini_bars(values: list[float], w: int = 96, h: int = 44) -> str:
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return ""
    hi = max(vals) or 1
    n, gap = len(vals), 3
    bw = max(2, (w - gap * (n - 1)) / n)
    rects = []
    for i, v in enumerate(vals):
        bh = max(3, v / hi * (h - 2))
        color = TOKENS["accent"] if i == n - 1 else "#BFD3F6"
        rects.append(f"<rect x='{i * (bw + gap):.1f}' y='{h - bh:.1f}' width='{bw:.1f}' "
                     f"height='{bh:.1f}' rx='1.5' fill='{color}'/>")
    return svg_img(f"<svg width='{w}' height='{h}' viewBox='0 0 {w} {h}'>{''.join(rects)}</svg>",
                   w, h, f"แนวโน้มย้อนหลัง {n} ปี", "bars")


def kpi_card(label: str, value: str, delta_html: str = "", history: list | None = None,
             unit: str = "") -> str:
    u = f"<small>{esc(unit)}</small>" if unit else ""
    return (f"<div class='kpi'><div><div class='label'>{esc(label)}</div>"
            f"<div class='value'>{esc(value)}{u}</div>{delta_html}</div>"
            f"{mini_bars(history or [])}</div>")


def insight_panel(items: list[dict]) -> str:
    cells = "".join(
        f"<div class='ins'><div class='value {esc(i['tone'])}'>{esc(i['value'])}</div>"
        f"<div class='t'>{esc(i['title'])}</div><div class='b'>{esc(i['body'])}</div></div>"
        for i in items)
    return f"<div class='ins-grid'>{cells}</div>"


_ARROW = svg_img("<svg width='64' height='12' viewBox='0 0 64 12' fill='none' stroke='#9AA8BF' stroke-width='1.6' "
                 "stroke-linecap='round' stroke-linejoin='round'><path d='M2 6h58'/><path d='M55 1.5 60 6l-5 4.5'/></svg>",
                 64, 12)


def ladder(levels: list[tuple[str, int]], rates: list[float | None], benchmark: float = 0.9) -> str:
    """levels: [(label, count)], rates: pass-through between consecutive levels."""
    if not levels:
        return "<div class='hint'>ไม่มีข้อมูลสำหรับปีที่เลือก</div>"
    hi = max(c for _, c in levels) or 1
    parts = []
    for i, (lv, c) in enumerate(levels):
        pct = max(4, c / hi * 100)
        parts.append(f"<div class='step'><div class='bar'><div class='fill' style='height:{pct:.0f}%'></div></div>"
                     f"<div class='n'>{c:,}</div><div class='lv'>{esc(lv)}</div></div>")
        if i < len(rates):
            r = rates[i]
            if r is None:
                rtxt, cls = "—", "neu"
            else:
                rtxt, cls = f"{r:.0%}", ("pos" if r >= benchmark else "neg")
            parts.append(f"<div class='link'><div class='r {cls}'>{rtxt}</div>{_ARROW}"
                         f"<div class='cap'>ไปต่อปีถัดไป</div></div>")
    return f"<div class='ladder'>{''.join(parts)}</div>"


_CHEV = svg_img("<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#9AA8BF' stroke-width='2' "
                "stroke-linecap='round' stroke-linejoin='round'><path d='m9 6 6 6-6 6'/></svg>", 16, 16)


def pipeline(steps: list[tuple[str, str, str]]) -> str:
    """steps: [(number, label, note)]; the last one is the final, highlighted state."""
    out = []
    for i, (n, label, note) in enumerate(steps):
        final = " final" if i == len(steps) - 1 else ""
        nt = f"<div class='ok'>{esc(note)}</div>" if note else ""
        out.append(f"<div class='s{final}'><div class='n'>{esc(n)}</div><div class='l'>{esc(label)}</div>{nt}</div>")
        if i < len(steps) - 1:
            out.append(_CHEV)
    return f"<div class='pipe'>{''.join(out)}</div>"


def plan_card(no: int, title: str, finding: str, cause: str, action: str, impact: str,
              priority: str = "") -> str:
    tone = {"สูง": "hi", "กลาง": "mid"}.get(priority, "")
    tag = f"<span class='tag {tone}'>ความสำคัญ{esc(priority)}</span>" if priority else ""
    cell = lambda k, v, cls="": f"<div class='c {cls}'><div class='k'>{k}</div><div class='v'>{esc(v)}</div></div>"
    return (f"<div class='plan-title'><span class='no'>{no:02d}</span><span class='h'>{esc(title)}</span>{tag}</div>"
            f"<div class='plan'>{cell('ปัญหาที่พบจากข้อมูล', finding)}{cell('สาเหตุที่เป็นไปได้ (สมมติฐาน)', cause)}"
            f"{cell('สิ่งที่ควรทำ', action)}{cell('ผลลัพธ์ที่คาดว่าจะได้', impact, 'impact')}</div>")
