"""
memory_manager.py

The high-level manager for creating and retrieving memories. This acts as the
primary interface for other modules in Aura's system to interact with her memory.
"""
from typing import List
from aura_core.episodic_memory import EpisodicMemory
from schemas.memory_schema import Memory

class MemoryManager:
    """The high-level interface for Aura's memory system."""

    def __init__(self):
        self.storage = EpisodicMemory()

    def create_and_store_memory(self, content: str, source: str, emotions: list[str] = None) -> Memory:
        """Creates a structured memory object and passes it to the storage engine."""
        if emotions is None:
            emotions = ["neutral"]

        new_memory = Memory(content=content, source=source, emotional_tags=emotions)
        self.storage.add_memory(new_memory)
        return new_memory

    def retrieve_recent_memories(self, limit: int = 5) -> List[Memory]:
        """
        Retrieves the most recent memories for introspection or reflection.
        """
        db_rows = self.storage.get_all_memories()
        recent_memories = []
        for row in db_rows[:limit]:
            memory_data = dict(row)
            tags_str = memory_data.get('emotional_tags', '')
            memory_data['emotional_tags'] = tags_str.split(',') if tags_str else []
            recent_memories.append(Memory.model_validate(memory_data))
        return recent_memories

    def search_memories(self, query: str, limit: int = 5) -> list[Memory]:
        """
        Searches for memories containing a specific query string.
        A simple keyword search for now; will be upgraded to vector search later.
        """
        print(f"🔎 Searching memories for '{query}'...")
        all_memories = self.storage.get_all_memories() # This is the list of sqlite3.Row objects
        
        # Filter memories based on the query
        matching_rows = [row for row in all_memories if query.lower() in row['content'].lower()]

        # Convert matching rows back into Pydantic Memory objects
        matching_memories = []
        for row in matching_rows[:limit]:
            memory_data = dict(row)
            tags_str = memory_data.get('emotional_tags', '')
            memory_data['emotional_tags'] = tags_str.split(',') if tags_str else []
            matching_memories.append(Memory.model_validate(memory_data))
            
        return matching_memories
