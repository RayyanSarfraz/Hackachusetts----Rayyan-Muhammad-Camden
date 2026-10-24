from django.contrib import admin

from apps.engine.models import Trial


@admin.register(Trial)
class TrialAdmin(admin.ModelAdmin):
    list_display = ("nct_id", "title", "phase", "status", "massachusetts_city")
    list_filter = ("status", "phase")
    search_fields = ("nct_id", "title", "conditions")
    readonly_fields = ("created_at", "updated_at")
