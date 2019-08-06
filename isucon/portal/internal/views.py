from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from ipware import get_client_ip

from isucon.portal.contest.models import Benchmarker, Job
from isucon.portal.internal.serializers import JobSerializer, JobResultSerializer


class JobViewSet(viewsets.GenericAPIViewSet):
    serializer_class = JobSerializer

    @detail_route(methods=['post'])
    def dequeue(self, request, *args, **kwargs):
        """ベンチマーカが処理すべきジョブをジョブキューからdequeueします"""
        client_ip, _ = get_client_ip(request)
        if client_ip is None:
            return HttpResponse('IPアドレスが不正です', status.HTTP_400_BAD_REQUEST)

        try:
            benchmarker = Benchmarker.objects.get(ip=client_ip)
        except Benchmarker.DoesNotExist:
            return HttpResponse('登録されていないベンチマーカーです', status.HTTP_400_BAD_REQUEST)

        job = Job.objects.dequeue(benchmarker)
        if job is None:
            return HttpResponse('ジョブキューが空です', status.HTTP_422_UNPROCESSABLE_ENTITY)

        # FIXME: うまく整形して返す
        job_serializer = self.serializer_class(instance=job)
        return Response(job_serializer.data)


class JobResultViewSet(viewsets.GenericAPIViewSet):
    serializer_class = JobResultSerializer

    @detail_route(methods=['post'])
    def report_result(self, request, *args, **kwargs):
        """ベンチマーカーからの結果報告を受け取り、ジョブを更新します"""
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            instance.done(**serializer.validated_data)
        except RuntimeError:
            return HttpResponse('ジョブ結果報告の形式が不正です', status.HTTP_400_BAD_REQUEST)

        return HttpResponse('ジョブ結果報告を受け付けました', status.HTTP_201_ACCEPTED)