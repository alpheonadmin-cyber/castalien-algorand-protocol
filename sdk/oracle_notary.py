"""
CASTALIEN Proof-of-Oracle On-Chain Notary SDK
=============================================
Computes deterministic SHA-256 cryptographic proofs for AI 1KICHING (64 Hexagrams)
and Astronomical Saju reports and broadcasts ARC-0002 compliant notarization
transactions on Algorand Mainnet (Alpheon ASA 3706444728).
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

DEFAULT_ALGOD_URL = os.getenv("ALGOD_SERVER", "https://mainnet-api.algonode.cloud")
ARC2_PREFIX = "castalien-oracle:v1:j"
ALPHEON_ASA_ID = 3706444728


def compute_report_sha256(
    report_uuid: str,
    service_type: str,
    hexagram_or_pillar_key: str,
    report_markdown: str,
) -> str:
    """
    Computes a canonical SHA-256 hex digest over an AI Oracle consultation report.
    """
    canonical_blob = "|".join(
        [
            report_uuid.strip(),
            service_type.strip().upper(),
            hexagram_or_pillar_key.strip(),
            report_markdown.strip(),
        ]
    )
    return hashlib.sha256(canonical_blob.encode("utf-8")).hexdigest()


def build_oracle_proof_payload(
    report_uuid: str,
    service_type: str,
    hexagram_binary: str,
    report_markdown: str,
) -> str:
    """
    Formats an ARC-0002 compliant transaction note payload (<1,024 bytes) suitable
    for attaching to an Algorand Mainnet transaction.
    """
    digest_hex = compute_report_sha256(
        report_uuid=report_uuid,
        service_type=service_type,
        hexagram_or_pillar_key=hexagram_binary,
        report_markdown=report_markdown,
    )
    payload = {
        "p": "CASTALIEN_ORACLE",
        "uuid": report_uuid,
        "svc": service_type,
        "hex": hexagram_binary,
        "sha256": digest_hex,
        "ts": int(datetime.now(timezone.utc).timestamp()),
        "asa": ALPHEON_ASA_ID,
    }
    return f"{ARC2_PREFIX}{json.dumps(payload, separators=(',', ':'))}"


def notarize_report_via_note(
    report_uuid: str,
    service_type: str,
    hexagram_binary: str,
    report_markdown: str,
    signer_mnemonic: Optional[str] = None,
    algod_url: str = DEFAULT_ALGOD_URL,
) -> Dict[str, Any]:
    """
    Broadcasts a 0-amount Alpheon ASA (3706444728) self-transfer carrying the ARC-0002
    Proof-of-Oracle SHA-256 payload in the transaction note field.
    Falls back to a 0-ALGO PaymentTxn if the signer account is not opted into ASA 3706444728.
    """
    note_str = build_oracle_proof_payload(
        report_uuid=report_uuid,
        service_type=service_type,
        hexagram_binary=hexagram_binary,
        report_markdown=report_markdown,
    )
    digest_hex = compute_report_sha256(
        report_uuid=report_uuid,
        service_type=service_type,
        hexagram_or_pillar_key=hexagram_binary,
        report_markdown=report_markdown,
    )

    mnemonic_phrase = signer_mnemonic or os.getenv("NOTARY_WALLET_MNEMONIC", "").strip()
    if not mnemonic_phrase:
        return {
            "status": "DRY_RUN_READY",
            "report_uuid": report_uuid,
            "sha256": digest_hex,
            "arc2_note": note_str,
        }

    from algosdk import account, mnemonic, transaction
    from algosdk.v2client import algod

    private_key = mnemonic.to_private_key(mnemonic_phrase)
    sender_addr = account.address_from_private_key(private_key)
    client = algod.AlgodClient("", algod_url)
    params = client.suggested_params()

    try:
        txn = transaction.AssetTransferTxn(
            sender=sender_addr,
            sp=params,
            receiver=sender_addr,
            amt=0,
            index=ALPHEON_ASA_ID,
            note=note_str.encode("utf-8"),
        )
        signed_txn = txn.sign(private_key)
        txid = client.send_transaction(signed_txn)
    except Exception:
        txn = transaction.PaymentTxn(
            sender=sender_addr,
            sp=params,
            receiver=sender_addr,
            amt=0,
            note=note_str.encode("utf-8"),
        )
        signed_txn = txn.sign(private_key)
        txid = client.send_transaction(signed_txn)

    return {
        "status": "SUBMITTED_MAINNET",
        "txid": txid,
        "explorer_url": f"https://explorer.perawallet.app/tx/{txid}",
        "report_uuid": report_uuid,
        "sha256": digest_hex,
    }
