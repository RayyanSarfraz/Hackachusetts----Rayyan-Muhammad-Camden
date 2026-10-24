import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager for the email-based custom user model."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user that authenticates with email instead of username."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


class PatientProfile(models.Model):
    """
    Persisted patient intake for the clinical-trial copilot.

    Stores both user-provided and AI-extracted medical information. List fields
    are JSON arrays of fact objects, each carrying a ``source`` ("user" or
    "extracted") so provenance is never lost. Missing information stays null or
    empty — nothing here is ever fabricated.
    """

    class Sex(models.TextChoices):
        FEMALE = "female", _("Female")
        MALE = "male", _("Male")
        INTERSEX = "intersex", _("Intersex")
        UNKNOWN = "unknown", _("Unknown / Prefer not to specify")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profiles",
    )

    # Basic patient information.
    age = models.PositiveIntegerField(null=True, blank=True)
    primary_condition = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=64, default="MA")
    sex_for_eligibility = models.CharField(
        max_length=16,
        choices=Sex.choices,
        null=True,
        blank=True,
    )

    # Free-text clinical note (treated as untrusted input downstream).
    medical_note = models.TextField(blank=True)

    # Structured medical lists. Each item is a dict that includes a "source"
    # key ("user" | "extracted"). Defaults to an empty list, never fabricated.
    conditions = models.JSONField(default=list, blank=True)
    symptoms = models.JSONField(default=list, blank=True)
    medications = models.JSONField(default=list, blank=True)
    previous_treatments = models.JSONField(default=list, blank=True)
    lab_results = models.JSONField(default=list, blank=True)

    # Conflicts flagged between user-provided and AI-extracted values.
    extraction_conflicts = models.JSONField(default=list, blank=True)

    # Whether the AI extractor actually ran for this profile.
    extraction_available = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "patient profile"
        verbose_name_plural = "patient profiles"

    def __str__(self):
        label = self.primary_condition or "unspecified condition"
        return f"PatientProfile<{self.user_id}: {label}>"
