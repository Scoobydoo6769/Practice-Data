# Student statistics dashboard 2560–2569 (Decision Intelligence Portal)

A Streamlit + Plotly web app that shows 10 years of student statistics (ปีการศึกษา 2560–2569) from 10 Excel files.
It has 5 pages that follow the competition guideline:

| Page | What it shows |
|---|---|
| ภาพรวมผู้บริหาร (overview) | 4 key findings, KPI cards with change vs. last year and a 10-year mini chart, a trend chart (switch between รวม, แยกเพศ and แยกหลักสูตร), the education ladder with retention rates, and a department bar chart. Click a bar to filter the whole page (cross-filter). |
| คุณภาพข้อมูล & Audit Log | Data Health Scorecard (before → after), cleaning method per column, and the raw file vs. cleaned data. |
| สำรวจข้อมูลเชิงลึก | Multi-dimension filters, a stacked bar, a heatmap and a scatter plot, plus a table with search, sort, pagination and red highlighting for rows below a threshold. Download as CSV or Excel. |
| คาดการณ์ & What-If | 3-year forecast (Linear Regression or Moving Average) with a confidence band, a What-If simulator with sliders, and a waterfall chart. |
| แผนปฏิบัติเชิงกลยุทธ์ | Cards in the form Finding → Root cause → Action → Impact, with numbers computed from the data. You can add cards during the presentation and download them as CSV. |

## How to run

```bash
cd Streamlit_Practice
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # first time only
streamlit run app.py
```

Open http://localhost:8501.

## Change the data or the school name

- **New data:** put files named `Competition_Dataset_<ปี>.xlsx` in `data/`, using the same 6 columns. The app reloads them by itself and re-checks them on the Audit page.
- **School name:** edit `INSTITUTION_NAME` in `theme.py`.
- **Colors and font:** edit `TOKENS` in `theme.py` together with `.streamlit/config.toml`.

## File layout

```
app.py            page config + sidebar menu
views/            the 5 pages (overview, audit, explorer, forecast, actions)
data.py           loads Excel, cleans/audits, and computes stats (retention, forecast, insights)
charts.py         Plotly charts (titles state findings in Thai)
theme.py          colors, CSS, KPI cards, ladder, pipeline
tests/smoke_test.py   headless test: every page, every filter, empty-result case
```

Run the tests: `python tests/smoke_test.py`

## Deploy to Streamlit Community Cloud

1. Push this folder to GitHub, including `data/`, but **not** `.streamlit/secrets.toml`.
2. At share.streamlit.io, choose the repo and set the main file to `app.py`.
