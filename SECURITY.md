# 🔒 Security Policy (`castalien-algorand-protocol`)

## Supported Versions & Mainnet Assets

| Component | Identifier | Network | Status |
| :--- | :--- | :--- | :--- |
| **Alpheon (`ALP`)** | `ASA 3706444728` | Algorand Mainnet | Active / Supported |
| **Castalia (`CST`)** | `ASA 3706444716` | Algorand Mainnet | Active / Supported |
| **Protocol Application** | `App ID 3724012001` | Algorand Mainnet | Active / Supported |

## Key Management & Repository Isolation

1. **Zero Secret Storage in Public Code:** No private keys, mnemonics, or internal database credentials are stored in this repository. All signing keys are strictly injected via isolated server environment variables (`.env`).
2. **Public vs. Private Architecture Separation:** This repository exposes only the public Algorand smart contract interface, ARC-69/Pera asset metadata, and client-side `ARC-0002` verification SDK. Internal AI reasoning pipelines and backend accounting services are isolated in private infrastructure.
3. **On-Chain Transaction Verification:** All `5DEX` deposits and `Proof-of-Oracle` notarizations are cryptographically verified against Algorand Mainnet round confirmations.

## Reporting a Vulnerability

If you discover a potential security issue, please report it privately to:
- **Email:** `admin@alpheon.org`
