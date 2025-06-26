from django.urls import path
from . import views


urlpatterns = [
    path('load_Catagory/',views.load_category_object,name='category_load')
]