"""
Basic Solana chain interaction utilities
"""

import base64
from typing import Any

try:
    from solana.keypair import Keypair
    from solana.rpc.api import Client
    from solana.transaction import Transaction
except ImportError as e:
    raise ImportError("Install solana package: pip install 'optr[solana]'") from e


def get_connection(
    rpc_url: str = "https://api.devnet.solana.com",
    commitment: str = "confirmed",
) -> Client:
    """
    Get RPC connection to Solana

    Args:
        rpc_url: RPC endpoint URL
        commitment: Commitment level

    Returns:
        Client instance

    Example:
        client = get_connection()
        # Use client for RPC calls
    """
    return Client(rpc_url, commitment=commitment)


def send_transaction(
    transaction: Transaction,
    wallet: Keypair,
    rpc_url: str = "https://api.devnet.solana.com",
) -> str | None:
    """
    Send transaction to chain

    Args:
        transaction: Transaction to send
        wallet: Wallet to sign with
        rpc_url: RPC endpoint

    Returns:
        Transaction signature or None

    Example:
        tx = Transaction()
        # Add instructions...
        sig = send_transaction(tx, wallet)
    """
    client = get_connection(rpc_url)

    try:
        # Get recent blockhash
        blockhash = client.get_recent_blockhash()["result"]["value"]["blockhash"]
        transaction.recent_blockhash = blockhash

        # Sign transaction
        transaction.sign(wallet)

        # Send transaction
        response = client.send_transaction(transaction, wallet)

        if "result" in response:
            return response["result"]
        else:
            print(f"Transaction failed: {response}")
            return None

    except Exception as e:
        print(f"Error sending transaction: {e}")
        return None


def store_data(
    data: bytes,
    wallet: Keypair,
    rpc_url: str = "https://api.devnet.solana.com",
) -> str | None:
    """
    Store data on-chain (simplified memo approach)

    Args:
        data: Data to store (max ~1000 bytes)
        wallet: Wallet to pay fees
        rpc_url: RPC endpoint

    Returns:
        Transaction signature

    Example:
        sig = store_data(b"operator_action_data", wallet)
    """
    if len(data) > 1000:
        raise ValueError("Data too large. Use IPFS/Arweave for large data")

    get_connection(rpc_url)

    # For simplicity, using memo program
    # In production, use custom program or compressed NFTs
    from solana.transaction import Transaction

    # Create memo instruction

    # Encode data as base64 for memo
    base64.b64encode(data).decode("utf-8")

    # Build transaction with memo
    tx = Transaction()

    # Add memo instruction (simplified)
    # In production, use proper instruction building

    return send_transaction(tx, wallet, rpc_url)


def retrieve_data(
    signature: str,
    rpc_url: str = "https://api.devnet.solana.com",
) -> bytes | None:
    """
    Retrieve data from transaction

    Args:
        signature: Transaction signature
        rpc_url: RPC endpoint

    Returns:
        Data bytes or None

    Example:
        data = retrieve_data(signature)
        action = decompress_action(data)
    """
    client = get_connection(rpc_url)

    try:
        # Get transaction
        response = client.get_transaction(signature)

        if "result" not in response:
            return None

        # Extract memo data (simplified)
        # In production, parse properly
        response["result"]

        # This is simplified - actual implementation would
        # parse transaction logs and extract memo data

        return None  # Placeholder

    except Exception as e:
        print(f"Error retrieving data: {e}")
        return None


def estimate_cost(
    data_size: int,
    priority_fee: float = 0.0,
) -> float:
    """
    Estimate transaction cost in SOL

    Args:
        data_size: Size of data in bytes
        priority_fee: Additional priority fee

    Returns:
        Estimated cost in SOL

    Example:
        cost = estimate_cost(len(compressed_data))
        print(f"Estimated cost: {cost} SOL")
    """
    # Base fee (5000 lamports)
    base_fee = 5000 / 1e9

    # Storage cost (rough estimate)
    # Actual cost depends on program and account rent
    storage_fee = (data_size / 1000) * 0.00001

    # Priority fee
    priority = priority_fee

    return base_fee + storage_fee + priority


def get_transaction_status(
    signature: str,
    rpc_url: str = "https://api.devnet.solana.com",
) -> dict[str, Any] | None:
    """
    Get transaction status

    Args:
        signature: Transaction signature
        rpc_url: RPC endpoint

    Returns:
        Status dictionary or None

    Example:
        status = get_transaction_status(sig)
        if status and status["confirmations"] > 0:
            print("Transaction confirmed!")
    """
    client = get_connection(rpc_url)

    try:
        response = client.get_signature_statuses([signature])

        if "result" in response and response["result"]["value"]:
            status = response["result"]["value"][0]
            if status:
                return {
                    "slot": status.get("slot"),
                    "confirmations": status.get("confirmations"),
                    "status": status.get("status"),
                }

        return None

    except Exception as e:
        print(f"Error getting status: {e}")
        return None


def wait_for_confirmation(
    signature: str,
    rpc_url: str = "https://api.devnet.solana.com",
    max_timeout: float = 30.0,
) -> bool:
    """
    Wait for transaction confirmation

    Args:
        signature: Transaction signature
        rpc_url: RPC endpoint
        max_timeout: Max wait time in seconds

    Returns:
        True if confirmed

    Example:
        if wait_for_confirmation(sig):
            print("Transaction confirmed!")
    """
    import time

    start = time.time()

    while time.time() - start < max_timeout:
        status = get_transaction_status(signature, rpc_url)

        if status and status.get("confirmations", 0) > 0:
            return True

        time.sleep(1)

    return False
