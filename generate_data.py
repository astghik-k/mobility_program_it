"""
Synthetic Data Generator - ADM Project 2025/2026
Generates: Users, Stations, Trips, Events

Extended event model with 5 categories:
  - Required:     GPS, ERROR, BATTERY, DELAY
  - Safety:       TILT, BRAKE, ZONE_EXIT
  - Lifecycle:    UNLOCK, LOCK, PAUSE, RESUME
  - Connectivity: SIGNAL_LOST, SIGNAL_RESTORED
  - Telemetry:    SPEED, TEMPERATURE

Dependencies: pip install faker
"""

import random
import json
import csv
from datetime import datetime, timedelta, date
from faker import Faker

# ─── CONFIG ───────────────────────────────────────────────────────────────────
NUM_USERS       = 50_000    # Benchmark: 1_000 / 10_000 / 50_000
NUM_STATIONS    = 100
NUM_TRIPS       = 100_000   # Benchmark: 10_000 / 50_000 / 100_000
EVENTS_PER_TRIP = 2         # Benchmark: 0 / 2 / 5 / 10

OUTPUT_FORMAT   = "json"    # "json" or "csv"
SEED            = 42

random.seed(SEED)
fake = Faker("it_IT")       # Italian locale — realistic names and streets
Faker.seed(SEED)

# ─── STATIC REFERENCE DATA ────────────────────────────────────────────────────

ITALIAN_CITIES = [
    "Milan", "Rome", "Naples", "Turin", "Palermo",
    "Genoa", "Bologna", "Florence", "Bari", "Catania",
    "Venice", "Verona", "Padua", "Trieste", "Brescia",
]

COUNTRIES = [
    "Italy", "Germany", "France", "Spain", "United Kingdom",
    "United States", "Brazil", "Argentina", "China", "Japan",
    "Portugal", "Netherlands", "Poland", "Romania", "Morocco",
]

STATION_SUFFIXES = [
    "Hub", "Stop", "Station", "Depot", "Point",
    "Terminal", "Dock", "Bay", "Zone", "Spot",
]

# ─── EVENT DEFINITIONS ────────────────────────────────────────────────────────
#
# Each event type has:
#   category : grouping for analysis and reporting
#   weight   : relative sampling probability (higher = more frequent)
#   value_fn : lambda returning a realistic value string

