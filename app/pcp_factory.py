<<<<<<< codex/show-git-remote-urls-3hsi8o
=======
<<<<<<< codex/show-git-remote-urls-arbjl7
>>>>>>> main
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path


_VERSIONED_PCP_FILE = re.compile(r"^pcp_v(\d+)(?:_(\d+))?\.py$", re.IGNORECASE)


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []

    env = os.environ.get("COMMISSION_PRO_PATH", "").strip()
    if env:
        roots.append(Path(env).expanduser().resolve())

    quote_repo = Path(__file__).resolve().parents[1]
    for name in ("CommissionPro", "PearsonCommissioningPro", "PearsonCommissionPro"):
        roots.append((quote_repo.parent / name).resolve())

    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            deduped.append(root)
            seen.add(key)
    return deduped


def _version_key(path: Path) -> tuple[int, int]:
    match = _VERSIONED_PCP_FILE.match(path.name)
    if not match:
        return (-1, -1)
    major = int(match.group(1) or 0)
    minor = int(match.group(2) or 0)
    return (major, minor)


def _find_latest_pcp_module_file() -> tuple[Path, Path]:
    errors: list[str] = []

    for root in _candidate_roots():
        legacy_dir = root / "legacy_pcp"
        if not legacy_dir.exists():
            errors.append(f"- {root}: missing legacy_pcp directory")
            continue

        candidates = [
            p for p in legacy_dir.glob("pcp_v*.py") if _VERSIONED_PCP_FILE.match(p.name)
        ]
        if not candidates:
            errors.append(f"- {legacy_dir}: no pcp_v*.py files found")
            continue

        module_file = sorted(candidates, key=_version_key, reverse=True)[0]
        return root, module_file

    details = "\n".join(errors) if errors else "- no candidate roots available"
    raise RuntimeError(
        "Unable to locate CommissionPro source repo with a versioned PCP module.\n"
        "Set COMMISSION_PRO_PATH to your CommissionPro checkout.\n"
        f"Searched:\n{details}"
    )


def _load_module_from_file(module_path: Path):
    import hashlib
    digest = hashlib.sha1(str(module_path).encode("utf-8")).hexdigest()[:12]
    unique_name = f"commissionpro_runtime_{module_path.stem}_{digest}"
    spec = importlib.util.spec_from_file_location(unique_name, str(module_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec for {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


def create_pcp_main_window():
    _, module_file = _find_latest_pcp_module_file()
    module = _load_module_from_file(module_file)

    pcp_cls = getattr(module, "PCPMainWindow", None) or getattr(module, "MainWindow", None)
    if pcp_cls is None:
        raise RuntimeError(
            f"{module_file} loaded but did not expose PCPMainWindow/MainWindow class."
        )
    return pcp_cls()
<<<<<<< codex/show-git-remote-urls-3hsi8o
=======
=======
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
>>>>>>> main
>>>>>>> main
