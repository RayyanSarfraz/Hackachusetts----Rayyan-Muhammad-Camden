from django.urls import path

from apps.engine.views import EngineStatusView

app_name = "engine"

urlpatterns = [
    path("status/", EngineStatusView.as_view(), name="status"),
]
