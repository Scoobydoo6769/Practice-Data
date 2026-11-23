"""Headless smoke test: every page renders, every filter works, empty results and reset don't crash.

Run:  python tests/smoke_test.py   (or pytest tests/smoke_test.py)
"""
from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
PAGES = ["views/overview.py", "views/audit.py", "views/explorer.py", "views/forecast.py", "views/actions.py"]


def _app(page: str | None = None) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=90)
    at.session_state["authed"] = True  # skip the login page; test_login covers it
    at.run()
    if page:
        at.switch_page(page).run()
    return at


def _ok(at: AppTest, what: str) -> None:
    assert not at.exception, f"{what}: {at.exception}"


def test_login() -> None:
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    _ok(at, "login page")
    assert not at.session_state["authed"] if "authed" in at.session_state else True
    at.text_input(key="login_user").set_value("admin")
    at.text_input(key="login_pass").set_value("wrong")
    at.button[0].click().run()
    assert at.error, "wrong password should show an error"
    at.text_input(key="login_user").set_value("admin")
    at.text_input(key="login_pass").set_value("dashboard")
    at.button[0].click().run()
    _ok(at, "after login")
    assert at.session_state["authed"] is True


def test_every_page_renders() -> None:
    for p in PAGES:
        _ok(_app(p), p)


def test_overview_filters_and_views() -> None:
    at = _app()
    at.sidebar.select_slider(key="ov_years").set_value((2565, 2566)).run()
    _ok(at, "overview year range")
    at.sidebar.select_slider(key="ov_years").set_value((2569, 2569)).run()
    _ok(at, "overview single year")
    at.sidebar.button(key="reset_filters").click().run()
    _ok(at, "overview reset")


def test_explorer_filters_empty_and_reset() -> None:
    at = _app("views/explorer.py")
    for ms in at.sidebar.multiselect:
        ms.set_value([ms.options[0]]).run()
        _ok(at, f"multiselect {ms.label}")
    sl = at.sidebar.slider(key="f_total")
    lo, hi = sl.value
    sl.set_value((lo, (lo + hi) // 2)).run()
    _ok(at, "total slider")
    at.sidebar.multiselect(key="f_levels").set_value(["ป.ตรี"]).run()
    at.sidebar.select_slider(key="f_years").set_value((2560, 2561)).run()  # ป.ตรี starts 2567 -> empty
    _ok(at, "empty result")
    assert any("ไม่มีข้อมูล" in i.value for i in at.info), "empty-state message missing"
    at.sidebar.button(key="reset_filters").click().run()
    _ok(at, "explorer reset")
    at.text_input(key="f_search").set_value("ช่างยนต์ 2569").run()
    _ok(at, "search")
    at.text_input(key="f_search").set_value("zzz-no-match").run()
    _ok(at, "search no match")


def test_whatif_sliders() -> None:
    at = _app("views/forecast.py")
    for key, val in [("wi_intake", 20), ("wi_ret", 95.0), ("wi_rem", 30), ("wi_fem", 25.0)]:
        at.slider(key=key).set_value(val).run()
        _ok(at, key)
    at.button(key="wi_reset").click().run()
    _ok(at, "what-if reset")
    for opt in ["ปวช.", "ป.ตรี", "ตกค้าง"]:
        at.button_group(key="fc_series").set_value(opt).run() if hasattr(at, "button_group") else None
        _ok(at, f"series {opt}")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("All smoke tests passed.")
