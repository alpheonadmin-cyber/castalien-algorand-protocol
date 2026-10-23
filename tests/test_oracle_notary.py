"""
Unit tests for the CASTALIEN Proof-of-Oracle Notary SDK & 5DEX Tokenomics
"""

import json
from sdk.oracle_notary import (
    ARC2_PREFIX,
    build_oracle_proof_payload,
    compute_report_sha256,
    notarize_report_via_note,
)
from sdk.algorand_verifier import calculate_dex_swap_quote


def test_deterministic_report_sha256():
    digest_1 = compute_report_sha256(
        report_uuid="RPT-20261023-0001",
        service_type="ORACLE_ICHING",
        hexagram_or_pillar_key="111101",
        report_markdown="# Hexagram 14: Possession in Great Measure",
    )
    digest_2 = compute_report_sha256(
        report_uuid="RPT-20261023-0001",
        service_type="oracle_iching",
        hexagram_or_pillar_key="111101",
        report_markdown="# Hexagram 14: Possession in Great Measure\n",
    )
    assert len(digest_1) == 64
    assert digest_1 == digest_2


def test_arc2_proof_payload_format_and_size():
    note_str = build_oracle_proof_payload(
        report_uuid="RPT-20261023-0001",
        service_type="ORACLE_SAJU",
        hexagram_binary="JIA-ZI",
        report_markdown="# Astronomical Saju Consultation Report",
    )
    assert note_str.startswith(ARC2_PREFIX)
    # Algorand transaction note field limit is 1024 bytes
    assert len(note_str.encode("utf-8")) <= 1024

    json_part = note_str[len(ARC2_PREFIX) :]
    parsed = json.loads(json_part)
    assert parsed["p"] == "CASTALIEN_ORACLE"
    assert parsed["uuid"] == "RPT-20261023-0001"
    assert parsed["asa"] == 3706444728
    assert len(parsed["sha256"]) == 64


def test_dry_run_notarization_without_mnemonic():
    res = notarize_report_via_note(
        report_uuid="RPT-20261023-0002",
        service_type="ORACLE_ICHING",
        hexagram_binary="111111",
        report_markdown="# Hexagram 1: The Creative",
        signer_mnemonic="",
    )
    assert res["status"] == "DRY_RUN_READY"
    assert res["report_uuid"] == "RPT-20261023-0002"


def test_5dex_dual_mode_swap_quotes():
    quote_algo = calculate_dex_swap_quote("ALGO", 1.0, settlement_mode="AUTO_SWAP_ALP")
    assert quote_algo["alp_output"] == 1024
    assert quote_algo["eon_output"] == 10240

    quote_portal = calculate_dex_swap_quote("ALGO", 2.5, settlement_mode="PORTAL_EON_CREDIT")
    assert quote_portal["alp_output"] == 2560
    assert quote_portal["eon_output"] == 25600

    quote_cst = calculate_dex_swap_quote("CST", 1.0)
    assert quote_cst["alp_output"] == 1000
    assert quote_cst["eon_output"] == 10000
