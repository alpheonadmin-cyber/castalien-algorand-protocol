"""
CASTALIEN Protocol — Algorand Python (ARC-4 / Puya) Smart Contract
==================================================================
Mainnet Reference App ID : 3724012001
Alpheon Utility ASA ID   : 3706444728 (ALP)
Castalia Governance ASA  : 3706444716 (CST)

Core Responsibilities:
1. Proof-of-Oracle Notarization: Anchors SHA-256 hashes of AI 1KICHING & Saju
   consultation reports on Algorand Mainnet with immutable timestamps.
2. 4SEEKER Daily Faucet Vault: Distributes 8 ALP daily attendance rewards to
   verified Pera Wallet accounts opted into ASA 3706444728.
3. 5DEX Atomic ALGO -> ALP Swap: Deterministic on-chain exchange at the protocol
   equivalence rate (1 ALGO = 1,024 ALP).
"""

from algopy import (
    ARC4Contract,
    Account,
    Asset,
    BoxMap,
    Global,
    PaymentTransaction,
    String,
    Txn,
    UInt64,
    arc4,
    gtxn,
    itxn,
    op,
)


class CastalienProtocol(ARC4Contract):
    """
    ARC-4 Smart Contract powering the CASTALIEN AI Oracle & Loyalty Ecosystem
    on Algorand Mainnet (https://algo.alpheon.org/).
    """

    def __init__(self) -> None:
        # Protocol Governance & Asset Configuration
        self.manager = Txn.sender
        self.alpheon_asa_id = UInt64(3706444728)   # Alpheon (ALP)
        self.castalia_asa_id = UInt64(3706444716)  # Castalia (CST)

        # Economic Constants (1 ALGO = 1,024 ALP; Daily Faucet = 8 ALP)
        self.swap_rate_alp_per_algo = UInt64(1024)
        self.daily_faucet_reward_alp = UInt64(8)

        # On-Chain Telemetry Counters
        self.total_notarized_reports = UInt64(0)
        self.total_faucet_claims = UInt64(0)

        # Box Map: report_uuid -> 32-byte SHA-256 digest of AI Oracle Report
        self.oracle_proofs = BoxMap(arc4.String, arc4.StaticArray[arc4.Byte, 32])
        # Box Map: user Account -> last claim Unix timestamp (24h cooldown)
        self.last_faucet_claim = BoxMap(Account, UInt64)

    @arc4.abimethod
    def configure_assets(self, alp_asa: Asset, cst_asa: Asset) -> None:
        """
        Opts the smart contract application account into Alpheon (ALP) and Castalia (CST).
        Restricted to the protocol manager.
        """
        self._only_manager()
        self.alpheon_asa_id = alp_asa.id
        self.castalia_asa_id = cst_asa.id

        itxn.AssetTransfer(
            xfer_asset=alp_asa,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=0,
        ).submit()

        itxn.AssetTransfer(
            xfer_asset=cst_asa,
            asset_receiver=Global.current_application_address,
            asset_amount=0,
            fee=0,
        ).submit()

    @arc4.abimethod
    def notarize_oracle_report(
        self,
        report_uuid: arc4.String,
        service_type: arc4.String,
        report_sha256: arc4.StaticArray[arc4.Byte, 32],
    ) -> arc4.UInt64:
        """
        Anchors a 1KICHING or Astronomical Saju AI consultation report hash on-chain.
        Creates an immutable Proof-of-Oracle record verifiable on Algorand Mainnet.
        """
        self._only_manager()
        self.oracle_proofs[report_uuid] = report_sha256.copy()
        self.total_notarized_reports += UInt64(1)
        op.log(report_uuid.bytes)
        op.log(service_type.bytes)
        return arc4.UInt64(self.total_notarized_reports)

    @arc4.abimethod(readonly=True)
    def verify_oracle_report(
        self,
        report_uuid: arc4.String,
        candidate_sha256: arc4.StaticArray[arc4.Byte, 32],
    ) -> arc4.Bool:
        """
        Read-only ABI method allowing any user or auditor to verify whether a given
        AI consultation report matches the immutable SHA-256 digest stored on-chain.
        """
        if report_uuid not in self.oracle_proofs:
            return arc4.Bool(False)
        stored_hash = self.oracle_proofs[report_uuid].copy()
        return arc4.Bool(stored_hash.bytes == candidate_sha256.bytes)

    @arc4.abimethod
    def claim_daily_faucet(self, recipient: Account) -> arc4.UInt64:
        """
        4SEEKER Digital Forest Daily Faucet:
        Distributes 8 ALP (ASA 3706444728) once every 24 hours (86,400s) to a verified
        Pera Wallet holder opted into Alpheon.
        """
        self._only_manager()
        now = Global.latest_timestamp
        if recipient in self.last_faucet_claim:
            last_ts = self.last_faucet_claim[recipient]
            assert now >= last_ts + UInt64(86400), "Daily 8 ALP faucet cooldown active (24h)"

        self.last_faucet_claim[recipient] = now
        self.total_faucet_claims += UInt64(1)

        itxn.AssetTransfer(
            xfer_asset=Asset(self.alpheon_asa_id),
            asset_receiver=recipient,
            asset_amount=self.daily_faucet_reward_alp,
            note=b"CASTALIEN:4SEEKER:DAILY_8_ALP",
            fee=0,
        ).submit()

        return arc4.UInt64(self.daily_faucet_reward_alp)

    @arc4.abimethod
    def atomic_swap_algo_for_alp(self, algo_payment: gtxn.PaymentTransaction) -> arc4.UInt64:
        """
        5DEX Atomic Swap:
        Accepts native ALGO payment (>= 1 ALGO) in an atomic transaction group and
        instantly settles Alpheon (ALP) at 1 ALGO = 1,024 ALP.
        """
        assert algo_payment.receiver == Global.current_application_address, "Invalid treasury receiver"
        assert algo_payment.amount >= UInt64(1_000_000), "Minimum swap is 1 ALGO (1,000,000 microAlgos)"

        # Integer division: 1,000,000 microAlgos -> 1,024 ALP (Decimals = 0)
        alp_out = (algo_payment.amount * self.swap_rate_alp_per_algo) // UInt64(1_000_000)
        assert alp_out > UInt64(0), "Computed ALP output must be positive"

        itxn.AssetTransfer(
            xfer_asset=Asset(self.alpheon_asa_id),
            asset_receiver=algo_payment.sender,
            asset_amount=alp_out,
            note=b"CASTALIEN:5DEX:ATOMIC_SWAP_1024_ALP",
            fee=0,
        ).submit()

        return arc4.UInt64(alp_out)

    def _only_manager(self) -> None:
        assert Txn.sender == self.manager, "Unauthorized: Only protocol manager may invoke"
