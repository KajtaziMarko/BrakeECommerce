from rest_framework import serializers
from .choices import VehicleCategory
from .models import Brands, Models, Types, Years, Displacements, DisplacementYear


class VehicleBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brands
        fields = ['id', 'name']

class VehicleModelSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False)
    date_end   = serializers.DateField(format="%m/%y", required=False)
    title = serializers.SerializerMethodField()

    class Meta:
        model = Models
        fields = ['id', 'title', 'name', 'date_start', 'date_end']

    def get_title(self, obj):
        if obj.vehicle_type != VehicleCategory.BIKE:
            start = obj.date_start.strftime("%m/%y") if obj.date_start else "?"
            end = obj.date_end.strftime("%m/%y") if obj.date_end else "now"

            return f"{obj.name} {start} - {end}"
        else: return obj.name

class VehicleTypeSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False)
    date_end   = serializers.DateField(format="%m/%y", required=False)
    title = serializers.SerializerMethodField()

    class Meta:
        model = Types
        fields = ['id', 'name', 'title', 'kw', 'cv', 'date_start', 'date_end', 'slug']

    def get_title(self, obj):
        start = obj.date_start.strftime("%m/%y") if obj.date_start else "?"
        end = obj.date_end.strftime("%m/%y") if obj.date_end else "now"
        return f"{obj.name} kw: {obj.kw} cv: {obj.cv} {start} - {end}"

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