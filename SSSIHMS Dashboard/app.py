import streamlit as st
import pandas as pd
import oracledb
import altair as alt

# --- Oracle DB Connection ---
try:
    oracledb.init_oracle_client(lib_dir=r"C:\Users\sumir\Downloads\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9")

    conn = oracledb.connect(
        user="hisapp",
        password="his@2025",
        dsn="192.168.21.6:1521/hisdb"
    )
    st.sidebar.success("✅ Connected to Oracle Database")

except Exception as e:
    st.sidebar.error(f"❌ Connection failed: {e}")
    st.stop()

# --- Dashboard Title ---
st.title("🏥 Hospital Intelligence Dashboard")

# --- Sidebar Filters ---
st.sidebar.header("🎚️ Filters")

# Get filter values dynamically
def get_unique_values(col_name, table):
    try:
        query = f"SELECT DISTINCT {col_name} FROM {table} WHERE {col_name} IS NOT NULL FETCH FIRST 100 ROWS ONLY"
        return [r[0] for r in conn.cursor().execute(query).fetchall()]
    except:
        return []

hospital_options = get_unique_values("HOSPITALID", "INPATIENT")
dept_options = get_unique_values("DEPTCODE", "DEPARTMENT")

hospital = st.sidebar.selectbox("Select Hospital", ["All"] + hospital_options)
department = st.sidebar.selectbox("Select Department", ["All"] + dept_options)

# --- Data Query ---
query = """
SELECT 
    P.MRN, P.PNAME, P.GENDER, P.DOB,
    I.INPATIENTID, I.DOA, I.DOD, I.DEPTCODE AS INPAT_DEPT, I.STATUS AS INPATIENT_STATUS,
    O.OUTPATIENTID, O.DOV, O.DEPTNAME AS OUTPAT_DEPT, O.DIAGNOSIS AS OUTPAT_DIAG
FROM PATIENT P
LEFT JOIN INPATIENT I ON P.MRN = I.MRN
LEFT JOIN OUTPATIENT O ON P.MRN = O.MRN
WHERE 1=1
"""

params = {}

if hospital != "All":
    query += """
        AND P.MRN IN (
            SELECT MRN FROM INPATIENT WHERE HOSPITALID = :hospital
            UNION
            SELECT MRN FROM OUTPATIENT WHERE HOSPITALID = :hospital
        )
    """
    params["hospital"] = hospital

if department != "All":
    query += " AND (I.DEPTCODE = :department OR O.DEPTNAME = :department)"
    params["department"] = department

query = f"""
SELECT * FROM (
    {query}
) WHERE ROWNUM <= 1000
"""

# --- Fetch Data ---
df = pd.DataFrame()
try:
    df = pd.read_sql(query, conn, params=params)
except Exception as e:
    st.error(f"⚠️ Query Error: {e}")

# --- Tabs for Sections ---
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🧾 Patients", "🏥 Departments", "📊 Analytics"])

# --- Overview Tab ---
with tab1:
    st.subheader("📊 Key Performance Indicators")

    if not df.empty:
        total_patients = df['MRN'].nunique()
        total_inpatients = df['INPATIENTID'].nunique()
        total_outpatients = df['OUTPATIENTID'].nunique()
        gender_counts = df['GENDER'].value_counts().to_dict()

        col1, col2, col3 = st.columns(3)
        col1.metric("👨‍⚕️ Total Patients", total_patients)
        col2.metric("🏥 Inpatients", total_inpatients)
        col3.metric("🚑 Outpatients", total_outpatients)

        st.markdown("### 🧬 Gender Distribution")
        gender_chart = alt.Chart(df).mark_arc().encode(
            theta='count(GENDER):Q',
            color='GENDER:N',
            tooltip=['GENDER', 'count(GENDER):Q']
        ).properties(width=400, height=300)
        st.altair_chart(gender_chart, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

# --- Patients Tab ---
with tab2:
    st.subheader("🩺 Patient Details (Limited to 1000 Rows)")
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No patient records found.")

# --- Departments Tab ---
with tab3:
    st.subheader("🏨 Inpatients by Department")
    if not df.empty:
        dept_counts = df['INPAT_DEPT'].value_counts().reset_index()
        dept_counts.columns = ["Department", "Inpatients"]
        chart = alt.Chart(dept_counts).mark_bar().encode(
            x=alt.X('Department:N', sort='-y'),
            y='Inpatients:Q',
            color='Department:N',
            tooltip=['Department', 'Inpatients']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No inpatient data found.")

# --- Analytics Tab ---
with tab4:
    st.subheader("📅 Admissions Over Time")
    if not df.empty and 'DOA' in df.columns:
        df['DOA'] = pd.to_datetime(df['DOA'], errors='coerce')
        admissions = df.dropna(subset=['DOA'])
        if not admissions.empty:
            line_chart = alt.Chart(admissions).mark_line(point=True).encode(
                x='yearmonth(DOA):T',
                y='count(INPATIENTID):Q',
                color='INPAT_DEPT:N',
                tooltip=['INPAT_DEPT', 'count(INPATIENTID):Q']
            ).properties(height=400)
            st.altair_chart(line_chart, use_container_width=True)
        else:
            st.warning("No admission date data available.")
    else:
        st.info("No inpatient admission data found.")

# --- Footer ---
st.markdown("---")
st.caption("© 2025 Hospital Analytics Dashboard | Built with Streamlit and Oracle")

# --- Close DB Connection ---
conn.close()
