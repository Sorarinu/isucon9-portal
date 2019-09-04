from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter
from rest_framework import exceptions
from ipware import get_client_ip

from isucon.portal.authentication.models import Team
from isucon.portal.contest.models import Benchmarker, Job
from isucon.portal.internal.serializers import JobSerializer, JobResultSerializer
from isucon.portal.contest import exceptions as contest_exceptions


router = SimpleRouter()


class JobViewSet(viewsets.GenericViewSet):
    serializer_class = JobSerializer

    @action(methods=['post'], detail=False)
    def dequeue(self, request, *args, **kwargs):
        """ベンチマーカが処理すべきジョブをジョブキューからdequeueします"""
        # ベンチマーカーを取得するため、HTTPクライアントのIPアドレスを用いる
        client_ip, _ = get_client_ip(request)
        if client_ip is None:
            raise exceptions.ParseError()

        try:
            benchmarker = Benchmarker.objects.get(ip=client_ip)
        except Benchmarker.DoesNotExist:
            return Response({"error":'Unknown IP Address'}, status=status.HTTP_400_BAD_REQUEST)


        # チームとベンチマーカーが紐づくと仮定して、ジョブを取ってくる
        try:
            job = Job.objects.dequeue(benchmarker)
            serializer = self.get_serializer_class()(instance=job)
            return Response(serializer.data)
        except contest_exceptions.JobDoesNotExistError:
            pass

        # チームに紐づくジョブを見つけられなかったら、他に手頃なジョブを引っ張ってくる
        # TODO: ポータルが、チームとベンチマーカーの紐付けがない状況かどうか判断できる何かしらを用意し、それを根拠に分岐する
        try:
            job = Job.objects.dequeue()
            serializer = self.get_serializer_class()(instance=job)
            return Response(serializer.data)
        except contest_exceptions.JobDoesNotExistError:
            pass

        # 結局ジョブが見つからなかった
        return Response(status=status.HTTP_204_NO_CONTENT)


router.register("job", JobViewSet, base_name="job")


class JobResultViewSet(viewsets.GenericViewSet):
    serializer_class = JobResultSerializer

    @action(methods=['post'], detail=True)
    def report(self, request, pk=None):
        """ベンチマーカーからの結果報告を受け取り、ジョブを更新します"""
        instance = get_object_or_404(Job.objects.all(), pk=pk)
        serializer = self.get_serializer(data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)

            if not "score" in serializer.validated_data:
                raise RuntimeError()

            data = {
                "is_passed": False,
            }
            data.update(serializer.validated_data)

            instance.done(**data)
        except RuntimeError:
            return Response({"error":'Invalid format'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data)


router.register("job", JobResultViewSet, base_name="job-result")
