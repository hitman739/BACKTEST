# 🚀 Cómo Usar el Sistema

Tienes dos modos disponibles:

---

## ⚡ OPCIÓN 1: Ultra Copy Trading (Producción)

**Uso**: Copy trading REAL con latencia mínima (<100ms)

### Iniciar Backend:

```bash
cd /home/user/BACKTEST/hyperliquid-copytrade/backend
./start_ultra.sh
```

### Iniciar Frontend:

```bash
cd /home/user/BACKTEST/hyperliquid-copytrade/frontend
npm run dev
```

### Usar:

1. Abre http://localhost:5173
2. Click en "ULTRA COPY TRADING"
3. Completa el formulario:
   - API Key
   - API Secret
   - Target Wallet (0x...)
   - Copy Ratio (1.0 = 100%)
   - Testnet (sí para pruebas)
4. Click "Iniciar Copy Trading"
5. Monitorea la latencia en tiempo real

**Importante:**
- ⚠️ Usa dinero real
- ✅ Empieza con testnet
- ✅ Usa copy ratio bajo (0.1-0.5)
- ✅ Monitorea latencia constantemente

---

## 📊 OPCIÓN 2: Simulator (Testing)

**Uso**: Testear múltiples traders con dinero fake

### Iniciar Backend:

```bash
cd /home/user/BACKTEST/hyperliquid-copytrade/backend
./start_v2.sh
```

### Iniciar Frontend:

```bash
cd /home/user/BACKTEST/hyperliquid-copytrade/frontend
npm run dev
```

### Usar:

1. Abre http://localhost:5173
2. Click en "SIMULATOR"
3. Añade wallets:
   - Pega dirección (0x...)
   - Ajusta balance inicial
   - Click "Add Wallet"
4. Observa métricas en tiempo real:
   - Equity
   - PnL
   - ROI
   - Fee Factor (FFr/FFt)
   - Trades
5. Compara múltiples traders
6. Elige el mejor para usar en Ultra Copy Trading

**Ventajas:**
- ✅ Sin riesgo (dinero fake)
- ✅ Múltiples wallets simultáneas
- ✅ Métricas completas
- ✅ Histórico guardado

---

## 🔧 Troubleshooting

### "No funciona cuando pego wallet"

**Causa**: Backend no está corriendo

**Solución**:
```bash
# Para Simulator
cd backend
./start_v2.sh

# Para Ultra Copy Trading
cd backend
./start_ultra.sh
```

### "Error 403 / Access denied"

**Causa**: Rate limit de Hyperliquid

**Solución**:
- Espera 30-60 minutos
- O usa testnet
- O usa el sistema ultra (tiene menos rate limiting)

### "Cannot connect to backend"

**Causa**: Backend no está en puerto 8000

**Solución**:
```bash
# Verificar si está corriendo
curl http://localhost:8000/health

# Si no responde, iniciar backend correspondiente
```

---

## 🎯 Workflow Recomendado

### Paso 1: Testing (Simulator)
1. Inicia `./start_v2.sh`
2. Añade 5-10 wallets de traders
3. Déjalo correr 24-48 horas
4. Mira estadísticas y elige el mejor

### Paso 2: Producción (Ultra Copy Trading)
1. Inicia `./start_ultra.sh`
2. Usa el mejor trader del testing
3. Empieza con copy_ratio = 0.5
4. Monitorea latencia
5. Ajusta copy_ratio según resultados

---

## 📁 Puertos Usados

| Sistema | Backend | Frontend |
|---------|---------|----------|
| Ambos   | 8000    | 5173     |

**Importante**: Solo puedes correr UN backend a la vez (ultra o v2), no ambos simultáneamente.

---

## ⚙️ Cambiar entre Sistemas

### Para cambiar de Simulator a Ultra Copy Trading:

1. Detén el backend actual (Ctrl+C)
2. Inicia el otro backend:
   ```bash
   ./start_ultra.sh  # Para copy trading real
   ```
3. Recarga el frontend (F5)
4. Navega a la opción correspondiente

### Para cambiar de Ultra Copy Trading a Simulator:

1. Detén el backend actual (Ctrl+C)
2. Inicia el otro backend:
   ```bash
   ./start_v2.sh  # Para simulator
   ```
3. Recarga el frontend (F5)
4. Navega a la opción correspondiente

---

## 📚 Más Información

- **Ultra Copy Trading**: Lee `ULTRA_COPY_TRADING.md`
- **Simulator v2**: Lee `QUICK_START_V2.md`
- **Comparación**: Lee `SYSTEMS_COMPARISON.md`

---

## 🆘 Ayuda Rápida

```bash
# Verificar qué backend está corriendo
ps aux | grep -E "(api_ultra|api_new)" | grep -v grep

# Matar proceso si está bloqueado
pkill -f "api_ultra.py"
# o
pkill -f "api_new.py"

# Reiniciar todo
cd backend
./start_ultra.sh  # o ./start_v2.sh
```

---

**Listo! Elige tu modo y empieza a tradear 🚀**
