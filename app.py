import streamlit as st
from supabase import create_client, Client
import requests
import random
import datetime
import time

# ==========================================
# 1. CREDENTIALS & SETUP
# ==========================================
SUPABASE_URL = "https://agmqzzzbwemwgnmhdtoi.supabase.co"
SUPABASE_KEY = "sb_publishable_0Yuo20gJhB7867u0z22bqA_0EL6AsrI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

EMAILJS_PUBLIC_KEY = "ajmaE46JFsU00LSOW"
EMAILJS_SERVICE_ID = "service_kjx20ng"
EMAILJS_TEMPLATE_ID = "template_yh5wpdm"

# Configure the Streamlit page
st.set_page_config(page_title="CLG-PTR Portal", page_icon="🎓", layout="centered")

# ==========================================
# 2. SESSION STATE MANAGEMENT
# ==========================================
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'generated_otp' not in st.session_state:
    st.session_state.generated_otp = None
if 'pending_reg' not in st.session_state:
    st.session_state.pending_reg = {}

def navigate_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# ==========================================
# 3. PAGE: HOME / LANDING
# ==========================================
if st.session_state.page == 'home':
    st.title("🎓 College Web Portal")
    st.write("Welcome to the unified database system. Please select your portal to securely access your records.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Student Portal", use_container_width=True, type="primary"):
            navigate_to('student_login')
    with col2:
        if st.button("Teacher Portal", use_container_width=True):
            navigate_to('teacher_login')

# ==========================================
# 4. PAGE: STUDENT LOGIN
# ==========================================
elif st.session_state.page == 'student_login':
    st.subheader("Student Portal - Secure Login")
    
    usn_input = st.text_input("USN:")
    dob_input = st.date_input("Date of Birth (Password):", value=None, min_value=datetime.date(1990, 1, 1), format="DD/MM/YYYY")
    
    if st.button("View Dashboard", type="primary", use_container_width=True):
        if not usn_input or dob_input is None:
            st.error("Please enter both your USN and Date of Birth.")
        else:
            formatted_dob = dob_input.strftime("%d/%m/%Y")
            try:
                response = supabase.table('students').select('*').eq('USN', usn_input).eq('Password', formatted_dob).execute()
                if len(response.data) > 0:
                    st.session_state.user_data = response.data[0]
                    navigate_to('student_dashboard')
                else:
                    st.error("Login failed: Incorrect USN or DOB.")
            except Exception as e:
                st.error(f"Database error: {e}")
            
    st.markdown("---")
    st.write("New Admission?")
    if st.button("Register Here", use_container_width=True):
        navigate_to('student_register')
        
    if st.button("← Back to Home"):
        navigate_to('home')

# ==========================================
# 5. PAGE: STUDENT REGISTRATION (OTP FLOW)
# ==========================================
elif st.session_state.page == 'student_register':
    st.subheader("CLG-PTR Admission")
    st.write("Enter your details. We will email you a secure OTP.")
    
    reg_email = st.text_input("Valid Email Address:")
    reg_dob = st.date_input("Date of Birth (This will act as your password):", value=None, min_value=datetime.date(1990, 1, 1), format="DD/MM/YYYY")
    
    if st.button("Send Secure OTP", type="primary", use_container_width=True):
        if not reg_email or reg_dob is None:
            st.error("Please enter a valid email and select your Date of Birth.")
        else:
            otp = str(random.randint(100000, 999999))
            st.session_state.generated_otp = otp
            st.session_state.pending_reg = {
                "email": reg_email,
                "dob": reg_dob.strftime("%d/%m/%Y")
            }
            
            payload = {
                "service_id": EMAILJS_SERVICE_ID,
                "template_id": EMAILJS_TEMPLATE_ID,
                "user_id": EMAILJS_PUBLIC_KEY,
                "template_params": {
                    "user_email": reg_email,
                    "otp_code": otp
                }
            }
            try:
                res = requests.post("https://api.emailjs.com/api/v1.0/email/send", json=payload)
                if res.status_code == 200:
                    navigate_to('verify_otp')
                else:
                    st.error("Failed to send email. Please check EmailJS configuration.")
            except Exception as e:
                st.error(f"Network error: {e}")
                
    if st.button("← Back to Login"):
        navigate_to('student_login')

