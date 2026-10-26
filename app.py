import sqlite3
from flask import Flask, render_template, request, jsonify, session

from database import init_db, get_db_connection


app = Flask(__name__)

app.secret_key = "devtrack_monasshir_2026_secret"

ADMIN_PASSWORD = "Anwari$355301"

init_db()


# =====================================
# TOPICS
# =====================================

LANGUAGE_TOPICS = {

    "C": [
        "Introduction",
        "Variables",
        "Data Types",
        "Operators",
        "Input Output",
        "If Else",
        "Switch Case",
        "Loops",
        "Functions",
        "Arrays",
        "Strings",
        "Pointers",
        "Structures",
        "File Handling"
    ],

    "C++": [
        "Basics",
        "Variables",
        "Functions",
        "Arrays",
        "Pointers",
        "Classes",
        "Objects",
        "Inheritance",
        "Polymorphism",
        "STL"
    ],

    "Python": [
        "Basics",
        "Variables",
        "Data Types",
        "Lists",
        "Tuples",
        "Dictionary",
        "Loops",
        "Functions",
        "OOP",
        "File Handling"
    ],

    "Java": [
        "Basics",
        "Variables",
        "Data Types",
        "Classes",
        "Objects",
        "Inheritance",
        "Polymorphism",
        "Exception Handling"
    ],

    "JavaScript": [
        "Variables",
        "Functions",
        "Arrays",
        "Objects",
        "DOM",
        "Events",
        "Promises",
        "Async Await"
    ],

    "DSA": [
        "Arrays",
        "Linked List",
        "Stack",
        "Queue",
        "Recursion",
        "Sorting",
        "Searching",
        "Hashing",
        "Trees",
        "Graphs",
        "Dynamic Programming"
    ]
}


def is_logged_in():
    return "user_id" in session


def login_required():
    if not is_logged_in():
        return False
    return True


# =====================================
# PAGES
# =====================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/contribution")
def contribution():
    if not login_required():
        return render_template("index.html")

    return render_template("contribution.html")


@app.route("/workspace")
def workspace():
    if not login_required():
        return render_template("index.html")

    return render_template("workspace.html")


@app.route("/ideas")
def ideas():
    if not login_required():
        return render_template("index.html")

    return render_template("ideas.html")


# =====================================
# LOGIN
# =====================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    password = data.get("password", "")

    if not name:
        return jsonify({
            "success": False,
            "message": "Please enter admin name"
        }), 400

    if password != ADMIN_PASSWORD:
        return jsonify({
            "success": False,
            "message": "Incorrect password"
        }), 401

    conn = get_db_connection()

    existing_user = conn.execute("""
        SELECT id, name
        FROM admin_users
        WHERE LOWER(name) = LOWER(?)
    """, (name,)).fetchone()

    if existing_user:

        user_id = existing_user["id"]
        saved_name = existing_user["name"]

    else:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO admin_users (name)
            VALUES (?)
        """, (name,))

        conn.commit()

        user_id = cursor.lastrowid
        saved_name = name

    conn.close()

    session.clear()

    session["user_id"] = user_id
    session["user_name"] = saved_name

    return jsonify({
        "success": True,
        "name": saved_name,
        "message": f"Welcome back, {saved_name}!"
    })


# =====================================
# USER
# =====================================

@app.route("/api/user")
def get_user():

    if not login_required():
        return jsonify({"logged_in": False}), 401

    return jsonify({
        "logged_in": True,
        "id": session["user_id"],
        "name": session["user_name"]
    })


# =====================================
# LOGOUT
# =====================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True
    })


# =====================================
# LANGUAGES
# =====================================

@app.route("/api/languages")
def get_languages():

    if not login_required():
        return jsonify({"error": "Login required"}), 401

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT
            languages.*,

            COUNT(DISTINCT saved_codes.id) AS saved_code_count,

            COALESCE(
                SUM(DISTINCT coding_sessions.elapsed_seconds),
                0
            ) AS total_seconds

        FROM languages

        LEFT JOIN saved_codes
            ON saved_codes.language_id = languages.id
            AND saved_codes.user_id = ?

        LEFT JOIN coding_sessions
            ON coding_sessions.language_id = languages.id
            AND coding_sessions.user_id = ?

        GROUP BY languages.id

        ORDER BY languages.name

    """, (
        session["user_id"],
        session["user_id"]
    )).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


