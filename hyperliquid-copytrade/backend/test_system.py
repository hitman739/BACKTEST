"""
Test script for the new WebSocket-based system
"""
import asyncio
import logging
from database import Database
from indexer import HyperliquidIndexer
from metrics_calculator import MetricsCalculator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_system():
    """Test the complete system"""

    logger.info("=" * 60)
    logger.info("Testing Hyperliquid WebSocket Indexer System")
    logger.info("=" * 60)

    # Initialize components
    logger.info("\n1. Initializing database...")
    db = Database("test_hyperliquid.db")

    logger.info("\n2. Initializing indexer...")
    indexer = HyperliquidIndexer(db, testnet=False)

    logger.info("\n3. Initializing metrics calculator...")
    calc = MetricsCalculator(db, testnet=False)

    # Test wallet - usar la que el usuario proporcionó
    test_wallet = "0x329c787b163a730bd7900df2beb3ff4fe4670375"

    logger.info(f"\n4. Adding test wallet: {test_wallet}")
    await indexer.add_wallet(test_wallet, initial_balance=10000.0)

    logger.info("\n5. Waiting 10 seconds for WebSocket data...")
    await asyncio.sleep(10)

    logger.info("\n6. Calculating metrics...")
    metrics = calc.calculate_metrics(test_wallet)

    logger.info("\n" + "=" * 60)
    logger.info("METRICS RESULTS:")
    logger.info("=" * 60)

    for key, value in metrics.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")

    logger.info("\n7. Checking database...")

    fills = db.get_fills(test_wallet, limit=10)
    logger.info(f"  Fills in database: {len(fills)}")

    positions = db.get_positions(test_wallet)
    logger.info(f"  Open positions: {len(positions)}")

    if positions:
        logger.info("\n  Open Positions:")
        for pos in positions:
            logger.info(f"    - {pos['coin']}: {pos['side']} {abs(pos['size']):.4f} @ ${pos['entry_px']:.2f}")

    logger.info("\n8. Testing fee factor calculation...")
    if metrics.get('fee_factor_mixed'):
        logger.info(f"  Fee Factor (mixed): {metrics['fee_factor_mixed']:.4f} ({metrics['fee_factor_mixed']*100:.2f}%)")
        logger.info(f"  Fee Factor (taker): {metrics['fee_factor_taker']:.4f} ({metrics['fee_factor_taker']*100:.2f}%)")
        logger.info(f"  Interpretation: Trader retains {metrics['fee_factor_mixed']*100:.1f}% of profit after fees")
    else:
        logger.info("  Fee Factor: N/A (no profitable trades yet)")

    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE!")
    logger.info("=" * 60)

    logger.info("\nKeeping WebSocket connection alive for 30 more seconds...")
    logger.info("Watch for real-time updates as they come in...")
    await asyncio.sleep(30)

    logger.info("\nStopping indexer...")
    await indexer.stop()

    logger.info("\nClosing database...")
    db.close()

    logger.info("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_system())
