"""Generate 6 monthly order files for test client TechMag_SA."""

import os
import random
import numpy as np
import pandas as pd

np.random.seed(2025)
random.seed(2025)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TechMag_SA")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# SKU pool – realistic alphanumeric codes
PREFIXES  = ["ELE","MEC","HYD","OPT","ELC","SEN","MOT","PWR","CTL","FLT"]
MIDDLES   = ["1000","2000","3000","4000","5000","6000","7000","8000"]
SUFFIXES  = ["AA","BB","CC","DD","EE","FF","GG","HH","XA","XB","XC"]

def gen_sku():
    return f"{random.choice(PREFIXES)}{random.choice(MIDDLES)}{random.choice(SUFFIXES)}{random.randint(10000,99999)}"

N_SKUS = 800
SKU_POOL = [gen_sku() for _ in range(N_SKUS)]
# 20% SKUs are "hot" – appear in 70% of orders
HOT_SKUS  = SKU_POOL[:160]
COLD_SKUS = SKU_POOL[160:]

ORDER_TYPES = ["250L","500L","PACZKA","PALETA","KURIER","EKSPRES"]
ORDER_PROBS = [0.30,  0.20,  0.20,   0.12,   0.12,   0.06  ]

# Approximate working days per month and base order volume
MONTHLY_CONFIG = {
    1: {"name": "Styczen", "days": 23, "base": 120, "weight": 0.90},
    2: {"name": "Luty",    "days": 20, "base": 110, "weight": 0.85},
    3: {"name": "Marzec",  "days": 21, "base": 130, "weight": 1.05},
    4: {"name": "Kwiecien","days": 22, "base": 125, "weight": 1.00},
    5: {"name": "Maj",     "days": 20, "base": 140, "weight": 1.10},
    6: {"name": "Czerwiec","days": 22, "base": 115, "weight": 0.95},
}

order_id_counter = 5_000_000_000

for month, cfg in MONTHLY_CONFIG.items():
    print(f"  Generating month {month:02d} ({cfg['name']})...")
    rows = []
    dates = pd.date_range(f"2025-{month:02d}-01", periods=cfg["days"], freq="B")

    for d in dates:
        n_orders = int(cfg["base"] * cfg["weight"] * np.random.uniform(0.85, 1.15))

        for _ in range(n_orders):
            order_id = order_id_counter
            order_id_counter += 1
            n_lines = np.random.randint(1, 8)
            order_type = np.random.choice(ORDER_TYPES, p=ORDER_PROBS)

            for _ in range(n_lines):
                # 70% hot SKUs
                if random.random() < 0.70:
                    sku = random.choice(HOT_SKUS)
                else:
                    sku = random.choice(COLD_SKUS)

                hour = np.random.randint(6, 18)
                minute = np.random.randint(0, 60)
                second = np.random.randint(0, 60)
                qty = np.random.randint(1, 25)

                rows.append({
                    "Data": d.strftime("%Y-%m-%d"),
                    "Czas": f"{hour:02d}:{minute:02d}:{second:02d}",
                    "ID Zlecenia": order_id,
                    "SKU": sku,
                    "Ilość sztuk": qty,
                    "Jednostka miary": "szt.",
                    "Rodzaj zlecenia": order_type,
                })

    df = pd.DataFrame(rows)
    fname = f"Zlecenia_2025_{month:02d}.xlsx"
    fpath = os.path.join(OUTPUT_DIR, fname)
    df.to_excel(fpath, index=False)
    print(f"    Saved {len(df):,} rows -> {fname}")

print(f"\nDone. Files saved in: {OUTPUT_DIR}")
