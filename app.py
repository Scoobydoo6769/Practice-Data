"""Entry point: page config, theme, sidebar navigation. Run with `streamlit run app.py`."""
import streamlit as st

from auth import logout, require_login
from theme import APP_TITLE, INSTITUTION_NAME, inject_theme, sidebar_brand

st.set_page_config(page_title=f"{APP_TITLE} · {INSTITUTION_NAME}", page_icon=":material/school:",
                   layout="wide", initial_sidebar_state="auto")
inject_theme()
require_login()  # shows the login page and stops until signed in

SECTIONS = {
    "แดชบอร์ด": [
        st.Page("views/overview.py", title="ภาพรวมผู้บริหาร", icon=":material/space_dashboard:", default=True),
    ],
    "ข้อมูล": [
        st.Page("views/audit.py", title="คุณภาพข้อมูล & Audit Log", icon=":material/fact_check:"),
        st.Page("views/explorer.py", title="สำรวจข้อมูลเชิงลึก", icon=":material/query_stats:"),
    ],
    "วางแผน": [
        st.Page("views/forecast.py", title="คาดการณ์ & What-If", icon=":material/insights:"),
        st.Page("views/actions.py", title="แผนปฏิบัติเชิงกลยุทธ์", icon=":material/flag:"),
    ],
}
page = st.navigation(SECTIONS, position="hidden")

# Own sidebar menu so the brand sits above it and page filters follow below.
with st.sidebar:
    sidebar_brand()
    for label, items in SECTIONS.items():
        st.html(f"<div class='nav-label'>{label}</div>")
        for p in items:
            st.page_link(p, width="stretch")
    st.divider()
    st.button("ออกจากระบบ", key="logout", on_click=logout, icon=":material/logout:", width="stretch")

page.run()
