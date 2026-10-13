# QR-Based Resume and Certificate Verification System

A full-stack web application using Django (backend) and HTML, CSS, JavaScript (frontend) for verifying student resumes and certificates using QR codes and image processing.

## Features

### Student Module
- **Registration**: Custom authentication (no Django User model)
- **Login/Logout**: Session-based authentication
- **Resume Handling**: Upload PDF/DOCX or generate ATS-optimized resume
- **QR Code Generation**: Unique QR codes for each resume
- **Certificate Upload**: Upload certificates (PDF/Image)
- **Certificate Verification**: Image processing with OpenCV for fake detection
- **Storage Rule**: Only REAL certificates are stored

### Recruiter Module
- **Login**: Hardcoded credentials (recruiter/recruiter)
- **Search**: Find students by name, email, or roll number
- **Resume Access**: View and download student resumes
- **Certificate Access**: View and download verified (REAL) certificates

## Tech Stack
- **Backend**: Django 5.x (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **Libraries**: qrcode, Pillow, OpenCV, reportlab

## Setup Instructions

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run Migrations**:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Create Superuser (Optional)**:
```bash
python manage.py createsuperuser
```

4. **Run Server**:
```bash
python manage.py runserver
```

5. **Access Application**:
- Home: http://127.0.0.1:8000/
- Student Register: http://127.0.0.1:8000/student/register/
- Student Login: http://127.0.0.1:8000/student/login/
- Recruiter Login: http://127.0.0.1:8000/recruiter/login/
- Admin Panel: http://127.0.0.1:8000/admin/

## Recruiter Credentials
- Username: `recruiter`
- Password: `recruiter`

## Project Structure
```
QR_Based_Single_Scan_Resume_Verification/
├── Student/               # Student app
│   ├── models.py         # Student, Resume, Certificate models
│   ├── views.py          # All student views
│   ├── admin.py          # Admin configuration
├── Recruiter/            # Recruiter app
│   ├── views.py          # All recruiter views
├── Templates/            # HTML templates
│   ├── index.html
│   ├── studentRegister.html
│   ├── studentLogin.html
│   ├── recruiterLogin.html
│   ├── Student/
│   └── Recruiter/
├── media/                # Uploaded files
└── manage.py
```

## Security Features
- Custom password hashing (SHA-256)
- Session-based authentication
- Role-based access control
- File validation

## Certificate Verification
Uses OpenCV-based image processing:
- Laplacian variance for image quality detection
- Canny edge detection for pattern analysis
- Resolution check for tampered images

## Note
This system uses custom-built authentication (not Django's default User model) for simplified role-based control as per project requirements.