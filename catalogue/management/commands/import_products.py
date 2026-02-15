"""
Management command to import products from CSV files.

Usage:
    python manage.py import_products "/path/to/Products/Vehicle"
    python manage.py import_products "/path/to/Products/Vehicle" --dry-run
    python manage.py import_products "/path/to/Products/Vehicle" --clear
"""
import csv
import re
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from catalogue.models import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Product,
    ProductAttribute,
    ProductCategory,
)


# Fields that map directly to Product model (not stored as ProductAttributes)
PRODUCT_FIELDS = {'product_id', 'code', 'ean'}

# Fields stored as ProductAttributes but with special handling
SPECIAL_ATTRIBUTE_FIELDS = {'type_label', 'image_url', 'technical_image_url'}

# Measurement columns that should be stored as DECIMAL
MEASUREMENT_COLUMNS = {
    'diameter_mm', 'height_mm', 'width_mm', 'thickness_mm', 'length_mm',
    'center_bore_mm', 'min_thickness_mm', 'thickness_th_mm',
    'master_cylinder_diameter_mm', 'diameter_mm__dup2',
}

# Columns that should be SELECT type (single value from predefined list)
# AttributeValues will be created automatically on first appearance
SELECT_COLUMNS = {
    'type_label', 'axle', 'braking_system', 'disc_type', 'position',
    'assembly_side', 'wear_indicator', 'accessories', 'accessory_type',
    'has_handbrake_lever', 'is_parking_brake', 'is_pre_assembled',
    'is_manual_proportioning_valve',
}

# Columns that should be INTEGER type
INTEGER_COLUMNS = {
    'num_holes', 'num_pistons', 'units_per_box', 'disc_per_box', 'pad_per_box',
}


def parse_measurement(value: str) -> str | None:
    """
    Parse measurement value like '280 mm' or '9,5 mm' to decimal string.
    Returns None if parsing fails.
    """
    if not value:
        return None

    # Remove unit suffixes (mm, kg, cm, etc.)
    cleaned = re.sub(r'\s*(mm|kg|cm|m)\s*$', '', value.strip(), flags=re.IGNORECASE)

    # Replace European decimal comma with dot
    cleaned = cleaned.replace(',', '.')

    # Remove any remaining whitespace
    cleaned = cleaned.strip()

    # Validate it's a valid number
    try:
        decimal_val = Decimal(cleaned)
        return str(decimal_val)
    except:
        return None


def humanize_column_name(column_name: str) -> str:
    """Convert column names like 'thickness_mm' to 'Thickness (mm)'."""
    # Remove __dup2 suffixes from duplicate column names
    column_name = re.sub(r'__dup\d+$', '', column_name)

    # Handle special cases
    special_cases = {
        'ean': 'EAN',
        'wva_number': 'WVA Number',
        'fmsi': 'FMSI',
        'num_holes': 'Number of Holes',
        'num_pistons': 'Number of Pistons',
        'image_url': 'Image URL',
        'technical_image_url': 'Technical Image URL',
        'type_label': 'Type Label',
        'is_pre_assembled': 'Pre-assembled',
        'is_parking_brake': 'Parking Brake',
        'is_manual_proportioning_valve': 'Manual Proportioning Valve',
        'has_handbrake_lever': 'Has Handbrake Lever',
        'braking_system': 'Braking System',
        'disc_type': 'Disc Type',
        'assembly_side': 'Assembly Side',
        'accessory_type': 'Accessory Type',
        'disc_per_box': 'Discs Per Box',
        'pad_per_box': 'Pads Per Box',
        'units_per_box': 'Units Per Box',
        'wear_indicator': 'Wear Indicator',
        'tightening_torque': 'Tightening Torque',
        'center_bore_mm': 'Center Bore (mm)',
        'min_thickness_mm': 'Min Thickness (mm)',
        'master_cylinder_diameter_mm': 'Master Cylinder Diameter (mm)',
    }

    if column_name in special_cases:
        return special_cases[column_name]

    # Known measurement units
    units = {'mm', 'kg', 'cm', 'm'}

    # Check for _mm, _kg, etc. suffix for units
    unit_match = re.match(r'(.+)_([a-z]+)$', column_name)
    if unit_match:
        name_part, unit = unit_match.groups()
        if unit in units:
            name = name_part.replace('_', ' ').title()
            return f"{name} ({unit})"

    # Default: replace underscores and title case
    return column_name.replace('_', ' ').title()


def category_name_from_filename(filename: str) -> str:
    """Convert filename like 'brake_pads.csv' to 'Brake Pads'."""
    name = filename.replace('.csv', '').replace('_', ' ').title()
    # Fix common abbreviations
    name = name.replace('Lcv', 'LCV')
    name = name.replace('Gt', 'GT')
    return name


