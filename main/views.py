from datetime import date
from lib2to3.fixes.fix_input import context

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render

from catalogue.admin import DiscAdmin
from catalogue.models import Disc, Drum, Pad, PadAccessory, Hose, WheelCylinder, MasterCylinder, ClutchCylinder, \
    ClutchMasterCylinder, Caliper, ShoeKit, Shoe, ProportioningValve, Kit
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
        start = vehicle.date_start.strftime('%m/%y') if vehicle.date_start else '?'
        end = vehicle.date_end.strftime('%m/%y') if vehicle.date_end else 'Now'
        vehicle_name = f"{vehicle.name} {start} - {end}"
    else:
        vehicle = CommercialVehicle.objects.filter(brand_id=brand_id, model_id=model_id, pk=type_id).first()
        start = vehicle.date_start.strftime('%m/%y') if vehicle.date_start else '?'
        end = vehicle.date_end.strftime('%m/%y') if vehicle.date_end else 'Now'
        vehicle_name = f"{vehicle.name} {start} - {end}"

    brand_name = vehicle.brand.name
    model_name = vehicle.model.name


    vehicle_ct = ContentType.objects.get_for_model(vehicle, for_concrete_model=False)
    discs = Disc.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    drums = Drum.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    pads = Pad.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    pad_accessories = PadAccessory.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    hoses = Hose.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    wheel_cylinders = WheelCylinder.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    master_cylinders = MasterCylinder.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    clutch_cylinders = ClutchCylinder.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    clutch_master_cylinders = ClutchMasterCylinder.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    calipers = Caliper.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    shoe_kits = ShoeKit.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    shoes = Shoe.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    proportioning_valves = ProportioningValve.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()
    kits = Kit.objects.filter(product_links__vehicle_ct=vehicle_ct, product_links__vehicle_id=vehicle.pk, available=True).distinct()

    products = [
        ("Brake Discs", discs),
        ("Brake Drum", drums),
        ("Brake Pad", pads),
        ("Pad Accessory", pad_accessories),
        ("Hose", hoses),
        ("Wheel Cylinder", wheel_cylinders),
        ("Master Cylinder", master_cylinders),
        ("Clutch Cylinder", clutch_cylinders),
        ("Clutch Master Cylinder", clutch_master_cylinders),
        ("Caliper", calipers),
        ("Shoe Kit", shoe_kits),
        ("Shoe", shoes),
        ("Proportioning Valve", proportioning_valves),
        ("Kits", kits),
    ]

    context = {
        'brand': brand_name,
        'model': model_name,
        'vehicle': vehicle_name,
        'products': products,
    }

    return render(request, 'catalogue.html', context=context)
