"""
root main.py — AuraGenesis launcher

Run from repo root:
    python main.py

All source code lives in the AuraGenesis/ subfolder.
This launcher sets the working directory there so all
relative imports and file paths resolve correctly.
"""
import sys
import os
from pathlib import Path

# The real package lives here
pkg = Path(__file__).parent / "AuraGenesis"

# Change working directory so relative paths (logs/, config/, etc.) work
os.chdir(pkg)

# Make AuraGenesis/ the top of the import path
sys.path.insert(0, str(pkg))

if __name__ == "__main__":
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", pkg / "main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.awaken_aura()
