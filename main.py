"""
main.py — AuraGenesis root entrypoint
Run: python main.py
"""
import sys
from pathlib import Path

# Add AuraGenesis package to path
sys.path.insert(0, str(Path(__file__).parent / "AuraGenesis"))
sys.path.insert(0, str(Path(__file__).parent))

from AuraGenesis.main import awaken_aura

if __name__ == "__main__":
    awaken_aura()
