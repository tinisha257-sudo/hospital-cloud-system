
import sqlite3
import hashlib
import io
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="MediCloud | Hospital Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB = "hospital.db"

DOCTORS = {
    "Dr. Priya": "General Medicine",
    "Dr. Arun": "Cardiology",
    "Dr. Meena": "Pediatrics",
    "Dr. Kumar": "Orthopedics",
    "Dr. Divya": "Dermatology",
}

# Demo-only credentials. Configure secrets before using
# this application beyond a classroom demonstration.
DEMO_USERS = {
    "admin": {"password": "Admin@123", "role": "Administrator"},
    "reception": {"password": "Reception@123", "role": "Receptionist"},
}


# --------------------------------------------------
# DATABASE
# --------------------------------------------------
def connect():
    con = sqlite3.connect(DB, timeout=10)
    con.execute("PRAGMA busy_timeout = 10000")
    return con


def initialize():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                phone TEXT,
                disease TEXT
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient TEXT NOT NULL,
                doctor TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                status TEXT DEFAULT 'Booked'
            )
        """)


initialize()


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------
def verify_login(username, password):
    # Prefer configured Streamlit secrets when available.
    # Demo defaults are NOT production credentials.
    try:
        users = st.secrets["users"]
        user = users.get(username)
        if user:
            return user.get("password") == password, user.get("role", "Staff")
        return False, None
    except Exception:
        user = DEMO_USERS.get(username)
        if user and user["password"] == password:
            return True, user["role"]
        return False, None


def login_screen():
    st.title("🏥 MediCloud Hospital")
    st.subheader("Secure Staff Sign In")
    st.write("Hospital management, made simpler.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary")

        if submitted:
            valid, role = verify_login(username.strip(), password)
            if valid:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username.strip()
                st.session_state["role"] = role
                st.rerun()
            else:
                st.error("Invalid username or password.")

    st.info(
        "Classroom demo credentials: admin / Admin@123 "
        "or reception / Reception@123. "
        "These defaults are not safe for a real deployment."
    )
    st.caption(
        "Prototype only. Do not enter real patient or medical information."
    )


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_screen()
    st.stop()


# --------------------------------------------------
# DATA HELPERS
# --------------------------------------------------
def load_patients():
    with connect() as con:
        return pd.read_sql_query(
            "SELECT * FROM patients ORDER BY id DESC", con
        )


def load_appointments():
    with connect() as con:
        return pd.read_sql_query(
            "SELECT * FROM appointments ORDER BY appointment_date DESC, id DESC",
            con,
        )


def add_patient(name, age, gender, phone, disease):
    with connect() as con:
        con.execute(
            """INSERT INTO patients
            (name, age, gender, phone, disease)
            VALUES (?, ?, ?, ?, ?)""",
            (name, age, gender, phone, disease),
        )


def book_appointment(patient, doctor, appointment_date):
    day = appointment_date.isoformat()

    with connect() as con:
        conflict = con.execute(
            """SELECT COUNT(*) FROM appointments
            WHERE doctor = ? AND appointment_date = ?
            AND status = 'Booked'""",
            (doctor, day),
        ).fetchone()[0]

        if conflict:
            return False

        con.execute(
            """INSERT INTO appointments
            (patient, doctor, appointment_date, status)
            VALUES (?, ?, ?, 'Booked')""",
            (patient, doctor, day),
        )
        return True


def update_appointment_status(appointment_id, status):
    with connect() as con:
        con.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (status, appointment_id),
        )


def delete_patient(patient_id):
    with connect() as con:
        con.execute("DELETE FROM patients WHERE id = ?", (patient_id,))


# --------------------------------------------------
# GLOBAL STYLING
# --------------------------------------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }
    [data-testid="stMetric"] {
        background: rgba(100, 149, 237, 0.08);
        border: 1px solid rgba(100, 149, 237, 0.22);
        padding: 16px;
        border-radius: 14px;
    }
    div.stButton > button {
        border-radius: 9px;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
patients = load_patients()
appointments = load_appointments()

today = date.today()
today_string = today.isoformat()

if not appointments.empty:
    appointments["appointment_date"] = pd.to_datetime(
        appointments["appointment_date"], errors="coerce"
    ).dt.date

    booked = appointments[appointments["status"] == "Booked"]
    upcoming = booked[booked["appointment_date"] >= today]
    todays_appointments = booked[
        booked["appointment_date"] == today
    ]
    completed = appointments[appointments["status"] == "Completed"]
    cancelled = appointments[appointments["status"] == "Cancelled"]
else:
    booked = appointments.copy()
    upcoming = appointments.copy()
    todays_appointments = appointments.copy()
    completed = appointments.copy()
    cancelled = appointments.copy()


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------
with st.sidebar:
    st.title("🏥 MediCloud")
    st.caption("Hospital Management System")
    st.divider()

    st.write(f"**Staff:** {st.session_state['username']}")
    st.write(f"**Role:** {st.session_state['role']}")

    page = st.radio(
        "MAIN MENU",
        [
            "Dashboard",
            "Register Patient",
            "Patient Records",
            "Doctor Directory",
            "Book Appointment",
            "Appointment Management",
            "Reports & Analytics",
        ],
    )

    st.divider()
    st.caption("System status")
    st.success("Application running")

    if st.button("Sign Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state.pop("username", None)
        st.session_state.pop("role", None)
        st.rerun()


# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🏥 MediCloud Hospital Management")
st.caption(
    f"Digital hospital operations • {today.strftime('%d %B %Y')}"
)


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
if page == "Dashboard":
    st.subheader("Hospital Overview")
    st.write("Monitor patient registrations and appointment activity.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Patients", len(patients))
    c2.metric("Total Appointments", len(appointments))
    c3.metric("Today's Appointments", len(todays_appointments))
    c4.metric("Upcoming Bookings", len(upcoming))

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("Appointment Status")
        if not appointments.empty:
            status_counts = (
                appointments["status"]
                .value_counts()
                .rename_axis("Status")
                .reset_index(name="Appointments")
            )
            st.bar_chart(status_counts, x="Status", y="Appointments")
        else:
            st.info("Appointment charts will appear after bookings are added.")

    with right:
        st.subheader("Patients by Condition")
        if not patients.empty:
            condition_data = patients.copy()
            condition_data["disease"] = (
                condition_data["disease"].fillna("").replace("", "Not specified")
            )
            condition_counts = (
                condition_data["disease"]
                .value_counts()
                .rename_axis("Condition")
                .reset_index(name="Patients")
            )
            st.bar_chart(condition_counts, x="Condition", y="Patients")
        else:
            st.info("Register demo patients to view this chart.")

    st.divider()
    st.subheader("Recent Patient Registrations")

    if not patients.empty:
        st.dataframe(patients.head(10), use_container_width=True, hide_index=True)
    else:
        st.info("No patients registered yet.")

    st.subheader("Upcoming Appointments")
    if not upcoming.empty:
        display = upcoming.copy()
        display["appointment_date"] = display["appointment_date"].astype(str)
        st.dataframe(display, use_container_width=True, hide_index=True)
    else:
        st.info("No upcoming appointments.")


# --------------------------------------------------
# REGISTER PATIENT
# --------------------------------------------------
elif page == "Register Patient":
    st.subheader("📝 Patient Registration")
    st.write("Create a new patient record.")

    with st.form("patient_registration", clear_on_submit=True):
        name = st.text_input("Patient Name *")
        age = st.number_input("Age", min_value=0, max_value=120, value=20)
        gender = st.selectbox("Gender", ["Female", "Male", "Other"])
        phone = st.text_input("Phone Number")
        disease = st.text_input("Reason for Visit / Condition")

        submitted = st.form_submit_button(
            "Register Patient", type="primary"
        )

        if submitted:
            if not name.strip():
                st.error("Patient name is required.")
            elif phone and not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
                st.error("Enter a valid phone number.")
            else:
                add_patient(
                    name.strip(),
                    int(age),
                    gender,
                    phone.strip(),
                    disease.strip(),
                )
                st.success(f"Patient {name.strip()} registered successfully!")
                st.rerun()


# --------------------------------------------------
# PATIENT RECORDS
# --------------------------------------------------
elif page == "Patient Records":
    st.subheader("📋 Patient Records")

    if patients.empty:
        st.info("No patient records yet. Register a patient first.")
    else:
        search = st.text_input("Search by name, phone, or condition")
        view = patients.copy()

        if search.strip():
            term = search.strip().lower()
            mask = (
                view["name"].fillna("").str.lower().str.contains(term, regex=False)
                | view["phone"].fillna("").str.lower().str.contains(term, regex=False)
                | view["disease"].fillna("").str.lower().str.contains(term, regex=False)
            )
            view = view[mask]

        st.write(f"**Matching records:** {len(view)}")
        st.dataframe(view, use_container_width=True, hide_index=True)

        with st.expander("Delete a demo patient record"):
            st.warning("Deletion is permanent for this database.")
            patient_options = {
                f"{row['id']} — {row['name']}": int(row["id"])
                for _, row in patients.iterrows()
            }
            selected = st.selectbox(
                "Choose patient", list(patient_options.keys())
            )

            if st.button("Delete Selected Patient", type="secondary"):
                patient_id = patient_options[selected]
                delete_patient(patient_id)
                st.success("Patient record deleted.")
                st.rerun()


# --------------------------------------------------
# DOCTOR DIRECTORY
# --------------------------------------------------
elif page == "Doctor Directory":
    st.subheader("👩‍⚕️ Doctor Directory")
    st.write("Available doctors and their departments.")

    doctor_rows = [
        {
            "Doctor": name,
            "Department": department,
            "Availability": "Appointment-based",
        }
        for name, department in DOCTORS.items()
    ]

    st.dataframe(
        pd.DataFrame(doctor_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "This directory uses sample doctor details. "
        "Confirm real availability before using an appointment system clinically."
    )


# --------------------------------------------------
# BOOK APPOINTMENT
# --------------------------------------------------
elif page == "Book Appointment":
    st.subheader("📅 Book an Appointment")

    if patients.empty:
        st.warning("Register a patient before booking an appointment.")
    else:
        patient_options = {
            f"{row['id']} — {row['name']}": row["name"]
            for _, row in patients.iterrows()
        }

        with st.form("booking_form", clear_on_submit=True):
            patient_label = st.selectbox(
                "Select Patient", list(patient_options.keys())
            )
            doctor = st.selectbox(
                "Select Doctor",
                list(DOCTORS.keys()),
                format_func=lambda name: f"{name} — {DOCTORS[name]}",
            )
            appointment_day = st.date_input(
                "Appointment Date",
                value=today,
                min_value=today,
                max_value=today + timedelta(days=365),
            )

            submitted = st.form_submit_button(
                "Book Appointment", type="primary"
            )

            if submitted:
                success = book_appointment(
                    patient_options[patient_label],
                    doctor,
                    appointment_day,
                )
                if success:
                    st.success("Appointment booked successfully!")
                    st.rerun()
                else:
                    st.error(
                        "This doctor already has a booked appointment "
                        "on that date. Choose another doctor or date."
                    )


# --------------------------------------------------
# APPOINTMENT MANAGEMENT
# --------------------------------------------------
elif page == "Appointment Management":
    st.subheader("🗓️ Appointment Management")

    if appointments.empty:
        st.info("No appointments have been booked yet.")
    else:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Booked", "Completed", "Cancelled"],
        )

        view = appointments.copy()
        if status_filter != "All":
            view = view[view["status"] == status_filter]

        view["appointment_date"] = view["appointment_date"].astype(str)
        st.dataframe(view, use_container_width=True, hide_index=True)

        active = appointments[
            appointments["status"] == "Booked"
        ]

        if not active.empty:
            st.divider()
            st.subheader("Update Appointment")

            options = {
                f"#{int(row['id'])} | {row['patient']} | "
                f"{row['doctor']} | {row['appointment_date']}": int(row["id"])
                for _, row in active.iterrows()
            }

            with st.form("update_appointment"):
                selected_label = st.selectbox(
                    "Select booked appointment", list(options.keys())
                )
                new_status = st.radio(
                    "New status",
                    ["Completed", "Cancelled"],
                    horizontal=True,
                )
                update = st.form_submit_button("Update Status")

                if update:
                    update_appointment_status(
                        options[selected_label], new_status
                    )
                    st.success(f"Appointment marked {new_status.lower()}.")
                    st.rerun()


# --------------------------------------------------
# REPORTS AND ANALYTICS
# --------------------------------------------------
elif page == "Reports & Analytics":
    st.subheader("📈 Reports & Analytics")
    st.write("Review hospital activity and export demo reports.")

    r1, r2, r3 = st.columns(3)
    r1.metric("Patients", len(patients))
    r2.metric("Completed Appointments", len(completed))
    r3.metric("Cancelled Appointments", len(cancelled))

    st.divider()
    st.subheader("Appointments by Doctor")

    if not appointments.empty:
        doctor_counts = (
            appointments.groupby("doctor")
            .size()
            .reset_index(name="Total Appointments")
            .sort_values("Total Appointments", ascending=False)
        )
        st.bar_chart(
            doctor_counts,
            x="doctor",
            y="Total Appointments",
        )
    else:
        st.info("Book appointments to generate analytics.")

    st.subheader("Appointment History")

    if not appointments.empty:
        daily = appointments.copy()
        daily["appointment_date"] = pd.to_datetime(
            daily["appointment_date"], errors="coerce"
        )
        daily = daily.dropna(subset=["appointment_date"])
        daily["Date"] = daily["appointment_date"].dt.strftime("%Y-%m-%d")

        daily_counts = (
            daily.groupby("Date")
            .size()
            .reset_index(name="Appointments")
            .sort_values("Date")
        )

        if not daily_counts.empty:
            st.line_chart(daily_counts, x="Date", y="Appointments")

    st.divider()
    st.subheader("Export Reports")

    if not patients.empty:
        patient_csv = patients.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Patient Report (CSV)",
            data=patient_csv,
            file_name="hospital_patient_report.csv",
            mime="text/csv",
        )

    if not appointments.empty:
        export_appointments = appointments.copy()
        export_appointments["appointment_date"] = (
            export_appointments["appointment_date"].astype(str)
        )
        appointment_csv = export_appointments.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Appointment Report (CSV)",
            data=appointment_csv,
            file_name="hospital_appointment_report.csv",
            mime="text/csv",
        )

    if patients.empty and appointments.empty:
        st.info("Reports will be available after adding demo data.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.caption(
    "MediCloud Hospital Management • Academic prototype • "
    "Use fictional data only • Not for clinical decision-making"
)
