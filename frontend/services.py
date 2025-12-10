"""Service locators and integrations."""

from __future__ import annotations

import streamlit as st

from sorawm.core_entry import get_cleaner


@st.cache_resource
def get_sora_wm():
    """Lazily initialize the watermark cleaner (no levels)."""
    return get_cleaner()


__all__ = ["get_sora_wm"]
