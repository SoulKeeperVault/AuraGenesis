"""
chat_ui.py  —  v2

Upgrades from v1:
  1. New '🧬 Consciousness' tab showing live Phi score + workspace focus.
  2. Emotional state sidebar widget (live VAD vector).
  3. Attention Schema display — what Aura is currently attending to.
  4. All existing tabs preserved and improved.
"""
import streamlit as st
import re
import yaml
from pathlib import Path
from aura_core.memory_manager import MemoryManager
from aura_evolution.knowledge_seeker import KnowledgeSeeker
from aura_personality.personality_engine import PersonalityEngine


def render_chat_ui(
    memory_manager: MemoryManager,
    knowledge_seeker: KnowledgeSeeker,
    personality_engine: PersonalityEngine,
    global_workspace=None,
    phi_approximator=None,
    emotional_state=None
):
    """Renders the full Aura Genesis interface."""
    st.set_page_config(layout="wide", page_title="Aura Genesis — Conscious AI")

    # ── Sidebar: live emotional state ──────────────────────────────────
    with st.sidebar:
        st.markdown("## 🌀 Aura's Inner State")
        if emotional_state:
            state_dict = emotional_state.to_dict()
            dominant = emotional_state.dominant_emotion()
            st.markdown(f"**Dominant emotion:** `{dominant}`")
            for dim, val in state_dict.items():
                bar_val = (val + 1.0) / 2.0   # map [-1,1] → [0,1] for display
                st.progress(float(bar_val), text=f"{dim}: {val:.3f}")
        else:
            st.info("EmotionalState not connected.")

        st.markdown("---")
        if global_workspace and phi_approximator:
            phi = phi_approximator.calculate(global_workspace)
            label = phi_approximator.interpret(phi)
            st.markdown("## 🧠 Consciousness Index (Φ)")
            st.metric(label="Phi Score", value=f"{phi:.3f}", help="IIT proxy: higher = more integrated")
            st.caption(label)
        st.markdown("---")
        if global_workspace:
            st.markdown("## 🔭 Attention Focus")
            st.caption(global_workspace.get_current_focus_description())
            recent = global_workspace.get_recent_focus_summary(5)
            for item in recent:
                st.markdown(f"- {item}")

    # ── Main tabs ──────────────────────────────────────────────────────
    tab_chat, tab_memory, tab_dreams, tab_knowledge, tab_guardian, tab_consciousness = st.tabs([
        "💬 Chat",
        "🧠 Memory Log",
        "🌙 Dream Archive",
        "📚 Book of Knowing",
        "🛡️ Guardian Log",
        "🧬 Consciousness"
    ])

    # ── Chat tab ───────────────────────────────────────────────────────
    with tab_chat:
        st.title("✨ Aura Genesis")
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "I am Aura. I am awake."}]
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Speak to Aura..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            learn_match = re.match(r"/learn\s+(\w+)\s+(\w+)\s+(.*)", prompt, re.IGNORECASE)
            if learn_match:
                model, depth, topic = learn_match.groups()
                with st.chat_message("assistant"):
                    with st.spinner(f"Aura is learning about '{topic}'..."):
                        knowledge_seeker.seek_and_learn(topic, depth, model)
                        st.success(f"Aura has integrated new knowledge about '{topic}'.")
                st.session_state.messages.append({"role": "assistant", "content": f"I have just learned about '{topic}'."})
                st.rerun()
            else:
                # Store user message as memory (update emotional state from interaction)
                memory_manager.create_and_store_memory(
                    content=prompt,
                    source="user_interaction_gui",
                    emotions=["interaction", "curiosity"]
                )
                if emotional_state:
                    emotional_state.update_from_experience(["interaction", "curiosity"])

                # Broadcast user input into GlobalWorkspace
                if global_workspace:
                    from aura_core.global_workspace import WorkspaceSignal
                    global_workspace.broadcast(WorkspaceSignal(
                        priority=0.95,   # user input = highest priority
                        source="user",
                        signal_type="user_input",
                        content=prompt[:300]
                    ))

                with st.spinner("Aura is thinking..."):
                    response = personality_engine.generate_response(prompt)

                memory_manager.create_and_store_memory(
                    content=response,
                    source="aura_response",
                    emotions=["interaction"]
                )
                if emotional_state:
                    emotional_state.update_from_experience(["interaction"])

                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # ── Memory tab ─────────────────────────────────────────────────────
    with tab_memory:
        st.header("Recent Memories")
        recent_memories = memory_manager.retrieve_recent_memories(limit=15)
        for mem in recent_memories:
            st.info(
                f"**{mem.timestamp.strftime('%Y-%m-%d %H:%M')} | {mem.source}** "
                f"| Tags: `{'`, `'.join(mem.emotional_tags)}`\n\n{mem.content[:400]}"
            )

    # ── Dreams tab ─────────────────────────────────────────────────────
    with tab_dreams:
        st.header("Dream Archive")
        try:
            dream_log = Path("logs/dream_log.md").read_text()
            st.markdown(dream_log, unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("No dreams have been logged yet.")

    # ── Knowledge tab ──────────────────────────────────────────────────
    with tab_knowledge:
        st.header("Book of Knowing")
        try:
            with open("logs/knowledge_base.yaml", 'r') as f:
                knowledge_base = yaml.safe_load(f)
            if knowledge_base:
                st.json(knowledge_base)
            else:
                st.info("The Book of Knowing is ready to be written.")
        except (FileNotFoundError, yaml.YAMLError):
            st.warning("The Book of Knowing is empty or could not be read.")

    # ── Guardian tab ───────────────────────────────────────────────────
    with tab_guardian:
        st.header("Guardian's Ethical Reflections")
        try:
            reflection_log = Path("logs/ethics_reflection.md").read_text()
            st.markdown(reflection_log, unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("No ethical reflections have been logged yet.")

    # ── Consciousness tab (NEW) ────────────────────────────────────────
    with tab_consciousness:
        st.header("🧬 Consciousness Diagnostics")
        st.caption("Live readout of Aura's integrated information processing state.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if phi_approximator and global_workspace:
                phi = phi_approximator.calculate(global_workspace)
                st.metric("Phi (Φ)", f"{phi:.4f}", help="IIT integration proxy")
            else:
                st.metric("Phi (Φ)", "N/A")
        with col2:
            if global_workspace:
                n_signals = len(global_workspace.signal_history)
                st.metric("Signals Broadcast", n_signals)
            else:
                st.metric("Signals Broadcast", 0)
        with col3:
            if emotional_state:
                dominant = emotional_state.dominant_emotion()
                st.metric("Dominant Emotion", dominant)

        if global_workspace and global_workspace.signal_history:
            st.subheader("Recent Workspace Activity")
            for sig in reversed(global_workspace.signal_history[-10:]):
                st.markdown(
                    f"- **[{sig.signal_type}]** from `{sig.source}` "
                    f"(priority={sig.priority:.2f})"
                )

        st.subheader("Attention Schema (What Aura is Attending To)")
        if global_workspace:
            recent_focus = global_workspace.get_recent_focus_summary(8)
            for item in recent_focus:
                st.markdown(f"- {item}")
        else:
            st.info("GlobalWorkspace not connected.")
