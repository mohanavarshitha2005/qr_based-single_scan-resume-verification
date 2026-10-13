import datetime

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Resume, Certificate, hash_password
import qrcode
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.urls import reverse
import os, json, uuid, base64
import imagehash
from PIL import Image, ImageDraw
from django.core.files.storage import default_storage
from openai import OpenAI


def home(request):
    return render(request, "index.html")


def student_register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        mobile_number = request.POST.get("mobile_number")
        password = request.POST.get("password")

        if Student.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("student_register")

        student = Student.objects.create(
            name=name,
            email=email,
            mobile_number=mobile_number,
            password=hash_password(password),
        )
        
        messages.success(request, "Registration successful! Please login.")
        return redirect("student_login")

    return render(request, "studentRegister.html")


def student_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            student = Student.objects.get(email=email)
            if student.check_password(password):
                request.session["student_id"] = student.id
                return redirect("student_dashboard")
            else:
                messages.error(request, "Invalid credentials")
        except Student.DoesNotExist:
            messages.error(request, "Invalid credentials")

    return render(request, "studentLogin.html")


def student_logout(request):
    if "student_id" in request.session:
        del request.session["student_id"]
    return redirect("home")


def student_dashboard(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("student_login")

    try:
        student = Student.objects.get(id=student_id)
        resumes = Resume.objects.filter(student=student).order_by("-created_at")
        certificates = Certificate.objects.filter(student=student).order_by(
            "-created_at"
        )

        context = {
            "student": student,
            "resumes": resumes,
            "certificates": certificates,
        }
        return render(request, "Student/studentHome.html", context)
    except Student.DoesNotExist:
        return redirect("student_login")


def generate_ats_resume(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("student_login")

    if request.method == "POST":
        student = Student.objects.get(id=student_id)

        ats_data = {
            "name": request.POST.get("name", student.name),
            "email": request.POST.get("email", student.email),
            "phone": request.POST.get("phone", student.mobile_number),
            "roll_number": request.POST.get("roll_number", student.roll_number or ""),
            "summary": request.POST.get("summary", ""),
            "education": request.POST.get("education", ""),
            "skills": request.POST.get("skills", ""),
            "experience": request.POST.get("experience", ""),
            "projects": request.POST.get("projects", ""),
        }

        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        name_style = ParagraphStyle(
            "Name", parent=styles["Title"], fontSize=16, spaceAfter=10
        )
        story.append(Paragraph(ats_data["name"], name_style))
        story.append(
            Paragraph(
                f"Email: {ats_data['email']} | Phone: {ats_data['phone']} | Roll: {ats_data['roll_number']}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        if ats_data["summary"]:
            story.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
            story.append(Paragraph(ats_data["summary"], styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        if ats_data["education"]:
            story.append(Paragraph("<b>Education</b>", styles["Heading2"]))
            story.append(Paragraph(ats_data["education"], styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        if ats_data["skills"]:
            story.append(Paragraph("<b>Skills</b>", styles["Heading2"]))
            story.append(Paragraph(ats_data["skills"], styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        if ats_data["experience"]:
            story.append(Paragraph("<b>Experience</b>", styles["Heading2"]))
            story.append(Paragraph(ats_data["experience"], styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        if ats_data["projects"]:
            story.append(Paragraph("<b>Projects</b>", styles["Heading2"]))
            story.append(Paragraph(ats_data["projects"], styles["Normal"]))

        doc.build(story)
        buffer.seek(0)

        resume = Resume.objects.create(student=student, file="")
        resume.file.save(f"resume_{student.roll_number}.pdf", File(buffer))

        qr_a = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_a.add_data(request.build_absolute_uri(f"/upload-certificates/{student.id}/"))
        qr_a.make(fit=True)
        img_a = qr_a.make_image(fill_color="black", back_color="white")

        buffer_qr_a = BytesIO()
        img_a.save(buffer_qr_a, format="PNG")
        resume.qr_upload.save(f"qr_upload_{resume.id}.png", File(buffer_qr_a))

        qr_b = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_b.add_data(request.build_absolute_uri(f"/public-resume/{resume.id}/"))
        qr_b.make(fit=True)
        img_b = qr_b.make_image(fill_color="black", back_color="white")

        buffer_qr_b = BytesIO()
        img_b.save(buffer_qr_b, format="PNG")
        resume.qr_resume.save(f"qr_resume_{resume.id}.png", File(buffer_qr_b))

        qr_c = qrcode.QRCode(version=1, box_size=10, border=5)
        qr_c.add_data(request.build_absolute_uri(f"/view-certificates/{student.id}/"))
        qr_c.make(fit=True)
        img_c = qr_c.make_image(fill_color="black", back_color="white")

        buffer_qr_c = BytesIO()
        img_c.save(buffer_qr_c, format="PNG")
        resume.qr_certificates.save(f"qr_cert_{resume.id}.png", File(buffer_qr_c))

        resume.save()
        messages.success(request, "ATS Resume generated successfully!")
        return redirect("student_dashboard")

    return render(request, "Student/ATSResumegeneration.html")


def upload_resume(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("student_login")

    if request.method == "POST":
        if "file" in request.FILES:
            student = Student.objects.get(id=student_id)
            resume_file = request.FILES["file"]

            resume = Resume.objects.create(student=student, file=resume_file)

            qr_a = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_a.add_data(
                request.build_absolute_uri(f"/upload-certificates/{student.id}/")
            )
            qr_a.make(fit=True)
            img_a = qr_a.make_image(fill_color="black", back_color="white")

            buffer_a = BytesIO()
            img_a.save(buffer_a, format="PNG")
            resume.qr_upload.save(f"qr_upload_{resume.id}.png", File(buffer_a))

            qr_b = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_b.add_data(request.build_absolute_uri(f"/public-resume/{resume.id}/"))
            qr_b.make(fit=True)
            img_b = qr_b.make_image(fill_color="black", back_color="white")

            buffer_b = BytesIO()
            img_b.save(buffer_b, format="PNG")
            resume.qr_resume.save(f"qr_resume_{resume.id}.png", File(buffer_b))

            qr_c = qrcode.QRCode(version=1, box_size=10, border=5)
            qr_c.add_data(
                request.build_absolute_uri(f"/view-certificates/{student.id}/")
            )
            qr_c.make(fit=True)
            img_c = qr_c.make_image(fill_color="black", back_color="white")

            buffer_c = BytesIO()
            img_c.save(buffer_c, format="PNG")
            resume.qr_certificates.save(f"qr_cert_{resume.id}.png", File(buffer_c))

            resume.save()
            messages.success(request, "Resume uploaded successfully!")
            return redirect("student_dashboard")

    return redirect("student_dashboard")





# =========================
# 📄 PDF → IMAGE
# =========================
def pdf_to_image(pdf_path):
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    page = doc[0]
    # Higher zoom factor for better quality
    pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
    img_path = pdf_path + ".jpg"
    pix.save(img_path)
    doc.close()
    return img_path


# =========================
# 📄 DOCX → IMAGE
# =========================
def docx_to_image(docx_path):
    from docx import Document

    doc = Document(docx_path)
    text = "\n".join([p.text for p in doc.paragraphs])

    img = Image.new("RGB", (1000, 1400), "white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), text[:2000], fill="black")

    img_path = docx_path + ".jpg"
    img.save(img_path)
    return img_path


# =========================
# 🔍 pHASH
# =========================
def generate_phash(image_path):
    return str(imagehash.phash(Image.open(image_path)))


def phash_distance(h1, h2):
    return imagehash.hex_to_hash(h1) - imagehash.hex_to_hash(h2)


# =========================
# 🧠 DYNAMIC PROMPT
# =========================
def get_dynamic_prompt(dist):
    system_msg = "You are a certificate authentication expert. Analyze certificates carefully and respond ONLY with valid JSON."
    
    if dist <= 30:
        analysis = "High visual similarity to trusted templates (phash distance <= 3). Accept minor rendering variations. Focus on major forgery indicators."
    elif dist <= 70:
        analysis = "Moderate visual differences (phash distance 4-7). Carefully check logos, watermarks, seals, signatures, fonts, and layout for inconsistencies."
    else:
        # No close match or very different
        if dist >= 100:
            analysis = "No reference certificate in database. Perform standalone authenticity check based on visual features: logo quality, watermark patterns, seal embossing, signature shape, font consistency, and overall professional appearance."
        else:
            analysis = f"Significant visual differences from trusted templates (phash distance {dist}). Be thorough - check all security features carefully."
    
    user_msg = f"""
{analysis}

Examine the certificate image. Look for:
- Accurate institutional logos and branding
- Proper watermark patterns (not blurry or misplaced)
- Correct seal/embossing quality
- Valid signature format and placement
- Consistent fonts and text alignment
- No signs of digital manipulation (pixelation, inconsistent edges, mismatched colors)

Return ONLY JSON: {{"status":"REAL" or "FAKE","confidence":0.0-1.0}}
"""
    return system_msg, user_msg


# =========================
# 🤖 MISTRAL AI
# =========================
from QR_Based_Single_Scan_Resume_Verification import settings
def verify_certificate(image_path, prompt):
    # Try mkey1 first, fallback to mkey2
    api_key = settings.mkey1 if hasattr(settings, "mkey1") else getattr(settings, "mkey2", None)
    
    print(f"Using API key (first 10 chars): {api_key[:10] if api_key else 'None'}")

    if not api_key:
        print("WARNING: No API key configured")
        return "REAL", 0.5

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.mistral.ai/v1/"
        )

        with open(image_path, "rb") as img:
            img_bytes = img.read()

        img_base64 = base64.b64encode(img_bytes).decode()
        import mimetypes
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type is None:
            mime_type = "image/jpeg"
        image_data_url = f"data:{mime_type};base64,{img_base64}"

        system_msg, user_msg = prompt if isinstance(prompt, tuple) else ("", prompt)
        
        messages = []
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_msg+ "today's date: " + str(datetime.date.today())},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_url,
                        "detail": "high"
                    }
                }
            ]
        })

        response = client.chat.completions.create(
            model="pixtral-12b-latest",
            messages=messages,
            max_tokens=50,
            temperature=0.1
        )
        print("AI RAW RESPONSE:", response)
        raw = response.choices[0].message.content.strip()
        print("AI Raw content:", raw)
        raw = raw.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(raw)
            status = data.get("status", "FAKE")
            conf = float(data.get("confidence", 0.5))
            print(f"AI parsed: status={status}, conf={conf}")
            return status, conf
        except Exception as pe:
            print(f"JSON parse error: {pe}")
            if "REAL" in raw.upper():
                return "REAL", 0.7
            return "FAKE", 0.3

    except Exception as e:
        print("AI ERROR:", e)
        import traceback
        traceback.print_exc()
        return "FAKE", 0.0


# =========================
# 📤 MAIN FUNCTION
# =========================
def upload_certificate(request):
    from .models import Student, Certificate
    import os, uuid

    # ================= SESSION =================
    student_id = request.session.get("student_id") or request.POST.get("student_id")

    if not student_id:
        messages.error(request, "Please login first")
        return redirect("student_login")

    try:
        student = Student.objects.get(id=int(student_id))
    except:
        messages.error(request, "Invalid session")
        return redirect("student_login")

    if request.method != "POST":
        return redirect("upload_certificates_page", student_id=student.id)

    files = request.FILES.getlist("files")

    real_count = 0
    fake_count = 0

    for cert_file in files:
        print(f"\n=== Processing file: {cert_file.name} ===")
        ext = cert_file.name.lower()

        if not ext.endswith((".pdf", ".jpg", ".jpeg", ".png", ".docx")):
            continue

        try:
            # ================= TEMP SAVE =================
            temp_path = default_storage.save(f"temp/{cert_file.name}", cert_file)
            full_path = os.path.join(settings.MEDIA_ROOT, temp_path)

            # ================= CONVERT =================
            if ext.endswith(".pdf"):
                image_path = pdf_to_image(full_path)
            elif ext.endswith(".docx"):
                image_path = docx_to_image(full_path)
            else:
                image_path = full_path

            # ================= pHASH =================
            phash_value = generate_phash(image_path)

            min_dist = None
            existing_with_phash = Certificate.objects.exclude(phash__isnull=True)
            print(f"Existing certificates with phash: {existing_with_phash.count()}")
            
            for cert in existing_with_phash:
                d = phash_distance(phash_value, cert.phash)
                print(f"Comparing with cert {cert.id}: distance={d}")
                if min_dist is None or d < min_dist:
                    min_dist = d

            if min_dist is None:
                min_dist = 100  # Default when no reference exists
                print("No existing phash references, using default distance=100")
            
            print(f"pHASH comparison: final min_dist={min_dist}")

            # ================= PROMPT =================
            prompt = get_dynamic_prompt(min_dist)

            # ================= AI =================
            ai_status, ai_conf = verify_certificate(image_path, prompt)

            print("DIST:", min_dist, "AI:", ai_status, ai_conf)

            # ================= FINAL =================
            # Adaptive threshold: lower for new certificates (no similar in DB)
            threshold = 0.6 if min_dist >= 100 else 0.7
            
            if ai_status == "REAL" and ai_conf >= threshold:

                filename = f"{cert_file.name}"
                new_path = f"certificates/{filename}"

                with open(full_path, "rb") as f:
                    saved_path = default_storage.save(new_path, f)

                if os.path.exists(full_path):
                    os.remove(full_path)

                Certificate.objects.create(
                    student=student,
                    file=saved_path,
                    phash=phash_value,
                    verification_status="REAL",
                    confidence=ai_conf,
                )

                real_count += 1

            else:
                if os.path.exists(full_path):
                    os.remove(full_path)

                fake_count += 1

        except Exception as e:
            print("ERROR:", e)
            fake_count += 1

    messages.success(request, f"REAL: {real_count} | FAKE: {fake_count}")
    return redirect("upload_certificates_page", student_id=student.id)

def resume_view(request, resume_id):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("student_login")

    try:
        resume = Resume.objects.get(id=resume_id, student_id=student_id)
        return render(request, "Student/resume_view.html", {"resume": resume})
    except Resume.DoesNotExist:
        messages.error(request, "Resume not found")
        return redirect("student_dashboard")


def public_resume_view(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
        return render(request, "Student/public_resume_view.html", {"resume": resume})
    except Resume.DoesNotExist:
        return render(request, "error.html", {"message": "Resume not found"})


# QR-1: Certificate Upload Page (accessed via Resume QR)
def upload_certificates_page(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        certificates = Certificate.objects.filter(student=student).order_by(
            "-created_at"
        )

        context = {
            "student": student,
            "certificates": certificates,
        }
        return render(request, "Student/upload_certificates.html", context)
    except Student.DoesNotExist:
        return redirect("student_login")


# QR-2: Certificate View Page (for recruiter via embedded QR in resume)
def view_certificates_page(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
        certificates = Certificate.objects.filter(
            student=student, verification_status="REAL"
        )

        context = {
            "student": student,
            "certificates": certificates,
        }
        return render(request, "Student/view_certificates.html", context)
    except Student.DoesNotExist:
        return render(request, "error.html", {"message": "Student not found"})


def delete_student_data(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("student_login")

    if request.method == "POST":
        try:
            student = Student.objects.get(id=student_id)

            for resume in Resume.objects.filter(student=student):
                if resume.file:
                    resume.file.delete()
                if resume.qr_upload:
                    resume.qr_upload.delete()
                if resume.qr_resume:
                    resume.qr_resume.delete()
                if resume.qr_certificates:
                    resume.qr_certificates.delete()
                resume.delete()

            for certificate in Certificate.objects.filter(student=student):
                if certificate.file:
                    certificate.file.delete()
                certificate.delete()

            messages.success(
                request, "All your data (resume and certificates) has been deleted."
            )
        except Student.DoesNotExist:
            messages.error(request, "Student not found")

    return redirect("student_dashboard")
