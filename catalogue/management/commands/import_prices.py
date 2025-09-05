# catalogue/management/commands/import_prices.py
from __future__ import annotations
import csv
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterable, List, Tuple
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, models
# Adjust this import if ProductBase is defined in a different module
from catalogue.models import ProductBase


# FOR RUNNING USE:
# python manage.py import_prices /path/to/Prices_cleaned.csv
#
# If your file uses "part number" (with a space) and "mpc" for price:
# python manage.py import_prices /path/to/file.csv --code-col "part number" --price-col mpc
#
# Don’t change the 'available' flag:
# python manage.py import_prices /path/to/file.csv --set-available=never
#
# Preview only, printing every 10 rows:
# python manage.py import_prices /path/to/file.csv --dry-run --print-every 10


def norm(name: str | None) -> str:
    return (name or "").strip().lower().replace(" ", "_")


def parse_decimal(val) -> Decimal | None:
    """
    Convert CSV value to Decimal with two decimal places.
    Returns None for blanks/invalid.
    """
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        try:
            # sometimes the CSV parser gives floats; use str(float) as fallback
            d = Decimal(str(float(s)))
        except Exception:
            return None
    return d.quantize(Decimal("0.01"))


def parse_int(val) -> int | None:
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    try:
        return int(float(s))
    except Exception:
        return None


