from django.shortcuts import render
from django.http import JsonResponse
import interview_bot

# Create your views here.
def test_view(request):
    return JsonResponse({"success": True, "file": interview_bot.__file__})
