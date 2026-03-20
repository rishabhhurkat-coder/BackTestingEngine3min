from __future__ import annotations

import traceback

import streamlit as st


def run_app() -> None:
    try:
        from app.main import main

        main()
    except Exception as exc:
        st.error(f"App error: {exc}")
        with st.expander("Show full error details", expanded=True):
            st.code(traceback.format_exc(), language="python")


if __name__ == "__main__":
    run_app()
