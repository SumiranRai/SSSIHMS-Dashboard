# pages/dashboard.py
"""
Hospital Dashboard
"""
import streamlit as st
import pandas as pd
import oracledb
import altair as alt
import io
import zipfile
import streamlit.components.v1 as components
import json
import os

from datetime import date, datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# CSS 
def inject_modern_css():
    """Inject modern, professional CSS styling"""
    st.markdown("""
    <style>
    /* ========== HIDE SIDEBAR PAGE NAVIGATION ========== */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Hide the divider line after nav */
    section[data-testid="stSidebar"] > div:first-child > div:first-child {
        padding-top: 0rem;
    }
    /* ================================================== */
    
    
    /* Global */
    .main { 
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); 
    }
    
    /* Enhanced KPI Cards */
    .kpi-card {
        padding: 24px 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%);
        pointer-events: none;
    }
    
    .kpi-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 16px 32px rgba(0,0,0,0.25);
    }
    
    .kpi-icon {
        font-size: 36px;
        margin-bottom: 10px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
    }
    
    .kpi-title {
        font-size: 13px;
        font-weight: 600;
        opacity: 0.95;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    
    .kpi-value {
        font-size: 38px;
        font-weight: 800;
        margin: 10px 0;
        text-shadow: 0 2px 8px rgba(0,0,0,0.2);
        line-height: 1;
    }
    
    .kpi-sub {
        font-size: 12px;
        opacity: 0.9;
        margin-top: 10px;
        font-weight: 500;
    }
    
    /* Modern Gradients */
    .kpi-grad-1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .kpi-grad-2 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .kpi-grad-3 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .kpi-grad-4 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .kpi-grad-5 { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    .kpi-grad-6 { background: linear-gradient(135deg, #30cfd0 0%, #330867 100%); }
    .kpi-grad-7 { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); }
    .kpi-grad-8 { background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); }
    
    /* Section Headers */
    .section-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 14px;
        margin: 28px 0 20px 0;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .section-header h2 {
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Breadcrumb */
    .breadcrumb {
        background: white;
        padding: 14px 24px;
        border-radius: 10px;
        margin: 18px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        font-size: 14px;
        font-weight: 500;
        color: #495057;
        border-left: 4px solid #667eea;
    }
    
    /* Enhanced Buttons */
    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s;
        border: none;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
    }
    
    /* Data Cards */
    .data-card {
        background: white;
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 16px 0;
        border-left: 4px solid #667eea;
    }
    
    /* Metrics */
    div[data-testid="metric-container"] {
        background: white;
        padding: 16px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Info/Warning Boxes */
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    /* Sidebar - Keep default styling */
    /* Removed custom sidebar styling to preserve default filters appearance */
    
    /* Tables */
    .dataframe {
        border-radius: 10px !important;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Charts */
    .chart-container {
        background: white;
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Updated kpi_card_html function with modern styling
def kpi_card_html(title, value, subtext, grad_class="kpi-grad-1", icon="📊"):
    """Generate modern KPI card HTML with enhanced styling"""
    return f"""
    <div class="kpi-card {grad_class}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{subtext}</div>
    </div>
    """
# -------------------------
# Page config (must be first Streamlit call)
# -------------------------
st.set_page_config(page_title="🏥 SSSIHMS Hospital Dashboard", page_icon="🏥", layout="wide")

inject_modern_css()

# def inject_navbar():
#     """Inject navigation bar at the top of the dashboard (accounting for Streamlit's top bar)"""
    
#     # Get user info from session state
#     staffname = st.session_state.get("staffname", "User")
#     role = st.session_state.get("role", "staff")
#     hospitalid = st.session_state.get("hospitalid", "N/A")
    
#     st.markdown(f"""
#     <style>
#     /* Navbar Styles - Positioned below Streamlit's default top bar */
#     .navbar {{
#         background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
#         padding: 1rem 2rem;
#         display: flex;
#         justify-content: space-between;
#         align-items: center;
#         box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
#         border-bottom: 2px solid rgba(96, 165, 250, 0.3);
#         margin: -1rem -5rem 2rem -5rem;
#         position: relative;
#         z-index: 999;
#     }}
    
#     .navbar-left {{
#         display: flex;
#         align-items: center;
#         gap: 1rem;
#     }}
    
#     .navbar-logo {{
#         width: 40px;
#         height: 40px;
#         background: white;
#         border-radius: 8px;
#         padding: 5px;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         font-size: 24px;
#     }}
    
#     .navbar-title {{
#         color: white;
#         font-size: 1.4rem;
#         font-weight: 700;
#         letter-spacing: -0.5px;
#     }}
    
#     .navbar-subtitle {{
#         color: #93c5fd;
#         font-size: 0.85rem;
#         margin-top: -2px;
#     }}
    
#     .navbar-right {{
#         display: flex;
#         align-items: center;
#         gap: 1.5rem;
#     }}
    
#     .navbar-user {{
#         text-align: right;
#     }}
    
#     .navbar-username {{
#         color: white;
#         font-weight: 600;
#         font-size: 0.95rem;
#     }}
    
#     .navbar-role {{
#         color: #93c5fd;
#         font-size: 0.8rem;
#         text-transform: uppercase;
#     }}
    
#     .navbar-hospital {{
#         background: rgba(96, 165, 250, 0.15);
#         border: 1px solid rgba(96, 165, 250, 0.3);
#         padding: 0.5rem 1rem;
#         border-radius: 8px;
#         color: #93c5fd;
#         font-size: 0.85rem;
#         font-weight: 600;
#     }}
#     </style>
    
#     <div class='navbar'>
#         <div class='navbar-left'>
#             <div class='navbar-logo'>🏥</div>
#             <div>
#                 <div class='navbar-title'>SSSIHMS Dashboard</div>
#                 <div class='navbar-subtitle'>Hospital Management System</div>
#             </div>
#         </div>
#         <div class='navbar-right'>
#             <div class='navbar-hospital'>🏥 {hospitalid}</div>
#             <div class='navbar-user'>
#                 <div class='navbar-username'>👤 {staffname}</div>
#                 <div class='navbar-role'>{"🛠️ Administrator" if role == "admin" else "👨‍⚕️ Staff"}</div>
#             </div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

# # Call the navbar
# inject_navbar()

# -------------------------
# Access guard (login handled in app.py)
# -------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 Please log in from the main page.")
    st.stop()

# -------------------------
# Oracle connection helper with connection pooling
# -------------------------

# Load environment variables (create .env file with DB credentials)
load_dotenv()

# Initialize connection pool (performance optimization)
@st.cache_resource
def init_connection_pool():
    """Initialize Oracle connection pool for better performance"""
    try:
        pool = oracledb.create_pool(
            user=os.getenv("DB_USER", "hisapp"),
            password=os.getenv("DB_PASSWORD", "his@2025"),
            dsn=os.getenv("DB_DSN", "192.168.21.6:1521/hisdb"),
            min=2,
            max=10,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT
        )
        return pool
    except Exception as e:
        st.error(f"Failed to create connection pool: {e}")
        st.stop()

# Get connection from pool
def get_conn():
    """Get connection from pool"""
    pool = init_connection_pool()
    return pool.acquire()

# Initialize main connection
try:
    conn = get_conn()
except Exception as e:
    st.error(f"Failed to connect to Oracle DB: {e}")
    st.stop()

# -------------------------
# Utilities
# -------------------------
def safe_sql(v):
    if v is None:
        return ""
    return str(v).replace("'", "''")

def build_hospital_where(alias_list):
    if selected_hospital in (None, "", "All Hospitals"):
        return "1=1"
    safe = safe_sql(selected_hospital)
    parts = [f"{a}.HOSPITALID = '{safe}'" for a in alias_list]
    parts.append(f"HOSPITALID = '{safe}'")
    return "(" + " OR ".join(parts) + ")"

# -------------------------
# Sidebar Navigation (matching admin panel design)
# -------------------------
st.sidebar.title("🎛️ Navigation")

col1, col2 = st.sidebar.columns(2)

with col1:
    # Dashboard (current page - disabled to show it's active)
    st.button("🏠 Dashboard", use_container_width=True, disabled=True, key="nav_dashboard_current")
    
    # Change Password
    if st.button("🔑 Password", use_container_width=True, key="nav_password"):
        st.switch_page("pages/change_password.py")

with col2:
    # Admin Panel (only for admins)
    if st.session_state.get("role") == "admin":
        if st.button("⚙️ Admin", use_container_width=True, key="nav_admin"):
            st.switch_page("pages/admin_panel.py")
    
    # Logout
    if st.button("🔒 Logout", use_container_width=True, key="nav_logout"):
        st.switch_page("app.py")

st.sidebar.markdown("---")

# User info display
st.sidebar.info(f"""
👤 **{st.session_state.get('staffname', 'User')}**  
🏥 **Hospital:** {st.session_state.get('hospitalid', 'N/A')}  
🔐 **Role:** {'🛡️ Admin' if st.session_state.get('role') == 'admin' else '👨‍⚕️ Staff'}
""")

st.sidebar.markdown("---")

# -------------------------
# Filters Section
# -------------------------
st.sidebar.header("📊 Filters")

# Date range / Year-Month
today = date.today()
# Default to current month (first day to today)
default_from = date(today.year, today.month, 1)
default_to = today

use_year_month = st.sidebar.checkbox("Use Year + Month filter (instead of From/To)", value=False)
months = ["January","February","March","April","May","June","July","August","September","October","November","December"]

if use_year_month:
    years = list(range(2000, today.year + 1))[::-1]  # years from 2000 to current year
    sel_year = st.sidebar.selectbox("Year", years, index=0)
    sel_month = st.sidebar.selectbox("Month", months, index=today.month - 1)
    m = months.index(sel_month) + 1
    from_date = date(sel_year, m, 1)
    to_date = (date(sel_year, m+1, 1) - timedelta(days=1)) if m < 12 else date(sel_year, 12, 31)
else:
    from_date = st.sidebar.date_input("From Date", value=default_from, min_value=date(2000,1,1), max_value=today)
    to_date = st.sidebar.date_input("To Date", value=default_to, min_value=date(2000,1,1), max_value=today)

# Department dropdown
try:
    dept_df = pd.read_sql("SELECT DISTINCT DEPTNAME, DEPTCODE, HOSPITALID FROM DEPARTMENT ORDER BY DEPTNAME", conn)
    dept_list = ["All"] + dept_df["DEPTNAME"].dropna().tolist()
except Exception:
    dept_list = ["All"]
selected_dept = st.sidebar.selectbox("Department", dept_list, index=0)

# Hospital dropdown - default to user's hospital from STAFFMASTER.HOSPITALID
try:
    hosp_df = pd.read_sql("SELECT DISTINCT HOSPITALID FROM DEPARTMENT ORDER BY HOSPITALID", conn)
    hosp_list = ["All Hospitals"] + hosp_df["HOSPITALID"].dropna().tolist()
except Exception:
    hosp_list = ["All Hospitals"]

# Get user's hospital from session state (set during login from STAFFMASTER)
user_hospital = st.session_state.get("hospitalid", None)
default_index = 0
if user_hospital and user_hospital in hosp_list:
    default_index = hosp_list.index(user_hospital)
    
selected_hospital = st.sidebar.selectbox("Hospital", hosp_list, index=default_index)

# =================================================================================
# Ordering dept for radiology
ordering_dept_options = ["All"] + (dept_df["DEPTNAME"].dropna().tolist() if 'dept_df' in globals() else [])
selected_ordering_dept = st.sidebar.selectbox("Ordering Dept (for Radiology)", ordering_dept_options, index=0)

# Radiology modality filter
try:
    category_base_q = "SELECT DISTINCT CATEGORY FROM STATS_DETAILS WHERE CATEGORY IS NOT NULL ORDER BY CATEGORY"
    category_options_df = pd.read_sql(category_base_q, conn)
    category_options = ["All"] + category_options_df["CATEGORY"].dropna().tolist()
except Exception:
    category_options = ["All"]

selected_category = st.sidebar.selectbox("Category", category_options, index=0)

# ======================== SURGEON FILTER ========================
st.sidebar.subheader("Surgeon Filter")

# ←←← MAKE SURE safe_sql() IS DEFINED BEFORE THIS BLOCK ←←←
# (It is defined later in our file — so we define a tiny local version here if missing)
try:
    _ = safe_sql  # Test if already exists
except NameError:
    def safe_sql(v):
        if v is None:
            return ""
        return str(v).replace("'", "''")

# Checkbox: Lifetime vs Current Period
use_lifetime = st.sidebar.checkbox(
    "Show surgeons by total lifetime surgeries (not just selected period)",
    value=True,
    help="Uncheck to show only surgeons active in the selected date range"
)

# Safe hospital condition
hospital_condition = "1=1"
if selected_hospital and selected_hospital not in ("", "All Hospitals"):
    hospital_condition = f"sp.HOSPITALID = '{safe_sql(selected_hospital)}'"

# Build query
if use_lifetime:
    surgeon_q = f"""
    SELECT 
        sp.STAFFID,
        NVL(sm.STAFFNAME, sp.STAFFID || ' (Name Missing)') AS STAFFNAME,
        COUNT(*) AS TOTAL_SURGERIES
    FROM SURGERY_PERSONNEL sp
    LEFT JOIN STAFFMASTER sm ON sp.STAFFID = sm.STAFFID
    WHERE sp.STAFFROLE = 'SURGEON'
      AND {hospital_condition}
    GROUP BY sp.STAFFID, sm.STAFFNAME
    HAVING COUNT(*) > 0
    ORDER BY TOTAL_SURGERIES DESC, STAFFNAME
    """
else:
    surgeon_q = f"""
    SELECT 
        sp.STAFFID,
        NVL(sm.STAFFNAME, sp.STAFFID || ' (Name Missing)') AS STAFFNAME,
        COUNT(*) AS TOTAL_SURGERIES
    FROM SURGERY_PERSONNEL sp
    LEFT JOIN STAFFMASTER sm ON sp.STAFFID = sm.STAFFID
    JOIN SURGERY s ON sp.SURGERYID = s.SURGERYID
    WHERE sp.STAFFROLE = 'SURGEON'
      AND s.SURGERYDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') 
                            AND TO_DATE('{to_date}', 'YYYY-MM-DD') + 0.99999
      AND {hospital_condition}
    GROUP BY sp.STAFFID, sm.STAFFNAME
    HAVING COUNT(*) > 0
    ORDER BY TOTAL_SURGERIES DESC, STAFFNAME
    """

try:
    surgeons_df = pd.read_sql(surgeon_q, conn)
    if not surgeons_df.empty:
        surgeons_df["DISPLAY"] = surgeons_df.apply(
            lambda r: f"{r['STAFFNAME']} ({r['TOTAL_SURGERIES']} surgeries)", axis=1
        )
        surgeon_options = ["All Surgeons"] + surgeons_df["DISPLAY"].tolist()
        surgeon_id_map = dict(zip(surgeons_df["DISPLAY"], surgeons_df["STAFFID"]))
        surgeon_name_map = dict(zip(surgeons_df["DISPLAY"], surgeons_df["STAFFNAME"]))
    else:
        surgeon_options = ["All Surgeons"]
        surgeon_id_map = surgeon_name_map = {}
except Exception as e:
    st.sidebar.error(f"Surgeon load failed: {e}")
    surgeon_options = ["All Surgeons"]
    surgeon_id_map = surgeon_name_map = {}

selected_doctor_label = st.sidebar.selectbox(
    "Surgeon (Real performers only)",
    options=surgeon_options,
    index=0,
    key="surgeon_select_final"
)

# Extract selected surgeon
selected_surgeon_id = surgeon_id_map.get(selected_doctor_label, None)
selected_surgeon_name = surgeon_name_map.get(selected_doctor_label, None)

# Show count in current period
if selected_surgeon_id and not use_lifetime:
    try:
        cnt_q = f"""
        SELECT COUNT(*) FROM SURGERY s
        JOIN SURGERY_PERSONNEL sp ON s.SURGERYID = sp.SURGERYID
        WHERE sp.STAFFROLE = 'SURGEON' 
          AND sp.STAFFID = '{safe_sql(selected_surgeon_id)}'
          AND s.SURGERYDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') 
                                AND TO_DATE('{to_date}', 'YYYY-MM-DD') + 0.99999
          AND (s.HOSPITALID = '{safe_sql(selected_hospital)}' OR '{selected_hospital}' = 'All Hospitals')
        """
        cnt = pd.read_sql(cnt_q, conn).iloc[0,0]
        st.sidebar.success(f"Selected period: **{cnt}** surgeries")
    except Exception as e:
        st.sidebar.warning(f"Count failed: {e}")
        cnt = pd.read_sql(cnt_q, conn).iloc[0,0]
        st.sidebar.success(f"Selected period: **{cnt}** surgeries")
    except:
        pass

# Update the sidebar display (around line 174):
st.sidebar.markdown(f"**Range:** {from_date} → {to_date}")
st.sidebar.markdown(f"**Department:** {selected_dept}")
st.sidebar.markdown(f"**Hospital:** {selected_hospital}")
st.sidebar.markdown(f"**Category:** {selected_category}")

# -------------------------
# Load Data Logic - Auto-load first time
# -------------------------
st.sidebar.markdown("---")

# Initialize session state for first load tracking
if "dashboard_first_load" not in st.session_state:
    st.session_state.dashboard_first_load = True
    st.session_state.data_loaded = True  # Auto-load on first visit

# Load Data button
load_data = st.sidebar.button("🔄 Load Data", type="primary", use_container_width=True)

# Set data_loaded flag when button is clicked
if load_data:
    st.session_state.data_loaded = True
    st.session_state.dashboard_first_load = False

# For first visit, auto-load and show info message
if st.session_state.dashboard_first_load:
    #st.info("ℹ️ Dashboard loaded with default filters (your hospital, current month). Change filters and click **'Load Data'** to refresh.")
    st.session_state.dashboard_first_load = False

# Show message if data not loaded yet (only after first load)
if not st.session_state.get("data_loaded", False):
    st.info("👆 Please adjust your filters and click **'Load Data'** button in the sidebar to refresh dashboard.")
    st.stop()

# -------------------------
# Data Validation Functions
# -------------------------
def validate_date_range(from_date, to_date):
    """Validate date range inputs"""
    if from_date > to_date:
        st.error("❌ Start date cannot be after end date!")
        return False
    
    days_diff = (to_date - from_date).days
    
    if days_diff > 365:
        st.warning(f"⚠️ Date range is {days_diff} days ({days_diff/30:.1f} months). Large ranges may affect performance.")
        
    if days_diff == 0:
        st.info("ℹ️ You've selected a single day.")
    
    return True

def validate_filters(hospital, dept, from_date, to_date):
    """Validate all filters before querying"""
    if not validate_date_range(from_date, to_date):
        return False
    
    # Add more validation as needed
    return True

# -------------------------
# Data Export Functions
# -------------------------
def create_excel_download(df, filename, sheet_name='Data'):
    """Create formatted Excel file for download"""
    buffer = io.BytesIO()
    
    try:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Add formatting
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#0ea77c',
                'font_color': 'white',
                'border': 1
            })
            
            # Format header row
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
                # Auto-adjust column width
                column_len = max(df[value].astype(str).str.len().max(), len(value)) + 2
                worksheet.set_column(col_num, col_num, min(column_len, 50))
        
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Failed to create Excel file: {e}")
        return None

