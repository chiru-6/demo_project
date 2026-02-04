"""One-off script to generate dataset.csv with varied data for better visualizations."""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

HEADER = [
    "LRU Name", "Project", "Division / Group", "System", "Part Number", "Serial No",
    "Received Data", "Type of Test", "Test Rig", "Date of PI", "Results & Remarks",
    "Date of Clearance"
]

LRU_NAMES = [
    "5RW GEN",
    "5RW GEN, DCMB GPRU",  # comma in name will be quoted by csv.writer
    "DCMB GPRU",
    "Starter Motor Assembly",
    "EPGS Controller",
    "Hydraulic Pump Unit",
]
PROJECTS = ["LCA", "IJT", "AMCA", "TEJAS", "MIG-21 Upgrade", "ALH", "LCH"]
DIVISIONS = [
    "A/C Division",
    "TD/Sagar",
    "Avionics Group",
    "Engine Division",
    "Hydraulics",
    "ELE Group",
    "Quality Assurance",
]
SYSTEMS = ["ELE", "HYD", "PNEU", "GEN", "AVIONICS"]
PART_NUMBER_PREFIXES = ["GCCAIA", "2246", "HDP", "EPGS", "STM", "AVN"]
TYPE_OF_TEST = [
    "PI",
    "PI Starter",
    "Functional Test",
    "Endurance Test",
    "Acceptance Test",
    "Calibration",
]
TEST_RIGS = [
    "LCA EPGS",
    "IJT EPGS",
    "AMCA Rig 1",
    "TEJAS Rig A",
    "Hydraulic Test Bench",
    "Avionics Rig",
    "Engine Test Cell",
]
RESULTS = ["OK", "OK", "OK", "NOT OK", "Pending", "Under Review"]  # weighted
BASE_DATE = datetime(2024, 1, 1)


def random_date(start: datetime, days_span: int) -> str:
    """Return date string DD-MM-YYYY."""
    d = start + timedelta(days=random.randint(0, days_span))
    return d.strftime("%d-%m-%Y")


def serial_no(seq: int) -> str:
    """Generate serial number."""
    return f"{96 + seq} / 1610{seq:06d}412024"


def main() -> None:
    days_span = 800  # ~2+ years of spread
    n_rows = 360
    rows = [HEADER]
    for i in range(1, n_rows + 1):
        result = random.choice(RESULTS)
        date_pi = random_date(BASE_DATE, days_span)
        # Clearance: OK usually has date, NOT OK often empty, Pending/Under Review often empty
        if result == "OK" and random.random() < 0.85:
            d = datetime.strptime(date_pi, "%d-%m-%Y") + timedelta(days=random.randint(1, 14))
            date_clearance = d.strftime("%d-%m-%Y")
        elif result == "NOT OK" and random.random() < 0.3:
            d = datetime.strptime(date_pi, "%d-%m-%Y") + timedelta(days=random.randint(5, 30))
            date_clearance = d.strftime("%d-%m-%Y")
        else:
            date_clearance = ""
        part = random.choice(PART_NUMBER_PREFIXES)
        if part in ("2246", "HDP"):
            part_number = f"{part}{random.randint(1, 99):04d}"
        else:
            part_number = part + str(random.randint(100, 999))
        lru = random.choice(LRU_NAMES)
        project = random.choice(PROJECTS)
        division = random.choice(DIVISIONS)
        system = random.choice(SYSTEMS)
        test_type = random.choice(TYPE_OF_TEST)
        rig = random.choice(TEST_RIGS)
        row = [
            lru,
            project,
            division,
            system,
            part_number,
            serial_no(i),
            "Unit received for inspection",
            test_type,
            rig,
            date_pi,
            result,
            date_clearance,
        ]
        rows.append(row)
    with open("dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Wrote {len(rows)-1} data rows to dataset.csv")


if __name__ == "__main__":
    main()
