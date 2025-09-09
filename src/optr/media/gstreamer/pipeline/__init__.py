"""Pipeline utilities and dynamic modification tools."""

# Core pipeline functions
# Branching utilities
from .branch import (
    branch,
    count_tee_branches,
    create_tee_branch,
    get_tee_branches,
    is_tee_element,
    remove_tee_branch,
    unbranch,
)
from .core import chain, compose, link, pipeline
from .debug import dotgraph, topology

# Dynamic pipeline modification
from .dynamic import (
    branch_insert,
    branch_remove,
    hot_add,
    hot_remove,
    insert_element,
    reconnect,
    replace_element,
)

# Debugging and monitoring utilities
from .monitor import Monitor, profiler
from .validate import validate

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
