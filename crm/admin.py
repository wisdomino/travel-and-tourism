from django.contrib import admin
from .models import (
    Organization,
    Branch,
    Program,
    Client,
    Case,
    StatusHistory,
    Document,
)


# -----------------------------
# ORGANIZATION & BRANCH
# -----------------------------

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "default_timezone", "default_language", "created_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "country_code", "city", "timezone", "created_at")
    list_filter = ("organization", "country_code")
    search_fields = ("name", "organization__name", "city")
    ordering = ("organization", "name")


# -----------------------------
# PROGRAMS (GLOBAL ROUTES)
# -----------------------------

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "destination_country_code",
        "application_type",
        "update_sla_days",
        "is_active",
    )
    list_filter = ("organization", "application_type", "destination_country_code", "is_active")
    search_fields = ("name",)
    ordering = ("organization", "name")


# -----------------------------
# CLIENT
# -----------------------------

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "client_code",
        "full_name",
        "phone_e164",
        "email",
        "organization",
        "timezone",
        "created_at",
    )
    list_filter = ("organization", "timezone", "preferred_language", "created_at")
    search_fields = ("client_code", "full_name", "phone_e164", "email")
    ordering = ("-created_at",)


# -----------------------------
# INLINE MODELS
# -----------------------------

class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ("old_status", "new_status", "changed_by", "changed_at")
    can_delete = False


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ("doc_type", "status", "file", "expiry_date", "version", "uploaded_by")
    readonly_fields = ("uploaded_by",)


# -----------------------------
# CASE
# -----------------------------

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        "case_code",
        "client",
        "organization",
        "destination_country_code",
        "application_type",
        "current_status",
        "priority",
        "assigned_officer",
        "updated_at",
    )
    list_filter = (
        "organization",
        "current_status",
        "application_type",
        "priority",
        "destination_country_code",
    )
    search_fields = (
        "case_code",
        "client__client_code",
        "client__full_name",
        "client__phone_e164",
    )
    autocomplete_fields = ("client", "assigned_officer", "program", "branch")
    ordering = ("-updated_at",)
    inlines = [StatusHistoryInline, DocumentInline]

    fieldsets = (
        ("Core Information", {
            "fields": (
                "case_code",
                "client",
                "organization",
                "branch",
                "program",
            )
        }),
        ("Application Details", {
            "fields": (
                "destination_country_code",
                "application_type",
                "current_status",
                "priority",
                "assigned_officer",
            )
        }),
        ("Progress Tracking", {
            "fields": (
                "last_client_update_at",
                "next_action",
                "notes",
            )
        }),
        ("Lifecycle Dates", {
            "fields": (
                "submitted_at",
                "closed_at",
            )
        }),
    )


# -----------------------------
# DOCUMENT
# -----------------------------

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "doc_type",
        "status",
        "expiry_date",
        "version",
        "uploaded_by",
        "updated_at",
    )
    list_filter = ("doc_type", "status")
    search_fields = (
        "case__case_code",
        "case__client__client_code",
        "case__client__full_name",
    )
    ordering = ("-updated_at",)


# -----------------------------
# STATUS HISTORY
# -----------------------------

@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "case",
        "old_status",
        "new_status",
        "changed_by",
        "changed_at",
    )
    list_filter = ("new_status", "changed_at")
    search_fields = (
        "case__case_code",
        "case__client__client_code",
        "case__client__full_name",
    )
    ordering = ("-changed_at",)