# ==========================================
# 6. PAGE: VERIFY OTP & GENERATE USN
# ==========================================
elif st.session_state.page == 'verify_otp':
    st.subheader("Verify Your Email")
    st.write("Check your inbox! We sent a 6-digit code to your email.")
    
    entered_otp = st.text_input("Enter 6-Digit OTP:")
    
    if st.button("Verify & Generate USN", type="primary"):
        if entered_otp == st.session_state.generated_otp:
            res = supabase.table('students').select('USN').execute()
            max_num = 0
            for student in res.data:
                usn = student.get('USN', '')
                if usn.startswith('STUD'):
                    try:
                        num = int(usn.replace('STUD', ''))
                        if num > max_num:
                            max_num = num
                    except:
                        pass
            
            new_usn = f"STUD{str(max_num + 1).zfill(3)}"
            
            new_record = {
                'USN': new_usn,
                'Password': st.session_state.pending_reg['dob'],
                'Attendance (%)': 0,
                'Fees Status': 'Not Paid',
                'Subject 1 Marks (out of 50)': 0,
                'Subject 2 Marks (out of 50)': 0,
                'Subject 3 Marks (out of 50)': 0,
                'Subject 4 Marks (out of 50)': 0,
                'Subject 5 Marks (out of 50)': 0,
                'Subject 6 Marks (out of 50)': 0
            }
            supabase.table('students').insert(new_record).execute()
            
            st.success("Registration Successful!")
            st.markdown(f"### Your permanently assigned USN is: **{new_usn}**")
            st.info("Please note this down. You will use this USN and your Date of Birth to log in.")
        else:
            st.error("Invalid OTP. Please try again.")
            
    if st.button("Go to Login Portal"):
        navigate_to('student_login')