def create_csv_download(df):
    """Create CSV for download"""
    return df.to_csv(index=False).encode('utf-8')

def export_data_options(df, base_filename):
    """Unified export UI component"""
    st.markdown("#### 📥 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = create_csv_download(df)
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"{base_filename}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        excel_data = create_excel_download(df, base_filename)
        if excel_data:
            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name=f"{base_filename}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

# -------------------------
# Data functions
# -------------------------

# Inpatients Function 
def load_inpatients(from_date, to_date, dept_name):
    # Build department filter
    if dept_name in (None, "", "All"):
        dept_filter = "1=1"
    else:
        # Get the department code for the selected department name
        try:
            dept_code_q = f"SELECT DEPTCODE FROM DEPARTMENT WHERE DEPTNAME = '{safe_sql(dept_name)}' AND ROWNUM = 1"
            dept_code_df = pd.read_sql(dept_code_q, conn)
            if not dept_code_df.empty:
                dept_code = dept_code_df['DEPTCODE'].iloc[0]
                dept_filter = f"I.DEPTCODE = '{safe_sql(dept_code)}'"
            else:
                dept_filter = "1=1"  # If dept not found, show all
        except:
            dept_filter = "1=1"
    
    # Hospital filter
    if selected_hospital in (None, "", "All Hospitals"):
        hosp_filter = "1=1"
    else:
        hosp_filter = f"I.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    q = (
        "SELECT I.INPATIENTID, I.MRN, I.DAYSCARED, I.ADMISSIONTYPE, I.DOA, P.DEATHDATE, I.DEPTCODE, I.HOSPITALID "
        "FROM INPATIENT I "
        "JOIN PATIENT P ON I.MRN = P.MRN "
        f"WHERE {dept_filter} AND {hosp_filter} "
        f"AND I.DOA BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
    )
    try:
        return pd.read_sql(q, conn)
    except Exception as e:
        st.error(f"Error loading inpatients: {e}")
        return pd.DataFrame()

# Outpatients Function
def load_outpatients(from_date, to_date, dept_name):
    # Build department filter
    if dept_name in (None, "", "All"):
        dept_filter = "1=1"
    else:
        dept_filter = f"O.DEPTNAME = '{safe_sql(dept_name)}'"
    
    # Hospital filter
    if selected_hospital in (None, "", "All Hospitals"):
        hosp_filter = "1=1"
    else:
        hosp_filter = f"O.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    q = (
        "SELECT O.OUTPATIENTID, O.MRN, O.DOV, O.DEPTNAME, O.HOSPITALID "
        "FROM OUTPATIENT O "
        f"WHERE {dept_filter} AND {hosp_filter} "
        f"AND O.DOV BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
    )
    try:
        return pd.read_sql(q, conn)
    except Exception as e:
        st.error(f"Error loading outpatients: {e}")
        return pd.DataFrame()
    
# Operational Efficiency Functions
def get_category_metrics(from_date, to_date, category_filter, ordering_dept):
    """
    Level 1: Get metrics for each CATEGORY.
    Returns list of dicts with CATEGORY, TOTAL, AVG_PER_DAY, MAX_ENTRY
    """
    sd_date_cond = f"THEDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
    sd_hosp_cond = "1=1" if selected_hospital in (None, "", "All Hospitals") else f"SD.HOSPITALID = '{safe_sql(selected_hospital)}'"

    sd_ordering_cond = "1=1"
    if ordering_dept not in (None, "", "All"):
        try:
            map_q = f"SELECT DEPTCODE FROM DEPARTMENT WHERE DEPTNAME = '{safe_sql(ordering_dept)}' AND ROWNUM = 1"
            mapped = pd.read_sql(map_q, conn)
            if not mapped.empty and mapped['DEPTCODE'].iloc[0] is not None:
                deptcode_val = mapped['DEPTCODE'].iloc[0]
                sd_ordering_cond = f"(SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}' OR SD.ORDERING_DEPT = '{safe_sql(deptcode_val)}')"
            else:
                sd_ordering_cond = f"SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}'"
        except Exception:
            sd_ordering_cond = f"SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}'"

    # Build CATEGORY filter
    if category_filter in (None, "", "All"):
        category_cond = "SD.CATEGORY IS NOT NULL"
    else:
        category_cond = f"SD.CATEGORY = '{safe_sql(category_filter)}'"

    try:
        # Get distinct categories
        category_q = (
            "SELECT DISTINCT CATEGORY FROM STATS_DETAILS SD "
            f"WHERE {sd_date_cond} AND {sd_hosp_cond} AND {category_cond} AND {sd_ordering_cond} "
            "AND CATEGORY IS NOT NULL "
            "ORDER BY CATEGORY"
        )
        category_df = pd.read_sql(category_q, conn)
        category_list = category_df["CATEGORY"].dropna().tolist() if not category_df.empty else []
    except Exception:
        category_list = []

    metrics = []
    for category in category_list:
        s_category = safe_sql(category)
        try:
            agg_q = (
                "SELECT SUM(NVL(THEVALUE,0)) AS TOTAL_CNT, MAX(NVL(THEVALUE,0)) AS MAX_ENTRY "
                "FROM STATS_DETAILS SD "
                f"WHERE SD.CATEGORY = '{s_category}' AND {sd_date_cond} AND {sd_hosp_cond} AND {sd_ordering_cond}"
            )
            agg_df = pd.read_sql(agg_q, conn)
            total_cnt = int(agg_df["TOTAL_CNT"].iloc[0]) if agg_df["TOTAL_CNT"].iloc[0] is not None else 0
            max_entry = int(agg_df["MAX_ENTRY"].iloc[0]) if agg_df["MAX_ENTRY"].iloc[0] is not None else 0
        except Exception:
            total_cnt = 0
            max_entry = 0
        
        days_range = (to_date - from_date).days + 1
        avg_per_day = (total_cnt / days_range) if days_range > 0 else 0.0
        metrics.append({
            "CATEGORY": category, 
            "TOTAL": total_cnt, 
            "AVG_PER_DAY": avg_per_day, 
            "MAX_ENTRY": max_entry
        })

    return metrics


def get_subcatg_metrics(category, from_date, to_date, ordering_dept):
    """
    Level 2: Get SUBCATG breakdown for a specific CATEGORY.
    Returns list of dicts with SUBCATG, TOTAL, AVG_PER_DAY, MAX_ENTRY
    """
    sd_date_cond = f"THEDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
    sd_hosp_cond = "1=1" if selected_hospital in (None, "", "All Hospitals") else f"SD.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    sd_ordering_cond = "1=1"
    if ordering_dept not in (None, "", "All"):
        try:
            map_q = f"SELECT DEPTCODE FROM DEPARTMENT WHERE DEPTNAME = '{safe_sql(ordering_dept)}' AND ROWNUM = 1"
            mapped = pd.read_sql(map_q, conn)
            if not mapped.empty and mapped['DEPTCODE'].iloc[0] is not None:
                deptcode_val = mapped['DEPTCODE'].iloc[0]
                sd_ordering_cond = f"(SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}' OR SD.ORDERING_DEPT = '{safe_sql(deptcode_val)}')"
            else:
                sd_ordering_cond = f"SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}'"
        except Exception:
            sd_ordering_cond = f"SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}'"

    try:
        q = (
            "SELECT SUBCATG, SUM(NVL(THEVALUE,0)) AS TOTAL_CNT, MAX(NVL(THEVALUE,0)) AS MAX_ENTRY "
            "FROM STATS_DETAILS SD "
            f"WHERE SD.CATEGORY = '{safe_sql(category)}' "
            f"AND {sd_date_cond} AND {sd_hosp_cond} AND {sd_ordering_cond} "
            "AND SUBCATG IS NOT NULL "
            "GROUP BY SUBCATG "
            "ORDER BY TOTAL_CNT DESC"
        )
        df = pd.read_sql(q, conn)
        
        days_range = (to_date - from_date).days + 1
        metrics = []
        for _, row in df.iterrows():
            total = int(row["TOTAL_CNT"])
            max_entry = int(row["MAX_ENTRY"])
            avg_per_day = (total / days_range) if days_range > 0 else 0.0
            metrics.append({
                "SUBCATG": row["SUBCATG"],
                "TOTAL": total,
                "AVG_PER_DAY": avg_per_day,
                "MAX_ENTRY": max_entry
            })
        return metrics
    except Exception:
        return []


def get_subcatgl2_metrics(category, subcatg, from_date, to_date, ordering_dept):
    """
    Level 3: Get SUBCATGL2 breakdown for a specific CATEGORY and SUBCATG.
    Returns list of dicts with SUBCATGL2, TOTAL, AVG_PER_DAY
    """
    sd_date_cond = f"THEDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
    sd_hosp_cond = "1=1" if selected_hospital in (None, "", "All Hospitals") else f"SD.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    sd_ordering_cond = "1=1"
    if ordering_dept not in (None, "", "All"):
        try:
            map_q = f"SELECT DEPTCODE FROM DEPARTMENT WHERE DEPTNAME = '{safe_sql(ordering_dept)}' AND ROWNUM = 1"
            mapped = pd.read_sql(map_q, conn)
            if not mapped.empty and mapped['DEPTCODE'].iloc[0] is not None:
                deptcode_val = mapped['DEPTCODE'].iloc[0]
                sd_ordering_cond = f"(SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}' OR SD.ORDERING_DEPT = '{safe_sql(deptcode_val)}')"
            else:
                sd_ordering_cond = f"SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}'"
        except Exception:
            sd_ordering_cond = f"SD.ORDERING_DEPT = '{safe_sql(ordering_dept)}'"

    try:
        q = (
            "SELECT SUBCATGL2, SUM(NVL(THEVALUE,0)) AS TOTAL_CNT "
            "FROM STATS_DETAILS SD "
            f"WHERE SD.CATEGORY = '{safe_sql(category)}' "
            f"AND SD.SUBCATG = '{safe_sql(subcatg)}' "
            f"AND {sd_date_cond} AND {sd_hosp_cond} AND {sd_ordering_cond} "
            "AND SUBCATGL2 IS NOT NULL "
            "GROUP BY SUBCATGL2 "
            "ORDER BY TOTAL_CNT DESC"
        )
        df = pd.read_sql(q, conn)
        
        days_range = (to_date - from_date).days + 1
        metrics = []
        for _, row in df.iterrows():
            total = int(row["TOTAL_CNT"])
            avg_per_day = (total / days_range) if days_range > 0 else 0.0
            metrics.append({
                "SUBCATGL2": row["SUBCATGL2"],
                "TOTAL": total,
                "AVG_PER_DAY": avg_per_day
            })
        return metrics
    except Exception:
        return []
    
