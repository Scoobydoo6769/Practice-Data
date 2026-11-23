# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python + Streamlit, Plotly for every chart, pandas/openpyxl for the Excel source. Chosen by the user. Entry point is `app.py` in this folder.

## Users

Primary: judges of a data-analysis skills competition. They open the site on a laptop or projector, have a few minutes per team, and must judge whether the team understood the data, cleaned it with care, and can turn it into decisions. Secondary: vocational-college administrators who plan enrolment.

## Product Purpose

A "Decision Intelligence Portal" over 10 years (ปีการศึกษา 2560–2569) of student headcounts at a Thai vocational college. It covers ten departments, levels ปวช.1–3, ปวส.1–2, ป.ตรี (from 2567), and ตกค้าง, split by gender. Success means a judge can understand the story in 10 seconds, verify the cleaning, explore the data, try what-if scenarios, and read concrete recommendations.

## Positioning

Not a chart gallery. It follows an analyst's sequence of overview → data audit → explorer → forecast/what-if → action plan. Insights come from the real numbers, such as the cohort pass-through between levels.

## Operating Context

Judging session at a competition, often on a projector or a 13–15" laptop. The site must run locally and on Streamlit Community Cloud without failing in front of the judges.

## Capabilities and Constraints

- Source data: 10 cleaned Excel files `Competition_Dataset_2560.xlsx` … `_2569.xlsx`, 630 rows (60 per year, 70 from 2567), 6 columns. The raw pre-cleaning files were not supplied.
- Five modules required by the competition brief: Executive Overview, Data Cleansing & Audit Log, Deep-Dive Explorer, Predictive & What-If Simulator, Strategic Action Plan.
- All chart titles are in Thai and phrase a finding, not a variable name.
- Institution name: วิทยาลัยเทคนิคสุราษฎร์ธานี (confirmed by user).

## Brand Commitments

From the competition guideline: 60-30-10 colour discipline (light clean ground, navy/slate theme colour, one accent). Red and green are reserved for data meaning (up/down, pass/fail). No rainbow charts. Layout follows the user's reference dashboard: left navigation, KPI cards stacked beside the main trend chart, a bar panel and a donut panel below.

## Evidence on Hand

Real data only, from the 10 Excel files. Root causes in the action plan are hypotheses and must be labelled as such. No invented school name, survey results, or budgets.

## Product Principles

1. Every number traces back to the data, and every inference is labelled.
2. The headline finding comes first, and detail comes on demand.
3. Show the cleaning work openly; transparency is a feature.
4. Nothing breaks in front of judges: empty filters and odd selections degrade gracefully.
