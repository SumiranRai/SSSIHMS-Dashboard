# pages/dashboard.py
"""
Hospital Dashboard - COMPLETE file with all updates.

Features:
- Wide layout
- Tabs: General KPIs, Operational Efficiency, Financial, Quality & Safety, Surgery Details, Reports, Stats
- Sidebar: Date range, Department, Hospital, Ordering Dept, Radiology modality, Doctor
- Sidebar action buttons: Logout, Change Password, Admin Panel
- Default to user's hospital ID (from STAFFMASTER.HOSPITALID via session state)
- Default date range: current month (first day to today)
- Auto-load on first visit, then require "Load Data" button for filter changes
- Date range: 2000 to current year
"""

import streamlit as st
import pandas as pd
import oracledb
import altair as alt
import io
import zipfile
from datetime import date, datetime, timedelta
import streamlit.components.v1 as components

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Elasticsearch configuration
ES_HOST = "localhost"
ES_PORT = 9200
ES_INDEX_PREFIX = "hospital_"

def get_es_client():
    """Create Elasticsearch client"""
    try:
        es = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
        if es.ping():
            return es
        else:
            st.warning("⚠️ Elasticsearch is not responding")
            return None
    except Exception as e:
        st.warning(f"⚠️ Elasticsearch connection failed: {e}")
        return None

# Initialize ES client
es_client = get_es_client()

# -------------------------
# Page config (must be first Streamlit call)
# -------------------------
st.set_page_config(page_title="🏥 SSSIHMS Hospital Dashboard", page_icon="🏥", layout="wide")

# -------------------------
# Access guard (login handled in app.py)
# -------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 Please log in from the main page.")
    st.stop()

# -------------------------
# Oracle connection helper - configure lib_dir if needed
# -------------------------
# Uncomment & set lib_dir if you use Oracle Instant Client:
# oracledb.init_oracle_client(lib_dir=r"C:\path\to\instantclient")
def get_conn():
    return oracledb.connect(
        user="hisapp",
        password="his@2025",
        dsn="192.168.21.6:1521/hisdb"
    )

try:
    conn = get_conn()
except Exception as e:
    st.error(f"Failed to connect to Oracle DB: {e}")
    st.stop()

# -------------------------
# Styling
# -------------------------
st.markdown(
    """
<style>
.kpi-card { padding: 18px; border-radius: 14px; color: white; text-align: center; transition: transform .18s ease, box-shadow .18s ease; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 10px; }
.kpi-card:hover { transform: translateY(-6px); box-shadow: 0 8px 30px rgba(0,0,0,0.5); }
.kpi-title { font-size:14px; opacity:0.92; margin-bottom:6px; }
.kpi-value { font-size:26px; font-weight:800; margin-top:4px; }
.kpi-sub { font-size:12px; opacity:0.85; margin-top:6px; }
.kpi-grad-1 { background: linear-gradient(135deg,#0f7769,#0ea77c); }
.kpi-grad-2 { background: linear-gradient(135deg,#1769ff,#47a7ff); }
.kpi-grad-3 { background: linear-gradient(135deg,#f6a623,#ffb86b); }
.kpi-grad-4 { background: linear-gradient(135deg,#ff3b30,#ff6b6b); }
.kpi-grad-5 { background: linear-gradient(135deg,#7a5cff,#a588ff); }
.kpi-grad-6 { background: linear-gradient(135deg,#00bfa6,#2ee6c8); }
.sidebar-buttons { margin-top: 12px; display:flex; gap:8px; }
</style>
""",
    unsafe_allow_html=True,
)

def kpi_card_html(title, value, subtext, grad_class="kpi-grad-1", icon=""):
    return f"""
    <div class="kpi-card {grad_class}">
        <div class="kpi-title">{icon} {title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{subtext}</div>
    </div>
    """

# -------------------------
# Sidebar: filters & actions
# -------------------------
st.sidebar.header("Filters")

# Action buttons -> navigate to existing pages
st.sidebar.markdown("<div class='sidebar-buttons'>", unsafe_allow_html=True)
if st.sidebar.button("🔒 Logout"):
    st.switch_page("app.py")
