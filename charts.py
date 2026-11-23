"""Plotly chart builders. Each returns a figure and never raises on empty input."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data as D
from theme import GENDER_COLORS, PROGRAM_COLORS, TOKENS

FONT = f"{TOKENS['font']}, Noto Sans Thai, sans-serif"
INK = TOKENS["text"]  # all chart text (ticks, legend, labels, annotations) uses the darkest text colour
PLOT_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "zoomIn2d", "zoomOut2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}


def style(fig: go.Figure, title: str | None = None, subtitle: str | None = None,
          height: int = 360, legend: bool = True) -> go.Figure:
    """Apply the dashboard look. The Thai title/subtitle ride in layout.meta and are drawn
    as HTML by show(), so long titles wrap on narrow screens instead of being clipped."""
    meta = {"title": title or "", "subtitle": subtitle or ""}
    fig.update_layout(
        meta=meta, height=height,
        font=dict(family=FONT, color=TOKENS["text"], size=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=TOKENS["palette"],
        margin=dict(l=8, r=12, b=8, t=34 if legend else 12),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, xanchor="left",
                    bgcolor="rgba(0,0,0,0)", font=dict(size=12, color=INK), title_text="") if legend else None,
        showlegend=legend,
        hoverlabel=dict(font_family=FONT, bgcolor="#fff", bordercolor=TOKENS["border"],
                        font_color=TOKENS["text"]),
        separators=".,",
    )
    fig.update_xaxes(gridcolor="#EDF0F5", zeroline=False, linecolor=TOKENS["border"],
                     tickfont=dict(color=INK), title_font=dict(color=INK))
    fig.update_yaxes(gridcolor="#EDF0F5", zeroline=False, tickfont=dict(color=INK), title_font=dict(color=INK),
                     tickformat=",")
    return fig


def empty_figure(message: str = "ไม่มีข้อมูลตามตัวกรองที่เลือก", height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14, color=INK))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style(fig, height=height, legend=False)


def show(fig: go.Figure, key: str, **kw):
    from theme import card_title
    meta = fig.layout.meta if isinstance(fig.layout.meta, dict) else {}
    if meta.get("title"):
        card_title(meta["title"], meta.get("subtitle", ""))
    cfg = dict(PLOT_CONFIG, toImageButtonOptions=dict(PLOT_CONFIG["toImageButtonOptions"],
                                                      filename=(meta.get("title") or key)[:60]))
    return st.plotly_chart(fig, width="stretch", key=key, config=cfg, **kw)


def _year_axis(fig, years):
    fig.update_xaxes(tickmode="array", tickvals=sorted(set(years)), tickformat="d")


# ---------------------------------------------------------------- overview --
def trend(df: pd.DataFrame, view: str, title: str, subtitle: str = "") -> go.Figure:
    if df.empty:
        return empty_figure()
    fig = go.Figure()
    if view == "แยกเพศ":
        y = D.yearly(df)
        for col in (D.MALE, D.FEMALE):
            fig.add_scatter(x=y[D.YEAR], y=y[col], name=col, mode="lines+markers",
                            line=dict(color=GENDER_COLORS[col], width=2.5, shape="spline", smoothing=0.6),
                            marker=dict(size=7, color="#fff", line=dict(width=2, color=GENDER_COLORS[col])),
                            hovertemplate=f"{col} %{{y:,}} คน<extra></extra>")
    elif view == "แยกหลักสูตร":
        y = D.yearly(df, D.PROGRAM)
        for p in D.PROGRAM_ORDER:
            s = y[y[D.PROGRAM] == p]
            if s.empty:
                continue
            fig.add_scatter(x=s[D.YEAR], y=s[D.TOTAL], name=p, mode="lines+markers",
                            line=dict(color=PROGRAM_COLORS[p], width=2.5, shape="spline", smoothing=0.6),
                            marker=dict(size=7, color="#fff", line=dict(width=2, color=PROGRAM_COLORS[p])),
                            hovertemplate=f"{p} %{{y:,}} คน<extra></extra>")
    else:
        y = D.yearly(df)
        fig.add_scatter(x=y[D.YEAR], y=y[D.TOTAL], name="รวม", mode="lines+markers",
                        fill="tozeroy", fillcolor="rgba(29,111,232,0.08)",
                        line=dict(color=TOKENS["accent"], width=3, shape="spline", smoothing=0.6),
                        marker=dict(size=8, color="#fff", line=dict(width=2.5, color=TOKENS["accent"])),
                        hovertemplate="รวม %{y:,} คน<extra></extra>")
    _year_axis(fig, df[D.YEAR])
    fig.update_layout(hovermode="x unified")
    return style(fig, title, subtitle, height=380, legend=len(fig.data) > 1)


def dept_bar(df: pd.DataFrame, selected: list[str], title: str, subtitle: str = "") -> go.Figure:
    if df.empty:
        return empty_figure()
    d = df.groupby(D.DEPT, as_index=False)[D.TOTAL].sum().sort_values(D.TOTAL)
    colors = [TOKENS["accent"] if (not selected or v in selected) else "#C9D7EE" for v in d[D.DEPT]]
    fig = go.Figure(go.Bar(x=d[D.TOTAL], y=d[D.DEPT], orientation="h", marker_color=colors,
                           customdata=d[D.DEPT], text=d[D.TOTAL], texttemplate="%{text:,}",
                           textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}<br>%{x:,} คน<extra></extra>"))
    fig.update_layout(bargap=0.35, clickmode="event+select")
    fig.update_xaxes(showgrid=False, showticklabels=False, range=[0, d[D.TOTAL].max() * 1.16])
    fig.update_yaxes(showgrid=False, tickfont=dict(color=INK))
    return style(fig, title, subtitle, height=430, legend=False)


def program_donut(df: pd.DataFrame, title: str, subtitle: str = "") -> go.Figure:
    if df.empty:
        return empty_figure()
    d = df.groupby(D.PROGRAM, as_index=False)[D.TOTAL].sum()
    d = d.set_index(D.PROGRAM).reindex([p for p in D.PROGRAM_ORDER if p in set(d[D.PROGRAM])]).reset_index()
    total = int(d[D.TOTAL].sum())
    fig = go.Figure(go.Pie(labels=d[D.PROGRAM], values=d[D.TOTAL], hole=0.64, sort=False,
                           direction="clockwise", marker=dict(colors=[PROGRAM_COLORS[p] for p in d[D.PROGRAM]],
                                                              line=dict(color="#fff", width=3)),
                           textinfo="percent", textfont=dict(color="#fff", size=12),
                           hovertemplate="%{label}<br>%{value:,} คน (%{percent})<extra></extra>"))
    fig.add_annotation(text=f"<b>{total:,}</b>", showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper",
                       yanchor="bottom", font=dict(size=26, color=TOKENS["navy"]))
    fig.add_annotation(text="นักเรียนรวม (คน)", showarrow=False, x=0.5, y=0.48, xref="paper", yref="paper",
                       yanchor="top", font=dict(size=12, color=INK))
    fig = style(fig, title, subtitle, height=430)
    fig.update_layout(legend=dict(orientation="v", x=1.02, xanchor="left", y=0.5, yanchor="middle"))
    return fig


# ---------------------------------------------------------------- explorer --
def level_stack(df: pd.DataFrame, title: str, subtitle: str = "") -> go.Figure:
    if df.empty:
        return empty_figure()
    y = D.yearly(df, D.PROGRAM)
    fig = go.Figure()
    for p in D.PROGRAM_ORDER:
        s = y[y[D.PROGRAM] == p]
        if not s.empty:
            fig.add_bar(x=s[D.YEAR], y=s[D.TOTAL], name=p, marker_color=PROGRAM_COLORS[p],
                        hovertemplate=f"{p} %{{y:,}} คน<extra></extra>")
    fig.update_layout(barmode="stack", bargap=0.3, hovermode="x unified")
    _year_axis(fig, df[D.YEAR])
    return style(fig, title, subtitle, height=380)


def heatmap(df: pd.DataFrame, title: str, subtitle: str = "") -> go.Figure:
    if df.empty:
        return empty_figure()
    p = df.pivot_table(index=D.DEPT, columns=D.YEAR, values=D.TOTAL, aggfunc="sum")
    p = p.loc[p.sum(axis=1).sort_values().index]
    fig = go.Figure(go.Heatmap(z=p.values, x=[str(c) for c in p.columns], y=p.index,
                               colorscale=[[0, "#EEF4FE"], [0.5, "#7FAEF2"], [1, "#0E3F99"]],
                               text=p.values, texttemplate="%{text:,}", textfont=dict(size=11),
                               hovertemplate="%{y} ปี %{x}<br>%{z:,} คน<extra></extra>",
                               colorbar=dict(thickness=10, outlinewidth=0, tickformat=",")))
    fig.update_xaxes(showgrid=False, type="category")
    fig.update_yaxes(showgrid=False)
    return style(fig, title, subtitle, height=440, legend=False)


def gender_scatter(df: pd.DataFrame, title: str, subtitle: str = "") -> go.Figure:
    if df.empty:
        return empty_figure()
    fig = go.Figure()
    for p in D.PROGRAM_ORDER:
        s = df[df[D.PROGRAM] == p]
        if s.empty:
            continue
        fig.add_scatter(x=s[D.MALE], y=s[D.FEMALE], name=p, mode="markers",
                        marker=dict(color=PROGRAM_COLORS[p], size=8, opacity=0.75, line=dict(width=0)),
                        customdata=np.stack([s[D.YEAR], s[D.LEVEL], s[D.DEPT]], axis=-1),
                        hovertemplate="%{customdata[2]} · %{customdata[1]} · ปี %{customdata[0]}"
                                      "<br>ชาย %{x:,} · หญิง %{y:,}<extra></extra>")
    fig.update_xaxes(title_text="นักเรียนชาย (คน)")
    fig.update_yaxes(title_text="นักเรียนหญิง (คน)")
    return style(fig, title, subtitle, height=380)


# ---------------------------------------------------------------- forecast --
def forecast_chart(years, values, fut_years, fut_vals, band: float, method: str,
                   title: str, subtitle: str = "", fitted=None) -> go.Figure:
    if len(years) == 0:
        return empty_figure()
    fig = go.Figure()
    if len(fut_years) and band > 0:
        bx = [years[-1], *fut_years]
        upper = [values[-1], *(np.asarray(fut_vals) + 1.96 * band)]
        lower = [values[-1], *(np.asarray(fut_vals) - 1.96 * band)]
        fig.add_scatter(x=bx + bx[::-1], y=upper + lower[::-1], fill="toself", mode="lines",
                        fillcolor="rgba(240,140,46,0.12)", line=dict(width=0), hoverinfo="skip",
                        name="ช่วงความเชื่อมั่น ~95%")
    if fitted is not None:
        fig.add_scatter(x=years, y=fitted, name=method, mode="lines",
                        line=dict(color="#B7C3D7", width=1.5, dash="dot"), hoverinfo="skip")
    fig.add_scatter(x=years, y=values, name="ข้อมูลจริง", mode="lines+markers",
                    line=dict(color=TOKENS["accent"], width=3),
                    marker=dict(size=7, color="#fff", line=dict(width=2, color=TOKENS["accent"])),
                    hovertemplate="ปี %{x}: %{y:,.0f} คน<extra>ข้อมูลจริง</extra>")
    if len(fut_years):
        fig.add_scatter(x=[years[-1], *fut_years], y=[values[-1], *fut_vals], name="คาดการณ์",
                        mode="lines+markers", line=dict(color=TOKENS["palette"][1], width=3, dash="dash"),
                        marker=dict(size=8, symbol="diamond", color=TOKENS["palette"][1]),
                        hovertemplate="ปี %{x}: %{y:,.0f} คน<extra>คาดการณ์</extra>")
        fig.add_vrect(x0=years[-1], x1=fut_years[-1] + 0.3, fillcolor="#F6F8FB", line_width=0, layer="below")
        fig.add_annotation(x=(years[-1] + fut_years[-1]) / 2, y=1.0, yref="paper", text="ช่วงคาดการณ์",
                           showarrow=False, font=dict(size=11, color=INK))
    _year_axis(fig, list(years) + list(fut_years))
    return style(fig, title, subtitle, height=400)


def waterfall(base: float, steps: list[tuple[str, float]], final: float, title: str, subtitle: str = "") -> go.Figure:
    labels = ["ฐานคาดการณ์", *[s[0] for s in steps], "ผลจำลอง"]
    vals = [base, *[s[1] for s in steps], final]
    measure = ["absolute", *["relative"] * len(steps), "total"]
    fig = go.Figure(go.Waterfall(
        x=labels, y=vals, measure=measure, text=[(f"{v:+,.0f}" if abs(v) >= 0.5 else "0") if m == "relative"
                                                 else f"{v:,.0f}"
                                                 for v, m in zip(vals, measure)],
        textposition="outside", cliponaxis=False,
        connector=dict(line=dict(color="#C8D1DF", width=1)),
        increasing=dict(marker=dict(color=TOKENS["positive"])),
        decreasing=dict(marker=dict(color=TOKENS["negative"])),
        totals=dict(marker=dict(color=TOKENS["navy"])),
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>"))
    levels, cum = [base], base
    for _, v in steps:
        cum += v
        levels.append(cum)
    lo, hi = min(levels + [final]), max(levels + [final])
    pad = max((hi - lo) * 0.35, hi * 0.03)
    fig.update_yaxes(range=[lo - pad, hi + pad])
    fig.update_layout(waterfallgap=0.45)
    return style(fig, title, subtitle, height=380, legend=False)


def retention_lines(r: pd.DataFrame, title: str, subtitle: str = "") -> go.Figure:
    if r.empty:
        return empty_figure()
    fig = go.Figure()
    colors = [TOKENS["palette"][i] for i in (0, 2, 1, 3)]
    for c, (step, s) in zip(colors, r.groupby("ขั้น", sort=False)):
        fig.add_scatter(x=s["ปีเริ่ม"], y=s["อัตรา"], name=step, mode="lines+markers",
                        line=dict(color=c, width=2.5), marker=dict(size=6),
                        hovertemplate=f"{step} รุ่นปี %{{x}}: %{{y:.1%}}<extra></extra>")
    _year_axis(fig, r["ปีเริ่ม"])
    fig.update_layout(hovermode="x unified")
    fig = style(fig, title, subtitle, height=360)
    fig.add_hline(y=0.9, line=dict(color="#9AA8BF", width=1, dash="dot"),
                  annotation_text="เกณฑ์ 90%", annotation_position="bottom right",
                  annotation_font=dict(size=11, color=INK))
    fig.update_yaxes(tickformat=".0%")
    return fig
