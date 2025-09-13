from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, List

from import_export import resources, fields
from import_export.results import RowResult
from import_export.widgets import Widget
from django.db import transaction

from catalogue.models import Disc, Drum, Pad, PadAccessory, Hose, CylinderBase, WheelCylinder, MasterCylinder, \
    ClutchCylinder, ClutchMasterCylinder, Caliper, ShoeKit, ProportioningValve, Shoe, Kit
from catalogue.choices import DiscType, Axle, AssemblySide, WearIndicator, PadAccessoryType, Material, CaliperPosition

# -------------------- Aliases (same idea as your script) --------------------
BAD_NULLS = {"", "-", "—", "–", "nan", "none", "null", "n/a", "na", "0", "N/A", "NaN"}

DISC_ALIASES = {
    "code": ["part_number", "pn", "disc_code"],
    "ean": ["ean code", "ean_code", "ean13", "ean 13"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "diameter_mm": ["diameter Ø", "diameter", "ø", "diameter_mm"],
    "thickness_th_mm": ["thickness (th)", "thickness", "thickness_th_mm", "th"],
    "min_thickness_mm": ["min. thickness", "min_thickness", "min_thickness_mm", "min th"],
    "height_mm": ["height (a)", "height", "height_mm"],
    "num_holes": ["number of holes (c)", "holes", "num_holes"],
    "disc_type": ["brake disc type", "disc_type", "type_code"],
    "center_bore_mm": ["centering (b)", "center_bore", "cb"],
    "tightening_torque": ["tightening torque", "torque"],
    "axle": ["axle"],
    "assembly_side": ["assembly_side", "side"],
    "units_per_box": ["units per box", "box_qty"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
}

DRUM_ALIASES = {
    "code": ["part_number", "pn", "drum_code"],
    "ean": ["ean code", "ean_code", "ean13", "ean 13"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name", "type_label"],
    "diameter_mm": ["diameter Ø", "diameter", "ø", "diameter_mm"],
    "width_mm": ["width", "width_mm"],
    "height_mm": ["height (a)", "height", "height_mm"],
    "num_holes": ["number of holes (c)", "holes", "num_holes"],
    "center_bore_mm": ["centering (b)", "center_bore", "cb", "center_bore_mm"],
    "max_diameter_mm": ["max diameter", "max_diameter", "diameter max", "diameter_mm__dup2"],
    "axle": ["axle", "position"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
}

PAD_ALIASES = {
    "code": ["part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code", "ean13", "ean 13"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],

    "width_mm": ["width", "width_mm", "width (w)"],
    "thickness_mm": ["thickness", "thickness_mm", "thickness (t)"],
    "height_mm": ["height", "height_mm", "height (h)"],

    "braking_system": ["braking system", "brake system", "system"],
    "wva_number": ["wva number", "wva", "wva no.", "wva_no"],
    "wear_indicator": ["wear indicator", "indicator", "wear_ind"],
    "accessories": ["accessories", "accs", "acc"],
    "axle": ["axle", "position"],
    "fmsi": ["fmsi", "fmsi ref", "fmsi number"],

    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
}

PAD_ACCESSORY_ALIASES = {
    "code": ["code", "part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
    "braking_system": ["braking_system", "brake system", "system"],
    "accessory_type": ["accessory_type"],
    "axle": ["axle", "position"],
    "length_mm": ["length", "length_mm"],
    "assembly_side": ["assembly_side", "side"],
}

HOSE_ALIASES = {
    "code": ["code", "part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
    "axle": ["axle", "position"],
    "length_mm": ["length", "length_mm"],
    "threading_1": ["threading_1", "threading 1"],
    "threading_2": ["threading_2", "threading 2"],
}

CYLINDER_ALIASES = {
    "code": ["code", "part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
    "axle": ["axle", "position"],
    "threading": ["threading"],
    "braking_system": ["braking_system", "brake system", "system"],
    "material": ["material"],
}

CALIPER_ALIASES = {
    "code": ["code", "part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
    "axle": ["axle"],
    "position": ["position"],
    "braking_system": ["braking_system", "brake system", "system"],
    "diameter_mm": ["diameter_mm", "diameter", "ø"],
    "num_pistons": ["num_pistons"],
    "assembly_side": ["assembly_side", "side"],
}

SHOE_KIT_ALIASES = {
    "code": ["code", "part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
    "diameter_mm": ["diameter_mm", "diameter", "ø"],
    "width_mm": ["width_mm", "width", "mm"],
    "master_cylinder_diameter_mm": ["master_cylinder_diameter_mm"],
    "is_pre_assembled": ["is_pre_assembled"],
    "braking_system": ["braking_system", "brake system", "system"],
    "axle": ["axle"],
    "is_manual_proportioning_valve": ["is_manual_proportioning_valve"],
}

SHOE_ALIASES = {
    "code": ["code", "part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
    "diameter_mm": ["diameter_mm", "diameter", "mm"],
    "width_mm": ["width_mm", "width", "mm"],
    "is_parking_brake": ["is_parking_brake"],
    "has_handbrake_lever": ["has_handbrake_lever"],
    "has_accessories": ["has_accessories"],
    "axle": ["axle"],
    "braking_system": ["braking_system", "brake system", "system"],
}

VALVE_ALIASES = {
    "code": ["code", "part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
    "threading": ["threading"],
    "material": ["material"],
    "braking_system": ["braking_system", "brake system", "system"],
}

KIT_ALIASES = {
    "code": ["code", "part_number", "pn", "pad_code"],
    "ean": ["ean code", "ean_code"],
    "price": ["mpc", "final price", "unit_price", "price_eur"],
    "quantity": ["qty", "stock"],
    "type_label": ["type", "title", "name"],
    "image_url": ["image_url", "image"],
    "technical_image_url": ["technical_image_url", "technical image", "tech_image", "technical_image"],
    "disc_per_box": ["disc_per_box"],
    "pad_per_box": ["pad_per_box"],
    "axle": ["axle"],
}


# -------------------- Helpers & Widgets --------------------
EAN_RE = re.compile(r"^\d{8,14}$")

def is_bad(val) -> bool:
    return val is None or str(val).strip().lower() in BAD_NULLS

class MaxLenCharWidget(Widget):
    def __init__(self, max_len: int):
        self.max_len = max_len
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value):
            return None
        s = " ".join(str(value).strip().split())
        return s[: self.max_len]

class FMSIWidget(Widget):
    """
    Extract plausible FMSI-like tokens, join with comma, and clamp to max_len.
    Example inputs:
      "D1234, D5678; D9012" -> "D1234, D5678, D9012"
      "D1234(Dodge) / D5678" -> "D1234, D5678"
    """
    TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?")
    def __init__(self, max_len: int = 70):
        self.max_len = max_len
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value):
            return None
        raw = " ".join(str(value).upper().split())
        tokens = self.TOKEN_RE.findall(raw)
        if not tokens:
            return None
        out = ", ".join(tokens)
        return out[: self.max_len]

def parse_ean(val) -> Optional[str]:
    if is_bad(val):
        return None
    s = str(val).strip()
    digits = re.sub(r"\D", "", s)
    if not digits or not EAN_RE.match(digits):
        return None
    return digits

def normalize_header(h: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (h or "").strip().lower()).strip()

def build_header_map(headers: List[str], aliases: Dict[str, List[str]]) -> Dict[str, str]:
    norm_headers = {normalize_header(h): h for h in headers}
    out = {}
    for field, alist in aliases.items():
        for candidate in [field] + alist:
            key = normalize_header(candidate)
            if key in norm_headers:
                out[field] = norm_headers[key]
                break
    return out

class DecimalFlexibleWidget(Widget):
    NUM_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")

    def clean(self, value, row=None, *args, **kwargs):
        if value is None:
            return None
        s = str(value).strip()
        if s.lower() in BAD_NULLS:
            return None
        m = self.NUM_RE.search(s)
        if not m:
            return None
        num = m.group(0).replace(",", ".")
        try:
            return Decimal(num)
        except (InvalidOperation, ValueError):
            return None

class IntFlexibleWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value):
            return None
        s = re.sub(r"[^0-9-]", "", str(value))
        try:
            return int(s)
        except ValueError:
            return None

class DiscTypeWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value):
            return None
        s = str(value).strip().lower()
        if s.startswith("v"): return DiscType.VENTILATED
        if s.startswith("s"): return DiscType.SOLID
        su = s.upper()
        return su if su in {"S", "V"} else None

class AxleWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value):
            return None
        s = str(value).strip().lower()
        if ("front" in s and "rear" in s) or s.startswith("b"): return Axle.BOTH
        if s.startswith("f") or "front" in s: return Axle.FRONT
        if s.startswith("r") or "rear" in s: return Axle.REAR
        su = s.upper()
        return su if su in {"F","R","B"} else None

class SideWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value): return None
        s = str(value).strip().lower()
        if ("left" in s and "right" in s) or s.startswith("b"): return AssemblySide.BOTH
        if "left" in s: return AssemblySide.LEFT
        if "right" in s: return AssemblySide.RIGHT
        su = s.upper()
        return su if su in {"L","R","B","N"} else None

class WearIndicatorWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value): return None
        s = str(value).strip().lower()
        if "acoustic" in s: return WearIndicator.ACOUSTIC
        if "without" in s: return WearIndicator.WITHOUT
        if "prepared" in s: return WearIndicator.PREPARED
        su = s.upper()
        return su if su in {"W","A"} else None

class EANWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        return parse_ean(value)

class PadAccessoryTypeWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value): return None
        s = str(value).strip().lower()
        if "assembly kit" in s: return PadAccessoryType.ASSEMBLY_KIT
        if "wear indicator" in s: return PadAccessoryType.WEAR_INDICATOR
        return None

class MaterialWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value): return None
        s = str(value).strip().lower()
        if "aluminium" in s: return Material.ALUMINIUM
        if "cast iron" in s: return Material.CAST_IRON
        if "plastic" in s: return Material.PLASTIC
        if "steel" in s: return Material.STEEL
        return None

class PositionWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value): return None
        s = str(value).strip().lower()
        if ("left" in s and "right" in s) or s.startswith("b"): return CaliperPosition.BOTH
        if "left" in s: return CaliperPosition.LEFT
        if "right" in s: return CaliperPosition.RIGHT
        return None

class IsPreAssembledWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value): return None
        s = str(value).strip().lower()
        if "not" in s: return False
        return True

class ProportioningValveWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if is_bad(value): return None
        s = str(value).strip().lower()
        if "manual" in s: return True
        return False

# -------------------- Base Resource --------------------
class BaseProductResource(resources.ModelResource):
    """
    Common behaviors:
    - Upsert by 'code'
    - Alias remapping in before_import_row
    - Compute 'available' from quantity / price
    """
    code = fields.Field(attribute="code", column_name="code")
    ean = fields.Field(attribute="ean", widget=EANWidget(), column_name="ean")
    price = fields.Field(attribute="price", widget=DecimalFlexibleWidget(), column_name="price")
    quantity = fields.Field(attribute="quantity", widget=IntFlexibleWidget(), column_name="quantity")
    type_label = fields.Field(attribute="type_label", column_name="type_label")
    image_url = fields.Field(attribute="image_url", column_name="image_url")
    technical_image_url = fields.Field(attribute="technical_image_url", column_name="technical_image_url")

    # To be provided by subclass
    ALIASES: Dict[str, List[str]] = {}

    def get_instance(self, instance_loader, row):
        code = (row.get("code") or "").strip()
        if not code:
            return None
        return self._meta.model.objects.filter(code=code).first()

    def get_or_init_instance(self, instance_loader, row):
        instance = self.get_instance(instance_loader, row)
        if instance is not None:
            return instance, False
        # create a fresh instance (let import-export populate fields later)
        instance = self.init_instance(row)
        code = (row.get("code") or "").strip()
        if code:
            setattr(instance, "code", code)
        return instance, True

    def before_import_row(self, row, **kwargs):
        """
        - Remap alias headers onto canonical field names (in-place)
        - Compute 'available'
        """
        # 1) alias remap: if canonical field is missing but an alias exists, copy value
        # (row behaves like a dict of column_name -> value)
        headers = list(row.keys())
        header_map = build_header_map(headers, self.ALIASES)

        def val(field, default=None):
            hdr = header_map.get(field)
            return row.get(hdr) if hdr else default

        # Make sure canonical keys exist
        for field in self.ALIASES.keys():
            if field not in row or row.get(field) in (None, ""):
                v = val(field, row.get(field))
                if v is not None:
                    row[field] = v

        # 2) availability flag (computed later in import_obj)
        # just ensure price/quantity are in canonical keys
        if "price" not in row and val("price") is not None:
            row["price"] = val("price")
        if "quantity" not in row and val("quantity") is not None:
            row["quantity"] = val("quantity")

        # Strip basics
        for k in ("code", "type_label", "image_url", "technical_image_url"):
            if k in row and isinstance(row[k], str):
                row[k] = row[k].strip()

        # Quick progress print (import-export shows row numbers already, but keeping as requested)
        code = (row.get("code") or "").strip() or "(missing)"
        print(f"[{self._meta.model.__name__.upper()}] Processing: code={code}")

    def import_obj(self, obj, data, dry_run, **kwargs):
        """
        After widgets parsed fields into obj, compute 'available'.
        """
        super().import_obj(obj, data, dry_run, **kwargs)
        qty = getattr(obj, "quantity", 0) or 0
        price = getattr(obj, "price", None)
        obj.available = bool(qty and qty > 0) or (price is not None)

    @transaction.atomic
    def import_data(self, dataset, dry_run=False, raise_errors=False,
                    use_transactions=None, collect_failed_rows=False, **kwargs):
        """
        Wrap whole import in a single transaction (unless dry-run).
        """
        return super().import_data(
            dataset, dry_run=dry_run, raise_errors=raise_errors,
            use_transactions=True, collect_failed_rows=collect_failed_rows, **kwargs
        )

