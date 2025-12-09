from rest_framework import serializers
from .models import Brands, Models, Types, Years, Displacements, DisplacementYear


class VehicleBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brands
        fields = ['id', 'name']

class VehicleModelSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False)
    date_end   = serializers.DateField(format="%m/%y", required=False)
    class Meta:
        model = Models
        fields = ['id', 'name', 'date_start', 'date_end']

class VehicleTypeSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False)
    date_end   = serializers.DateField(format="%m/%y", required=False)

    class Meta:
        model = Types
        fields = ['id', 'name', 'kw', 'cv', 'date_start', 'date_end', 'slug']

class VehicleDisplacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Displacements
        fields = ['id', 'value']

class VehicleYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Years
        fields = ['id', 'value']

class DisplacementYearSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='year.value', read_only=True)

    class Meta:
        model = DisplacementYear
        fields = ['id', 'value', 'slug']