def build_category_pdf(category, from_date, to_date, ordering_dept):
    """Generate multi-page PDF: one section per SUBCATG with full SUBCATGL2 table"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=0.6*inch, rightMargin=0.6*inch,
                            topMargin=0.8*inch, bottomMargin=0.8*inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=16, leading=18, spaceAfter=12))
    styles.add(ParagraphStyle(name='SubHeader', fontSize=12, leading=14, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=10))

    elements = []

    # Title
    title = Paragraph(f"<b>Operational Efficiency Report – CATEGORY: {category}</b>", styles['Center'])
    subtitle = Paragraph(f"<b>Date Range:</b> {from_date} to {to_date} | <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
    elements.extend([title, subtitle, Spacer(1, 0.3*inch)])

    # Get SUBCATG list
    subcatg_metrics = get_subcatg_metrics(category, from_date, to_date, ordering_dept)
    if not subcatg_metrics:
        elements.append(Paragraph("No data available for this category.", styles['Normal']))
    else:
        days = (to_date - from_date).days + 1

        for idx, sub in enumerate(subcatg_metrics):
            subcatg_name = sub['SUBCATG']
            total_sub = sub['TOTAL']
            avg_sub = sub['AVG_PER_DAY']

            # SUBCATG Header
            elements.append(Paragraph(f"<b>SUBCATG:</b> {subcatg_name}", styles['SubHeader']))
            elements.append(Paragraph(f"Total: <b>{total_sub:,}</b> | Avg/Day: <b>{avg_sub:.2f}</b>", styles['Normal']))
            elements.append(Spacer(1, 0.15*inch))

            # SUBCATGL2 Table
            subcatgl2 = get_subcatgl2_metrics(category, subcatg_name, from_date, to_date, ordering_dept)
            if not subcatgl2:
                elements.append(Paragraph("<i>No SUBCATGL2 details available.</i>", styles['Normal']))
            else:
                df_sub = pd.DataFrame(subcatgl2)
                df_sub['AVG_PER_DAY'] = df_sub['AVG_PER_DAY'].round(2)
                df_sub = df_sub.sort_values('TOTAL', ascending=False).reset_index(drop=True)
                df_sub.insert(0, 'Rank', range(1, len(df_sub) + 1))

                data = [['Rank', 'SUBCATGL2', 'Total', 'Avg/Day']]
                for _, row in df_sub.iterrows():
                    data.append([
                        str(row['Rank']),
                        str(row['SUBCATGL2']),
                        f"{row['TOTAL']:,}",
                        f"{row['AVG_PER_DAY']:.2f}"
                    ])

                table = Table(data, colWidths=[0.6*inch, 2.8*inch, 1.0*inch, 1.0*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0ea77c')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                ]))
                elements.append(table)

            # Page break (except last)
            if idx < len(subcatg_metrics) - 1:
                elements.append(PageBreak())

    # Footer: Page Numbers
    def add_page_number(canvas, doc):
        canvas.saveState()
        page_num = Paragraph(f"Page {doc.page}", styles['Right'])
        page_num.wrap(doc.width, doc.bottomMargin)
        page_num.drawOn(canvas, doc.leftMargin, 0.4*inch)
        canvas.restoreState()

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    buffer.seek(0)
    return buffer.getvalue()
    
# Bed Occupancy Analysis Functions
def calculate_bed_occupancy(from_date, to_date, dept_name=None, location_filter=None):
    """Calculate bed occupancy with proper department filtering"""
    try:
        # Build bed query with filters
        bed_query = """
            SELECT 
                SPECIALITY,
                LOCATION,
                NVL(BEDSTRENGTH, 0) AS BEDSTRENGTH
            FROM BEDMASTER
            WHERE STATUS = 'A'
        """
        
        bed_conditions = []
        
        # Department filter - map DEPTNAME to SPECIALITY in BEDMASTER
        if dept_name and dept_name not in (None, "", "All"):
            bed_conditions.append(f"SPECIALITY = '{safe_sql(dept_name)}'")
        
        # Location filter
        if location_filter and location_filter not in (None, "", "All"):
            bed_conditions.append(f"LOCATION = '{safe_sql(location_filter)}'")
        
        if bed_conditions:
            bed_query += " AND " + " AND ".join(bed_conditions)
        
        bed_df = pd.read_sql(bed_query, conn)
        total_beds = int(bed_df['BEDSTRENGTH'].sum()) if not bed_df.empty else 0
        
        if total_beds == 0:
            return 0.0, 0.0, 0, pd.DataFrame()
        
        # Rest of the function remains the same...
        
        # Build census query with matching logic
        # CENSUSDATA.SPECIALITY should match BEDMASTER.LOCATION
        census_query = f"""
            SELECT 
                THEDATE,
                SPECIALITY,
                NVL(OPBAL, 0) AS OPBAL,
                NVL(ADMIT, 0) AS ADMIT,
                NVL(DISCH, 0) AS DISCH,
                NVL(TRIN, 0) AS TRIN,
                NVL(TROUT, 0) AS TROUT,
                NVL(DEATH, 0) AS DEATH,
                (NVL(OPBAL, 0) + NVL(ADMIT, 0) - NVL(DISCH, 0) + NVL(TRIN, 0) - NVL(TROUT, 0) - NVL(DEATH, 0)) AS DAILY_OCCUPANCY
            FROM CENSUSDATA
            WHERE THEDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') 
                              AND TO_DATE('{to_date}', 'YYYY-MM-DD')
        """
        
        census_conditions = []
        
        # Match CENSUSDATA.SPECIALITY with BEDMASTER.LOCATION
        if location_filter and location_filter not in (None, "", "All"):
            census_conditions.append(f"SPECIALITY = '{safe_sql(location_filter)}'")
        elif dept_name and dept_name not in (None, "", "All"):
            # Get all locations for this department
            dept_locations = bed_df[bed_df['SPECIALITY'] == dept_name]['LOCATION'].tolist()
            if dept_locations:
                location_list = "', '".join([safe_sql(loc) for loc in dept_locations])
                census_conditions.append(f"SPECIALITY IN ('{location_list}')")
        
        if census_conditions:
            census_query += " AND " + " AND ".join(census_conditions)
        
        census_query += " ORDER BY THEDATE, SPECIALITY"
        
        census_df = pd.read_sql(census_query, conn)
        
        if census_df.empty:
            return 0.0, 0.0, total_beds, pd.DataFrame()
        
        # Calculate metrics
        total_patient_days = census_df['DAILY_OCCUPANCY'].sum()
        days_in_period = (to_date - from_date).days + 1
        available_bed_days = total_beds * days_in_period
        
        occupancy_rate = (total_patient_days / available_bed_days * 100) if available_bed_days > 0 else 0.0
        avg_daily_census = total_patient_days / days_in_period if days_in_period > 0 else 0.0
        
        # Return detail dataframe for drill-down
        return round(occupancy_rate, 2), round(avg_daily_census, 1), total_beds, census_df
        
    except Exception as e:
        st.error(f"Error calculating bed occupancy: {e}")
        return 0.0, 0.0, 0, pd.DataFrame()

def get_department_occupancy_breakdown(from_date, to_date):
    """Get bed occupancy breakdown by department"""
    try:
        # Get all departments from BEDMASTER
        dept_query = """
            SELECT DISTINCT SPECIALITY
            FROM BEDMASTER
            WHERE STATUS = 'A' AND SPECIALITY IS NOT NULL
            ORDER BY SPECIALITY
        """
        dept_df = pd.read_sql(dept_query, conn)
        
        results = []
        for dept in dept_df['SPECIALITY']:
            rate, avg_census, beds, _ = calculate_bed_occupancy(from_date, to_date, dept_name=dept)
            results.append({
                'DEPARTMENT': dept,
                'TOTAL_BEDS': beds,
                'AVG_CENSUS': avg_census,
                'OCCUPANCY_RATE': rate
            })
        
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"Error getting department breakdown: {e}")
        return pd.DataFrame()

def get_location_occupancy_breakdown(from_date, to_date, dept_name=None):
    """Get bed occupancy breakdown by location (ward/ICU level)"""
    try:
        # Get locations from BEDMASTER
        loc_query = """
            SELECT 
                SPECIALITY AS DEPARTMENT,
                LOCATION,
                BEDSTRENGTH
            FROM BEDMASTER
            WHERE STATUS = 'A'
        """
        
        if dept_name and dept_name not in (None, "", "All"):
            loc_query += f" AND SPECIALITY = '{safe_sql(dept_name)}'"
        
        loc_query += " ORDER BY SPECIALITY, LOCATION"
        
        loc_df = pd.read_sql(loc_query, conn)
        
        results = []
        for _, row in loc_df.iterrows():
            rate, avg_census, beds, _ = calculate_bed_occupancy(
                from_date, to_date, 
                dept_name=row['DEPARTMENT'], 
                location_filter=row['LOCATION']
            )
            results.append({
                'DEPARTMENT': row['DEPARTMENT'],
                'LOCATION': row['LOCATION'],
                'TOTAL_BEDS': row['BEDSTRENGTH'],
                'AVG_CENSUS': avg_census,
                'OCCUPANCY_RATE': rate
            })
        
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"Error getting location breakdown: {e}")
        return pd.DataFrame()
    
# Stats Age Distribution Function
def compute_age_distribution():
    try:
        q = "SELECT TRUNC(MONTHS_BETWEEN(SYSDATE, DOB) / 12) AS AGE FROM PATIENT WHERE DOB IS NOT NULL"
        df = pd.read_sql(q, conn)
        if df.empty:
            return None, pd.DataFrame(columns=['AGE_GROUP','CNT'])
        avg_age = df['AGE'].mean()
        bins = [0,20,40,60,80,200]
        labels = ['0-19','20-39','40-59','60-79','80+']
        df['AGE_GROUP'] = pd.cut(df['AGE'], bins=bins, labels=labels, right=False)
        age_dist = df.groupby('AGE_GROUP').size().reset_index(name='CNT')
        return avg_age, age_dist
    except Exception:
        return None, pd.DataFrame(columns=['AGE_GROUP','CNT'])

# Stats Admission Type Breakdown Functions
def admission_type_breakdown(from_date, to_date, dept_name):
    # Build department filter
    if dept_name in (None, "", "All"):
        dept_filter = "1=1"
    else:
        try:
            dept_code_q = f"SELECT DEPTCODE FROM DEPARTMENT WHERE DEPTNAME = '{safe_sql(dept_name)}' AND ROWNUM = 1"
            dept_code_df = pd.read_sql(dept_code_q, conn)
            if not dept_code_df.empty:
                dept_code = dept_code_df['DEPTCODE'].iloc[0]
                dept_filter = f"I.DEPTCODE = '{safe_sql(dept_code)}'"
            else:
                dept_filter = "1=1"
        except:
            dept_filter = "1=1"
    
    # Hospital filter
    if selected_hospital in (None, "", "All Hospitals"):
        hosp_filter = "1=1"
    else:
        hosp_filter = f"I.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    q = (
        "SELECT NVL(ADMISSIONTYPE,'UNKNOWN') AS ADMISSIONTYPE, COUNT(*) AS CNT "
        "FROM INPATIENT I "
        f"WHERE {dept_filter} AND {hosp_filter} "
        f"AND I.DOA BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD') "
        "GROUP BY NVL(ADMISSIONTYPE,'UNKNOWN') ORDER BY CNT DESC"
    )
    try:
        return pd.read_sql(q, conn)
    except Exception:
        return pd.DataFrame(columns=['ADMISSIONTYPE','CNT'])

# Stats State Metrics Function
def state_stats_aggregate(from_date, to_date, use_year_month=False, sel_year=None, sel_month=None):
    base_where = "1=1"
    if selected_hospital not in (None, '', 'All Hospitals'):
        base_where = f"HOSPITALID = '{safe_sql(selected_hospital)}'"

    if use_year_month:
        year = sel_year
        month = sel_month
        ss_q = (
            "SELECT STATE, SUM(CNT) AS CNT FROM STATESTATS "
            f"WHERE {base_where} AND THEYR = {year} AND THEMNTH = {month} "
            "GROUP BY STATE ORDER BY CNT DESC"
        )
        try:
            ss_df = pd.read_sql(ss_q, conn)
            return ss_df
        except Exception:
            return pd.DataFrame(columns=['STATE','CNT'])
    else:
        try:
            ss_q = f"SELECT THEYR, THEMNTH, STATE, CNT FROM STATESTATS WHERE {base_where}"
            ss_df = pd.read_sql(ss_q, conn)
            if ss_df.empty:
                return pd.DataFrame(columns=['STATE','CNT'])
            ss_df['THEDATE'] = pd.to_datetime(ss_df['THEYR'].astype(int).astype(str) + '-' + ss_df['THEMNTH'].astype(int).astype(str) + '-01')
            mask = (ss_df['THEDATE'].dt.date >= pd.to_datetime(from_date).date()) & (ss_df['THEDATE'].dt.date <= pd.to_datetime(to_date).date())
            ss_df = ss_df.loc[mask]
            state_agg = ss_df.groupby('STATE', as_index=False)['CNT'].sum().sort_values('CNT', ascending=False)
            return state_agg
        except Exception:
            return pd.DataFrame(columns=['STATE','CNT'])

def read_staff_patient_ratio():
    candidates = ["STAFF_PATIENT_RATIO", "STAFF_PATIENT"]
    for tab in candidates:
        try:
            q = f"SELECT * FROM {tab} FETCH FIRST 1 ROWS ONLY"
            df = pd.read_sql(q, conn)
            if not df.empty:
                return df
        except Exception:
            continue
    return None

# Reports tab functions
def search_mrns(prefix: str, limit: int = 100):
    """Return up to `limit` MRNs from NOTESDATA that match the prefix (case-insensitive)."""
    if prefix is None:
        return []
    safe_prefix = safe_sql(prefix.strip())
    if safe_prefix == "":
        return []
    like_val = f"%{safe_prefix}%"
    q = f"SELECT DISTINCT MRN FROM NOTESDATA WHERE MRN LIKE '{like_val}' AND ROWNUM <= {limit} ORDER BY MRN"
    try:
        df = pd.read_sql(q, conn)
        return df['MRN'].dropna().tolist() if not df.empty else []
    except Exception:
        return []

def fetch_reports_for_mrn(mrn: str):
    """Return DataFrame of reports for a given MRN."""
    if not mrn:
        return pd.DataFrame()
    safe_mrn = safe_sql(mrn)
    q = (
        "SELECT ACCESSION_NUM, NOTENAME, VISITTYPE, VISITDATE, DONEBY, DEPTNAME, NOTEDATA "
        "FROM NOTESDATA "
        f"WHERE MRN = '{safe_mrn}' "
        "ORDER BY NVL(VISITDATE, TO_DATE('1900-01-01','YYYY-MM-DD')) DESC"
    )
    try:
        df = pd.read_sql(q, conn)
        expected_cols = ['ACCESSION_NUM','NOTENAME','VISITTYPE','VISITDATE','DONEBY','DEPTNAME','NOTEDATA']
        for c in expected_cols:
            if c not in df.columns:
                df[c] = None
        return df[expected_cols]
    except Exception:
        return pd.DataFrame(columns=['ACCESSION_NUM','NOTENAME','VISITTYPE','VISITDATE','DONEBY','DEPTNAME','NOTEDATA'])

def build_report_label(row):
    """Produce a friendly label for a report in multi-select: accession | name | date"""
    acc = str(row.get('ACCESSION_NUM','')) if pd.notna(row.get('ACCESSION_NUM',None)) else ''
    name = row.get('NOTENAME','') if pd.notna(row.get('NOTENAME',None)) else ''
    date_val = row.get('VISITDATE',None)
    if pd.isna(date_val) or date_val is None:
        date_str = ''
    else:
        if isinstance(date_val, str):
            date_str = date_val
        elif isinstance(date_val, (datetime, pd.Timestamp)):
            date_str = date_val.strftime('%Y-%m-%d')
        else:
            date_str = str(date_val)
    label = f"{acc} | {name} | {date_str}"
    return label

def create_zip_of_reports(reports_df: pd.DataFrame, selected_accessions: list):
    """Create a ZIP in-memory with one .html file per selected accession. Returns bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for acc in selected_accessions:
            row = reports_df[reports_df['ACCESSION_NUM'] == acc]
            if row.empty:
                continue
            html_content = row.iloc[0].get('NOTEDATA', '') or ''
            fname = f"{str(acc)}.html"
            zf.writestr(fname, html_content)
    buf.seek(0)
    return buf.read()

