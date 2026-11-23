"""Simple login gate. Call require_login() before drawing any page.

Default account: admin / dashboard. To change it without editing code, add this to
.streamlit/secrets.toml (or the Streamlit Cloud secrets box):

    [auth]
    username = "..."
    password = "..."

This is a demo-level gate (one shared account, session-based), not a substitute for real user management.
"""
from __future__ import annotations

import hmac
import time

import streamlit as st

import theme as T

DEFAULT_USER, DEFAULT_PASSWORD = "admin", "dashboard"
MAX_TRIES, LOCK_SECONDS = 5, 30


def _credentials() -> tuple[str, str]:
    try:
        a = st.secrets["auth"]
        return str(a["username"]), str(a["password"])
    except (KeyError, FileNotFoundError, st.errors.StreamlitAPIException):
        return DEFAULT_USER, DEFAULT_PASSWORD


def _same(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())


def logout() -> None:
    st.session_state["authed"] = False
    st.session_state["login_fails"] = 0


def require_login() -> None:
    """Show the login page and stop the script until the user signs in."""
    if st.session_state.get("authed"):
        return

    st.html("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl'],"
            "[data-testid='stExpandSidebarButton']{display:none}"
            ".st-key-card-login{max-width:420px;margin:7vh auto 0;padding:1.6rem 1.8rem 1.4rem}"
            ".login-head{text-align:center;margin-bottom:1rem}"
            ".login-head img{margin:0 auto .8rem}"
            ".login-head .t{font-weight:700;color:var(--navy);font-size:1.25rem;line-height:1.35}"
            ".login-head .s{color:var(--muted);font-size:.88rem;margin-top:.2rem}</style>")

    fails = st.session_state.get("login_fails", 0)
    locked_until = st.session_state.get("login_locked_until", 0.0)
    locked = time.time() < locked_until

    with st.container(key="card-login"):
        st.html(f"<div class='login-head'>{T._logo_html(84)}"
                f"<div class='t'>{T.esc(T.INSTITUTION_NAME)}</div>"
                f"<div class='s'>{T.esc(T.APP_TITLE)} · กรุณาเข้าสู่ระบบ</div></div>")
        with st.form("login_form", border=False):
            user = st.text_input("ชื่อผู้ใช้", key="login_user", autocomplete="username")
            pw = st.text_input("รหัสผ่าน", type="password", key="login_pass", autocomplete="current-password")
            go = st.form_submit_button("เข้าสู่ระบบ", type="primary", width="stretch",
                                       icon=":material/login:", disabled=locked)
        if locked:
            st.warning(f"ลองผิดหลายครั้ง กรุณารอ {int(locked_until - time.time()) + 1} วินาทีแล้วลองใหม่")
        elif go:
            ok_user, ok_pw = _credentials()
            # evaluate both so timing doesn't reveal which field was wrong
            good = _same(user.strip(), ok_user) & _same(pw, ok_pw)
            if good:
                st.session_state["authed"] = True
                st.session_state["login_fails"] = 0
                st.rerun()
            fails += 1
            st.session_state["login_fails"] = fails
            if fails >= MAX_TRIES:
                st.session_state["login_locked_until"] = time.time() + LOCK_SECONDS
                st.session_state["login_fails"] = 0
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    st.stop()