if st.sidebar.button("🔑 Change Password"):
    st.switch_page("pages/change_password.py")
if st.sidebar.button("⚙️ Admin Panel"):
    st.switch_page("pages/admin_panel.py")
st.sidebar.markdown("</div>", unsafe_allow_html=True)

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

# Update the sidebar display (around line 174):
st.sidebar.markdown(f"**Category:** {selected_category}")

# Doctor selector
try:
    if selected_hospital in (None, "", "All Hospitals"):
        doctors_df = pd.read_sql("SELECT STAFFID, STAFFNAME FROM STAFFMASTER ORDER BY STAFFNAME", conn)
    else:
        safe_h = selected_hospital.replace("'", "''")
        doctors_df = pd.read_sql(f"SELECT STAFFID, STAFFNAME FROM STAFFMASTER WHERE HOSPITALID = '{safe_h}' ORDER BY STAFFNAME", conn)
    doctors_list = ["All Doctors"] + doctors_df.apply(lambda r: f"{r['STAFFID']}|{r['STAFFNAME']}", axis=1).tolist()
except Exception:
    doctors_list = ["All Doctors"]
selected_doctor = st.sidebar.selectbox("Doctor (for surgery KPIs)", doctors_list, index=0)

st.sidebar.markdown(f"**Range:** {from_date} → {to_date}")
st.sidebar.markdown(f"**Department:** {selected_dept}")
st.sidebar.markdown(f"**Hospital:** {selected_hospital}")
st.sidebar.markdown(f"**Category:** {selected_category}")

# -------------------------
# Load Data Logic - Auto-load first time, then require button
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
    st.info("ℹ️ Dashboard loaded with default filters (your hospital, current month). Change filters and click **'Load Data'** to refresh.")
    st.session_state.dashboard_first_load = False

# Show message if data not loaded yet (only after first load)
if not st.session_state.get("data_loaded", False):
    st.info("👆 Please adjust your filters and click **'Load Data'** button in the sidebar to refresh dashboard.")
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

def parse_doctor(sel):
    if not sel or sel == "All Doctors":
        return None, None
    if "|" in sel:
        sid, sname = sel.split("|", 1)
        return sid, sname
    return sel, sel

doc_id, doc_name = parse_doctor(selected_doctor)

#Elastic
def create_es_indices():
    """Create Elasticsearch indices with mappings"""
    if not es_client:
        return False
    
    indices_config = {
        f"{ES_INDEX_PREFIX}patients": {
            "mappings": {
                "properties": {
                    "mrn": {"type": "keyword"},
                    "patient_name": {"type": "text"},
                    "dob": {"type": "date"},
                    "age": {"type": "integer"},
                    "gender": {"type": "keyword"},
                    "state": {"type": "keyword"},
                    "admission_date": {"type": "date"},
                    "discharge_date": {"type": "date"},
                    "department": {"type": "keyword"},
                    "hospital_id": {"type": "keyword"},
                    "diagnosis": {"type": "text"},
                    "indexed_at": {"type": "date"}
                }
            }
        },
        f"{ES_INDEX_PREFIX}surgeries": {
            "mappings": {
                "properties": {
                    "surgery_id": {"type": "keyword"},
                    "mrn": {"type": "keyword"},
                    "surgeon_id": {"type": "keyword"},
                    "surgeon_name": {"type": "text"},
                    "surgery_date": {"type": "date"},
                    "surgery_type": {"type": "keyword"},
                    "department": {"type": "keyword"},
                    "hospital_id": {"type": "keyword"},
                    "duration": {"type": "integer"},
                    "indexed_at": {"type": "date"}
                }
            }
        },
        f"{ES_INDEX_PREFIX}reports": {
            "mappings": {
                "properties": {
                    "accession_num": {"type": "keyword"},
                    "mrn": {"type": "keyword"},
                    "note_name": {"type": "text"},
                    "visit_type": {"type": "keyword"},
                    "visit_date": {"type": "date"},
                    "done_by": {"type": "keyword"},
                    "department": {"type": "keyword"},
                    "note_data": {"type": "text"},
                    "hospital_id": {"type": "keyword"},
                    "indexed_at": {"type": "date"}
                }
            }
        },
        f"{ES_INDEX_PREFIX}stats": {
            "mappings": {
                "properties": {
                    "category": {"type": "keyword"},
                    "subcatg": {"type": "keyword"},
                    "subcatgl2": {"type": "keyword"},
                    "the_date": {"type": "date"},
                    "the_value": {"type": "integer"},
                    "ordering_dept": {"type": "keyword"},
                    "hospital_id": {"type": "keyword"},
                    "indexed_at": {"type": "date"}
                }
            }
        }
    }
    
    for index_name, config in indices_config.items():
        try:
            if not es_client.indices.exists(index=index_name):
                es_client.indices.create(index=index_name, body=config)
                st.success(f"✅ Created index: {index_name}")
        except Exception as e:
            st.error(f"❌ Failed to create index {index_name}: {e}")
            return False
    
    return True