# Surgery Details Functions
def load_surgery_metrics(from_date, to_date, dept_name, surgeon_id):
    surg_dept_filter = "1=1" if dept_name in (None, "", "All") else f"D.DEPTNAME = '{safe_sql(dept_name)}'"
    
    # Fixed hospital filter
    if selected_hospital in (None, "", "All Hospitals"):
        surg_hosp_filter = "1=1"
    else:
        surg_hosp_filter = f"S.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    surg_date_cond = f"S.SURGERYDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"

    # total surgeries
    try:
        total_q = (
            "SELECT COUNT(*) AS CNT FROM SURGERY S JOIN DEPARTMENT D ON S.DEPTCODE = D.DEPTCODE AND S.HOSPITALID = D.HOSPITALID "
            f"WHERE {surg_date_cond} AND {surg_dept_filter} AND {surg_hosp_filter}"
        )
        total = int(pd.read_sql(total_q, conn)["CNT"].iloc[0])
    except Exception:
        total = 0

    # by surgeon
    if surgeon_id:
        try:
            bydoc_q = (
                "SELECT COUNT(*) AS CNT FROM SURGERY S JOIN DEPARTMENT D ON S.DEPTCODE = D.DEPTCODE AND S.HOSPITALID = D.HOSPITALID "
                f"WHERE {surg_date_cond} AND {surg_dept_filter} AND {surg_hosp_filter} AND S.SURGEONID = '{safe_sql(surgeon_id)}'"
            )
            bydoc = int(pd.read_sql(bydoc_q, conn)["CNT"].iloc[0])
        except Exception:
            bydoc = 0
    else:
        bydoc = None

    # top surgery type
    try:
        top_q = (
            "SELECT NVL(SURGERYTYPE,'UNKNOWN') AS SURGERYTYPE, COUNT(*) AS CNT "
            "FROM SURGERY S JOIN DEPARTMENT D ON S.DEPTCODE = D.DEPTCODE AND S.HOSPITALID = D.HOSPITALID "
            f"WHERE {surg_date_cond} AND {surg_dept_filter} AND {surg_hosp_filter} "
            "GROUP BY NVL(SURGERYTYPE,'UNKNOWN') ORDER BY CNT DESC"
        )
        top_df = pd.read_sql(top_q, conn)
        top_type = top_df["SURGERYTYPE"].iloc[0] if not top_df.empty else "N/A"
    except Exception:
        top_type = "N/A"

    days = (to_date - from_date).days + 1
    daily_avg = (total / days) if days > 0 else 0.0

    return {"total": total, "bydoc": bydoc, "top_type": top_type, "daily_avg": daily_avg}

