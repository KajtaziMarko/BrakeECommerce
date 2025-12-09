from django.db.models import Exists, OuterRef
from django.shortcuts import render
from vehicles.choices import VehicleCategory
from vehicles.models import Brands, Models, DisplacementYear
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
    print(vehicle_type)
    if vehicle_type == VehicleCategory.BIKE:
        pass

    return render(request, 'catalogue.html')