from rest_framework import serializers


class GraphSerializer(serializer.Serializer):
    graph_min = serializers.CharField(max_length=255)
    graph_max = serializers.CharField(max_length=255)