# -------------------- Disc Resource --------------------
class DiscResource(BaseProductResource):
    ALIASES = DISC_ALIASES

    diameter_mm = fields.Field(attribute="diameter_mm", widget=DecimalFlexibleWidget(), column_name="diameter_mm")
    thickness_th_mm = fields.Field(attribute="thickness_th_mm", widget=DecimalFlexibleWidget(), column_name="thickness_th_mm")
    min_thickness_mm = fields.Field(attribute="min_thickness_mm", widget=DecimalFlexibleWidget(), column_name="min_thickness_mm")
    height_mm = fields.Field(attribute="height_mm", widget=DecimalFlexibleWidget(), column_name="height_mm")
    num_holes = fields.Field(attribute="num_holes", widget=IntFlexibleWidget(), column_name="num_holes")
    disc_type = fields.Field(attribute="disc_type", widget=DiscTypeWidget(), column_name="disc_type")
    center_bore_mm = fields.Field(attribute="center_bore_mm", widget=DecimalFlexibleWidget(), column_name="center_bore_mm")
    tightening_torque = fields.Field(attribute="tightening_torque", widget=IntFlexibleWidget(), column_name="tightening_torque")
    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")
    assembly_side = fields.Field(attribute="assembly_side", widget=SideWidget(), column_name="assembly_side")
    units_per_box = fields.Field(attribute="units_per_box", widget=IntFlexibleWidget(), column_name="units_per_box")

    class Meta:
        model = Disc
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        if not row.get("assembly_side") and row.get("axle"):
            row["assembly_side"] = row["axle"]

