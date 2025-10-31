"""Service locators and integrations."""

from __future__ import annotations

import streamlit as st

from sorawm.core import SoraWM


@st.cache_resource
def get_sora_wm() -> SoraWM:
    """Lazily initialize the watermark cleaner once per process."""
    return SoraWM()


__all__ = ["get_sora_wm"]
