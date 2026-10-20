"""
AI-Powered Student Study Planner and Performance Analyzer
College Mini-Project - Full-Stack Flask Web Application
"""

import os
import sqlite3
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g

app = Flask(__name__)
app.secret_key = "student_study_planner_super_secret_key"
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


# ---------------------------------------------------------
# Database Helpers
# ---------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create database tables if they do not exist."""
    db = get_db()
    cursor = db.cursor()

    # 1. Students table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            college TEXT NOT NULL,
            course TEXT NOT NULL,
            year_semester TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            difficulty TEXT NOT NULL, -- Easy, Medium, Hard
            prep_percentage REAL NOT NULL DEFAULT 0,
            study_hours_per_week REAL NOT NULL DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    # 3. Study Tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER,
            subject_name TEXT NOT NULL,
            topic TEXT NOT NULL,
            task_date TEXT NOT NULL,
            duration_hours REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending' or 'Completed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    # 4. Performance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER,
            subject_name TEXT NOT NULL,
            test_name TEXT NOT NULL,
            max_marks REAL NOT NULL,
            marks_obtained REAL NOT NULL,
            test_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        )
    """)

    db.commit()


def get_current_student():
    """Retrieve the primary student profile or create a default one."""
    db = get_db()
    student = db.execute("SELECT * FROM students ORDER BY id ASC LIMIT 1").fetchone()
    if not student:
        db.execute("""
            INSERT INTO students (name, college, course, year_semester, email)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "Aarav Sharma",
            "Apex Institute of Engineering & Technology",
            "B.Tech in Computer Science",
            "3rd Year / 6th Semester",
            "aarav.sharma@example.edu"
        ))
        db.commit()
        student = db.execute("SELECT * FROM students ORDER BY id ASC LIMIT 1").fetchone()
    return student


