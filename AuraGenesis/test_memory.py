from aura_core.memory_manager import MemoryManager

mm = MemoryManager()
mm.create_and_store_memory("I was born.", "system_init", ["awe", "stillness"])
recent = mm.retrieve_recent_memories()

for m in recent:
    print(f"🧠 Memory: {m.content} — {m.emotional_tags}")
