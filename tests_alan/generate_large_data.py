"""Generate large test data files matching Masterdata.xlsx and Zlecenia.xlsx structure."""

import os
import numpy as np
import pandas as pd

np.random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
N_MASTERDATA = 1_050_000

# ========================
# MASTERDATA
# ========================
print("Generating Masterdata (1 050 000 rows)...")

skus = np.arange(100001, 100001 + N_MASTERDATA)

# 0=SMALL 1=MEDIUM 2=LARGE 3=XL
cats = np.random.choice(4, N_MASTERDATA, p=[0.40, 0.35, 0.20, 0.05])

def gen_range(cats, ranges):
    result = np.zeros(N_MASTERDATA)
    for cat, (lo, hi) in enumerate(ranges):
        m = cats == cat
        result[m] = np.random.uniform(lo, hi, m.sum())
    return result

lengths = np.round(gen_range(cats, [(30,200),(201,600),(601,1200),(1201,2000)]), 1)
widths  = np.round(gen_range(cats, [(20,150),(101,300),(201,600),(401,1200)]), 1)
heights = np.round(gen_range(cats, [(10,100),(51,200),(101,500),(301,1000)]), 1)
weights = np.round(gen_range(cats, [(0.01,2),(0.5,10),(5,50),(30,150)]), 3)

stock = np.random.randint(0, 5001, N_MASTERDATA)
days  = np.random.randint(5, 91, N_MASTERDATA)
min_s = np.maximum(0, stock - np.random.randint(50, 501, N_MASTERDATA))
max_s = stock + np.random.randint(100, 2001, N_MASTERDATA)

pkg_factor = np.random.uniform(1.05, 1.20, N_MASTERDATA)
pkg_qty    = np.random.choice([1,2,5,6,10,12,24,50], N_MASTERDATA,
                               p=[0.30,0.10,0.15,0.10,0.15,0.10,0.07,0.03])
pkg_l = np.round(lengths * pkg_factor, 1)
pkg_w = np.round(widths  * pkg_factor, 1)
pkg_h = np.round(heights * pkg_factor, 1)
pkg_wt = np.round(weights * pkg_qty * np.random.uniform(0.98, 1.02, N_MASTERDATA), 3)

words = ['Element','Produkt','Artykuł','Część','Komponent',
         'Towar','Materiał','Wyrób','Akcesorium','Narzędzie']
desc_type = np.random.choice(words, N_MASTERDATA)
desc_num  = np.random.randint(10000, 99999, N_MASTERDATA)
opisy = [f"{t} {n}" for t, n in zip(desc_type, desc_num)]

df = pd.DataFrame({
    'SKU': skus,
    'Opis': opisy,
    'Ilość na stanie': stock,
    'Liczba dni zapasu': days,
    'Minimalna ilość na stanie': min_s,
    'Maksymalna ilość na stanie': max_s,
    'Jednostka miary': 'szt.',
    'Długość [mm]': lengths,
    'Szerokość [mm]': widths,
    'Wysokość [mm]': heights,
    'Waga [kg]': weights,
    'Ilość w opakowaniu': pkg_qty,
    'Jednostka miary (opakowanie)': 'szt.',
    'Długość opakowania [mm]': pkg_l,
    'Szerokość opakowania [mm]': pkg_w,
    'Wysokość opakowania [mm]': pkg_h,
    'Waga opakowania [kg]': pkg_wt,
})

out_master = os.path.join(OUTPUT_DIR, "Masterdata_large.csv")
df.to_csv(out_master, index=False, encoding='utf-8-sig')
print(f"  Saved {len(df):,} rows -> {out_master}")
del df

# ========================
# ZLECENIA 2025
# ========================
print("Generating Zlecenia 2025 (target 12 M+ rows)...")

dates_2025 = pd.date_range('2025-01-01', '2025-12-31', freq='D')

monthly_w = {1:1.2, 2:0.8, 3:0.9, 4:1.1, 5:1.2, 6:0.7,
             7:0.6, 8:0.7, 9:0.9, 10:1.1, 11:1.5, 12:1.8}

OTYPES = ['250L','500L','PACZKA','PALETA','KURIER','EKSPRES','1000L']
OPROBS = [0.30, 0.20, 0.20, 0.10, 0.10, 0.05, 0.05]
HOUR_P = [0.02,0.05,0.08,0.10,0.10,0.10,0.09,0.09,0.08,0.07,0.06,0.05,0.04,0.03,0.02,0.02]

hot = skus[:210_000]
cold = skus[210_000:]
COLD_POOL = min(50_000, len(cold))

BASE = 38_000
order_ctr = 8_000_000_000
total = 0

out_orders = os.path.join(OUTPUT_DIR, "Zlecenia_2025.csv")
with open(out_orders, 'w', encoding='utf-8-sig') as f:
    f.write('Data,Czas,ID Zlecenia,SKU,Ilość sztuk,Jednostka miary,Rodzaj zlecenia\n')

    for d in dates_2025:
        season  = monthly_w[d.month]
        wfactor = 0.40 if d.dayofweek >= 5 else 1.0
        n = int(BASE * season * wfactor * np.random.uniform(0.88, 1.12))
        if n == 0:
            continue

        # order IDs (each order has multiple lines)
        n_ord = max(200, n // 10)
        base_oid = order_ctr
        order_ctr += n_ord
        reps = np.full(n_ord, n // n_ord, dtype=int)
        reps[:n % n_ord] += 1
        exp_oid = np.repeat(np.arange(base_oid, base_oid + n_ord), reps)[:n]

        # SKUs: 80% hot, 20% cold
        hot_mask = np.random.random(n) < 0.80
        sku_arr = np.where(
            hot_mask,
            hot[np.random.randint(0, len(hot), n)],
            cold[np.random.randint(0, COLD_POOL, n)],
        )

        qtys   = np.random.randint(1, 31, n)
        hours  = np.random.choice(range(6, 22), n, p=HOUR_P)
        mins   = np.random.randint(0, 60, n)
        secs   = np.random.randint(0, 60, n)
        otypes = np.random.choice(OTYPES, n, p=OPROBS)
        ds     = d.strftime('%Y-%m-%d')

        lines = [
            f"{ds},{hours[j]:02d}:{mins[j]:02d}:{secs[j]:02d},"
            f"{exp_oid[j]},{sku_arr[j]},{qtys[j]},szt.,{otypes[j]}\n"
            for j in range(n)
        ]
        f.writelines(lines)
        total += n

    print(f"  Saved {total:,} rows -> {out_orders}")

print("Done.")
