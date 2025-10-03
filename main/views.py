from django.db.models import Exists, OuterRef
from django.shortcuts import render
from vehicles.choices import VehicleCategory
from vehicles.models import Brands, Types, Models
from vehicles.serializers import VehicleBrandSerializer


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

    serializer = VehicleBrandSerializer(qs, many=True)
    context = {'brands': serializer.data}

    return render(request, 'index.html', context)

def catalogue(request):
    return render(request, 'catalogue.html')