from rest_framework import serializers
from .models import Brand, Model, Car, CommercialVehicle, MotorBike

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']

class VehicleModelSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False)
    date_end   = serializers.DateField(format="%m/%y", required=False)
    class Meta:
        model = Model
        fields = ['id', 'name', 'date_start', 'date_end']

class CarSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False)
    date_end   = serializers.DateField(format="%m/%y", required=False)
    class Meta:
        model = Car
        fields = ['id', 'name', 'kw', 'cv', 'date_start', 'date_end']

class CVSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False)
    date_end   = serializers.DateField(format="%m/%y", required=False)
    class Meta:
        model = CommercialVehicle
        fields = ['id', 'name', 'kw', 'cv', 'date_start', 'date_end']

class MotorBikeSerializer(serializers.ModelSerializer):
    years = serializers.SlugRelatedField(many=True, read_only=True, slug_field='value')
    class Meta:
        model = MotorBike
        fields = ['id', 'brand', 'model', 'displacement', 'years']
