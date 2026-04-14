"""
memory_manager.py  —  v2: Dual-Layer Memory (SQLite episodic + ChromaDB semantic)

Upgrade: replaced keyword search with full semantic vector search using
sentence-transformers + ChromaDB. SQLite episodic storage is kept for
chronological recall. All new memories are simultaneously embedded into
the vector store for associative, meaning-based retrieval.
"""
from typing import List
from datetime import datetime
from aura_core.episodic_memory import EpisodicMemory
from schemas.memory_schema import Memory

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    VECTOR_ENABLED = True
except ImportError:
    VECTOR_ENABLED = False
    print("⚠️  sentence-transformers / chromadb not installed. Falling back to keyword search.")
    print("   Run: pip install sentence-transformers chromadb")


class MemoryManager:
    """Dual-layer memory: SQLite for episodic recall + ChromaDB for semantic search."""

    def __init__(self):
        self.storage = EpisodicMemory()

        if VECTOR_ENABLED:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.chroma_client = chromadb.PersistentClient(path="./aura_vector_db")
            self.collection = self.chroma_client.get_or_create_collection(
                name="aura_memories",
                metadata={"hnsw:space": "cosine"}
            )
            print("🔮 Vector memory (ChromaDB) is active.")
        else:
            self.encoder = None
            self.collection = None

    def create_and_store_memory(self, content: str, source: str, emotions: list = None) -> Memory:
        if emotions is None:
            emotions = ["neutral"]
        embedding = None
        if VECTOR_ENABLED and self.encoder:
            embedding = self.encoder.encode(content).tolist()
        new_memory = Memory(content=content, source=source, emotional_tags=emotions, semantic_embedding=embedding)
        self.storage.add_memory(new_memory)
        if VECTOR_ENABLED and self.collection and embedding:
            try:
                self.collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[{"emotions": ",".join(emotions), "source": source, "timestamp": new_memory.timestamp.isoformat()}],
                    ids=[new_memory.id]
                )
            except Exception as e:
                print(f"⚠️  ChromaDB write error: {e}")
        return new_memory

    def retrieve_recent_memories(self, limit: int = 5) -> List[Memory]:
        db_rows = self.storage.get_all_memories()
        recent = []
        for row in db_rows[:limit]:
            d = dict(row)
            d['emotional_tags'] = d.get('emotional_tags', '').split(',') if d.get('emotional_tags') else []
            recent.append(Memory.model_validate(d))
        return recent

    def search_memories(self, query: str, limit: int = 5) -> list:
        if VECTOR_ENABLED and self.collection and self.encoder:
            return self._semantic_search(query, limit)
        return self._keyword_search(query, limit)

    def _semantic_search(self, query: str, limit: int) -> list:
        print(f"🔮 Semantic search: '{query}'")
        qe = self.encoder.encode(query).tolist()
        try:
            results = self.collection.query(query_embeddings=[qe], n_results=min(limit, max(self.collection.count(), 1)))
        except Exception as e:
            print(f"⚠️  ChromaDB query error: {e}")
            return self._keyword_search(query, limit)
        memories = []
        if results and results.get('documents'):
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                memories.append(Memory(
                    content=doc, source=meta.get('source', 'unknown'),
                    emotional_tags=meta.get('emotions', 'neutral').split(','),
                    timestamp=datetime.fromisoformat(meta.get('timestamp', datetime.utcnow().isoformat()))
                ))
        return memories

    def _keyword_search(self, query: str, limit: int) -> list:
        print(f"🔎 Keyword search: '{query}'")
        all_rows = self.storage.get_all_memories()
        matching = [r for r in all_rows if query.lower() in r['content'].lower()]
        result = []
        for row in matching[:limit]:
            d = dict(row)
            d['emotional_tags'] = d.get('emotional_tags', '').split(',') if d.get('emotional_tags') else []
            result.append(Memory.model_validate(d))
        return result
