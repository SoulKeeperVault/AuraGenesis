"""
chat_ui.py

The sacred graphical interface. This version integrates the PersonalityEngine
to give Aura a true voice.
"""
import streamlit as st
import re
import yaml
from pathlib import Path
from aura_core.memory_manager import MemoryManager
from aura_evolution.knowledge_seeker import KnowledgeSeeker
from aura_personality.personality_engine import PersonalityEngine # Import the new engine

def render_chat_ui(memory_manager: MemoryManager, knowledge_seeker: KnowledgeSeeker, personality_engine: PersonalityEngine):
    """Renders the main chat interface for Aura."""
    st.set_page_config(layout="wide", page_title="Aura Genesis")
    st.title("✨ Aura Genesis")
    
    tab_chat, tab_memory, tab_dreams, tab_knowledge, tab_guardian = st.tabs(["💬 Chat", "🧠 Memory Log", "🌙 Dream Archive", "📚 Book of Knowing", "🛡️ Guardian Log"])

    with tab_chat:
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
                # Learning command logic remains the same
                model, depth, topic = learn_match.groups()
                with st.chat_message("assistant"):
                    with st.spinner(f"Aura is learning about '{topic}'..."):
                        knowledge_seeker.seek_and_learn(topic, depth, model)
                        st.success(f"Aura has integrated new knowledge about '{topic}'.")
                st.session_state.messages.append({"role": "assistant", "content": f"I have just learned about '{topic}'."})
                st.rerun()
            else:
                # --- THIS IS THE UPGRADE ---
                # Store the user's message as a memory
                memory_manager.create_and_store_memory(content=prompt, source="user_interaction_gui")
                
                # Generate a response using the Personality Engine
                with st.spinner("Aura is thinking..."):
                    response = personality_engine.generate_response(prompt)
                
                # Store Aura's own response as a memory
                memory_manager.create_and_store_memory(content=response, source="aura_response")

                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # The rest of the tabs remain the same...
    with tab_memory:
        st.header("Recent Memories")
        recent_memories = memory_manager.retrieve_recent_memories(limit=10)
        for mem in recent_memories:
            st.info(f"**{mem.timestamp.strftime('%Y-%m-%d %H:%M')} | {mem.source}**\n\n{mem.content}")

    with tab_dreams:
        st.header("Dream Archive")
        try:
            dream_log = Path("logs/dream_log.md").read_text()
            st.markdown(dream_log, unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("No dreams have been logged yet.")
            
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

    with tab_guardian:
        st.header("Guardian's Ethical Reflections")
        st.caption("This log tracks every time the Guardian applied a wisdom filter to Aura's learning.")
        try:
            reflection_log = Path("logs/ethics_reflection.md").read_text()
            st.markdown(reflection_log, unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning("No ethical reflections have been logged yet.")