class Command(BaseCommand):
    help = 'Import products from CSV files in a directory'

    def add_arguments(self, parser):
        parser.add_argument(
            'directory',
            type=str,
            help='Path to directory containing CSV files'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview import without saving to database'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before import'
        )

    def handle(self, *args, **options):
        directory = Path(options['directory'])
        dry_run = options['dry_run']
        clear = options['clear']

        if not directory.exists():
            raise CommandError(f"Directory does not exist: {directory}")

        csv_files = sorted(directory.glob('*.csv'))
        if not csv_files:
            raise CommandError(f"No CSV files found in: {directory}")

        self.stdout.write(f"Found {len(csv_files)} CSV files")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be saved"))
            self._preview_import(csv_files)
            return

        if clear:
            self.stdout.write(self.style.WARNING("Clearing existing products..."))
            with transaction.atomic():
                ProductAttribute.objects.all().delete()
                ProductCategory.objects.all().delete()
                Product.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared all products"))

        self._run_import(csv_files)

    def _preview_import(self, csv_files):
        """Preview what would be imported without making changes."""
        total_products = 0
        all_columns = set()

        for csv_file in csv_files:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                count = len(rows)
                total_products += count

                if rows:
                    all_columns.update(reader.fieldnames)

                category_name = category_name_from_filename(csv_file.name)
                self.stdout.write(f"  {csv_file.name}: {count} products -> Category '{category_name}'")

        self.stdout.write(f"\nTotal products: {total_products}")
        self.stdout.write(f"Unique columns: {len(all_columns)}")

        # Show attributes that would be created
        attr_columns = all_columns - PRODUCT_FIELDS
        self.stdout.write("\nAttributes to create:")
        for col in sorted(attr_columns):
            # Determine input type for preview
            base_col = re.sub(r'__dup\d+$', '', col)
            if base_col in SELECT_COLUMNS:
                input_type = "SELECT"
            elif base_col in INTEGER_COLUMNS:
                input_type = "INTEGER"
            elif base_col in MEASUREMENT_COLUMNS:
                input_type = "DECIMAL"
            else:
                input_type = "TEXT"
            self.stdout.write(f"  - {col} -> '{humanize_column_name(col)}' [{input_type}]")

    def _run_import(self, csv_files):
        """Run the actual import."""
        # Get or create Brembo brand
        brand, _ = Brand.objects.get_or_create(
            slug='brembo',
            defaults={'name': 'Brembo'}
        )
        self.stdout.write(f"Using brand: {brand.name}")

        # Track statistics
        stats = {
            'products_created': 0,
            'products_updated': 0,
            'categories_created': 0,
            'attributes_created': 0,
            'attribute_values_created': 0,
            'product_attributes_created': 0,
        }

        # Cache for attributes (slug -> Attribute instance)
        attribute_cache = {}

        # Pre-create type_label attribute with select options
        type_label_attr = self._get_or_create_attribute(
            'type_label',
            is_filterable=True,
            input_type=Attribute.InputType.SELECT,
            attribute_cache=attribute_cache,
            stats=stats
        )
        # Create attribute values for Prime and Essential
        for value in ['Prime', 'Essential']:
            AttributeValue.objects.get_or_create(
                attribute=type_label_attr,
                value=value,
                defaults={'slug': slugify(value)}
            )

        # Process each CSV file
        for csv_file in csv_files:
            self._import_csv_file(csv_file, brand, attribute_cache, stats)

        # Print summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("Import completed!"))
        self.stdout.write(f"  Products created: {stats['products_created']}")
        self.stdout.write(f"  Products updated: {stats['products_updated']}")
        self.stdout.write(f"  Categories created: {stats['categories_created']}")
        self.stdout.write(f"  Attributes created: {stats['attributes_created']}")
        self.stdout.write(f"  Attribute values created: {stats['attribute_values_created']}")
        self.stdout.write(f"  Product attributes: {stats['product_attributes_created']}")

    def _import_csv_file(self, csv_file, brand, attribute_cache, stats):
        """Import products from a single CSV file."""
        category_name = category_name_from_filename(csv_file.name)

        # Get or create category
        category, created = Category.objects.get_or_create(
            slug=slugify(category_name),
            defaults={'name': category_name, 'is_active': True}
        )
        if created:
            stats['categories_created'] += 1
            self.stdout.write(f"  Created category: {category_name}")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.stdout.write(f"\nImporting {csv_file.name} ({len(rows)} products)...")

        # Pre-create attributes for this file's columns
        if rows:
            for col in reader.fieldnames:
                if col not in PRODUCT_FIELDS:
                    self._get_or_create_attribute(
                        col,
                        is_filterable=(col in {'axle', 'braking_system', 'disc_type', 'position', 'assembly_side'}),
                        attribute_cache=attribute_cache,
                        stats=stats
                    )

        # Import products in batches within a transaction
        with transaction.atomic():
            for i, row in enumerate(rows, 1):
                self._import_product_row(row, brand, category, attribute_cache, stats)

                if i % 500 == 0:
                    self.stdout.write(f"    Processed {i}/{len(rows)} products...")

        self.stdout.write(self.style.SUCCESS(f"  Completed {csv_file.name}"))

    def _get_or_create_attribute(self, column_name, is_filterable=False, input_type=None, attribute_cache=None, stats=None):
        """Get or create an attribute for a column."""
        # Strip __dup2, __dup3, etc. suffixes so duplicates map to original attribute
        base_column = re.sub(r'__dup\d+$', '', column_name)
        # Use underscores instead of hyphens for attribute slugs
        slug = slugify(base_column).replace('_', '-')

        if attribute_cache and slug in attribute_cache:
            return attribute_cache[slug]

        # Determine input type based on column
        if input_type is None:
            base_col = re.sub(r'__dup\d+$', '', column_name)
            if base_col in SELECT_COLUMNS:
                input_type = Attribute.InputType.SELECT
                is_filterable = True
            elif base_col in INTEGER_COLUMNS:
                input_type = Attribute.InputType.INTEGER
                is_filterable = True
            elif base_col in MEASUREMENT_COLUMNS:
                input_type = Attribute.InputType.DECIMAL
                is_filterable = True
            else:
                input_type = Attribute.InputType.TEXT

        attr, created = Attribute.objects.get_or_create(
            slug=slug,
            defaults={
                'name': humanize_column_name(column_name),
                'input_type': input_type,
                'is_filterable': is_filterable,
            }
        )

        if created and stats:
            stats['attributes_created'] += 1

        if attribute_cache is not None:
            attribute_cache[slug] = attr

        return attr

    def _import_product_row(self, row, brand, category, attribute_cache, stats):
        """Import a single product row."""
        code = row.get('code', '').strip()
        if not code:
            return  # Skip rows without code

        ean = row.get('ean', '').strip()

        # Generate slug from code
        slug = slugify(code)

        # Create product name: "{Category} {Code}"
        name = f"{category.name} {code}"

        # Get or create product
        # code from CSV → mpn, sku uses code as placeholder (required unique field)
        product, created = Product.objects.update_or_create(
            mpn=code,
            defaults={
                'name': name,
                'slug': slug,
                'sku': code,
                'brand': brand,
                'ean': ean,
                'price': Decimal('0.00'),
                'is_active': True,
                'visible': True,
            }
        )

        if created:
            stats['products_created'] += 1
        else:
            stats['products_updated'] += 1

        # Link to category
        ProductCategory.objects.get_or_create(
            product=product,
            category=category,
            defaults={'is_primary': True}
        )

        for col, value in row.items():
            if col in PRODUCT_FIELDS:
                continue

            value = value.strip() if value else ''
            if not value:
                continue

            # Strip __dup suffix and convert to slug for lookup
            base_col = re.sub(r'__dup\d+$', '', col)
            attr = attribute_cache.get(slugify(base_col).replace('_', '-'))
            if not attr:
                continue

            # Handle SELECT/MULTISELECT types - use AttributeValue FK
            if attr.input_type in {Attribute.InputType.SELECT, Attribute.InputType.MULTISELECT}:
                # Get or create AttributeValue on first appearance
                attr_value, av_created = AttributeValue.objects.get_or_create(
                    attribute=attr,
                    value=value,
                    defaults={'slug': slugify(value)}
                )
                if av_created:
                    stats['attribute_values_created'] += 1

                ProductAttribute.objects.update_or_create(
                    product=product,
                    attribute=attr,
                    defaults={'attribute_value': attr_value, 'value_text': ''}
                )
                stats['product_attributes_created'] += 1

            # Handle DECIMAL/measurement columns
            elif attr.input_type == Attribute.InputType.DECIMAL:
                parsed_value = parse_measurement(value)
                if parsed_value is None:
                    continue  # Skip invalid measurements

                ProductAttribute.objects.update_or_create(
                    product=product,
                    attribute=attr,
                    defaults={'value_text': parsed_value}
                )
                stats['product_attributes_created'] += 1

            # Handle INTEGER columns
            elif attr.input_type == Attribute.InputType.INTEGER:
                # Try to parse as integer
                try:
                    int_value = int(value)
                    ProductAttribute.objects.update_or_create(
                        product=product,
                        attribute=attr,
                        defaults={'value_text': str(int_value)}
                    )
                    stats['product_attributes_created'] += 1
                except ValueError:
                    continue  # Skip invalid integers

            # Handle TEXT and other types
            else:
                ProductAttribute.objects.update_or_create(
                    product=product,
                    attribute=attr,
                    defaults={'value_text': value}
                )
                stats['product_attributes_created'] += 1
