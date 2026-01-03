from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os



app = Flask(__name__, static_folder="static", static_url_path="/static")

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    return psycopg2.connect("DATABASE_URL")

def init_db():
    """Create database and tables on first run using schema.sql."""
    if not os.path.exists(DB_NAME):
        with get_db() as conn, open("schema.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())


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
        query += " AND (title LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like])

    # Order: not done first, then priority, then due date, then newest
    query += " ORDER BY done ASC, priority ASC, due_date IS NULL, due_date ASC, created_at DESC"

    conn = get_db()
    tasks = conn.execute(query, params).fetchall()

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
        conn.execute(
            """
            INSERT INTO tasks (title, description, category, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, description, category, int(priority), due_date),
        )
        conn.commit()

    return redirect(url_for("index"))


@app.route("/toggle/<int:task_id>")
def toggle(task_id):
    """Toggle a task between done and not done."""
    conn = get_db()
    cur = conn.execute("SELECT done FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    if row is not None:
        new_status = 0 if row["done"] else 1
        conn.execute("UPDATE tasks SET done = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:task_id>")
def delete(task_id):
    """Delete a task."""
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
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
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, category = ?, priority = ?, due_date = ?
                WHERE id = ?
                """,
                (title, description, category, int(priority), due_date, task_id),
            )
            conn.commit()

        return redirect(url_for("index"))

    # GET: show edit form
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        return redirect(url_for("index"))

    return render_template("edit.html", task=task)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
