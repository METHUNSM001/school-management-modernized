from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os, json
from datetime import datetime, timedelta
import sys
sys.path.insert(0, os.path.dirname(__file__))
from utils.excel_helper import *

app = Flask(__name__)
app.secret_key = 'school_mgmt_secret_2024'
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif','pdf','doc','docx','xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

def dashboard():
    role = session.get('role')
    if role == 'admin': return redirect(url_for('admin_dashboard'))
    if role == 'teacher': return redirect(url_for('teacher_dashboard'))
    if role == 'student': return redirect(url_for('student_dashboard'))
    if role == 'parent': return redirect(url_for('parent_dashboard'))
    return redirect(url_for('login'))

app.add_url_rule('/dashboard', 'dashboard', login_required(dashboard))

# ─── PUBLIC PAGES ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    events = read_all('events')[-3:]
    announcements = read_where('announcements', is_active=1)[-5:]
    return render_template('index.html', events=events, announcements=announcements)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/academics')
def academics():
    return render_template('academics.html')

@app.route('/admissions', methods=['GET','POST'])
def admissions():
    if request.method == 'POST':
        rid = next_id('admissions')
        data = {
            'id': rid,
            'applicant_name': request.form.get('applicant_name',''),
            'dob': request.form.get('dob',''),
            'gender': request.form.get('gender',''),
            'class_applying': request.form.get('class_applying',''),
            'parent_name': request.form.get('parent_name',''),
            'parent_phone': request.form.get('parent_phone',''),
            'email': request.form.get('email',''),
            'address': request.form.get('address',''),
            'prev_school': request.form.get('prev_school',''),
            'status': 'pending',
            'applied_date': datetime.now().strftime('%Y-%m-%d')
        }
        insert('admissions', data)
        flash(f'Application submitted! Your Application ID is ADM{rid:04d}. We will contact you soon.', 'success')
        return redirect(url_for('admissions'))
    return render_template('admissions.html')

@app.route('/facilities')
def facilities():
    return render_template('facilities.html')

@app.route('/events')
def events():
    all_events = read_all('events')
    return render_template('events.html', events=all_events)

