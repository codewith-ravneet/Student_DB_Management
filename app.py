import sqlite3

import pandas as pd
import streamlit as st

DB_FILE = "students.db"


# ---------- Database helpers ----------
def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_no TEXT NOT NULL UNIQUE,
                email TEXT,
                course TEXT,
                year INTEGER
            )
            """
        )


def add_student(name, roll_no, email, course, year):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO students (name, roll_no, email, course, year) VALUES (?, ?, ?, ?, ?)",
            (name, roll_no, email, course, year),
        )


def get_students():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM students ORDER BY id", conn)


def update_student(student_id, name, roll_no, email, course, year):
    with get_connection() as conn:
        conn.execute(
            "UPDATE students SET name=?, roll_no=?, email=?, course=?, year=? WHERE id=?",
            (name, roll_no, email, course, year, student_id),
        )


def delete_student(student_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM students WHERE id=?", (student_id,))


# ---------- UI ----------
st.set_page_config(page_title="Student Record Management", page_icon="🎓", layout="centered")
init_db()

st.title("🎓 Student Record Management System")

tab_add, tab_view, tab_update, tab_delete = st.tabs(
    ["➕ Add", "📋 View", "✏️ Update", "🗑️ Delete"]
)

COURSES = ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"]

# CREATE
with tab_add:
    st.subheader("Add New Student")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        roll_no = st.text_input("Roll Number")
        email = st.text_input("Email")
        course = st.selectbox("Course", COURSES)
        year = st.number_input("Year", min_value=1, max_value=4, step=1)
        submitted = st.form_submit_button("Add Student")

    if submitted:
        if not name.strip() or not roll_no.strip():
            st.error("Name and Roll Number are required.")
        else:
            try:
                add_student(name.strip(), roll_no.strip(), email.strip(), course, int(year))
                st.success(f"Student '{name}' added successfully!")
            except sqlite3.IntegrityError:
                st.error("A student with this Roll Number already exists.")

# READ
with tab_view:
    st.subheader("All Students")
    df = get_students()
    search = st.text_input("Search by name or roll number")
    if search:
        mask = df["name"].str.contains(search, case=False, na=False) | df[
            "roll_no"
        ].str.contains(search, case=False, na=False)
        df = df[mask]

    if df.empty:
        st.info("No records found.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"Total records: {len(df)}")

# UPDATE
with tab_update:
    st.subheader("Update Student")
    df = get_students()
    if df.empty:
        st.info("No students to update.")
    else:
        options = {f"{row['roll_no']} - {row['name']}": row["id"] for _, row in df.iterrows()}
        choice = st.selectbox("Select student", list(options.keys()), key="update_select")
        student = df[df["id"] == options[choice]].iloc[0]

        with st.form("update_form"):
            new_name = st.text_input("Full Name", value=student["name"])
            new_roll = st.text_input("Roll Number", value=student["roll_no"])
            new_email = st.text_input("Email", value=student["email"] or "")
            course_index = COURSES.index(student["course"]) if student["course"] in COURSES else 0
            new_course = st.selectbox("Course", COURSES, index=course_index)
            new_year = st.number_input(
                "Year", min_value=1, max_value=4, step=1, value=int(student["year"] or 1)
            )
            update_clicked = st.form_submit_button("Update Student")

        if update_clicked:
            if not new_name.strip() or not new_roll.strip():
                st.error("Name and Roll Number are required.")
            else:
                try:
                    update_student(
                        int(student["id"]),
                        new_name.strip(),
                        new_roll.strip(),
                        new_email.strip(),
                        new_course,
                        int(new_year),
                    )
                    st.success("Student updated successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Another student already has this Roll Number.")

# DELETE
with tab_delete:
    st.subheader("Delete Student")
    df = get_students()
    if df.empty:
        st.info("No students to delete.")
    else:
        options = {f"{row['roll_no']} - {row['name']}": row["id"] for _, row in df.iterrows()}
        choice = st.selectbox("Select student", list(options.keys()), key="delete_select")
        confirm = st.checkbox("I confirm I want to delete this record")
        if st.button("Delete Student", type="primary", disabled=not confirm):
            delete_student(int(options[choice]))
            st.success("Student deleted.")
            st.rerun()