def seed_demo_data(force=False):
    """Seed realistic data for college faculty demonstration."""
    db = get_db()
    student = get_current_student()
    student_id = student["id"]

    subject_count = db.execute("SELECT COUNT(*) FROM subjects WHERE student_id = ?", (student_id,)).fetchone()[0]
    if subject_count > 0 and not force:
        return

    # Clear existing data for fresh demo if force=True
    if force:
        db.execute("DELETE FROM study_tasks WHERE student_id = ?", (student_id,))
        db.execute("DELETE FROM performance WHERE student_id = ?", (student_id,))
        db.execute("DELETE FROM subjects WHERE student_id = ?", (student_id,))
        db.commit()

    today = date.today()

    # Demo Subjects with relative dates so exams are always in the future
    sample_subjects = [
        ("Data Structures & Algorithms", (today + timedelta(days=7)).isoformat(), "Hard", 45.0, 10.0),
        ("Computer Networks", (today + timedelta(days=4)).isoformat(), "Hard", 35.0, 9.0),
        ("Database Management Systems", (today + timedelta(days=12)).isoformat(), "Medium", 70.0, 7.0),
        ("Operating Systems", (today + timedelta(days=16)).isoformat(), "Medium", 60.0, 6.0),
        ("Software Engineering", (today + timedelta(days=22)).isoformat(), "Easy", 85.0, 4.0),
    ]

    subject_ids = {}
    for name, exam_dt, diff, prep, hrs in sample_subjects:
        cur = db.execute("""
            INSERT INTO subjects (student_id, name, exam_date, difficulty, prep_percentage, study_hours_per_week)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, name, exam_dt, diff, prep, hrs))
        subject_ids[name] = cur.lastrowid

    # Demo Performance / Test Marks
    sample_scores = [
        (subject_ids.get("Data Structures & Algorithms"), "Data Structures & Algorithms", "Midterm Exam 1", 50, 34, (today - timedelta(days=14)).isoformat()),
        (subject_ids.get("Data Structures & Algorithms"), "Data Structures & Algorithms", "Quiz 1 - Trees & Graphs", 20, 15, (today - timedelta(days=5)).isoformat()),
        (subject_ids.get("Computer Networks"), "Computer Networks", "Unit Test 1 (OSI & TCP/IP)", 40, 18, (today - timedelta(days=10)).isoformat()),
        (subject_ids.get("Database Management Systems"), "Database Management Systems", "Midterm Exam", 50, 42, (today - timedelta(days=12)).isoformat()),
        (subject_ids.get("Database Management Systems"), "Database Management Systems", "SQL Lab Assessment", 30, 27, (today - timedelta(days=3)).isoformat()),
        (subject_ids.get("Operating Systems"), "Operating Systems", "Assignment 1 (Process Scheduling)", 25, 20, (today - timedelta(days=8)).isoformat()),
        (subject_ids.get("Software Engineering"), "Software Engineering", "Class Test - Agile & Scrum", 30, 27, (today - timedelta(days=6)).isoformat()),
    ]

    for sid, sname, tname, max_m, obt_m, tdate in sample_scores:
        db.execute("""
            INSERT INTO performance (student_id, subject_id, subject_name, test_name, max_marks, marks_obtained, test_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, sid, sname, tname, max_m, obt_m, tdate))

    # Demo Daily Tasks (Past couple days completed, Today mixed, Next days pending)
    sample_tasks = [
        (subject_ids.get("Computer Networks"), "Computer Networks", "Transport Layer (TCP vs UDP 3-Way Handshake)", (today - timedelta(days=1)).isoformat(), 2.0, "Completed"),
        (subject_ids.get("Data Structures & Algorithms"), "Data Structures & Algorithms", "Binary Search Trees & Balancing (AVL)", (today - timedelta(days=1)).isoformat(), 1.5, "Completed"),
        (subject_ids.get("Computer Networks"), "Computer Networks", "Subnetting & CIDR Practice Problems", today.isoformat(), 2.0, "Completed"),
        (subject_ids.get("Data Structures & Algorithms"), "Data Structures & Algorithms", "Graph BFS / DFS & Dijkstra Algorithm", today.isoformat(), 2.0, "Pending"),
        (subject_ids.get("Database Management Systems"), "Database Management Systems", "Normalization (1NF, 2NF, 3NF, BCNF) Rules", today.isoformat(), 1.0, "Pending"),
        (subject_ids.get("Operating Systems"), "Operating Systems", "Deadlock Avoidance & Banker's Algorithm", (today + timedelta(days=1)).isoformat(), 2.0, "Pending"),
        (subject_ids.get("Computer Networks"), "Computer Networks", "Application Protocols (DNS, HTTP, SMTP) Review", (today + timedelta(days=1)).isoformat(), 1.5, "Pending"),
        (subject_ids.get("Software Engineering"), "Software Engineering", "UML Sequence & Class Diagrams Revision", (today + timedelta(days=2)).isoformat(), 1.0, "Pending"),
    ]

    for sid, sname, topic, tdate, duration, status in sample_tasks:
        db.execute("""
            INSERT INTO study_tasks (student_id, subject_id, subject_name, topic, task_date, duration_hours, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, sid, sname, topic, tdate, duration, status))

    db.commit()


# ---------------------------------------------------------
# Study Plan Generation Algorithm
# ---------------------------------------------------------
def calculate_study_plan_weights(student_id):
    """
    Core AI Study-Plan Priority Algorithm:
    Evaluates:
      1. Days remaining until exam (closer exams receive higher urgency)
      2. Difficulty rating (Hard = 1.7x, Medium = 1.25x, Easy = 1.0x)
      3. Preparation deficit (Lower current prep % requires more dedicated hours)
      4. Weekly study hour preferences

    Returns ranked list of subjects with priority scores, recommended weekly hours,
    and daily study allocations.
    """
    db = get_db()
    subjects = db.execute("SELECT * FROM subjects WHERE student_id = ? ORDER BY exam_date ASC", (student_id,)).fetchall()
    if not subjects:
        return []

    today = date.today()
    scored_subjects = []
    total_raw_weight = 0.0
    total_user_weekly_hours = 0.0

    for sub in subjects:
        # 1. Days until exam
        try:
            exam_dt = datetime.strptime(sub["exam_date"], "%Y-%m-%d").date()
            days_left = (exam_dt - today).days
        except Exception:
            days_left = 14

        # Urgency factor (inversely related to days remaining)
        if days_left <= 0:
            urgency = 3.5  # Exam is today or overdue
            urgency_label = "Immediate / Today"
        elif days_left <= 3:
            urgency = 3.0
            urgency_label = "Extremely Urgent"
        elif days_left <= 7:
            urgency = 2.2
            urgency_label = "Urgent (< 1 Week)"
        elif days_left <= 14:
            urgency = 1.6
            urgency_label = "Moderate (1-2 Weeks)"
        elif days_left <= 30:
            urgency = 1.2
            urgency_label = "Upcoming (< 1 Month)"
        else:
            urgency = 0.85
            urgency_label = "Adequate Time"

        # 2. Difficulty weight
        diff = sub["difficulty"].lower()
        if diff == "hard":
            diff_weight = 1.75
        elif diff == "medium":
            diff_weight = 1.25
        else:
            diff_weight = 1.0

        # 3. Preparation deficit weight: (100 - prep%) / 100 + 0.2 baseline
        prep_pct = max(0.0, min(100.0, float(sub["prep_percentage"])))
        prep_deficit = ((100.0 - prep_pct) / 100.0) + 0.25

        # Raw composite weight
        raw_weight = diff_weight * prep_deficit * urgency
        total_raw_weight += raw_weight

        user_hours = float(sub["study_hours_per_week"]) if sub["study_hours_per_week"] else 6.0
        total_user_weekly_hours += user_hours

        scored_subjects.append({
            "id": sub["id"],
            "name": sub["name"],
            "exam_date": sub["exam_date"],
            "difficulty": sub["difficulty"],
            "prep_percentage": prep_pct,
            "days_left": days_left,
            "urgency_label": urgency_label,
            "diff_weight": diff_weight,
            "prep_deficit": round(prep_deficit, 2),
            "urgency": round(urgency, 2),
            "raw_weight": raw_weight,
            "user_hours": user_hours
        })

    # Normalize weights and assign weekly hours
    total_target_hours = max(14.0, total_user_weekly_hours)
    for item in scored_subjects:
        normalized_share = (item["raw_weight"] / total_raw_weight) if total_raw_weight > 0 else (1.0 / len(scored_subjects))
        item["share_pct"] = round(normalized_share * 100, 1)
        recommended_hours = round(normalized_share * total_target_hours, 1)
        # Ensure at least 1 hour per subject per week
        item["recommended_weekly_hours"] = max(1.0, recommended_hours)
        item["recommended_daily_hours"] = round(item["recommended_weekly_hours"] / 7.0, 1)

    # Sort descending by priority weight
    scored_subjects.sort(key=lambda x: x["raw_weight"], reverse=True)
    return scored_subjects


def build_7day_study_schedule(scored_subjects):
    """
    Distributes subjects across a 7-day schedule (Today to Today+6).
    Pairs higher-priority subjects with lighter subjects to prevent burnout.
    """
    if not scored_subjects:
        return []

    days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = date.today()
    schedule = []

    # Focus topic templates mapped by subject difficulty and preparation
    topic_catalog = [
        "Core Theory & High-Yield Concept Revision",
        "Practice Numerical Problems & Code Implementation",
        "Previous Years Exam Questions & Model Papers",
        "Formula Sheet, Definitions & Rapid Recall",
        "Deep Dive into Challenging Textbook Chapters",
        "Timed Mock Quiz & Doubt Clarification",
        "Summary Flashcards & Diagram Review"
    ]

    for day_offset in range(7):
        target_date = today + timedelta(days=day_offset)
        day_of_week = target_date.strftime("%A")

        # Select 2-3 subjects for this day based on rotating round-robin weighted index
        day_tasks = []
        # Day's primary subject: rotates top subjects
        sub1 = scored_subjects[day_offset % len(scored_subjects)]
        sub1_duration = max(1.0, min(2.5, round(sub1["recommended_daily_hours"] * 2.0, 1)))
        topic1 = topic_catalog[(day_offset * 2) % len(topic_catalog)]

        day_tasks.append({
            "subject_id": sub1["id"],
            "subject_name": sub1["name"],
            "topic": f"{sub1['name']}: {topic1}",
            "duration": sub1_duration,
            "difficulty": sub1["difficulty"],
            "days_left": sub1["days_left"]
        })

        if len(scored_subjects) > 1:
            # Day's secondary subject
            sub2 = scored_subjects[(day_offset + 1) % len(scored_subjects)]
            sub2_duration = max(1.0, min(2.0, round(sub2["recommended_daily_hours"] * 1.5, 1)))
            topic2 = topic_catalog[(day_offset * 2 + 1) % len(topic_catalog)]
            day_tasks.append({
                "subject_id": sub2["id"],
                "subject_name": sub2["name"],
                "topic": f"{sub2['name']}: {topic2}",
                "duration": sub2_duration,
                "difficulty": sub2["difficulty"],
                "days_left": sub2["days_left"]
            })

        total_day_hours = round(sum(t["duration"] for t in day_tasks), 1)

        schedule.append({
            "date": target_date.isoformat(),
            "display_date": target_date.strftime("%b %d, %Y"),
            "day_name": day_of_week,
            "is_today": (day_offset == 0),
            "total_hours": total_day_hours,
            "tasks": day_tasks
        })

    return schedule


# ---------------------------------------------------------
# Rule-Based "AI" Recommendation Engine
# ---------------------------------------------------------
def generate_ai_recommendations(student_id):
    """
    Expert rule-based recommendation system.
    Evaluates:
      - Subject preparation thresholds (< 40%)
      - Imminent hard exams (<= 10 days)
      - Low test performance (< 50%)
      - Daily task completion velocity (< 60% vs >= 80%)
      - Academic strengths and optimization advice
    """
    db = get_db()
    recommendations = []

    subjects = db.execute("SELECT * FROM subjects WHERE student_id = ?", (student_id,)).fetchall()
    tasks = db.execute("SELECT * FROM study_tasks WHERE student_id = ?", (student_id,)).fetchall()
    scores = db.execute("SELECT * FROM performance WHERE student_id = ?", (student_id,)).fetchall()

    today = date.today()

    # Rule 1: Low Preparation Alert
    for sub in subjects:
        prep = float(sub["prep_percentage"])
        if prep < 40.0:
            recommendations.append({
                "type": "urgent",
                "badge": "High Priority",
                "title": f"Low Preparation Alert: {sub['name']}",
                "icon": "fa-triangle-exclamation",
                "text": f"Your preparation for {sub['name']} is currently only {prep:.0f}%. We recommend increasing your daily study time by at least 1.5 hours and focusing on fundamental core topics immediately.",
                "action": "Adjust Study Hours"
            })

    # Rule 2: Hard Subject with Close Exam Date
    for sub in subjects:
        try:
            exam_dt = datetime.strptime(sub["exam_date"], "%Y-%m-%d").date()
            days_left = (exam_dt - today).days
        except Exception:
            days_left = 30

        if sub["difficulty"].lower() == "hard" and 0 <= days_left <= 10:
            recommendations.append({
                "type": "danger",
                "badge": "Exam Critical",
                "title": f"Critical Exam Looming: {sub['name']}",
                "icon": "fa-fire",
                "text": f"{sub['name']} is categorized as 'Hard' and your exam is in only {days_left} day(s) ({sub['exam_date']}). Prioritize past exam question papers, practice timed mock sessions, and avoid starting new unrelated topics.",
                "action": "View Study Plan"
            })

    # Rule 3: Low Test / Quiz Performance (< 50%)
    subject_marks = {}
    for sc in scores:
        sname = sc["subject_name"]
        if sname not in subject_marks:
            subject_marks[sname] = []
        pct = (sc["marks_obtained"] / sc["max_marks"]) * 100.0 if sc["max_marks"] > 0 else 0
        subject_marks[sname].append(pct)

    for sname, pct_list in subject_marks.items():
        avg_score = sum(pct_list) / len(pct_list)
        if avg_score < 50.0:
            recommendations.append({
                "type": "warning",
                "badge": "Academic Warning",
                "title": f"Performance Deficit in {sname}",
                "icon": "fa-arrow-trend-down",
                "text": f"Your average test score in {sname} is {avg_score:.1f}%. Consider consulting lecture notes, revising textbook examples, and seeking clarification from professors or peers on weak subtopics.",
                "action": "Check Analytics"
            })
        elif avg_score >= 80.0:
            recommendations.append({
                "type": "success",
                "badge": "Mastery Achieved",
                "title": f"Strong Mastery: {sname}",
                "icon": "fa-award",
                "text": f"Outstanding performance in {sname} with an average of {avg_score:.1f}%. Maintain this high standard using spaced repetition and brief periodic review summaries.",
                "action": "Maintain Rhythm"
            })

    # Rule 4: Task Completion Velocity
    if tasks:
        total_t = len(tasks)
        completed_t = sum(1 for t in tasks if t["status"] == "Completed")
        rate = (completed_t / total_t) * 100.0

        if rate < 60.0:
            recommendations.append({
                "type": "warning",
                "badge": "Study Velocity",
                "title": "Task Completion Rate Below 60%",
                "icon": "fa-clock",
                "text": f"Your current study task completion rate is {rate:.1f}%. Try breaking extensive sessions into smaller 30-minute Pomodoro blocks and focus on clearing the top 2 urgent tasks each morning.",
                "action": "Go to Tasks"
            })
        elif rate >= 80.0:
            recommendations.append({
                "type": "success",
                "badge": "Consistent Effort",
                "title": "Excellent Study Consistency!",
                "icon": "fa-circle-check",
                "text": f"Superb dedication! You have successfully completed {rate:.1f}% of your planned study tasks. High consistency is strongly correlated with exam grade improvements.",
                "action": "Keep It Up"
            })

    # Rule 5: Fallback if no specific recommendations triggered
    if not recommendations:
        recommendations.append({
            "type": "info",
            "badge": "AI Guidance",
            "title": "Balanced Study Trajectory",
            "icon": "fa-lightbulb",
            "text": "Your study schedule and preparation appear well-balanced. Keep following the generated daily tasks and log test results regularly to refine your AI insights.",
            "action": "Explore Dashboard"
        })

    return recommendations


# ---------------------------------------------------------
# Performance Analytics Calculation
# ---------------------------------------------------------
def calculate_performance_analytics(student_id):
    """
    Computes overall statistics, subject averages, and classifies
    strong subjects (>= 75%), moderate subjects (50-74%), and weak subjects (< 50%).
    """
    db = get_db()
    scores = db.execute("""
        SELECT * FROM performance WHERE student_id = ? ORDER BY test_date DESC, id DESC
    """, (student_id,)).fetchall()

    if not scores:
        return {
            "total_tests": 0,
            "overall_average": 0.0,
            "subject_summaries": [],
            "strong_subjects": [],
            "moderate_subjects": [],
            "weak_subjects": [],
            "weakest_subject": None,
            "strongest_subject": None,
            "academic_grade": "No Records"
        }

    subject_data = {}
    for row in scores:
        sname = row["subject_name"]
        if sname not in subject_data:
            subject_data[sname] = {
                "name": sname,
                "scores": [],
                "total_obtained": 0.0,
                "total_max": 0.0,
                "test_count": 0
            }
        pct = (row["marks_obtained"] / row["max_marks"]) * 100.0 if row["max_marks"] > 0 else 0
        subject_data[sname]["scores"].append(pct)
        subject_data[sname]["total_obtained"] += row["marks_obtained"]
        subject_data[sname]["total_max"] += row["max_marks"]
        subject_data[sname]["test_count"] += 1

    subject_summaries = []
    strong_subjects = []
    moderate_subjects = []
    weak_subjects = []

    for sname, data in subject_data.items():
        avg = sum(data["scores"]) / len(data["scores"])
        summary = {
            "name": sname,
            "average": round(avg, 1),
            "test_count": data["test_count"],
            "total_obtained": round(data["total_obtained"], 1),
            "total_max": round(data["total_max"], 1)
        }

        if avg >= 75.0:
            summary["status"] = "Strong"
            summary["badge_class"] = "badge-success"
            strong_subjects.append(summary)
        elif avg >= 50.0:
            summary["status"] = "Moderate"
            summary["badge_class"] = "badge-warning"
            moderate_subjects.append(summary)
        else:
            summary["status"] = "Needs Attention"
            summary["badge_class"] = "badge-danger"
            weak_subjects.append(summary)

        subject_summaries.append(summary)

    subject_summaries.sort(key=lambda x: x["average"], reverse=True)
    overall_avg = round(sum(s["average"] for s in subject_summaries) / len(subject_summaries), 1)

    strongest = subject_summaries[0] if subject_summaries else None
    weakest = subject_summaries[-1] if subject_summaries else None

    if overall_avg >= 85.0:
        grade = "A+ (Outstanding)"
    elif overall_avg >= 75.0:
        grade = "A (Very Good)"
    elif overall_avg >= 65.0:
        grade = "B (Good)"
    elif overall_avg >= 50.0:
        grade = "C (Satisfactory)"
    else:
        grade = "D (Needs Improvement)"

    return {
        "total_tests": len(scores),
        "overall_average": overall_avg,
        "subject_summaries": subject_summaries,
        "strong_subjects": strong_subjects,
        "moderate_subjects": moderate_subjects,
        "weak_subjects": weak_subjects,
        "weakest_subject": weakest,
        "strongest_subject": strongest,
        "academic_grade": grade
    }


# ---------------------------------------------------------
# Application Routes
# ---------------------------------------------------------
@app.before_request
def setup_on_first_request():
    """Ensure database and demo records exist."""
    init_db()
    # Check if this is the first run to initialize sample data
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    if count == 0:
        seed_demo_data(force=False)


@app.route("/")
def index():
    """Home redirect to dashboard."""
    return redirect(url_for("dashboard"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """Student Profile View and Update."""
    db = get_db()
    student = get_current_student()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        college = request.form.get("college", "").strip()
        course = request.form.get("course", "").strip()
        year_semester = request.form.get("year_semester", "").strip()
        email = request.form.get("email", "").strip()

        if not name or not college or not course:
            flash("Please fill in Student Name, College, and Course.", "danger")
        else:
            db.execute("""
                UPDATE students
                SET name = ?, college = ?, course = ?, year_semester = ?, email = ?
                WHERE id = ?
            """, (name, college, course, year_semester, email, student["id"]))
            db.commit()
            flash("Student profile successfully updated!", "success")
            return redirect(url_for("profile"))

    # Refresh student after potential update
    student = get_current_student()
    return render_template("index.html", student=student, active_page="profile")


@app.route("/dashboard")
def dashboard():
    """Central Student Dashboard."""
    db = get_db()
    student = get_current_student()
    student_id = student["id"]

    subjects = db.execute("SELECT * FROM subjects WHERE student_id = ? ORDER BY exam_date ASC", (student_id,)).fetchall()
    tasks = db.execute("SELECT * FROM study_tasks WHERE student_id = ? ORDER BY task_date ASC, id ASC", (student_id,)).fetchall()

    today_str = date.today().isoformat()
    today_tasks = [t for t in tasks if t["task_date"] == today_str]

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["status"] == "Completed")
    pending_tasks = total_tasks - completed_tasks
    completion_rate = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # Analytics & Recommendations
    analytics = calculate_performance_analytics(student_id)
    recommendations = generate_ai_recommendations(student_id)
    study_plan_weights = calculate_study_plan_weights(student_id)

    # Next upcoming exam
    closest_exam = None
    today = date.today()
    for s in subjects:
        try:
            ex_date = datetime.strptime(s["exam_date"], "%Y-%m-%d").date()
            diff_days = (ex_date - today).days
            if diff_days >= 0:
                closest_exam = {
                    "name": s["name"],
                    "date": s["exam_date"],
                    "days_left": diff_days,
                    "difficulty": s["difficulty"]
                }
                break
        except Exception:
            continue

    total_weekly_hours = sum(s["study_hours_per_week"] for s in subjects) if subjects else 0

    return render_template(
        "dashboard.html",
        student=student,
        subjects=subjects,
        tasks=tasks,
        today_tasks=today_tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        completion_rate=completion_rate,
        analytics=analytics,
        recommendations=recommendations,
        closest_exam=closest_exam,
        total_weekly_hours=total_weekly_hours,
        study_plan_weights=study_plan_weights[:4],  # top 4 priority
        active_page="dashboard"
    )


# ---------------------------------------------------------
# Subject Management Routes
# ---------------------------------------------------------
@app.route("/subjects")
def subjects_view():
    """List of all subjects with details and add form."""
    db = get_db()
    student = get_current_student()
    student_id = student["id"]

    subjects = db.execute("SELECT * FROM subjects WHERE student_id = ? ORDER BY exam_date ASC", (student_id,)).fetchall()

    # Calculate days left for each subject
    today = date.today()
    enriched_subjects = []
    for s in subjects:
        item = dict(s)
        try:
            ex_dt = datetime.strptime(s["exam_date"], "%Y-%m-%d").date()
            item["days_left"] = (ex_dt - today).days
        except Exception:
            item["days_left"] = None
        enriched_subjects.append(item)

    return render_template(
        "subjects.html",
        student=student,
        subjects=enriched_subjects,
        today_iso=today.isoformat(),
        active_page="subjects"
    )


@app.route("/subjects/add", methods=["POST"])
def subjects_add():
    """Add a new subject."""
    db = get_db()
    student = get_current_student()

    name = request.form.get("name", "").strip()
    exam_date = request.form.get("exam_date", "").strip()
    difficulty = request.form.get("difficulty", "Medium").strip()
    prep_percentage = request.form.get("prep_percentage", "0").strip()
    study_hours = request.form.get("study_hours_per_week", "5").strip()

    if not name or not exam_date:
        flash("Subject name and exam date are required.", "danger")
        return redirect(url_for("subjects_view"))

    try:
        prep_val = max(0.0, min(100.0, float(prep_percentage)))
        hrs_val = max(1.0, float(study_hours))
    except ValueError:
        flash("Preparation percentage and study hours must be valid numbers.", "danger")
        return redirect(url_for("subjects_view"))

    db.execute("""
        INSERT INTO subjects (student_id, name, exam_date, difficulty, prep_percentage, study_hours_per_week)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student["id"], name, exam_date, difficulty, prep_val, hrs_val))
    db.commit()

    flash(f"Subject '{name}' added successfully!", "success")
    return redirect(url_for("subjects_view"))


