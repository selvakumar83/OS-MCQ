import streamlit as st
import json
import os
import time
from datetime import datetime, timezone

# ============================================================
# MEMORY MANAGEMENT ONLINE TEST
# ============================================================

TEST_TITLE = "Memory Management Online Test"
TOTAL_QUESTIONS = 10
DURATION_MINUTES = 4

# ============================================================
# SUPABASE / ADMIN SETTINGS
# ============================================================

def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)

SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "SELVAKUMAR@1983")

try:
    from supabase import create_client
except ImportError:
    create_client = None


# ============================================================
# QUESTION BANK
# ============================================================

QUESTIONS = [
    {
        "id": 1,
        "q": """A student opens a large application stored on an SSD. After the application
starts, the CPU repeatedly uses a small portion of its instructions. The first access
takes longer, while later accesses are faster.

Which situation best explains the later improvement?""",
        "options": [
            "The SSD has become faster",
            "Frequently used instructions are available in cache",
            "RAM has become permanent storage",
            "The CPU has stopped using registers",
        ],
        "answer": 1,
    },
    {
        "id": 2,
        "q": """During execution, the CPU needs an intermediate value immediately.
The value is already available inside the processor rather than in RAM.

Which component is most likely holding the value?""",
        "options": [
            "SSD",
            "Main memory",
            "Register",
            "ROM",
        ],
        "answer": 2,
    },
    {
        "id": 3,
        "q": """A CPU requests a data item. The cache is checked first and the requested
item is already present. The CPU obtains it without retrieving it from main memory.

What has occurred?""",
        "options": [
            "Cache miss",
            "Cache hit",
            "Page fault",
            "Memory overflow",
        ],
        "answer": 1,
    },
    {
        "id": 4,
        "q": """A CPU requests an instruction, but the instruction is not currently present
in cache. The system obtains the required instruction from main memory.

What does this situation represent?""",
        "options": [
            "Cache hit",
            "Cache miss",
            "Register hit",
            "Secondary-storage hit",
        ],
        "answer": 1,
    },
    {
        "id": 5,
        "q": """A program repeatedly executes the same loop. Initially, accessing the loop
instructions is slower, but later executions become faster because the required
instructions remain close to the CPU.

Which explanation is most appropriate?""",
        "options": [
            "Cache hits are increasing",
            "SSD capacity is increasing",
            "RAM is becoming non-volatile",
            "Registers are being converted into cache",
        ],
        "answer": 0,
    },
    {
        "id": 6,
        "q": """A computer is switched off unexpectedly while a student is editing an
unsaved document. After restarting, the unsaved changes are lost, but previously
saved documents remain available.

Which explanation is correct?""",
        "options": [
            "RAM is volatile and SSD is non-volatile",
            "RAM is non-volatile and SSD is volatile",
            "Cache is non-volatile and RAM is permanent",
            "Registers are non-volatile and SSD is volatile",
        ],
        "answer": 0,
    },
    {
        "id": 7,
        "q": """A processor requests the same instruction several times. The first request
does not find it in cache, but after it is loaded, subsequent requests find it in cache.

Which sequence best represents these accesses?""",
        "options": [
            "Hit → Hit → Miss",
            "Miss → Hit → Hit",
            "Miss → Miss → Miss",
            "Hit → Miss → Hit",
        ],
        "answer": 1,
    },
    {
        "id": 8,
        "q": """A student says: 'My computer has a 1 TB SSD, so the CPU should execute
programs faster than a computer with a 512 GB SSD.'

Which observation most directly challenges this conclusion?""",
        "options": [
            "Storage capacity and memory access speed are different characteristics",
            "The larger SSD always contains more registers",
            "SSD capacity determines CPU clock speed",
            "SSD directly replaces cache memory",
        ],
        "answer": 0,
    },
    {
        "id": 9,
        "q": """During program execution, the CPU finds one required value in a register,
another in cache, and a third in RAM.

What does this scenario demonstrate?""",
        "options": [
            "All three storage levels have the same access speed",
            "The CPU is using different levels of the memory hierarchy",
            "RAM is being used as secondary storage",
            "Cache is slower than SSD",
        ],
        "answer": 1,
    },
    {
        "id": 10,
        "q": """A program repeatedly accesses data A, B, and C. Initially, these items are
not in cache. They are loaded into cache and remain there while the CPU continues
to use them.

What would you expect during subsequent accesses?""",
        "options": [
            "Mostly cache hits",
            "Mostly cache misses",
            "Direct SSD accesses",
            "Register failures",
        ],
        "answer": 0,
    },
]


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY or create_client is None:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def save_result(record):
    sb = supabase_client()

    if sb is None:
        import sqlite3

        conn = sqlite3.connect("exam_results.db")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                srn TEXT NOT NULL,
                student_name TEXT NOT NULL,
                section TEXT NOT NULL,
                test_title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                submit_time TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                answers TEXT NOT NULL,
                submitted_by_timeout INTEGER NOT NULL
            )
        """)

        # One attempt per SRN
        existing = conn.execute(
            "SELECT id FROM exam_submissions WHERE srn = ? LIMIT 1",
            (record["srn"],)
        ).fetchone()

        if existing:
            conn.close()
            raise Exception("This SRN has already submitted the examination.")

        conn.execute("""
            INSERT INTO exam_submissions
            (srn, student_name, section, test_title, start_time,
             submit_time, score, total, percentage, answers,
             submitted_by_timeout)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["srn"],
            record["student_name"],
            record["section"],
            record["test_title"],
            record["start_time"],
            record["submit_time"],
            record["score"],
            record["total"],
            record["percentage"],
            json.dumps(record["answers"]),
            int(record["submitted_by_timeout"]),
        ))

        conn.commit()
        conn.close()
        return True

    # Supabase database
    response = sb.table("exam_submissions").insert(record).execute()
    return True


