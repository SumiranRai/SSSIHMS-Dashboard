# hospital_dashboard_tabs_daterange.py
import streamlit as st
import pandas as pd
import oracledb
import altair as alt
from datetime import datetime, date

# --- Oracle Client Setup ---
oracledb.init_oracle_client(
    lib_dir=r"C:\Users\sumir\Downloads\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9"
)

conn = oracledb.connect(
    user="hisapp",
    password="his@2025",
    dsn="192.168.21.6:1521/hisdb"
)

st.set_page_config(page_title="Hospital Dashboard", layout="wide")
st.title("🏥 Hospital Management Dashboard (Date Range + Tabs)")

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Date Range Filter
col1, col2 = st.sidebar.columns(2)
default_from = date(datetime.now().year, 1, 1)
default_to = date.today()
from_date = col1.date_input("From Date", default_from)
to_date = col2.date_input("To Date", default_to)

# Department Filter
dept_query = "SELECT DISTINCT DEPTNAME FROM DEPARTMENT ORDER BY DEPTNAME"
departments = pd.read_sql(dept_query, conn)['DEPTNAME'].tolist()
departments = ['All'] + departments
selected_dept = st.sidebar.selectbox("Department", departments, index=0)

# --- Helper Function ---
def dept_condition(selected):
    return "1=1" if selected == 'All' else f"D.DEPTNAME = '{selected}'"

dept_cond = dept_condition(selected_dept)

# --- SQL Date Filter Conditions ---
date_cond_inp = f"I.DOA BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
date_cond_out = f"O.DOV BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"
date_cond_surg = f"S.SURGERYDATE BETWEEN TO_DATE('{from_date}', 'YYYY-MM-DD') AND TO_DATE('{to_date}', 'YYYY-MM-DD')"

# --- Tabs for Segments ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 KPIs",
    "🏥 Department Metrics",
    "🩺 Surgery per Doctor",
    "📈 Inpatient Trend",
    "🧾 Admission Breakdown",
    "📋 Detailed Reports"
])

