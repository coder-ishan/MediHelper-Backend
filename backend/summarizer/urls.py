from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_and_summarize, name='upload_and_summarize'),
    path('test/', views.get_text_from_pdf, name='get_text_from_pdf'),
    path('answer/', views.answer_question, name='answer_question'),
]
