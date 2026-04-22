"""
Synthetic Data Generator - ADM Project 2025/2026
Generates: Users, Stations, Trips, Events
Schema based on handwritten design + project spec
"""

import random
import string
import json
import csv
from datetime import datetime, timedelta, date

# ─── CONFIG ──────────────────────────────────────────────────────────────────
NUM_USERS    = 50_000   # Change to 1k / 10k / 50k for benchmarks
NUM_STATIONS = 100
NUM_TRIPS    = 100_000  # Change to 10k / 50k / 100k
EVENTS_PER_TRIP = 2     # Change to 0 / 2 / 5 / 10

OUTPUT_FORMAT = "json"  # "json" or "csv"
SEED = 42
random.seed(SEED)

ITALIAN_CITIES = [
    "Milan", "Rome", "Naples", "Turin", "Palermo",
    "Genoa", "Bologna", "Florence", "Bari", "Catania",
    "Venice", "Verona", "Padua", "Trieste", "Brescia",
]

COUNTRIES = [
    "Italy", "Germany", "France", "Spain", "UK",
    "USA", "Brazil", "Argentina", "China", "Japan",
]

FIRST_NAMES = [
    "Luca", "Marco", "Giuseppe", "Antonio", "Francesco",
    "Sofia", "Giulia", "Martina", "Sara", "Laura",
    "Alessandro", "Andrea", "Matteo", "Lorenzo", "Davide",
    "Chiara", "Valentina", "Federica", "Elena", "Alice",
]

LAST_NAMES = [
    "Rossi", "Ferrari", "Esposito", "Bianchi", "Romano",
    "Colombo", "Ricci", "Marino", "Greco", "Bruno",
    "Gallo", "Conti", "De Luca", "Mancini", "Costa",
]

EVENT_TYPES = ["GPS", "ERROR", "BATTERY", "DELAY"]

# ─── ID GENERATORS ───────────────────────────────────────────────────────────

def make_user_id(birthdate: date) -> str:
    """Format: NS + MMDDYYYY + 4 random digits"""
    return f"NS{birthdate.strftime('%m%d%Y')}{random.randint(1000, 9999)}"

def make_station_id() -> str:
    """8 random digits"""
    return f"{random.randint(10_000_000, 99_999_999)}"

def make_trip_id() -> str:
    """8 digits (extended from 6 for 100k trips)"""
    return f"{random.randint(10_000_000, 99_999_999)}"

def make_event_id(index: int) -> str:
    """2 digits (per trip, 01-10)"""
    return f"{index:02d}"

def random_date(start_year=1970, end_year=2003) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def random_datetime(start_year=2024, end_year=2025) -> datetime:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=random.randint(0, int(delta)))

# ─── GENERATORS ──────────────────────────────────────────────────────────────

def generate_users(n: int) -> list[dict]:
    print(f"Generating {n} users...")
    users = []
    for _ in range(n):
        bday = random_date()
        users.append({
            "user_id":   make_user_id(bday),
            "name":      random.choice(FIRST_NAMES),
            "surname":   random.choice(LAST_NAMES),
            "birthdate": bday.strftime("%m/%d/%Y"),   # MDY as in your schema
            "country":   random.choice(COUNTRIES),
        })
    return users

def generate_stations(n: int) -> list[dict]:
    print(f"Generating {n} stations...")
    stations = []
    used_ids = set()
    for i in range(n):
        sid = make_station_id()
        while sid in used_ids:
            sid = make_station_id()
        used_ids.add(sid)
        stations.append({
            "station_id":    sid,
            "name":          f"Station_{i+1:04d}",
            "city":          random.choice(ITALIAN_CITIES),
            "max_capacity":  random.choice([10, 20, 30, 50, 100]),
        })
    return stations

def generate_trips(n: int, users: list, stations: list) -> list[dict]:
    print(f"Generating {n} trips...")
    trips = []
    user_ids    = [u["user_id"]    for u in users]
    station_ids = [s["station_id"] for s in stations]
    used_ids = set()

    for _ in range(n):
        tid = make_trip_id()
        while tid in used_ids:
            tid = make_trip_id()
        used_ids.add(tid)

        start_time = random_datetime()
        duration   = timedelta(minutes=random.randint(5, 180))
        end_time   = start_time + duration

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
            "cost":          round(random.uniform(0.5, 25.0), 2),
        })
    return trips

def generate_events(trips: list, events_per_trip: int) -> list[dict]:
    if events_per_trip == 0:
        print("Skipping events (events_per_trip=0)")
        return []

    print(f"Generating events ({events_per_trip} per trip × {len(trips)} trips)...")
    events = []
    for trip in trips:
        trip_start = datetime.fromisoformat(trip["start_time"])
        trip_end   = datetime.fromisoformat(trip["end_time"])
        duration   = (trip_end - trip_start).total_seconds()

        for i in range(1, events_per_trip + 1):
            offset    = random.uniform(0, duration)
            timestamp = trip_start + timedelta(seconds=offset)
            etype     = random.choice(EVENT_TYPES)

            # Value depends on type
            if etype == "GPS":
                value = f"{random.uniform(40.0, 46.0):.6f},{random.uniform(9.0, 15.0):.6f}"
            elif etype == "ERROR":
                value = random.choice(["E001", "E002", "E003", "E004", "TIMEOUT"])
            elif etype == "BATTERY":
                value = str(random.randint(0, 100))
            else:  # DELAY
                value = str(random.randint(1, 30))  # minutes

            event = {
                "event_id":  make_event_id(i),
                "trip_id":   trip["trip_id"],
                "timestamp": timestamp.isoformat(),
                "type":      etype,
                "value":     value,
            }

            # Schema evolution preview: BATTERY events get battery_level field
            if etype == "BATTERY":
                event["battery_level"] = int(value)

            events.append(event)
    return events

# ─── OUTPUT ──────────────────────────────────────────────────────────────────

def save_json(data: list, filename: str):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved {len(data)} records → {filename}")

def save_csv(data: list, filename: str):
    if not data:
        return
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"  Saved {len(data)} records → {filename}")

def save(data: list, name: str):
    if OUTPUT_FORMAT == "json":
        save_json(data, f"{name}.json")
    else:
        save_csv(data, f"{name}.csv")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f" ADM Data Generator")
    print(f" Users: {NUM_USERS} | Trips: {NUM_TRIPS} | Events/trip: {EVENTS_PER_TRIP}")
    print(f"{'='*50}\n")

    users    = generate_users(NUM_USERS)
    stations = generate_stations(NUM_STATIONS)
    trips    = generate_trips(NUM_TRIPS, users, stations)
    events   = generate_events(trips, EVENTS_PER_TRIP)

    save(users,    "users")
    save(stations, "stations")
    save(trips,    "trips")
    if events:
        save(events, "events")

    print(f"\n✅ Done! Summary:")
    print(f"   Users:    {len(users):>8,}")
    print(f"   Stations: {len(stations):>8,}")
    print(f"   Trips:    {len(trips):>8,}")
    print(f"   Events:   {len(events):>8,}")
    print(f"\nTo change scale, edit the CONFIG block at the top of this file.")
    print(f"Benchmark combinations to run:")
    print(f"  NUM_USERS    = 1_000 / 10_000 / 50_000")
    print(f"  NUM_TRIPS    = 10_000 / 50_000 / 100_000")
    print(f"  EVENTS_PER_TRIP = 0 / 2 / 5 / 10")