@app.route("/api/languages", methods=["POST"])
def add_language():

    if not login_required():
        return jsonify({"success": False}), 401

    data = request.get_json() or {}

    name = data.get("name", "").strip()

    if not name:
        return jsonify({
            "success": False,
            "message": "Enter language name"
        })

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO languages (name, category)
            VALUES (?, ?)
        """, (
            name,
            "Custom Programming Language"
        ))

        conn.commit()

        message = "Language added"

    except sqlite3.IntegrityError:

        message = "Language already exists"

    conn.close()

    return jsonify({
        "success": True,
        "message": message
    })


# =====================================
# DASHBOARD
# =====================================

@app.route("/api/dashboard")
def dashboard():

    if not login_required():
        return jsonify({"error": "Login required"}), 401

    user_id = session["user_id"]

    conn = get_db_connection()

    active_days = conn.execute("""
        SELECT COUNT(DISTINCT DATE(created_at)) AS total
        FROM saved_codes
        WHERE user_id = ?
    """, (user_id,)).fetchone()["total"]

    total_seconds = conn.execute("""
        SELECT COALESCE(
            SUM(elapsed_seconds),
            0
        ) AS total
        FROM coding_sessions
        WHERE user_id = ?
    """, (user_id,)).fetchone()["total"]

    completed_topics = conn.execute("""
        SELECT COUNT(*) AS total
        FROM topic_progress
        WHERE user_id = ?
        AND completed = 1
    """, (user_id,)).fetchone()["total"]

    total_codes = conn.execute("""
        SELECT COUNT(*) AS total
        FROM saved_codes
        WHERE user_id = ?
    """, (user_id,)).fetchone()["total"]

    conn.close()

    return jsonify({
        "active_days": active_days,
        "total_seconds": total_seconds,
        "completed_topics": completed_topics,
        "total_codes": total_codes
    })


# =====================================
# CONTRIBUTIONS
# =====================================

@app.route("/api/contributions")
def contributions():

    if not login_required():
        return jsonify([])

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT
            DATE(created_at) AS day,
            COUNT(*) AS count
        FROM saved_codes
        WHERE user_id = ?
        GROUP BY DATE(created_at)
    """, (session["user_id"],)).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# =====================================
# TOPICS
# =====================================

@app.route("/api/topics/<int:language_id>")
def get_topics(language_id):

    if not login_required():
        return jsonify({"error": "Login required"}), 401

    conn = get_db_connection()

    language = conn.execute("""
        SELECT *
        FROM languages
        WHERE id = ?
    """, (language_id,)).fetchone()

    if not language:

        conn.close()

        return jsonify({
            "error": "Language not found"
        }), 404

    progress_rows = conn.execute("""
        SELECT topic, completed
        FROM topic_progress
        WHERE user_id = ?
        AND language_id = ?
    """, (
        session["user_id"],
        language_id
    )).fetchall()

    progress = {
        row["topic"]: row["completed"]
        for row in progress_rows
    }

    topics = LANGUAGE_TOPICS.get(
        language["name"],
        [
            "Basics",
            "Syntax",
            "Functions",
            "Practice",
            "Advanced"
        ]
    )

    result = []

    for topic in topics:

        result.append({
            "topic": topic,
            "completed": progress.get(topic, 0)
        })

    conn.close()

    return jsonify({
        "language": dict(language),
        "topics": result
    })


@app.route("/api/topics/update", methods=["POST"])
def update_topic():

    if not login_required():
        return jsonify({"success": False}), 401

    data = request.get_json() or {}

    language_id = data.get("language_id")
    topic = data.get("topic", "").strip()
    completed = 1 if data.get("completed") else 0

    if not language_id or not topic:
        return jsonify({
            "success": False,
            "message": "Invalid topic"
        })

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO topic_progress
        (
            user_id,
            language_id,
            topic,
            completed
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(user_id, language_id, topic)

        DO UPDATE SET
            completed = excluded.completed

    """, (
        session["user_id"],
        language_id,
        topic,
        completed
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True})


# =====================================
# SESSION
# =====================================

@app.route("/api/session/start", methods=["POST"])
def start_coding_session():

    if not login_required():
        return jsonify({"success": False}), 401

    data = request.get_json() or {}

    language_id = data.get("language_id")

    if not language_id:
        return jsonify({
            "success": False,
            "message": "Language required"
        })

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO coding_sessions
        (
            user_id,
            language_id,
            elapsed_seconds
        )
        VALUES (?, ?, 0)
    """, (
        session["user_id"],
        language_id
    ))

    conn.commit()

    session_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "success": True,
        "session_id": session_id
    })


