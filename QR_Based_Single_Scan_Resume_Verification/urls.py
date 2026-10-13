from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from Student import views as student_views
from Recruiter import views as recruiter_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Home & Auth
    path("", student_views.home, name="home"),
    path("student/register/", student_views.student_register, name="student_register"),
    path("student/login/", student_views.student_login, name="student_login"),
    path("student/logout/", student_views.student_logout, name="student_logout"),
    path(
        "student/dashboard/", student_views.student_dashboard, name="student_dashboard"
    ),
    # Resume
    path("student/upload/resume/", student_views.upload_resume, name="upload_resume"),
    path(
        "student/generate/resume/",
        student_views.generate_ats_resume,
        name="generate_ats_resume",
    ),
    # QR-1: Certificate Upload (accessed via Resume QR)
    path(
        "upload-certificates/<int:student_id>/",
        student_views.upload_certificates_page,
        name="upload_certificates_page",
    ),
    # Certificate Upload
    path(
        "student/upload/certificate/",
        student_views.upload_certificate,
        name="upload_certificate",
    ),
    # QR-2: Certificate View (for recruiter)
    path(
        "view-certificates/<int:student_id>/",
        student_views.view_certificates_page,
        name="view_certificates_page",
    ),
    # Resume View
    path(
        "student/resume/view/<int:resume_id>/",
        student_views.resume_view,
        name="resume_view",
    ),
    path(
        "public-resume/<int:resume_id>/",
        student_views.public_resume_view,
        name="public_resume_view",
    ),
    path(
        "student/delete/data/",
        student_views.delete_student_data,
        name="delete_student_data",
    ),
    # Recruiter
    path("recruiter/login/", recruiter_views.recruiter_login, name="recruiter_login"),
    path(
        "recruiter/dashboard/",
        recruiter_views.recruiter_dashboard,
        name="recruiter_dashboard",
    ),
    path("recruiter/students/", recruiter_views.student_list, name="student_list"),
    path(
        "recruiter/preview/resume/<int:resume_id>/",
        recruiter_views.preview_resume_with_qr,
        name="preview_resume",
    ),
    path(
        "recruiter/download/resume/<int:resume_id>/",
        recruiter_views.download_resume,
        name="download_resume",
    ),
    path(
        "recruiter/download/resume/with-qr/<int:resume_id>/",
        recruiter_views.download_resume_with_qr,
        name="download_resume_with_qr",
    ),
    # urls.py
path('download-certificate/<int:certificate_id>/', recruiter_views.download_certificate, name='download_certificate'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
