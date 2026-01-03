from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__, static_folder="static", static_url_path="/static")

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")
    conn = psycopg2.connect(DATABASE_URL)
    return conn


@app.route("/")
def index():
    """
    Home page: show tasks with optional filter and search.
    Filters: active / done / all
    Search: q in title, description, or category
    """
    filter_status = request.args.get("filter", "active")
    search = request.args.get("q", "").strip()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if filter_status == "active":
        query += " AND done = 0"
    elif filter_status == "done":
        query += " AND done = 1"

    if search:
        query += " AND (title ILIKE %s OR description ILIKE %s OR category ILIKE %s)"
        like = f"%{search}%"
        params.extend([like, like, like])

    # Order: not done first, then priority, then due date, then newest
    query += (
        " ORDER BY done ASC, priority ASC, (due_date IS NULL) ASC,"
        " due_date ASC, created_at DESC"
    )

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(query, params)
    tasks = cur.fetchall()
    cur.close()
    conn.close()

    return render_template(
        "index.html",
        tasks=tasks,
        filter_status=filter_status,
        search=search,
    )


@app.route("/add", methods=["POST"])
def add():
    """Add a new task."""
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "").strip()
    priority = request.form.get("priority", "2")
    due_date = request.form.get("due_date") or None  # empty string -> None

    if title:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tasks (title, description, category, priority, due_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (title, description, category, int(priority), due_date),
        )
        conn.commit()
        cur.close()
        conn.close()

    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    """Toggle a task between done and not done."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT done FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()

    if row is not None:
        new_status = 0 if row["done"] else 1
        cur.execute("UPDATE tasks SET done = %s WHERE id = %s", (new_status, task_id))
        conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    """Delete a task."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("index"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id):
    """Edit an existing task."""
    conn = get_db()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        priority = request.form.get("priority", "2")
        due_date = request.form.get("due_date") or None

        if title:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE tasks
                SET title = %s, description = %s, category = %s,
                    priority = %s, due_date = %s
                WHERE id = %s
                """,
                (title, description, category, int(priority), due_date, task_id),
            )
            conn.commit()
            cur.close()
            conn.close()
        else:
            conn.close()

        return redirect(url_for("index"))

    # GET: show edit form
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cur.fetchone()
    cur.close()
    conn.close()

    if task is None:
        return redirect(url_for("index"))

    return render_template("edit.html", task=task)


if __name__ == "__main__":
    app.run(debug=True)