# -------------------- Drum Resource --------------------
class DrumResource(BaseProductResource):
    ALIASES = DRUM_ALIASES

    diameter_mm = fields.Field(attribute="diameter_mm", widget=DecimalFlexibleWidget(), column_name="diameter_mm")
    width_mm = fields.Field(attribute="width_mm", widget=DecimalFlexibleWidget(), column_name="width_mm")
    height_mm = fields.Field(attribute="height_mm", widget=DecimalFlexibleWidget(), column_name="height_mm")
    num_holes = fields.Field(attribute="num_holes", widget=IntFlexibleWidget(), column_name="num_holes")
    center_bore_mm = fields.Field(attribute="center_bore_mm", widget=DecimalFlexibleWidget(), column_name="center_bore_mm")
    max_diameter_mm = fields.Field(attribute="max_diameter_mm", widget=DecimalFlexibleWidget(), column_name="max_diameter_mm")
    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")

    class Meta:
        model = Drum
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

# -------------------- Pad Resource --------------------
class PadResource(BaseProductResource):
    ALIASES = PAD_ALIASES

    width_mm = fields.Field(attribute="width_mm", widget=DecimalFlexibleWidget(), column_name="width_mm")
    thickness_mm = fields.Field(attribute="thickness_mm", widget=DecimalFlexibleWidget(), column_name="thickness_mm")
    height_mm = fields.Field(attribute="height_mm", widget=DecimalFlexibleWidget(), column_name="height_mm")

    braking_system = fields.Field(attribute="braking_system", column_name="braking_system")
    wva_number = fields.Field(attribute="wva_number", column_name="wva_number")
    wear_indicator = fields.Field(attribute="wear_indicator", widget=WearIndicatorWidget(), column_name="wear_indicator")
    accessories = fields.Field(attribute="accessories", column_name="accessories")
    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")
    fmsi = fields.Field(
        attribute="fmsi", column_name="fmsi",
        widget=FMSIWidget(max_len=70)
    )

    class Meta:
        model = Pad
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

