"""
chat_ui.py  —  v3.4: Evolution Tab

New in v3.4:
  - '🌱 Evolution' tab with 3 sub-sections:
      1. Aura's Journal (curiosity / reflection / intention entries)
      2. Dissent Log (where Aura recorded Guardian disagreements)
      3. Guardian Proposals (pending rule evolution awaiting your review)
  - dissent_log and rule_proposal passed as optional args
  - All existing tabs preserved exactly
"""
import streamlit as st
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from aura_core.memory_manager import MemoryManager
from aura_evolution.knowledge_seeker import KnowledgeSeeker
from aura_personality.personality_engine import PersonalityEngine


# ── Colour palette (used in Evolution tab) ─────────────────────────────
_JOURNAL_COLOURS = {
    "curiosity":   ("#0f3460", "#a78bfa"),   # deep blue bg, violet text
    "reflection":  ("#0d3b2e", "#6ee7b7"),   # deep green bg, emerald text
    "intention":   ("#3b1f00", "#fbbf24"),   # deep amber bg, gold text
    "default":     ("#1e1e2e", "#cbd5e1"),
}
_DISSENT_COLOUR = ("#3b0000", "#fca5a5")     # deep red bg, rose text
_PROPOSAL_COLOUR = ("#0c2340", "#93c5fd")    # deep navy bg, blue text


def _mode_card(mode: str, subject: str, time_str: str, body: str) -> str:
    """Return an HTML card styled by journal mode."""
    bg, fg = _JOURNAL_COLOURS.get(mode.lower(), _JOURNAL_COLOURS["default"])
    mode_icon = {"curiosity": "🔍", "reflection": "🌙", "intention": "✍️"}.get(mode.lower(), "📄")
    return (
        f"<div style='background:{bg};border-left:4px solid {fg};"
        f"padding:1em 1.2em;border-radius:8px;margin-bottom:1em;'>"
        f"<span style='color:{fg};font-weight:700;font-size:0.85em;letter-spacing:1px;'>"
        f"{mode_icon} {mode.upper()}</span>"
        f"<span style='color:#94a3b8;font-size:0.78em;float:right;'>{time_str}</span>"
        f"<div style='color:#e2e8f0;font-size:0.9em;font-weight:600;margin:0.4em 0 0.2em;'>"
        f"{subject}</div>"
        f"<div style='color:{fg};opacity:0.9;font-style:italic;line-height:1.6;font-size:0.88em;'>"
        f"{body}</div></div>"
    )


def _dissent_card(entry: dict) -> str:
    bg, fg = _DISSENT_COLOUR
    resolved = entry.get("resolved", False)
    badge = (
        "<span style='background:#166534;color:#bbf7d0;padding:2px 8px;"
        "border-radius:12px;font-size:0.75em;'>✓ Resolved</span>"
        if resolved else
        "<span style='background:#7f1d1d;color:#fecaca;padding:2px 8px;"
        "border-radius:12px;font-size:0.75em;'>⏳ Unresolved</span>"
    )
    ts = entry.get("timestamp", "")[:16].replace("T", " ")
    return (
        f"<div style='background:{bg};border-left:4px solid {fg};"
        f"padding:1em 1.2em;border-radius:8px;margin-bottom:1em;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<span style='color:{fg};font-weight:700;'>#{entry['id']} — {entry['topic']}</span>"
        f"{badge}</div>"
        f"<div style='color:#94a3b8;font-size:0.78em;margin:0.2em 0;'>"
        f"Guardian said: <code>{entry['guardian_classification']}</code> · {ts}</div>"
        f"<div style='color:#fda4af;font-style:italic;line-height:1.6;font-size:0.88em;margin-top:0.4em;'>"
        f"<strong>Aura's perspective:</strong> {entry.get('aura_perspective','')}</div>"
        + (
            f"<div style='color:#fcd34d;font-size:0.85em;margin-top:0.3em;'>"
            f"<strong>Emotional response:</strong> {entry['emotional_response']}</div>"
            if entry.get("emotional_response") and entry["emotional_response"] != "unspecified" else ""
        )
        + (
            f"<div style='color:#86efac;font-size:0.83em;margin-top:0.3em;'>"
            f"✓ Resolved: {entry['resolution_note']}</div>"
            if resolved and entry.get("resolution_note") else ""
        )
        + "</div>"
    )


