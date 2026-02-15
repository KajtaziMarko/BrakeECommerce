import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from catalogue.models import Product, ProductVehicleCompatibility
from vehicles.models import Types


class Command(BaseCommand):
    help = "Import Product–Vehicle compatibilities from CSV"

    PROGRESS_EVERY = 1000  # rows

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Path to CSV file (type_id, code, title)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run without writing to the database"
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        dry_run = options["dry_run"]

        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"CSV not found: {csv_path}"))
            return

        created = skipped = missing_products = missing_types = 0

        self.stdout.write(f"Importing from {csv_path}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no data will be saved"))

        # Count rows for progress percentage
        with open(csv_path, encoding="utf-8") as f:
            total_rows = sum(1 for _ in f) - 1  # minus header

        processed = 0

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            with transaction.atomic():
                for row in reader:
                    processed += 1

                    type_sync_id = str(row["type_id"]).strip()
                    mpn = row["code"].strip()

                    # Resolve Product
                    try:
                        product = Product.objects.get(mpn=mpn)
                    except Product.DoesNotExist:
                        missing_products += 1
                        skipped += 1
                        continue

                    # Resolve Vehicle Type via sync_id
                    try:
                        vehicle_type = Types.objects.get(sync_id=type_sync_id)
                    except Types.DoesNotExist:
                        missing_types += 1
                        skipped += 1
                        continue

                    _, was_created = ProductVehicleCompatibility.objects.get_or_create(
                        product=product,
                        vehicle_type=vehicle_type,
                        defaults={"notes": ""}
                    )

                    if was_created:
                        created += 1
                    else:
                        skipped += 1

                    # Progress output
                    if processed % self.PROGRESS_EVERY == 0 or processed == total_rows:
                        percent = (processed / total_rows) * 100
                        self.stdout.write(
                            f"[{processed}/{total_rows} | {percent:.1f}%] "
                            f"Created: {created}, Skipped: {skipped}"
                        )

                if dry_run:
                    transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS("Import comapleted"))
        self.stdout.write(f"Total rows: {total_rows}")
        self.stdout.write(f"Created: {created}")
        self.stdout.write(f"Skipped: {skipped}")
        self.stdout.write(f"Missing products: {missing_products}")
        self.stdout.write(f"Missing vehicle types: {missing_types}")
