"""
CASTALIEN Algorand Mainnet Account, Opt-In & 5DEX Swap Verification SDK
=======================================================================
Provides real-time Algorand Mainnet verification via Algonode APIs for:
1. Wallet existence and Minimum Balance Requirement (MBR) checks.
2. ASA Opt-In verification for Alpheon (3706444728) and Castalia (3706444716).
3. On-chain TXID verification and 5DEX Dual-Mode Swap quote calculation.
"""

import json
import urllib.request
from typing import Any, Dict

ALGOD_MAINNET_API = "https://mainnet-api.algonode.cloud"
INDEXER_MAINNET_API = "https://mainnet-idx.algonode.cloud/v2"

ALPHEON_ASA_ID = 3706444728
CASTALIA_ASA_ID = 3706444716
TREASURY_ADDRESS = "FGRDXIENOISLCFTP2FRHXH25OJTZNANSXCVTKEFJRWR3NCXPO4PDJTWET4"

# Public Protocol Equivalence Constants
ALP_PER_ALGO = 1024
EON_PER_ALP = 10
EON_PER_ALGO = ALP_PER_ALGO * EON_PER_ALP  # 10,240 EON
ALP_PER_CST = 1000
EON_PER_CST = ALP_PER_CST * EON_PER_ALP    # 10,000 EON


def _fetch_json(url: str, timeout: float = 10.0) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "CastalienAlgorandSDK/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def calculate_dex_swap_quote(
    asset_in: str,
    amount_in: float,
    settlement_mode: str = "AUTO_SWAP_ALP",
) -> Dict[str, Any]:
    """
    Calculates deterministic 5DEX conversion outputs under the two supported
    Mainnet settlement modes:
      - 'PORTAL_EON_CREDIT': Authenticated web user submits TXID on 5DEX portal
        to receive in-app EON utility balance (1 ALGO = 10,240 EON, 1 ALP = 10 EON).
      - 'AUTO_SWAP_ALP': Direct external wallet ALGO transfer to Treasury
        automatically settles Alpheon (ALP) back to the sender wallet on-chain
        (1 ALGO = 1,024 ALP).
    """
    token = asset_in.strip().upper()
    mode = settlement_mode.strip().upper()
    if amount_in <= 0:
        raise ValueError("amount_in must be positive")

    if token == "ALGO":
        alp_equiv = int(round(amount_in * ALP_PER_ALGO))
        eon_equiv = alp_equiv * EON_PER_ALP
    elif token == "ALP":
        alp_equiv = int(round(amount_in))
        eon_equiv = alp_equiv * EON_PER_ALP
    elif token == "CST":
        alp_equiv = int(round(amount_in * ALP_PER_CST))
        eon_equiv = alp_equiv * EON_PER_ALP
    else:
        raise ValueError(f"Unsupported asset_in: {asset_in}")

    return {
        "asset_in": token,
        "amount_in": amount_in,
        "settlement_mode": mode,
        "alp_output": alp_equiv,
        "eon_output": eon_equiv,
        "treasury_receiver": TREASURY_ADDRESS,
    }


def check_mainnet_account_status(wallet_address: str) -> Dict[str, Any]:
    """
    Queries Algorand Mainnet to verify whether a Pera Wallet address is funded
    and opted into Alpheon (ASA 3706444728) and Castalia (ASA 3706444716).
    """
    url = f"{ALGOD_MAINNET_API}/v2/accounts/{wallet_address.strip()}"
    data = _fetch_json(url)

    algo_balance = data.get("amount", 0) / 1_000_000
    min_balance = data.get("min-balance", 100_000) / 1_000_000
    assets = data.get("assets", [])

    alp_opted_in = False
    alp_balance = 0
    cst_opted_in = False
    cst_balance = 0

    for asset in assets:
        aid = asset.get("asset-id")
        if aid == ALPHEON_ASA_ID:
            alp_opted_in = True
            alp_balance = int(asset.get("amount", 0))
        elif aid == CASTALIA_ASA_ID:
            cst_opted_in = True
            cst_balance = int(asset.get("amount", 0))

    return {
        "address": wallet_address,
        "algo_balance": round(algo_balance, 6),
        "min_balance_required": round(min_balance, 6),
        "has_sufficient_mbr_for_optin": algo_balance >= (min_balance + 0.101),
        "alpheon_asa_3706444728": {
            "opted_in": alp_opted_in,
            "balance_alp": alp_balance,
        },
        "castalia_asa_3706444716": {
            "opted_in": cst_opted_in,
            "balance_cst": cst_balance,
        },
    }


def verify_deposit_txid(
    txid: str,
    expected_receiver: str = TREASURY_ADDRESS,
) -> Dict[str, Any]:
    """
    Verifies a Mainnet ALGO or ASA transfer transaction via Algonode Indexer
    for 5DEX swap settlement.
    """
    url = f"{INDEXER_MAINNET_API}/transactions/{txid.strip()}"
    tx = _fetch_json(url).get("transaction", {})

    tx_type = tx.get("tx-type")
    sender = tx.get("sender")
    confirmed_round = tx.get("confirmed-round", 0)

    if tx_type == "pay":
        pay_info = tx.get("payment-transaction", {})
        receiver = pay_info.get("receiver")
        amount_algo = pay_info.get("amount", 0) / 1_000_000
        return {
            "verified": receiver == expected_receiver and confirmed_round > 0,
            "txid": txid,
            "asset": "ALGO",
            "sender": sender,
            "receiver": receiver,
            "amount": amount_algo,
            "equivalent_alp": int(round(amount_algo * ALP_PER_ALGO)),
            "equivalent_eon": int(round(amount_algo * EON_PER_ALGO)),
            "confirmed_round": confirmed_round,
        }

    if tx_type == "axfer":
        axfer_info = tx.get("asset-transfer-transaction", {})
        receiver = axfer_info.get("receiver")
        asset_id = axfer_info.get("asset-id")
        amount_units = int(axfer_info.get("amount", 0))
        return {
            "verified": receiver == expected_receiver and confirmed_round > 0,
            "txid": txid,
            "asset": f"ASA_{asset_id}",
            "sender": sender,
            "receiver": receiver,
            "amount": amount_units,
            "confirmed_round": confirmed_round,
        }

    return {"verified": False, "txid": txid, "reason": f"Unsupported tx-type: {tx_type}"}