EVENT_TYPES = {

    # ── Required (project spec) ───────────────────────────────────────────────
    "GPS": {
        "category": "required",
        "weight": 30,
        "value_fn": lambda: f"{random.uniform(36.0, 47.0):.6f},{random.uniform(7.0, 18.0):.6f}",
    },
    "ERROR": {
        "category": "required",
        "weight": 5,
        "value_fn": lambda: random.choice([
            "E001_SENSOR_FAIL", "E002_COMM_TIMEOUT", "E003_AUTH_FAIL",
            "E004_MOTOR_FAULT", "E005_BRAKE_SYSTEM", "TIMEOUT",
        ]),
    },
    "BATTERY": {
        "category": "required",
        "weight": 15,
        "value_fn": lambda: str(random.randint(0, 100)),
    },
    "DELAY": {
        "category": "required",
        "weight": 8,
        "value_fn": lambda: str(random.randint(1, 45)),
    },

    # ── Safety ────────────────────────────────────────────────────────────────
    "TILT": {
        "category": "safety",
        "weight": 3,
        # 1=slight lean, 2=significant tilt, 3=fallen over
        "value_fn": lambda: str(random.choices([1, 2, 3], weights=[60, 30, 10])[0]),
    },
    "BRAKE": {
        "category": "safety",
        "weight": 8,
        # Deceleration in m/s2 — harsh braking > 4.0
        "value_fn": lambda: f"{random.uniform(0.5, 9.0):.2f}",
    },
    "ZONE_EXIT": {
        "category": "safety",
        "weight": 2,
        # Metres beyond the permitted zone boundary
        "value_fn": lambda: str(random.randint(10, 500)),
    },

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    "UNLOCK": {
        "category": "lifecycle",
        "weight": 10,
        "value_fn": lambda: random.choice(["APP", "NFC", "QR_CODE", "KEYPAD"]),
    },
    "LOCK": {
        "category": "lifecycle",
        "weight": 10,
        "value_fn": lambda: random.choice(["CONFIRMED", "CONFIRMED", "CONFIRMED", "FAILED"]),
    },
    "PAUSE": {
        "category": "lifecycle",
        "weight": 5,
        "value_fn": lambda: random.choice([
            "USER_REQUESTED", "LOW_BATTERY", "GEOFENCE_LIMIT", "TRAFFIC_STOP"
        ]),
    },
    "RESUME": {
        "category": "lifecycle",
        "weight": 5,
        # Seconds the trip was paused before resuming
        "value_fn": lambda: str(random.randint(30, 1800)),
    },

    # ── Connectivity ──────────────────────────────────────────────────────────
    "SIGNAL_LOST": {
        "category": "connectivity",
        "weight": 4,
        # Last known signal strength in dBm before loss
        "value_fn": lambda: str(random.randint(-110, -70)),
    },
    "SIGNAL_RESTORED": {
        "category": "connectivity",
        "weight": 4,
        # Signal strength in dBm after restoration
        "value_fn": lambda: str(random.randint(-90, -40)),
    },

    # ── Telemetry ─────────────────────────────────────────────────────────────
    "SPEED": {
        "category": "telemetry",
        "weight": 20,
        # Speed in km/h — shared e-vehicles typically capped at 25-30 km/h
        "value_fn": lambda: f"{random.uniform(0.0, 30.0):.1f}",
    },
    "TEMPERATURE": {
        "category": "telemetry",
        "weight": 8,
        # Battery/motor temperature in Celsius
        "value_fn": lambda: f"{random.uniform(-5.0, 65.0):.1f}",
    },
}

_EVENT_NAMES   = list(EVENT_TYPES.keys())
_EVENT_WEIGHTS = [EVENT_TYPES[e]["weight"] for e in _EVENT_NAMES]

# ─── ID GENERATORS ────────────────────────────────────────────────────────────

def make_user_id(birthdate: date) -> str:
    return f"NS{birthdate.strftime('%m%d%Y')}{random.randint(1000, 9999)}"

def make_station_id() -> str:
    return f"{random.randint(10_000_000, 99_999_999)}"

def make_trip_id() -> str:
    return f"{random.randint(10_000_000, 99_999_999)}"

def make_event_id(index: int) -> str:
    return f"{index:02d}"

def random_date(start_year=1970, end_year=2003) -> date:
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def random_datetime(start_year=2024, end_year=2025) -> datetime:
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# ─── GENERATORS ───────────────────────────────────────────────────────────────

def generate_users(n: int) -> list:
    print(f"Generating {n:,} users...")
    users = []
    for _ in range(n):
        bday = random_date()
        users.append({
            "user_id":   make_user_id(bday),
            "name":      fake.first_name(),
            "surname":   fake.last_name(),
            "birthdate": bday.strftime("%m/%d/%Y"),
            "country":   random.choice(COUNTRIES),
        })
    return users


def generate_stations(n: int) -> list:
    print(f"Generating {n:,} stations...")
    stations = []
    used_ids = set()
    for _ in range(n):
        sid = make_station_id()
        while sid in used_ids:
            sid = make_station_id()
        used_ids.add(sid)
        city   = random.choice(ITALIAN_CITIES)
        street = fake.street_name()
        suffix = random.choice(STATION_SUFFIXES)
        stations.append({
            "station_id":   sid,
            "name":         f"{street} {suffix}",
            "city":         city,
            "max_capacity": random.choice([10, 20, 30, 50, 100]),
        })
    return stations


