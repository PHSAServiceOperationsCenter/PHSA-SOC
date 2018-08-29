# api/serializers.py

from rest_framework import serializers
from .models import NmapCertsData, NmapHistory

class CertsDataSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = NmapCertsData
        fields = '__all__'

class CertsHistSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = NmapHistory
        fields = '__all__'