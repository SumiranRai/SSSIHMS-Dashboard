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
# HIDE SIDEBAR NAVIGATION + ADD STYLING
# =====================================================
st.markdown("""
    <style>
    /* Hide Streamlit page navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Modern styling for buttons */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar navigation buttons styling */
    .nav-buttons {
        display: flex;
        gap: 8px;
        margin-bottom: 20px;
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
# SIDEBAR NAVIGATION BUTTONS
# =====================================================
st.sidebar.title("🎛️ Navigation")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard"):
        st.switch_page("pages/dashboard.py")
    if st.button("🔑 Password", use_container_width=True, key="nav_password"):
        st.switch_page("pages/change_password.py")

with col2:
    if st.button("🔒 Logout", use_container_width=True, key="nav_logout"):
        st.switch_page("app.py")
    # Admin panel is current page, show as disabled or highlighted
    st.button("⚙️ Admin", use_container_width=True, disabled=True, key="nav_admin_current")

st.sidebar.markdown("---")
st.sidebar.info(f"👤 **{st.session_state.get('staffname', 'Admin')}**\n🏥 {st.session_state.get('hospitalid', 'N/A')}")

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
        st.success(f"✅ LOGINOK for {staffid} updated to '{value}'.")
    except Exception as e:
        st.error(f"❌ Failed to update LOGINOK: {e}")

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
        st.success(f"✅ ACCESS_ROLE for {staffid} updated to '{role}'.")
    except Exception as e:
        st.error(f"❌ Failed to update ACCESS_ROLE: {e}")

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
        st.success(f"✅ Password for {staffid} has been reset.")
    except Exception as e:
        st.error(f"❌ Failed to reset password: {e}")

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
        st.success(f"✅ Staff '{staffid}' added successfully (Role = {access_role}).")

    except oracledb.IntegrityError as ie:
        st.error(f"❌ Integrity error (maybe STAFFID exists): {ie}")
    except Exception as e:
        st.error(f"❌ Failed to add staff: {e}")

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
        st.success(f"✅ Staff '{staffid}' deleted.")
    except Exception as e:
        st.error(f"❌ Failed to delete staff: {e}")

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

if not df.empty:
    # Add color coding for roles
    def highlight_role(row):
        if row['ACCESS_ROLE'] == 'A':
            return ['background-color: #ffe6e6'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        df.style.apply(highlight_role, axis=1),
        use_container_width=True,
        height=400
    )
    
    st.caption("💡 Admin users (ACCESS_ROLE='A') are highlighted in red")
else:
    st.info("No staff records found.")

st.markdown("---")

# ===============================
# STAFF ACTIONS
# ===============================
st.subheader("👨‍⚕️ Staff Actions")

staff_list = df["STAFFID"].tolist() if not df.empty else []
selected = st.selectbox("Select STAFFID", [""] + staff_list, key="staff_select")

if selected:
    # Show selected staff info
    staff_info = df[df["STAFFID"] == selected].iloc[0]
    st.info(f"""
    **Name:** {staff_info['STAFFNAME']}  
    **Department:** {staff_info['DEPTNAME']}  
    **Role:** {'🛡️ Admin' if staff_info['ACCESS_ROLE'] == 'A' else '👤 Staff'}  
    **Status:** {'✅ Active' if staff_info['LOGINOK'] == 'Y' else '🔴 Inactive'}
    """)

col1, col2, col3 = st.columns(3)

# --- LOGINOK updates
with col1:
    if st.button("✅ Activate (LOGINOK='Y')", use_container_width=True) and selected:
        update_loginok(selected, "Y")
        st.rerun()

with col2:
    if st.button("🔴 Deactivate (LOGINOK='N')", use_container_width=True) and selected:
        update_loginok(selected, "N")
        st.rerun()

# --- Reset password
with col3:
    with st.expander("🔑 Reset Password"):
        new_pw = st.text_input("Enter new password", type="password", key="reset_pw")
        if st.button("Reset Password", use_container_width=True) and selected:
            if not new_pw:
                st.error("Please enter a password before resetting.")
            else:
                reset_password(selected, new_pw)
                st.rerun()

# --- Update Access Role
st.markdown("---")
st.subheader("🔐 Update User Access Role")
role_col1, role_col2 = st.columns([3, 1])
with role_col1:
    role_choice = st.selectbox("Set ACCESS_ROLE", ["A", "U"], 
                               format_func=lambda x: "🛡️ Admin (A)" if x == "A" else "👤 Staff (U)",
                               key="role_set")
with role_col2:
    if st.button("Update Role", use_container_width=True, type="primary") and selected:
        update_access_role(selected, role_choice)
        st.rerun()

st.markdown("---")

# ===============================
# ADD NEW STAFF
# ===============================
st.subheader("➕ Add New Staff")

with st.expander("➕ Add New Staff Member", expanded=False):
    with st.form("add_staff_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        staffid = c1.text_input("STAFFID (unique)*", placeholder="e.g., DOC001")
        staffname = c2.text_input("STAFFNAME*", placeholder="Dr. John Doe")

        c3, c4 = st.columns(2)
        deptname = c3.text_input("DEPTNAME", placeholder="Cardiology")
        designation = c4.text_input("DESIGNATION", placeholder="Senior Physician")
        
        c5, c6 = st.columns(2)
        hospitalid = c5.text_input("HOSPITALID", placeholder="HOSP001")
        deptcode = c6.text_input("DEPTCODE", placeholder="CARD")
        
        athmaid = st.text_input("ATHMAID", placeholder="ATH001")

        passwd = st.text_input("Initial Password*", type="password", placeholder="Enter strong password")
        
        c7, c8 = st.columns(2)
        loginok_opt = c7.selectbox("LOGINOK (activate now?)", ["N", "Y"], index=0,
                                   format_func=lambda x: "✅ Yes - Activate" if x == "Y" else "🔴 No - Keep Inactive")
        access_role = c8.selectbox("ACCESS_ROLE", ["U", "A"], index=0,
                                   format_func=lambda x: "🛡️ Admin" if x == "A" else "👤 Staff")

        submitted = st.form_submit_button("➕ Add Staff Member", use_container_width=True, type="primary")

        if submitted:
            if not staffid or not staffname or not passwd:
                st.error("❌ STAFFID, STAFFNAME, and Initial Password are required.")
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
                st.rerun()

st.markdown("---")

# ===============================
# DELETE STAFF
# ===============================
st.subheader("🗑️ Delete Staff")

with st.expander("⚠️ Delete Staff Member", expanded=False):
    del_staff = st.selectbox("Select staff to delete", [""] + staff_list, key="del_select")
    
    if del_staff:
        staff_to_delete = df[df["STAFFID"] == del_staff].iloc[0]
        st.warning(f"""
        ⚠️ **You are about to delete:**  
        **ID:** {staff_to_delete['STAFFID']}  
        **Name:** {staff_to_delete['STAFFNAME']}  
        **Role:** {staff_to_delete['ACCESS_ROLE']}
        """)
    
    confirm = st.checkbox("⚠️ I understand this will permanently delete the staff record.", key="del_confirm")

    if st.button("🗑️ Delete Staff", use_container_width=True, type="primary"):
        if not del_staff:
            st.error("❌ Select a staff ID first.")
        elif not confirm:
            st.error("❌ Please confirm deletion by checking the box above.")
        else:
            delete_staff(del_staff)
            st.rerun()

st.markdown("---")
st.caption("🛡️ Admins (A) have full access | 👤 Staff (U) have limited access")
st.caption("Roles are controlled by ACCESS_ROLE in STAFFMASTER table")