
#  My Main Python Project code 
# Learning Python

from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime
# Create a new Flask application
# creates your Flask application object.
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "expenses.db")


def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------- Create database ----------



# ---------- Show all expenses ----------
@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses ORDER BY id asc")
    expenses = cur.fetchall()
    total = sum([row[3] for row in expenses])
    conn.close()
    return render_template("index.html", expenses=expenses, total=total, title="All Expenses")
# I want to display the index.html file.

# ---------- Add Expense ----------
@app.route('/add', methods=['POST'])
def add():
    description = request.form.get('description')
    category = request.form.get('category')
    amount = request.form.get('amount')
    date = request.form.get('date') or datetime.now().strftime("%Y-%m-%d")

    if description and category and amount:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute("INSERT INTO expenses (description, category, amount, date) VALUES (?, ?, ?, ?)",
                    (description, category, float(amount), date))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))


# ---------- Delete Expense ----------
@app.route('/delete/<int:expense_id>')
def delete(expense_id):
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# ---------- Filter by Day, Month, Year, Quarter, Custom Range ----------
@app.route('/filter', methods=['GET', 'POST'])
def filter_expenses():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    filter_type = request.args.get('type')
    title = ""

    # Predefined filters (day/month/year/quarter)
    if filter_type == "day":
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute("SELECT * FROM expenses WHERE date = ?", (today,))
        title = f"Expenses for Today ({today})"

    elif filter_type == "month":
        month = datetime.now().strftime("%Y-%m")
        cur.execute("SELECT * FROM expenses WHERE strftime('%Y-%m', date) = ?", (month,))
        title = f"Expenses for This Month ({month})"

    elif filter_type == "year":
        year = datetime.now().strftime("%Y")
        cur.execute("SELECT * FROM expenses WHERE strftime('%Y', date) = ?", (year,))
        title = f"Expenses for This Year ({year})"

    elif filter_type == "quarter":
        month = datetime.now().month
        year = datetime.now().strftime("%Y")
        if month in [1, 2, 3]:
            start, end = 1, 3
            q = "Q1"
        elif month in [4, 5, 6]:
            start, end = 4, 6
            q = "Q2"
        elif month in [7, 8, 9]:
            start, end = 7, 9
            q = "Q3"
        else:
            start, end = 10, 12
            q = "Q4"
        cur.execute("""SELECT * FROM expenses 
                       WHERE strftime('%Y', date)=? 
                       AND CAST(strftime('%m', date) AS INTEGER) BETWEEN ? AND ?""",
                    (year, start, end))
        title = f"Expenses for {q} {year}"

    # Custom date range filter (POST form)
    elif request.method == "POST":
        from_date = request.form.get("from_date")
        to_date = request.form.get("to_date")

        if from_date and to_date:
            cur.execute("SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date DESC", 
                        (from_date, to_date))
            title = f"Expenses from {from_date} to {to_date}"
        else:
            cur.execute("SELECT * FROM expenses ORDER BY date DESC")
            title = "All Expenses"

    else:
        cur.execute("SELECT * FROM expenses ORDER BY id asc")
        title = "All Expenses"

    expenses = cur.fetchall()
    total = sum([row[3] for row in expenses])
    conn.close()

    return render_template("index.html", expenses=expenses, total=total, title=title)


# ---------- Chart Data ----------
@app.route('/chart-data')
def chart_data():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    category_data = cur.fetchall()
    conn.close()

    labels = [row[0] for row in category_data]
    values = [row[1] for row in category_data]
    return jsonify({"labels": labels, "values": values})


# ---------- Run App ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

