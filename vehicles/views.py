# vehicles/views.py
from urllib.parse import urlparse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .choices import VehicleCategory
from .models import Brand, Model, Car, CommercialVehicle, MotorBike
from .serializers import (
    BrandSerializer, VehicleModelSerializer, CarSerializer, CVSerializer, MotorBikeSerializer
)

def check_access(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return False
    referer = request.META.get('HTTP_REFERER')
    return bool(referer and urlparse(referer).netloc == request.get_host())

@api_view(['GET'])
def get_brands(request):
    # if not check_access(request): return Response({"error":"Access denied."}, status=403)

    raw = request.headers.get('Vehicle-Type')  # accept 'c'/'t'/'b' or labels
    code = VehicleCategory.parse(raw)
    if not code:
        return Response({"error": "Invalid or missing Vehicle-Type."}, status=400)

    brands = Brand.objects.filter(vehicle_type=code).order_by('name')
    return Response(BrandSerializer(brands, many=True).data)

@api_view(['GET'])
def get_models(request):
    # if not check_access(request): return Response({"error":"Access denied."}, status=403)

    brand_id = request.headers.get('Brand-Id')
    raw = request.headers.get('Vehicle-Type')
    code = VehicleCategory.parse(raw)
    if not brand_id or not code:
        return Response({"error": "Invalid or missing Brand-Id or Vehicle-Type."}, status=400)

    qs = Model.objects.filter(brand__vehicle_type=code, brand_id=brand_id).order_by('name')
    return Response(VehicleModelSerializer(qs, many=True).data)

@api_view(['GET'])
def get_types(request):
    brand_id = request.headers.get('Brand-Id')
    model_id = request.headers.get('Model-Id')
    raw = request.headers.get('Vehicle-Type')
    code = VehicleCategory.parse(raw)
    if not (brand_id and model_id and code):
        return Response({"error": "Invalid or missing Brand-Id, Model-Id or Vehicle-Type."}, status=400)

    if code == VehicleCategory.CAR:
        qs = Car.objects.filter(brand__vehicle_type=code, brand_id=brand_id, model_id=model_id).order_by('name')
        return Response(CarSerializer(qs, many=True).data)

    if code == VehicleCategory.CV:
        qs = CommercialVehicle.objects.filter(brand__vehicle_type=code, brand_id=brand_id, model_id=model_id).order_by('name')
        return Response(CVSerializer(qs, many=True).data)

    return Response({"error": "Unsupported Vehicle-Type for this endpoint."}, status=400)

@api_view(['GET'])
def get_motorbikes(request):
    brand_id = request.headers.get('Brand-Id')
    model_id = request.headers.get('Model-Id')
    if not (brand_id and model_id):
        return Response({"error": "Invalid or missing Brand-Id or Model-Id."}, status=400)

    raw = request.headers.get('Vehicle-Type')
    code = VehicleCategory.parse(raw)
    if code != VehicleCategory.BIKE:
        return Response({"error": "Vehicle-Type must be 'b' (Motor Bike)."}, status=400)

    qs = MotorBike.objects.filter(brand_id=brand_id, model_id=model_id).order_by('displacement')
    return Response(MotorBikeSerializer(qs, many=True).data)
