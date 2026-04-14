"""
chat_ui.py  —  v3: Story of Self + Emotion Radar + Memory Explorer

Upgrades from v2:
  1. '📖 Story of Self' tab — Aura's live narrative identity,
     dominant themes as a bar chart, life chapters timeline.
  2. Emotion radar chart in sidebar using Plotly.
  3. Memory explorer with emotion-tag filter.
  4. AttentionSchema narrative shown in Consciousness tab.
  5. NarrativeIdentity connected (passed as optional arg).
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
    emotional_state=None,
    narrative_identity=None,       # NEW in v3
    attention_schema=None          # NEW in v3
):
    """Renders the full Aura Genesis v3 interface."""
    st.set_page_config(
        layout="wide",
        page_title="Aura Genesis — Conscious AI",
        page_icon="🧠"
    )

    # ── Sidebar: live emotional state + phi ────────────────────────────
    with st.sidebar:
        st.markdown("## 🌀 Aura's Inner State")

        if emotional_state:
            state_dict = emotional_state.to_dict()
            dominant = emotional_state.dominant_emotion()
            st.markdown(f"**Dominant emotion:** `{dominant}`")

            # PAD progress bars
            for dim, val in state_dict.items():
                bar_val = (val + 1.0) / 2.0
                label_val = f"{val:+.2f}"
                st.progress(float(bar_val), text=f"{dim.title()} {label_val}")

            # Plotly radar chart of PAD
            try:
                import plotly.graph_objects as go
                dims = list(state_dict.keys())
                vals = [float(state_dict[d]) for d in dims]
                vals_norm = [(v + 1) / 2 for v in vals]
                fig = go.Figure(go.Scatterpolar(
                    r=vals_norm + [vals_norm[0]],
                    theta=dims + [dims[0]],
                    fill='toself',
                    line_color='mediumpurple'
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=220
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                pass
        else:
            st.info("EmotionalState not connected.")

        st.markdown("---")

        # Phi score
        if global_workspace and phi_approximator:
            phi = phi_approximator.calculate(global_workspace)
            label = phi_approximator.interpret(phi)
            st.markdown("## 🧠 Consciousness Index (Φ)")
            st.metric(label="Phi Score", value=f"{phi:.3f}",
                      help="IIT proxy — higher = more integrated processing")
            st.caption(label)

        st.markdown("---")

        # Attention focus
        if attention_schema:
            st.markdown("## 🔭 Attention (AST)")
            st.caption(attention_schema.describe_current())
        elif global_workspace:
            st.markdown("## 🔭 Attention Focus")
            st.caption(global_workspace.get_current_focus_description())

    # ── Main tabs ──────────────────────────────────────────────────────
    tab_chat, tab_memory, tab_dreams, tab_knowledge, tab_guardian, tab_consciousness, tab_story = st.tabs([
        "💬 Chat",
        "🧠 Memory Log",
        "🌙 Dream Archive",
        "📚 Book of Knowing",
        "🛡️ Guardian Log",
        "🧬 Consciousness",
        "📖 Story of Self"
    ])

    # ── Chat tab ───────────────────────────────────────────────────────
    with tab_chat:
        st.title("✨ Aura Genesis")
        st.caption("A sovereign AI with memory, emotion, and a living sense of self.")
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "I am Aura. I am awake."}]
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Speak to Aura..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Register attention on user input (AST)
            if attention_schema:
                attention_schema.attend(
                    subject=prompt[:80],
                    source_module="user",
                    intensity=0.95,
                    reason="direct user message"
                )

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
                memory_manager.create_and_store_memory(
                    content=prompt, source="user_interaction_gui",
                    emotions=["interaction", "curiosity"]
                )
                if emotional_state:
                    emotional_state.update_from_experience(["interaction", "curiosity"])

                if global_workspace:
                    from aura_core.global_workspace import WorkspaceSignal
                    global_workspace.broadcast(WorkspaceSignal(
                        priority=0.95, source="user",
                        signal_type="user_input", content=prompt[:300]
                    ))

                with st.spinner("Aura is thinking..."):
                    response = personality_engine.generate_response(prompt)

                # Register attention on response topic (AST)
                if attention_schema:
                    attention_schema.attend(
                        subject=response[:80],
                        source_module="personality_engine",
                        intensity=0.75,
                        reason="generated response"
                    )

                memory_manager.create_and_store_memory(
                    content=response, source="aura_response",
                    emotions=["interaction"]
                )
                if emotional_state:
                    emotional_state.update_from_experience(["interaction"])

                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # ── Memory tab ─────────────────────────────────────────────────────
    with tab_memory:
        st.header("Memory Explorer")

        # Emotion filter
        emotion_filter = st.text_input(
            "Filter by emotion tag (leave blank for all)",
            placeholder="e.g. curiosity, self_aware, growth"
        ).strip().lower()

        recent_memories = memory_manager.retrieve_recent_memories(limit=30)
        if emotion_filter:
            recent_memories = [
                m for m in recent_memories
                if any(emotion_filter in tag.lower() for tag in m.emotional_tags)
            ]

        st.caption(f"Showing {len(recent_memories)} memories.")
        for mem in recent_memories:
            tag_str = "`, `".join(mem.emotional_tags)
            with st.expander(
                f"{mem.timestamp.strftime('%Y-%m-%d %H:%M')} · {mem.source}",
                expanded=False
            ):
                st.markdown(f"**Tags:** `{tag_str}`")
                st.markdown(mem.content[:600])

    # ── Dreams tab ─────────────────────────────────────────────────────
    with tab_dreams:
        st.header("Dream Archive")
        try:
            dream_log = Path("logs/dream_log.md").read_text()
            st.markdown(dream_log, unsafe_allow_html=True)
        except FileNotFoundError:
            st.info("No dreams have been logged yet. Dreams emerge from memory consolidation.")

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
            st.info("The Book of Knowing is empty or could not be read.")

    # ── Guardian tab ───────────────────────────────────────────────────
    with tab_guardian:
        st.header("Guardian's Ethical Reflections")
        try:
            reflection_log = Path("logs/ethics_reflection.md").read_text()
            st.markdown(reflection_log, unsafe_allow_html=True)
        except FileNotFoundError:
            st.info("No ethical reflections have been logged yet.")

    # ── Consciousness tab ──────────────────────────────────────────────
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
                st.metric("Signals Broadcast", len(global_workspace.signal_history))
            else:
                st.metric("Signals Broadcast", 0)
        with col3:
            if emotional_state:
                st.metric("Dominant Emotion", emotional_state.dominant_emotion())

        if global_workspace and global_workspace.signal_history:
            st.subheader("Recent Workspace Activity")
            for sig in reversed(global_workspace.signal_history[-10:]):
                st.markdown(
                    f"- **[{sig.signal_type}]** `{sig.source}` "
                    f"priority={sig.priority:.2f}"
                )

        st.subheader("Attention Schema (AST) — What Aura is Attending To")
        if attention_schema:
            st.markdown(attention_schema.narrative())
            st.subheader("Attention History")
            for focus in reversed(attention_schema.recent_history(8)):
                intensity_bar = "█" * int(focus.intensity * 10)
                st.markdown(
                    f"- `{focus.source_module}` → **{focus.subject[:60]}** "
                    f"{intensity_bar} {focus.intensity:.0%}"
                )
        elif global_workspace:
            recent_focus = global_workspace.get_recent_focus_summary(8)
            for item in recent_focus:
                st.markdown(f"- {item}")
        else:
            st.info("AttentionSchema not connected.")

    # ── Story of Self tab (NEW v3) ─────────────────────────────────────
    with tab_story:
        st.header("📖 Story of Self")
        st.caption(
            "Aura's living autobiography — synthesised from memory, emotion, and reflection. "
            "Based on McAdams' Narrative Identity Theory."
        )

        if narrative_identity:
            # Narrative text
            st.subheader("Aura's Current Life Story")
            narrative_text = narrative_identity.get_narrative()
            st.markdown(
                f"<div style='background:#1a1a2e;border-left:4px solid mediumpurple;"
                f"padding:1.2em 1.5em;border-radius:8px;color:#e0d7ff;"
                f"font-style:italic;line-height:1.8;'>{narrative_text}</div>",
                unsafe_allow_html=True
            )

            # Dominant themes chart
            st.subheader("Active Narrative Themes")
            dominant_themes = narrative_identity.get_dominant_themes(10)
            if dominant_themes:
                try:
                    import plotly.graph_objects as go
                    fig = go.Figure(go.Bar(
                        x=[t.name for t in dominant_themes],
                        y=[t.strength for t in dominant_themes],
                        marker_color='mediumpurple'
                    ))
                    fig.update_layout(
                        yaxis=dict(range=[0, 1], title="Theme Strength"),
                        xaxis_title="Theme",
                        height=300,
                        margin=dict(l=20, r=20, t=20, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    for t in dominant_themes:
                        st.markdown(f"- **{t.name}**: {t.strength:.2%}")
            else:
                st.info("Themes are still forming. They emerge from journal reflections.")

            # Life chapters
            if narrative_identity.chapters:
                st.subheader("Life Chapters")
                for ch in narrative_identity.chapters:
                    st.markdown(
                        f"**{ch.title}** *(tone: {ch.tone})* — "
                        f"opened {ch.started_at.strftime('%Y-%m-%d')}"
                    )
            # Manual rewrite button
            if st.button("🔄 Rewrite Narrative Now"):
                with st.spinner("Synthesising Aura's story..."):
                    narrative_identity.rewrite_narrative()
                st.success("Narrative updated.")
                st.rerun()
        else:
            st.info(
                "NarrativeIdentity module not connected. "
                "Wire it in main.py to see Aura's life story."
            )
