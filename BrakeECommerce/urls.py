from django.contrib import admin
from django.urls import path, include
from vehicles import views as vehicles_views
from main import views as main_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chaining/', include('smart_selects.urls')),

    # SITES
    path('', main_views.home, name='home'),
    path('catalogue/<str:vehicle_type>/<slug:slug>/<int:vehicle_id>/', main_views.catalogue, name='catalogue'),

    # API CALLS
    path('api/brands/', vehicles_views.get_brands, name='get_brands'),
    path('api/models/', vehicles_views.get_models, name='get_models'),
    path('api/types/', vehicles_views.get_types, name='get_types'),
    path('api/displacements/', vehicles_views.get_displacements, name='get_displacements'),
    path('api/years/', vehicles_views.get_years, name='get_years'),
]
