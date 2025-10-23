from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_interview, name='start_interview'),
    path('next/', views.next_question, name='next_question'),
    path('answer/', views.submit_answer, name='submit_answer'),
]