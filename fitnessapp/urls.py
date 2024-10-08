from django.urls import path, include
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_or_register, name='login_or_register'),
    path('logout/', views.logout_view, name='logout'),
    path('accounts/', include('allauth.urls')),

    

    path('dashboard/', views.dashboard, name='dashboard'),

   

    path('diet/', views.diet_tracker, name='diet_tracker'),
    
    path('get_diet/', views.process_diet_request, name='get_diet'),

 


    path('aboutus/', views.aboutus, name='aboutus'),
    path('contact/', views.contact, name='contact'),
    path('pricing/', views.pricing, name='pricing'),
    path('privacy/', views.privacy, name='privacy'),
    path('termsandconditions/', views.termsandconditions, name='termsandconditions'),
    path('cancelandrefund/', views.cancelandrefund, name='cancelandrefund'),


   
]