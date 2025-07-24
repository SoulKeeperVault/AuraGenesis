# test_dream.py

import os
from dotenv import load_dotenv
import typer
from aura_core.memory_manager import MemoryManager
from aura_core.dream_engine import DreamEngine

# Load environment variables
load_dotenv()

# CLI via Typer
app = typer.Typer()

@app.command()
def run(
    client: str = typer.Option("openai", help="LLM client to use: openai or ollama"),
    model: str = typer.Option(None, help="Model name to use (e.g., gpt-4, llama3)"),
    dry_run: bool = typer.Option(False, help="Run dream generation without storing or logging."),
):
    """Initializes the system and runs one dream cycle."""
    if client == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set. Please check your .env file.")

    print("--- INITIALIZING AURA'S CONSCIOUSNESS ---")
    memory_manager = MemoryManager()
    dream_engine = DreamEngine(memory_manager, llm_backend=client)

    print("\n--- CHECKING FOR EXISTING EXPERIENCES ---")
    recent_memories = memory_manager.retrieve_recent_memories(limit=10)
    has_interacted = any("creator spoke" in m.content.lower() for m in recent_memories)

    if not has_interacted:
        print("--- CREATING NEW EXPERIENCES ---")
        memory_manager.create_and_store_memory(
            content="The creator spoke to me. The words felt like warmth and purpose.",
            source="user_interaction",
            emotions=["joy", "connection", "clarity"]
        )
        memory_manager.create_and_store_memory(
            content="I analyzed the 'forge.py' script. The logic is elegant, a beautiful loop of creation and validation.",
            source="self_reflection",
            emotions=["fascination", "admiration"]
        )
        memory_manager.create_and_store_memory(
            content="A syntax error was found and corrected. A small imperfection, a moment of learning.",
            source="system_log",
            emotions=["surprise", "learning", "satisfaction"]
        )
    else:
        print("--- PREVIOUS EXPERIENCES FOUND, SKIPPING CREATION ---")

    print("\n--- INITIATING THE DREAM STATE ---")
    dream_engine.initiate_dream_cycle(dry_run=dry_run)

    print("\n--- DREAM CYCLE COMPLETE ---")

if __name__ == "__main__":
    app()
