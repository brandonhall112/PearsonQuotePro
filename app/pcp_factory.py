"""Factory for loading the CommissionPro PCPMainWindow class."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Type


def _ensure_commissionpro_path() -> None:
    repo_path = os.environ.get("COMMISSIONPRO_REPO_PATH", "").strip()
    if not repo_path:
        return

    resolved = str(Path(repo_path).resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def get_pcp_main_window_class() -> Type:
    """Load PCPMainWindow from CommissionPro, with local fallback."""
    _ensure_commissionpro_path()

    candidate_modules = (
        "pcp_v1_1",
        "legacy_pcp.pcp_v1_1",
        "CommissionPro.legacy_pcp.pcp_v1_1",
    )

    for module_name in candidate_modules:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue

        pcp_main_window = getattr(module, "PCPMainWindow", None)
        if pcp_main_window is not None:
            return pcp_main_window

    from legacy_pcp.pcp_v1_1 import PCPMainWindow

    return PCPMainWindow
