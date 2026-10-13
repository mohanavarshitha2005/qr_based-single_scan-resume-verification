from django.shortcuts import render, redirect
from django.contrib import messages
from Student.models import Student, Resume, Certificate


def recruiter_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username == "recruiter" and password == "recruiter":
            return redirect("recruiter_dashboard")
        else:
            messages.error(request, "Invalid recruiter credentials")

    return render(request, "recruiterLogin.html")


def recruiter_dashboard(request):
    return render(request, "Recruiter/recruiterHome.html")


def download_resume(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
        from django.http import FileResponse

        return FileResponse(
            open(resume.file.path, "rb"),
            as_attachment=True,
            filename=f"resume_{resume.student.roll_number}.pdf",
        )
    except Resume.DoesNotExist:
        messages.error(request, "Resume not found")
        return redirect("recruiter_dashboard")


from django.http import HttpResponse
from PIL import Image
import io

def download_certificate(request, certificate_id):
    try:
        certificate = Certificate.objects.get(
            id=certificate_id, verification_status="REAL"
        )

        image = Image.open(certificate.file.path)

        # Convert to RGB (important for PNG with transparency)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        buffer = io.BytesIO()
        image.save(buffer, format="PDF")
        buffer.seek(0)

        return HttpResponse(
            buffer,
            content_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="certificate_{certificate.student.roll_number}.pdf"'
            },
        )

    except Certificate.DoesNotExist:
        messages.error(request, "Certificate not found or not verified")
        return redirect("recruiter_dashboard")


def student_list(request):
    students = Student.objects.all().prefetch_related("resumes")
    students_data = []
    for student in students:
        latest_resume = student.resumes.first()
        students_data.append({"student": student, "resume": latest_resume})
    return render(
        request, "Recruiter/student_list.html", {"students_data": students_data}
    )

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO


def preview_resume_with_qr(request, resume_id):
    try:
        # ✅ Get resume
        resume = get_object_or_404(Resume, id=resume_id)

        # ✅ Load original PDF
        reader = PdfReader(resume.file.path)
        writer = PdfWriter()

        # ✅ Process first page for QR
        first_page = reader.pages[0]

        # ✅ Get actual PDF size (IMPORTANT FIX)
        page_width = float(first_page.mediabox.width)
        page_height = float(first_page.mediabox.height)

        # ✅ Create overlay PDF
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))

        if resume.qr_certificates:
            qr_image_path = resume.qr_certificates.path

            # ✅ QR size
            qr_width = 80
            qr_height = 80

            # ✅ Perfect TOP-RIGHT CORNER
            x_pos = page_width - qr_width - 20
            y_pos = page_height - qr_height - 20

            # ✅ White background (professional look)
            can.setFillColorRGB(1, 1, 1)
            can.rect(x_pos - 5, y_pos - 5, qr_width + 10, qr_height + 20, fill=1)

            # ✅ Draw QR
            can.drawImage(qr_image_path, x_pos, y_pos,
                          width=qr_width, height=qr_height)

            # ✅ Label
            can.setFillColorRGB(0, 0, 0)
            can.setFont("Helvetica-Bold", 8)
            can.drawString(x_pos, y_pos - 12, "View Certificate")

        # ✅ Save overlay
        can.save()
        packet.seek(0)

        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        # ✅ Merge QR with FIRST PAGE
        first_page.merge_page(overlay_page)

        # ✅ Add all pages
        for page in reader.pages:
            writer.add_page(page)

        # ✅ Return PDF in browser (preview)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "inline; filename=resume_preview.pdf"

        writer.write(response)
        return response

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect("student_list")
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO


def download_resume_with_qr(request, resume_id):
    try:
        # ✅ Get resume
        resume = get_object_or_404(Resume, id=resume_id)

        reader = PdfReader(resume.file.path)
        writer = PdfWriter()

        # ✅ Get first page
        first_page = reader.pages[0]

        # ✅ Get ACTUAL PDF size (IMPORTANT FIX)
        page_width = float(first_page.mediabox.width)
        page_height = float(first_page.mediabox.height)

        # ✅ Create overlay
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))

        if resume.qr_certificates:
            qr_image_path = resume.qr_certificates.path

            # ✅ QR size
            qr_width = 80   
            qr_height = 80

            # ✅ PERFECT TOP-RIGHT CORNER
            x_pos = page_width - qr_width - 20
            y_pos = page_height - qr_height - 20

            # ✅ White background (clean look)
            can.setFillColorRGB(1, 1, 1)
            can.rect(x_pos - 5, y_pos - 5, qr_width + 10, qr_height + 20, fill=1)

            # ✅ Draw QR
            can.drawImage(qr_image_path, x_pos, y_pos,
                          width=qr_width, height=qr_height)

            # ✅ Label
            can.setFillColorRGB(0, 0, 0)
            can.setFont("Helvetica-Bold", 8)
            can.drawString(x_pos, y_pos - 12, "View Certificate")

        # ✅ Save overlay
        can.save()
        packet.seek(0)

        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        # ✅ Merge QR onto FIRST PAGE
        first_page.merge_page(overlay_page)

        # ✅ Add all pages
        for page in reader.pages:
            writer.add_page(page)

        # ✅ Download response
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="resume_{resume.student.roll_number}_with_qr.pdf"'
        )

        writer.write(response)
        return response

    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect("student_list")