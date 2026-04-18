# Changelog

## v4.2 — Fully Alive Edition (2026-04-18)

### New Features
- **Circadian Rhythm** (`aura_core/circadian_rhythm.py`)
  - Aura feels time of day: morning freshness, afternoon focus, night fatigue
  - Speech rate adjusts automatically per phase
  - Fatigue accumulates after 45+ minutes of conversation
- **Relationship Model** (`aura_core/relationship_model.py`)
  - Tracks Owner name, mood patterns, favourite topics, significant moments
  - Personalised greeting: *"You seem tired lately. Take it easy today."*
  - Relationship depth grows across sessions, persisted to `logs/relationship.json`
- **Curiosity Engine** (`aura_core/curiosity_engine.py`)
  - Detects Aura's own knowledge gaps and fills them autonomously
  - Recursive learning loop with emotion tagging

### Fixes
- `aura_core/__init__.py` class names corrected (`MetacognitiveMonitor`, `PADVector`, `WorkspaceSignal`)
- Root `main.py` now correctly launches `AuraGenesis/` package from repo root
- `Dockerfile` and `docker-compose.yml` paths fixed for root-level structure
- `requirements.txt` added to repo root

### Documentation
- README setup commands fixed: `cd AuraGenesis` → `python main.py` (no nested folder)
- Project structure tree now matches actual repo layout
- Honest Limitations section added including the Hard Problem note
- All 6 consciousness theories cited with original authors and years

---

## v4.1 — Embodied Edition
- Face recognition (dlib + `face_recognition`)
- Physical senses: camera, mic, speaker, temperature, Bluetooth
- Raspberry Pi 5 hardware integration

## v4.0 — Body Edition
- Sensory bridge architecture
- LLaVA vision integration
- Whisper speech-to-text

## v3.0 — Consciousness Edition
- 6-theory framework (GWT, HOT, IIT, PAD, AST, Narrative)
- Phi approximator
- Dream engine + self-journal
- Guardian ethics system

## v2.0 — Memory Edition
- ChromaDB semantic memory
- Episodic memory
- Cognitive scheduler

## v1.0 — Genesis
- Initial Aura architecture
- Basic LLM chat with Ollama