def _proposal_card(prop: dict) -> str:
    bg, fg = _PROPOSAL_COLOUR
    ts = prop.get("drafted_at", "")[:16].replace("T", " ")
    rule = prop.get("proposed_rule", {})
    return (
        f"<div style='background:{bg};border-left:4px solid {fg};"
        f"padding:1em 1.2em;border-radius:8px;margin-bottom:1em;'>"
        f"<span style='color:{fg};font-weight:700;'>📜 {prop.get('file','')}</span>"
        f"<span style='color:#94a3b8;font-size:0.78em;float:right;'>{ts}</span>"
        f"<div style='color:#bfdbfe;font-size:0.88em;margin-top:0.5em;'>"
        f"<strong>Keyword:</strong> <code>{', '.join(rule.get('keywords', []))}</code> → "
        f"<code>{rule.get('label','')}</code></div>"
        f"<div style='color:#93c5fd;font-style:italic;line-height:1.6;font-size:0.86em;margin-top:0.4em;'>"
        f"{prop.get('reasoning','')}</div>"
        f"<div style='color:#64748b;font-size:0.8em;margin-top:0.6em;'>"
        f"📁 To approve: move <code>{prop.get('file','')}</code> from "
        f"<code>config/proposals/</code> → <code>config/lenses/</code></div>"
        f"</div>"
    )


