"""
URL configuration for config project.

Modular Monolith: each module under ``apps`` exposes its own URLConf, mounted
here under the ``/api/`` prefix.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/users/", include("apps.users.urls")),
    path("api/engine/", include("apps.engine.urls")),
    path("api/integration/", include("apps.integration.urls")),
]
