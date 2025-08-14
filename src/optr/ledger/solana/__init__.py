"""
Solana blockchain integration toolkit for operator action recording
"""

from . import action
from .batch import ActionBatch, BatchConfig, create_batch_manager
from .chain import (
    estimate_cost,
    get_connection,
    get_transaction_status,
    retrieve_data,
    send_transaction,
    store_data,
    wait_for_confirmation,
)
from .serialize import (
    compress_action,
    compress_state,
    create_action_proof,
    decompress_action,
    estimate_storage_size,
    hash_action,
    merkle_root,
)
from .wallet import (
    create_wallet,
    fund_wallet,
    get_balance,
    get_wallet_address,
    load_wallet,
)

__all__ = [
    # Action module
    "action",
    # Wallet utilities
    "load_wallet",
    "get_balance",
    "fund_wallet",
    "create_wallet",
    "get_wallet_address",
    # Batching utilities
    "ActionBatch",
    "BatchConfig",
    "create_batch_manager",
    # Serialization utilities (legacy names for compatibility)
    "compress_action",
    "decompress_action",
    "hash_action",
    "merkle_root",
    "compress_state",
    "create_action_proof",
    "estimate_storage_size",
    # Chain utilities
    "get_connection",
    "send_transaction",
    "store_data",
    "retrieve_data",
    "estimate_cost",
    "get_transaction_status",
    "wait_for_confirmation",
]
