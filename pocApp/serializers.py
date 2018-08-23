# api/serializers.py

from rest_framework import serializers
from .models import MyCertsData

class MyCertsDataSerializer(serializers.ModelSerializer):
    """Serializer to map the Model instance into JSON format."""

    class Meta:
        """Meta class to map serializer's fields with the model fields."""
        model = MyCertsData
        fields = ('valid_start', 'valid_end', 'xmldata', 'status', 'hostname', 'md5', 'sha1')