# --- KPIs ---
with tab1:
    st.subheader("Key Performance Indicators")

    inpatients = pd.read_sql(
        f"SELECT COUNT(*) AS CNT FROM INPATIENT I JOIN DEPARTMENT D ON I.DEPTCODE=D.DEPTCODE WHERE {date_cond_inp} AND {dept_cond}",
        conn
    )['CNT'][0]

    outpatients = pd.read_sql(
        f"SELECT COUNT(*) AS CNT FROM OUTPATIENT O JOIN DEPARTMENT D ON O.DEPTCODE=D.DEPTCODE WHERE {date_cond_out} AND {dept_cond}",
        conn
    )['CNT'][0]

    surgeries = pd.read_sql(
        f"SELECT COUNT(*) AS CNT FROM SURGERY S JOIN DEPARTMENT D ON S.DEPTCODE=D.DEPTCODE WHERE {date_cond_surg} AND {dept_cond}",
        conn
    )['CNT'][0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Inpatients", inpatients)
    c2.metric("Outpatients", outpatients)
    c3.metric("Surgeries", surgeries)

# --- Department Metrics ---
with tab2:
    st.subheader("Department-wise Summary")

    dept_kpi_query = f"""
    SELECT D.DEPTNAME,
           COUNT(DISTINCT I.INPATIENTID) AS INPATIENTS,
           COUNT(DISTINCT O.OUTPATIENTID) AS OUTPATIENTS,
           COUNT(DISTINCT S.SURGERYID) AS SURGERIES
    FROM DEPARTMENT D
    LEFT JOIN INPATIENT I ON D.DEPTCODE = I.DEPTCODE AND {date_cond_inp}
    LEFT JOIN OUTPATIENT O ON D.DEPTCODE = O.DEPTCODE AND {date_cond_out}
    LEFT JOIN SURGERY S ON D.DEPTCODE = S.DEPTCODE AND {date_cond_surg}
    GROUP BY D.DEPTNAME
    ORDER BY INPATIENTS+OUTPATIENTS+SURGERIES DESC
    """
    dept_kpi = pd.read_sql(dept_kpi_query, conn)
    st.dataframe(dept_kpi, use_container_width=True)

# --- Surgery per Doctor ---
with tab3:
    st.subheader("Surgeries per Doctor")

    surgery_metrics_query = f"""
    SELECT D.DEPTNAME, SM.STAFFNAME AS DOCTOR, COUNT(S.SURGERYID) AS SURGERY_COUNT
    FROM SURGERY S
    JOIN DEPARTMENT D ON S.DEPTCODE = D.DEPTCODE
    JOIN STAFFMASTER SM ON S.SURGEONID = SM.STAFFID
    WHERE {date_cond_surg} AND {dept_cond}
    GROUP BY D.DEPTNAME, SM.STAFFNAME
    ORDER BY SURGERY_COUNT DESC
    """
    surgery_metrics = pd.read_sql(surgery_metrics_query, conn)

    if not surgery_metrics.empty:
        chart = alt.Chart(surgery_metrics).mark_bar().encode(
            x='DOCTOR:N',
            y='SURGERY_COUNT:Q',
            color='DEPTNAME:N',
            tooltip=['DOCTOR', 'DEPTNAME', 'SURGERY_COUNT']
        ).properties(title="Surgeries per Doctor")
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No surgery data found for selected filters.")

# --- Inpatient Trend ---
with tab4:
    st.subheader("Monthly Inpatient Trend")

    trend_query = f"""
    SELECT D.DEPTNAME,
           EXTRACT(MONTH FROM I.DOA) AS MONTH,
           COUNT(I.INPATIENTID) AS INPATIENTS
    FROM INPATIENT I
    JOIN DEPARTMENT D ON I.DEPTCODE = D.DEPTCODE
    WHERE {date_cond_inp} AND {dept_cond}
    GROUP BY D.DEPTNAME, EXTRACT(MONTH FROM I.DOA)
    ORDER BY D.DEPTNAME, MONTH
    """
    inpatient_trend = pd.read_sql(trend_query, conn)

    if not inpatient_trend.empty:
        trend_chart = alt.Chart(inpatient_trend).mark_line(point=True).encode(
            x='MONTH:O',
            y='INPATIENTS:Q',
            color='DEPTNAME:N',
            tooltip=['DEPTNAME', 'MONTH', 'INPATIENTS']
        ).properties(title="Inpatient Trend (Monthly)")
        st.altair_chart(trend_chart, use_container_width=True)
    else:
        st.info("No inpatient trend data for selected filters.")

# --- Admission Type Breakdown ---
with tab5:
    st.subheader("Admission Type Breakdown")

    admission_query = f"""
    SELECT I.ADMISSIONTYPE, COUNT(I.INPATIENTID) AS CNT
    FROM INPATIENT I
    JOIN DEPARTMENT D ON I.DEPTCODE = D.DEPTCODE
    WHERE {date_cond_inp} AND {dept_cond}
    GROUP BY I.ADMISSIONTYPE
    """
    admission_data = pd.read_sql(admission_query, conn)

    if not admission_data.empty:
        pie_chart = alt.Chart(admission_data).mark_arc().encode(
            theta=alt.Theta(field="CNT", type="quantitative"),
            color=alt.Color(field="ADMISSIONTYPE", type="nominal"),
            tooltip=["ADMISSIONTYPE", "CNT"]
        ).properties(title="Admission Type Distribution")
        st.altair_chart(pie_chart, use_container_width=True)
    else:
        st.info("No admission data found.")

# --- Detailed Reports ---
with tab6:
    st.subheader("Inpatient Detailed Report (Top 100)")
    inpatient_report_query = f"""
    SELECT * FROM (
        SELECT I.INPATIENTID, I.MRN, P.PNAME, P.GENDER, P.DOB, I.DOA, I.DOD, I.DIAGNOSIS,
               I.ADMISSIONTYPE, D.DEPTNAME,
               LISTAGG(S.SURGERYID || '-' || S.SURGERYTYPE, ', ') WITHIN GROUP (ORDER BY S.SURGERYDATE) AS SURGERIES
        FROM INPATIENT I
        JOIN PATIENT P ON I.MRN = P.MRN
        JOIN DEPARTMENT D ON I.DEPTCODE = D.DEPTCODE
        LEFT JOIN SURGERY S ON I.INPATIENTID = S.VISITID
        WHERE {date_cond_inp} AND {dept_cond}
        GROUP BY I.INPATIENTID, I.MRN, P.PNAME, P.GENDER, P.DOB, I.DOA, I.DOD, I.DIAGNOSIS, I.ADMISSIONTYPE, D.DEPTNAME
        ORDER BY I.DOA DESC
    ) WHERE ROWNUM <= 100
    """
    inpatient_report = pd.read_sql(inpatient_report_query, conn)
    st.dataframe(inpatient_report, use_container_width=True)

    st.subheader("Reports (Top 100)")
    reports_query = """
    SELECT * FROM (
        SELECT REPORTID, REPORTNAME, STATUS, HOSPITALID, CATEGORY, PATH2REPORT
        FROM REPORT_MASTER
        ORDER BY REPORTID DESC
    ) WHERE ROWNUM <= 100
    """
    reports = pd.read_sql(reports_query, conn)
    st.dataframe(reports, use_container_width=True)
