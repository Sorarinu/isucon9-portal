from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from ipware import get_client_ip

from isucon.portal.contest import models as contest_models
from isucon.portal.internal import serializers as internal_serializers


class JobViewSet(viewsets.GenericAPIViewSet):
    serializer_class = internal_serializers.JobSerializer

    def get_queryset(self):
        client_ip, _ = get_client_ip(self.request)
        if client_ip is None:
            # FIXME: client_ip取得できなかったエラー
            pass

        queryset = contest_models.Job.objects.all()
        benchmarker = get_object_or_404(queryset, ip=client_ip)
        return contest_models.Job.objects.dequeue(benchmarker)

    @detail_route(methods=['post'])
    def dequeue(self, request, *args, **kwargs):
        """ベンチマーカが処理すべきジョブをジョブキューからdequeueします"""
        client_ip, _ = get_client_ip(request)
        if client_ip is None:
            return HttpResponse('IPアドレスが不正です', status.HTTP_400_BAD_REQUEST)

        try:
            benchmarker = contest_models.Benchmarker.objects.get(ip=client_ip)
        except contest_models.Benchmarker.DoesNotExist:
            return HttpResponse('登録されていないベンチマーカーです', status.HTTP_400_BAD_REQUEST)

        job = contest_models.Job.dequeue(benchmarker)
        if job is None:
            return HttpResponse('ジョブキューが空です', status.HTTP_404_NOT_FOUND)

        job_serializer = self.serializer_class(instance=job)
        return Response(job_serializer.data)

    @detail_route(methods=['post'])
    def report_result(self, request, *args, **kwargs):
        """ベンチマーカーからの結果報告を受け取り、ジョブを更新します"""
        pass