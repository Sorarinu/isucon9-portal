from rest_framework import serializers

from isucon.portal.contest import models as contest_models


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = contest_models.Job
        fields = ('id', 'target_server_ip')

    def get_target_server_ip(self, obj):
        team = obj.team
        target_server = contest_models.ServerManager.objects.get_bench_target(team)
        return target_server.private_ip


class JobResultSerializer(serializers.Serializer):
    score = serializers.IntegerField(required=True)
    is_passed = serializers.BooleanField(required=True)
    stdout = serializers.CharField(required=True)
    stderr = serializers.CharField(required=True)

    def validate(self, data):
        pass