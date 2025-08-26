import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session,g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from helpers import dormitories, dormitory_names


app = Flask(__name__)
DATABASE = "dormapp.db"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# --- Get DB connection per request ---
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  
    return g.db

# --- Close DB after request ---
@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# --- Initialize tables ---
def init_db():
    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS userss(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            dorm_number TEXT,
            room_number INTEGER,
            role TEXT,
            password_hashed TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute( """CREATE TABLE IF NOT EXISTS problems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    dorm TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    date_reported TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES userss(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS laundry_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    status TEXT DEFAULT 'booked',
    FOREIGN KEY (user_id) REFERENCES userss(id)
    )""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS lost_and_found (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT,
    user_id INTEGER NOT NULL,
    item_description TEXT NOT NULL,
    status TEXT DEFAULT 'lost',
    date_reported TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES userss(id)
    )""")

    db.commit()
    db.close()

# --- Run init once at startup ---
with app.app_context():
    init_db()


#-- homapge ---
@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/login")


#--this was gpt idea to help visualise database --
@app.route("/inspect")
def inspect_db():
    conn = sqlite3.connect("dormapp.db")
    cursor = conn.cursor()

    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    db_info = []
    for table_tuple in tables:
        table_name = table_tuple[0]
        
        # Get table columns
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Get sample rows
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
        rows = cursor.fetchall()
        
        db_info.append({
            "table": table_name,
            "columns": columns,
            "rows": rows
        })

    conn.close()
    return render_template("inspect.html", db_info=db_info)


@app.route('/login', methods=["POST","GET"])
def login():
 
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("mail"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        db = get_db()
        # Execute query safely
        cursor = db.execute("SELECT * FROM userss WHERE email = ? ",(request.form.get("mail"),))
        rows = cursor.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hashed"], request.form.get("password")
        ):
            return apology("invalid mail and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["name"] = rows[0]["name"]
        session["role"] = rows[0]["role"]
        session["dorm"] = rows[0]["dorm_number"]
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
    


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        mail = request.form.get("mail")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        name = request.form.get("name")
        role = request.form.get("role")
        dorm = request.form.get("dorm")
        room_number = request.form.get("room_number")
        if not mail or not password or not confirmation or not name or not role or not dorm:             
            return apology("Empty places still, fill them up", 400)
        if password != confirmation:
            return apology("password and confirmation should match", 400)
        if dorm not in dormitory_names: 
            return apology("not valid dorm",400)
        hashedPassword = generate_password_hash(password)
        try:
            db = get_db()
            # Execute query safely
            cursor = db.execute( "INSERT INTO userss (name,email,dorm_number,room_number,role,password_hashed) VALUES (?, ?, ?, ?, ?, ?)",
            (name, mail, dorm, room_number, role, hashedPassword))
            db.commit()
        except (ValueError,sqlite3.IntegrityError):
            return apology("username already exists", 400)
        return redirect("/login")
    else:    
        return render_template("register.html",dormitories=dormitories)


@app.route("/report_problem", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        if session["role"] == "Student":
            description = request.form.get("description")
            title = request.form.get("title") 
            if not description or not title:
                return apology("Fill in all fields", 400)
            db = get_db()
             #Execute query safely
            cursor = db.execute( "INSERT INTO problems (user_id,dorm,title,description) VALUES (?, ?, ?,?)",
            (session["user_id"],session["dorm"], title,description,))
            db.commit()
            return redirect("/")
        elif session["role"] == "Officer":
            print("a")
    else:    
            db = get_db()
             #Execute query safely
            cursor = db.execute( "SELECT * FROM problems WHERE dorm= ?",(session["dorm"],))
            rows = cursor.fetchall()
            return render_template("report.html",rows=rows)



if __name__ == "__main__":
    app.run(debug=True)
    
