"""Pipeline utilities and dynamic modification tools."""

# Core pipeline functions
from .core import pipeline, link, chain, compose

# Branching utilities
from .branch import (
    branch,
    unbranch,
    create_tee_branch,
    remove_tee_branch,
    get_tee_branches,
    count_tee_branches,
    is_tee_element,
)

# Dynamic pipeline modification
from .dynamic import (
    hot_add,
    hot_remove,
    reconnect,
    replace_element,
    insert_element,
    branch_insert,
    branch_remove,
)

# Debugging and monitoring utilities
from .monitor import Monitor, profiler
from .validate import validate
from .debug import topology, dotgraph

__all__ = [
    # Core pipeline functions
    "pipeline",
    "link", 
    "chain",
    "compose",
    # Branching utilities
    "branch",
    "unbranch",
    "create_tee_branch",
    "remove_tee_branch",
    "get_tee_branches",
    "count_tee_branches",
    "is_tee_element",
    # Dynamic modification
    "hot_add",
    "hot_remove",
    "reconnect",
    "replace_element",
    "insert_element",
    "branch_insert",
    "branch_remove",
    # Monitoring and debugging
    "Monitor",
    "profiler",
    "validate",
    "topology",
    "dotgraph",
]
