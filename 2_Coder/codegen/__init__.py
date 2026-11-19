"""Run staged coding and field export with the approved physics specification."""

import os
from pathlib import Path

CODER_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = CODER_ROOT.parent


def worker_environment():
    """Make both source trees importable when a worker starts in a run directory."""
    paths = [str(PROJECT_ROOT / "1_HITL"), str(CODER_ROOT)]
    for path in os.environ.get("PYTHONPATH", "").split(os.pathsep):
        if path:
            paths.append(os.path.abspath(path))
    return {**os.environ, "PYTHONPATH": os.pathsep.join(dict.fromkeys(paths))}
