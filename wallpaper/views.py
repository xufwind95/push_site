from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Wallpaper
from .source_spider import get_source
from common.const import (
    CODE_OK, CODE_INPUT_ERROR, CODE_SERVER_ERROR, CODE_VALIDATE_ERROR, CODE_AUTHENTICATION
)


@api_view(['GET'])
def get_wallpaper(request):
    url = request.GET.get("url", None)
    if not url:
        return Response(
            {
                'code': CODE_INPUT_ERROR,
                'msg': 'user input error',
                'data': ''
            }
        )
    instance = Wallpaper.objects.filter(original_url=url).first()
    host = request.get_host()
    if instance:
        return Response(
            {
                'code': 0,
                'msg': 'OK',
                'data': '{}{}'.format(host, instance.mp3.url)
            }
        )
    file_stream = get_source(url)
    if not file_stream:
        return Response(
            {
                'code': CODE_INPUT_ERROR,
                'msg': 'no such source',
                'data': ''
            },
            status=status.HTTP_200_OK
        )
    try:
        # reopen = open('/Users/cpx/PythonWorkSpace/PushSite/test/test_upload.mp3', 'rb')
        # django_file = File(reopen)
        file_name = url.split('/')[-1]
        upload_file = ContentFile(file_stream, name=file_name)
        instance = Wallpaper(
            name=file_name,
            original_url=url,
            mp3=upload_file,
        )
        instance.save()
        return Response(
            {
                'code': CODE_OK,
                'msg': 'OK',
                'data': '{}{}'.format(host, instance.mp3.url)
            }
        )
    except Exception as e:
        return Response(
            {
                'code': CODE_SERVER_ERROR,
                'msg': 'failed to upload file: {}'.format(e),
                'data': ''
            },
            status=status.HTTP_200_OK
        )