def srn_already_submitted(srn):
    sb = supabase_client()

    if sb is None:
        import sqlite3

        conn = sqlite3.connect("exam_results.db")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                srn TEXT,
                student_name TEXT,
                section TEXT,
                test_title TEXT,
                start_time TEXT,
                submit_time TEXT,
                score INTEGER,
                total INTEGER,
                percentage REAL,
                answers TEXT,
                submitted_by_timeout INTEGER
            )
        """)

        row = conn.execute(
            "SELECT id FROM exam_submissions WHERE srn = ? LIMIT 1",
            (srn,)
        ).fetchone()

        conn.close()
        return row is not None

    response = (
        sb.table("exam_submissions")
        .select("id")
        .eq("srn", srn)
        .limit(1)
        .execute()
    )

    return bool(response.data)


def get_results():
    sb = supabase_client()

    if sb is None:
        import sqlite3

        conn = sqlite3.connect("exam_results.db")

        try:
            rows = conn.execute("""
                SELECT srn, student_name, section, test_title,
                       start_time, submit_time, score, total,
                       percentage, submitted_by_timeout
                FROM exam_submissions
                ORDER BY submit_time DESC
            """).fetchall()
        except Exception:
            rows = []

        conn.close()

        cols = [
            "srn", "student_name", "section", "test_title",
            "start_time", "submit_time", "score", "total",
            "percentage", "submitted_by_timeout"
        ]

        return [dict(zip(cols, row)) for row in rows]

    return (
        sb.table("exam_submissions")
        .select(
            "srn,student_name,section,test_title,start_time,"
            "submit_time,score,total,percentage,submitted_by_timeout"
        )
        .order("submit_time", desc=True)
        .execute()
        .data
    )


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Memory Management Test",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.main-title {
    text-align:center;
    font-size:30px;
    font-weight:800;
    margin-bottom:2px;
}

.subtitle {
    text-align:center;
    color:#666;
    margin-bottom:18px;
}

.question-card {
    border:1px solid #d9d9d9;
    border-radius:12px;
    padding:20px;
    margin-bottom:12px;
    background:#ffffff;
color:#222222 !important;
}

.palette-title {
    font-size:18px;
    font-weight:700;
    margin-bottom:10px;
}

.exam-timer {
    background:#111827;
    color:white;
    padding:12px;
    border-radius:10px;
    text-align:center;
    font-size:25px;
    font-weight:800;
}

.timer-danger {
    background:#991b1b;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

state_defaults = {
    "page": "login",
    "student_name": "",
    "srn": "",
    "section": "",
    "start_time": None,
    "current_q": 0,
    "answers": {},
    "submitted": False,
    "score": None,
    "timeout": False,
    "submit_time": None,
    "show_submit_confirm": False,
}

for key, value in state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# TIMER
# ============================================================

def remaining_seconds():
    if st.session_state.start_time is None:
        return DURATION_MINUTES * 60

    elapsed = time.time() - st.session_state.start_time
    return max(0, int(DURATION_MINUTES * 60 - elapsed))


def submit_exam(timeout=False):
    """
    Calculates score and stores the examination result.
    This function is called by the student submission flow.
    """
    if st.session_state.submitted:
        return

    score = 0
    answers_for_db = {}

    for i, q in enumerate(QUESTIONS):
        selected = st.session_state.answers.get(i)

        answers_for_db[str(q["id"])] = (
            selected if selected is not None else None
        )

        if selected is not None and selected == q["answer"]:
            score += 1

    percentage = round(score / TOTAL_QUESTIONS * 100, 2)
    submit_time = datetime.now(timezone.utc).isoformat()

    record = {
        "srn": st.session_state.srn,
        "student_name": st.session_state.student_name,
        "section": st.session_state.section,
        "test_title": TEST_TITLE,
        "start_time": datetime.fromtimestamp(
            st.session_state.start_time,
            tz=timezone.utc
        ).isoformat(),
        "submit_time": submit_time,
        "score": score,
        "total": TOTAL_QUESTIONS,
        "percentage": percentage,
        "answers": answers_for_db,
        "submitted_by_timeout": timeout,
    }

    try:
        save_result(record)

        st.session_state.score = score
        st.session_state.submit_time = submit_time
        st.session_state.timeout = timeout
        st.session_state.submitted = True
        st.session_state.page = "result"

    except Exception as e:
        st.error(f"Submission failed: {e}")
        st.stop()


def show_timer():
    """
    Displays HH:MM:SS countdown.

    IMPORTANT:
    The browser countdown is visual. The server-side remaining_seconds()
    is checked whenever Streamlit reruns. The exam can therefore never
    legitimately be submitted after its 10-minute duration.
    """
    remaining = remaining_seconds()

    hours = remaining // 3600
    minutes = (remaining % 3600) // 60
    seconds = remaining % 60

    timer_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    if remaining <= 30:
        timer_class = "exam-timer timer-danger"
    else:
        timer_class = "exam-timer"

    st.markdown(
        f'<div class="{timer_class}">⏱️ TIME REMAINING<br>'
        f'<span style="font-size:30px;">{timer_text}</span></div>',
        unsafe_allow_html=True
    )


def run_browser_timer():
    # Kept for compatibility; the actual timer is driven by Streamlit reruns.
    return


# OLD_BROWSER_TIMER_REMOVED

def old_run_browser_timer():
    return


# ============================================================
# LOGIN PAGE
# ============================================================

if st.session_state.page == "login":

    st.markdown(
        '<div class="main-title">📝 Memory Management Online Test</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        '10 Questions • 10 Marks • 5 Minutes'
        '</div>',
        unsafe_allow_html=True
    )

    st.info(
        "Enter your details carefully. Your examination timer starts "
        "only after you click START EXAM."
    )

    with st.container(border=True):

        name = st.text_input(
            "Student Name",
            placeholder="Enter your full name"
        )

        srn = st.text_input(
            "SRN / Register Number",
            placeholder="Example: PES2UG25AM221"
        ).strip().upper()

        section = st.selectbox(
            "Section",
            ["B", "C", "D"]
        )

        declaration = st.checkbox(
            "I confirm that the Name, SRN and Section entered above are correct."
        )

        if st.button(
            "🚀 START EXAM",
            type="primary",
            use_container_width=True
        ):

            if not name.strip() or not srn or not declaration:
                st.error(
                    "Please complete all details and confirm the declaration."
                )

            else:
                try:

                    if srn_already_submitted(srn):

                        st.error(
                            "This SRN has already submitted this examination. "
                            "Only one attempt is permitted."
                        )

                    else:

                        # TIMER STARTS HERE
                        st.session_state.student_name = name.strip()
                        st.session_state.srn = srn
                        st.session_state.section = section

                        st.session_state.start_time = time.time()

                        st.session_state.current_q = 0
                        st.session_state.answers = {}
                        st.session_state.timeout = False
                        st.session_state.submitted = False
                        st.session_state.show_submit_confirm = False
                        st.session_state.page = "exam"

                        st.rerun()

                except Exception as e:
                    st.error(f"Unable to start the examination: {e}")


# ============================================================
# EXAM PAGE
# ============================================================

elif st.session_state.page == "exam":

    # --------------------------------------------------------
    # SERVER-SIDE TIME EXPIRY CHECK
    # --------------------------------------------------------

    if remaining_seconds() <= 0:

        # Automatically submit with timeout flag
        submit_exam(timeout=True)
        st.rerun()

    # Refresh the page every second so the HH:MM:SS timer is updated reliably.
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, key="exam_timer_refresh")

    st.markdown(
        '<div class="main-title">📝 Memory Management Test</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:

        st.markdown(
            f"**Student:** {st.session_state.student_name}<br>"
            f"**SRN:** {st.session_state.srn}<br>"
            f"**Section:** {st.session_state.section}",
            unsafe_allow_html=True
        )

    with col2:

        st.write(f"**Questions:** {TOTAL_QUESTIONS}")
        st.write("**Maximum Marks:** 10")

    with col3:

        show_timer()

    st.divider()

    # --------------------------------------------------------
    # TWO COLUMN BANK EXAM LAYOUT
    # --------------------------------------------------------

    question_col, palette_col = st.columns([4.5, 1.5])

    q_index = st.session_state.current_q
    q = QUESTIONS[q_index]

    with question_col:

        st.markdown(
            f"### Question {q_index + 1} of {TOTAL_QUESTIONS}"
        )

        st.progress(
            (q_index + 1) / TOTAL_QUESTIONS
        )

        st.markdown(
            f'<div class="question-card">'
            f'<b>Q{q_index + 1}.</b><br><br>'
            f'{q["q"]}'
            f'</div>',
            unsafe_allow_html=True
        )

        existing = st.session_state.answers.get(q_index)

        selected = st.radio(
            "Select your answer:",
            q["options"],
            index=existing if existing is not None else None,
            key=f"answer_{q_index}",
        )

        if selected is not None:
            st.session_state.answers[q_index] = (
                q["options"].index(selected)
            )

        st.write("")

        prev_col, next_col = st.columns(2)

        with prev_col:

            if q_index > 0:

                if st.button(
                    "⬅ PREVIOUS",
                    use_container_width=True
                ):

                    st.session_state.current_q -= 1
                    st.rerun()

        with next_col:

            if q_index < TOTAL_QUESTIONS - 1:

                if st.button(
                    "SAVE & NEXT ➜",
                    type="primary",
                    use_container_width=True
                ):

                    st.session_state.current_q += 1
                    st.rerun()

        st.write("")

        if st.button(
            "📤 SUBMIT TEST",
            type="primary",
            use_container_width=True
        ):

            st.session_state.show_submit_confirm = True
            st.rerun()

    # --------------------------------------------------------
    # QUESTION PALETTE
    # --------------------------------------------------------

    with palette_col:

        st.markdown(
            '<div class="palette-title">Question Palette</div>',
            unsafe_allow_html=True
        )

        st.caption("🟢 Green = Answered")
        st.caption("⚪ Grey = Not Answered")

        for start in range(0, TOTAL_QUESTIONS, 2):

            cols = st.columns(2)

            for j, col in enumerate(cols):

                idx = start + j

                if idx >= TOTAL_QUESTIONS:
                    continue

                with col:

                    if idx in st.session_state.answers:
                        label = f"🟢 {idx + 1}"
                    else:
                        label = f"⚪ {idx + 1}"

                    if st.button(
                        label,
                        key=f"palette_{idx}",
                        use_container_width=True
                    ):

                        st.session_state.current_q = idx
                        st.rerun()

        st.divider()

        answered = len(st.session_state.answers)
        unanswered = TOTAL_QUESTIONS - answered

        st.write(f"🟢 **Answered:** {answered}")
        st.write(f"⚪ **Not Answered:** {unanswered}")

    # --------------------------------------------------------
    # SUBMIT CONFIRMATION
    # --------------------------------------------------------

    if st.session_state.show_submit_confirm:

        st.warning(
            f"You have answered {len(st.session_state.answers)} "
            f"out of {TOTAL_QUESTIONS} questions."
        )

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "❌ CANCEL",
                use_container_width=True
            ):

                st.session_state.show_submit_confirm = False
                st.rerun()

        with c2:

            if st.button(
                "✅ CONFIRM SUBMISSION",
                type="primary",
                use_container_width=True
            ):

                st.session_state.show_submit_confirm = False
                submit_exam(timeout=False)
                st.rerun()


# ============================================================
# RESULT PAGE
# ============================================================

elif st.session_state.page == "result":

    st.markdown(
        '<div class="main-title">✅ Examination Submitted</div>',
        unsafe_allow_html=True
    )

    st.success(
        "Your responses have been recorded successfully."
    )

    if st.session_state.timeout:

        st.warning(
            "⏰ The examination was automatically submitted "
            "because the time expired."
        )

    st.markdown("---")

    st.subheader("Final Result")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Score",
            f"{st.session_state.score}/{TOTAL_QUESTIONS}"
        )

    with c2:

        st.metric(
            "Percentage",
            f"{st.session_state.score / TOTAL_QUESTIONS * 100:.0f}%"
        )

    with c3:

        st.metric(
            "Section",
            st.session_state.section
        )

    st.write(
        f"**Student:** {st.session_state.student_name}"
    )

    st.write(
        f"**SRN:** {st.session_state.srn}"
    )

    st.info(
        "The examination result has been stored. "
        "You may close this page."
    )


# ============================================================
# FACULTY / ADMIN RESULTS
# ============================================================

st.divider()

with st.expander("🔐 Faculty / Admin Results"):

    admin_password = st.text_input(
        "Admin Password",
        type="password"
    )

    if st.button(
        "View Results",
        use_container_width=True
    ):

        if admin_password != ADMIN_PASSWORD:

            st.error("Incorrect admin password.")

        else:

            try:

                results = get_results()

                if not results:

                    st.info(
                        "No examination submissions found."
                    )

                else:

                    import pandas as pd

                    df = pd.DataFrame(results)

                    st.success(
                        f"{len(df)} submission(s) found."
                    )

                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True
                    )

                    csv = df.to_csv(
                        index=False
                    ).encode("utf-8")

                    st.download_button(
                        "⬇️ Download Results CSV",
                        csv,
                        "memory_management_test_results.csv",
                        "text/csv",
                        use_container_width=True
                    )

            except Exception as e:

                st.error(
                    f"Unable to retrieve results: {e}"
                )
