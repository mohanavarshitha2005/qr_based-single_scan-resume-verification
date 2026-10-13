import hashlib
from django.db import models


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


class StudentManager(models.Manager):
    def create_student(self, name, email, mobile_number, password):
        return self.create(
            name=name,
            email=email,
            mobile_number=mobile_number,
            password=hash_password(password),
        )


class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15)
    roll_number = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = StudentManager()

    def __str__(self):
        return f"{self.name}"

    def check_password(self, raw_password):
        return self.password == hash_password(raw_password)


class Resume(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="resumes"
    )
    file = models.FileField(upload_to="resumes/")
    qr_upload = models.FileField(upload_to="qr/", null=True, blank=True)
    qr_resume = models.FileField(upload_to="qr/", null=True, blank=True)
    qr_certificates = models.FileField(upload_to="qr/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume of {self.student.name}"


class Certificate(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="certificates"
    )
    file = models.FileField(upload_to="certificates/")
    file_type = models.CharField(
        max_length=10,
        choices=[("PDF", "PDF"), ("IMAGE", "Image")],
        null=True,
        blank=True,
    )
    certificate_id = models.CharField(max_length=100, null=True, blank=True)
    certificate_issuer = models.CharField(max_length=200, null=True, blank=True)
    phash = models.CharField(max_length=64, null=True, blank=True)
    file_hash = models.CharField(max_length=64, null=True, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=[("REAL", "REAL"), ("FAKE", "FAKE")],
        default="PENDING",
    )
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate of {self.student.name}"