def index_patients_to_es(from_date, to_date, batch_size=1000):
    """Index patient data from Oracle to Elasticsearch"""
    if not es_client:
        return 0
    
    query = f"""
        SELECT 
            P.MRN, P.PATIENTNAME, P.DOB, P.GENDER, P.STATE,
            I.DOA as ADMISSION_DATE, I.DAYSCARED, I.DEPTCODE,
            I.HOSPITALID, I.ADMISSIONTYPE
        FROM PATIENT P
        LEFT JOIN INPATIENT I ON P.MRN = I.MRN
        WHERE I.DOA BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') 
                        AND TO_DATE('{to_date}', 'YYYY-MM-DD')
    """
    
    try:
        df = pd.read_sql(query, conn)
        
        actions = []
        for _, row in df.iterrows():
            doc = {
                "_index": f"{ES_INDEX_PREFIX}patients",
                "_id": f"{row['MRN']}_{row.get('ADMISSION_DATE', '')}",
                "_source": {
                    "mrn": row['MRN'],
                    "patient_name": row.get('PATIENTNAME', ''),
                    "dob": row.get('DOB'),
                    "gender": row.get('GENDER', ''),
                    "state": row.get('STATE', ''),
                    "admission_date": row.get('ADMISSION_DATE'),
                    "department": row.get('DEPTCODE', ''),
                    "hospital_id": row.get('HOSPITALID', ''),
                    "admission_type": row.get('ADMISSIONTYPE', ''),
                    "days_cared": row.get('DAYSCARED', 0),
                    "indexed_at": datetime.now()
                }
            }
            actions.append(doc)
        
        if actions:
            success, failed = bulk(es_client, actions, raise_on_error=False)
            return success
        return 0
        
    except Exception as e:
        st.error(f"Failed to index patients: {e}")
        return 0


def index_reports_to_es(batch_size=1000):
    """Index reports from NOTESDATA to Elasticsearch"""
    if not es_client:
        return 0
    
    query = """
        SELECT ACCESSION_NUM, MRN, NOTENAME, VISITTYPE, VISITDATE,
               DONEBY, DEPTNAME, NOTEDATA
        FROM NOTESDATA
        WHERE ROWNUM <= 10000
    """
    
    try:
        df = pd.read_sql(query, conn)
        
        actions = []
        for _, row in df.iterrows():
            # Extract text from CLOB
            note_data = ""
            if row.get('NOTEDATA'):
                try:
                    note_data = row['NOTEDATA'].read() if hasattr(row['NOTEDATA'], 'read') else str(row['NOTEDATA'])
                except:
                    note_data = str(row['NOTEDATA'])
            
            doc = {
                "_index": f"{ES_INDEX_PREFIX}reports",
                "_id": row['ACCESSION_NUM'],
                "_source": {
                    "accession_num": row['ACCESSION_NUM'],
                    "mrn": row['MRN'],
                    "note_name": row.get('NOTENAME', ''),
                    "visit_type": row.get('VISITTYPE', ''),
                    "visit_date": row.get('VISITDATE'),
                    "done_by": row.get('DONEBY', ''),
                    "department": row.get('DEPTNAME', ''),
                    "note_data": note_data[:10000],  # Limit size
                    "indexed_at": datetime.now()
                }
            }
            actions.append(doc)
        
        if actions:
            success, failed = bulk(es_client, actions, raise_on_error=False)
            return success
        return 0
        
    except Exception as e:
        st.error(f"Failed to index reports: {e}")
        return 0
    
    
