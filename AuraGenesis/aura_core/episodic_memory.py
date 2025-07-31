"""
episodic_memory.py

The low-level storage engine for Aura's memories. This module directly
interacts with the SQLite database to perform CRUD operations on memory records.
"""
import sqlite3
from pathlib import Path
from typing import List
from schemas.memory_schema import Memory

class EpisodicMemory:
    """Handles direct interaction with the SQLite database for memory storage."""

    def __init__(self, db_path: str = "aura_memory.db"):
        self.db_path = Path(db_path)
        self._create_table()

    def _get_connection(self):
        """Returns a new connection to the database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_table(self):
        """Creates the 'memories' table if it doesn't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    emotional_tags TEXT
                )
            """)
            conn.commit()

    def add_memory(self, memory: Memory):
        """Adds a new memory object to the database using parameterized queries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            tags_str = ",".join(memory.emotional_tags)
            cursor.execute(
                "INSERT INTO memories (id, timestamp, content, source, emotional_tags) VALUES (?, ?, ?, ?, ?)",
                (memory.id, memory.timestamp.isoformat(), memory.content, memory.source, tags_str)
            )
            conn.commit()
            print(f"✅ Memory stored with ID: {memory.id}")

    def get_all_memories(self) -> List[sqlite3.Row]:
        """Retrieves all memories from the database, most recent first."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories ORDER BY timestamp DESC")
            return cursor.fetchall()

    def search_memories(self, query: str, limit: int = 5) -> List[sqlite3.Row]:
        """Searches for memories containing the query string using parameterized queries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Use parameterized query to prevent SQL injection
            cursor.execute(
                "SELECT * FROM memories WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (f"%{query}%", limit)
            )
            return cursor.fetchall()
