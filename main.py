"""
root main.py — AuraGenesis launcher

Run from repo root:
    python main.py

This file simply sets up the Python path so the AuraGenesis
package is importable, then delegates to AuraGenesis/main.py.
"""
import sys
from pathlib import Path

# Make AuraGenesis/ package importable from repo root
root = Path(__file__).parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "AuraGenesis"))

if __name__ == "__main__":
    # Import and run the real entrypoint
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "main", root / "AuraGenesis" / "main.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.awaken_aura()
