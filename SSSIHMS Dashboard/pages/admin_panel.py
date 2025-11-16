import streamlit as st
import oracledb
import hashlib
import pandas as pd

# =====================================================
# STREAMLIT CONFIG
# =====================================================
st.set_page_config(
    page_title="🛠 Admin Panel - User Management",
    page_icon="🛠",
    layout="wide"
)

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
    return hashlib.sha256(password.encode("utf-8")).hexdigest().lower()

# =====================================================
# AUTH CHECK (RESTRICT TO ADMIN ONLY)
# =====================================================

# -- Session login check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔒 Please log in first.")
    st.stop()

# -- Strong DB role verification
def fetch_role(staffid: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ACCESS_ROLE 
            FROM STAFFMASTER 
            WHERE STAFFID = :id
        """, {"id": staffid})
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else None
    except:
        return None

db_role = fetch_role(st.session_state.username)

if db_role != "A":   # Role must be admin
    st.error("🚫 Access denied. Only administrators can access this page.")
    st.stop()

# =====================================================
# DB OPERATIONS
# =====================================================
def fetch_all_staff():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT STAFFID, STAFFNAME, DEPTNAME, DESIGNATION, 
                   HOSPITALID, DEPTCODE, ATHMAID, LOGINOK, ACCESS_ROLE
            FROM STAFFMASTER
            ORDER BY STAFFID
        """)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        cur.close()
        conn.close()
        return pd.DataFrame(rows, columns=cols)

    except Exception as e:
        st.error(f"Database error while fetching staff: {e}")
        return pd.DataFrame(columns=[
            "STAFFID","STAFFNAME","DEPTNAME","DESIGNATION",
            "HOSPITALID","DEPTCODE","ATHMAID","LOGINOK","ACCESS_ROLE"
        ])

def update_loginok(staffid: str, value: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE STAFFMASTER 
            SET LOGINOK = :val 
            WHERE STAFFID = :sid
        """, {"val": value, "sid": staffid})
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"LOGINOK for {staffid} updated to '{value}'.")
    except Exception as e:
        st.error(f"Failed to update LOGINOK: {e}")

def update_access_role(staffid: str, role: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE STAFFMASTER 
            SET ACCESS_ROLE = :role 
            WHERE STAFFID = :sid
        """, {"role": role, "sid": staffid})
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"ACCESS_ROLE for {staffid} updated to '{role}'.")
    except Exception as e:
        st.error(f"Failed to update ACCESS_ROLE: {e}")

def reset_password(staffid: str, new_password: str):
    try:
        enc = hash_password(new_password)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE STAFFMASTER 
            SET TXTPASSWD = :pwd 
            WHERE STAFFID = :sid
        """, {"pwd": enc, "sid": staffid})
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"Password for {staffid} has been reset.")
    except Exception as e:
        st.error(f"Failed to reset password: {e}")

def add_staff(staffid, staffname, deptname, designation,
              hospitalid, deptcode, athmaid, passwd,
              loginok="N", access_role="U"):
    try:
        enc = hash_password(passwd)
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO STAFFMASTER
            (STAFFID, STAFFNAME, DEPTNAME, DESIGNATION, HOSPITALID,
             DEPTCODE, ATHMAID, TXTPASSWD, LOGINOK, ACCESS_ROLE)
            VALUES (
             :sid, :sname, :dname, :desig, :hid,
             :dcode, :ath, :pwd, :loginok, :acc_role
            )
        """, {
            "sid": staffid,
            "sname": staffname,
            "dname": deptname,
            "desig": designation,
            "hid": hospitalid,
            "dcode": deptcode,
            "ath": athmaid,
            "pwd": enc,
            "loginok": loginok,
            "acc_role": access_role
        })

        conn.commit()
        cur.close()
        conn.close()
        st.success(f"Staff '{staffid}' added successfully (Role = {access_role}).")

    except oracledb.IntegrityError as ie:
        st.error(f"Integrity error (maybe STAFFID exists): {ie}")
    except Exception as e:
        st.error(f"Failed to add staff: {e}")

