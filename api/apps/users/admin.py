from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.users.models import PatientProfile

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "primary_condition",
        "age",
        "state",
        "extraction_available",
        "created_at",
    )
    list_filter = ("state", "extraction_available", "sex_for_eligibility")
    search_fields = ("user__email", "primary_condition", "city")
    readonly_fields = ("created_at", "updated_at")
