import MetaTrader5 as mt5

print("=== ESTADO REAL DE LA CUENTA ===")
mt5.initialize()
account = mt5.account_info()
print(f"Cuenta: {account.login}")
print(f"Balance: ${account.balance:.2f}")
print(f"Servidor: {account.server}")

positions = mt5.positions_get()
if positions:
    print(f"\nPosiciones actuales: {len(positions)}")
    for p in positions:
        side = "BUY" if p.type == 0 else "SELL"
        print(f"  Ticket {p.ticket}: {p.symbol} {side} {p.volume} P&L: ${p.profit:.2f}")
else:
    print("\nNo hay posiciones abiertas")

mt5.shutdown()