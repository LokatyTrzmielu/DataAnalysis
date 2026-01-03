"""Generator syntetycznych danych testowych dla DataAnalysis."""

import random
from datetime import datetime, timedelta
from pathlib import Path

import polars as pl
import yaml


# ============================================================================
# Konfiguracja generatora
# ============================================================================

SEED = 42
random.seed(SEED)

FIXTURES_DIR = Path(__file__).parent

# Zakresy wymiarow (mm)
DIM_RANGES = {
    "small": {"length": (50, 200), "width": (50, 150), "height": (20, 100)},
    "medium": {"length": (150, 400), "width": (100, 300), "height": (50, 200)},
    "large": {"length": (300, 600), "width": (200, 500), "height": (100, 400)},
    "oversize": {"length": (500, 800), "width": (400, 700), "height": (300, 600)},
}

# Zakresy wag (kg)
WEIGHT_RANGES = {
    "light": (0.1, 2.0),
    "medium": (1.5, 10.0),
    "heavy": (8.0, 35.0),
    "very_heavy": (30.0, 80.0),
}

# Proporcje kategorii
SIZE_DISTRIBUTION = {"small": 0.4, "medium": 0.35, "large": 0.2, "oversize": 0.05}
WEIGHT_DISTRIBUTION = {"light": 0.45, "medium": 0.35, "heavy": 0.15, "very_heavy": 0.05}


def weighted_choice(distribution: dict) -> str:
    """Wybor z rozkladu prawdopodobienstwa."""
    items = list(distribution.keys())
    weights = list(distribution.values())
    return random.choices(items, weights=weights, k=1)[0]


# ============================================================================
# Generator Masterdata
# ============================================================================


def generate_masterdata_clean(n_sku: int = 1000) -> pl.DataFrame:
    """Generuj czyste dane Masterdata bez bledow."""
    data = []

    for i in range(n_sku):
        sku = f"SKU-{i+1:06d}"
        size_cat = weighted_choice(SIZE_DISTRIBUTION)
        weight_cat = weighted_choice(WEIGHT_DISTRIBUTION)

        dims = DIM_RANGES[size_cat]
        length = random.uniform(*dims["length"])
        width = random.uniform(*dims["width"])
        height = random.uniform(*dims["height"])

        weight = random.uniform(*WEIGHT_RANGES[weight_cat])

        # Stock - rozklad log-normalny
        stock = max(1, int(random.lognormvariate(4, 1.5)))

        data.append({
            "sku": sku,
            "length_mm": round(length, 1),
            "width_mm": round(width, 1),
            "height_mm": round(height, 1),
            "weight_kg": round(weight, 3),
            "stock_qty": stock,
        })

    return pl.DataFrame(data)


def generate_masterdata_dirty(n_sku: int = 1000) -> pl.DataFrame:
    """Generuj dane Masterdata z typowymi problemami jakosciowymi."""
    clean_df = generate_masterdata_clean(n_sku)
    data = clean_df.to_dicts()

    # 5% - brakujace wymiary (0 lub NULL)
    missing_dims_count = int(n_sku * 0.05)
    for i in random.sample(range(n_sku), missing_dims_count):
        dim = random.choice(["length_mm", "width_mm", "height_mm"])
        data[i][dim] = 0 if random.random() > 0.5 else None

    # 3% - brakujaca waga
    missing_weight_count = int(n_sku * 0.03)
    for i in random.sample(range(n_sku), missing_weight_count):
        data[i]["weight_kg"] = 0 if random.random() > 0.5 else None

    # 2% - ujemne wartosci (bled importu)
    negative_count = int(n_sku * 0.02)
    for i in random.sample(range(n_sku), negative_count):
        field = random.choice(["length_mm", "width_mm", "height_mm", "weight_kg"])
        if data[i][field] is not None:
            data[i][field] = -abs(data[i][field])

    # 1% - outliery (bardzo duze wartosci)
    outlier_count = int(n_sku * 0.01)
    for i in random.sample(range(n_sku), outlier_count):
        field = random.choice(["length_mm", "width_mm", "height_mm"])
        data[i][field] = random.uniform(2000, 5000)  # Bardzo duzy wymiar

    # 2% - duplikaty SKU (rozne wartosci)
    duplicate_count = int(n_sku * 0.02)
    for _ in range(duplicate_count):
        orig_idx = random.randint(0, n_sku - 1)
        duplicate = data[orig_idx].copy()
        # Zmien nieco wartosci
        duplicate["length_mm"] = duplicate["length_mm"] * random.uniform(0.95, 1.05) if duplicate["length_mm"] else None
        duplicate["stock_qty"] = int(duplicate["stock_qty"] * random.uniform(0.8, 1.2))
        data.append(duplicate)

    return pl.DataFrame(data)


# ============================================================================
# Generator Orders
# ============================================================================


