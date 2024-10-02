from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_or_register, name='login_or_register'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/', include('allauth.urls')),
    

    path('dashboard/', views.dashboard, name='dashboard'),
    path('update-user/', views.update_user, name='update_user'),
   
]