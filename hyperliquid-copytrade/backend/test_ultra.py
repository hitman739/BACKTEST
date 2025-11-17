"""
Test script for Ultra-Low Latency Copy Trading System
"""
import asyncio
import logging
from ultra_copytrader import UltraCopyTrader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_ultra_system():
    """Test the ultra copy trading system"""

    logger.info("=" * 70)
    logger.info("⚡ Testing Ultra-Low Latency Copy Trading System")
    logger.info("=" * 70)
    logger.info("")

    # Test parameters
    test_api_key = input("Enter your API key (or 'skip' to skip): ")

    if test_api_key.lower() == 'skip':
        logger.info("⚠️ Skipping test (no API key provided)")
        logger.info("")
        logger.info("To test properly, you need:")
        logger.info("  1. Hyperliquid API key + secret")
        logger.info("  2. Target wallet address to copy")
        logger.info("  3. Some balance in your account")
        logger.info("")
        logger.info("Example:")
        logger.info("  python test_ultra.py")
        logger.info("  Enter API key: your_key_here")
        logger.info("  Enter API secret: your_secret_here")
        logger.info("  Enter target wallet: 0x...")
        logger.info("")
        return

    test_api_secret = input("Enter your API secret: ")
    test_target_wallet = input("Enter target wallet to copy: ")
    test_copy_ratio = float(input("Enter copy ratio (default 0.1 for 10%): ") or "0.1")
    use_testnet = input("Use testnet? (y/n, default n): ").lower() == 'y'

    logger.info("")
    logger.info(f"Configuration:")
    logger.info(f"  Target wallet: {test_target_wallet}")
    logger.info(f"  Copy ratio: {test_copy_ratio * 100}%")
    logger.info(f"  Testnet: {use_testnet}")
    logger.info("")

    # Create copy trader
    logger.info("1️⃣ Creating UltraCopyTrader...")
    copy_trader = UltraCopyTrader(
        api_key=test_api_key,
        api_secret=test_api_secret,
        target_wallet=test_target_wallet,
        copy_ratio=test_copy_ratio,
        testnet=use_testnet
    )
    logger.info("✅ Copy trader created")
    logger.info("")

    # Start copy trading
    logger.info("2️⃣ Starting copy trading...")
    try:
        await copy_trader.start()
        logger.info("✅ Copy trading started successfully")
        logger.info("")
    except Exception as e:
        logger.error(f"❌ Failed to start: {e}")
        logger.info("")
        logger.info("Common issues:")
        logger.info("  - Check API keys are correct")
        logger.info("  - Check wallet address is valid")
        logger.info("  - Check you have balance in account")
        logger.info("  - Check Hyperliquid API is accessible")
        return

    # Run for a bit
    logger.info("3️⃣ Monitoring for 60 seconds...")
    logger.info("   Waiting for target trader to make trades...")
    logger.info("   (If trader doesn't trade, nothing will happen)")
    logger.info("")

    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️ Interrupted by user")

    # Show stats
    logger.info("")
    logger.info("4️⃣ Getting statistics...")
    stats = copy_trader.get_stats()

    logger.info("")
    logger.info("=" * 70)
    logger.info("📊 FINAL STATISTICS")
    logger.info("=" * 70)
    logger.info(f"Trades Copied: {stats['trades_copied']}")
    logger.info(f"Average Latency: {stats['avg_latency_ms']:.1f}ms")

    if stats['trades_copied'] > 0:
        logger.info(f"Min Latency: {stats['min_latency_ms']:.1f}ms")
        logger.info(f"Max Latency: {stats['max_latency_ms']:.1f}ms")

    logger.info(f"My Positions: {stats['my_positions']}")
    logger.info(f"Target Positions: {stats['target_positions']}")
    logger.info(f"My Account Value: ${stats['my_account_value']:,.2f}")
    logger.info(f"Target Account Value: ${stats['target_account_value']:,.2f}")
    logger.info("=" * 70)
    logger.info("")

    # Stop
    logger.info("5️⃣ Stopping copy trading...")
    await copy_trader.stop()
    logger.info("✅ Stopped")
    logger.info("")

    logger.info("=" * 70)
    logger.info("✅ TEST COMPLETE")
    logger.info("=" * 70)

    if stats['trades_copied'] == 0:
        logger.info("")
        logger.info("ℹ️ No trades were copied because:")
        logger.info("   - Target trader didn't open/close any positions")
        logger.info("   - This is normal if trader is inactive")
        logger.info("   - Try again when trader is actively trading")
        logger.info("")


if __name__ == "__main__":
    asyncio.run(test_ultra_system())