def generate_orders_clean(
    n_lines: int = 10000,
    n_sku: int = 1000,
    days: int = 90,
    start_date: datetime | None = None,
) -> pl.DataFrame:
    """Generuj czyste dane zamowien."""
    if start_date is None:
        start_date = datetime(2024, 10, 1, 7, 0, 0)

    data = []
    order_id = 1
    line_id = 1
    current_date = start_date

    # Generuj zamowienia
    lines_remaining = n_lines
    while lines_remaining > 0:
        # Dzien roboczy? (pon-pia)
        if current_date.weekday() < 5:
            # Ile zamowien dzisiaj (normalne: 20-50, peak: 60-100)
            is_peak = random.random() < 0.1  # 10% dni to peak
            if is_peak:
                orders_today = random.randint(60, 100)
            else:
                orders_today = random.randint(20, 50)

            # Generuj zamowienia na dzien
            for _ in range(orders_today):
                if lines_remaining <= 0:
                    break

                # Ile linii w zamowieniu (1-15, rozklad geometryczny)
                n_order_lines = min(lines_remaining, max(1, int(random.expovariate(0.3))))

                # Czas zamowienia (7:00 - 22:00)
                hour = random.randint(7, 21)
                minute = random.randint(0, 59)
                order_time = current_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))

                # Generuj linie zamowienia
                for _ in range(n_order_lines):
                    sku_num = random.randint(1, n_sku)
                    quantity = max(1, int(random.expovariate(0.5)))  # 1-10 sztuk

                    data.append({
                        "order_id": f"ORD-{order_id:08d}",
                        "line_id": f"L-{line_id:010d}",
                        "sku": f"SKU-{sku_num:06d}",
                        "quantity": quantity,
                        "timestamp": order_time.strftime("%Y-%m-%d %H:%M:%S"),
                    })
                    line_id += 1
                    lines_remaining -= 1

                order_id += 1

        current_date += timedelta(days=1)
        if (current_date - start_date).days > days:
            break

    return pl.DataFrame(data)


def generate_orders_dirty(
    n_lines: int = 10000,
    n_sku: int = 1000,
    days: int = 90,
    start_date: datetime | None = None,
) -> pl.DataFrame:
    """Generuj dane zamowien z typowymi problemami jakosciowymi."""
    clean_df = generate_orders_clean(n_lines, n_sku, days, start_date)
    data = clean_df.to_dicts()

    n_rows = len(data)

    # 3% - brakujace SKU (NULL lub pusty string)
    missing_sku_count = int(n_rows * 0.03)
    for i in random.sample(range(n_rows), missing_sku_count):
        data[i]["sku"] = None if random.random() > 0.5 else ""

    # 2% - nieprawidlowe SKU (nieistniejace w masterdata)
    invalid_sku_count = int(n_rows * 0.02)
    for i in random.sample(range(n_rows), invalid_sku_count):
        data[i]["sku"] = f"INVALID-{random.randint(1, 9999):04d}"

    # 2% - ujemna ilosc
    negative_qty_count = int(n_rows * 0.02)
    for i in random.sample(range(n_rows), negative_qty_count):
        data[i]["quantity"] = -abs(data[i]["quantity"])

    # 2% - zerowa ilosc
    zero_qty_count = int(n_rows * 0.02)
    for i in random.sample(range(n_rows), zero_qty_count):
        data[i]["quantity"] = 0

    # 1% - bardzo duze ilosci (outliery)
    outlier_qty_count = int(n_rows * 0.01)
    for i in random.sample(range(n_rows), outlier_qty_count):
        data[i]["quantity"] = random.randint(1000, 10000)

    # 2% - nieprawidlowy format timestamp
    invalid_ts_count = int(n_rows * 0.02)
    invalid_formats = [
        "2024/10/15 12:30:00",  # slash zamiast dash
        "15-10-2024 12:30:00",  # DD-MM-YYYY
        "Oct 15, 2024 12:30 PM",  # text format
        "",  # pusty
        None,  # null
    ]
    for i in random.sample(range(n_rows), invalid_ts_count):
        data[i]["timestamp"] = random.choice(invalid_formats)

    # 1% - duplikaty linii (identyczne line_id)
    duplicate_count = int(n_rows * 0.01)
    for _ in range(duplicate_count):
        orig_idx = random.randint(0, n_rows - 1)
        duplicate = data[orig_idx].copy()
        # Zmien nieco ilosc ale zachowaj line_id
        duplicate["quantity"] = max(1, duplicate["quantity"] + random.randint(-2, 2)) if duplicate["quantity"] else 1
        data.append(duplicate)

    return pl.DataFrame(data)


# ============================================================================
# Generator Konfiguracji
# ============================================================================


