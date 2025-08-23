from lib2to3.fixes.fix_input import context

from django.shortcuts import render

from vehicles.choices import VehicleCategory
from vehicles.serializers import *


# Create your views here.
def home(request):
    vehicle_type = 'c'
    brands = Brand.objects.filter(vehicle_type=vehicle_type).order_by('name')

    serializer = BrandSerializer(brands, many=True)
    context = {'brands': serializer.data}

    return render(request, 'index.html', context)

def catalogue(request):
    vehicle_type = VehicleCategory.parse(request.GET.get('vehicle'))
    brand_id = request.GET.get('brand')
    model_id = request.GET.get('model')
    type_id = request.GET.get('type')
    disp_id = request.GET.get('displacement')
    year = request.GET.get('year')

    if vehicle_type == VehicleCategory.BIKE:
        vehicle = MotorBike.objects.filter(brand_id=brand_id, model_id=model_id, displacement=disp_id).first()
        vehicle_name = f"{vehicle.displacement}cc {year}"
    elif vehicle_type == VehicleCategory.CAR:
        vehicle = Car.objects.filter(brand_id=brand_id, model_id=model_id, pk=type_id).first()
        vehicle_name = f"{vehicle.name} {vehicle.date_start} - {vehicle.date_end}"
    else:
        vehicle = CommercialVehicle.objects.filter(brand_id=brand_id, model_id=model_id, pk=type_id).first()
        vehicle_name = f"{vehicle.name} {vehicle.date_start} - {vehicle.date_end}"

    brand_name = vehicle.brand.name
    model_name = vehicle.model.name
    context = {
        'brand': brand_name,
        'model': model_name,
        'vehicle': vehicle_name,
    }
    return render(request, 'catalogue.html', context)