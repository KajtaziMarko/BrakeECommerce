# CarApp/management/commands/import_brembo.py

import csv
import datetime
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from vehicles.models import (
    Brand,
    Model    as CarModel,
    Car,
    CommercialVehicle,
    MotorBike,
    Year,
)

# map the CSV’s full names to your one‐letter codes
VEHICLE_TYPE_MAP = {
    'Car':   'c',
    'Truck': 't',
    'Bike':  'b',
}

def parse_mmyy(date_str):
    """
    Converts “MM/YY” → date(YYYY,MM,1),
    or returns None if the field is empty or “>”.
    Two‐digit years ≤ current_year%100 → 20YY, else → 19YY.
    """
    if not date_str or date_str.strip() == '>':
        return None
    try:
        month_str, year_str = date_str.split('/')
        month = int(month_str)
        year  = int(year_str)
        cutoff = datetime.date.today().year % 100
        full_year = 2000 + year if year <= cutoff else 1900 + year
        return datetime.date(full_year, month, 1)
    except Exception:
        return None

class Command(BaseCommand):
    help = "Import Brembo brand/model/type data from CSVs"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir', default='.',
            help='Directory where brand.csv, model.csv, type.csv, bikeDisplacement.csv, bikeYear.csv live',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        base = options['dir'].rstrip('/')
        self.stdout.write("➡️  Starting import…")

        self.import_brands(f"{base}/brand.csv")
        self.import_models(f"{base}/model.csv")
        self.import_types(f"{base}/type.csv")
        self.import_bikes(
            disp_path = f"{base}/bikeDisplacement.csv",
            year_path = f"{base}/bikeYear.csv",
        )

        self.stdout.write(self.style.SUCCESS("✅  Done!"))

    def import_brands(self, path):
        self.stdout.write(f" • Importing brands from {path}")
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                bid = int(row['brand_id'])
                b, created = Brand.objects.update_or_create(
                    id=bid,
                    defaults={
                        'name':         row['brand_name'],
                        'vehicle_type': VEHICLE_TYPE_MAP[row['vehicle_type']],
                    }
                )
                verb = "Created" if created else "Updated"
                self.stdout.write(f"   {verb} Brand {b.name!r} (id={bid})")

    def import_models(self, path):
        self.stdout.write(f" • Importing models from {path}")
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                mid     = int(row['model_id'])
                bid_csv = int(row['brand_id'])
                try:
                    brand = Brand.objects.get(id=bid_csv)
                except Brand.DoesNotExist:
                    self.stderr.write(
                        f"⚠️  Skipping model {row['model_name']!r}: unknown brand_id {bid_csv}"
                    )
                    continue

                m, created = CarModel.objects.update_or_create(
                    id=mid,
                    defaults={
                        'brand':      brand,
                        'name':       row['model_name'],
                        'date_start': parse_mmyy(row['date_start']),
                        'date_end':   parse_mmyy(row['date_end']),
                    }
                )
                verb = "Created" if created else "Updated"
                self.stdout.write(
                    f"   {verb} Model {m.name!r} of Brand {brand.name!r} (id={mid})"
                )

    def import_types(self, path):
        self.stdout.write(f" • Importing cars & commercial vehicles from {path}")
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                tid    = int(row['type_id'])
                mid    = int(row['model_id'])
                try:
                    model = CarModel.objects.get(id=mid)
                except CarModel.DoesNotExist:
                    self.stderr.write(f"⚠️  Skipping type {row['type_name']!r}: unknown model_id {mid}")
                    continue

                defaults = {
                    'name':       row['type_name'],
                    'date_start': parse_mmyy(row['date_start']),
                    'date_end':   parse_mmyy(row['date_end']),
                    'kw':         int(row.get('kw') or 0),
                    'cv':         int(row.get('cv') or 0),
                }

                if model.brand.vehicle_type == 'c':
                    cls = Car
                elif model.brand.vehicle_type == 't':
                    cls = CommercialVehicle
                else:
                    # skip anything not Car/CommercialVehicle here
                    continue

                obj, created = cls.objects.update_or_create(
                    id=tid,
                    defaults={**defaults,
                              'brand': model.brand,
                              'model': model,
                    }
                )
                verb = "Created" if created else "Updated"
                self.stdout.write(f"   {verb} {cls.__name__} {obj.name!r} (id={tid})")

    def import_bikes(self, disp_path, year_path):
        # first build a map of disp_id → [year_value, …]
        self.stdout.write(f" • Importing bike years from {year_path}")
        years_map = defaultdict(list)
        with open(year_path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                d_id = int(row['disp_id'])
                years_map[d_id].append(int(row['year_value']))

        self.stdout.write(f" • Importing bike displacements from {disp_path}")
        with open(disp_path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                disp_id = int(row['disp_id'])
                mid     = int(row['model_id'])
                try:
                    model = CarModel.objects.get(id=mid)
                except CarModel.DoesNotExist:
                    self.stderr.write(f"⚠️  Skipping bike disp_id={disp_id}: unknown model_id {mid}")
                    continue

                mb, created = MotorBike.objects.update_or_create(
                    id=disp_id,
                    defaults={
                        'brand':        model.brand,
                        'model':        model,
                        'displacement': int(row['value']),
                    }
                )
                # now handle the ManyToMany to Year
                year_vals = sorted(years_map.get(disp_id, []))
                year_objs = []
                for y in year_vals:
                    year_obj, _ = Year.objects.get_or_create(value=y)
                    year_objs.append(year_obj)
                mb.years.set(year_objs)

                verb = "Created" if created else "Updated"
                self.stdout.write(
                    f"   {verb} MotorBike {mb} (id={disp_id}, years={year_vals})"
                )