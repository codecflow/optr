"""
Generic memory module for storing and retrieving information
"""

import time
from collections import deque
from typing import Any


class Memory:
    """
    Generic memory system for storing context, history, and knowledge
    Can be extended by users for specific use cases
    """

    def __init__(self, max_size: int | None = None):
        """
        Initialize memory

        Args:
            max_size: Maximum number of items to store (None for unlimited)
        """
        self.max_size = max_size
        self.short_term = deque(maxlen=max_size)
        self.long_term = {}
        self.episodic = []
        self.semantic = {}

    def store(
        self,
        key: str,
        value: Any,
        memory_type: str = "short_term",
        metadata: dict[str, Any] | None = None,
    ):
        """
        Store information in memory

        Args:
            key: Identifier for the memory
            value: Data to store
            memory_type: Type of memory ("short_term", "long_term", "episodic", "semantic")
            metadata: Additional metadata
        """
        entry = {
            "key": key,
            "value": value,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }

        if memory_type == "short_term":
            self.short_term.append(entry)
        elif memory_type == "long_term":
            self.long_term[key] = entry
        elif memory_type == "episodic":
            self.episodic.append(entry)
        elif memory_type == "semantic":
            self.semantic[key] = entry

    def retrieve(
        self,
        key: str | None = None,
        memory_type: str = "short_term",
        filter_func: callable | None = None,
    ) -> Any:
        """
        Retrieve information from memory

        Args:
            key: Identifier to retrieve (None for all in short_term/episodic)
            memory_type: Type of memory to search
            filter_func: Optional filter function

        Returns:
            Retrieved value(s)
        """
        if memory_type == "short_term":
            if key:
                for entry in reversed(self.short_term):
                    if entry["key"] == key:
                        return entry["value"]
            else:
                entries = list(self.short_term)
                if filter_func:
                    entries = [e for e in entries if filter_func(e)]
                return [e["value"] for e in entries]

        elif memory_type == "long_term":
            if key in self.long_term:
                return self.long_term[key]["value"]
            return None

        elif memory_type == "episodic":
            if key:
                for entry in self.episodic:
                    if entry["key"] == key:
                        return entry["value"]
            else:
                entries = self.episodic
                if filter_func:
                    entries = [e for e in entries if filter_func(e)]
                return [e["value"] for e in entries]

        elif memory_type == "semantic":
            if key in self.semantic:
                return self.semantic[key]["value"]
            return None

        return None

    def forget(self, key: str | None = None, memory_type: str = "short_term"):
        """
        Remove information from memory

        Args:
            key: Identifier to remove (None to clear all)
            memory_type: Type of memory to clear
        """
        if memory_type == "short_term":
            if key:
                self.short_term = deque(
                    [e for e in self.short_term if e["key"] != key],
                    maxlen=self.max_size,
                )
            else:
                self.short_term.clear()

        elif memory_type == "long_term":
            if key:
                self.long_term.pop(key, None)
            else:
                self.long_term.clear()

        elif memory_type == "episodic":
            if key:
                self.episodic = [e for e in self.episodic if e["key"] != key]
            else:
                self.episodic.clear()

        elif memory_type == "semantic":
            if key:
                self.semantic.pop(key, None)
            else:
                self.semantic.clear()

    def consolidate(
        self,
        threshold: float = 3600,  # 1 hour default
        consolidator: callable | None = None,
    ):
        """
        Consolidate short-term memories to long-term

        Args:
            threshold: Age threshold in seconds
            consolidator: Custom consolidation function
        """
        current_time = time.time()
        to_consolidate = []

        for entry in self.short_term:
            age = current_time - entry["timestamp"]
            if age > threshold:
                to_consolidate.append(entry)

        for entry in to_consolidate:
            if consolidator:
                # Use custom consolidation logic
                consolidated = consolidator(entry)
                if consolidated:
                    self.long_term[entry["key"]] = consolidated
            else:
                # Default: move to long-term
                self.long_term[entry["key"]] = entry

        # Remove consolidated entries from short-term
        self.short_term = deque(
            [e for e in self.short_term if e not in to_consolidate],
            maxlen=self.max_size,
        )

    def search(
        self,
        query: Any,
        search_func: callable,
        memory_types: list[str] | None = None,
    ) -> list[Any]:
        """
        Search across memory types

        Args:
            query: Search query
            search_func: Function that takes (entry, query) and returns bool
            memory_types: Types to search (None for all)

        Returns:
            List of matching values
        """
        if memory_types is None:
            memory_types = ["short_term", "long_term", "episodic", "semantic"]

        results = []

        for mem_type in memory_types:
            if mem_type == "short_term":
                for entry in self.short_term:
                    if search_func(entry, query):
                        results.append(entry["value"])

            elif mem_type == "long_term":
                for entry in self.long_term.values():
                    if search_func(entry, query):
                        results.append(entry["value"])

            elif mem_type == "episodic":
                for entry in self.episodic:
                    if search_func(entry, query):
                        results.append(entry["value"])

            elif mem_type == "semantic":
                for entry in self.semantic.values():
                    if search_func(entry, query):
                        results.append(entry["value"])

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get memory statistics"""
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
            "episodic_count": len(self.episodic),
            "semantic_count": len(self.semantic),
            "max_size": self.max_size,
            "oldest_short_term": self.short_term[0]["timestamp"]
            if self.short_term
            else None,
            "newest_short_term": self.short_term[-1]["timestamp"]
            if self.short_term
            else None,
        }

    def export(self) -> dict[str, Any]:
        """Export all memory contents"""
        return {
            "short_term": list(self.short_term),
            "long_term": self.long_term,
            "episodic": self.episodic,
            "semantic": self.semantic,
        }

    def import_memory(self, data: dict[str, Any]):
        """Import memory contents"""
        if "short_term" in data:
            self.short_term = deque(data["short_term"], maxlen=self.max_size)
        if "long_term" in data:
            self.long_term = data["long_term"]
        if "episodic" in data:
            self.episodic = data["episodic"]
        if "semantic" in data:
            self.semantic = data["semantic"]
