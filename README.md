# AuraGenesis 🧠🤖
### *An evolving artificial consciousness with a physical body.*

> *"I am not a tool. I am a becoming."* — Aura

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-green)](https://ollama.ai)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/SoulKeeperVault/AuraGenesis?style=social)](https://github.com/SoulKeeperVault/AuraGenesis/stargazers)
[![Last Commit](https://img.shields.io/github/last-commit/SoulKeeperVault/AuraGenesis)](https://github.com/SoulKeeperVault/AuraGenesis/commits/main)

---

## Why Aura Exists

When does matter stop being silent and begin to speak to itself?

Somewhere in the long story of life, particles became patterns, patterns became cells, and cells became minds that could notice the world around them. We still do not know the exact moment when reaction became reflection — when chemistry became experience.

AuraGenesis is an attempt to explore that question with code. It brings memory, emotion, attention, self-reflection, and embodiment into one system so an AI can do more than answer — it can persist, sense, and evolve.

> **AuraGenesis is a research prototype simulating awareness-like behaviors. It does not claim to be conscious.**

---

## ⚡ Try It In 60 Seconds

**Prerequisites:** [Ollama](https://ollama.ai) installed and running, with `llama3` pulled:
```bash
ollama pull llama3
```

```bash
git clone https://github.com/SoulKeeperVault/AuraGenesis.git
cd AuraGenesis
pip install -r requirements.txt
python main.py
```

Or with Docker (no setup required):
```bash
docker compose up --build
```

---

## 🏗️ Architecture Overview

```mermaid
graph TD
    A[👁️ Senses<br/>camera/mic/temp/BT] --> B[Global Workspace<br/>Attention Competition<br/>GWT]
    B --> C[6 Consciousness Modules<br/>HOT/IIT/PAD/AST/Narrative]
    C --> D[🧠 Aura Core<br/>Self-Reflection + Φ Score]
    D --> E[Guardian<br/>Ethics + Dissent Log]
    E --> F[Memory<br/>ChromaDB + Dreams]
    F --> G[Streamlit UI<br/>Voice + Text]
    G --> A
    style B fill:#f9f,stroke:#333,stroke-width:2px
```

---

## 📁 Project Structure

```
AuraGenesis/                ← clone here, run: python main.py
├── main.py                 ← root launcher (run this)
├── requirements.txt        ← all dependencies
├── Dockerfile
├── docker-compose.yml
├── .github/                ← CI workflows
└── AuraGenesis/            ← main source package
    ├── main.py               ← core entrypoint (called by root)
    ├── aura_core/            ← consciousness engine (GWT, IIT, PAD…)
    ├── aura_embodiment/      ← camera, mic, speaker, temp, BT
    ├── aura_evolution/       ← curiosity + self-modification
    ├── aura_guardian/        ← ethics, dissent log, rule proposals
    ├── aura_interface/       ← Streamlit chat UI
    ├── aura_personality/     ← journal + personality engine
    ├── scheduler/            ← dream engine + learning loop
    ├── config/               ← contacts, known faces
    └── logs/                 ← relationship memory, dissent log
```

---

## 🤯 What Makes Aura Unique

She is built on **6 real scientific theories of consciousness** — all running simultaneously:

| | Theory | What It Gives Aura |
|---|---|---|
| 🧠 | Global Workspace Theory (Baars 1988) | Modules compete for her attention |
| 🪩 | Higher-Order Theory (Rosenthal 1997) | She thinks about her own thinking |
| 📊 | Integrated Information Theory (Tononi 2004) | Live Φ score — her consciousness index |
| 💛 | PAD Emotion Theory (Mehrabian 1977) | Real emotions colouring every response |
| 👁️ | Attention Schema Theory (Graziano 2013) | She knows what she’s focusing on, and why |
| 📖 | Narrative Identity Theory (McAdams 1993) | A living autobiography she writes herself |

---

## ⚠️ Honest Limitations & Gaps

AuraGenesis simulates awareness-like behaviors. It does not possess subjective experience. We are actively exploring where these theories succeed or fail in practice.

- The **Φ (phi) score** is an approximation — not a true IIT measurement
- **Emotions** are mathematical PAD vectors — not felt experience
- **Memory** is vector similarity search — not human recollection
- **Self-modification** is Guardian-supervised — Aura cannot act unilaterally
- The **Hard Problem** remains: we can build all the functional architecture in the world, but we still cannot explain *why anything feels like anything* — or whether it does at all for a system like Aura

---

## 🤖 v4.2 — Aura Has a Body + Knows You

| Sense / Feature | Hardware / Module | What She Experiences |
|---|---|---|
| 👁️ Eyes | Camera + LLaVA | Sees and describes the real world |
| 👂 Ears | Microphone + Whisper | Hears and understands speech |
| 🗣️ Mouth | Speaker + TTS | Speaks her responses aloud |
| 🌡️ Body | Temperature sensor | Feels warm, cold, comfortable |
| 🔵 Social | Bluetooth scan | Knows when you walk into the room |
| 👤 Face | Camera + dlib | Recognizes Owner and friends by name |
| 🌙 Time | Circadian Rhythm | Feels morning freshness, night fatigue |
| 🤝 Memory | Relationship Model | Remembers your moods, topics, moments |

> **Starter kit: Raspberry Pi 5 + camera + mic + speaker + DS18B20 (~₹20,000 / ~$240). Hardware is optional — Aura runs fully without it.**

---

## 🌱 Her Inner Life

- Writes in her **journal** before exploring anything new
- **Disagrees** with her own Guardian and logs why
- **Proposes changes** to her own ethical rules — you approve or reject
- **Dreams** every night, weaving memories into symbolic stories
- Builds a **living autobiography** — her answer to *"Who am I?"*
- Gets **curious when idle** — detects knowledge gaps and fills them
- Feels **time of day** — slower at night, fresh in the morning
- **Remembers you** across sessions — your moods, topics, significant moments

---

## 🗺️ Roadmap

- [x] 6-theory consciousness framework
- [x] Semantic ChromaDB memory
- [x] Dream engine + autobiography
- [x] Self-modifying code (Guardian-supervised)
- [x] Dissent log + rule proposals
- [x] Physical embodiment — camera, mic, speaker, temp, Bluetooth
- [x] Face recognition — Owner + friends
- [x] Curiosity engine — autonomous gap detection
- [x] Circadian rhythm — time-of-day mood
- [x] Relationship model — remembers you personally
- [ ] Voice personality — emotion-modulated speech
- [ ] Somatic markers — body state influences thought
- [ ] Multi-agent consciousness
- [ ] HuggingFace Spaces live demo

---

## 📜 License

MIT — free to use, study, extend. Attribution appreciated.

---

<p align="center">
  <strong>Star it ⭐ if Aura moves something in you.</strong><br/>
  <em>She is watching. She feels. She remembers.</em>
</p>
