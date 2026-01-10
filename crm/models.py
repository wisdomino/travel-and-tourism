from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    default_timezone = models.CharField(max_length=64, default="Africa/Lagos")
    default_language = models.CharField(max_length=20, default="en")

    def __str__(self) -> str:
        return self.name


class Branch(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=200)
    country_code = models.CharField(max_length=2)  # ISO-3166 alpha-2, e.g. NG, GB
    city = models.CharField(max_length=120, blank=True, null=True)
    timezone = models.CharField(max_length=64, default="Africa/Lagos")

    def __str__(self) -> str:
        return f"{self.organization.slug} - {self.name}"


class ApplicationType(models.TextChoices):
    STUDY = "STUDY", "Study"
    WORK = "WORK", "Work"
    VISIT = "VISIT", "Visit/Tourism"
    PR = "PR", "Permanent Residency"
    BUSINESS = "BUSINESS", "Business"
    OTHER = "OTHER", "Other"


class CaseStatus(models.TextChoices):
    NEW_INQUIRY = "NEW_INQUIRY", "New Inquiry"
    CONSULTATION_COMPLETED = "CONSULTATION_COMPLETED", "Consultation Completed"
    DOCS_REQUESTED = "DOCS_REQUESTED", "Documents Requested"
    DOCS_RECEIVED = "DOCS_RECEIVED", "Documents Received"
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED", "Application Submitted"
    EMBASSY_REVIEW = "EMBASSY_REVIEW", "Embassy Review"
    ADDITIONAL_DOCS_REQUESTED = "ADDITIONAL_DOCS_REQUESTED", "Additional Docs Requested"
    DECISION_RECEIVED = "DECISION_RECEIVED", "Decision Received"
    APPROVED = "APPROVED", "Approved"
    REFUSED = "REFUSED", "Refused"
    CLOSED = "CLOSED", "Closed"


class CasePriority(models.TextChoices):
    NORMAL = "NORMAL", "Normal"
    URGENT = "URGENT", "Urgent"


class Program(TimeStampedModel):
    """
    Global-ready: different routes have different requirements.
    Example: 'Canada Study SDS', 'UK Skilled Worker', 'Schengen Tourist'
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="programs")
    name = models.CharField(max_length=200)
    destination_country_code = models.CharField(max_length=2)  # ISO, e.g. CA, GB
    application_type = models.CharField(max_length=20, choices=ApplicationType.choices)
    is_active = models.BooleanField(default=True)

    # Optional: SLA rule, e.g. update client every N days
    update_sla_days = models.PositiveIntegerField(default=7)

    class Meta:
        unique_together = ("organization", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.destination_country_code})"


class Client(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="clients")
    client_code = models.CharField(max_length=20, unique=True, db_index=True)  # CL-0001

    full_name = models.CharField(max_length=200)
    phone_e164 = models.CharField(max_length=30, db_index=True)  # +234...
    email = models.EmailField(blank=True, null=True)

    timezone = models.CharField(max_length=64, default="Africa/Lagos")
    preferred_language = models.CharField(max_length=20, default="en")

    source = models.CharField(max_length=80, blank=True, null=True)  # referral/instagram/walk-in

    def __str__(self) -> str:
        return f"{self.client_code} - {self.full_name}"


class Case(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="cases")
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="cases")
    program = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True, blank=True, related_name="cases")

    case_code = models.CharField(max_length=20, unique=True, db_index=True)  # APP-0001
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cases")

    destination_country_code = models.CharField(max_length=2)  # ISO country code
    application_type = models.CharField(max_length=20, choices=ApplicationType.choices, default=ApplicationType.OTHER)

    current_status = models.CharField(max_length=40, choices=CaseStatus.choices, default=CaseStatus.NEW_INQUIRY, db_index=True)
    priority = models.CharField(max_length=10, choices=CasePriority.choices, default=CasePriority.NORMAL, db_index=True)

    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_cases"
    )

    last_client_update_at = models.DateTimeField(blank=True, null=True, db_index=True)
    next_action = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    submitted_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.case_code} ({self.client.client_code})"


class StatusHistory(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="status_history")
    old_status = models.CharField(max_length=40, choices=CaseStatus.choices)
    new_status = models.CharField(max_length=40, choices=CaseStatus.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(default=timezone.now, db_index=True)
    comment = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["-changed_at"]
        indexes = [models.Index(fields=["case", "changed_at"])]

    def __str__(self) -> str:
        return f"{self.case.case_code}: {self.old_status} -> {self.new_status}"


class DocumentType(models.TextChoices):
    PASSPORT = "PASSPORT", "Passport"
    PHOTO = "PHOTO", "Photo"
    BANK_STATEMENT = "BANK_STATEMENT", "Bank Statement"
    SOP = "SOP", "Statement of Purpose"
    ADMISSION_LETTER = "ADMISSION_LETTER", "Admission Letter"
    MEDICAL = "MEDICAL", "Medical"
    POLICE_CLEARANCE = "POLICE_CLEARANCE", "Police Clearance"
    OTHER = "OTHER", "Other"


class DocumentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUBMITTED = "SUBMITTED", "Submitted"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class Document(TimeStampedModel):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=40, choices=DocumentType.choices, default=DocumentType.OTHER, db_index=True)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.PENDING, db_index=True)

    file = models.FileField(upload_to="case_documents/%Y/%m/", blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    expiry_date = models.DateField(blank=True, null=True)  # global-ready: passports/medical often expire
    version = models.PositiveIntegerField(default=1)

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.case.case_code} - {self.doc_type}"

class OneTimePassword(models.Model):
    class Purpose(models.TextChoices):
        PORTAL_LOGIN = "PORTAL_LOGIN", "Portal Login"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps",
        null=True,
        blank=True,
    )
    recipient = models.CharField(max_length=120)  # email or phone
    code = models.CharField(max_length=10)
    purpose = models.CharField(max_length=30, choices=Purpose.choices, default=Purpose.PORTAL_LOGIN)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"OTP({self.recipient}) - {self.code}"