# ========================================
# CUSTOM METRICS MANAGER
# ========================================
class CustomMetricsManager:
    def __init__(self, config_dir="custom_metrics"):
        """Initialize the custom metrics manager"""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.metrics_file = self.config_dir / "saved_metrics.json"
        self.templates_dir = self.config_dir / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
    def parse_metric_file(self, file_content):
        """Parse a metric definition file"""
        lines = file_content.strip().split('\n')
        metric_def = {
            'name': '',
            'icon': '📊',
            'color': 'kpi-grad-1',
            'description': '',
            'query': '',
            'type': 'single_value',  # NEW: default type
            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        query_started = False
        query_lines = []
        
        for line in lines:
            line = line.strip()
            
            if query_started:
                query_lines.append(line)
            elif line.startswith('METRIC_NAME:'):
                metric_def['name'] = line.split('METRIC_NAME:', 1)[1].strip()
            elif line.startswith('METRIC_ICON:'):
                metric_def['icon'] = line.split('METRIC_ICON:', 1)[1].strip()
            elif line.startswith('METRIC_COLOR:'):
                metric_def['color'] = line.split('METRIC_COLOR:', 1)[1].strip()
            elif line.startswith('METRIC_TYPE:'):  # NEW: optional type specification
                metric_def['type'] = line.split('METRIC_TYPE:', 1)[1].strip().lower()
            elif line.startswith('DESCRIPTION:'):
                metric_def['description'] = line.split('DESCRIPTION:', 1)[1].strip()
            elif line.startswith('QUERY:'):
                query_started = True
        
        metric_def['query'] = '\n'.join(query_lines).strip()
        
        if not metric_def['name']:
            raise ValueError("METRIC_NAME is required")
        if not metric_def['query']:
            raise ValueError("QUERY is required")
            
        return metric_def
    
    def save_metric(self, metric_def):
        """Save a metric definition to persistent storage"""
        metrics = self.load_saved_metrics()
        metric_id = metric_def['name'].lower().replace(' ', '_')
        metrics[metric_id] = metric_def
        
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        return metric_id
    
    def load_saved_metrics(self):
        """Load all saved metrics from storage"""
        if not self.metrics_file.exists():
            return {}
        
        try:
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def delete_metric(self, metric_id):
        """Delete a saved metric"""
        metrics = self.load_saved_metrics()
        if metric_id in metrics:
            del metrics[metric_id]
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            return True
        return False
    
    def execute_metric_query(self, query, conn, from_date=None, to_date=None, 
                            selected_hospital=None, selected_dept=None):
        """
        FIXED: Execute a metric query with parameter substitution
        Now supports both single values and tables
        """
        if from_date:
            query = query.replace('{from_date}', str(from_date))
        if to_date:
            query = query.replace('{to_date}', str(to_date))
        if selected_hospital:
            query = query.replace('{hospital}', str(selected_hospital))
        if selected_dept:
            query = query.replace('{dept}', str(selected_dept))
        
        try:
            result = pd.read_sql(query, conn)
            
            # FIXED: Check if this is a table result (multiple rows or columns)
            if len(result) > 1 or len(result.columns) > 1:
                return result  # Return DataFrame for tables
            
            # Single value result
            if 'VALUE' in result.columns:
                return result['VALUE'].iloc[0]
            else:
                return result.iloc[0, 0]
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def create_sample_template(self):
        """FIXED: Create a sample metric template file with both types"""
        sample = """METRIC_NAME: Total Active Patients
                    METRIC_ICON: 👥
                    METRIC_COLOR: kpi-grad-1
                    METRIC_TYPE: single_value
                    DESCRIPTION: Count of all active patients in the system
                    QUERY:
                        SELECT COUNT(*) as VALUE
                        FROM PATIENT
                        WHERE STATUS = 'A'
                        ---

                    Example for TABLE metric:

                    METRIC_NAME: Top Departments by Patient Count
                    METRIC_ICON: 🏥
                    METRIC_COLOR: kpi-grad-2
                    METRIC_TYPE: table
                    DESCRIPTION: Shows patient distribution across departments
                    QUERY:
                        SELECT 
                            DEPTNAME as Department,
                            COUNT(*) as Patient_Count,
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as Percentage
                        FROM INPATIENT i
                        JOIN DEPARTMENT d ON i.DEPTCODE = d.DEPTCODE
                        WHERE i.DOA BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') 
                                        AND TO_DATE('{to_date}', 'YYYY-MM-DD')
                        GROUP BY DEPTNAME
                        ORDER BY Patient_Count DESC
                        FETCH FIRST 10 ROWS ONLY
                        """
        template_file = self.templates_dir / "sample_metric.txt"
        with open(template_file, 'w') as f:
            f.write(sample)
        return template_file

# ========================================
# RENDER FUNCTION - FIXED FOR PERMISSIONS
# ========================================

def render_custom_metrics_ui(conn, from_date, to_date, selected_hospital, selected_dept):
    """
    FIXED: Render the custom metrics UI in Streamlit
    Now supports role-based access:
    - Admins: Can view, add, and manage metrics
    - Users: Can only view metrics
    """
    #st.header("🎯 Custom Metrics Manager")
   
    manager = CustomMetricsManager()
    is_admin = st.session_state.get("role") == "admin"
   
    # FIXED: Show different tabs based on role
    if is_admin:
        tab1, tab2, tab3 = st.tabs(["📊 View Metrics", "➕ Add New Metric", "⚙️ Manage Metrics"])
    else:
        # Non-admin users only see View Metrics - create a single tab list
        tabs_list = st.tabs(["📊 View Metrics"])
        tab1 = tabs_list[0]
   
    # ============================================
    # TAB 1: VIEW METRICS (Available to all users)
    # ============================================
    with tab1:
        # Show info for non-admin users
        if not is_admin:
            st.info("💡 Only administrators can add or manage custom metrics. Contact your admin to create new metrics.")
    
        st.subheader("Active Custom Metrics")
    
        saved_metrics = manager.load_saved_metrics()
    
        if not saved_metrics:
            if is_admin:
                st.info("📭 No custom metrics saved yet. Go to 'Add New Metric' tab to create one!")
            else:
                st.info("📭 No custom metrics available yet. Ask an administrator to create metrics.")
        else:
            # FIXED: Add a "Refresh Metrics" button to control when queries execute
            if st.button("🔄 Refresh All Metrics", key="refresh_metrics_btn", type="primary"):
                st.session_state.metrics_refreshed = True
            
            if st.session_state.get("metrics_refreshed", False):
                metrics_per_row = 3
                metric_items = list(saved_metrics.items())
            
                for i in range(0, len(metric_items), metrics_per_row):
                    cols = st.columns(metrics_per_row)
                
                    for j in range(metrics_per_row):
                        idx = i + j
                        if idx >= len(metric_items):
                            break
                    
                        metric_id, metric_def = metric_items[idx]
                    
                        with cols[j]:
                            with st.container():
                                st.markdown(f"### {metric_def['icon']} {metric_def['name']}")
                            
                                try:
                                    # Show loading spinner for each metric
                                    with st.spinner(f"Loading {metric_def['name']}..."):
                                        result = manager.execute_metric_query(
                                            metric_def['query'],
                                            conn,
                                            from_date=from_date,
                                            to_date=to_date,
                                            selected_hospital=selected_hospital,
                                            selected_dept=selected_dept
                                        )
                                
                                    # Check if result is a DataFrame (table) or single value
                                    if isinstance(result, pd.DataFrame):
                                        st.caption(metric_def['description'])
                                        st.dataframe(result, use_container_width=True, height=300)
                                        st.caption(f"📊 {len(result)} rows returned")
                                    else:
                                        # Single value
                                        if isinstance(result, (int, float)):
                                            if isinstance(result, float):
                                                display_value = f"{result:,.2f}"
                                            else:
                                                display_value = f"{result:,}"
                                        else:
                                            display_value = str(result)
                                    
                                        st.metric(label=metric_def['name'], value=display_value)
                                        st.caption(metric_def['description'])
                                
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                    st.caption(metric_def['description'])
            else:
                st.info("👆 Click 'Refresh All Metrics' button above to load custom metrics data.")
                st.write(f"**{len(saved_metrics)} custom metrics** available")
   
    # ============================================
    # TAB 2 & 3: ADD NEW METRIC & MANAGE (Admin only)
    # ============================================
    if is_admin:
        with tab2:
            st.subheader("➕ Create New Custom Metric")
           
            st.info("""
            📝 **How to create a metric:**
            1. Upload a text file with metric definition, OR
            2. Use the form below to create one
           
            **Metric Types:**
            - **Single Value**: Returns one number (e.g., COUNT, SUM, AVG)
            - **Table**: Returns multiple rows of data
           
            **Supported placeholders in queries:**
            - `{from_date}` - Start date from filters
            - `{to_date}` - End date from filters
            - `{hospital}` - Selected hospital
            - `{dept}` - Selected department
            """)
           
            st.markdown("#### Option 1: Upload Metric File")
            uploaded_file = st.file_uploader("Upload metric definition (.txt)", type=['txt'], key="metric_upload")
           
            if uploaded_file:
                try:
                    file_content = uploaded_file.read().decode('utf-8')
                    metric_def = manager.parse_metric_file(file_content)
                   
                    st.success(f"✅ Parsed metric: **{metric_def['name']}**")
                    st.json(metric_def)
                   
                    if st.button("💾 Save This Metric", key="save_uploaded"):
                        metric_id = manager.save_metric(metric_def)
                        st.success(f"✅ Metric saved with ID: {metric_id}")
                        st.balloons()
                        st.rerun()
                       
                except Exception as e:
                    st.error(f"❌ Error parsing file: {str(e)}")
           
            st.markdown("---")
            st.markdown("#### Option 2: Create Using Form")
           
            with st.form("new_metric_form"):
                metric_name = st.text_input("Metric Name*", placeholder="e.g., Total Revenue")
               
                col1, col2 = st.columns(2)
                with col1:
                    metric_icon = st.text_input("Icon (emoji)", value="📊")
                with col2:
                    color_options = ["kpi-grad-1", "kpi-grad-2", "kpi-grad-3", "kpi-grad-4",
                                    "kpi-grad-5", "kpi-grad-6", "kpi-grad-7", "kpi-grad-8"]
                    metric_color = st.selectbox("Color Theme", color_options)
               
                metric_type = st.radio(
                    "Metric Type*",
                    options=["Single Value", "Table"],
                    help="Single Value: Shows one number. Table: Shows multiple rows of data."
                )
               
                metric_desc = st.text_area("Description", placeholder="What does this metric measure?")
               
                if metric_type == "Single Value":
                    query_placeholder = """SELECT COUNT(*) as VALUE
                                            FROM YOUR_TABLE
                                            WHERE DATE_COLUMN BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD')
                                            AND TO_DATE('{to_date}', 'YYYY-MM-DD')"""
                    query_help = "Query must return a single value. Use column name 'VALUE' or it will use first column."
                else:
                    query_placeholder = """SELECT
                                                COLUMN1,
                                                COLUMN2,
                                                COUNT(*) as COUNT
                                            FROM YOUR_TABLE
                                            WHERE DATE_COLUMN BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD')
                                            AND TO_DATE('{to_date}', 'YYYY-MM-DD')
                                            GROUP BY COLUMN1, COLUMN2
                                            ORDER BY COUNT DESC"""
                    query_help = "Query can return multiple rows and columns. Results will be displayed as a table."
               
                metric_query = st.text_area(
                    "SQL Query*",
                    placeholder=query_placeholder,
                    height=200
                )
               
                st.caption(f"⚠️ {query_help}")
               
                submitted = st.form_submit_button("💾 Save Metric")
               
                if submitted:
                    if not metric_name or not metric_query:
                        st.error("❌ Metric Name and Query are required!")
                    else:
                        metric_def = {
                            'name': metric_name,
                            'icon': metric_icon,
                            'color': metric_color,
                            'description': metric_desc,
                            'query': metric_query,
                            'type': metric_type.lower().replace(" ", "_"),
                            'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                       
                        try:
                            metric_id = manager.save_metric(metric_def)
                            st.success(f"✅ Metric '{metric_name}' saved successfully!")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error saving metric: {str(e)}")
           
            st.markdown("---")
            st.markdown("#### 📥 Download Sample Template")
            if st.button("Download Sample Metric Template"):
                template_file = manager.create_sample_template()
                with open(template_file, 'r') as f:
                    st.download_button(
                        label="📄 Download sample_metric.txt",
                        data=f.read(),
                        file_name="sample_metric.txt",
                        mime="text/plain"
                    )
       
        # ============================================
        # TAB 3: MANAGE METRICS (Admin only)
        # ============================================
        with tab3:
            st.subheader("⚙️ Manage Saved Metrics")
           
            saved_metrics = manager.load_saved_metrics()
           
            if not saved_metrics:
                st.info("No metrics to manage.")
            else:
                for metric_id, metric_def in saved_metrics.items():
                    with st.expander(f"{metric_def['icon']} {metric_def['name']}", expanded=False):
                        st.markdown(f"**ID:** `{metric_id}`")
                        st.markdown(f"**Type:** {metric_def.get('type', 'single_value').replace('_', ' ').title()}")
                        st.markdown(f"**Description:** {metric_def['description']}")
                        st.markdown(f"**Created:** {metric_def.get('created_date', 'N/A')}")
                       
                        st.code(metric_def['query'], language='sql')
                       
                        col1, col2, col3 = st.columns(3)
                       
                        with col1:
                            if st.button("🧪 Test Query", key=f"test_{metric_id}"):
                                try:
                                    result = manager.execute_metric_query(
                                        metric_def['query'],
                                        conn,
                                        from_date=from_date,
                                        to_date=to_date,
                                        selected_hospital=selected_hospital,
                                        selected_dept=selected_dept
                                    )
                                   
                                    if isinstance(result, pd.DataFrame):
                                        st.success(f"✅ Table Result: {len(result)} rows")
                                        st.dataframe(result)
                                    else:
                                        st.success(f"✅ Result: **{result}**")
                                except Exception as e:
                                    st.error(f"❌ Query failed: {str(e)}")
                       
                        with col2:
                            file_content = f"""METRIC_NAME: {metric_def['name']}
                                            METRIC_ICON: {metric_def['icon']}
                                            METRIC_COLOR: {metric_def['color']}
                                            METRIC_TYPE: {metric_def.get('type', 'single_value')}
                                            DESCRIPTION: {metric_def['description']}
                                            QUERY:
                                            {metric_def['query']}
                                            """
                            st.download_button(
                                label="📥 Download",
                                data=file_content,
                                file_name=f"{metric_id}.txt",
                                mime="text/plain",
                                key=f"download_{metric_id}"
                            )
                       
                        with col3:
                            if st.button("🗑️ Delete", key=f"delete_{metric_id}", type="secondary"):
                                if manager.delete_metric(metric_id):
                                    st.success(f"✅ Deleted {metric_def['name']}")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete")

# ========================================
# DISPLAY FUNCTION - FIXED FOR TABLES
# ========================================
def display_custom_metrics_row(conn, from_date, to_date, selected_hospital, selected_dept, kpi_card_html):
    """
    FIXED: Display custom metrics in a row
    Now supports both single values and tables
    """
    manager = CustomMetricsManager()
    saved_metrics = manager.load_saved_metrics()
    
    if saved_metrics:
        st.markdown("---")
        st.subheader("🎯 Custom Metrics")
        
        metrics_per_row = 4
        metric_items = list(saved_metrics.items())
        
        for i in range(0, len(metric_items), metrics_per_row):
            cols = st.columns(metrics_per_row)
            
            for j in range(metrics_per_row):
                idx = i + j
                if idx >= len(metric_items):
                    break
                
                metric_id, metric_def = metric_items[idx]
                
                with cols[j]:
                    try:
                        result = manager.execute_metric_query(
                            metric_def['query'],
                            conn,
                            from_date=from_date,
                            to_date=to_date,
                            selected_hospital=selected_hospital,
                            selected_dept=selected_dept
                        )
                        
                        # FIXED: Check if result is a DataFrame (table)
                        if isinstance(result, pd.DataFrame):
                            # For tables, show row count as the metric
                            display_value = f"{len(result)} rows"
                            st.markdown(
                                kpi_card_html(
                                    metric_def['name'],
                                    display_value,
                                    f"📊 {metric_def['description'][:30]}...",
                                    metric_def['color'],
                                    metric_def['icon']
                                ),
                                unsafe_allow_html=True
                            )
                            with st.expander("View Details"):
                                st.dataframe(result, use_container_width=True)
                        else:
                            # Single value
                            if isinstance(result, (int, float)):
                                if isinstance(result, float):
                                    display_value = f"{result:,.2f}"
                                else:
                                    display_value = f"{result:,}"
                            else:
                                display_value = str(result)
                            
                            st.markdown(
                                kpi_card_html(
                                    metric_def['name'],
                                    display_value,
                                    metric_def['description'],
                                    metric_def['color'],
                                    metric_def['icon']
                                ),
                                unsafe_allow_html=True
                            )
                        
                    except Exception as e:
                        st.markdown(
                            kpi_card_html(
                                metric_def['name'],
                                "Error",
                                str(e)[:50],
                                "kpi-grad-5",
                                "⚠️"
                            ),
                            unsafe_allow_html=True
                        )

# -------------------------
# Tabs and rendering
# -------------------------
tabs = st.tabs(["🏠 General KPIs", "⚡ Operational Efficiency", "💰 Financial", 
                "✅ Quality & Safety", "📄 Reports", "📊 Stats", "🎯 Custom Metrics",
                "🩺 Surgery Details"
                ])  # Added new tab

# ---- TAB 0: General KPIs ----
with tabs[0]:
    st.header("General KPIs")
    in_df = load_inpatients(from_date, to_date, selected_dept)
    out_df = load_outpatients(from_date, to_date, selected_dept)

    total_inpatients = len(in_df)
    total_outpatients = len(out_df)

    try:
        alos = float(in_df["DAYSCARED"].fillna(0).astype(float).mean()) if total_inpatients else 0.0
    except Exception:
        alos = 0.0

    # mortality
    try:
        if not in_df.empty:
            def died_in_range(d):
                if pd.isna(d):
                    return False
                if isinstance(d, datetime):
                    d = d.date()
                return (from_date <= d <= to_date)
            deaths = in_df["DEATHDATE"].apply(died_in_range).sum()
        else:
            deaths = 0
    except Exception:
        deaths = 0
    mortality_rate = (deaths / total_inpatients * 100) if total_inpatients else 0.0

    # readmission & morbidity
    try:
        readmissions = in_df["ADMISSIONTYPE"].isin(["READMISSION", "EMERGENCY READMISSION"]).sum() if total_inpatients else 0
    except Exception:
        readmissions = 0
    readmission_rate = (readmissions / total_inpatients * 100) if total_inpatients else 0.0

    try:
        morbidity_count = (in_df["DAYSCARED"].fillna(0).astype(float) > 15).sum() if total_inpatients else 0
    except Exception:
        morbidity_count = 0
    morbidity_rate = (morbidity_count / total_inpatients * 100) if total_inpatients else 0.0

    # staff:patient - direct read (no formula)
    spr_df = read_staff_patient_ratio()
    if spr_df is not None and not spr_df.empty:
        spr_display = spr_df.to_dict(orient='records')[0]
        spr_value = ", ".join([f"{k}: {v}" for k, v in spr_display.items()])
    else:
        spr_value = "N/A"

    # KPI cards
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        st.markdown(kpi_card_html("Total Inpatients", total_inpatients, f"{from_date} → {to_date}", "kpi-grad-1", "🏨"), unsafe_allow_html=True)
    with r1c2:
        st.markdown(kpi_card_html("Total Outpatients", total_outpatients, f"{from_date} → {to_date}", "kpi-grad-2", "🧍"), unsafe_allow_html=True)
    with r1c3:
        st.markdown(kpi_card_html("Avg Length of Stay", f"{alos:.2f} days", "Mean of DAYSCARED", "kpi-grad-3", "⏱️"), unsafe_allow_html=True)

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        st.markdown(kpi_card_html("Mortality Rate", f"{mortality_rate:.2f}%", f"{deaths} deaths / {total_inpatients}", "kpi-grad-4", "⚰️"), unsafe_allow_html=True)
    with r2c2:
        st.markdown(kpi_card_html("Readmission Rate", f"{readmission_rate:.2f}%", f"{readmissions} cases", "kpi-grad-5", "🔁"), unsafe_allow_html=True)
    with r2c3:
        st.markdown(kpi_card_html("Morbidity (>15d)", f"{morbidity_rate:.2f}%", f"{morbidity_count} cases", "kpi-grad-6", "📈"), unsafe_allow_html=True)

    p1, p2, p3, p4 = st.columns(4)

# Calculate bed occupancy for the KPI card
occupancy_rate, avg_census, total_beds, _ = calculate_bed_occupancy(from_date, to_date)

with p1:
    color = "kpi-grad-2"
    if occupancy_rate > 95:
        color = "kpi-grad-5"  # Red for overcrowding
    elif occupancy_rate > 85:
        color = "kpi-grad-4"  # Green for optimal
    elif occupancy_rate < 60:
        color = "kpi-grad-3"  # Blue for underutilized
    
    st.markdown(
        kpi_card_html(
            "Bed Occupancy Rate", 
            f"{occupancy_rate:.1f}%", 
            f"{avg_census:.0f} / {total_beds} beds avg", 
            color, 
            "🛏️"
        ), 
        unsafe_allow_html=True
    )

with p2:
    st.markdown(kpi_card_html("ER Wait Times", "N/A", "Requires ER timestamps", "kpi-grad-3", "🚑"), unsafe_allow_html=True)

with p3:
    # Calculate Surgery Wait Time - Match each surgery with closest preceding admission
    try:
        wait_time_q = f"""
        WITH SurgeryAdmission AS (
            SELECT 
                s.SURGERYID,
                s.MRN,
                s.SURGERYDATE,
                i.DOA,
                (s.SURGERYDATE - i.DOA) AS WAIT_DAYS,
                ROW_NUMBER() OVER (
                    PARTITION BY s.SURGERYID 
                    ORDER BY ABS(s.SURGERYDATE - i.DOA)
                ) AS rn
            FROM SURGERY s
            JOIN INPATIENT i ON s.MRN = i.MRN
            WHERE s.SURGERYDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') 
                                    AND TO_DATE('{to_date}', 'YYYY-MM-DD')
              AND i.DOA IS NOT NULL
              AND s.SURGERYDATE >= i.DOA
              AND (s.SURGERYDATE - i.DOA) <= 365
              AND (s.HOSPITALID = '{safe_sql(selected_hospital)}' OR '{selected_hospital}' = 'All Hospitals')
        )
        SELECT 
            AVG(WAIT_DAYS) AS AVG_WAIT_DAYS,
            COUNT(*) AS TOTAL_SURGERIES,
            MIN(WAIT_DAYS) AS MIN_WAIT,
            MAX(WAIT_DAYS) AS MAX_WAIT
        FROM SurgeryAdmission
        WHERE rn = 1 AND WAIT_DAYS >= 0
        """
        wait_df = pd.read_sql(wait_time_q, conn)
        
        if not wait_df.empty and pd.notna(wait_df['AVG_WAIT_DAYS'].iloc[0]):
            avg_wait_days = float(wait_df['AVG_WAIT_DAYS'].iloc[0])
            total_surg = int(wait_df['TOTAL_SURGERIES'].iloc[0])
            wait_display = f"{avg_wait_days:.1f} days"
            wait_subtext = f"{total_surg} surgeries tracked"
        else:
            wait_display = "N/A"
            wait_subtext = "No matched admissions"
    except Exception as e:
        wait_display = "N/A"
        wait_subtext = f"Data unavailable"
    
    st.markdown(kpi_card_html("Surgery Wait Times", wait_display, wait_subtext, "kpi-grad-5", "⏳"), unsafe_allow_html=True)

with p4:
    st.markdown(kpi_card_html("Staff : Patients", spr_value, "Direct DB value if available", "kpi-grad-6", "👩‍⚕️"), unsafe_allow_html=True)

    # display_custom_metrics_row(
    #     conn, 
    #     from_date, 
    #     to_date, 
    #     selected_hospital, 
    #     selected_dept, 
    #     kpi_card_html
    # )
    
# ---- TAB 1: Operational Efficiency
with tabs[1]:
    st.header("Operational Efficiency")
    st.subheader("📊 Category Hierarchy: CATEGORY → SUBCATG → SUBCATGL2")
    
    if selected_hospital not in (None, "", "All Hospitals"):
        st.info(f"🏥 Filtering for Hospital: {selected_hospital}")
    
    # Initialize session state for navigation (use different names to avoid conflict with sidebar filters)
    if "nav_category" not in st.session_state:
        st.session_state.nav_category = None
    if "nav_subcatg" not in st.session_state:
        st.session_state.nav_subcatg = None
    if "view_level" not in st.session_state:
        st.session_state.view_level = 1  # 1=Category, 2=SUBCATG, 3=SUBCATGL2
    
    # Navigation buttons
    nav_cols = st.columns([1, 1, 6])
    with nav_cols[0]:
        if st.session_state.view_level > 1:
            if st.button("⬅️ Back", key="back_btn"):
                if st.session_state.view_level == 3:
                    st.session_state.view_level = 2
                    st.session_state.nav_subcatg = None
                elif st.session_state.view_level == 2:
                    st.session_state.view_level = 1
                    st.session_state.nav_category = None
                st.rerun()
    
    with nav_cols[1]:
        if st.session_state.view_level > 1:
            if st.button("🏠 Home", key="home_btn"):
                st.session_state.view_level = 1
                st.session_state.nav_category = None
                st.session_state.nav_subcatg = None
                st.rerun()
    
    # Breadcrumb
    breadcrumb = "📁 Categories"
    if st.session_state.view_level >= 2:
        breadcrumb += f" → 📂 {st.session_state.nav_category}"
    if st.session_state.view_level == 3:
        breadcrumb += f" → 📄 {st.session_state.nav_subcatg}"
    st.markdown(f"**Navigation:** {breadcrumb}")
    st.markdown("---")
    
    # ============================================
    # LEVEL 1: CATEGORY VIEW
    # ============================================
    if st.session_state.view_level == 1:
        category_metrics = get_category_metrics(from_date, to_date, selected_category, selected_ordering_dept)
        
        if not category_metrics:
            st.warning("No metrics found for selected filters.")
            st.code(f"""
            Date Range: {from_date} to {to_date}
            Hospital: {selected_hospital}
            Category: {selected_category}
            Ordering Dept: {selected_ordering_dept}
            """)
        else:
            st.markdown("### Level 1: Categories")
            st.info("Click on any category card to drill down")

            # === PDF DOWNLOAD: Select Category + Button ===
            col_left, col_right = st.columns([3, 1])
            with col_left:
                cat_names = [m['CATEGORY'] for m in category_metrics]
                selected_pdf_cat = st.selectbox(
                    "Select Category for PDF Report",
                    options=cat_names,
                    key="pdf_category_select"
                )
            with col_right:
                if st.button("Download PDF Report", use_container_width=True, type="primary"):
                    with st.spinner(f"Generating PDF for {selected_pdf_cat}..."):
                        pdf_bytes = build_category_pdf(
                            selected_pdf_cat, from_date, to_date, selected_ordering_dept
                        )
                        st.download_button(
                            label="Click to Download PDF",
                            data=pdf_bytes,
                            file_name=f"{selected_pdf_cat.replace(' ', '_')}_Full_Report.pdf",
                            mime="application/pdf",
                            key="final_pdf_download"
                        )
                    st.success("PDF ready! Click above to download.")

            st.markdown("---")

            # === Category Cards (unchanged) ===
            per_row = 3
            rows = (len(category_metrics) + per_row - 1) // per_row
            for r in range(rows):
                cols = st.columns(per_row)
                for i in range(per_row):
                    idx = r * per_row + i
                    if idx >= len(category_metrics):
                        continue
                    m = category_metrics[idx]
                    with cols[i]:
                        st.markdown(
                            kpi_card_html(
                                f"{m['CATEGORY']}", 
                                f"{m['TOTAL']:,}", 
                                f"Avg/day {m['AVG_PER_DAY']:.2f} • Max {m['MAX_ENTRY']:,}", 
                                grad_class="kpi-grad-1", 
                                icon=""
                            ), 
                            unsafe_allow_html=True
                        )
                        if st.button(f"View Details →", key=f"cat_{idx}", use_container_width=True):
                            st.session_state.nav_category = m['CATEGORY']
                            st.session_state.view_level = 2
                            st.rerun()
    
    # ============================================
    # LEVEL 2: SUBCATG VIEW
    # ============================================
    elif st.session_state.view_level == 2:
        category_name = st.session_state.nav_category
        st.markdown(f"### 📂 Level 2: SUBCATG within '{category_name}'")
        st.info("👆 Click on any subcategory card to see detailed breakdown")
        
        subcatg_metrics = get_subcatg_metrics(category_name, from_date, to_date, selected_ordering_dept)
        
        if not subcatg_metrics:
            st.warning(f"No SUBCATG data available for {category_name}")
        else:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 SUBCATG Count", len(subcatg_metrics))
            with col2:
                total_subcatg = sum(item['TOTAL'] for item in subcatg_metrics)
                st.metric("📈 Total Count", f"{total_subcatg:,}")
            with col3:
                avg_subcatg = total_subcatg / len(subcatg_metrics) if subcatg_metrics else 0
                st.metric("📊 Avg per SUBCATG", f"{avg_subcatg:,.0f}")
            
            st.markdown("---")
            
            # Display SUBCATG cards
            per_row = 3
            rows = (len(subcatg_metrics) + per_row - 1) // per_row
            
            for r in range(rows):
                cols = st.columns(per_row)
                for i in range(per_row):
                    idx = r * per_row + i
                    if idx >= len(subcatg_metrics):
                        continue
                    m = subcatg_metrics[idx]
                    
                    with cols[i]:
                        st.markdown(
                            kpi_card_html(
                                f"{m['SUBCATG']}", 
                                f"{m['TOTAL']:,}", 
                                f"Avg/day {m['AVG_PER_DAY']:.2f} • Max {m['MAX_ENTRY']:,}", 
                                grad_class="kpi-grad-2", 
                                icon="📂"
                            ), 
                            unsafe_allow_html=True
                        )
                        
                        if st.button(f"View Details →", key=f"sub_{idx}", use_container_width=True):
                            st.session_state.nav_subcatg = m['SUBCATG']
                            st.session_state.view_level = 3
                            st.rerun()
    
    # ============================================
    # LEVEL 3: SUBCATGL2 VIEW
    # ============================================
    elif st.session_state.view_level == 3:
        category_name = st.session_state.nav_category
        subcatg_name = st.session_state.nav_subcatg
        
        st.markdown(f"### 📄 Level 3: SUBCATGL2 Details")
        st.markdown(f"**Category:** {category_name} → **SUBCATG:** {subcatg_name}")
        
        subcatgl2_metrics = get_subcatgl2_metrics(
            category_name, subcatg_name, from_date, to_date, selected_ordering_dept
        )
        
        if not subcatgl2_metrics:
            st.warning(f"No SUBCATGL2 data available for {subcatg_name}")
        else:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 SUBCATGL2 Count", len(subcatgl2_metrics))
            with col2:
                total_subcatgl2 = sum(item['TOTAL'] for item in subcatgl2_metrics)
                st.metric("📈 Total Count", f"{total_subcatgl2:,}")
            with col3:
                avg_subcatgl2 = total_subcatgl2 / len(subcatgl2_metrics) if subcatgl2_metrics else 0
                st.metric("📊 Avg per Item", f"{avg_subcatgl2:,.0f}")
            
            st.markdown("---")
            
            # Display as enhanced dataframe
            df_display = pd.DataFrame(subcatgl2_metrics)
            df_display['AVG_PER_DAY'] = df_display['AVG_PER_DAY'].round(2)
            df_display = df_display.sort_values('TOTAL', ascending=False).reset_index(drop=True)
            
            # Add ranking
            if 'Rank' not in df_display.columns:
                df_display.insert(0, 'Rank', range(1, len(df_display) + 1))
            
            st.markdown("#### 📊 SUBCATGL2 Breakdown Table")
            st.dataframe(
                df_display.style.background_gradient(subset=['TOTAL'], cmap='Greens')
                .format({'TOTAL': '{:,.0f}', 'AVG_PER_DAY': '{:.2f}'}),
                use_container_width=True,
                height=min(500, len(df_display) * 35 + 38)
            )
            
            st.markdown("---")
            
            # Visualization tabs
            viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📊 Bar Chart", "🥧 Pie Chart", "📈 Top 10"])
            
            with viz_tab1:
                # Bar chart
                chart = alt.Chart(df_display).mark_bar().encode(
                    x=alt.X('SUBCATGL2:N', sort='-y', title='SUBCATGL2', axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y('TOTAL:Q', title='Total Count'),
                    color=alt.Color('TOTAL:Q', scale=alt.Scale(scheme='greens'), legend=None),
                    tooltip=[
                        alt.Tooltip('SUBCATGL2:N', title='SUBCATGL2'),
                        alt.Tooltip('TOTAL:Q', title='Total', format=','),
                        alt.Tooltip('AVG_PER_DAY:Q', title='Avg/Day', format='.2f')
                    ]
                ).properties(height=400)
                st.altair_chart(chart, use_container_width=True)
            
            with viz_tab2:
                # Pie chart (top 10 + Others)
                df_pie = df_display.head(10).copy()
                if len(df_display) > 10:
                    others_total = df_display.iloc[10:]['TOTAL'].sum()
                    if others_total > 0:  # Only add Others if there's actual data
                        others_row = pd.DataFrame([{
                            'SUBCATGL2': 'Others',
                            'TOTAL': others_total,
                            'AVG_PER_DAY': 0
                        }])
                        df_pie = pd.concat([df_pie, others_row], ignore_index=True)
                
                pie_chart = alt.Chart(df_pie).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta('TOTAL:Q'),
                    color=alt.Color('SUBCATGL2:N', legend=alt.Legend(title='SUBCATGL2')),
                    tooltip=[
                        alt.Tooltip('SUBCATGL2:N', title='SUBCATGL2'),
                        alt.Tooltip('TOTAL:Q', title='Total', format=',')
                    ]
                ).properties(height=400)
                st.altair_chart(pie_chart, use_container_width=True)
            
            with viz_tab3:
                # Top 10 horizontal bar
                df_top10 = df_display.head(10)
                top10_chart = alt.Chart(df_top10).mark_bar().encode(
                    y=alt.Y('SUBCATGL2:N', sort='-x', title='SUBCATGL2'),
                    x=alt.X('TOTAL:Q', title='Total Count'),
                    color=alt.Color('TOTAL:Q', scale=alt.Scale(scheme='greens'), legend=None),
                    tooltip=[
                        alt.Tooltip('Rank:Q', title='Rank'),
                        alt.Tooltip('SUBCATGL2:N', title='SUBCATGL2'),
                        alt.Tooltip('TOTAL:Q', title='Total', format=','),
                        alt.Tooltip('AVG_PER_DAY:Q', title='Avg/Day', format='.2f')
                    ]
                ).properties(height=400)
                st.altair_chart(top10_chart, use_container_width=True)
            
            st.markdown("---")
            
            # Download section
            st.markdown("#### 📥 Download Data")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df_display.to_csv(index=False)
                st.download_button(
                    label="📄 Download as CSV",
                    data=csv,
                    file_name=f"{category_name}_{subcatg_name}_subcatgl2.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Excel download would require openpyxl
                st.info("💡 CSV format includes all data with rankings")

    st.markdown("---")

# ---- Financial tab (placeholder) ----
with tabs[2]:
    st.header("Financial")
    st.info("Financial tab placeholder. Add billing/invoice/ledger tables and queries to populate.")
    try:
        fin_q = "SELECT * FROM FINANCIAL_SUMMARY FETCH FIRST 200 ROWS ONLY"
        fin_df = pd.read_sql(fin_q, conn)
        if not fin_df.empty:
            st.dataframe(fin_df)
        else:
            st.info("FINANCIAL_SUMMARY empty or unavailable.")
    except Exception:
        st.info("Financial data not available. Add FINANCIAL_SUMMARY or equivalent table/view.")

# ---- Quality & Safety tab (placeholder) ----
with tabs[3]:
    st.header("Quality & Safety")
    st.info("Placeholder: Add infection rates, incident reports, audit logs, sentinel event tables, etc.")
    try:
        q_q = "SELECT * FROM QUALITY_METRICS FETCH FIRST 200 ROWS ONLY"
        q_df = pd.read_sql(q_q, conn)
        if not q_df.empty:
            st.dataframe(q_df)
        else:
            st.info("QUALITY_METRICS table not present or empty.")
    except Exception:
        st.info("No quality metrics source found.")

# ---- Reports tab ----
with tabs[4]:
    st.header("📑 Patient Reports Viewer")

    st.subheader("🔍 Search Patient MRN")
    mrn_input = st.text_input("Enter MRN / partial MRN", "")
    suggestions = []
    if mrn_input.strip() != "":
        suggestions = search_mrns(mrn_input.strip())

    if suggestions:
        sel_mrn = st.selectbox("Select MRN", suggestions)
    else:
        sel_mrn = None
        if mrn_input.strip() != "":
            st.warning("No matching MRNs found.")

    if sel_mrn:
        st.success(f"MRN selected: {sel_mrn}")
        reports_df = fetch_reports_for_mrn(sel_mrn)

        if reports_df.empty:
            st.info("No reports for this MRN.")
        else:
            def safe_clob(x):
                if x is None:
                    return ""
                try:
                    return x.read() if hasattr(x, "read") else str(x)
                except:
                    return str(x)

            reports_df["NOTEDATA"] = reports_df["NOTEDATA"].apply(safe_clob)
            reports_df["LABEL"] = reports_df.apply(build_report_label, axis=1)

            st.subheader("🗂 Select Reports to View / Download")
            selected_labels = st.multiselect(
                "Select one or multiple reports",
                reports_df["LABEL"].tolist()
            )

            if selected_labels:
                sel_rows = reports_df[reports_df["LABEL"].isin(selected_labels)]
                st.subheader("📄 Report Viewer")

                CSS_WRAPPER_START = '<div style="background-color:white; padding:15px; color:black;">'
                CSS_WRAPPER_END = "</div>"

                for idx, row in sel_rows.iterrows():
                    st.markdown(f"### 📝 {row['NOTENAME']} ({row['ACCESSION_NUM']})")
                    html_data = row["NOTEDATA"]
                    if not html_data or html_data.strip() == "":
                        html_data = "<p>No data.</p>"
                    wrapped_html = CSS_WRAPPER_START + html_data + CSS_WRAPPER_END
                    components.html(wrapped_html, height=500, scrolling=True)
                    st.markdown("---")

                st.subheader("⬇️ Download Selected Reports")
                selected_accessions = sel_rows["ACCESSION_NUM"].dropna().tolist()

                if selected_accessions:
                    def create_zip_safe(df, accession_list):
                        mem_zip = io.BytesIO()
                        with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                            for _, r in df[df["ACCESSION_NUM"].isin(accession_list)].iterrows():
                                fname = f"{r['ACCESSION_NUM']}_{r['NOTENAME'].replace(' ', '_')}.html"
                                content = safe_clob(r["NOTEDATA"])
                                if not isinstance(content, str):
                                    content = str(content)
                                html_wrapped = CSS_WRAPPER_START + content + CSS_WRAPPER_END
                                zf.writestr(fname, html_wrapped)
                        mem_zip.seek(0)
                        return mem_zip.getvalue()

                    zip_bytes = create_zip_safe(reports_df, selected_accessions)
                    st.download_button(
                        label="📦 Download as ZIP",
                        data=zip_bytes,
                        file_name=f"reports_{sel_mrn}.zip",
                        mime="application/zip"
                    )

# ---- Stats Tab ----
with tabs[5]:
    st.header("📊 Patient Stats")
    
    # ============================================
    # BED OCCUPANCY ANALYSIS
    # ============================================
    st.subheader("🛏️ Bed Occupancy Analysis")
    
    # Calculate overall bed occupancy
    occupancy_rate, avg_census, total_beds, _ = calculate_bed_occupancy(from_date, to_date)
    
    # Detailed breakdown tabs (NO KPI cards here)
    occ_tab1, occ_tab2, occ_tab3 = st.tabs(["📈 Daily Trend", "🏥 By Department", "📍 By Location"])

    # TAB 1: Daily Trend
with occ_tab1:
    st.markdown("#### Daily Occupancy Trend")
    
    # Get daily trend data
    _, _, _, trend_df = calculate_bed_occupancy(from_date, to_date)
    
    if not trend_df.empty:
        # Aggregate by date
        daily_agg = trend_df.groupby('THEDATE').agg({
            'OPBAL': 'sum',
            'ADMIT': 'sum',
            'DISCH': 'sum',
            'TRIN': 'sum',
            'TROUT': 'sum',
            'DEATH': 'sum',
            'DAILY_OCCUPANCY': 'sum'
        }).reset_index()
        
        daily_agg['OCCUPANCY_PCT'] = (daily_agg['DAILY_OCCUPANCY'] / total_beds * 100).round(2)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Beds", total_beds)
        with col2:
            st.metric("👥 Avg Daily Census", f"{avg_census:.0f}")
        with col3:
            peak = daily_agg['DAILY_OCCUPANCY'].max()
            peak_pct = (peak / total_beds * 100)
            st.metric("📈 Peak Occupancy", f"{int(peak)} ({peak_pct:.1f}%)")
        with col4:
            low = daily_agg['DAILY_OCCUPANCY'].min()
            low_pct = (low / total_beds * 100)
            st.metric("📉 Lowest Occupancy", f"{int(low)} ({low_pct:.1f}%)")
        
        # Chart
        chart_data = daily_agg[['THEDATE', 'OCCUPANCY_PCT', 'DAILY_OCCUPANCY', 'ADMIT', 'DISCH']].copy()
        
        # Line chart for occupancy
        line = alt.Chart(chart_data).mark_line(point=True, color='#00d4aa', strokeWidth=3).encode(
            x=alt.X('THEDATE:T', title='Date'),
            y=alt.Y('OCCUPANCY_PCT:Q', title='Occupancy %', scale=alt.Scale(domain=[0, max(100, chart_data['OCCUPANCY_PCT'].max() + 10)])),
            tooltip=[
                alt.Tooltip('THEDATE:T', title='Date', format='%d-%b-%Y'),
                alt.Tooltip('DAILY_OCCUPANCY:Q', title='Census', format='.0f'),
                alt.Tooltip('OCCUPANCY_PCT:Q', title='Occupancy %', format='.2f'),
                alt.Tooltip('ADMIT:Q', title='Admissions', format='.0f'),
                alt.Tooltip('DISCH:Q', title='Discharges', format='.0f')
            ]
        )
        
        # Reference lines
        target_line = alt.Chart(pd.DataFrame({'y': [85], 'label': ['Target 85%']})).mark_rule(
            color='green', strokeDash=[5, 5], strokeWidth=2
        ).encode(y='y:Q')
        
        critical_line = alt.Chart(pd.DataFrame({'y': [95], 'label': ['Critical 95%']})).mark_rule(
            color='red', strokeDash=[5, 5], strokeWidth=2
        ).encode(y='y:Q')
        
        st.altair_chart(line + target_line + critical_line, use_container_width=True)
        
        # Data table
        st.markdown("#### 📋 Daily Data Table")
        display_df = daily_agg.copy()
        display_df['THEDATE'] = pd.to_datetime(display_df['THEDATE']).dt.strftime('%d-%b-%Y')
        display_df = display_df.rename(columns={
            'THEDATE': 'Date',
            'OPBAL': 'Opening',
            'ADMIT': 'Admitted',
            'DISCH': 'Discharged',
            'TRIN': 'Transfer In',
            'TROUT': 'Transfer Out',
            'DEATH': 'Deaths',
            'DAILY_OCCUPANCY': 'Final Census',
            'OCCUPANCY_PCT': 'Occupancy %'
        })
        
        st.dataframe(
            display_df.style.format({
                'Opening': '{:.0f}',
                'Admitted': '{:.0f}',
                'Discharged': '{:.0f}',
                'Transfer In': '{:.0f}',
                'Transfer Out': '{:.0f}',
                'Deaths': '{:.0f}',
                'Final Census': '{:.0f}',
                'Occupancy %': '{:.2f}%'
            }).background_gradient(subset=['Occupancy %'], cmap='RdYlGn', vmin=50, vmax=100),
            use_container_width=True,
            height=400
        )
    else:
        st.info("No census data available for the selected period.")
    
    # TAB 2: By Department
    with occ_tab2:
        st.markdown("#### 🏥 Department-wise Bed Occupancy")
        
        dept_breakdown = get_department_occupancy_breakdown(from_date, to_date)
        
        if not dept_breakdown.empty:
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏥 Total Departments", len(dept_breakdown))
            with col2:
                highest = dept_breakdown.loc[dept_breakdown['OCCUPANCY_RATE'].idxmax()]
                st.metric("📈 Highest Occupancy", f"{highest['DEPARTMENT']}", f"{highest['OCCUPANCY_RATE']:.1f}%")
            with col3:
                lowest = dept_breakdown.loc[dept_breakdown['OCCUPANCY_RATE'].idxmin()]
                st.metric("📉 Lowest Occupancy", f"{lowest['DEPARTMENT']}", f"{lowest['OCCUPANCY_RATE']:.1f}%")
            
            # Chart
            chart = alt.Chart(dept_breakdown).mark_bar().encode(
                y=alt.Y('DEPARTMENT:N', sort='-x', title='Department'),
                x=alt.X('OCCUPANCY_RATE:Q', title='Occupancy Rate (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('OCCUPANCY_RATE:Q', 
                    scale=alt.Scale(domain=[0, 60, 85, 95, 100], range=['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#c0392b']),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip('DEPARTMENT:N', title='Department'),
                    alt.Tooltip('TOTAL_BEDS:Q', title='Total Beds', format=','),
                    alt.Tooltip('AVG_CENSUS:Q', title='Avg Census', format='.1f'),
                    alt.Tooltip('OCCUPANCY_RATE:Q', title='Occupancy %', format='.2f')
                ]
            ).properties(height=max(300, len(dept_breakdown) * 40))
            
            st.altair_chart(chart, use_container_width=True)
            
            # Table
            st.dataframe(
                dept_breakdown.style.format({
                    'TOTAL_BEDS': '{:.0f}',
                    'AVG_CENSUS': '{:.1f}',
                    'OCCUPANCY_RATE': '{:.2f}%'
                }).background_gradient(subset=['OCCUPANCY_RATE'], cmap='RdYlGn', vmin=50, vmax=100),
                use_container_width=True
            )
        else:
            st.info("No department data available.")
    
    # TAB 3: By Location
    with occ_tab3:
        st.markdown("#### 📍 Location-wise Bed Occupancy (Ward/ICU Level)")
        
        # Option to filter by department
        if not get_department_occupancy_breakdown(from_date, to_date).empty:
            dept_filter_list = ["All"] + get_department_occupancy_breakdown(from_date, to_date)['DEPARTMENT'].tolist()
            selected_dept_filter = st.selectbox("Filter by Department", dept_filter_list, key="loc_dept_filter")
        else:
            selected_dept_filter = "All"
        
        dept_param = None if selected_dept_filter == "All" else selected_dept_filter
        loc_breakdown = get_location_occupancy_breakdown(from_date, to_date, dept_param)
        
        if not loc_breakdown.empty:
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📍 Total Locations", len(loc_breakdown))
            with col2:
                highest = loc_breakdown.loc[loc_breakdown['OCCUPANCY_RATE'].idxmax()]
                st.metric("📈 Highest", f"{highest['LOCATION']}", f"{highest['OCCUPANCY_RATE']:.1f}%")
            with col3:
                lowest = loc_breakdown.loc[loc_breakdown['OCCUPANCY_RATE'].idxmin()]
                st.metric("📉 Lowest", f"{lowest['LOCATION']}", f"{lowest['OCCUPANCY_RATE']:.1f}%")
            
            # Chart
            chart = alt.Chart(loc_breakdown).mark_bar().encode(
                y=alt.Y('LOCATION:N', sort='-x', title='Location'),
                x=alt.X('OCCUPANCY_RATE:Q', title='Occupancy Rate (%)', scale=alt.Scale(domain=[0, 100])),
                color=alt.Color('DEPARTMENT:N', legend=alt.Legend(title='Department')),
                tooltip=[
                    alt.Tooltip('DEPARTMENT:N', title='Department'),
                    alt.Tooltip('LOCATION:N', title='Location'),
                    alt.Tooltip('TOTAL_BEDS:Q', title='Beds', format=','),
                    alt.Tooltip('AVG_CENSUS:Q', title='Avg Census', format='.1f'),
                    alt.Tooltip('OCCUPANCY_RATE:Q', title='Occupancy %', format='.2f')
                ]
            ).properties(height=max(400, len(loc_breakdown) * 30))
            
            st.altair_chart(chart, use_container_width=True)
            
            # Table with grouping
            st.markdown("#### 📋 Detailed Location Data")
            display_loc = loc_breakdown.copy()
            st.dataframe(
                display_loc.style.format({
                    'TOTAL_BEDS': '{:.0f}',
                    'AVG_CENSUS': '{:.1f}',
                    'OCCUPANCY_RATE': '{:.2f}%'
                }).background_gradient(subset=['OCCUPANCY_RATE'], cmap='RdYlGn', vmin=50, vmax=100),
                use_container_width=True,
                height=500
            )
        else:
            st.info("No location data available.")
    
    # ============================================
    # EXISTING PATIENT STATS (AFTER BED OCCUPANCY)
    # ============================================
    st.markdown("---")
    st.markdown("---")
    
    # Continue with existing age distribution, admission type, state-wise metrics...
    avg_age, age_dist = compute_age_distribution()
    st.subheader("Age Distribution")
    # ... rest of your existing stats tab code ...
    if not age_dist.empty:
        chart = alt.Chart(age_dist).mark_bar().encode(
            x="AGE_GROUP",
            y="CNT",
            tooltip=["AGE_GROUP", "CNT"]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
        if avg_age:
            st.info(f"Average age: {avg_age:.1f} years")
    else:
        st.info("No age data available.")

    adm_type = admission_type_breakdown(from_date, to_date, selected_dept)
    st.subheader("Admission Type Breakdown")
    if not adm_type.empty:
        chart2 = alt.Chart(adm_type).mark_bar().encode(
            x="ADMISSIONTYPE",
            y="CNT",
            tooltip=["ADMISSIONTYPE", "CNT"]
        ).properties(height=300)
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.info("No admission type data available.")

    st.subheader("State-wise Metrics")
    stats_hosp_list = ["All Hospitals"] + (hosp_df["HOSPITALID"].dropna().tolist() if 'hosp_df' in globals() else [])
    stats_selected_hosp = st.selectbox(
        "Hospital", stats_hosp_list, index=0, key="stats_hosp_selectbox"
    )

    stats_dept_list = ["All"] + (dept_df["DEPTCODE"].dropna().tolist() if 'dept_df' in globals() else [])
    stats_selected_dept = st.selectbox(
        "Department", stats_dept_list, index=0, key="stats_dept_selectbox"
    )

    stats_years = list(range(2000, today.year + 1))
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox(
            "Start Year", stats_years, index=0, key="stats_start_year_selectbox"
        )
    with col2:
        start_month = st.selectbox(
            "Start Month", list(range(1,13)), index=0, key="stats_start_month_selectbox"
        )
    col3, col4 = st.columns(2)
    with col3:
        end_year = st.selectbox(
            "End Year", stats_years, index=len(stats_years)-1, key="stats_end_year_selectbox"
        )
    with col4:
        end_month = st.selectbox(
            "End Month", list(range(1,13)), index=today.month-1, key="stats_end_month_selectbox"
        )

    where_clauses = []
    if stats_selected_hosp not in (None, "", "All Hospitals"):
        where_clauses.append(f"HOSPITALID = '{safe_sql(stats_selected_hosp)}'")
    if stats_selected_dept not in (None, "", "All"):
        where_clauses.append(f"DEPTCODE = '{safe_sql(stats_selected_dept)}'")
    start_ym = start_year*100 + start_month
    end_ym = end_year*100 + end_month
    where_clauses.append(f"(YR*100 + MNTH) BETWEEN {start_ym} AND {end_ym}")
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    stats_q = f"""
        SELECT STATE, SUM(CNT) AS CNT, YR, MNTH
        FROM STATESTATS
        WHERE {where_sql}
        GROUP BY STATE, YR, MNTH
        ORDER BY YR, MNTH, STATE
    """
    try:
        stats_df = pd.read_sql(stats_q, conn)
    except Exception:
        stats_df = pd.DataFrame(columns=["STATE","CNT","YR","MNTH"])

    if stats_df.empty:
        st.info("No state-wise data available for selected filters.")
    else:
        state_total = stats_df.groupby("STATE")["CNT"].sum().reset_index()
        st.markdown("**Total Count by State**")
        chart_state = alt.Chart(state_total).mark_bar().encode(
            x=alt.X("STATE", sort="-y"),
            y="CNT",
            tooltip=["STATE","CNT"]
        ).properties(height=400)
        st.altair_chart(chart_state, use_container_width=True)

        st.markdown("**State-wise Trend Over Time**")
        stats_df["DATE"] = pd.to_datetime(stats_df["YR"].astype(str) + "-" + stats_df["MNTH"].astype(str) + "-01")
        chart_trend = alt.Chart(stats_df).mark_line(point=True).encode(
            x="DATE:T",
            y="CNT",
            color="STATE",
            tooltip=["STATE","CNT","DATE"]
        ).properties(height=400)
        st.altair_chart(chart_trend, use_container_width=True)

# ---- TAB 6: Custom Metrics Manager ----
with tabs[6]:
    st.header("Custom Metrics Manager")

    try:
        custom_dir = Path("custom_metrics")
        templates_dir = custom_dir / "templates"
        metrics_file = custom_dir / "saved_metrics.json"

        custom_dir.mkdir(exist_ok=True)
        templates_dir.mkdir(exist_ok=True)

        # Ensure the JSON file exists (create empty if not)
        if not metrics_file.exists():
            metrics_file.write_text("{}", encoding="utf-8")
    except Exception as e:
        st.error(f"Failed to initialize custom metrics folder: {e}")
        st.stop()

    try:
        if conn.closed:
            conn = get_conn()
    except:
        try:
            conn = get_conn()
        except Exception as db_e:
            st.error(f"Cannot reconnect to database: {db_e}")
            st.stop()
    try:
        render_custom_metrics_ui(
            conn=conn,
            from_date=from_date,
            to_date=to_date,
            selected_hospital=selected_hospital,
            selected_dept=selected_dept
        )
    except Exception as e:
        st.error("Custom Metrics failed to load:")
        st.exception(e)

# ---- Surgery Details tab ----
with tabs[7]:
    st.header("Surgery Details")

    # ============================================
    # BUILD DEPARTMENT FILTER USING DEPTCODE
    # ============================================
    dept_filter = ""
    if selected_dept and selected_dept not in (None, "", "All"):
        try:
            # Get DEPTCODE for selected department name
            dept_code_q = f"SELECT DEPTCODE FROM DEPARTMENT WHERE DEPTNAME = '{safe_sql(selected_dept)}' AND ROWNUM = 1"
            dept_code_df = pd.read_sql(dept_code_q, conn)
            
            if not dept_code_df.empty and dept_code_df['DEPTCODE'].iloc[0] is not None:
                dept_code = dept_code_df['DEPTCODE'].iloc[0]
                dept_filter = f"AND s.DEPTCODE = '{safe_sql(dept_code)}'"
                st.info(f"🏥 Filtering for Department: {selected_dept} (Code: {dept_code})")
            else:
                st.warning(f"⚠️ Department '{selected_dept}' not found in DEPARTMENT table")
                dept_filter = "AND 1=0"  # Return no results if dept not found
        except Exception as e:
            st.error(f"Error getting department code: {e}")
            dept_filter = ""
    
    # Build surgeon filter (if any)
    surgeon_filter = ""
    if selected_surgeon_id:
        surgeon_filter = f"AND EXISTS (SELECT 1 FROM SURGERY_PERSONNEL sp WHERE sp.SURGERYID = s.SURGERYID AND sp.STAFFROLE = 'SURGEON' AND sp.STAFFID = '{safe_sql(selected_surgeon_id)}')"
        st.info(f"👨‍⚕️ Filtering for Surgeon: {selected_surgeon_name}")

    # Hospital filter
    if selected_hospital not in (None, "", "All Hospitals"):
        st.info(f"🏥 Filtering for Hospital: {selected_hospital}")

    # COMPLETE QUERY with DEPTCODE filter
    surgery_q = f"""
    WITH RankedPersonnel AS (
        SELECT 
            sp.SURGERYID,
            sp.STAFFID,
            sp.STAFFROLE,
            NVL(sm.STAFFNAME, sp.STAFFID) AS STAFFNAME,
            ROW_NUMBER() OVER (PARTITION BY sp.SURGERYID, sp.STAFFROLE ORDER BY sp.STAFFID) AS rn
        FROM SURGERY_PERSONNEL sp
        LEFT JOIN STAFFMASTER sm ON sp.STAFFID = sm.STAFFID
        WHERE UPPER(sp.STAFFID) != 'MIGRATED'
    )
    SELECT
        s.SURGERYID,
        s.MRN,
        s.SURGERYDATE,
        s.OTNUMBER,
        s.ANAESTHESIA,
        s.SURGERYTYPE,
        s.DEPTCODE,
        NVL(d.DEPTNAME, s.DEPTCODE) AS DEPTNAME,
        NVL(sd.SURGERYNAME, 'Procedure Name Not Found') AS PROCEDURE_NAME,
        NVL(sd.CATEGORY, 'Uncategorized') AS PROC_CATEGORY,
        NVL(sd.SUBCATEGORY, '-') AS PROC_SUBCATEGORY,
        -- Main roles
        NVL(surgeon.STAFFNAME, 'Unknown Surgeon') AS SURGEON_NAME,
        NVL(anaesthetist.STAFFNAME, 'Not Recorded') AS ANAESTHETIST_NAME,
        NVL(asst_surgeon.STAFFNAME, '-') AS ASST_SURGEON_NAME,
        NVL(asst_anes.STAFFNAME, '-') AS ASST_ANAESTHETIST_NAME,
        NVL(perfusionist.STAFFNAME, '-') AS PERFUSIONIST_NAME,
        NVL(rnurse.STAFFNAME, '-') AS RNURSE_NAME,
        NVL(scnurse.STAFFNAME, '-') AS SCNURSE_NAME,
        -- Additional roles
        NVL(nurse.STAFFNAME, '-') AS NURSE_NAME,
        NVL(techcath.STAFFNAME, '-') AS TECHCATH_NAME,
        NVL(physiciancath.STAFFNAME, '-') AS PHYSICIANCATH_NAME,
        NVL(technician.STAFFNAME, '-') AS TECHNICIAN_NAME,
        NVL(asstphycath.STAFFNAME, '-') AS ASSTPHYCATH_NAME,
        NVL(iomtech.STAFFNAME, '-') AS IOMTECH_NAME,
        NVL(circnurse.STAFFNAME, '-') AS CIRCNURSE_NAME,
        NVL(asstnurse.STAFFNAME, '-') AS ASSTNURSE_NAME,
        NVL(wardnurse.STAFFNAME, '-') AS WARDNURSE_NAME
    FROM SURGERY s
    LEFT JOIN DEPARTMENT d ON s.DEPTCODE = d.DEPTCODE AND s.HOSPITALID = d.HOSPITALID
    LEFT JOIN SURGERY_DETAILS sd 
      ON s.SURGERYID = sd.SURGERYID
     AND s.HOSPITALID = sd.HOSPITALID
    -- Main roles (7)
    LEFT JOIN RankedPersonnel surgeon ON s.SURGERYID = surgeon.SURGERYID AND surgeon.STAFFROLE = 'SURGEON' AND surgeon.rn = 1
    LEFT JOIN RankedPersonnel anaesthetist ON s.SURGERYID = anaesthetist.SURGERYID AND anaesthetist.STAFFROLE = 'ANAESTHETIST' AND anaesthetist.rn = 1
    LEFT JOIN RankedPersonnel asst_surgeon ON s.SURGERYID = asst_surgeon.SURGERYID AND asst_surgeon.STAFFROLE = 'ASSISTING SURGEON' AND asst_surgeon.rn = 1
    LEFT JOIN RankedPersonnel asst_anes ON s.SURGERYID = asst_anes.SURGERYID AND asst_anes.STAFFROLE = 'ASSISTING ANAESTHETIST' AND asst_anes.rn = 1
    LEFT JOIN RankedPersonnel perfusionist ON s.SURGERYID = perfusionist.SURGERYID AND perfusionist.STAFFROLE = 'PERFUSIONIST' AND perfusionist.rn = 1
    LEFT JOIN RankedPersonnel rnurse ON s.SURGERYID = rnurse.SURGERYID AND rnurse.STAFFROLE = 'RNURSE' AND rnurse.rn = 1
    LEFT JOIN RankedPersonnel scnurse ON s.SURGERYID = scnurse.SURGERYID AND scnurse.STAFFROLE = 'SCNURSE' AND scnurse.rn = 1
    -- Additional roles (9)
    LEFT JOIN RankedPersonnel nurse ON s.SURGERYID = nurse.SURGERYID AND nurse.STAFFROLE = 'NURSE' AND nurse.rn = 1
    LEFT JOIN RankedPersonnel techcath ON s.SURGERYID = techcath.SURGERYID AND techcath.STAFFROLE = 'TECHCATH' AND techcath.rn = 1
    LEFT JOIN RankedPersonnel physiciancath ON s.SURGERYID = physiciancath.SURGERYID AND physiciancath.STAFFROLE = 'PHYSICIANCATH' AND physiciancath.rn = 1
    LEFT JOIN RankedPersonnel technician ON s.SURGERYID = technician.SURGERYID AND technician.STAFFROLE = 'TECHNICIAN' AND technician.rn = 1
    LEFT JOIN RankedPersonnel asstphycath ON s.SURGERYID = asstphycath.SURGERYID AND asstphycath.STAFFROLE = 'ASSTPHYCATH' AND asstphycath.rn = 1
    LEFT JOIN RankedPersonnel iomtech ON s.SURGERYID = iomtech.SURGERYID AND iomtech.STAFFROLE = 'IOMTECH' AND iomtech.rn = 1
    LEFT JOIN RankedPersonnel circnurse ON s.SURGERYID = circnurse.SURGERYID AND circnurse.STAFFROLE = 'CIRCNURSE' AND circnurse.rn = 1
    LEFT JOIN RankedPersonnel asstnurse ON s.SURGERYID = asstnurse.SURGERYID AND asstnurse.STAFFROLE = 'ASSTNURSE' AND asstnurse.rn = 1
    LEFT JOIN RankedPersonnel wardnurse ON s.SURGERYID = wardnurse.SURGERYID AND wardnurse.STAFFROLE = 'WARDNURSE' AND wardnurse.rn = 1
    WHERE s.SURGERYDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD')
                           AND TO_DATE('{to_date}', 'YYYY-MM-DD') + 0.99999
      AND (s.HOSPITALID = '{safe_sql(selected_hospital)}' OR '{selected_hospital}' = 'All Hospitals')
      {dept_filter}
      {surgeon_filter}
    ORDER BY s.SURGERYDATE DESC
    """

    try:
        df = pd.read_sql(surgery_q, conn)
    except Exception as e:
        st.error(f"❌ Query failed: {e}")
        with st.expander("🔍 Show SQL Query for Debugging"):
            st.code(surgery_q, language="sql")
        df = pd.DataFrame()

    if df.empty:
        st.warning("⚠️ No surgeries found for the selected filters.")
        
        # Show applied filters for debugging
        with st.expander("🔍 Applied Filters"):
            st.code(f"""
Date Range: {from_date} to {to_date}
Department: {selected_dept}
Hospital: {selected_hospital}
Surgeon: {selected_surgeon_name if selected_surgeon_id else 'All Surgeons'}

Query Filters Applied:
- Date Filter: ✅
- Hospital Filter: {'✅ ' + selected_hospital if selected_hospital != 'All Hospitals' else '❌ (All Hospitals)'}
- Department Filter: {'✅ ' + selected_dept if selected_dept != 'All' else '❌ (All Departments)'}
- Surgeon Filter: {'✅ ' + (selected_surgeon_name or '') if selected_surgeon_id else '❌ (All Surgeons)'}
            """)
        st.stop()

    total_surgeries = len(df)
    days = (to_date - from_date).days + 1
    daily_avg = round(total_surgeries / days, 1)

    # Display filter summary
    st.success(f"✅ Found {total_surgeries:,} surgeries matching your filters")

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(kpi_card_html("Total Surgeries", f"{total_surgeries:,}", f"{from_date} → {to_date}", "kpi-grad-1", "🔪"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card_html("Daily Average", daily_avg, f"{days} days", "kpi-grad-2", "📅"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card_html("Unique Patients", df["MRN"].nunique(), "Distinct MRNs", "kpi-grad-3", "👥"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card_html("OT Rooms Used", df["OTNUMBER"].nunique(), "Active theatres", "kpi-grad-4", "🚪"), unsafe_allow_html=True)
    with c5:
        active_surgeons = df[df["SURGEON_NAME"] != "Unknown Surgeon"]["SURGEON_NAME"].nunique()
        st.markdown(kpi_card_html("Active Surgeons", active_surgeons, "Performed at least 1 surgery", "kpi-grad-5", "👨‍⚕️"), unsafe_allow_html=True)

    # Show department breakdown if "All" is selected
    if selected_dept in (None, "", "All"):
        dept_breakdown = df.groupby('DEPTNAME').size().reset_index(name='Count')
        dept_breakdown = dept_breakdown.sort_values('Count', ascending=False)
        
        with st.expander("🏥 View Breakdown by Department"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.dataframe(dept_breakdown.style.format({"Count": "{:,}"}), use_container_width=True)
            with col2:
                st.metric("Total Departments", len(dept_breakdown))
                if not dept_breakdown.empty:
                    top_dept = dept_breakdown.iloc[0]
                    st.metric("Top Department", top_dept['DEPTNAME'], f"{top_dept['Count']:,} surgeries")

    st.markdown("---")

    # === 1. TOP PROCEDURES ===
    st.subheader("📊 Top 20 Procedures Performed")
    proc = df["PROCEDURE_NAME"].value_counts().head(20).reset_index()
    proc.columns = ["Procedure", "Count"]

    col1, col2 = st.columns([3, 1])
    with col1:
        chart = alt.Chart(proc).mark_bar(color="#00d4aa").encode(
            y=alt.Y("Procedure:N", sort="-x"),
            x="Count:Q",
            tooltip=["Procedure", "Count"]
        ).properties(height=520)
        st.altair_chart(chart, use_container_width=True)
    with col2:
        st.metric("Total Unique Procedures", len(df["PROCEDURE_NAME"].unique()))
        if not proc.empty:
            st.metric("Most Common", proc.iloc[0]["Procedure"])
            st.metric("Performed", f"{proc.iloc[0]['Count']:,} times")

    # === 2. FULL PROCEDURE LIST ===
    with st.expander("📋 Complete Procedure Master List (All Performed)", expanded=False):
        full_proc = df["PROCEDURE_NAME"].value_counts().reset_index()
        full_proc.columns = ["Procedure Name", "Times Performed"]
        full_proc = full_proc.sort_values("Times Performed", ascending=False).reset_index(drop=True)
        full_proc.insert(0, "Rank", range(1, len(full_proc)+1))

        search = st.text_input("🔍 Search procedure", key="proc_search_tab4")
        display = full_proc[full_proc["Procedure Name"].str.contains(search, case=False, na=False)] if search else full_proc

        st.dataframe(display.style.format({"Times Performed": "{:,}"}), use_container_width=True, height=500)

        csv = full_proc.to_csv(index=False).encode()
        st.download_button("📥 Download Full List (CSV)", data=csv,
                           file_name=f"Procedures_{from_date}_to_{to_date}.csv", mime="text/csv")

    st.markdown("---")

    # === 3. ALL STAFF LEADERBOARDS (16 ROLES) ===
    st.subheader("👨‍⚕️ Staff Leaderboards by Role")

    # Create tabs for main roles
    tab_roles = st.tabs([
        "🔪 Surgeons", 
        "💉 Anaesthetists", 
        "🩺 Assisting Surgeons",
        "💊 Assisting Anaesthetists",
        "❤️ Perfusionists",
        "👩‍⚕️ R Nurses",
        "🏥 SC Nurses",
        "👨‍⚕️ Nurses",
        "🔧 Technicians",
        "📡 More Roles"
    ])

    # Define role configurations (main 8)
    roles_config = [
        {"col": "SURGEON_NAME", "title": "Surgeon", "color": "#ff6b6b", "exclude": ["Unknown Surgeon"]},
        {"col": "ANAESTHETIST_NAME", "title": "Anaesthetist", "color": "#4ecdc4", "exclude": ["Not Recorded"]},
        {"col": "ASST_SURGEON_NAME", "title": "Assisting Surgeon", "color": "#f39c12", "exclude": ["-"]},
        {"col": "ASST_ANAESTHETIST_NAME", "title": "Assisting Anaesthetist", "color": "#9b59b6", "exclude": ["-"]},
        {"col": "PERFUSIONIST_NAME", "title": "Perfusionist", "color": "#e74c3c", "exclude": ["-"]},
        {"col": "RNURSE_NAME", "title": "R Nurse", "color": "#1abc9c", "exclude": ["-"]},
        {"col": "SCNURSE_NAME", "title": "SC Nurse", "color": "#3498db", "exclude": ["-"]},
        {"col": "NURSE_NAME", "title": "Nurse", "color": "#16a085", "exclude": ["-"]},
        {"col": "TECHNICIAN_NAME", "title": "Technician", "color": "#34495e", "exclude": ["-"]}
    ]

    # Render first 9 tabs
    for i, (tab, config) in enumerate(zip(tab_roles[:9], roles_config)):
        with tab:
            filtered_df = df[
                df[config["col"]].notna() & 
                (~df[config["col"]].isin(config["exclude"]))
            ]
            
            if filtered_df.empty:
                st.info(f"No {config['title']} data available for this period.")
                continue
            
            role_count = filtered_df[config["col"]].value_counts().head(25).reset_index()
            role_count.columns = [config["title"], "Cases"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"Total {config['title']}s", len(role_count))
            with col2:
                st.metric("Total Cases", role_count["Cases"].sum())
            with col3:
                if not role_count.empty:
                    st.metric("Top Performer", role_count.iloc[0][config["title"]], f"{role_count.iloc[0]['Cases']:,} cases")
            
            st.altair_chart(
                alt.Chart(role_count).mark_bar(color=config["color"]).encode(
                    y=alt.Y(f"{config['title']}:N", sort="-x"),
                    x="Cases:Q",
                    tooltip=[config["title"], "Cases"]
                ).properties(height=min(600, len(role_count) * 30 + 100)), 
                use_container_width=True
            )
            
            st.dataframe(role_count.style.format({"Cases": "{:,}"}), use_container_width=True)

    # Last tab: More roles
    with tab_roles[9]:
        st.markdown("#### Additional Specialized Roles")
        
        additional_roles = [
            ("TECHCATH_NAME", "Cath Lab Technician"),
            ("PHYSICIANCATH_NAME", "Cath Lab Physician"),
            ("ASSTPHYCATH_NAME", "Assisting Cath Physician"),
            ("IOMTECH_NAME", "IOM Technician"),
            ("CIRCNURSE_NAME", "Circulating Nurse"),
            ("ASSTNURSE_NAME", "Assistant Nurse"),
            ("WARDNURSE_NAME", "Ward Nurse")
        ]
        
        for col_name, role_title in additional_roles:
            filtered_df = df[df[col_name].notna() & (df[col_name] != "-")]
            
            if not filtered_df.empty:
                role_count = filtered_df[col_name].value_counts().head(10).reset_index()
                role_count.columns = [role_title, "Cases"]
                
                with st.expander(f"📊 {role_title} ({len(role_count)} staff)", expanded=False):
                    st.dataframe(role_count.style.format({"Cases": "{:,}"}), use_container_width=True)

    st.markdown("---")

    # === 5. FULL SURGERY REGISTER ===
    with st.expander("📄 View Full Surgery Register (All Details)", expanded=False):
        reg = df[[
            "SURGERYDATE", "MRN", "DEPTNAME", "PROCEDURE_NAME", "PROC_CATEGORY", "PROC_SUBCATEGORY",
            "SURGEON_NAME", "ANAESTHETIST_NAME", "ASST_SURGEON_NAME", "ASST_ANAESTHETIST_NAME",
            "PERFUSIONIST_NAME", "RNURSE_NAME", "SCNURSE_NAME", "NURSE_NAME", 
            "OTNUMBER", "ANAESTHESIA"
        ]].copy()
        
        reg["SURGERYDATE"] = pd.to_datetime(reg["SURGERYDATE"]).dt.strftime("%d-%b-%Y")
        reg.rename(columns={
            "SURGERYDATE": "Date",
            "MRN": "Patient",
            "DEPTNAME": "Department",
            "PROCEDURE_NAME": "Procedure",
            "PROC_CATEGORY": "Category",
            "PROC_SUBCATEGORY": "Subcategory",
            "SURGEON_NAME": "Surgeon",
            "ANAESTHETIST_NAME": "Anaesthetist",
            "ASST_SURGEON_NAME": "Asst Surgeon",
            "ASST_ANAESTHETIST_NAME": "Asst Anaesthetist",
            "PERFUSIONIST_NAME": "Perfusionist",
            "RNURSE_NAME": "R Nurse",
            "SCNURSE_NAME": "SC Nurse",
            "NURSE_NAME": "Nurse",
            "OTNUMBER": "OT",
            "ANAESTHESIA": "Anaesthesia Type"
        }, inplace=True)
        
        st.dataframe(reg, use_container_width=True, height=500)
        
        csv_reg = reg.to_csv(index=False).encode()
        st.download_button(
            "📥 Download Full Register (CSV)",
            data=csv_reg,
            file_name=f"Surgery_Register_{from_date}_to_{to_date}.csv",
            mime="text/csv"
        )

# Close DB connection
try:
    conn.close()
except Exception:
    pass