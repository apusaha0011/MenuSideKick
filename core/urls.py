from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


#--------------------------------------
# DRF-YASG API Documentation
#--------------------------------------
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
schema_view = get_schema_view(
    openapi.Info(
        title="🍽️ Menu Sidekick API - Made by Shemanto Sharkar",
        default_version='v1',
        description="API documentation for the Menu SideKick project by Shemanto",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
#--------------------------------------



#--------------------------------------
# Sentry Error Trigger
#--------------------------------------
def trigger_error(request):
    division_by_zero = 1 / 0
#--------------------------------------



#--------------------------------------
# Redirect backend root to docs
#--------------------------------------
def redirect_to_docs(request):
    """Redirect root URL to API documentation"""
    return redirect('schema-swagger-ui')
#--------------------------------------



urlpatterns = [
    path('admin/', admin.site.urls),

    # Sentry Error Trigger
    path('sentry-debug/', trigger_error),

    # Local app routes
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.admin_dashboard.urls')),
    path('api/', include('apps.ai_responses.urls')),
    path('api/', include('apps.payments.urls')),

    path("api/auth/", include("dj_rest_auth.urls")),           # login/logout
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # Redirect root to docs
    path('', redirect_to_docs, name='root-redirect'),
]

