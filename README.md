# AI-Powered Student Study Planner and Performance Analyzer

An intelligent, full-stack college mini-project web application built using **Python Flask**, **SQLite**, **HTML5/CSS3/JavaScript**, and **Chart.js**.

---

## 📌 Project Overview

College students often struggle to allocate balanced study time across multiple coursework subjects, prepare adequately before impending exam dates, and analyze which subjects require academic remediation. 

The **AI-Powered Student Study Planner and Performance Analyzer** solves this problem by providing:
1. **Curriculum & Exam Organization**: Track subjects, exam dates, perceived difficulty, and current preparation levels.
2. **Algorithmic Study Plan Generator**: Rule-based AI scheduling that automatically computes subject priority weights based on exam proximity, difficulty, and preparation deficits.
3. **Daily Task Execution**: Breaks weekly targets into actionable daily 1–2.5 hour study tasks with real-time completion tracking.
4. **Performance & Grade Analytics**: Records test/quiz scores, computes subject and overall averages, and classifies subjects into **Strong (&ge; 75%)**, **Moderate (50–74%)**, and **Needs Attention (&lt; 50%)**.
5. **Rule-Based AI Recommendation Engine**: Generates personalized, prioritized academic recommendations and warnings without requiring heavy machine learning libraries.
6. **Interactive Visualizations**: Clean Chart.js bar charts, doughnut charts, and progress bars.

---

## 🏗️ System Architecture & Project Flow

```
                      ┌────────────────────────┐
                      │    Student Profile     │
                      └───────────┬────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │ Enter Subjects + Exams │
                      │  + Difficulty + Prep % │
                      └───────────┬────────────┘
                                  │
                                  ▼
                      ┌────────────────────────┐
                      │ AI Study Plan Engine   │
                      │   (Priority Weights)   │
                      └───────────┬────────────┘
                                  │
                   ┌──────────────┴──────────────┐
                   ▼                             ▼
        ┌─────────────────────┐       ┌─────────────────────┐
        │ Daily Task Tracking │       │ Performance Analyzer│
        │ (Checklist Tracker) │       │ (Test Marks & Visual│
        └──────────┬──────────┘       │  Analytics/Averages)│
                   │                  └──────────┬──────────┘
                   └──────────────┬──────────────┘
                                  ▼
                      ┌────────────────────────┐
                      │ Rule-Based AI Advisory │
                      │  & Central Dashboard   │
                      └────────────────────────┘
```

---

## 🗂️ Project Folder Structure

```
student-study-planner/
│
├── app.py                     # Flask application routes, AI algorithms, DB operations
├── database.db                # SQLite database (auto-created on first run)
├── requirements.txt           # Python package dependencies
│
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Shared layout, responsive sidebar & topbar
│   ├── index.html             # Student Profile view and edit
│   ├── dashboard.html         # Central student dashboard with metrics & AI tips
│   ├── subjects.html          # Subject management (Add, Edit, Delete, Prep slider)
│   ├── study_plan.html        # 7-day visual schedule & algorithm breakdown
│   ├── tasks.html             # Daily task tracker & execution checklist
│   └── performance.html       # Test score records, subject classification & analytics
│
├── static/
│   ├── css/
│   │   └── style.css          # Clean, modern, responsive CSS styling
│   └── js/
│       └── script.js          # Chart.js initializations & asynchronous task toggles
│
└── README.md                  # Complete documentation and faculty viva guide
```

---

## 🧠 Core Algorithms & Technical Logic

### 1. Study Plan Generation Algorithm
Rather than assigning equal hours to every subject, the system uses a multi-factor weighting algorithm:

$$\text{Priority Weight } W_i = \text{Difficulty}_i \times \text{Preparation Deficit}_i \times \text{Exam Urgency}_i$$

- **Exam Urgency ($U_i$)**: Inversely proportional to days remaining:
  - $\le 0\text{ days (Exam Today/Overdue)}$: $3.5\times$
  - $\le 3\text{ days (Extremely Urgent)}$: $3.0\times$
  - $\le 7\text{ days (Within 1 week)}$: $2.2\times$
  - $\le 14\text{ days (Within 2 weeks)}$: $1.6\times$
  - $\le 30\text{ days (Upcoming)}$: $1.2\times$
  - $> 30\text{ days (Ample Time)}$: $0.85\times$
- **Subject Difficulty ($\text{Diff}_i$)**:
  - $\text{Hard} = 1.75\times$
  - $\text{Medium} = 1.25\times$
  - $\text{Easy} = 1.0\times$
- **Preparation Deficit ($\text{Def}_i$)**:
  $$\text{Def}_i = \frac{100 - \text{prep\_percentage}_i}{100} + 0.25$$
  *(Even 100% prepared subjects maintain a baseline 0.25 weight for periodic revision).*
- **Normalized Weekly Hours Allocation**:
  $$\text{Hours}_i = \left(\frac{W_i}{\sum W}\right) \times \text{Total Weekly Study Hours}$$
- **7-Day Rolling Schedule**:
  Distributes high-priority and secondary subjects across Monday through Sunday in manageable 1.0 to 2.5 hour sessions paired with high-yield revision topics.

---

### 2. Rule-Based AI Recommendation Engine
The AI recommendation engine executes deterministic heuristic rules based on student inputs:

