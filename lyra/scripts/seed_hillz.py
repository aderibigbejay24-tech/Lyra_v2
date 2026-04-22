"""Seed the HillzDealer inventory cache from a local JSON file.

Usage:
    make seed-inventory
    python scripts/seed_hillz.py [--json path/to/inventory.json]

The JSON file should contain a list of vehicle objects matching the
InventoryVehicle schema. If no file is given, a default set of 4
Fornest vehicles is written to scripts/seed_data.json and loaded.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hillz_inventory import seed_inventory, _set_cache
from src.models import InventoryVehicle

DEFAULT_VEHICLES = [
    {
        "stock_number": "FN-24-0112",
        "year": 2020,
        "make": "Honda",
        "model": "Accord",
        "trim": "Sport 1.5T",
        "vin": "1HGCV1F34LA012345",
        "mileage_km": 54200,
        "colour": "Sonic Gray Pearl",
        "price_cad": 26995.0,
        "url": "https://www.hillzdealer.com/inventory/FN-24-0112",
        "highlights": [
            "1.5L Turbocharged engine",
            "Apple CarPlay / Android Auto",
            "Heated front seats",
            "Honda Sensing suite",
            "One previous owner",
            "Clean CarFax — no accidents",
        ],
    },
    {
        "stock_number": "FN-24-0155",
        "year": 2019,
        "make": "BMW",
        "model": "330i",
        "trim": "xDrive M Sport",
        "vin": "WBA8E9G55KNU12345",
        "mileage_km": 72100,
        "colour": "Alpine White",
        "price_cad": 38990.0,
        "url": "https://www.hillzdealer.com/inventory/FN-24-0155",
        "highlights": [
            "2.0L TwinPower Turbo",
            "M Sport package",
            "Panoramic sunroof",
            "Harman Kardon sound",
            "All-wheel drive",
            "Clean CarFax",
        ],
    },
    {
        "stock_number": "FN-24-0098",
        "year": 2021,
        "make": "Toyota",
        "model": "Tundra",
        "trim": "SR5 TRD Off-Road",
        "vin": "5TFDW5F14MX123456",
        "mileage_km": 41500,
        "colour": "Midnight Black",
        "price_cad": 54450.0,
        "url": "https://www.hillzdealer.com/inventory/FN-24-0098",
        "highlights": [
            "5.7L V8 engine",
            "TRD Off-Road package",
            "Toyota Safety Sense",
            "Tow package — 10,200 lb rating",
            "Heated / ventilated seats",
        ],
    },
    {
        "stock_number": "FN-24-0071",
        "year": 2022,
        "make": "Mazda",
        "model": "CX-5",
        "trim": "GT AWD",
        "vin": None,
        "mileage_km": 28900,
        "colour": "Soul Red Crystal",
        "price_cad": 34200.0,
        "url": "https://www.hillzdealer.com/inventory/FN-24-0071",
        "highlights": [
            "2.5L Skyactiv-G engine",
            "AWD",
            "Bose premium audio",
            "Head-up display",
            "i-Activsense safety suite",
        ],
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json",
        default=None,
        help="Path to inventory JSON file (default: writes and uses scripts/seed_data.json)",
    )
    args = parser.parse_args()

    if args.json:
        data = json.loads(Path(args.json).read_text())
    else:
        seed_path = Path(__file__).parent / "seed_data.json"
        seed_path.write_text(json.dumps(DEFAULT_VEHICLES, indent=2))
        print(f"Wrote default inventory to {seed_path}")
        data = DEFAULT_VEHICLES

    vehicles = [InventoryVehicle.model_validate(v) for v in data]
    seed_inventory(vehicles)
    _set_cache(vehicles)

    print(f"Seeded {len(vehicles)} vehicles into HillzDealer cache:")
    for v in vehicles:
        print(f"  {v.stock_number}  {v.year} {v.make} {v.model}  {v.price_cad:,.0f} CAD")


if __name__ == "__main__":
    main()
