from rest_framework import serializers
from .models import Brand, Model, Car, CommercialVehicle, MotorBike

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']

class VehicleModelSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False, allow_null=True)
    date_end   = serializers.DateField(format="%m/%y", required=False, allow_null=True)

    class Meta:
        model = Model
        fields = ['id', 'name', 'date_start', 'date_end']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['date_start'] = data['date_start'] or "?"
        data['date_end']   = data['date_end'] or "now"
        return data

class CarSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False, allow_null=True)
    date_end   = serializers.DateField(format="%m/%y", required=False, allow_null=True)

    class Meta:
        model = Car
        fields = ['id', 'name', 'kw', 'cv', 'date_start', 'date_end']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['date_start'] = data['date_start'] or "?"
        data['date_end']   = data['date_end'] or "now"
        return data

class CVSerializer(serializers.ModelSerializer):
    date_start = serializers.DateField(format="%m/%y", required=False, allow_null=True)
    date_end   = serializers.DateField(format="%m/%y", required=False, allow_null=True)

    class Meta:
        model = CommercialVehicle
        fields = ['id', 'name', 'kw', 'cv', 'date_start', 'date_end']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['date_start'] = data['date_start'] or "?"
        data['date_end']   = data['date_end'] or "now"
        return data

class MotorBikeSerializer(serializers.ModelSerializer):
    years = serializers.SlugRelatedField(many=True, read_only=True, slug_field='value')
    class Meta:
        model = MotorBike
        fields = ['id', 'brand', 'model', 'displacement', 'years']
