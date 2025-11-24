#!/usr/bin/env python
import sqlite3

conn = sqlite3.connect('data/trading.db')
cursor = conn.execute('SELECT ts, symbol, strength, payload FROM signals ORDER BY ts DESC LIMIT 5')
recent = cursor.fetchall()

print("Ultimas señales generadas:")
print("=" * 60)
for row in recent:
    print(f"{row[0]} | {row[1]} | Strength: {row[2]} | {row[3][:100]}...")
    print("-" * 60)

conn.close()