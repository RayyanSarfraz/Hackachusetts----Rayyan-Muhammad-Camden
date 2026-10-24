from django.urls import path

from apps.engine.views import EngineStatusView, IntakeView, TrialSearchView

app_name = "engine"

urlpatterns = [
    path("status/", EngineStatusView.as_view(), name="status"),
    path("intake/", IntakeView.as_view(), name="intake"),
    path("trials/", TrialSearchView.as_view(), name="trials"),
]
