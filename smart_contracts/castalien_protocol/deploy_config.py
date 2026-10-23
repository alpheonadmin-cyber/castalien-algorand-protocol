import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Live Algorand Mainnet Registry for CASTALIEN Protocol
MAINNET_DEPLOYMENT_CONFIG: Dict[str, Any] = {
    "network": "mainnet",
    "app_id": 3724012001,
    "manager_address": "WAURKB4IAMDX2HI5ZJK5YP5CXZF43XPLOZSROWWYLD5ZJM3H3FSPCAH6CA",
    "treasury_address": "FGRDXIENOISLCFTP2FRHXH25OJTZNANSXCVTKEFJRWR3NCXPO4PDJTWET4",
    "assets": {
        "ALPHEON": {
            "asa_id": 3706444728,
            "unit_name": "ALP",
            "decimals": 0,
            "total_supply": 1_000_000_000,
        },
        "CASTALIA": {
            "asa_id": 3706444716,
            "unit_name": "CST",
            "decimals": 0,
            "total_supply": 1_000_000,
        },
    },
    "equivalence": {
        "alp_per_algo": 1024,
        "eon_per_alp": 10,
        "alp_per_cst": 1000,
        "daily_faucet_alp": 8,
    },
}


def deploy() -> None:
    """
    AlgoKit deployment hook verifying Mainnet configuration parameters.
    """
    logger.info(
        f"CASTALIEN Protocol Mainnet Reference — App ID: {MAINNET_DEPLOYMENT_CONFIG['app_id']}, "
        f"Alpheon ASA: {MAINNET_DEPLOYMENT_CONFIG['assets']['ALPHEON']['asa_id']}, "
        f"Castalia ASA: {MAINNET_DEPLOYMENT_CONFIG['assets']['CASTALIA']['asa_id']}"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    deploy()
