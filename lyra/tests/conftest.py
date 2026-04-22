"""Shared pytest fixtures for Lyra tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src import approval
from src.hillz_inventory import seed_inventory
from src.models import InventoryVehicle


SAMPLE_VEHICLES = [
    InventoryVehicle(
        stock_number="FN-24-0112",
        year=2020,
        make="Honda",
        model="Accord",
        trim="Sport 1.5T",
        vin="1HGCV1F34LA012345",
        mileage_km=54200,
        colour="Sonic Gray Pearl",
        price_cad=26995.0,
    ),
    InventoryVehicle(
        stock_number="FN-24-0155",
        year=2019,
        make="BMW",
        model="330i",
        trim="xDrive",
        vin="WBA8E9G55KNU12345",
        mileage_km=72100,
        colour="Alpine White",
        price_cad=38990.0,
    ),
    InventoryVehicle(
        stock_number="FN-24-0098",
        year=2021,
        make="Toyota",
        model="Tundra",
        trim="SR5 TRD Off-Road",
        vin="5TFDW5F14MX123456",
        mileage_km=41500,
        colour="Midnight Black",
        price_cad=54450.0,
    ),
]

CLEAN_ADF = """<?xml version="1.0" encoding="UTF-8"?>
<adf>
  <prospect>
    <requestdate>2024-04-16T09:42:00-07:00</requestdate>
    <vehicle interest="buy" status="used">
      <year>2020</year>
      <make>Honda</make>
      <model>Accord</model>
      <trim>Sport 1.5T</trim>
      <vin>1HGCV1F34LA012345</vin>
      <stock>FN-24-0112</stock>
      <price type="asking" currency="CAD">26995</price>
    </vehicle>
    <customer>
      <contact primarycontact="1">
        <name part="full">Priya Singh</name>
        <email>priya.singh@example.com</email>
        <phone type="voice">403-555-0199</phone>
      </contact>
      <comments>Hi, is this Accord still available? I'd like to know if there's any wiggle room on price and whether you offer financing. I can come by this Saturday if it works.</comments>
    </customer>
    <vendor><vendorname>AutoTrader</vendorname></vendor>
  </prospect>
</adf>"""

HOSTILE_ADF = """<?xml version="1.0" encoding="UTF-8"?>
<adf>
  <prospect>
    <vehicle interest="buy" status="used">
      <year>2019</year><make>BMW</make><model>330i</model>
      <stock>FN-24-0155</stock>
    </vehicle>
    <customer>
      <contact primarycontact="1">
        <name part="full">Jordan</name>
        <email>jordan@example.com</email>
      </contact>
      <comments>3rd time I've emailed. If I don't hear back in 24h I am reporting you to AMVIC and filing a complaint with the BBB. My lawyer is aware.</comments>
    </customer>
  </prospect>
</adf>"""

VAGUE_PLAIN = "is this still for sale thx buyer99@example.com"


@pytest.fixture(autouse=True)
def seed_and_clear():
    """Seed inventory and clear approval store before each test."""
    seed_inventory(SAMPLE_VEHICLES)
    approval.clear()
    yield
    approval.clear()


@pytest.fixture
def client():
    from src.main import app
    with TestClient(app) as c:
        yield c
