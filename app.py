
import sqlite3
from datetime import date

import streamlit as st

st.set_page_config(
    page_title="MediCloud Hospital",
    page_icon="🏥",
    layout="wide"
)

DB = "hospital.db"


def connect():
    return sqlite3.connect(DB)


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

st.title("🏥 MediCloud Hospital Management")
st.caption("Cloud-ready digital hospital management dashboard")
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choose a module",
    [
        "Dashboard",
        "Register Patient",
        "Patient Records",
        "Book Appointment",
        "Appointments"
    ]
)

with connect() as con:
    patient_count = con.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    appointment_count = con.execute(
        "SELECT COUNT(*) FROM appointments"
    ).fetchone()[0]

    booked_count = con.execute(
        "SELECT COUNT(*) FROM appointments WHERE status='Booked'"
    ).fetchone()[0]

    patient_rows = con.execute(
        "SELECT * FROM patients ORDER BY id DESC"
    ).fetchall()

    appointment_rows = con.execute(
        "SELECT * FROM appointments ORDER BY appointment_date DESC"
    ).fetchall()

if page == "Dashboard":
    st.subheader("Hospital Overview")

    a, b, c = st.columns(3)
    a.metric("Total Patients", patient_count)
    b.metric("Total Appointments", appointment_count)
    c.metric("Upcoming / Booked", booked_count)

    st.divider()
    st.subheader("Recent Patient Registrations")

    if patient_rows:
        st.dataframe(
            [
                {
                    "ID": p[0],
                    "Name": p[1],
                    "Age": p[2],
                    "Gender": p[3],
                    "Phone": p[4],
                    "Condition": p[5]
                }
                for p in patient_rows[:10]
            ],
            use_container_width=True
        )
    else:
        st.info("No patients registered yet. Add a demo patient!")

elif page == "Register Patient":
    st.subheader("📝 Patient Registration")

    with st.form("patient_form", clear_on_submit=True):
        name = st.text_input("Patient Name")
        age = st.number_input("Age", min_value=0, max_value=120, value=20)
        gender = st.selectbox("Gender", ["Female", "Male", "Other"])
        phone = st.text_input("Phone Number")
        disease = st.text_input("Reason for Visit / Condition")

        submitted = st.form_submit_button("Register Patient")

        if submitted:
            if not name.strip():
                st.error("Please enter the patient's name.")
            else:
                with connect() as con:
                    con.execute(
                        """INSERT INTO patients
                        (name, age, gender, phone, disease)
                        VALUES (?, ?, ?, ?, ?)""",
                        (name.strip(), age, gender, phone.strip(), disease.strip())
                    )
                st.success(f"Patient {name} registered successfully!")
                st.rerun()

elif page == "Patient Records":
    st.subheader("📋 Patient Records")
    search = st.text_input("Search by patient name")

    filtered = [
        p for p in patient_rows
        if search.lower() in p[1].lower()
    ]

    if filtered:
        st.dataframe(
            [
                {
                    "ID": p[0],
                    "Name": p[1],
                    "Age": p[2],
                    "Gender": p[3],
                    "Phone": p[4],
                    "Condition": p[5]
                }
                for p in filtered
            ],
            use_container_width=True
        )
    else:
        st.info("No matching patient records found.")

elif page == "Book Appointment":
    st.subheader("📅 Book an Appointment")

    names = [p[1] for p in patient_rows]

    if not names:
        st.warning("Register a patient before booking an appointment.")
    else:
        with st.form("appointment_form", clear_on_submit=True):
            patient = st.selectbox("Select Patient", names)
            doctor = st.selectbox(
                "Select Doctor",
                [
                    "Dr. Priya - General Medicine",
                    "Dr. Arun - Cardiology",
                    "Dr. Meena - Pediatrics",
                    "Dr. Kumar - Orthopedics"
                ]
            )
            appointment_date = st.date_input(
                "Appointment Date",
                value=date.today(),
                min_value=date.today()
            )

            submitted = st.form_submit_button("Book Appointment")

            if submitted:
                with connect() as con:
                    con.execute(
                        """INSERT INTO appointments
                        (patient, doctor, appointment_date)
                        VALUES (?, ?, ?)""",
                        (patient, doctor, appointment_date.isoformat())
                    )
                st.success("Appointment booked successfully!")
                st.rerun()

elif page == "Appointments":
    st.subheader("🗓️ Appointment Management")

    if appointment_rows:
        for appt in appointment_rows:
            with st.container(border=True):
                st.write(f"**Patient:** {appt[1]}")
                st.write(f"**Doctor:** {appt[2]}")
                st.write(f"**Date:** {appt[3]}")
                st.write(f"**Status:** {appt[4]}")

                if appt[4] == "Booked":
                    if st.button(
                        "Mark Completed",
                        key=f"complete_{appt[0]}"
                    ):
                        with connect() as con:
                            con.execute(
                                "UPDATE appointments SET status='Completed' WHERE id=?",
                                (appt[0],)
                            )
                        st.rerun()
    else:
        st.info("No appointments booked yet.")

st.sidebar.divider()
st.sidebar.success("System Status: Running")
st.sidebar.caption("Academic prototype — use fictional demo data only.")