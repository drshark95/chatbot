from django.contrib.auth import authenticate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.parsers import JSONParser

from .faq_chatbot import faq_answer
from .models import Addresses
from .serializers import AddressesSerializer


def get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def address_list(request):
    if request.method == 'GET':
        serializer = AddressesSerializer(Addresses.objects.all(), many=True)
        return JsonResponse(serializer.data, safe=False)

    data = JSONParser().parse(request)
    serializer = AddressesSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data, status=201)
    return JsonResponse(serializer.errors, status=400)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'DELETE'])
def address(request, pk):
    obj = get_object_or_404(Addresses, pk=pk)

    if request.method == 'GET':
        return JsonResponse(AddressesSerializer(obj).data)

    if request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = AddressesSerializer(obj, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    obj.delete()
    return HttpResponse(status=204)


@require_http_methods(['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        username = request.POST.get('userid', '')
        password = request.POST.get('userpw', '')
        if authenticate(username=username, password=password):
            return HttpResponse(status=200)
        return HttpResponse(status=401)
    return render(request, 'addresses/login.html')


@csrf_exempt
@require_http_methods(['POST'])
def app_login(request):
    username = request.POST.get('userid', '')
    password = request.POST.get('userpw', '')
    if authenticate(username=username, password=password):
        return JsonResponse({'code': '0000', 'msg': '로그인 성공입니다.'})
    return JsonResponse({'code': '1001', 'msg': '로그인 실패입니다.'})


def _chat_response(request, template_name):
    if request.method == 'GET':
        return render(request, template_name)

    question = request.POST.get('input1', '').strip()
    if not question:
        return JsonResponse({'error': '질문을 입력해 주세요.'}, status=400)

    response = faq_answer(
        question,
        request.POST.get('useragent1', ''),
        get_client_ip(request),
    )
    return JsonResponse({'response': response})


@require_http_methods(['GET', 'POST'])
def chat_test(request):
    return _chat_response(request, 'addresses/chat_test.html')


@require_http_methods(['GET', 'POST'])
def chat_service(request):
    return _chat_response(request, 'addresses/chat_service.html')
