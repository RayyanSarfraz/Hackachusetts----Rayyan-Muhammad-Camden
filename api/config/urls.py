"""
URL configuration for config project.

Modular Monolith: each module under ``apps`` exposes its own URLConf, mounted
here under the ``/api/`` prefix.
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.integration.views import ExtractFactsView, TrialsView


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/users/", include("apps.users.urls")),
    path("api/engine/", include("apps.engine.urls")),
    path("api/integration/", include("apps.integration.urls")),
    # Frontend-facing seam consumed by the React client's HttpTrialBridgeApi.
    # Mounted at top-level /api to match client/src/api/adapter.ts expectations.
    path("api/trials/", TrialsView.as_view(), name="trials"),
    path("api/extract-facts/", ExtractFactsView.as_view(), name="extract-facts"),
]
