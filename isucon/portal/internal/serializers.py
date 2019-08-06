from rest_framework import serializers

from isucon.portal.authentication.models import Team
from isucon.portal.contest.models import Server, Job


class ServerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Server
        fields = ('id', 'hostname', 'global_ip', 'private_ip', 'is_bench_target')


class TeamSerializer(serializers.ModelSerializer):
    """チームと、ベンチマークやblackboxで必要なサーバ情報のシリアライザ"""
    servers = ServerSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ('id', 'owner', 'name', 'servers')


class JobSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job
        fields = ('id', 'score', 'is_passed', 'reason', 'stdout', 'stderr')