# -------------------------
# Data functions
# -------------------------
def load_inpatients(from_date, to_date, dept_name):
    dept_filter = "1=1" if dept_name in (None, "", "All") else f"D.DEPTNAME = '{safe_sql(dept_name)}'"
    
    # Fixed hospital filter - use only I.HOSPITALID
    if selected_hospital in (None, "", "All Hospitals"):
        hosp_filter = "1=1"
    else:
        hosp_filter = f"I.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    q = (
        "SELECT I.INPATIENTID, I.MRN, I.DAYSCARED, I.ADMISSIONTYPE, I.DOA, P.DEATHDATE, I.DEPTCODE, I.HOSPITALID "
        "FROM INPATIENT I "
        "JOIN PATIENT P ON I.MRN = P.MRN "
        "JOIN DEPARTMENT D ON I.DEPTCODE = D.DEPTCODE AND I.HOSPITALID = D.HOSPITALID "
        f"WHERE {dept_filter} AND {hosp_filter} "
        f"AND I.DOA BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
    )
    try:
        return pd.read_sql(q, conn)
    except Exception:
        return pd.DataFrame()

def load_outpatients(from_date, to_date, dept_name):
    dept_filter = "1=1" if dept_name in (None, "", "All") else f"D.DEPTNAME = '{safe_sql(dept_name)}'"
    
    # Fixed hospital filter - use only O.HOSPITALID
    if selected_hospital in (None, "", "All Hospitals"):
        hosp_filter = "1=1"
    else:
        hosp_filter = f"O.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    q = (
        "SELECT O.OUTPATIENTID, O.MRN, O.DOV, O.DEPTNAME, O.HOSPITALID "
        "FROM OUTPATIENT O "
        "JOIN DEPARTMENT D ON O.DEPTNAME = D.DEPTNAME AND O.HOSPITALID = D.HOSPITALID "
        f"WHERE {dept_filter} AND {hosp_filter} "
        f"AND O.DOV BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
    )
    try:
        return pd.read_sql(q, conn)
    except Exception:
        return pd.DataFrame()

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

def admission_type_breakdown(from_date, to_date, dept_name):
    dept_filter = "1=1" if dept_name in (None, "", "All") else f"D.DEPTNAME = '{safe_sql(dept_name)}'"
    
    # Fixed hospital filter
    if selected_hospital in (None, "", "All Hospitals"):
        hosp_filter = "1=1"
    else:
        hosp_filter = f"I.HOSPITALID = '{safe_sql(selected_hospital)}'"
    
    q = (
        "SELECT NVL(ADMISSIONTYPE,'UNKNOWN') AS ADMISSIONTYPE, COUNT(*) AS CNT "
        "FROM INPATIENT I JOIN DEPARTMENT D ON I.DEPTCODE = D.DEPTCODE AND I.HOSPITALID = D.HOSPITALID "
        f"WHERE {dept_filter} AND {hosp_filter} "
        f"AND I.DOA BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD') "
        "GROUP BY NVL(ADMISSIONTYPE,'UNKNOWN') ORDER BY CNT DESC"
    )
    try:
        return pd.read_sql(q, conn)
    except Exception:
        return pd.DataFrame(columns=['ADMISSIONTYPE','CNT'])

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

# -------------------------
# Reports tab functions
# -------------------------
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

# -------------------------
# Tabs and rendering
# -------------------------
tabs = st.tabs(["🏠 General KPIs", "⚡ Operational Efficiency", "💰 Financial", 
                "✅ Quality & Safety", "🩺 Surgery Details", "📄 Reports", "📊 Stats"])

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
    with p1:
        st.markdown(kpi_card_html("Bed Occupancy Rate", "N/A", "Requires bed census table", "kpi-grad-2", "🛏️"), unsafe_allow_html=True)
    with p2:
        st.markdown(kpi_card_html("ER Wait Times", "N/A", "Requires ER timestamps", "kpi-grad-3", "🚑"), unsafe_allow_html=True)
    with p3:
        st.markdown(kpi_card_html("Surgery Wait Times", "N/A", "Requires booking timestamps", "kpi-grad-5", "⏳"), unsafe_allow_html=True)
    with p4:
        st.markdown(kpi_card_html("Staff : Patients", spr_value, "Direct DB value if available", "kpi-grad-6", "👩‍⚕️"), unsafe_allow_html=True)

