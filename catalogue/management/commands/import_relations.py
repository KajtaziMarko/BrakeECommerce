from __future__ import annotations
import csv
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Model

# FOR RUNNING USE:
# python manage.py import_relations "path to relations csv"


# ---------- User-editable assumptions ----------
# Adjust these dotted paths if your app labels / model names differ.
VEHICLE_MODEL_PATHS: Sequence[str] = (
    "vehicles.Car",
    "vehicles.CommercialVehicle",
    # Add "vehicles.Motorbike" here if needed in the future.
)

# If your product models all subclass a common abstract base (e.g., ProductBase),
# set this to the dotted path of that base class to auto-discover products.
PRODUCT_BASE_PATH: Optional[str] = "catalogue.ProductBase"

# If you do NOT have a common base, set PRODUCT_BASE_PATH = None
# and list concrete product models explicitly here:
EXPLICIT_PRODUCT_MODELS: Sequence[str] = (
    "catalogue.Disc",
    "catalogue.Drum",
    "catalogue.Pad",
    "catalogue.PadAccessory",
    "catalogue.Hose",
    "catalogue.WheelCylinder",
    "catalogue.MasterCylinder",
    "catalogue.ClutchCylinder",
    "catalogue.ClutchMasterCylinder",
    "catalogue.Caliper",
    "catalogue.ShoeKit",
    "catalogue.Shoe",
    "catalogue.ProportioningValve",
    "catalogue.Kit",
)

PRODUCT_BASE_PATH = None
# ----------------------------------------------


@dataclass(frozen=True)
class FoundModel:
    model: type[Model]
    instance: Model


def _load_model(path: str) -> type[Model]:
    try:
        return apps.get_model(path)
    except Exception as e:
        raise CommandError(f"Could not load model '{path}': {e}")


def _iter_concrete_subclasses_of(base_model: type[Model]) -> Iterable[type[Model]]:
    for m in apps.get_models():
        try:
            if issubclass(m, base_model) and not m._meta.abstract:
                yield m
        except Exception:
            # Some models might not be comparable or imported cleanly; ignore
            continue


def _product_models() -> List[type[Model]]:
    models: List[type[Model]] = []
    if PRODUCT_BASE_PATH:
        base = _load_model(PRODUCT_BASE_PATH)
        models.extend(list(_iter_concrete_subclasses_of(base)))
    if EXPLICIT_PRODUCT_MODELS:
        for path in EXPLICIT_PRODUCT_MODELS:
            m = _load_model(path)
            if m not in models:
                models.append(m)
    if not models:
        raise CommandError(
            "No product models resolved. Set PRODUCT_BASE_PATH or EXPLICIT_PRODUCT_MODELS."
        )
    return models


def _vehicle_models() -> List[type[Model]]:
    return [ _load_model(p) for p in VEHICLE_MODEL_PATHS ]


def _find_product_by_code(code: str, product_models: Sequence[type[Model]]) -> Optional[FoundModel]:
    # Try exact match in each model by a 'code' field, then fallback to pk lookup if code==pk.
    for M in product_models:
        # Prefer a 'code' unique field if present
        if "code" in M._meta.fields_map or any(f.name == "code" for f in M._meta.fields):
            try:
                obj = M._default_manager.get(code=code)
                return FoundModel(model=M, instance=obj)
            except M.DoesNotExist:
                pass
        # If primary key is also a string code, this may succeed
        try:
            obj = M._default_manager.get(pk=code)
            return FoundModel(model=M, instance=obj)
        except M.DoesNotExist:
            continue
        except (ValueError, TypeError):
            # pk type mismatch (e.g. int pk but code is non-numeric)
            continue
    return None


def _find_vehicle_by_id(type_id: int, vehicle_models: Sequence[type[Model]], prefer: str) -> List[FoundModel]:
    """
    Returns a list of matches. With prefer='car' we prefer first model that matches;
    with prefer='cv' we prefer later models; with prefer='both' we return all matches.
    """
    matches: List[FoundModel] = []
    for M in vehicle_models:
        try:
            obj = M._default_manager.get(pk=type_id)
            matches.append(FoundModel(model=M, instance=obj))
        except M.DoesNotExist:
            continue
    if not matches:
        return []
    if prefer == "both":
        return matches
    # Prefer first match depending on preference ordering
    if prefer == "cv":
        # reverse preference: last match wins if multiple
        return [matches[-1]]
    # default 'car' (first match)
    return [matches[0]]