# -------------------- Pad Accessory Resource --------------------
class PadAccessoryResource(BaseProductResource):
    ALIASES = PAD_ACCESSORY_ALIASES

    braking_system = fields.Field(attribute="braking_system", column_name="braking_system")
    accessory_type = fields.Field(attribute="accessory_type", widget=PadAccessoryTypeWidget(), column_name="accessory_type")
    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")
    assembly_side = fields.Field(attribute="assembly_side", widget=SideWidget(), column_name="assembly_side")
    length_mm = fields.Field(attribute="length_mm", widget=DecimalFlexibleWidget(), column_name="length_mm")

    class Meta:
        model = PadAccessory
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        if not row.get("assembly_side") and row.get("axle"):
            row["assembly_side"] = row["axle"]

# -------------------- Hose Resource --------------------
class HoseResource(BaseProductResource):
    ALIASES = HOSE_ALIASES

    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")
    length_mm = fields.Field(attribute="length_mm", widget=DecimalFlexibleWidget(), column_name="length_mm")
    threading_1 = fields.Field(attribute="threading_1", column_name="threading_1")
    threading_2 = fields.Field(attribute="threading_2", column_name="threading_2")

    class Meta:
        model = Hose
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

class CylinderBaseResource(BaseProductResource):
    ALIASES = CYLINDER_ALIASES

    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")
    braking_system = fields.Field(attribute="braking_system", column_name="braking_system")
    diameter_mm = fields.Field(attribute="diameter_mm", widget=DecimalFlexibleWidget(), column_name="diameter_mm")
    material = fields.Field(attribute="material", widget=MaterialWidget(), column_name="material")

    class Meta:
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

# One resource per concrete model
class WheelCylinderResource(CylinderBaseResource):
    class Meta(CylinderBaseResource.Meta):
        model = WheelCylinder

class MasterCylinderResource(CylinderBaseResource):
    class Meta(CylinderBaseResource.Meta):
        model = MasterCylinder

class ClutchCylinderResource(CylinderBaseResource):
    class Meta(CylinderBaseResource.Meta):
        model = ClutchCylinder

class ClutchMasterCylinderResource(CylinderBaseResource):
    class Meta(CylinderBaseResource.Meta):
        model = ClutchMasterCylinder

# -------------------- Caliper Resource --------------------
class CaliperResource(BaseProductResource):
    ALIASES = CALIPER_ALIASES

    diameter_mm = fields.Field(attribute="diameter_mm", widget=DecimalFlexibleWidget(), column_name="diameter_mm")
    braking_system = fields.Field(attribute="braking_system", column_name="braking_system")
    num_pistons = fields.Field(attribute="num_pistons", widget=IntFlexibleWidget(), column_name="num_pistons")
    position = fields.Field(attribute="position", widget=PositionWidget(), column_name="position")
    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")
    assembly_side = fields.Field(attribute="assembly_side", widget=SideWidget(), column_name="assembly_side")

    class Meta:
        model = Caliper
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        if not row.get("assembly_side") and row.get("axle"):
            row["assembly_side"] = row["axle"]