@app.route("/api/session/update", methods=["POST"])
def update_coding_session():

    if not login_required():
        return jsonify({"success": False}), 401

    data = request.get_json() or {}

    session_id = data.get("session_id")
    elapsed_seconds = int(data.get("elapsed_seconds", 0))

    if not session_id:
        return jsonify({
            "success": False
        })

    conn = get_db_connection()

    conn.execute("""
        UPDATE coding_sessions

        SET
            elapsed_seconds = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE id = ?
        AND user_id = ?

    """, (
        elapsed_seconds,
        session_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


# =====================================
# SAVE CODE
# =====================================

@app.route("/api/code/save", methods=["POST"])
def save_code():

    if not login_required():
        return jsonify({
            "success": False
        }), 401

    data = request.get_json() or {}

    language_id = data.get("language_id")

    title = data.get(
        "title",
        "Untitled Code"
    ).strip()

    topic = data.get(
        "topic",
        ""
    ).strip()

    code = data.get(
        "code",
        ""
    )

    if not language_id:
        return jsonify({
            "success": False,
            "message": "Language required"
        })

    if not code.strip():
        return jsonify({
            "success": False,
            "message": "Code is empty"
        })

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO saved_codes
        (
            user_id,
            language_id,
            topic,
            title,
            code
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user_id"],
        language_id,
        topic,
        title,
        code
    ))

    conn.commit()

    code_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "success": True,
        "code_id": code_id,
        "message": "Code saved successfully"
    })


# =====================================
# GET SAVED CODES
# =====================================

@app.route("/api/code/list/<int:language_id>")
def get_code_list(language_id):

    if not login_required():
        return jsonify([])

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT
            id,
            title,
            topic,
            code,
            created_at
        FROM saved_codes

        WHERE user_id = ?
        AND language_id = ?

        ORDER BY id DESC

    """, (
        session["user_id"],
        language_id
    )).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


# =====================================
# GET ONE CODE
# =====================================

@app.route("/api/code/<int:code_id>")
def get_single_code(code_id):

    if not login_required():
        return jsonify({}), 401

    conn = get_db_connection()

    row = conn.execute("""
        SELECT *
        FROM saved_codes
        WHERE id = ?
        AND user_id = ?
    """, (
        code_id,
        session["user_id"]
    )).fetchone()

    conn.close()

    if not row:
        return jsonify({
            "success": False,
            "message": "Code not found"
        }), 404

    return jsonify(dict(row))


# =====================================
# DELETE CODE
# =====================================

@app.route("/api/code/<int:code_id>", methods=["DELETE"])
def delete_code(code_id):

    if not login_required():
        return jsonify({
            "success": False
        }), 401

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM saved_codes
        WHERE id = ?
        AND user_id = ?
    """, (
        code_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


# =====================================
# FLOW DIAGRAM
# =====================================

@app.route("/api/flow")
def get_flow():

    if not login_required():
        return jsonify([])

    conn = get_db_connection()

    rows = conn.execute("""
        SELECT *
        FROM flow_diagrams
        WHERE user_id = ?
        ORDER BY updated_at DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])


@app.route("/api/flow/save", methods=["POST"])
def save_flow():

    if not login_required():
        return jsonify({
            "success": False
        }), 401

    data = request.get_json() or {}

    title = data.get(
        "title",
        "My Flowchart"
    ).strip()

    diagram_data = data.get(
        "diagram_data",
        "[]"
    )

    if not title:
        title = "My Flowchart"

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO flow_diagrams
        (
            user_id,
            title,
            diagram_data,
            updated_at
        )
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)

        ON CONFLICT(user_id, title)

        DO UPDATE SET
            diagram_data = excluded.diagram_data,
            updated_at = CURRENT_TIMESTAMP

    """, (
        session["user_id"],
        title,
        diagram_data
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Flowchart saved"
    })


@app.route("/api/flow/<int:flow_id>", methods=["DELETE"])
def delete_flow(flow_id):

    if not login_required():
        return jsonify({
            "success": False
        }), 401

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM flow_diagrams
        WHERE id = ?
        AND user_id = ?
    """, (
        flow_id,
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


if __name__ == "__main__":
    app.run(debug=True)