class Command(BaseCommand):
    help = "Import ProductVehicle relations from a CSV with columns: code, type_id, title (ignored)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to CSV file containing code,type_id[,title]")
        parser.add_argument("--dry-run", action="store_true", help="Parse and validate only; do not write.")
        parser.add_argument(
            "--prefer",
            choices=["car", "cv", "both"],
            default="car",
            help="If a type_id exists in multiple vehicle models, choose 'car' (first), 'cv' (last), or 'both' (create relations for all).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Write in batches (for bulk_create when --use-bulk).",
        )
        parser.add_argument(
            "--use-bulk",
            action="store_true",
            help="Use bulk_create(ignore_conflicts=True) for faster inserts (no per-row get_or_create).",
        )

    def handle(self, *args, **opts):
        from catalogue.models import ProductVehicle

        csv_path: str = opts["csv_path"]
        dry_run: bool = opts["dry_run"]
        prefer: str = opts["prefer"]
        use_bulk: bool = opts["use_bulk"]
        batch_size: int = opts["batch_size"]

        product_models = _product_models()
        vehicle_models = _vehicle_models()

        # Precompute ContentTypes for speed
        ct_cache = {}
        def ct_for(model: type[Model]) -> ContentType:
            if model not in ct_cache:
                ct_cache[model] = ContentType.objects.get_for_model(model)
            return ct_cache[model]

        # Stats
        total = 0
        created = 0
        skipped_product_missing = 0
        skipped_vehicle_missing = 0
        duplicates = 0
        bulk_bucket: List[ProductVehicle] = []

        def flush_bulk():
            nonlocal created, duplicates, bulk_bucket
            if not bulk_bucket:
                return
            # ignore_conflicts so unique constraint duplicates are skipped
            res = ProductVehicle.objects.bulk_create(bulk_bucket, ignore_conflicts=True)
            # bulk_create returns created objects only (no count on conflicts)
            created += len(res)
            # approximate duplicates as attempted - actually created
            duplicates += (len(bulk_bucket) - len(res))
            bulk_bucket.clear()

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # normalize headers
            headers = {h.strip().lower() for h in reader.fieldnames or []}
            required = {"code", "type_id"}
            missing = required - headers
            if missing:
                raise CommandError(f"CSV missing required columns: {', '.join(sorted(missing))}. Found headers: {sorted(headers)}")

            for row in reader:
                total += 1
                self.stdout.write(f"Processing line {total}...")
                code = (row.get("code") or "").strip()
                type_raw = (row.get("type_id") or "").strip()

                if not code:
                    skipped_product_missing += 1
                    continue
                try:
                    type_id = int(type_raw)
                except ValueError:
                    skipped_vehicle_missing += 1
                    continue

                found_product = _find_product_by_code(code, product_models)
                if not found_product:
                    skipped_product_missing += 1
                    continue

                found_vehicles = _find_vehicle_by_id(type_id, vehicle_models, prefer)
                if not found_vehicles:
                    skipped_vehicle_missing += 1
                    continue

                for fv in found_vehicles:
                    pv_kwargs = dict(
                        product_ct = ct_for(found_product.model),
                        product_id = str(found_product.instance.pk),
                        vehicle_ct = ct_for(fv.model),
                        vehicle_id = fv.instance.pk,
                    )
                    if dry_run:
                        continue
                    if use_bulk:
                        bulk_bucket.append(ProductVehicle(**pv_kwargs))
                        if len(bulk_bucket) >= batch_size:
                            flush_bulk()
                    else:
                        # safe & clear: honor the unique constraint
                        obj, was_created = ProductVehicle.objects.get_or_create(**pv_kwargs)
                        created += int(was_created)
                        duplicates += int(not was_created)

        if use_bulk and not dry_run:
            flush_bulk()

        self.stdout.write("---- Import summary ----")
        self.stdout.write(f"Rows read:               {total}")
        self.stdout.write(f"Created relations:       {created}")
        self.stdout.write(f"Skipped (no product):    {skipped_product_missing}")
        self.stdout.write(f"Skipped (no vehicle):    {skipped_vehicle_missing}")
        if not dry_run:
            self.stdout.write(f"Duplicates (existing):   {duplicates}")
        else:
            self.stdout.write("Dry-run: no changes written.")