def generate_carriers_config() -> dict:
    """Generuj konfiguracje nosnikow Kardex."""
    return {
        "carriers": [
            {
                "carrier_id": "TRAY_S",
                "name": "Tray Small",
                "inner_length_mm": 600,
                "inner_width_mm": 400,
                "inner_height_mm": 100,
                "max_weight_kg": 50,
                "is_active": True,
            },
            {
                "carrier_id": "TRAY_M",
                "name": "Tray Medium",
                "inner_length_mm": 600,
                "inner_width_mm": 400,
                "inner_height_mm": 200,
                "max_weight_kg": 80,
                "is_active": True,
            },
            {
                "carrier_id": "TRAY_L",
                "name": "Tray Large",
                "inner_length_mm": 600,
                "inner_width_mm": 400,
                "inner_height_mm": 350,
                "max_weight_kg": 120,
                "is_active": True,
            },
            {
                "carrier_id": "TRAY_XL",
                "name": "Tray Extra Large",
                "inner_length_mm": 800,
                "inner_width_mm": 600,
                "inner_height_mm": 450,
                "max_weight_kg": 180,
                "is_active": True,
            },
            {
                "carrier_id": "BOX_STD",
                "name": "MiB Standard Box",
                "inner_length_mm": 400,
                "inner_width_mm": 300,
                "inner_height_mm": 200,
                "max_weight_kg": 35,
                "is_active": True,
            },
        ]
    }


def generate_shifts_config() -> dict:
    """Generuj konfiguracje zmian roboczych."""
    return {
        "timezone": "Europe/Warsaw",
        "productive_hours": {
            "default_per_shift": 7.0,
        },
        "weekly_schedule": {
            "Mon": [
                {"name": "S1", "start": "07:00", "end": "15:00", "shift_type": "base"},
                {"name": "S2", "start": "15:00", "end": "23:00", "shift_type": "base"},
            ],
            "Tue": [
                {"name": "S1", "start": "07:00", "end": "15:00", "shift_type": "base"},
                {"name": "S2", "start": "15:00", "end": "23:00", "shift_type": "base"},
            ],
            "Wed": [
                {"name": "S1", "start": "07:00", "end": "15:00", "shift_type": "base"},
                {"name": "S2", "start": "15:00", "end": "23:00", "shift_type": "base"},
            ],
            "Thu": [
                {"name": "S1", "start": "07:00", "end": "15:00", "shift_type": "base"},
                {"name": "S2", "start": "15:00", "end": "23:00", "shift_type": "base"},
            ],
            "Fri": [
                {"name": "S1", "start": "07:00", "end": "15:00", "shift_type": "base"},
            ],
            "Sat": [],
            "Sun": [],
        },
        "exceptions": [
            {
                "id": "peak_2024Q4",
                "type": "range_overlay",
                "from": "2024-11-15",
                "to": "2024-12-20",
                "reason": "Peak season",
                "add_shifts_by_weekday": {
                    "Mon": [{"name": "OT_N", "start": "23:00", "end": "03:00", "shift_type": "overlay"}],
                    "Tue": [{"name": "OT_N", "start": "23:00", "end": "03:00", "shift_type": "overlay"}],
                    "Wed": [{"name": "OT_N", "start": "23:00", "end": "03:00", "shift_type": "overlay"}],
                    "Thu": [{"name": "OT_N", "start": "23:00", "end": "03:00", "shift_type": "overlay"}],
                    "Sat": [{"name": "SAT1", "start": "08:00", "end": "14:00", "shift_type": "overlay"}],
                },
            }
        ],
    }


# ============================================================================
# Main - generuj wszystkie fixtures
# ============================================================================


def main() -> None:
    """Generuj wszystkie pliki testowe."""
    print("Generowanie danych testowych...")
    print(f"Katalog: {FIXTURES_DIR}")

    # Masterdata clean (XLSX via CSV)
    print("\n1. Masterdata Clean (1000 SKU)...")
    md_clean = generate_masterdata_clean(1000)
    md_clean.write_csv(FIXTURES_DIR / "masterdata_clean.csv")
    print(f"   -> {len(md_clean)} wierszy")

    # Masterdata dirty
    print("\n2. Masterdata Dirty (z bledami)...")
    md_dirty = generate_masterdata_dirty(1000)
    md_dirty.write_csv(FIXTURES_DIR / "masterdata_dirty.csv")
    print(f"   -> {len(md_dirty)} wierszy")

    # Orders clean
    print("\n3. Orders Clean (10000 linii)...")
    orders = generate_orders_clean(10000)
    orders.write_csv(FIXTURES_DIR / "orders_clean.csv")
    print(f"   -> {len(orders)} wierszy")

    # Orders dirty
    print("\n4. Orders Dirty (z bledami)...")
    orders_dirty = generate_orders_dirty(10000)
    orders_dirty.write_csv(FIXTURES_DIR / "orders_dirty.csv")
    print(f"   -> {len(orders_dirty)} wierszy")

    # Carriers config
    print("\n5. Carriers config...")
    carriers = generate_carriers_config()
    with open(FIXTURES_DIR / "carriers.yml", "w", encoding="utf-8") as f:
        yaml.dump(carriers, f, default_flow_style=False, allow_unicode=True)
    print(f"   -> {len(carriers['carriers'])} nosnikow")

    # Shifts config
    print("\n6. Shifts config...")
    shifts = generate_shifts_config()
    with open(FIXTURES_DIR / "shifts_base.yml", "w", encoding="utf-8") as f:
        yaml.dump(shifts, f, default_flow_style=False, allow_unicode=True)
    print("   -> done")

    print("\n" + "=" * 50)
    print("Generowanie zakonczone!")


if __name__ == "__main__":
    main()
