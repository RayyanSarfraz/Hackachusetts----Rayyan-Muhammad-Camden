"""
Integration API URLs.
"""

from django.urls import path

from .views import (
    AnswerQuestionView,
    CompareTrialsView,
    DemoComparisonView,
    UpdatePreferencesView,
)

app_name = "integration"

urlpatterns = [
    path("compare/", CompareTrialsView.as_view(), name="compare"),
    path("answer/", AnswerQuestionView.as_view(), name="answer"),
    path("preferences/", UpdatePreferencesView.as_view(), name="preferences"),
    path("demo/", DemoComparisonView.as_view(), name="demo"),
]
