"""
Paper Trading Manager
Simula copy trading sin dinero real, incluyendo fees de Hyperliquid
"""
import asyncio
import logging
from typing import Callable, Optional, List, Dict
from datetime import datetime
from hyperliquid.info import Info
from hyperliquid.utils import constants

logger = logging.getLogger(__name__)


class PaperTradingManager:
    """Simula copy trading con dinero fake"""

    # Hyperliquid fees
    MAKER_FEE = 0.0002  # 0.02% (puede ser negativo con rebate)
    TAKER_FEE = 0.0005  # 0.05%

    def __init__(
        self,
        target_wallet: str,
        initial_balance: float = 10000.0,  # $10k inicial
        testnet: bool = True,
        callback: Optional[Callable] = None
    ):
        self.target_wallet = target_wallet
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.testnet = testnet
        self.callback = callback

        # State
        self.is_running = False
        self.trades_copied = 0
        self.last_positions = {}
        self.open_positions = {}  # {coin: position_data}
        self.trade_history = []  # Lista de todos los trades
        self.total_pnl = 0.0
        self.total_fees_paid = 0.0
        self.initialized = False  # Flag para ignorar posiciones pre-existentes
        self.fee_factor_ratio = None  # FFr calculado de datos históricos (75% maker, 25% taker)
        self.fee_factor_ratio_taker = None  # FFr con 100% taker (peor caso)

        # Initialize Hyperliquid Info client (solo para leer)
        base_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        self.info = Info(base_url, skip_ws=True)

        logger.info(f"Initialized PaperTradingManager")
        logger.info(f"Target wallet: {target_wallet}")
        logger.info(f"Initial balance: ${initial_balance:,.2f}")
        logger.info(f"Testnet: {testnet}")

    async def start(self):
        """Start paper trading"""
        self.is_running = True
        logger.info("Starting paper trading...")

        await self._send_update({
            "type": "info",
            "message": f"Paper trading iniciado. Simulando con ${self.initial_balance:,.2f}"
        })

        try:
            while self.is_running:
                await self._check_and_simulate()
                await asyncio.sleep(5)  # Check every 5 seconds

        except Exception as e:
            logger.error(f"Error in paper trading loop: {e}")
            await self._send_update({
                "type": "error",
                "message": f"Error: {str(e)}"
            })
            self.is_running = False

    async def stop(self):
        """Stop paper trading"""
        self.is_running = False
        logger.info("Stopping paper trading...")

        # Send final summary
        await self._send_summary()

    async def _check_and_simulate(self):
        """Check target wallet and simulate trades"""
        try:
            # Get target wallet's current positions
            user_state = self.info.user_state(self.target_wallet)

            if not user_state:
                logger.warning("No user state returned from API")
                return

            current_positions = {}

            # Parse positions
            if "assetPositions" in user_state:
                for position in user_state["assetPositions"]:
                    if "position" in position:
                        pos = position["position"]
                        coin = pos["coin"]
                        size = float(pos["szi"])

                        if size != 0:
                            current_positions[coin] = {
                                "size": size,
                                "entry_px": float(pos.get("entryPx", 0)),
                                "leverage": float(pos.get("leverage", {}).get("value", 1)),
                                "margin_used": float(pos.get("marginUsed", 0)),
                            }

            # Get target account value
            target_account_value = float(user_state.get("marginSummary", {}).get("accountValue", 0))

            if target_account_value == 0:
                logger.warning("Target account value is 0")
                return

            # Si es la primera vez, solo guardamos las posiciones actuales (baseline)
            # NO las copiamos porque ya existían antes de iniciar la simulación
            if not self.initialized:
                self.last_positions = current_positions
                self.initialized = True
                logger.info(f"Baseline establecido. Posiciones pre-existentes ignoradas: {list(current_positions.keys())}")
                await self._send_update({
                    "type": "info",
                    "message": f"Baseline: {len(current_positions)} posiciones pre-existentes ignoradas. Esperando nuevos trades..."
                })
                return

            # Process changes (solo después de establecer baseline)
            await self._process_position_changes(current_positions, target_account_value)

            # Update last positions
            self.last_positions = current_positions

        except Exception as e:
            logger.error(f"Error checking positions: {e}")

    async def _process_position_changes(self, current_positions: dict, target_account_value: float):
        """Process position changes and simulate trades"""

        # Check for new positions
        for coin, pos_data in current_positions.items():
            if coin not in self.last_positions:
                # New position opened
                await self._simulate_open(coin, pos_data, target_account_value)

        # Check for closed positions
        for coin in self.last_positions:
            if coin not in current_positions:
                # Position closed
                await self._simulate_close(coin)

        # Check for position size changes
        for coin, pos_data in current_positions.items():
            if coin in self.last_positions:
                old_size = self.last_positions[coin]["size"]
                new_size = pos_data["size"]

                if abs(new_size - old_size) > 0.0001:
                    # Size changed (DCA or partial close)
                    await self._simulate_adjust(coin, pos_data, target_account_value)

    async def _simulate_open(self, coin: str, pos_data: dict, target_account_value: float):
        """Simulate opening a position"""
        try:
            # Calculate margin % used by target
            margin_used = pos_data["margin_used"]
            margin_pct = (margin_used / target_account_value) * 100

            # Calculate my position size
            my_margin = (margin_pct / 100) * self.current_balance
            leverage = pos_data["leverage"]
            entry_px = pos_data["entry_px"]

            if entry_px == 0:
                logger.warning(f"Entry price is 0 for {coin}")
                return

            # Calculate size
            my_size = (my_margin * leverage) / entry_px
            is_buy = pos_data["size"] > 0

            # Calculate fee (assuming taker fee for market order)
            position_value = abs(my_size) * entry_px
            fee = position_value * self.TAKER_FEE
            self.total_fees_paid += fee

            # Store position
            self.open_positions[coin] = {
                "coin": coin,
                "size": my_size,
                "entry_price": entry_px,
                "is_long": is_buy,
                "margin_used": my_margin,
                "leverage": leverage,
                "opened_at": datetime.now().isoformat(),
                "fees_paid": fee
            }

            self.trades_copied += 1

            # Log trade
            trade = {
                "type": "open",
                "coin": coin,
                "size": my_size,
                "entry_price": entry_px,
                "is_long": is_buy,
                "margin_pct": margin_pct,
                "fee": fee,
                "timestamp": datetime.now().isoformat()
            }
            self.trade_history.append(trade)

            await self._send_update({
                "type": "trade",
                "action": "opened",
                "coin": coin,
                "size": my_size,
                "entry_price": entry_px,
                "is_long": is_buy,
                "margin_pct": margin_pct,
                "fee": fee,
                "balance": self.current_balance,
                "total_pnl": self.total_pnl
            })

            logger.info(f"Simulated OPEN: {coin}, size={my_size:.4f}, entry=${entry_px:.2f}, fee=${fee:.2f}")

        except Exception as e:
            logger.error(f"Error simulating open {coin}: {e}")

    async def _simulate_close(self, coin: str):
        """Simulate closing a position"""
        try:
            if coin not in self.open_positions:
                logger.info(f"No open position to close for {coin}")
                return

            position = self.open_positions[coin]

            # Get current price from market
            current_price = self._get_current_price(coin)

            if current_price == 0:
                logger.warning(f"Could not get current price for {coin}, skipping close")
                return

            # Calculate PnL
            size = position["size"]
            entry_price = position["entry_price"]
            is_long = position["is_long"]

            if is_long:
                pnl = size * (current_price - entry_price)
            else:
                pnl = abs(size) * (entry_price - current_price)

            # Calculate closing fee
            position_value = abs(size) * current_price
            fee = position_value * self.TAKER_FEE
            self.total_fees_paid += fee

            # Net PnL (after fees)
            net_pnl = pnl - position["fees_paid"] - fee

            # Update balance
            self.current_balance += net_pnl
            self.total_pnl += net_pnl

            # Log trade
            trade = {
                "type": "close",
                "coin": coin,
                "size": size,
                "entry_price": entry_price,
                "exit_price": current_price,
                "pnl": pnl,
                "fees": position["fees_paid"] + fee,
                "net_pnl": net_pnl,
                "timestamp": datetime.now().isoformat()
            }
            self.trade_history.append(trade)

            # Remove from open positions
            del self.open_positions[coin]

            self.trades_copied += 1

            await self._send_update({
                "type": "trade",
                "action": "closed",
                "coin": coin,
                "size": size,
                "entry_price": entry_price,
                "exit_price": current_price,
                "pnl": pnl,
                "fees": position["fees_paid"] + fee,
                "net_pnl": net_pnl,
                "balance": self.current_balance,
                "total_pnl": self.total_pnl
            })

            logger.info(f"Simulated CLOSE: {coin}, pnl=${pnl:.2f}, fees=${fee:.2f}, net_pnl=${net_pnl:.2f}")

        except Exception as e:
            logger.error(f"Error simulating close {coin}: {e}")

    async def _simulate_adjust(self, coin: str, pos_data: dict, target_account_value: float):
        """Simulate adjusting position (DCA or partial close)"""
        # For simplicity, we'll close and reopen with new size
        # In a more sophisticated version, we'd track each entry separately
        logger.info(f"Position adjustment for {coin} (closing and reopening)")

        # Close current
        if coin in self.open_positions:
            await self._simulate_close(coin)

        # Reopen with new size
        await self._simulate_open(coin, pos_data, target_account_value)

    def _get_current_price(self, coin: str) -> float:
        """Get current market price for a coin"""
        try:
            # Get all mids (current prices)
            all_mids = self.info.all_mids()

            if coin in all_mids:
                price = float(all_mids[coin])
                return price
            else:
                logger.warning(f"No price found for {coin}")
                return 0.0

        except Exception as e:
            logger.error(f"Error getting price for {coin}: {e}")
            return 0.0

    async def _send_summary(self):
        """Send final summary of paper trading session"""
        roi = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100

        summary = {
            "type": "summary",
            "initial_balance": self.initial_balance,
            "final_balance": self.current_balance,
            "total_pnl": self.total_pnl,
            "total_fees_paid": self.total_fees_paid,
            "roi": roi,
            "trades_copied": self.trades_copied,
            "open_positions": len(self.open_positions),
            "trade_history": self.trade_history[-10:]  # Last 10 trades
        }

        await self._send_update(summary)

    async def _send_update(self, update: dict):
        """Send update via callback"""
        if self.callback:
            try:
                await self.callback(update)
            except Exception as e:
                logger.error(f"Error sending update: {e}")

    def _calculate_unrealized_pnl(self) -> float:
        """Calcula el PnL no realizado de las posiciones abiertas"""
        unrealized_pnl = 0.0

        for coin, position in self.open_positions.items():
            try:
                # Obtener precio actual
                current_price = self._get_current_price(coin)

                if current_price == 0:
                    logger.warning(f"No se pudo obtener precio para {coin}, ignorando PnL")
                    continue

                # Calcular PnL según si es long o short
                size = position["size"]
                entry_price = position["entry_price"]
                is_long = position["is_long"]

                if is_long:
                    pnl = size * (current_price - entry_price)
                else:
                    pnl = abs(size) * (entry_price - current_price)

                unrealized_pnl += pnl

            except Exception as e:
                logger.error(f"Error calculando PnL para {coin}: {e}")

        return unrealized_pnl

    def _calculate_fee_factor_ratio(self) -> float:
        """
        Calcula el Fee Factor Ratio basado en datos históricos del trader.
        FFr = profit_neto / profit_bruto

        Asume 75% maker, 25% taker
        """
        try:
            # Obtener estadísticas del usuario
            user_state = self.info.user_state(self.target_wallet)

            if not user_state:
                return None

            # Extraer accountValue como proxy de profit histórico
            # Nota: Hyperliquid API no expone directamente profit histórico total
            # Usaremos PNL acumulado si está disponible
            margin_summary = user_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))

            # Intentar obtener datos de fills históricos para calcular volumen
            # Esto requiere usar user_fills
            try:
                fills = self.info.user_fills(self.target_wallet)

                if not fills or len(fills) == 0:
                    return None

                total_volume = 0.0
                gross_profit = 0.0

                # Calcular volumen total y profit bruto de los fills
                for fill in fills:
                    # Volumen = precio * size
                    px = float(fill.get("px", 0))
                    sz = abs(float(fill.get("sz", 0)))
                    total_volume += px * sz

                    # PnL de cada fill (si está disponible)
                    if "closedPnl" in fill:
                        gross_profit += float(fill.get("closedPnl", 0))

                # Si no hay profit bruto o es negativo, retornar None
                if gross_profit <= 0:
                    return None

                # Calcular fee rate mezclado (75% maker, 25% taker)
                MAKER_FEE = 0.00015  # 0.015%
                TAKER_FEE = 0.00045  # 0.045%
                mixed_fee_rate = 0.75 * MAKER_FEE + 0.25 * TAKER_FEE

                # Estimar fees pagadas
                estimated_fees = mixed_fee_rate * total_volume

                # Profit neto
                net_profit = gross_profit - estimated_fees

                # Fee Factor Ratio
                fee_factor_ratio = net_profit / gross_profit

                logger.info(f"FFr calculated: {fee_factor_ratio:.4f} (gross: ${gross_profit:.2f}, fees: ${estimated_fees:.2f}, net: ${net_profit:.2f})")

                return fee_factor_ratio

            except Exception as e:
                logger.warning(f"Could not calculate FFr from fills: {e}")
                return None

        except Exception as e:
            logger.error(f"Error calculating Fee Factor Ratio: {e}")
            return None

    def _calculate_fee_factor_ratio_taker(self) -> float:
        """
        Calcula el Fee Factor Ratio asumiendo 100% taker fees (peor caso).
        FFt = profit_neto / profit_bruto

        Asume 100% taker (0.045%)
        """
        try:
            # Obtener estadísticas del usuario
            user_state = self.info.user_state(self.target_wallet)

            if not user_state:
                return None

            # Intentar obtener datos de fills históricos para calcular volumen
            try:
                fills = self.info.user_fills(self.target_wallet)

                if not fills or len(fills) == 0:
                    return None

                total_volume = 0.0
                gross_profit = 0.0

                # Calcular volumen total y profit bruto de los fills
                for fill in fills:
                    # Volumen = precio * size
                    px = float(fill.get("px", 0))
                    sz = abs(float(fill.get("sz", 0)))
                    total_volume += px * sz

                    # PnL de cada fill (si está disponible)
                    if "closedPnl" in fill:
                        gross_profit += float(fill.get("closedPnl", 0))

                # Si no hay profit bruto o es negativo, retornar None
                if gross_profit <= 0:
                    return None

                # Usar 100% taker fee (peor caso)
                TAKER_FEE = 0.00045  # 0.045%

                # Estimar fees pagadas
                estimated_fees = TAKER_FEE * total_volume

                # Profit neto
                net_profit = gross_profit - estimated_fees

                # Fee Factor Ratio (taker)
                fee_factor_ratio_taker = net_profit / gross_profit

                logger.info(f"FFt calculated: {fee_factor_ratio_taker:.4f} (gross: ${gross_profit:.2f}, fees: ${estimated_fees:.2f}, net: ${net_profit:.2f})")

                return fee_factor_ratio_taker

            except Exception as e:
                logger.warning(f"Could not calculate FFt from fills: {e}")
                return None

        except Exception as e:
            logger.error(f"Error calculating Fee Factor Ratio (taker): {e}")
            return None

    def get_stats(self) -> dict:
        """Get current paper trading stats"""
        # Calcular PnL no realizado (posiciones abiertas)
        unrealized_pnl = self._calculate_unrealized_pnl()

        # PnL total = realizado + no realizado
        total_pnl_with_unrealized = self.total_pnl + unrealized_pnl

        # Balance incluyendo PnL no realizado
        balance_with_unrealized = self.current_balance + unrealized_pnl

        # ROI incluyendo posiciones abiertas
        roi = ((balance_with_unrealized - self.initial_balance) / self.initial_balance) * 100

        # Calcular Fee Factor Ratios solo una vez
        if self.fee_factor_ratio is None and self.initialized:
            self.fee_factor_ratio = self._calculate_fee_factor_ratio()

        if self.fee_factor_ratio_taker is None and self.initialized:
            self.fee_factor_ratio_taker = self._calculate_fee_factor_ratio_taker()

        return {
            "is_running": self.is_running,
            "target_wallet": self.target_wallet,
            "initial_balance": self.initial_balance,
            "current_balance": balance_with_unrealized,
            "total_pnl": total_pnl_with_unrealized,
            "realized_pnl": self.total_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_fees_paid": self.total_fees_paid,
            "roi": roi,
            "trades_copied": self.trades_copied,
            "open_positions": len(self.open_positions),
            "open_positions_list": list(self.open_positions.values()),
            "fee_factor_ratio": self.fee_factor_ratio,
            "fee_factor_ratio_taker": self.fee_factor_ratio_taker
        }