# ==========================================
# 7. PAGE: STUDENT DASHBOARD
# ==========================================
elif st.session_state.page == 'student_dashboard':
    user = st.session_state.user_data
    st.header("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("USN", user['USN'])
    col2.metric("Attendance", f"{user['Attendance (%)']}%")
    col3.metric("Fees Status", user['Fees Status'])
    
    st.subheader("Academic Performance")
    marks_data = {
        "Subject": ["Subject 1", "Subject 2", "Subject 3", "Subject 4", "Subject 5", "Subject 6"],
        "Marks Obtained (Out of 50)": [
            user['Subject 1 Marks (out of 50)'],
            user['Subject 2 Marks (out of 50)'],
            user['Subject 3 Marks (out of 50)'],
            user['Subject 4 Marks (out of 50)'],
            user['Subject 5 Marks (out of 50)'],
            user['Subject 6 Marks (out of 50)']
        ]
    }
    st.dataframe(marks_data, use_container_width=True, hide_index=True)
    
    if st.button("Logout", type="primary"):
        st.session_state.user_data = None
        navigate_to('home')

# ==========================================
# 8. PAGE: TEACHER LOGIN
# ==========================================
elif st.session_state.page == 'teacher_login':
    st.subheader("Teacher Portal Login")
    
    t_email = st.text_input("Email Address:")
    t_pass = st.text_input("Password:", type="password")
    
    if st.button("Secure Login", type="primary", use_container_width=True):
        res = supabase.table('teachers').select('*').eq('College Login ID', t_email).eq('Password', t_pass).execute()
        if len(res.data) > 0:
            st.session_state.user_data = res.data[0]
            # Interceptor for First Time Login
            if st.session_state.user_data.get('First Login') is True:
                navigate_to('teacher_force_password')
            else:
                navigate_to('teacher_dashboard')
        else:
            st.error("Invalid Email or Password.")
            
    st.markdown("---")
    st.write("New Faculty?")
    if st.button("Register as Staff", use_container_width=True):
        navigate_to('teacher_secret_auth')
            
    if st.button("← Back to Home"):
        navigate_to('home')

# ==========================================
# 8.5 PAGE: MANDATORY PASSWORD CHANGE
# ==========================================
elif st.session_state.page == 'teacher_force_password':
    st.subheader("Security Setup Required 🔒")
    st.warning("You are using a temporary password. Please set a permanent password.")
    new_pass = st.text_input("Enter New Password:", type="password")
    confirm_pass = st.text_input("Confirm New Password:", type="password")
    
    if st.button("Update Password & Continue", type="primary", use_container_width=True):
        if new_pass == confirm_pass and len(new_pass) >= 6:
            email_id = st.session_state.user_data['College Login ID']
            supabase.table('teachers').update({'Password': new_pass, 'First Login': False}).eq('College Login ID', email_id).execute()
            st.session_state.user_data['First Login'] = False
            st.session_state.user_data['Password'] = new_pass
            st.success("Password updated! Redirecting...")
            time.sleep(1.5)
            navigate_to('teacher_dashboard')
        else: 
            st.error("Passwords do not match or are too short (minimum 6 characters).")

# ==========================================
# 9. PAGE: TEACHER DASHBOARD
# ==========================================
elif st.session_state.page == 'teacher_dashboard':
    st.header("Control Panel")
    st.write(f"Welcome, **{st.session_state.user_data.get('Name', 'Teacher')}**")
    
    tab1, tab2 = st.tabs(["Edit Existing Student", "Add New Student"])
    
    with tab1:
        st.subheader("Modify Records")
        search_usn = st.text_input("Enter USN to find student:")
        
        if st.button("Retrieve Record"):
            res = supabase.table('students').select('*').eq('USN', search_usn).execute()
            if len(res.data) > 0:
                st.session_state.edit_student = res.data[0]
            else:
                st.error("404: Student record not found.")
                
        if 'edit_student' in st.session_state:
            s_data = st.session_state.edit_student
            st.markdown(f"### Editing Record: **{s_data['USN']}**")
            
            with st.form("edit_form"):
                att = st.number_input("Attendance (%)", min_value=0, max_value=100, value=int(s_data['Attendance (%)']))
                
                fee_options = ["Paid", "Not Paid"]
                default_fee_index = fee_options.index(s_data['Fees Status']) if s_data['Fees Status'] in fee_options else 1
                fees = st.selectbox("Financial Status", fee_options, index=default_fee_index)
                
                st.write("Academic Metrics")
                s1 = st.number_input("Subject 1", min_value=0, max_value=50, value=int(s_data['Subject 1 Marks (out of 50)']))
                s2 = st.number_input("Subject 2", min_value=0, max_value=50, value=int(s_data['Subject 2 Marks (out of 50)']))
                s3 = st.number_input("Subject 3", min_value=0, max_value=50, value=int(s_data['Subject 3 Marks (out of 50)']))
                s4 = st.number_input("Subject 4", min_value=0, max_value=50, value=int(s_data['Subject 4 Marks (out of 50)']))
                s5 = st.number_input("Subject 5", min_value=0, max_value=50, value=int(s_data['Subject 5 Marks (out of 50)']))
                s6 = st.number_input("Subject 6", min_value=0, max_value=50, value=int(s_data['Subject 6 Marks (out of 50)']))
                
                if st.form_submit_button("Commit Changes to Database"):
                    update_payload = {
                        'Attendance (%)': att,
                        'Fees Status': fees,
                        'Subject 1 Marks (out of 50)': s1,
                        'Subject 2 Marks (out of 50)': s2,
                        'Subject 3 Marks (out of 50)': s3,
                        'Subject 4 Marks (out of 50)': s4,
                        'Subject 5 Marks (out of 50)': s5,
                        'Subject 6 Marks (out of 50)': s6
                    }
                    supabase.table('students').update(update_payload).eq('USN', s_data['USN']).execute()
                    st.success("Database successfully overwritten!")
    
    with tab2:
        st.subheader("Enroll New Candidate")
        with st.form("add_form"):
            new_usn = st.text_input("Assign USN:")
            new_dob = st.date_input("Date of Birth:", value=None, min_value=datetime.date(1990, 1, 1), format="DD/MM/YYYY")
            new_att = st.number_input("Initial Attendance (%)", min_value=0, max_value=100, value=0)
            new_fees = st.selectbox("Financial Status", ["Paid", "Not Paid"], index=1)
            
            st.write("Academic Metrics")
            n1 = st.number_input("Subject 1", min_value=0, max_value=50, value=0, key="n1")
            n2 = st.number_input("Subject 2", min_value=0, max_value=50, value=0, key="n2")
            n3 = st.number_input("Subject 3", min_value=0, max_value=50, value=0, key="n3")
            n4 = st.number_input("Subject 4", min_value=0, max_value=50, value=0, key="n4")
            n5 = st.number_input("Subject 5", min_value=0, max_value=50, value=0, key="n5")
            n6 = st.number_input("Subject 6", min_value=0, max_value=50, value=0, key="n6")
            
            if st.form_submit_button("Register Identity"):
                if not new_usn or new_dob is None:
                    st.error("Missing required identity fields (USN and Date of Birth).")
                else:
                    new_record = {
                        'USN': new_usn,
                        'Password': new_dob.strftime("%d/%m/%Y"),
                        'Attendance (%)': new_att,
                        'Fees Status': new_fees,
                        'Subject 1 Marks (out of 50)': n1,
                        'Subject 2 Marks (out of 50)': n2,
                        'Subject 3 Marks (out of 50)': n3,
                        'Subject 4 Marks (out of 50)': n4,
                        'Subject 5 Marks (out of 50)': n5,
                        'Subject 6 Marks (out of 50)': n6
                    }
                    try:
                        supabase.table('students').insert(new_record).execute()
                        st.success(f"Identity {new_usn} successfully enrolled!")
                    except Exception as e:
                        st.error(f"Insertion Failed: {e}")
    
    st.markdown("---")
    if st.button("End Session (Logout)", type="primary"):
        st.session_state.user_data = None
        if 'edit_student' in st.session_state:
            del st.session_state['edit_student']
        navigate_to('home')

# ==========================================
# 10. PAGE: TEACHER SECRET AUTHENTICATION
# ==========================================
elif st.session_state.page == 'teacher_secret_auth':
    st.subheader("Secure Faculty Onboarding")
    st.write("Please enter the administrative secret key to access the registration portal.")
    
    ADMIN_SECRET_KEY = "CLGPTR-ADMIN-2026"
    
    secret_input = st.text_input("Registration Key:", type="password")
    
    if st.button("Verify Key", type="primary", use_container_width=True):
        if secret_input == ADMIN_SECRET_KEY:
            navigate_to('teacher_registration_form')
        elif secret_input:
            st.error("Access Denied: Invalid Security Key.")
            
    if st.button("← Back to Teacher Login"):
        navigate_to('teacher_login')

# ==========================================
# 11. PAGE: TEACHER REGISTRATION FORM
# ==========================================
elif st.session_state.page == 'teacher_registration_form':
    st.subheader("Faculty Registration")
    st.write("Enter your professional details below to generate your official college credentials.")
    
    with st.form("teacher_reg"):
        t_name = st.text_input("Full Name:")
        t_dob = st.date_input("Date of Birth:", value=None, min_value=datetime.date(1950, 1, 1), format="DD/MM/YYYY")
        t_personal_email = st.text_input("Personal Email:")
        t_phone = st.text_input("Phone Number:")
        t_qual = st.text_input("Highest Qualification (e.g., Ph.D. in Computer Science):")
        t_exp = st.number_input("Years of Experience:", min_value=0, max_value=50, value=0)
        
        submit_reg = st.form_submit_button("Generate Official Credentials")
        
        if submit_reg:
            if not t_name or not t_personal_email or t_dob is None:
                st.error("Please fill in your Name, DOB, and Personal Email.")
            else:
                clean_name = t_name.strip().lower().replace(" ", ".")
                college_email = f"{clean_name}@clg-ptr.edu"
                
                generated_password = f"PTR-{random.randint(1000, 9999)}"
                
                new_teacher = {
                    'Name': t_name,
                    'College Login ID': college_email,
                    'Password': generated_password,
                    'DOB': t_dob.strftime("%d/%m/%Y"),
                    'Personal Email': t_personal_email,
                    'Qualification': t_qual,
                    'Experience': t_exp,
                    'Phone': t_phone,
                    'First Login': True  # Added to trigger the force password flow
                }
                
                try:
                    supabase.table('teachers').insert(new_teacher).execute()
                    
                    st.success("✅ Faculty Onboarding Complete!")
                    st.info("Please securely record your new login credentials below. You will use these to access the Teacher Portal.")
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Official College ID", college_email)
                    col2.metric("Temporary Password", generated_password)
                    
                except Exception as e:
                    st.error(f"Database Error: It looks like this email might already exist. ({e})")
                    
    if st.button("Proceed to Teacher Login"):
        navigate_to('teacher_login')
