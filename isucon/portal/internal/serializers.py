from rest_framework import serializers

from isucon.portal.authentication.models import Team
from isucon.portal.contest.models import Server, Job


class ServerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Server
        fields = ('id', 'hostname', 'global_ip', 'private_ip', 'is_bench_target')
        read_only_fields = fields


class TeamSerializer(serializers.ModelSerializer):
    """チームと、ベンチマークやblackboxで必要なサーバ情報のシリアライザ"""

    class Meta:
        model = Team
        fields = ('id', 'owner', 'name', 'servers')
        read_only_fields = fields

    servers = ServerSerializer(many=True, read_only=True)

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ('id', 'team', 'status', 'score', 'reason', 'stdout', 'stderr')
        read_only_fields = fields

    team = TeamSerializer(many=False, read_only=True)


class JobResultSerializer(serializers.ModelSerializer):

    class Meta:
        model = Job
        fields = ('id', 'score', 'is_passed', 'reason', 'stdout', 'stderr')