# ---- TAB 1: Operational Efficiency (Radiology + State-wise) ----
# Replace the entire TAB 1 section (Operational Efficiency) with this fixed version:

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
            st.markdown("### 📁 Level 1: Categories")
            st.info("👆 Click on any category card to drill down")
            
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
                        # Display KPI card
                        st.markdown(
                            kpi_card_html(
                                f"{m['CATEGORY']}", 
                                f"{m['TOTAL']:,}", 
                                f"Avg/day {m['AVG_PER_DAY']:.2f} • Max {m['MAX_ENTRY']:,}", 
                                grad_class="kpi-grad-1", 
                                icon="📁"
                            ), 
                            unsafe_allow_html=True
                        )
                        
                        # Clickable button below card
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
    
    # # State-wise metrics (keep as is)
    # st.subheader("State-wise Metrics (STATESTATS)")
    # if use_year_month:
    #     ss_df = state_stats_aggregate(from_date, to_date, use_year_month=True, sel_year=sel_year, sel_month=months.index(sel_month)+1)
    # else:
    #     ss_df = state_stats_aggregate(from_date, to_date, use_year_month=False)
    # if not ss_df.empty:
    #     st.altair_chart(alt.Chart(ss_df).mark_bar().encode(
    #         x=alt.X('STATE:N', sort='-y', title='State'),
    #         y=alt.Y('CNT:Q', title='Count'),
    #         tooltip=['STATE','CNT']
    #     ).properties(width=900, height=450))
    # else:
    #     st.info("No state-wise data available for selected filters.")

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

# ---- Surgery Details tab ----
with tabs[4]:
    st.header("Surgery Details")
    surg_metrics = load_surgery_metrics(from_date, to_date, selected_dept, doc_id)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(kpi_card_html("Total Surgeries", surg_metrics["total"], f"{from_date} → {to_date}", "kpi-grad-2", "🔪"), unsafe_allow_html=True)
    with s2:
        if surg_metrics["bydoc"] is not None:
            st.markdown(kpi_card_html(f"Surgeries — {doc_name}", surg_metrics["bydoc"], f"Doctor {doc_id}", "kpi-grad-1", "🩺"), unsafe_allow_html=True)
        else:
            st.markdown(kpi_card_html("Surgeries — Selected Doctor", "N/A", "Select a doctor", "kpi-grad-1", "🩺"), unsafe_allow_html=True)
    with s3:
        st.markdown(kpi_card_html("Top Surgery Type", surg_metrics["top_type"], "Most frequent surgery", "kpi-grad-3", "🏷️"), unsafe_allow_html=True)
    with s4:
        st.markdown(kpi_card_html("Daily Avg Surgeries", f"{surg_metrics['daily_avg']:.2f}", f"{(to_date-from_date).days+1} days", "kpi-grad-4", "📅"), unsafe_allow_html=True)

    st.markdown("---")
    try:
        recent_q = (
            "SELECT SURGERYID, MRN, SURGEONID, SURGERYDATE, SURGERYTYPE, DEPTCODE, HOSPITALID "
            "FROM SURGERY "
            f"WHERE SURGERYDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD') "
            "ORDER BY SURGERYDATE DESC FETCH FIRST 200 ROWS ONLY"
        )
        recent_df = pd.read_sql(recent_q, conn)
        if not recent_df.empty:
            st.dataframe(recent_df)
        else:
            st.info("No surgeries found in the selected date range.")
    except Exception:
        st.info("Failed to fetch recent surgeries (table may be missing).")

# ---- Reports tab ----
with tabs[5]:
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
with tabs[6]:
    st.header("📊 Patient Stats")

    avg_age, age_dist = compute_age_distribution()
    st.subheader("Age Distribution")
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

# Close DB connection
try:
    conn.close()
except Exception:
    pass