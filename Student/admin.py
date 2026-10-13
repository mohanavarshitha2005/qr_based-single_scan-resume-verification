from django.contrib import admin
from .models import Student, Resume, Certificate


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "mobile_number", "created_at"]
    search_fields = ["email", "name"]


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ["student", "created_at"]
    search_fields = ["student__name"]


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ["student", "file_type", "created_at"]
    list_filter = ["file_type"]
    search_fields = ["student__name"]
