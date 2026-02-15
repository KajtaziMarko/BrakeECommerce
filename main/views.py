from django.db.models import Exists, OuterRef
from django.shortcuts import render

from catalogue.models import Product, Category
from vehicles.choices import VehicleCategory
from vehicles.models import Brands, Models, DisplacementYear, Types
from vehicles.serializers import VehicleBrandSerializer, DisplacementYearSerializer


# Create your views here.
def home(request):
    qs = (
        Brands.objects
        .annotate(has_type=Exists(
            Models.objects.filter(
                brand=OuterRef("pk"),
                vehicle_type=VehicleCategory.CAR,
            )
        ))
        .filter(has_type=True)
    ).order_by('name')

    context = {'brands': VehicleBrandSerializer(qs, many=True).data}

    return render(request, 'index.html', context)

def catalogue(request, vehicle_type, slug, vehicle_id):
    vehicle_type = VehicleCategory.parse(vehicle_type)
    if vehicle_type == VehicleCategory.BIKE:
        vehicle = DisplacementYear.objects.get(pk=vehicle_id, slug=slug)
        products = (
            Product.objects
            .prefetch_related(
                'product_attributes__attribute',
                'product_attributes__attribute_value',
            )
            .filter(vehicle_compatibilities__displacement_year__id=vehicle_id)
        )
    else:
        vehicle = Types.objects.get(pk=vehicle_id, slug=slug)
        products = (
            Product.objects
            .prefetch_related(
                'product_attributes__attribute',
                'product_attributes__attribute_value',
            )
            .filter(vehicle_compatibilities__vehicle_type_id=vehicle_id)
        )

    categories_with_products = []
    for category in Category.objects.all():
        category_products = products.filter(categories=category)
        if category_products.exists():
            categories_with_products.append({
                'category': category,
                'products': category_products
            })

    context = {'vehicle': vehicle, 'vehicle_type': vehicle_type, 'categories_with_products': categories_with_products}

    return render(request, 'catalogue.html', context)