class Command(BaseCommand):
    help = (
        "Import prices & quantities from a CSV and apply them to all models that inherit ProductBase, "
        "matching on the product code (CSV column 'part number' or 'part_number'). "
        "If a code isn’t found in any product model, the row is skipped."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Path to CSV file (e.g., Prices_cleaned.csv)")
        parser.add_argument(
            "--code-col",
            default="part_number",
            help='Column name for product code. Aliases accepted: "part number", "part_number", "code".',
        )
        parser.add_argument(
            "--price-col",
            default="final_price",
            help='Column name for price (default: "final_price"). Fallbacks try "price" then "mpc" if not present.',
        )
        parser.add_argument(
            "--qty-col",
            default="quantity",
            help='Column name for quantity (default: "quantity").',
        )
        parser.add_argument(
            "--set-available",
            choices=["never", "qty", "any"],
            default="qty",
            help=(
                "How to set ProductBase.available: "
                '"qty" -> available=True if quantity>0 (default); '
                '"any" -> available=True if either price or quantity was provided; '
                '"never" -> do not touch available.'
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Do everything except saving changes to the database.",
        )
        parser.add_argument(
            "--print-every",
            type=int,
            default=1,
            help="Print a progress line for every N CSV rows processed (default: 1 = every row).",
        )

    def handle(self, *args, **opts):
        csv_path = Path(opts["csv_path"])
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        # Determine target models = all non-abstract subclasses of ProductBase
        product_models = [
            m
            for m in apps.get_models()
            if isinstance(m, type)
            and issubclass(m, ProductBase)
            and not m._meta.abstract
        ]
        if not product_models:
            raise CommandError("No concrete models found that inherit ProductBase.")

        # Read CSV header & rows
        with csv_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise CommandError("CSV appears to have no header row.")

            header_map = {norm(h): h for h in reader.fieldnames}  # normalized -> original

            # Resolve columns (support multiple common aliases)
            code_candidates = [norm(opts["code_col"]), "part_number", "part_number_", "part_number__", "part_number___", "part_number____", "part_number_____", "part_number______", "part_number_______", "part_number________"]  # safeguard, but norm handles
            code_candidates += ["part_number", "partnumber", "part_no", "part", "code", "part_number_cleaned", "part_number_clean"]
            code_col = self._pick_column(code_candidates, header_map, aliases=("part number",))

            price_candidates = [norm(opts["price_col"]), "final_price", "price", "mpc"]
            price_col = self._pick_column(price_candidates, header_map)

            qty_candidates = [norm(opts["qty_col"]), "quantity", "qty", "stock"]
            qty_col = self._pick_column(qty_candidates, header_map)

            if not code_col:
                raise CommandError(
                    "Could not find a code column. Tried aliases like 'part number', 'part_number', 'code'."
                )
            if not price_col and not qty_col:
                raise CommandError(
                    "Neither price nor quantity column found. Provide at least one."
                )

            rows = list(reader)

        # Collect all codes present in CSV (non-empty)
        codes: List[str] = []
        for row in rows:
            code_val = (row.get(code_col) or "").strip()
            if code_val:
                codes.append(code_val)

        unique_codes = set(codes)
        if not unique_codes:
            self.stdout.write(self.style.WARNING("No non-empty codes found in CSV. Nothing to do."))
            return

        # Build a map code -> list[(model, instance)]
        # (We might update multiple models if the same code exists in multiple product tables.)
        found_map: Dict[str, List[Tuple[models.Model, ProductBase]]] = {c: [] for c in unique_codes}
        for model in product_models:
            qs = model.objects.filter(pk__in=unique_codes).only("pk", "price", "quantity", "available")
            for obj in qs.iterator():
                found_map[str(obj.pk)].append((model, obj))

        total = len(rows)
        updated = 0
        skipped_not_found = 0
        unchanged = 0
        touched_available = 0
        line_no = 0

        # Apply updates row-by-row for clear reporting
        with (transaction.atomic() if not opts["dry_run"] else self._noop_context()):
            for row in rows:
                line_no += 1
                code_raw = row.get(code_col)
                code = (code_raw or "").strip()
                if not code:
                    if opts["print_every"] and line_no % opts["print_every"] == 0:
                        self.stdout.write(f"[line {line_no}] SKIP (empty code)")
                    continue

                price = parse_decimal(row.get(price_col)) if price_col else None
                qty = parse_int(row.get(qty_col)) if qty_col else None

                targets = found_map.get(code) or []
                if not targets:
                    skipped_not_found += 1
                    if opts["print_every"] and line_no % opts["print_every"] == 0:
                        self.stdout.write(f"[line {line_no}] {code}: NOT FOUND → skipped")
                    continue

                any_change_for_row = False
                for model, obj in targets:
                    changed = False

                    if price is not None and obj.price != price:
                        obj.price = price
                        changed = True

                    if qty is not None and obj.quantity != qty:
                        obj.quantity = qty
                        changed = True

                    # available policy
                    if opts["set_available"] != "never":
                        make_available = False
                        if opts["set_available"] == "qty" and qty is not None:
                            make_available = qty > 0
                        elif opts["set_available"] == "any" and (price is not None or qty is not None):
                            make_available = True

                        if make_available and not obj.available:
                            obj.available = True
                            changed = True
                            touched_available += 1

                    if changed and not opts["dry_run"]:
                        obj.save(update_fields=["price", "quantity", "available"])
                    any_change_for_row = any_change_for_row or changed

                if any_change_for_row:
                    updated += 1
                    if opts["print_every"] and line_no % opts["print_every"] == 0:
                        p = f" price={price}" if price is not None else ""
                        q = f" qty={qty}" if qty is not None else ""
                        self.stdout.write(f"[line {line_no}] {code}: UPDATED{p}{q}")
                else:
                    unchanged += 1
                    if opts["print_every"] and line_no % opts["print_every"] == 0:
                        self.stdout.write(f"[line {line_no}] {code}: unchanged")

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write(f"  CSV rows:           {total}")
        self.stdout.write(f"  Updated rows:       {updated}")
        self.stdout.write(f"  Unchanged rows:     {unchanged}")
        self.stdout.write(f"  Not found (skipped):{skipped_not_found}")
        if opts["set_available"] != "never":
            self.stdout.write(f"  Set available=True: {touched_available}")
        if opts["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY RUN: no changes were saved."))

    # --- helpers ---

    def _pick_column(self, candidates: Iterable[str], header_map: Dict[str, str], aliases: Tuple[str, ...] = ()) -> str | None:
        """
        Choose the first column present in the CSV header from a list of normalized candidates.
        """
        normalized_headers = set(header_map.keys())
        for c in candidates:
            c_norm = norm(c)
            if c_norm in normalized_headers:
                return header_map[c_norm]
        for alias in aliases:
            a_norm = norm(alias)
            if a_norm in normalized_headers:
                return header_map[a_norm]
        return None

    from contextlib import contextmanager

    @contextmanager
    def _noop_context(self):
        yield