def generate_trips(n: int, users: list, stations: list) -> list:
    print(f"Generating {n:,} trips...")
    trips       = []
    user_ids    = [u["user_id"]    for u in users]
    station_ids = [s["station_id"] for s in stations]
    used_ids    = set()

    for _ in range(n):
        tid = make_trip_id()
        while tid in used_ids:
            tid = make_trip_id()
        used_ids.add(tid)

        start_time    = random_datetime()
        end_time      = start_time + timedelta(minutes=random.randint(5, 180))
        start_station = random.choice(station_ids)
        end_station   = random.choice(station_ids)
        while end_station == start_station:
            end_station = random.choice(station_ids)

        trips.append({
            "trip_id":       tid,
            "user_id":       random.choice(user_ids),
            "start_station": start_station,
            "end_station":   end_station,
            "start_time":    start_time.isoformat(),
            "end_time":      end_time.isoformat(),
            "cost":          round(random.uniform(0.50, 25.00), 2),
        })
    return trips


def generate_events(trips: list, events_per_trip: int) -> list:
    if events_per_trip == 0:
        print("Skipping events (events_per_trip=0)")
        return []

    total = events_per_trip * len(trips)
    print(f"Generating {events_per_trip}/trip x {len(trips):,} trips = {total:,} events...")
    events = []

    for trip in trips:
        trip_start = datetime.fromisoformat(trip["start_time"])
        trip_end   = datetime.fromisoformat(trip["end_time"])
        duration_s = (trip_end - trip_start).total_seconds()

        chosen_types = random.choices(_EVENT_NAMES, weights=_EVENT_WEIGHTS, k=events_per_trip)

        for i, etype in enumerate(chosen_types, start=1):
            defn      = EVENT_TYPES[etype]
            timestamp = trip_start + timedelta(seconds=random.uniform(0, duration_s))

            event = {
                "event_id":  make_event_id(i),
                "trip_id":   trip["trip_id"],
                "timestamp": timestamp.isoformat(),
                "category":  defn["category"],
                "type":      etype,
                "value":     defn["value_fn"](),
            }

            # Schema evolution preview (Part 2.1.3)
            if etype == "BATTERY":
                event["battery_level"] = int(event["value"])

            events.append(event)

    return events

# ─── OUTPUT ───────────────────────────────────────────────────────────────────

def save_json(data: list, filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  saved -> {filename}  ({len(data):,} records)")

def save_csv(data: list, filename: str):
    if not data:
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"  saved -> {filename}  ({len(data):,} records)")

def save(data: list, name: str):
    if not data:
        return
    if OUTPUT_FORMAT == "json":
        save_json(data, f"{name}.json")
    else:
        save_csv(data, f"{name}.csv")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"  ADM Synthetic Data Generator")
    print(f"  Users: {NUM_USERS:,}  |  Trips: {NUM_TRIPS:,}  |  Events/trip: {EVENTS_PER_TRIP}")
    print(f"  Event types: {len(EVENT_TYPES)} across 5 categories")
    print(f"{'='*55}\n")

    users    = generate_users(NUM_USERS)
    stations = generate_stations(NUM_STATIONS)
    trips    = generate_trips(NUM_TRIPS, users, stations)
    events   = generate_events(trips, EVENTS_PER_TRIP)

    print()
    save(users,    "users")
    save(stations, "stations")
    save(trips,    "trips")
    save(events,   "events")

    print(f"\n--- Summary ---")
    print(f"  Users:    {len(users):>10,}")
    print(f"  Stations: {len(stations):>10,}")
    print(f"  Trips:    {len(trips):>10,}")
    print(f"  Events:   {len(events):>10,}")

    if events:
        from collections import Counter
        cats = Counter(e["category"] for e in events)
        typs = Counter(e["type"]     for e in events)
        print(f"\n  By category:")
        for cat, cnt in sorted(cats.items()):
            print(f"    {cat:<16} {cnt:>8,}  ({cnt/len(events)*100:.1f}%)")
        print(f"\n  By type:")
        for typ, cnt in sorted(typs.items(), key=lambda x: -x[1]):
            print(f"    {typ:<18} {cnt:>8,}  ({cnt/len(events)*100:.1f}%)")
