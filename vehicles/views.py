# vehicles/views.py
from urllib.parse import urlparse
from django.db.models import Exists, OuterRef
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .choices import VehicleCategory
from .models import Brands, Types, Models, Years, DisplacementYear, Displacements
from .serializers import VehicleBrandSerializer, VehicleModelSerializer, VehicleTypeSerializer, VehicleYearSerializer, \
    VehicleDisplacementSerializer


def check_access(request):
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return False
    referer = request.META.get('HTTP_REFERER')
    return bool(referer and urlparse(referer).netloc == request.get_host())


@api_view(['GET'])
def get_brands(request):
    # if not check_access(request): return Response({"error":"Access denied."}, status=403)

    raw = request.headers.get('Vehicle-Type')
    code = VehicleCategory.parse(raw)
    if not code:
        return Response({"error": "Invalid or missing Vehicle-Type."}, status=400)

    qs = (
        Brands.objects
        .annotate(has_type=Exists(
            Models.objects.filter(
                brand=OuterRef("pk"),
                vehicle_type=code,
            )
        ))
        .filter(has_type=True)
    ).order_by('name')

    return Response(VehicleBrandSerializer(qs, many=True).data)


@api_view(['GET'])
def get_models(request):
    # if not check_access(request): return Response({"error":"Access denied."}, status=403)

    brand_id = request.headers.get('Brand-Id')
    raw = request.headers.get('Vehicle-Type')
    code = VehicleCategory.parse(raw)
    if not brand_id or not code:
        return Response({"error": "Invalid or missing Brand-Id or Vehicle-Type."}, status=400)

    qs = Models.objects.filter(brand_id=brand_id, vehicle_type=code).order_by('name')
    return Response(VehicleModelSerializer(qs, many=True).data)


@api_view(['GET'])
def get_types(request):
    brand_id = request.headers.get('Brand-Id')
    model_id = request.headers.get('Model-Id')
    raw = request.headers.get('Vehicle-Type')
    code = VehicleCategory.parse(raw)
    if not (brand_id and model_id and code):
        return Response({"error": "Invalid or missing Brand-Id, Model-Id or Vehicle-Type."}, status=400)

    qs = Types.objects.filter(brand_id=brand_id, model_id=model_id, model__vehicle_type=code).order_by('name')
    return Response(VehicleTypeSerializer(qs, many=True).data)

@api_view(['GET'])
def get_displacements(request):
    brand_id = request.headers.get('Brand-Id')
    model_id = request.headers.get('Model-Id')
    raw = request.headers.get('Vehicle-Type')
    code = VehicleCategory.parse(raw)
    if not (brand_id and model_id and code):
        return Response({"error": "Invalid or missing Brand-Id, Model-Id or Vehicle-Type."}, status=400)

    qs = Displacements.objects.filter(brand_id=brand_id, model_id=model_id, model__vehicle_type=code).order_by('value')
    return Response(VehicleDisplacementSerializer(qs, many=True).data)

@api_view(['GET'])
def get_years(request):
    brand_id = request.headers.get('Brand-Id')
    model_id = request.headers.get('Model-Id')
    displacement_id = request.headers.get('Displacement-Id')
    raw = request.headers.get('Vehicle-Type')
    code = VehicleCategory.parse(raw)

    if not (brand_id and model_id and code and displacement_id):
        return Response({"error": "Invalid or missing Brand-Id or Model-Id or Displacement-Id or Vehicle-Type."}, status=400)

    if code != VehicleCategory.BIKE:
        return Response({"error": "Invalid Vehicle-Type."}, status=400)

    qs = Years.objects.filter(displacementyear__displacement_id=displacement_id).distinct().order_by('value')
    return Response(VehicleYearSerializer(qs, many=True).data)