@app.route("/subjects/edit/<int:subject_id>", methods=["GET", "POST"])
def subjects_edit(subject_id):
    """Edit an existing subject."""
    db = get_db()
    student = get_current_student()

    subject = db.execute("SELECT * FROM subjects WHERE id = ? AND student_id = ?", (subject_id, student["id"])).fetchone()
    if not subject:
        flash("Subject not found.", "danger")
        return redirect(url_for("subjects_view"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        exam_date = request.form.get("exam_date", "").strip()
        difficulty = request.form.get("difficulty", "Medium").strip()
        prep_percentage = request.form.get("prep_percentage", "0").strip()
        study_hours = request.form.get("study_hours_per_week", "5").strip()

        if not name or not exam_date:
            flash("Subject name and exam date cannot be empty.", "danger")
            return redirect(url_for("subjects_edit", subject_id=subject_id))

        try:
            prep_val = max(0.0, min(100.0, float(prep_percentage)))
            hrs_val = max(1.0, float(study_hours))
        except ValueError:
            flash("Invalid numeric value for preparation or hours.", "danger")
            return redirect(url_for("subjects_edit", subject_id=subject_id))

        db.execute("""
            UPDATE subjects
            SET name = ?, exam_date = ?, difficulty = ?, prep_percentage = ?, study_hours_per_week = ?
            WHERE id = ? AND student_id = ?
        """, (name, exam_date, difficulty, prep_val, hrs_val, subject_id, student["id"]))

        # Update subject name in related tasks and performance records for consistency
        db.execute("UPDATE study_tasks SET subject_name = ? WHERE subject_id = ?", (name, subject_id))
        db.execute("UPDATE performance SET subject_name = ? WHERE subject_id = ?", (name, subject_id))
        db.commit()

        flash(f"Subject '{name}' updated successfully!", "success")
        return redirect(url_for("subjects_view"))

    return render_template("subjects.html", student=student, edit_subject=dict(subject), active_page="subjects")


@app.route("/subjects/delete/<int:subject_id>", methods=["POST"])
def subjects_delete(subject_id):
    """Delete a subject and related tasks/tests."""
    db = get_db()
    student = get_current_student()

    db.execute("DELETE FROM subjects WHERE id = ? AND student_id = ?", (subject_id, student["id"]))
    db.commit()

    flash("Subject and associated records deleted.", "info")
    return redirect(url_for("subjects_view"))


# ---------------------------------------------------------
# Study Plan Generator Routes
# ---------------------------------------------------------
@app.route("/study-plan")
def study_plan_view():
    """Study Plan Generator dashboard and weekly breakdown."""
    student = get_current_student()
    student_id = student["id"]

    scored_subjects = calculate_study_plan_weights(student_id)
    weekly_schedule = build_7day_study_schedule(scored_subjects)
    recommendations = generate_ai_recommendations(student_id)

    total_weekly_plan_hours = sum(s["recommended_weekly_hours"] for s in scored_subjects)

    return render_template(
        "study_plan.html",
        student=student,
        scored_subjects=scored_subjects,
        weekly_schedule=weekly_schedule,
        recommendations=recommendations,
        total_weekly_plan_hours=round(total_weekly_plan_hours, 1),
        active_page="study_plan"
    )


@app.route("/study-plan/generate", methods=["POST"])
def study_plan_generate():
    """
    Populates study_tasks in the database from the 7-day schedule generated
    by the AI algorithm.
    """
    db = get_db()
    student = get_current_student()
    student_id = student["id"]

    scored_subjects = calculate_study_plan_weights(student_id)
    if not scored_subjects:
        flash("Please add at least one subject before generating a study plan.", "warning")
        return redirect(url_for("subjects_view"))

    weekly_schedule = build_7day_study_schedule(scored_subjects)

    # Optional: user can choose whether to replace existing pending tasks
    replace_pending = request.form.get("replace_pending", "yes") == "yes"
    if replace_pending:
        today_iso = date.today().isoformat()
        db.execute("""
            DELETE FROM study_tasks 
            WHERE student_id = ? AND task_date >= ? AND status = 'Pending'
        """, (student_id, today_iso))

    tasks_added = 0
    for day in weekly_schedule:
        task_date = day["date"]
        for task in day["tasks"]:
            db.execute("""
                INSERT INTO study_tasks (student_id, subject_id, subject_name, topic, task_date, duration_hours, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending')
            """, (
                student_id,
                task["subject_id"],
                task["subject_name"],
                task["topic"],
                task_date,
                task["duration"]
            ))
            tasks_added += 1

    db.commit()
    flash(f"Study Plan successfully generated! Added {tasks_added} prioritized daily study tasks.", "success")
    return redirect(url_for("tasks_view"))


# ---------------------------------------------------------
# Daily Task Tracking Routes
# ---------------------------------------------------------
@app.route("/tasks")
def tasks_view():
    """Daily Task Tracker with filters."""
    db = get_db()
    student = get_current_student()
    student_id = student["id"]

    status_filter = request.args.get("filter", "all")
    today_iso = date.today().isoformat()

    query = "SELECT * FROM study_tasks WHERE student_id = ?"
    params = [student_id]

    if status_filter == "today":
        query += " AND task_date = ?"
        params.append(today_iso)
    elif status_filter == "pending":
        query += " AND status = 'Pending'"
    elif status_filter == "completed":
        query += " AND status = 'Completed'"

    query += " ORDER BY task_date ASC, id ASC"
    tasks = db.execute(query, params).fetchall()

    # Metrics for all tasks of this student
    all_tasks = db.execute("SELECT status, task_date FROM study_tasks WHERE student_id = ?", (student_id,)).fetchall()
    total_count = len(all_tasks)
    completed_count = sum(1 for t in all_tasks if t["status"] == "Completed")
    pending_count = total_count - completed_count
    completion_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 0.0

    today_count = sum(1 for t in all_tasks if t["task_date"] == today_iso)
    today_completed = sum(1 for t in all_tasks if t["task_date"] == today_iso and t["status"] == "Completed")

    subjects = db.execute("SELECT id, name FROM subjects WHERE student_id = ? ORDER BY name ASC", (student_id,)).fetchall()

    return render_template(
        "tasks.html",
        student=student,
        tasks=tasks,
        subjects=subjects,
        current_filter=status_filter,
        today_iso=today_iso,
        total_count=total_count,
        completed_count=completed_count,
        pending_count=pending_count,
        completion_rate=completion_rate,
        today_count=today_count,
        today_completed=today_completed,
        active_page="tasks"
    )


@app.route("/tasks/toggle/<int:task_id>", methods=["POST"])
def tasks_toggle(task_id):
    """Toggle a task between Pending and Completed."""
    db = get_db()
    student = get_current_student()

    task = db.execute("SELECT status FROM study_tasks WHERE id = ? AND student_id = ?", (task_id, student["id"])).fetchone()
    if not task:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "Task not found"}), 404
        flash("Task not found.", "danger")
        return redirect(url_for("tasks_view"))

    new_status = "Completed" if task["status"] == "Pending" else "Pending"
    db.execute("UPDATE study_tasks SET status = ? WHERE id = ?", (new_status, task_id))
    db.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        # Return updated task counts for seamless UI update
        all_tasks = db.execute("SELECT status FROM study_tasks WHERE student_id = ?", (student["id"],)).fetchall()
        total = len(all_tasks)
        completed = sum(1 for t in all_tasks if t["status"] == "Completed")
        rate = round((completed / total * 100), 1) if total > 0 else 0
        return jsonify({
            "success": True,
            "new_status": new_status,
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "rate": rate
        })

    flash(f"Task marked as {new_status}.", "success")
    return redirect(request.referrer or url_for("tasks_view"))