# -------------------- Shoe Kit Resource --------------------
class ShoeKitResource(BaseProductResource):
    ALIASES = SHOE_KIT_ALIASES

    diameter_mm = fields.Field(attribute="diameter_mm", widget=DecimalFlexibleWidget(), column_name="diameter_mm")
    width_mm = fields.Field(attribute="width_mm", widget=DecimalFlexibleWidget(), column_name="width_mm")
    master_cylinder_diameter_mm = fields.Field(attribute="master_cylinder_diameter_mm", widget=DecimalFlexibleWidget(), column_name="master_cylinder_diameter_mm")
    braking_system = fields.Field(attribute="braking_system", column_name="braking_system")
    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")
    is_pre_assembled = fields.Field(attribute="is_pre_assembled", widget=IsPreAssembledWidget(), column_name="is_pre_assembled")
    is_manual_proportioning_valve = fields.Field(attribute="is_manual_proportioning_valve", widget=ProportioningValveWidget(), column_name="is_manual_proportioning_valve")

    class Meta:
        model = ShoeKit
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        super().before_import_row(row, **kwargs)
        if not row.get("is_manual_proportioning_valve"):
            row["is_manual_proportioning_valve"] = False


# -------------------- Shoe Resource --------------------
class IsParkingBrakeWidget(Widget):
    def clean(self, value, row=None, **kwargs):
        if is_bad(value): return False
        s = str(value).strip().lower()
        if "parking brake" in s: return True
        return False

class HasHandbrakeLeverWidget(Widget):
    def clean(self, value, row=None, **kwargs):
        if is_bad(value): return False
        s = str(value).strip().lower()
        if "with" in s: return True
        return False

class HasAccessoriesWidget(Widget):
    def clean(self, value, row=None, **kwargs):
        if is_bad(value): return False
        s = str(value).strip().lower()
        if "with" in s: return True
        return False

class ShoeResource(BaseProductResource):
    ALIASES = SHOE_ALIASES

    diameter_mm = fields.Field(attribute="diameter_mm", widget=DecimalFlexibleWidget(), column_name="diameter_mm")
    width_mm = fields.Field(attribute="width_mm", widget=DecimalFlexibleWidget(), column_name="width_mm")
    braking_system = fields.Field(attribute="braking_system", column_name="braking_system")
    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")
    is_parking_brake = fields.Field(attribute="is_parking_brake", widget=IsParkingBrakeWidget(), column_name="is_parking_brake")
    has_handbrake_lever = fields.Field(attribute="has_handbrake_lever", widget=HasHandbrakeLeverWidget(), column_name="has_handbrake_lever")
    has_accessories = fields.Field(attribute="has_accessories", widget=HasAccessoriesWidget(), column_name="has_accessories")

    class Meta:
        model = Shoe
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True


class ProportioningValveResource(BaseProductResource):
    ALIASES = VALVE_ALIASES

    braking_system = fields.Field(attribute="braking_system", column_name="braking_system")
    material = fields.Field(attribute="material", widget=MaterialWidget(), column_name="material")
    threading = fields.Field(attribute="threading", column_name="threading")

    class Meta:
        model = ProportioningValve
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True

class KitResource(BaseProductResource):
    ALIASES = KIT_ALIASES

    disc_per_box = fields.Field(attribute="disc_per_box", widget=IntFlexibleWidget(), column_name="disc_per_box")
    pad_per_box = fields.Field(attribute="pad_per_box", widget=IntFlexibleWidget(), column_name="pad_per_box")
    axle = fields.Field(attribute="axle", widget=AxleWidget(), column_name="axle")

    class Meta:
        model = Kit
        import_id_fields = ("code",)
        skip_unchanged = True
        report_skipped = True