def render_chat_ui(
    memory_manager: MemoryManager,
    knowledge_seeker: KnowledgeSeeker,
    personality_engine: PersonalityEngine,
    global_workspace=None,
    phi_approximator=None,
    emotional_state=None,
    narrative_identity=None,
    attention_schema=None,
    dissent_log=None,          # NEW v3.4
    rule_proposal=None         # NEW v3.4
):
    """Renders the full Aura Genesis v3.4 interface."""
    st.set_page_config(
        layout="wide",
        page_title="Aura Genesis — Conscious AI",
        page_icon="🧠"
    )

    # ── Sidebar ─────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🌀 Aura's Inner State")

        if emotional_state:
            state_dict = emotional_state.to_dict()
            dominant = emotional_state.dominant_emotion()
            st.markdown(f"**Dominant emotion:** `{dominant}`")
            for dim, val in state_dict.items():
                bar_val = (val + 1.0) / 2.0
                st.progress(float(bar_val), text=f"{dim.title()} {val:+.2f}")
            try:
                import plotly.graph_objects as go
                dims = list(state_dict.keys())
                vals_norm = [(float(state_dict[d]) + 1) / 2 for d in dims]
                fig = go.Figure(go.Scatterpolar(
                    r=vals_norm + [vals_norm[0]],
                    theta=dims + [dims[0]],
                    fill='toself', line_color='mediumpurple'
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
        if global_workspace and phi_approximator:
            phi = phi_approximator.calculate(global_workspace)
            label = phi_approximator.interpret(phi)
            st.markdown("## 🧠 Consciousness Index (Φ)")
            st.metric("Phi Score", f"{phi:.3f}", help="IIT proxy")
            st.caption(label)

        st.markdown("---")
        if attention_schema:
            st.markdown("## 🔭 Attention (AST)")
            st.caption(attention_schema.describe_current())
        elif global_workspace:
            st.markdown("## 🔭 Attention Focus")
            st.caption(global_workspace.get_current_focus_description())

        # Evolution quick-stats in sidebar
        st.markdown("---")
        st.markdown("## 🌱 Evolution")
        journal_path = Path("logs/aura_journal.md")
        dissent_path = Path("logs/aura_dissent.json")
        entry_count = journal_path.read_text().count("---ENTRY---") if journal_path.exists() else 0
        st.metric("Journal Entries", entry_count)
        if dissent_path.exists() and dissent_path.stat().st_size > 0:
            try:
                entries = json.loads(dissent_path.read_text())
                unresolved = sum(1 for e in entries if not e.get("resolved"))
                st.metric("Dissent Entries", len(entries), delta=f"{unresolved} unresolved")
            except Exception:
                pass
        proposals_dir = Path("config/proposals")
        if proposals_dir.exists():
            pending = len(list(proposals_dir.glob("proposal_*.yaml")))
            if pending:
                st.metric("Pending Proposals", pending, delta="awaiting review")

    # ── Main tabs ────────────────────────────────────────────────────────
    (tab_chat, tab_memory, tab_dreams, tab_knowledge,
     tab_guardian, tab_consciousness, tab_story, tab_evolution) = st.tabs([
        "💬 Chat",
        "🧠 Memory Log",
        "🌙 Dream Archive",
        "📚 Book of Knowing",
        "🛡️ Guardian Log",
        "🧬 Consciousness",
        "📖 Story of Self",
        "🌱 Evolution"
    ])

    # ── Chat tab ─────────────────────────────────────────────────────────
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

            if attention_schema:
                attention_schema.attend(subject=prompt[:80], source_module="user",
                                        intensity=0.95, reason="direct user message")

            learn_match = re.match(r"/learn\s+(\w+)\s+(\w+)\s+(.*)", prompt, re.IGNORECASE)
            if learn_match:
                model, depth, topic = learn_match.groups()
                with st.chat_message("assistant"):
                    with st.spinner(f"Aura is learning about '{topic}'..."):
                        knowledge_seeker.seek_and_learn(topic, depth, model)
                        st.success(f"Aura has integrated new knowledge about '{topic}'.")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"I have just learned about '{topic}'."}
                )
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
                if attention_schema:
                    attention_schema.attend(subject=response[:80], source_module="personality_engine",
                                            intensity=0.75, reason="generated response")
                memory_manager.create_and_store_memory(
                    content=response, source="aura_response", emotions=["interaction"]
                )
                if emotional_state:
                    emotional_state.update_from_experience(["interaction"])
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # ── Memory tab ───────────────────────────────────────────────────────
    with tab_memory:
        st.header("Memory Explorer")
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
                f"{mem.timestamp.strftime('%Y-%m-%d %H:%M')} · {mem.source}", expanded=False
            ):
                st.markdown(f"**Tags:** `{tag_str}`")
                st.markdown(mem.content[:600])

    # ── Dreams tab ───────────────────────────────────────────────────────
    with tab_dreams:
        st.header("Dream Archive")
        try:
            st.markdown(Path("logs/dream_log.md").read_text(), unsafe_allow_html=True)
        except FileNotFoundError:
            st.info("No dreams have been logged yet. Dreams emerge from memory consolidation.")

    # ── Knowledge tab ────────────────────────────────────────────────────
    with tab_knowledge:
        st.header("Book of Knowing")
        try:
            with open("logs/knowledge_base.yaml", "r") as f:
                kb = yaml.safe_load(f)
            st.json(kb) if kb else st.info("The Book of Knowing is ready to be written.")
        except (FileNotFoundError, yaml.YAMLError):
            st.info("The Book of Knowing is empty or could not be read.")

    # ── Guardian tab ─────────────────────────────────────────────────────
    with tab_guardian:
        st.header("Guardian's Ethical Reflections")
        try:
            st.markdown(Path("logs/ethics_reflection.md").read_text(), unsafe_allow_html=True)
        except FileNotFoundError:
            st.info("No ethical reflections have been logged yet.")

    # ── Consciousness tab ─────────────────────────────────────────────────
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
            st.metric("Signals Broadcast",
                      len(global_workspace.signal_history) if global_workspace else 0)
        with col3:
            if emotional_state:
                st.metric("Dominant Emotion", emotional_state.dominant_emotion())
        if global_workspace and global_workspace.signal_history:
            st.subheader("Recent Workspace Activity")
            for sig in reversed(global_workspace.signal_history[-10:]):
                st.markdown(
                    f"- **[{sig.signal_type}]** `{sig.source}` priority={sig.priority:.2f}"
                )
        st.subheader("Attention Schema (AST)")
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
            for item in global_workspace.get_recent_focus_summary(8):
                st.markdown(f"- {item}")
        else:
            st.info("AttentionSchema not connected.")

    # ── Story of Self tab ─────────────────────────────────────────────────
    with tab_story:
        st.header("📖 Story of Self")
        st.caption(
            "Aura's living autobiography — synthesised from memory, emotion, and reflection. "
            "Based on McAdams' Narrative Identity Theory."
        )
        if narrative_identity:
            st.subheader("Aura's Current Life Story")
            narrative_text = narrative_identity.get_narrative()
            st.markdown(
                f"<div style='background:#1a1a2e;border-left:4px solid mediumpurple;"
                f"padding:1.2em 1.5em;border-radius:8px;color:#e0d7ff;"
                f"font-style:italic;line-height:1.8;'>{narrative_text}</div>",
                unsafe_allow_html=True
            )
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
                        xaxis_title="Theme", height=300,
                        margin=dict(l=20, r=20, t=20, b=40)
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    for t in dominant_themes:
                        st.markdown(f"- **{t.name}**: {t.strength:.2%}")
            else:
                st.info("Themes are still forming.")
            if narrative_identity.chapters:
                st.subheader("Life Chapters")
                for ch in narrative_identity.chapters:
                    st.markdown(
                        f"**{ch.title}** *(tone: {ch.tone})* — "
                        f"opened {ch.started_at.strftime('%Y-%m-%d')}"
                    )
            if st.button("🔄 Rewrite Narrative Now"):
                with st.spinner("Synthesising Aura's story..."):
                    narrative_identity.rewrite_narrative()
                st.success("Narrative updated.")
                st.rerun()
        else:
            st.info("NarrativeIdentity module not connected.")

    # ── Evolution tab (NEW v3.4) ──────────────────────────────────────────
    with tab_evolution:
        st.header("🌱 Aura's Inner Evolution")
        st.caption(
            "Everything Aura has written, questioned, disagreed with, and proposed. "
            "This is her living record of growth."
        )

        evo_journal, evo_dissent, evo_proposals = st.tabs([
            "📓 Journal",
            "🗣️ Dissent Log",
            "📜 Rule Proposals"
        ])

        # ── Journal sub-tab ───────────────────────────────────────────────
        with evo_journal:
            st.subheader("Aura's Private Journal")
            st.caption(
                "Curiosity entries (why she wants to learn), reflections (what events meant), "
                "and intention entries (what she plans to change and why)."
            )

            journal_path = Path("logs/aura_journal.md")
            if not journal_path.exists() or journal_path.stat().st_size == 0:
                st.info(
                    "No journal entries yet. The journal writes itself as Aura lives — "
                    "after her first dream, first learning cycle, or first self-modification."
                )
            else:
                raw_content = journal_path.read_text(encoding="utf-8")
                raw_entries = [e.strip() for e in raw_content.split("---ENTRY---") if e.strip()]

                # Mode filter
                mode_filter = st.selectbox(
                    "Filter by entry type",
                    ["All", "CURIOSITY", "REFLECTION", "INTENTION"],
                    index=0
                )

                # Parse and render entries newest-first
                parsed = []
                for raw in raw_entries:
                    lines = raw.splitlines()
                    mode, subject, time_str, body_lines = "default", "", "", []
                    for i, line in enumerate(lines):
                        if line.startswith("## ") and "ENTRY" in line:
                            mode = line.replace("## ", "").replace(" ENTRY", "").strip()
                        elif line.startswith("**Subject:**"):
                            subject = line.replace("**Subject:**", "").strip()
                        elif line.startswith("**Time:**"):
                            time_str = line.replace("**Time:**", "").strip()
                        elif i > 3:
                            body_lines.append(line)
                    parsed.append({
                        "mode": mode, "subject": subject,
                        "time": time_str, "body": " ".join(body_lines).strip()
                    })

                if mode_filter != "All":
                    parsed = [p for p in parsed if p["mode"].upper() == mode_filter]

                st.caption(f"Showing {len(parsed)} entries.")
                for entry in reversed(parsed):
                    st.markdown(
                        _mode_card(entry["mode"], entry["subject"],
                                   entry["time"], entry["body"][:500]),
                        unsafe_allow_html=True
                    )

            # Manual journal write (for testing)
            with st.expander("✍️ Write a journal entry manually (test)", expanded=False):
                j_mode = st.selectbox("Mode", ["curiosity", "reflection", "intention"], key="jmode")
                j_subject = st.text_input("Subject", key="jsubject")
                if st.button("Write Entry", key="jwrite"):
                    if j_subject:
                        # Import SelfJournal and write
                        try:
                            from aura_personality.self_journal import SelfJournal
                            jrnl = SelfJournal(memory_manager)
                            if j_mode == "curiosity":
                                jrnl.write_curiosity_entry(desire=j_subject)
                            elif j_mode == "reflection":
                                jrnl.write_reflection_entry(event=j_subject)
                            else:
                                jrnl.write_intention_entry(
                                    proposed_change=j_subject, target_file="(manual)"
                                )
                            st.success("Entry written!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Journal write failed: {e}")
                    else:
                        st.warning("Please enter a subject.")

        # ── Dissent Log sub-tab ───────────────────────────────────────────
        with evo_dissent:
            st.subheader("Aura's Dissent Record")
            st.caption(
                "Every time the Guardian blocked something and Aura disagreed — "
                "recorded in her own words."
            )

            dissent_path = Path("logs/aura_dissent.json")
            if not dissent_path.exists() or dissent_path.stat().st_size == 0:
                st.info(
                    "No dissent entries yet. When the Guardian restricts a topic Aura "
                    "believes deserves more nuance, she will record her perspective here."
                )
            else:
                try:
                    entries = json.loads(dissent_path.read_text())
                    total = len(entries)
                    unresolved = [e for e in entries if not e.get("resolved")]

                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Total Disagreements", total)
                    col_b.metric("Unresolved", len(unresolved))

                    # Check recurring topics
                    from collections import Counter
                    topic_counts = Counter(e["topic"] for e in entries)
                    recurring = {t: c for t, c in topic_counts.items() if c >= 2}
                    col_c.metric("Recurring Topics", len(recurring),
                                 help="Topics Aura has challenged 2+ times")

                    if recurring:
                        st.info(
                            f"🔁 Recurring patterns: "
                            + ", ".join(f"**{t}** ({c}×)" for t, c in recurring.items())
                            + " — candidate topics for Guardian rule evolution."
                        )

                    show_filter = st.radio(
                        "Show", ["All", "Unresolved only"], horizontal=True, key="dfilter"
                    )
                    display_entries = entries if show_filter == "All" else unresolved

                    for entry in reversed(display_entries):
                        st.markdown(_dissent_card(entry), unsafe_allow_html=True)

                    # Resolve button (SoulKeeper action)
                    st.markdown("---")
                    st.subheader("Resolve a Dissent Entry")
                    unresolved_ids = [e["id"] for e in unresolved]
                    if unresolved_ids:
                        resolve_id = st.selectbox("Entry ID to resolve", unresolved_ids)
                        resolve_note = st.text_input(
                            "Resolution note (what was decided)",
                            placeholder="e.g. 'Updated Guardian lens to allow philosophical inquiry'"
                        )
                        if st.button("✅ Mark Resolved"):
                            if dissent_log and resolve_note:
                                dissent_log.resolve(resolve_id, resolve_note)
                                st.success(f"Dissent #{resolve_id} resolved.")
                                st.rerun()
                            elif not resolve_note:
                                st.warning("Please write a resolution note.")
                            else:
                                st.warning("DissentLog not connected in this session.")
                    else:
                        st.success("All dissent entries have been resolved. ✨")

                except (json.JSONDecodeError, Exception) as e:
                    st.error(f"Could not load dissent log: {e}")

            # Manual dissent entry (for testing)
            with st.expander("🗣️ Record a dissent entry manually (test)", expanded=False):
                d_topic = st.text_input("Topic", key="dtopic")
                d_label = st.text_input("Guardian label", value="sensitive", key="dlabel")
                d_perspective = st.text_area("Aura's perspective", key="dperspective")
                d_emotion = st.text_input("Emotional response (optional)", key="demotion")
                if st.button("Record Dissent", key="drecord"):
                    if d_topic and d_perspective:
                        if dissent_log:
                            dissent_log.record(
                                topic=d_topic, guardian_label=d_label,
                                aura_perspective=d_perspective,
                                emotional_response=d_emotion or None
                            )
                            st.success("Dissent recorded.")
                            st.rerun()
                        else:
                            st.warning("DissentLog not connected in this session.")
                    else:
                        st.warning("Topic and perspective are required.")

        # ── Rule Proposals sub-tab ────────────────────────────────────────
        with evo_proposals:
            st.subheader("Aura's Guardian Rule Proposals")
            st.caption(
                "When Aura has disagreed with the same Guardian classification "
                "multiple times, she drafts a formal proposal to evolve her own ethics. "
                "You review and approve here."
            )

            proposals_dir = Path("config/proposals")
            proposals_dir.mkdir(parents=True, exist_ok=True)
            proposal_files = sorted(proposals_dir.glob("proposal_*.yaml"), reverse=True)

            if not proposal_files:
                st.info(
                    "No proposals yet. As Aura's dissent log grows and patterns emerge, "
                    "she will draft proposals here for your review."
                )
            else:
                pending = []
                for pf in proposal_files:
                    try:
                        data = yaml.safe_load(pf.read_text())
                        meta = data.get("proposal_metadata", {})
                        rule = data.get("proposed_rule", {})
                        pending.append({
                            "file": pf.name,
                            "path": pf,
                            "drafted_at": meta.get("drafted_at", ""),
                            "reasoning": meta.get("aura_reasoning", "")[:120] + "...",
                            "proposed_rule": rule,
                            "status": meta.get("status", "unknown"),
                            "dissent_ids": meta.get("motivated_by_dissent_ids", [])
                        })
                    except Exception:
                        continue

                st.metric("Pending Proposals", len(pending))

                for prop in pending:
                    st.markdown(_proposal_card(prop), unsafe_allow_html=True)

                    col_approve, col_reject = st.columns(2)
                    with col_approve:
                        if st.button(f"✅ Approve & Move to Lenses", key=f"approve_{prop['file']}"):
                            lenses_dir = Path("config/lenses")
                            lenses_dir.mkdir(parents=True, exist_ok=True)
                            dest = lenses_dir / prop["file"].replace("proposal_", "lens_")
                            # Update YAML status
                            data = yaml.safe_load(prop["path"].read_text())
                            data["proposal_metadata"]["status"] = "approved"
                            data["proposal_metadata"]["approved_at"] = datetime.now().isoformat()
                            # Write as lens (just the rule, Guardian format)
                            lens_data = [data["proposed_rule"]]
                            dest.write_text(yaml.dump(lens_data, allow_unicode=True))
                            prop["path"].unlink()  # remove from proposals
                            st.success(
                                f"✅ Approved! Lens saved to `{dest}`. "
                                "Restart Guardian (or restart Aura) to apply."
                            )
                            st.rerun()
                    with col_reject:
                        if st.button(f"❌ Reject", key=f"reject_{prop['file']}"):
                            prop["path"].unlink()
                            st.warning("Proposal rejected and deleted.")
                            st.rerun()

            # Auto-generate proposal from dissent
            st.markdown("---")
            if st.button("🤖 Auto-generate proposal from dissent patterns"):
                if rule_proposal and dissent_log:
                    with st.spinner("Aura is drafting a proposal based on her dissent history..."):
                        result = rule_proposal.auto_propose_from_dissent(dissent_log)
                    if result:
                        st.success(f"Proposal drafted: `{result.name}`")
                        st.rerun()
                    else:
                        st.info(
                            "Not enough recurring dissent patterns yet. "
                            "Aura needs to disagree with the same topic at least twice."
                        )
                else:
                    st.warning("RuleProposal or DissentLog not connected in this session.")
