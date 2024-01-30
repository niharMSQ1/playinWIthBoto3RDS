from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

from .models import *

import json
import random
import pdfkit

from .s3Util import upload_to_s3


@csrf_exempt
def register(request):
    username = (json.loads(request.body)).get('username')
    email = json.loads(request.body).get('email')
    password = json.loads(request.body).get('password')

    createUser = User.objects.create_user(username = username, email = email, password = password)

    return json(
        {
            "status":"Success",
            "message":f"User {username} registered successfully"
        },
        status = status.HTTP_201_CREATED
    )

@csrf_exempt
def login(request):
    username = (json.loads(request.body)).get('username')
    password = (json.loads(request.body)).get('password')

    user = authenticate(request, username=username, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)

        return JsonResponse(
            {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def createPdf(request):
    all_objects = InspirationalValue.objects.all()
    values_list = [{'key': obj.key, 'value': obj.value} for obj in all_objects]

    random_element = random.choice(values_list)

    context = {'key': random_element['key'],
               'value':random_element['value']}

    html_content = render(request, 'inspirational_value.html', context)

    html_message = render_to_string('inspirational_value.html', context)

    pdf_filename = "inspiration.pdf"
    pdfkit.from_string(html_message,pdf_filename)

    # Upload the PDF to S3
    s3_bucket = settings.BUCKET_NAME
    s3_file_path = f"{pdf_filename}"

    upload_to_s3(pdf_filename, s3_bucket, s3_file_path)

    s3_url = f"https://{s3_bucket}.s3.amazonaws.com/{s3_file_path}"

    return

@csrf_exempt
def storeQuotes(request):
    try:
        data = json.loads(request.body.decode('utf-8'))

        for key, value in data.items():
            InspirationalValue.objects.create(key=key, value=value)

        response_data = {'success': True, 'message': 'Values saved successfully.'}
        status_code = 200

    except json.JSONDecodeError:
        response_data = {'success': False, 'message': 'Invalid JSON data.'}
        status_code = 400

    except Exception as e:
        response_data = {'success': False, 'message': str(e)}
        status_code = 500

    return JsonResponse(response_data, status=status_code)
