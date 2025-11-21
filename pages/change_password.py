import streamlit as st
import oracledb
import hashlib

# =====================================================
# STREAMLIT CONFIG
# =====================================================
st.set_page_config(
    page_title="🔑 Change Password",
    page_icon="🔑",
    layout="centered"
)

# =====================================================
# HIDE SIDEBAR NAVIGATION + ADD STYLING
# =====================================================
st.markdown("""
    <style>
    /* Hide Streamlit page navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Modern styling */
    .main {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Password strength indicator */
    .password-strength {
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: 600;
    }
    
    .strength-weak {
        background-color: #fee;
        color: #c00;
        border-left: 4px solid #c00;
    }
    
    .strength-medium {
        background-color: #fef6e6;
        color: #f57c00;
        border-left: 4px solid #f57c00;
    }
    
    .strength-strong {
        background-color: #e8f5e9;
        color: #2e7d32;
        border-left: 4px solid #2e7d32;
    }
    
    /* Info card */
    .info-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        margin: 20px 0;
        color: white;
    }
    
    .info-card h4 {
        color: white !important;
        margin: 0 !important;
    }
    
    .info-card p {
        color: rgba(255, 255, 255, 0.95) !important;
        margin: 5px 0 !important;
    }
    
    .info-card strong {
        color: rgba(255, 255, 255, 0.85);
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# ORACLE CLIENT INIT
# =====================================================
oracledb.init_oracle_client(
    lib_dir=r"C:\Users\sumir\Downloads\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9"
)

def get_connection():
    return oracledb.connect(
        user="hisapp",
        password="his@2025",
        dsn="192.168.21.6:1521/hisdb"
    )

# =====================================================
# PASSWORD HASH (SHA-256)
# =====================================================
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest().lower()

# =====================================================
# AUTH CHECK
# =====================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 Please log in first.")
    st.stop()

# =====================================================
# SIDEBAR NAVIGATION BUTTONS
# =====================================================
st.sidebar.title("🎛️ Navigation")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard"):
        st.switch_page("pages/dashboard.py")
    if st.button("🔒 Logout", use_container_width=True, key="nav_logout"):
        st.switch_page("app.py")

with col2:
    # Change password is current page
    st.button("🔑 Password", use_container_width=True, disabled=True, key="nav_password_current")
    
    # Show admin panel button only if user is admin
    if st.session_state.get("role") == "admin":
        if st.button("⚙️ Admin", use_container_width=True, key="nav_admin"):
            st.switch_page("pages/admin_panel.py")

st.sidebar.markdown("---")
st.sidebar.info(f"""
👤 **{st.session_state.get('staffname', 'User')}**  
🆔 {st.session_state.get('username', 'N/A')}  
🏥 {st.session_state.get('hospitalid', 'N/A')}
""")

# =====================================================
# PASSWORD OPERATIONS
# =====================================================
def verify_old_password(staffid: str, old_password: str) -> bool:
    """Verify if the old password matches in database"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        encrypted_old = hash_password(old_password)
        
        cur.execute("""
            SELECT TXTPASSWD 
            FROM STAFFMASTER 
            WHERE STAFFID = :sid
        """, {"sid": staffid})
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row and row[0]:
            return row[0].lower() == encrypted_old
        return False
        
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return False

def update_password(staffid: str, new_password: str) -> bool:
    """Update password in STAFFMASTER table"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        encrypted_new = hash_password(new_password)
        
        cur.execute("""
            UPDATE STAFFMASTER 
            SET TXTPASSWD = :pwd 
            WHERE STAFFID = :sid
        """, {"pwd": encrypted_new, "sid": staffid})
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to update password: {e}")
        return False

def check_password_strength(password: str) -> tuple:
    """Check password strength and return (strength_level, message, css_class)"""
    if len(password) < 6:
        return ("weak", "⚠️ Weak: Password too short (minimum 6 characters)", "strength-weak")
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    strength_count = sum([has_upper, has_lower, has_digit, has_special])
    
    if strength_count >= 3 and len(password) >= 8:
        return ("strong", "✅ Strong: Password meets all requirements", "strength-strong")
    elif strength_count >= 2 and len(password) >= 6:
        return ("medium", "⚡ Medium: Consider adding more variety", "strength-medium")
    else:
        return ("weak", "⚠️ Weak: Add uppercase, numbers, and special characters", "strength-weak")

# =====================================================
# UI — CHANGE PASSWORD
# =====================================================
st.title("🔑 Change Your Password")
st.markdown("Update your password securely. Your old password is required for verification.")

# User info card
st.markdown(f"""
<div class="info-card">
    <h4 style="margin:0;">👤 Account Information</h4>
    <p style="margin:5px 0;"><strong>Staff ID:</strong> {st.session_state.get('username', 'N/A')}</p>
    <p style="margin:5px 0;"><strong>Name:</strong> {st.session_state.get('staffname', 'N/A')}</p>
    <p style="margin:5px 0;"><strong>Hospital:</strong> {st.session_state.get('hospitalid', 'N/A')}</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Password change form
with st.form("change_password_form", clear_on_submit=False):
    st.subheader("🔐 Password Update")
    
    old_password = st.text_input(
        "Old Password *",
        type="password",
        placeholder="Enter your current password",
        help="Enter your existing password for verification"
    )
    
    st.markdown("---")
    
    new_password = st.text_input(
        "New Password *",
        type="password",
        placeholder="Enter new password (min 6 characters)",
        help="Choose a strong password with uppercase, lowercase, numbers, and special characters"
    )
    
    # Password strength indicator
    if new_password:
        strength_level, strength_msg, strength_class = check_password_strength(new_password)
        st.markdown(f'<div class="password-strength {strength_class}">{strength_msg}</div>', 
                   unsafe_allow_html=True)
    
    confirm_password = st.text_input(
        "Confirm New Password *",
        type="password",
        placeholder="Re-enter new password",
        help="Must match the new password above"
    )
    
    st.markdown("---")
    
    # Password requirements
    with st.expander("📋 Password Requirements", expanded=False):
        st.markdown("""
        **For a strong password, include:**
        - ✅ At least 6 characters (8+ recommended)
        - ✅ Uppercase letters (A-Z)
        - ✅ Lowercase letters (a-z)
        - ✅ Numbers (0-9)
        - ✅ Special characters (!@#$%^&*)
        
        **Avoid:**
        - ❌ Common words or patterns
        - ❌ Personal information (name, birthdate)
        - ❌ Sequential numbers (123456)
        """)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        submitted = st.form_submit_button(
            "🔄 Update Password",
            use_container_width=True,
            type="primary"
        )
    with col2:
        if st.form_submit_button("❌ Cancel", use_container_width=True):
            st.switch_page("pages/dashboard.py")

# =====================================================
# FORM SUBMISSION LOGIC
# =====================================================
if submitted:
    username = st.session_state.get('username')
    
    # Validation checks
    if not old_password or not new_password or not confirm_password:
        st.error("❌ All fields are required. Please fill in all password fields.")
    
    elif new_password != confirm_password:
        st.error("❌ New passwords do not match. Please ensure both fields are identical.")
    
    elif old_password == new_password:
        st.warning("⚠️ New password must be different from old password.")
    
    elif len(new_password) < 6:
        st.error("❌ Password too short. Minimum 6 characters required.")
    
    else:
        # Verify old password
        with st.spinner("🔍 Verifying old password..."):
            if not verify_old_password(username, old_password):
                st.error("❌ Old password is incorrect. Please try again.")
            else:
                # Update password
                with st.spinner("🔄 Updating password..."):
                    if update_password(username, new_password):
                        st.success("✅ Password updated successfully!")
                        st.info("💡 Please remember your new password. You can now use it to log in.")
                        
                        # Option to go back to dashboard
                        if st.button("🏠 Return to Dashboard", type="primary"):
                            st.switch_page("pages/dashboard.py")
                    else:
                        st.error("❌ Failed to update password. Please try again or contact support.")

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.caption("🔒 Your password is encrypted using SHA-256 hashing for security.")
st.caption("💡 Tip: Use a password manager to generate and store strong passwords securely.")