| Condition Trigger | Alert Level | Recommendation Generated |
| :--- | :---: | :--- |
| **Preparation < 40%** | `High Priority` | "Your preparation is low (X%). Increase daily study time by 1.5 hrs and prioritize fundamental concepts." |
| **Difficulty = Hard & Exam $\le$ 10 Days** | `Exam Critical` | "Critical exam looming in X days. Prioritize past exam question papers, practice timed mock sessions." |
| **Subject Test Average < 50%** | `Academic Warning` | "Performance deficit in [Subject] (avg X%). Consult textbook notes and seek professor doubt clarification." |
| **Task Completion Rate < 60%** | `Study Velocity` | "Completion rate is below 60%. Break sessions into smaller 30-min Pomodoro blocks." |
| **Task Completion Rate $\ge$ 80%** | `Consistent Effort` | "Superb consistency (X% tasks cleared). High study consistency strongly correlates with top exam grades." |
| **Subject Average $\ge$ 80%** | `Mastery Achieved` | "Strong mastery achieved. Maintain your edge with spaced repetition and brief periodic reviews." |

---

## 💾 Database Schema (SQLite)

The application utilizes 4 normalized tables with referential integrity (`ON DELETE CASCADE`):

1. **`students`**:
   - `id` (INTEGER PRIMARY KEY)
   - `name` (TEXT)
   - `college` (TEXT)
   - `course` (TEXT)
   - `year_semester` (TEXT)
   - `email` (TEXT)
   - `created_at` (TIMESTAMP)

2. **`subjects`**:
   - `id` (INTEGER PRIMARY KEY)
   - `student_id` (INTEGER, FK &rarr; students.id)
   - `name` (TEXT)
   - `exam_date` (TEXT ISO)
   - `difficulty` (TEXT: Easy / Medium / Hard)
   - `prep_percentage` (REAL: 0–100)
   - `study_hours_per_week` (REAL)
   - `created_at` (TIMESTAMP)

3. **`study_tasks`**:
   - `id` (INTEGER PRIMARY KEY)
   - `student_id` (INTEGER, FK &rarr; students.id)
   - `subject_id` (INTEGER, FK &rarr; subjects.id)
   - `subject_name` (TEXT)
   - `topic` (TEXT)
   - `task_date` (TEXT ISO)
   - `duration_hours` (REAL)
   - `status` (TEXT: 'Pending' or 'Completed')
   - `created_at` (TIMESTAMP)

4. **`performance`**:
   - `id` (INTEGER PRIMARY KEY)
   - `student_id` (INTEGER, FK &rarr; students.id)
   - `subject_id` (INTEGER, FK &rarr; subjects.id)
   - `subject_name` (TEXT)
   - `test_name` (TEXT)
   - `max_marks` (REAL)
   - `marks_obtained` (REAL)
   - `test_date` (TEXT)
   - `created_at` (TIMESTAMP)

---

## 🚀 How to Run the Project Locally

### Prerequisites
- Python 3.9+ (Python 3.12 recommended)
- Any modern web browser (Google Chrome, Edge, Firefox, Safari)

### Step 1: Open Terminal in the Project Directory
Navigate to the project folder:
```powershell
cd C:\Users\KHASIM\.gemini\antigravity\scratch\student-study-planner
```

### Step 2: Install Dependencies
Install Flask using pip:
```powershell
pip install -r requirements.txt
```
*(Or use the direct python path: `python -m pip install -r requirements.txt`)*

### Step 3: Run the Application
Start the Flask development server:
```powershell
python app.py
```

### Step 4: Access in Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

> **Note for Faculty Presentation**:
> The project automatically initializes with realistic sample data on its first launch (Aarav Sharma, 5 engineering subjects, past & today's study tasks, and test results).
> If you ever want to re-seed or reset back to pristine presentation demo data, simply click the **"Load Demo Data"** button located at the bottom of the sidebar!

---

## 🎓 Faculty Presentation & Viva Q&A Guide

When presenting this project to college professors, use these clear explanations:

### Q1: Why did you use a rule-based AI system instead of a Machine Learning model?
> **Answer**: In a student study planner, student data starts from zero on day one. A machine learning model requires thousands of historical training records to generalize and acts as a "black box" that cannot explain its reasoning to the student. A rule-based AI expert system is deterministic, instantly adaptable, explainable to the user, and computationally lightweight without requiring heavy dependencies like TensorFlow or PyTorch.

### Q2: How does the Study Plan Generator prioritize subjects?
> **Answer**: The generator uses a composite score combining three key academic metrics:
> 1. **Exam Proximity**: Closer exams have an exponential urgency factor ($1.0\times$ to $3.5\times$).
> 2. **Difficulty Coefficient**: Hard subjects get a $1.75\times$ multiplier.
> 3. **Preparation Gap**: Calculated as $(100 - \text{prep}\%) / 100$.
> The composite weights are normalized against the student's available weekly study hours and populated into daily study tasks.

### Q3: How is data stored and queried?
> **Answer**: We use SQLite, an ACID-compliant embedded relational database. All queries use **parameterized SQL queries (`?`)** to prevent SQL injection vulnerabilities. Cascading foreign keys (`PRAGMA foreign_keys = ON`) maintain referential integrity when deleting subjects.

### Q4: How is Chart.js integrated?
> **Answer**: The Flask backend exposes a clean REST API endpoint (`/api/chart-data`) returning JSON summaries. The frontend JavaScript asynchronously fetches this endpoint and dynamically binds the datasets to responsive HTML5 `<canvas>` elements.

---

## 🛠️ Technologies Used
- **Frontend**: HTML5, CSS3 (CSS Custom Properties, Flexbox, CSS Grid), Vanilla JavaScript ES6+
- **Icons & Fonts**: Font Awesome 6, Google Inter Fonts
- **Data Visualization**: Chart.js 4 (via CDN)
- **Backend Framework**: Python Flask 3
- **Database**: SQLite 3
- **Architecture Pattern**: Model-View-Controller (MVC)