def delete_staff(staffid: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM STAFFMASTER 
            WHERE STAFFID = :sid
        """, {"sid": staffid})
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"Staff '{staffid}' deleted.")
    except Exception as e:
        st.error(f"Failed to delete staff: {e}")

# =====================================================
# UI — ADMIN PANEL
# =====================================================
st.title("🛠 Admin Panel — STAFFMASTER Management")
st.markdown("Manage hospital staff, roles, and login permissions.")

# ===============================
# SHOW ALL STAFF
# ===============================
st.subheader("📋 Current Staff Records")
df = fetch_all_staff()
st.dataframe(df, use_container_width=True)

st.markdown("---")

# ===============================
# STAFF ACTIONS
# ===============================
st.subheader("👨‍⚕️ Staff Actions")

staff_list = df["STAFFID"].tolist() if not df.empty else []
selected = st.selectbox("Select STAFFID", [""] + staff_list)

col1, col2, col3 = st.columns(3)

# --- LOGINOK updates
with col1:
    if st.button("Activate (LOGINOK='Y')") and selected:
        update_loginok(selected, "Y")

with col2:
    if st.button("Deactivate (LOGINOK='N')") and selected:
        update_loginok(selected, "N")

# --- Reset password
with col3:
    new_pw = st.text_input("Enter new password", key="reset_pw")
    if st.button("Reset Password") and selected:
        if not new_pw:
            st.error("Please enter a password before resetting.")
        else:
            reset_password(selected, new_pw)

# --- Update Access Role
st.subheader("🔐 Update User Access Role (Admin / Staff)")
role_choice = st.selectbox("Set ACCESS_ROLE", ["A", "U"], key="role_set")
if st.button("Update Role") and selected:
    update_access_role(selected, role_choice)

st.markdown("---")

# ===============================
# ADD NEW STAFF
# ===============================
st.subheader("➕ Add New Staff")

with st.form("add_staff_form", clear_on_submit=False):
    c1, c2 = st.columns(2)
    staffid = c1.text_input("STAFFID (unique)")
    staffname = c2.text_input("STAFFNAME")

    deptname = st.text_input("DEPTNAME")
    designation = st.text_input("DESIGNATION")
    hospitalid = st.text_input("HOSPITALID")
    deptcode = st.text_input("DEPTCODE")
    athmaid = st.text_input("ATHMAID")

    passwd = st.text_input("Initial Password", type="password")
    loginok_opt = st.selectbox("LOGINOK (activate now?)", ["N", "Y"], index=0)
    access_role = st.selectbox("ACCESS_ROLE (Admin or Staff)", ["U", "A"], index=0)

    submitted = st.form_submit_button("Add Staff")

    if submitted:
        if not staffid or not staffname or not passwd:
            st.error("STAFFID, STAFFNAME, and Initial Password are required.")
        else:
            add_staff(
                staffid.strip(),
                staffname.strip(),
                deptname.strip() or None,
                designation.strip() or None,
                hospitalid.strip() or None,
                deptcode.strip() or None,
                athmaid.strip() or None,
                passwd,
                loginok_opt,
                access_role
            )

st.markdown("---")

# ===============================
# DELETE STAFF
# ===============================
st.subheader("🗑 Delete Staff")

del_staff = st.selectbox("Select staff to delete", [""] + staff_list, key="del_select")
confirm = st.checkbox("I understand this will permanently delete the staff record.", key="del_confirm")

if st.button("Delete Staff"):
    if not del_staff:
        st.error("Select a staff ID first.")
    elif not confirm:
        st.error("Please confirm deletion.")
    else:
        delete_staff(del_staff)

st.markdown("---")
st.caption("Admins and staff roles are controlled by ACCESS_ROLE in STAFFMASTER.")
