from django.http.response import HttpResponse


def test_index(request):
    return HttpResponse('hello world')