@app.route('/gallery')
def gallery():
    items = read_all('gallery')
    return render_template('gallery.html', items=items)

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        rid = next_id('contact_msgs')
        data = {
            'id': rid,
            'name': request.form.get('name',''),
            'email': request.form.get('email',''),
            'phone': request.form.get('phone',''),
            'subject': request.form.get('subject',''),
            'message': request.form.get('message',''),
            'received_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'is_read': 0
        }
        insert('contact_msgs', data)
        flash('Thank you! Your message has been received. We will respond within 24 hours.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

# ─── AUTH ──────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        users = read_where('users', username=username)
        if users:
            u = users[0]
            if check_password_hash(str(u['password']), password) and u.get('status') == 'active':
                session['user_id'] = u['id']
                session['username'] = u['username']
                session['role'] = u['role']
                session['name'] = u['name']
                session['email'] = u.get('email','')
                flash(f'Welcome back, {u["name"]}!', 'success')
                return redirect(url_for('dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ─── ADMIN ─────────────────────────────────────────────────────────────────────

@app.route('/admin')
@role_required('admin')
def admin_dashboard():
    stats = {
        'students': count('students'),
        'teachers': count('teachers'),
        'classes': count('classes'),
        'announcements': count('announcements'),
        'events': count('events'),
        'fees_pending': len(read_where('fees', status='pending')),
        'fees_paid': len(read_where('fees', status='paid')),
        'library_books': count('library_books'),
    }
    announcements = read_all('announcements')[-5:]
    events = read_all('events')[-3:]
    recent_students = read_all('students')[-5:]
    return render_template('admin/dashboard.html', stats=stats, announcements=announcements,
                           events=events, recent_students=recent_students)

# STUDENTS
@app.route('/admin/students')
@role_required('admin')
def admin_students():
    students = read_all('students')
    classes = read_all('classes')
    classes_map = {str(c['id']): c['name'] for c in classes}
    return render_template('admin/students.html', students=students, classes=classes, classes_map=classes_map)

@app.route('/admin/students/add', methods=['GET','POST'])
@role_required('admin')
def admin_add_student():
    classes = read_all('classes')
    if request.method == 'POST':
        f = request.form
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Create user
        uid = next_id('users')
        insert('users', {'id':uid,'username':f.get('username'),'password':generate_password_hash(f.get('password','student123')),
                          'role':'student','name':f.get('name'),'email':f.get('email',''),
                          'phone':f.get('parent_phone',''),'status':'active','created_at':now})
        sid = next_id('students')
        insert('students', {
            'id':sid,'user_id':uid,'name':f.get('name'),'roll_no':f.get('roll_no'),
            'class_id':f.get('class_id'),'section':f.get('section'),
            'dob':f.get('dob'),'gender':f.get('gender'),'address':f.get('address'),
            'parent_name':f.get('parent_name'),'parent_phone':f.get('parent_phone'),
            'parent_email':f.get('parent_email'),'admission_date':f.get('admission_date',''),
            'photo':'','status':'active'
        })
        flash('Student added successfully!', 'success')
        return redirect(url_for('admin_students'))
    return render_template('admin/add_student.html', classes=classes)

@app.route('/admin/students/edit/<int:sid>', methods=['GET','POST'])
@role_required('admin')
def admin_edit_student(sid):
    student = read_by_id('students', sid)
    classes = read_all('classes')
    if request.method == 'POST':
        f = request.form
        update('students', sid, {
            'name':f.get('name'),'roll_no':f.get('roll_no'),'class_id':f.get('class_id'),
            'section':f.get('section'),'dob':f.get('dob'),'gender':f.get('gender'),
            'address':f.get('address'),'parent_name':f.get('parent_name'),
            'parent_phone':f.get('parent_phone'),'parent_email':f.get('parent_email')
        })
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin_students'))
    return render_template('admin/add_student.html', student=student, classes=classes, edit=True)

@app.route('/admin/students/delete/<int:sid>', methods=['POST'])
@role_required('admin')
def admin_delete_student(sid):
    delete('students', sid)
    flash('Student deleted.', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/students/view/<int:sid>')
@role_required('admin')
def admin_view_student(sid):
    student = read_by_id('students', sid)
    classes = read_all('classes')
    classes_map = {str(c['id']): c['name'] for c in classes}
    fees = read_where('fees', student_id=sid)
    attendance = read_where('attendance', student_id=sid)
    marks_list = read_where('marks', student_id=sid)
    exams = read_all('exams')
    exams_map = {str(e['id']): e for e in exams}
    subjects = read_all('subjects')
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    return render_template('admin/view_student.html', student=student, classes_map=classes_map,
                           fees=fees, attendance=attendance, marks_list=marks_list,
                           exams_map=exams_map, subjects_map=subjects_map)

# TEACHERS
@app.route('/admin/teachers')
@role_required('admin')
def admin_teachers():
    teachers = read_all('teachers')
    return render_template('admin/teachers.html', teachers=teachers)

@app.route('/admin/teachers/add', methods=['GET','POST'])
@role_required('admin')
def admin_add_teacher():
    subjects = read_all('subjects')
    if request.method == 'POST':
        f = request.form
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        uid = next_id('users')
        insert('users', {'id':uid,'username':f.get('username'),'password':generate_password_hash(f.get('password','teacher123')),
                          'role':'teacher','name':f.get('name'),'email':f.get('email',''),
                          'phone':f.get('phone',''),'status':'active','created_at':now})
        tid = next_id('teachers')
        insert('teachers', {
            'id':tid,'user_id':uid,'name':f.get('name'),'employee_id':f.get('employee_id'),
            'subject':f.get('subject'),'qualification':f.get('qualification'),
            'phone':f.get('phone'),'email':f.get('email'),'address':f.get('address'),
            'joining_date':f.get('joining_date',''),'salary':f.get('salary',0),
            'photo':'','status':'active'
        })
        flash('Teacher added successfully!', 'success')
        return redirect(url_for('admin_teachers'))
    return render_template('admin/add_teacher.html', subjects=subjects)

@app.route('/admin/teachers/edit/<int:tid>', methods=['GET','POST'])
@role_required('admin')
def admin_edit_teacher(tid):
    teacher = read_by_id('teachers', tid)
    if request.method == 'POST':
        f = request.form
        update('teachers', tid, {
            'name':f.get('name'),'employee_id':f.get('employee_id'),'subject':f.get('subject'),
            'qualification':f.get('qualification'),'phone':f.get('phone'),'email':f.get('email'),
            'address':f.get('address'),'salary':f.get('salary',0)
        })
        flash('Teacher updated!', 'success')
        return redirect(url_for('admin_teachers'))
    return render_template('admin/add_teacher.html', teacher=teacher, edit=True)

@app.route('/admin/teachers/delete/<int:tid>', methods=['POST'])
@role_required('admin')
def admin_delete_teacher(tid):
    delete('teachers', tid)
    flash('Teacher deleted.', 'success')
    return redirect(url_for('admin_teachers'))

# CLASSES
@app.route('/admin/classes')
@role_required('admin')
def admin_classes():
    classes = read_all('classes')
    teachers = read_all('teachers')
    teachers_map = {str(t['id']): t['name'] for t in teachers}
    return render_template('admin/classes.html', classes=classes, teachers=teachers, teachers_map=teachers_map)

@app.route('/admin/classes/add', methods=['POST'])
@role_required('admin')
def admin_add_class():
    f = request.form
    cid = next_id('classes')
    insert('classes', {'id':cid,'name':f.get('name'),'section':f.get('section'),
                        'teacher_id':f.get('teacher_id',''),'capacity':f.get('capacity',40),
                        'academic_year':f.get('academic_year','2024-25')})
    flash('Class added!', 'success')
    return redirect(url_for('admin_classes'))

@app.route('/admin/classes/delete/<int:cid>', methods=['POST'])
@role_required('admin')
def admin_delete_class(cid):
    delete('classes', cid)
    flash('Class deleted.', 'success')
    return redirect(url_for('admin_classes'))

# SUBJECTS
@app.route('/admin/subjects')
@role_required('admin')
def admin_subjects():
    subjects = read_all('subjects')
    classes = read_all('classes')
    teachers = read_all('teachers')
    classes_map = {str(c['id']): c['name'] for c in classes}
    teachers_map = {str(t['id']): t['name'] for t in teachers}
    return render_template('admin/subjects.html', subjects=subjects, classes=classes,
                           teachers=teachers, classes_map=classes_map, teachers_map=teachers_map)

@app.route('/admin/subjects/add', methods=['POST'])
@role_required('admin')
def admin_add_subject():
    f = request.form
    sid = next_id('subjects')
    insert('subjects', {'id':sid,'name':f.get('name'),'code':f.get('code'),
                         'class_id':f.get('class_id'),'teacher_id':f.get('teacher_id',''),
                         'max_marks':f.get('max_marks',100)})
    flash('Subject added!', 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/subjects/delete/<int:sid>', methods=['POST'])
@role_required('admin')
def admin_delete_subject(sid):
    delete('subjects', sid)
    flash('Subject deleted.', 'success')
    return redirect(url_for('admin_subjects'))

# ATTENDANCE
@app.route('/admin/attendance')
@role_required('admin')
def admin_attendance():
    classes = read_all('classes')
    selected_class = request.args.get('class_id','')
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    students = []
    attendance_map = {}
    if selected_class:
        students = read_where('students', class_id=selected_class)
        att = read_where('attendance', class_id=selected_class, date=selected_date)
        attendance_map = {str(a['student_id']): a['status'] for a in att}
    return render_template('admin/attendance.html', classes=classes, students=students,
                           attendance_map=attendance_map, selected_class=selected_class,
                           selected_date=selected_date)

@app.route('/admin/attendance/save', methods=['POST'])
@role_required('admin')
def admin_save_attendance():
    class_id = request.form.get('class_id')
    date = request.form.get('date')
    student_ids = request.form.getlist('student_ids')
    statuses = request.form.getlist('statuses')
    # Delete existing
    existing = read_where('attendance', class_id=class_id, date=date)
    for e in existing:
        delete('attendance', e['id'])
    # Insert new
    for i, (sid, status) in enumerate(zip(student_ids, statuses)):
        aid = next_id('attendance')
        insert('attendance', {'id':aid,'student_id':sid,'class_id':class_id,
                               'date':date,'status':status,'marked_by':session['user_id']})
    flash(f'Attendance saved for {date}!', 'success')
    return redirect(url_for('admin_attendance', class_id=class_id, date=date))

# EXAMS
@app.route('/admin/exams')
@role_required('admin')
def admin_exams():
    exams = read_all('exams')
    classes = read_all('classes')
    subjects = read_all('subjects')
    classes_map = {str(c['id']): c['name'] for c in classes}
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    return render_template('admin/exams.html', exams=exams, classes=classes,
                           subjects=subjects, classes_map=classes_map, subjects_map=subjects_map)

@app.route('/admin/exams/add', methods=['POST'])
@role_required('admin')
def admin_add_exam():
    f = request.form
    eid = next_id('exams')
    insert('exams', {'id':eid,'name':f.get('name'),'class_id':f.get('class_id'),
                      'subject_id':f.get('subject_id'),'exam_date':f.get('exam_date'),
                      'max_marks':f.get('max_marks',100),'passing_marks':f.get('passing_marks',35),
                      'created_by':session['user_id']})
    flash('Exam created!', 'success')
    return redirect(url_for('admin_exams'))

@app.route('/admin/exams/delete/<int:eid>', methods=['POST'])
@role_required('admin')
def admin_delete_exam(eid):
    delete('exams', eid)
    flash('Exam deleted.', 'success')
    return redirect(url_for('admin_exams'))

@app.route('/admin/marks/<int:eid>', methods=['GET','POST'])
@role_required('admin')
def admin_marks(eid):
    exam = read_by_id('exams', eid)
    students = read_where('students', class_id=str(exam['class_id']))
    marks = read_where('marks', exam_id=eid)
    marks_map = {str(m['student_id']): m for m in marks}
    subjects = read_all('subjects')
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids')
        marks_list = request.form.getlist('marks')
        remarks_list = request.form.getlist('remarks')
        for sid, m, rem in zip(student_ids, marks_list, remarks_list):
            try: mo = float(m)
            except: mo = 0
            max_m = float(exam.get('max_marks', 100))
            pct = (mo/max_m)*100 if max_m else 0
            grade = 'A+' if pct>=90 else 'A' if pct>=80 else 'B+' if pct>=70 else 'B' if pct>=60 else 'C' if pct>=50 else 'D' if pct>=35 else 'F'
            existing = read_where('marks', exam_id=eid, student_id=int(sid))
            if existing:
                update('marks', existing[0]['id'], {'marks_obtained':mo,'grade':grade,'remarks':rem})
            else:
                mid = next_id('marks')
                insert('marks', {'id':mid,'exam_id':eid,'student_id':int(sid),
                                  'marks_obtained':mo,'grade':grade,'remarks':rem})
        flash('Marks saved!', 'success')
        return redirect(url_for('admin_marks', eid=eid))
    return render_template('admin/marks.html', exam=exam, students=students,
                           marks_map=marks_map, subjects_map=subjects_map)

# FEES
@app.route('/admin/fees')
@role_required('admin')
def admin_fees():
    fees = read_all('fees')
    students = read_all('students')
    students_map = {str(s['id']): s['name'] for s in students}
    return render_template('admin/fees.html', fees=fees, students=students, students_map=students_map)

@app.route('/admin/fees/add', methods=['POST'])
@role_required('admin')
def admin_add_fee():
    f = request.form
    fid = next_id('fees')
    insert('fees', {'id':fid,'student_id':f.get('student_id'),'fee_type':f.get('fee_type'),
                     'amount':f.get('amount'),'due_date':f.get('due_date'),
                     'status':'pending','paid_date':'','receipt_no':'',
                     'academic_year':f.get('academic_year','2024-25')})
    flash('Fee record added!', 'success')
    return redirect(url_for('admin_fees'))

@app.route('/admin/fees/pay/<int:fid>', methods=['POST'])
@role_required('admin')
def admin_pay_fee(fid):
    fee = read_by_id('fees', fid)
    rno = f"RCP{fid:04d}"
    update('fees', fid, {'status':'paid','paid_date':datetime.now().strftime('%Y-%m-%d'),'receipt_no':rno})
    flash(f'Payment recorded. Receipt: {rno}', 'success')
    return redirect(url_for('admin_fees'))

@app.route('/admin/fees/delete/<int:fid>', methods=['POST'])
@role_required('admin')
def admin_delete_fee(fid):
    delete('fees', fid)
    flash('Fee record deleted.', 'success')
    return redirect(url_for('admin_fees'))

# ANNOUNCEMENTS
@app.route('/admin/announcements')
@role_required('admin')
def admin_announcements():
    announcements = read_all('announcements')
    return render_template('admin/announcements.html', announcements=announcements)

@app.route('/admin/announcements/add', methods=['POST'])
@role_required('admin')
def admin_add_announcement():
    f = request.form
    aid = next_id('announcements')
    insert('announcements', {'id':aid,'title':f.get('title'),'content':f.get('content'),
                              'target_role':f.get('target_role','all'),
                              'created_by':session['user_id'],
                              'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'is_active':1})
    flash('Announcement published!', 'success')
    return redirect(url_for('admin_announcements'))

@app.route('/admin/announcements/delete/<int:aid>', methods=['POST'])
@role_required('admin')
def admin_delete_announcement(aid):
    delete('announcements', aid)
    flash('Announcement deleted.', 'success')
    return redirect(url_for('admin_announcements'))

# EVENTS
@app.route('/admin/events')
@role_required('admin')
def admin_events():
    events = read_all('events')
    return render_template('admin/events.html', events=events)

@app.route('/admin/events/add', methods=['POST'])
@role_required('admin')
def admin_add_event():
    f = request.form
    eid = next_id('events')
    photo = ''
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"event_{eid}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo = filename
    insert('events', {'id':eid,'title':f.get('title'),'description':f.get('description'),
                       'event_date':f.get('event_date'),'location':f.get('location',''),
                       'photo':photo,'created_by':session['user_id'],
                       'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    flash('Event added!', 'success')
    return redirect(url_for('admin_events'))

@app.route('/admin/events/delete/<int:eid>', methods=['POST'])
@role_required('admin')
def admin_delete_event(eid):
    delete('events', eid)
    flash('Event deleted.', 'success')
    return redirect(url_for('admin_events'))

# LIBRARY
@app.route('/admin/library')
@role_required('admin')
def admin_library():
    books = read_all('library_books')
    issued = read_all('issued_books')
    students = read_all('students')
    students_map = {str(s['id']): s['name'] for s in students}
    books_map = {str(b['id']): b['title'] for b in books}
    return render_template('admin/library.html', books=books, issued=issued,
                           students=students, students_map=students_map, books_map=books_map)

@app.route('/admin/library/add', methods=['POST'])
@role_required('admin')
def admin_add_book():
    f = request.form
    bid = next_id('library_books')
    copies = int(f.get('copies',1))
    insert('library_books', {'id':bid,'title':f.get('title'),'author':f.get('author'),
                              'isbn':f.get('isbn',''),'category':f.get('category','General'),
                              'copies':copies,'available':copies,'added_date':datetime.now().strftime('%Y-%m-%d')})
    flash('Book added!', 'success')
    return redirect(url_for('admin_library'))

@app.route('/admin/library/issue', methods=['POST'])
@role_required('admin')
def admin_issue_book():
    f = request.form
    book_id = int(f.get('book_id'))
    student_id = f.get('student_id')
    book = read_by_id('library_books', book_id)
    avail = int(book.get('available',0)) if book else 0
    if avail < 1:
        flash('No copies available!', 'danger')
        return redirect(url_for('admin_library'))
    iid = next_id('issued_books')
    issue_date = datetime.now().strftime('%Y-%m-%d')
    due = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    insert('issued_books', {'id':iid,'book_id':book_id,'student_id':student_id,
                             'issue_date':issue_date,'due_date':due,'return_date':'','fine':0})
    update('library_books', book_id, {'available': avail-1})
    flash('Book issued!', 'success')
    return redirect(url_for('admin_library'))

@app.route('/admin/library/return/<int:iid>', methods=['POST'])
@role_required('admin')
def admin_return_book(iid):
    issued = read_by_id('issued_books', iid)
    return_date = datetime.now().strftime('%Y-%m-%d')
    due = datetime.strptime(str(issued.get('due_date',return_date)), '%Y-%m-%d')
    today = datetime.now()
    fine = max(0, (today - due).days * 2) if today > due else 0
    update('issued_books', iid, {'return_date':return_date,'fine':fine})
    book_id = issued.get('book_id')
    book = read_by_id('library_books', book_id)
    if book:
        update('library_books', book_id, {'available': int(book.get('available',0))+1})
    flash(f'Book returned! Fine: ₹{fine}', 'success')
    return redirect(url_for('admin_library'))

@app.route('/admin/library/delete/<int:bid>', methods=['POST'])
@role_required('admin')
def admin_delete_book(bid):
    delete('library_books', bid)
    flash('Book deleted.', 'success')
    return redirect(url_for('admin_library'))

# TRANSPORT
@app.route('/admin/transport')
@role_required('admin')
def admin_transport():
    routes = read_all('transport')
    return render_template('admin/transport.html', routes=routes)

@app.route('/admin/transport/add', methods=['POST'])
@role_required('admin')
def admin_add_transport():
    f = request.form
    tid = next_id('transport')
    insert('transport', {'id':tid,'route_name':f.get('route_name'),'vehicle_no':f.get('vehicle_no'),
                          'driver_name':f.get('driver_name'),'driver_phone':f.get('driver_phone'),
                          'stops':f.get('stops',''),'students':''})
    flash('Route added!', 'success')
    return redirect(url_for('admin_transport'))

@app.route('/admin/transport/delete/<int:tid>', methods=['POST'])
@role_required('admin')
def admin_delete_transport(tid):
    delete('transport', tid)
    flash('Route deleted.', 'success')
    return redirect(url_for('admin_transport'))

# GALLERY ADMIN
@app.route('/admin/gallery')
@role_required('admin')
def admin_gallery():
    items = read_all('gallery')
    return render_template('admin/gallery.html', items=items)

@app.route('/admin/gallery/upload', methods=['POST'])
@role_required('admin')
def admin_upload_gallery():
    f = request.form
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        gid = next_id('gallery')
        filename = secure_filename(f"gallery_{gid}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        insert('gallery', {'id':gid,'title':f.get('title',''),'category':f.get('category','General'),
                            'file_path':filename,'uploaded_by':session['user_id'],
                            'uploaded_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        flash('Image uploaded!', 'success')
    else:
        flash('Invalid file type.', 'danger')
    return redirect(url_for('admin_gallery'))

@app.route('/admin/gallery/delete/<int:gid>', methods=['POST'])
@role_required('admin')
def admin_delete_gallery(gid):
    delete('gallery', gid)
    flash('Deleted.', 'success')
    return redirect(url_for('admin_gallery'))

# ADMISSIONS ADMIN
@app.route('/admin/admissions')
@role_required('admin')
def admin_admissions():
    apps = read_all('admissions')
    return render_template('admin/admissions_list.html', applications=apps)

@app.route('/admin/admissions/update/<int:aid>', methods=['POST'])
@role_required('admin')
def admin_update_admission(aid):
    status = request.form.get('status')
    update('admissions', aid, {'status': status})
    flash(f'Application status updated to {status}.', 'success')
    return redirect(url_for('admin_admissions'))

# CONTACT MESSAGES
@app.route('/admin/messages')
@role_required('admin')
def admin_messages():
    msgs = read_all('contact_msgs')
    return render_template('admin/messages.html', messages=msgs)

@app.route('/admin/messages/delete/<int:mid>', methods=['POST'])
@role_required('admin')
def admin_delete_message(mid):
    delete('contact_msgs', mid)
    flash('Message deleted.', 'success')
    return redirect(url_for('admin_messages'))

# ASSIGNMENTS ADMIN
@app.route('/admin/assignments')
@role_required('admin')
def admin_assignments():
    assignments = read_all('assignments')
    classes = read_all('classes')
    subjects = read_all('subjects')
    classes_map = {str(c['id']): c['name'] for c in classes}
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    return render_template('admin/assignments.html', assignments=assignments, classes=classes,
                           subjects=subjects, classes_map=classes_map, subjects_map=subjects_map)

@app.route('/admin/assignments/add', methods=['POST'])
@role_required('admin')
def admin_add_assignment():
    f = request.form
    aid = next_id('assignments')
    file_path = ''
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"assign_{aid}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = filename
    insert('assignments', {'id':aid,'title':f.get('title'),'description':f.get('description'),
                            'class_id':f.get('class_id'),'subject_id':f.get('subject_id'),
                            'teacher_id':session['user_id'],'due_date':f.get('due_date'),
                            'file_path':file_path,'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    flash('Assignment created!', 'success')
    return redirect(url_for('admin_assignments'))

@app.route('/admin/assignments/delete/<int:aid>', methods=['POST'])
@role_required('admin')
def admin_delete_assignment(aid):
    delete('assignments', aid)
    flash('Assignment deleted.', 'success')
    return redirect(url_for('admin_assignments'))

# TIMETABLE
@app.route('/admin/timetable')
@role_required('admin')
def admin_timetable():
    timetable = read_all('timetable')
    classes = read_all('classes')
    subjects = read_all('subjects')
    teachers = read_all('teachers')
    selected_class = request.args.get('class_id','')
    if selected_class:
        timetable = [t for t in timetable if str(t.get('class_id')) == selected_class]
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    teachers_map = {str(t['id']): t['name'] for t in teachers}
    return render_template('admin/timetable.html', timetable=timetable, classes=classes,
                           subjects=subjects, teachers=teachers, subjects_map=subjects_map,
                           teachers_map=teachers_map, selected_class=selected_class)

@app.route('/admin/timetable/add', methods=['POST'])
@role_required('admin')
def admin_add_timetable():
    f = request.form
    tid = next_id('timetable')
    insert('timetable', {'id':tid,'class_id':f.get('class_id'),'day':f.get('day'),
                          'period':f.get('period'),'subject_id':f.get('subject_id'),
                          'teacher_id':f.get('teacher_id'),'start_time':f.get('start_time'),
                          'end_time':f.get('end_time')})
    flash('Timetable entry added!', 'success')
    return redirect(url_for('admin_timetable', class_id=f.get('class_id')))

@app.route('/admin/timetable/delete/<int:tid>', methods=['POST'])
@role_required('admin')
def admin_delete_timetable(tid):
    delete('timetable', tid)
    flash('Entry deleted.', 'success')
    return redirect(url_for('admin_timetable'))

# ─── TEACHER ───────────────────────────────────────────────────────────────────

@app.route('/teacher')
@role_required('teacher')
def teacher_dashboard():
    teacher = read_where('teachers', user_id=session['user_id'])
    teacher = teacher[0] if teacher else {}
    announcements = read_all('announcements')[-5:]
    return render_template('teacher/dashboard.html', teacher=teacher, announcements=announcements)

@app.route('/teacher/attendance', methods=['GET','POST'])
@role_required('teacher')
def teacher_attendance():
    classes = read_all('classes')
    selected_class = request.args.get('class_id','')
    selected_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    students = []
    attendance_map = {}
    if selected_class:
        students = read_where('students', class_id=selected_class)
        att = read_where('attendance', class_id=selected_class, date=selected_date)
        attendance_map = {str(a['student_id']): a['status'] for a in att}
    if request.method == 'POST':
        class_id = request.form.get('class_id')
        date = request.form.get('date')
        student_ids = request.form.getlist('student_ids')
        statuses = request.form.getlist('statuses')
        existing = read_where('attendance', class_id=class_id, date=date)
        for e in existing: delete('attendance', e['id'])
        for sid, status in zip(student_ids, statuses):
            aid = next_id('attendance')
            insert('attendance', {'id':aid,'student_id':sid,'class_id':class_id,
                                   'date':date,'status':status,'marked_by':session['user_id']})
        flash(f'Attendance saved!', 'success')
        return redirect(url_for('teacher_attendance', class_id=class_id, date=date))
    return render_template('teacher/attendance.html', classes=classes, students=students,
                           attendance_map=attendance_map, selected_class=selected_class,
                           selected_date=selected_date)

@app.route('/teacher/marks', methods=['GET','POST'])
@role_required('teacher')
def teacher_marks():
    exams = read_all('exams')
    selected_exam = request.args.get('exam_id','')
    students = []
    marks_map = {}
    exam = None
    subjects = read_all('subjects')
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    if selected_exam:
        exam = read_by_id('exams', selected_exam)
        if exam:
            students = read_where('students', class_id=str(exam['class_id']))
            marks = read_where('marks', exam_id=int(selected_exam))
            marks_map = {str(m['student_id']): m for m in marks}
    if request.method == 'POST':
        exam_id = int(request.form.get('exam_id'))
        e = read_by_id('exams', exam_id)
        student_ids = request.form.getlist('student_ids')
        marks_list = request.form.getlist('marks')
        remarks_list = request.form.getlist('remarks')
        for sid, m, rem in zip(student_ids, marks_list, remarks_list):
            try: mo = float(m)
            except: mo = 0
            max_m = float(e.get('max_marks',100)) if e else 100
            pct = (mo/max_m)*100
            grade = 'A+' if pct>=90 else 'A' if pct>=80 else 'B+' if pct>=70 else 'B' if pct>=60 else 'C' if pct>=50 else 'D' if pct>=35 else 'F'
            existing = read_where('marks', exam_id=exam_id, student_id=int(sid))
            if existing:
                update('marks', existing[0]['id'], {'marks_obtained':mo,'grade':grade,'remarks':rem})
            else:
                mid = next_id('marks')
                insert('marks', {'id':mid,'exam_id':exam_id,'student_id':int(sid),'marks_obtained':mo,'grade':grade,'remarks':rem})
        flash('Marks saved!', 'success')
        return redirect(url_for('teacher_marks', exam_id=exam_id))
    return render_template('teacher/marks.html', exams=exams, selected_exam=selected_exam,
                           students=students, marks_map=marks_map, exam=exam, subjects_map=subjects_map)

@app.route('/teacher/assignments', methods=['GET','POST'])
@role_required('teacher')
def teacher_assignments():
    assignments = read_all('assignments')
    classes = read_all('classes')
    subjects = read_all('subjects')
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    classes_map = {str(c['id']): c['name'] for c in classes}
    if request.method == 'POST':
        f = request.form
        aid = next_id('assignments')
        file_path = ''
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"assign_{aid}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                file_path = filename
        insert('assignments', {'id':aid,'title':f.get('title'),'description':f.get('description'),
                                'class_id':f.get('class_id'),'subject_id':f.get('subject_id'),
                                'teacher_id':session['user_id'],'due_date':f.get('due_date'),
                                'file_path':file_path,'created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        flash('Assignment created!', 'success')
        return redirect(url_for('teacher_assignments'))
    return render_template('teacher/assignments.html', assignments=assignments,
                           classes=classes, subjects=subjects,
                           subjects_map=subjects_map, classes_map=classes_map)

@app.route('/teacher/students')
@role_required('teacher')
def teacher_students():
    classes = read_all('classes')
    selected_class = request.args.get('class_id','')
    students = []
    if selected_class:
        students = read_where('students', class_id=selected_class)
    return render_template('teacher/students.html', classes=classes, students=students,
                           selected_class=selected_class)

# ─── STUDENT ───────────────────────────────────────────────────────────────────

@app.route('/student')
@role_required('student')
def student_dashboard():
    students = read_where('students', user_id=session['user_id'])
    student = students[0] if students else {}
    fees = read_where('fees', student_id=str(student.get('id',''))) if student else []
    pending_fees = [f for f in fees if f.get('status') == 'pending']
    announcements = read_all('announcements')[-5:]
    return render_template('student/dashboard.html', student=student, fees=fees,
                           pending_fees=pending_fees, announcements=announcements)

@app.route('/student/results')
@role_required('student')
def student_results():
    students = read_where('students', user_id=session['user_id'])
    student = students[0] if students else {}
    marks = read_where('marks', student_id=str(student.get('id',''))) if student else []
    exams = read_all('exams')
    exams_map = {str(e['id']): e for e in exams}
    subjects = read_all('subjects')
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    return render_template('student/results.html', student=student, marks=marks,
                           exams_map=exams_map, subjects_map=subjects_map)

@app.route('/student/attendance')
@role_required('student')
def student_attendance():
    students = read_where('students', user_id=session['user_id'])
    student = students[0] if students else {}
    attendance = read_where('attendance', student_id=str(student.get('id',''))) if student else []
    present = len([a for a in attendance if a.get('status')=='present'])
    total = len(attendance)
    pct = round((present/total)*100, 1) if total else 0
    return render_template('student/attendance.html', student=student, attendance=attendance,
                           present=present, total=total, pct=pct)

@app.route('/student/fees')
@role_required('student')
def student_fees():
    students = read_where('students', user_id=session['user_id'])
    student = students[0] if students else {}
    fees = read_where('fees', student_id=str(student.get('id',''))) if student else []
    return render_template('student/fees.html', student=student, fees=fees)

@app.route('/student/assignments')
@role_required('student')
def student_assignments():
    students = read_where('students', user_id=session['user_id'])
    student = students[0] if students else {}
    class_id = str(student.get('class_id','')) if student else ''
    assignments = read_where('assignments', class_id=class_id) if class_id else []
    submissions = read_where('submissions', student_id=str(student.get('id',''))) if student else []
    submitted_ids = {str(s['assignment_id']) for s in submissions}
    subjects = read_all('subjects')
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    return render_template('student/assignments.html', assignments=assignments,
                           submitted_ids=submitted_ids, subjects_map=subjects_map)

@app.route('/student/assignments/submit/<int:aid>', methods=['POST'])
@role_required('student')
def student_submit_assignment(aid):
    students = read_where('students', user_id=session['user_id'])
    student = students[0] if students else {}
    file_path = ''
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename and allowed_file(file.filename):
            sid = next_id('submissions')
            filename = secure_filename(f"sub_{aid}_{student.get('id',0)}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_path = filename
    subid = next_id('submissions')
    insert('submissions', {'id':subid,'assignment_id':aid,'student_id':student.get('id',''),
                            'file_path':file_path,'submitted_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'marks':'','feedback':''})
    flash('Assignment submitted!', 'success')
    return redirect(url_for('student_assignments'))

@app.route('/student/timetable')
@role_required('student')
def student_timetable():
    students = read_where('students', user_id=session['user_id'])
    student = students[0] if students else {}
    class_id = str(student.get('class_id','')) if student else ''
    timetable = read_where('timetable', class_id=class_id) if class_id else []
    subjects = read_all('subjects')
    teachers = read_all('teachers')
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    teachers_map = {str(t['id']): t['name'] for t in teachers}
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
    tt_by_day = {d: sorted([t for t in timetable if t.get('day')==d], key=lambda x: x.get('period',0)) for d in days}
    return render_template('student/timetable.html', tt_by_day=tt_by_day, days=days,
                           subjects_map=subjects_map, teachers_map=teachers_map)

# ─── PARENT ────────────────────────────────────────────────────────────────────

@app.route('/parent')
@role_required('parent')
def parent_dashboard():
    # Find parent's children by parent_email matching user email
    user_email = session.get('email','')
    children = read_where('students', parent_email=user_email)
    if not children:
        # Try by user_id match  
        children = []
        for s in read_all('students'):
            if str(s.get('parent_phone','')) == session.get('phone',''):
                children.append(s)
    announcements = read_all('announcements')[-5:]
    return render_template('parent/dashboard.html', children=children, announcements=announcements)

@app.route('/parent/student/<int:sid>')
@role_required('parent')
def parent_student(sid):
    student = read_by_id('students', sid)
    fees = read_where('fees', student_id=sid)
    attendance = read_where('attendance', student_id=str(sid))
    present = len([a for a in attendance if a.get('status')=='present'])
    total = len(attendance)
    pct = round((present/total)*100, 1) if total else 0
    marks = read_where('marks', student_id=str(sid))
    exams = read_all('exams')
    exams_map = {str(e['id']): e for e in exams}
    subjects = read_all('subjects')
    subjects_map = {str(s['id']): s['name'] for s in subjects}
    classes = read_all('classes')
    classes_map = {str(c['id']): c['name'] for c in classes}
    return render_template('parent/student_view.html', student=student, fees=fees,
                           attendance=attendance, present=present, total=total, pct=pct,
                           marks=marks, exams_map=exams_map, subjects_map=subjects_map,
                           classes_map=classes_map)

# ─── API ────────────────────────────────────────────────────────────────────────

@app.route('/api/stats')
@role_required('admin')
def api_stats():
    att = read_all('attendance')
    fees = read_all('fees')
    present_count = len([a for a in att if a.get('status')=='present'])
    total_att = len(att)
    paid_fees = sum(float(f.get('amount',0)) for f in fees if f.get('status')=='paid')
    pending_fees = sum(float(f.get('amount',0)) for f in fees if f.get('status')=='pending')
    return jsonify({
        'students': count('students'),
        'teachers': count('teachers'),
        'classes': count('classes'),
        'attendance_pct': round((present_count/total_att)*100,1) if total_att else 0,
        'paid_fees': paid_fees,
        'pending_fees': pending_fees,
        'books': count('library_books'),
        'events': count('events')
    })

@app.route('/api/attendance_chart')
@role_required('admin')
def api_attendance_chart():
    att = read_all('attendance')
    from collections import Counter
    dates = [a.get('date','') for a in att if a.get('date')]
    cnt = Counter(dates)
    sorted_dates = sorted(cnt.keys())[-7:]
    return jsonify({'labels': sorted_dates, 'data': [cnt[d] for d in sorted_dates]})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─── PROFILE ───────────────────────────────────────────────────────────────────

@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    user = read_by_id('users', session['user_id'])
    if request.method == 'POST':
        f = request.form
        update_data = {'name': f.get('name'), 'email': f.get('email'), 'phone': f.get('phone')}
        if f.get('new_password'):
            if check_password_hash(str(user['password']), f.get('current_password','')):
                update_data['password'] = generate_password_hash(f.get('new_password'))
            else:
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('profile'))
        update('users', session['user_id'], update_data)
        session['name'] = f.get('name')
        flash('Profile updated!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    init_data()
    app.run(debug=True, port=5000)
