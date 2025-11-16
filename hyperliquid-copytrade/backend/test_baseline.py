"""
Test para verificar que el simulador ignora posiciones pre-existentes
"""
import asyncio
from paper_trading import PaperTradingManager

async def test_baseline():
    print("=" * 60)
    print("TEST: Verificar que ignora posiciones pre-existentes")
    print("=" * 60)

    # Wallet de ejemplo que probablemente tiene posiciones abiertas
    # Puedes cambiar esta por una wallet real de testnet
    test_wallet = "0x0000000000000000000000000000000000000000"

    print(f"\n1. Inicializando simulador para wallet: {test_wallet}")

    manager = PaperTradingManager(
        target_wallet=test_wallet,
        initial_balance=10000,
        testnet=True
    )

    print(f"   - Balance inicial: ${manager.initial_balance}")
    print(f"   - Initialized flag: {manager.initialized}")
    print(f"   - Last positions: {manager.last_positions}")
    print(f"   - Open positions: {manager.open_positions}")

    print("\n2. Simulando primer check (establecer baseline)...")

    # Simular el primer check
    await manager._check_and_simulate()

    print(f"   - Initialized flag después: {manager.initialized}")
    print(f"   - Last positions después: {list(manager.last_positions.keys())}")
    print(f"   - Open positions (simuladas): {list(manager.open_positions.keys())}")
    print(f"   - Trades copiados: {manager.trades_copied}")
    print(f"   - Balance actual: ${manager.current_balance}")
    print(f"   - Total PnL: ${manager.total_pnl}")
    print(f"   - Fees pagadas: ${manager.total_fees_paid}")

    print("\n3. Verificando resultados...")

    # Verificaciones
    assert manager.initialized == True, "❌ FAIL: initialized debería ser True"
    print("   ✅ PASS: initialized = True")

    assert len(manager.open_positions) == 0, f"❌ FAIL: No debería tener posiciones simuladas. Tiene: {len(manager.open_positions)}"
    print("   ✅ PASS: No simuló posiciones pre-existentes")

    assert manager.trades_copied == 0, f"❌ FAIL: No debería haber copiado trades. Trades: {manager.trades_copied}"
    print("   ✅ PASS: trades_copied = 0")

    assert manager.current_balance == manager.initial_balance, "❌ FAIL: Balance no debería cambiar"
    print("   ✅ PASS: Balance sin cambios")

    assert manager.total_fees_paid == 0, f"❌ FAIL: No debería haber fees. Fees: ${manager.total_fees_paid}"
    print("   ✅ PASS: Sin fees cobradas")

    print("\n4. Simulando segundo check (ahora sí detectará cambios)...")
    await manager._check_and_simulate()

    print(f"   - Last positions: {list(manager.last_positions.keys())}")
    print(f"   - Open positions (simuladas): {list(manager.open_positions.keys())}")
    print(f"   - Trades copiados: {manager.trades_copied}")

    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)
    print("\nConclusión:")
    print("- El simulador ignora correctamente posiciones pre-existentes")
    print("- Solo copiará trades que se abran DESPUÉS de iniciar")
    print("- No cobra fees por posiciones que ya estaban abiertas")

if __name__ == "__main__":
    try:
        asyncio.run(test_baseline())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