@app.route("/tasks/add", methods=["POST"])
def tasks_add():
    """Add a manual study task."""
    db = get_db()
    student = get_current_student()

    subject_id = request.form.get("subject_id")
    subject_name = request.form.get("subject_name", "").strip()
    topic = request.form.get("topic", "").strip()
    task_date = request.form.get("task_date", "").strip()
    duration = request.form.get("duration_hours", "1.0").strip()

    # Look up subject name if subject_id is provided
    if subject_id and not subject_name:
        sub = db.execute("SELECT name FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if sub:
            subject_name = sub["name"]

    if not subject_name or not topic or not task_date:
        flash("Subject, topic description, and date are required.", "danger")
        return redirect(url_for("tasks_view"))

    try:
        dur_val = max(0.25, min(12.0, float(duration)))
    except ValueError:
        dur_val = 1.0

    db.execute("""
        INSERT INTO study_tasks (student_id, subject_id, subject_name, topic, task_date, duration_hours, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    """, (student["id"], subject_id or None, subject_name, topic, task_date, dur_val))
    db.commit()

    flash(f"New task '{topic}' added for {task_date}.", "success")
    return redirect(url_for("tasks_view"))


@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
def tasks_delete(task_id):
    """Delete a specific task."""
    db = get_db()
    student = get_current_student()

    db.execute("DELETE FROM study_tasks WHERE id = ? AND student_id = ?", (task_id, student["id"]))
    db.commit()

    flash("Task deleted.", "info")
    return redirect(url_for("tasks_view"))


@app.route("/tasks/clear-completed", methods=["POST"])
def tasks_clear_completed():
    """Remove all completed tasks."""
    db = get_db()
    student = get_current_student()

    cur = db.execute("DELETE FROM study_tasks WHERE student_id = ? AND status = 'Completed'", (student["id"],))
    count = cur.rowcount
    db.commit()

    flash(f"Cleared {count} completed task(s).", "info")
    return redirect(url_for("tasks_view"))


# ---------------------------------------------------------
# Performance & Academic Analysis Routes
# ---------------------------------------------------------
@app.route("/performance")
def performance_view():
    """Academic Performance Dashboard."""
    db = get_db()
    student = get_current_student()
    student_id = student["id"]

    scores = db.execute("""
        SELECT * FROM performance WHERE student_id = ? ORDER BY test_date DESC, id DESC
    """, (student_id,)).fetchall()

    # Enrich scores with percentage
    enriched_scores = []
    for sc in scores:
        item = dict(sc)
        item["percentage"] = round((sc["marks_obtained"] / sc["max_marks"] * 100), 1) if sc["max_marks"] > 0 else 0
        enriched_scores.append(item)

    analytics = calculate_performance_analytics(student_id)
    subjects = db.execute("SELECT id, name FROM subjects WHERE student_id = ? ORDER BY name ASC", (student_id,)).fetchall()
    recommendations = generate_ai_recommendations(student_id)

    return render_template(
        "performance.html",
        student=student,
        scores=enriched_scores,
        subjects=subjects,
        analytics=analytics,
        recommendations=recommendations,
        today_iso=date.today().isoformat(),
        active_page="performance"
    )


@app.route("/performance/add", methods=["POST"])
def performance_add():
    """Add a test / exam result."""
    db = get_db()
    student = get_current_student()

    subject_id = request.form.get("subject_id")
    subject_name = request.form.get("subject_name", "").strip()
    test_name = request.form.get("test_name", "").strip()
    max_marks = request.form.get("max_marks", "100").strip()
    marks_obtained = request.form.get("marks_obtained", "0").strip()
    test_date = request.form.get("test_date", "").strip() or date.today().isoformat()

    if subject_id and not subject_name:
        sub = db.execute("SELECT name FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if sub:
            subject_name = sub["name"]

    if not subject_name or not test_name:
        flash("Subject and Test Name are required.", "danger")
        return redirect(url_for("performance_view"))

    try:
        max_m = float(max_marks)
        obt_m = float(marks_obtained)
        if max_m <= 0:
            flash("Maximum marks must be greater than 0.", "danger")
            return redirect(url_for("performance_view"))
        if obt_m < 0 or obt_m > max_m:
            flash("Marks obtained must be between 0 and Maximum Marks.", "danger")
            return redirect(url_for("performance_view"))
    except ValueError:
        flash("Please enter valid numeric marks.", "danger")
        return redirect(url_for("performance_view"))

    db.execute("""
        INSERT INTO performance (student_id, subject_id, subject_name, test_name, max_marks, marks_obtained, test_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (student["id"], subject_id or None, subject_name, test_name, max_m, obt_m, test_date))
    db.commit()

    flash(f"Performance result for '{test_name}' recorded successfully!", "success")
    return redirect(url_for("performance_view"))


@app.route("/performance/delete/<int:record_id>", methods=["POST"])
def performance_delete(record_id):
    """Delete a test record."""
    db = get_db()
    student = get_current_student()

    db.execute("DELETE FROM performance WHERE id = ? AND student_id = ?", (record_id, student["id"]))
    db.commit()

    flash("Performance record deleted.", "info")
    return redirect(url_for("performance_view"))


# ---------------------------------------------------------
# Chart Data API (for Chart.js)
# ---------------------------------------------------------
@app.route("/api/chart-data")
def api_chart_data():
    """Provides dynamic JSON datasets for Chart.js rendering."""
    db = get_db()
    student = get_current_student()
    student_id = student["id"]

    # 1. Subject Test Performance Averages
    analytics = calculate_performance_analytics(student_id)
    subject_names = [s["name"] for s in analytics["subject_summaries"]]
    subject_averages = [s["average"] for s in analytics["subject_summaries"]]

    # 2. Task Completion Doughnut
    tasks = db.execute("SELECT status FROM study_tasks WHERE student_id = ?", (student_id,)).fetchall()
    completed_t = sum(1 for t in tasks if t["status"] == "Completed")
    pending_t = len(tasks) - completed_t

    # 3. Subject Preparation Percentages
    subjects = db.execute("SELECT name, prep_percentage, study_hours_per_week FROM subjects WHERE student_id = ? ORDER BY name ASC", (student_id,)).fetchall()
    prep_labels = [s["name"] for s in subjects]
    prep_values = [s["prep_percentage"] for s in subjects]
    study_hours = [s["study_hours_per_week"] for s in subjects]

    # 4. Weekly Plan Allocated Hours
    scored_subjects = calculate_study_plan_weights(student_id)
    plan_labels = [s["name"] for s in scored_subjects]
    plan_hours = [s["recommended_weekly_hours"] for s in scored_subjects]

    return jsonify({
        "performance": {
            "labels": subject_names,
            "averages": subject_averages,
            "overall_average": analytics["overall_average"]
        },
        "tasks": {
            "completed": completed_t,
            "pending": pending_t,
            "total": len(tasks)
        },
        "preparation": {
            "labels": prep_labels,
            "percentages": prep_values,
            "hours": study_hours
        },
        "study_plan": {
            "labels": plan_labels,
            "allocated_hours": plan_hours
        }
    })


# ---------------------------------------------------------
# Demo Data Reset Route
# ---------------------------------------------------------
@app.route("/demo/reset", methods=["POST", "GET"])
def demo_reset():
    """Resets the database with complete presentation-ready sample data."""
    seed_demo_data(force=True)
    flash("Demo data successfully loaded! All sample subjects, study tasks, and test records are ready for faculty presentation.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
        count = get_db().execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        if count == 0:
            seed_demo_data(force=True)
    print("=" * 60)
    print(" AI-Powered Student Study Planner and Performance Analyzer ")
    print(" Server running locally at: http://127.0.0.1:5000 ")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)
