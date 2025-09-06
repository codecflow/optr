"""
Wallet utilities for Solana integration
"""

import json
import os
from pathlib import Path

try:
    from solana.rpc.api import Client
    from solana.rpc.commitment import Commitment
    from solders.keypair import Keypair
except ImportError as e:
    raise ImportError("Install solana package: pip install 'optr[solana]'") from e


def load_wallet(path: str | Path | None = None) -> Keypair:
    """
    Load wallet from file or environment variable

    Args:
        path: Path to wallet file (JSON array format)
              If None, checks SOLANA_WALLET_PATH env var

    Returns:
        Keypair instance

    Example:
        wallet = load_wallet("~/.solana/id.json")
        wallet = load_wallet()  # Uses env var
    """
    if path is None:
        path = os.environ.get("SOLANA_WALLET_PATH")
        if not path:
            raise ValueError(
                "No wallet path provided. Set SOLANA_WALLET_PATH or pass path"
            )

    path = Path(path).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Wallet file not found: {path}")

    with open(path) as f:
        secret_key = json.load(f)

    return Keypair.from_seed(bytes(secret_key[:32]))


def get_balance(
    wallet: Keypair,
    rpc_url: str = "https://api.devnet.solana.com",
) -> float:
    """
    Get wallet balance in SOL

    Args:
        wallet: Keypair instance
        rpc_url: RPC endpoint URL

    Returns:
        Balance in SOL

    Example:
        balance = get_balance(wallet)
        print(f"Balance: {balance} SOL")
    """
    client = Client(rpc_url)
    response = client.get_balance(wallet.pubkey(), commitment=Commitment("confirmed"))

    if response.value is None:
        return 0.0

    # Convert lamports to SOL (1 SOL = 1e9 lamports)
    return response.value / 1e9


def fund_wallet(
    wallet: Keypair,
    amount: float = 1.0,
    rpc_url: str = "https://api.devnet.solana.com",
) -> str | None:
    """
    Fund wallet from devnet faucet (devnet only)

    Args:
        wallet: Keypair to fund
        amount: Amount in SOL (max 2 SOL on devnet)
        rpc_url: RPC endpoint (must be devnet)

    Returns:
        Transaction signature or None if failed

    Example:
        sig = fund_wallet(wallet, 1.0)
        if sig:
            print(f"Funded: {sig}")
    """
    if "devnet" not in rpc_url:
        raise ValueError("Faucet only available on devnet")

    if amount > 2.0:
        raise ValueError("Max 2 SOL per request on devnet")

    client = Client(rpc_url)

    # Convert SOL to lamports
    lamports = int(amount * 1e9)

    try:
        response = client.request_airdrop(wallet.pubkey(), lamports)
        return str(response.value)
    except Exception as e:
        print(f"Airdrop failed: {e}")
        return None


def create_wallet() -> tuple[Keypair, list[int]]:
    """
    Create new wallet keypair

    Returns:
        Tuple of (Keypair, secret_key_array)

    Example:
        wallet, secret = create_wallet()
        # Save secret to file for later use
        with open("wallet.json", "w") as f:
            json.dump(secret, f)
    """
    keypair = Keypair()
    secret_key = list(bytes(keypair))
    return keypair, secret_key


def get_wallet_address(wallet: Keypair) -> str:
    """
    Get wallet public address as string

    Args:
        wallet: Keypair instance

    Returns:
        Base58 encoded public key

    Example:
        address = get_wallet_address(wallet)
        print(f"Address: {address}")
    """
    return str(wallet.pubkey())
