# 🎓 MONTFORT SENIOR SECONDARY SCHOOL Management System

A full-featured **School ERP + Public Website** built with **Flask + Excel (openpyxl)** for data storage, and **HTML/CSS/JS** for the frontend.

---

## 🏫 Features

### Public Website
- Home page with announcements & events
- About Us, Academics, Admissions, Facilities, Events, Gallery, Contact pages
- Online admission application form
- Contact form with message storage

### School ERP (4 Role Dashboards)

| Role | Features |
|------|----------|
| **Admin** | Full system control — students, teachers, classes, subjects, attendance, exams, marks, fees, library, transport, gallery, announcements, events, admissions |
| **Teacher** | Mark attendance, enter marks, create assignments, view students |
| **Student** | View timetable, attendance, results, assignments, fee status |
| **Parent** | Monitor child's attendance, results, fees, announcements |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip

### Installation

```bash
# 1. Navigate to project folder
cd school_management

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python run.py
```

Then open: https://school-management-modernized.onrender.com/

---

## 🔑 Default Login Credentials

| Role    | Username  | Password     |
|---------|-----------|--------------|
| Admin   | admin     | admin123     |
| Teacher | teacher1  | teacher123   |
| Student | student1  | student123   |
| Parent  | parent1   | parent123    |

---

## 📁 Project Structure

```
school_management/
├── app.py                  # Main Flask application (all routes)
├── run.py                  # Setup + run script
├── requirements.txt        # Python dependencies
├── README.md
├── data/                   # Excel files (auto-created)
│   ├── users.xlsx
│   ├── students.xlsx
│   ├── teachers.xlsx
│   ├── classes.xlsx
│   ├── subjects.xlsx
│   ├── attendance.xlsx
│   ├── exams.xlsx
│   ├── marks.xlsx
│   ├── fees.xlsx
│   ├── announcements.xlsx
│   ├── events.xlsx
│   ├── library_books.xlsx
│   ├── issued_books.xlsx
│   ├── transport.xlsx
│   ├── gallery.xlsx
│   ├── timetable.xlsx
│   ├── assignments.xlsx
│   ├── submissions.xlsx
│   ├── admissions.xlsx
│   └── contact_msgs.xlsx
├── static/
│   └── uploads/            # Uploaded files
├── templates/
│   ├── base.html           # Public website base
│   ├── dashboard_base.html # ERP dashboard base
│   ├── index.html          # Home page
│   ├── about.html
│   ├── academics.html
│   ├── admissions.html
│   ├── facilities.html
│   ├── events.html
│   ├── gallery.html
│   ├── contact.html
│   ├── login.html
│   ├── profile.html
│   ├── admin/              # Admin dashboard pages
│   ├── teacher/            # Teacher dashboard pages
│   ├── student/            # Student dashboard pages
│   └── parent/             # Parent dashboard pages
└── utils/
    └── excel_helper.py     # Excel CRUD operations
```

---

## 📊 Data Storage

All data is stored in **Excel (.xlsx) files** using `openpyxl`. No database server required! Files are auto-created in the `data/` folder on first run.

### Excel Sheets
- `users.xlsx` — Login credentials & roles
- `students.xlsx` — Student records
- `teachers.xlsx` — Teacher records
- `classes.xlsx` — Class & section info
- `subjects.xlsx` — Subject catalog
- `attendance.xlsx` — Daily attendance
- `exams.xlsx` — Exam definitions
- `marks.xlsx` — Student marks
- `fees.xlsx` — Fee records
- `announcements.xlsx` — School notices
- `events.xlsx` — School events
- `library_books.xlsx` — Book catalog
- `issued_books.xlsx` — Book issue/return
- `transport.xlsx` — Bus routes
- `gallery.xlsx` — Photo gallery
- `timetable.xlsx` — Class timetable
- `assignments.xlsx` — Teacher assignments
- `admissions.xlsx` — Application forms
- `contact_msgs.xlsx` — Contact form messages

---

## 🔐 Security
- Passwords hashed with **bcrypt** (Werkzeug)
- Session-based authentication
- Role-based access control (RBAC)
- Protected routes for each role

---

## 📱 Responsive Design
- Mobile-first responsive layout
- Works on desktop, tablet, and mobile
- Collapsible sidebar navigation

---

## 🎨 Tech Stack
- **Backend**: Flask (Python)
- **Data Storage**: Excel (.xlsx) via openpyxl
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Icons**: Font Awesome 6
- **Charts**: Chart.js
- **Security**: Werkzeug password hashing

---

## 📝 Adding New Users

Login as admin and use the **Students** or **Teachers** section to add users. Each added student/teacher automatically gets a login account.

---

*Built with ❤️ for MONTFORT SENIOR SECONDARY SCHOOL*
