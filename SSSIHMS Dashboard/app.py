import streamlit as st
import oracledb
import hashlib
import base64
from pathlib import Path

# Page config
st.set_page_config(
    page_title="🏥 SSSIHMS Dashboard Login",
    page_icon="🏥",
    layout="centered"
)

# Oracle client init
oracledb.init_oracle_client(
    lib_dir=r"C:\Users\sumir\Downloads\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9"
)

def get_connection():
    return oracledb.connect(
        user="hisapp",
        password="his@2025",
        dsn="192.168.21.6:1521/hisdb"
    )

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest().lower()

def verify_user_from_db(staffid, password):
    try:
        conn = get_connection()
        cur = conn.cursor()
        encrypted = hash_password(password)
        query = """
            SELECT STAFFNAME, LOGINOK, ACCESS_ROLE, HOSPITALID
            FROM STAFFMASTER
            WHERE STAFFID = :staffid
              AND TXTPASSWD = :pwd
        """
        cur.execute(query, {"staffid": staffid, "pwd": encrypted})
        row = cur.fetchone()
        if row is None:
            return None
        staffname, loginok, access_role, hospitalid = row
        if loginok != "Y":
            return "NOT_ACTIVE"
        role = "admin" if access_role == "A" else "staff"
        return {
            "staffname": staffname, 
            "role": role,
            "hospitalid": hospitalid
        }
    except Exception as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# Session defaults
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.staffname = ""
    st.session_state.role = "staff"
    st.session_state.hospitalid = None

# CSS with HIDDEN SIDEBAR
st.markdown("""
    <style>
    /* ========== HIDE SIDEBAR NAVIGATION ========== */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    button[kind="header"] {
        display: none;
    }
    /* ============================================== */
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0f3460 100%);
        overflow: hidden;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container - Fit to viewport */
    .main .block-container {
        padding: 1.5rem 1rem;
        max-width: 480px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 100vh;
    }
    
    /* Outer container - More Compact */
    .login-outer-container {
        background: rgba(26, 32, 46, 0.85);
        backdrop-filter: blur(20px);
        padding: 1.5rem 2.5rem 1.8rem 2.5rem;
        border-radius: 20px;
        box-shadow: 
            0 15px 45px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Logo container - Smaller */
    .logo-container {
        background: white;
        padding: 0.7rem;
        border-radius: 10px;
        display: inline-block;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .logo-img {
        max-width: 80px;
        height: auto;
        display: block;
    }
    
    .hospital-icon {
        font-size: 3rem;
    }
    
    /* Header section - More Compact */
    .login-header {
        text-align: center;
        margin-bottom: 1.2rem;
    }
    
    .login-title {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
        text-shadow: 0 2px 8px rgba(255, 255, 255, 0.15);
        letter-spacing: -0.5px;
    }
    
    .login-subtitle {
        color: #b8c5d6;
        font-size: 0.95rem;
        font-weight: 400;
    }
    
    /* Divider - More Subtle */
    .divider {
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.12), transparent);
        margin: 1.2rem 0 1rem 0;
    }
    
    /* Input labels - Soft */
    .stTextInput > label {
        color: #cbd5e0 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Input fields - Soft dark */
    .stTextInput > div > div > input {
        background: rgba(15, 20, 30, 0.6) !important;
        border: 1.5px solid rgba(100, 116, 139, 0.3) !important;
        border-radius: 10px !important;
        padding: 0.9rem 1.1rem !important;
        font-size: 1.1rem !important;
        color: #e2e8f0 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(96, 165, 250, 0.6) !important;
        background: rgba(15, 20, 30, 0.8) !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.15) !important;
    }
    
    /* Login button - Compact */
    .stButton > button {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.85rem 1.5rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-top: 0.8rem !important;
        box-shadow: 0 4px 16px rgba(96, 165, 250, 0.3) !important;
        letter-spacing: 0.3px !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 24px rgba(96, 165, 250, 0.4) !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Alert messages - Soft */
    .stAlert {
        border-radius: 10px !important;
        font-size: 0.95rem !important;
        padding: 0.9rem !important;
        border: none !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Info badge - Soft */
    .info-badge {
        background: rgba(96, 165, 250, 0.12);
        border: 1px solid rgba(96, 165, 250, 0.25);
        border-radius: 8px;
        padding: 0.65rem 1rem;
        text-align: center;
        color: #93c5fd;
        font-weight: 600;
        font-size: 0.95rem;
        margin-top: 0.8rem;
    }
    
    /* Footer - More Compact */
    .footer-text {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        margin-top: 1.2rem;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #60a5fa !important;
    }
    
    /* Remove extra spacing */
    .stTextInput {
        margin-bottom: 0.7rem !important;
    }
    
    /* Tighter input spacing */
    .stTextInput > div {
        margin-bottom: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Logo loading
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

try:
    logo_base64 = get_base64_image("assets/hospital_logo.png")
    logo_html = f'<div class="logo-container"><img src="data:image/png;base64,{logo_base64}" class="logo-img" alt="SSSIHMS Logo"></div>'
except:
    logo_html = '<div class="logo-container"><div class="hospital-icon">🏥</div></div>'

# Login UI
st.markdown(f"""
    <div class='login-outer-container'>
        <div class='login-header'>
            {logo_html}
            <div class='login-title'>SSSIHMS Dashboard</div>
            <div class='login-subtitle'>Staff Portal Login</div>
        </div>
        <div class='divider'></div>
""", unsafe_allow_html=True)

username = st.text_input("👤 Staff ID", placeholder="Enter staff ID", key="username_input")
password = st.text_input("🔒 Password", type="password", placeholder="Enter password", key="password_input")
login_button = st.button("Login", use_container_width=True)

# Login logic
if login_button:
    if not username or not password:
        st.error("⚠️ Please enter both Staff ID and Password")
    else:
        with st.spinner("Authenticating..."):
            result = verify_user_from_db(username, password)
            if result is None:
                st.error("❌ Invalid Staff ID or Password")
            elif result == "NOT_ACTIVE":
                st.error("🚫 Your login is not yet activated. Please contact admin.")
            else:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.staffname = result["staffname"]
                st.session_state.role = result["role"]
                st.session_state.hospitalid = result["hospitalid"]
                if result["role"] == "admin":
                    st.success(f"🛠️ Admin Access - Welcome {result['staffname']}!")
                else:
                    st.success(f"✅ Welcome back, {result['staffname']}!")
                if result["hospitalid"]:
                    st.markdown(f"<div class='info-badge'>🏥 Hospital: {result['hospitalid']}</div>", unsafe_allow_html=True)
                st.switch_page("pages/dashboard.py")

st.markdown("""
        <div class='footer-text'>
            🔒 Secured Access | SSSIHMS © 2025
        </div>
    </div>
""", unsafe_allow_html=True)