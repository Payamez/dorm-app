import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session,g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from helpers import dormitories, dormitory_names, laundry_time_intervals
from sql import init_db
from datetime import date,timedelta
import json
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
@login_required
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
            cursor = db.execute( "SELECT problems.id as id, problems.title as title, problems.description as description, problems.status as status, problems.date_reported as date_reported,userss.email as email FROM problems JOIN userss ON userss.id = problems.user_id  WHERE dorm= ?",(session["dorm"],))
            rows = cursor.fetchall()
            return render_template("report.html",rows=rows)
@app.route("/change_status",methods=["POST"])
def change_status():
    problem_id = request.form.get("problem_id")
    if not problem_id:
        return apology("could not find the problem :(")
    db = get_db()
    cursor = db.execute(" UPDATE problems SET status = CASE  WHEN status = 'open' THEN 'closed'  ELSE 'open' END WHERE id = ?",(problem_id,))
    db.commit()
    return redirect("/report_problem")

@app.route("/lost_and_found", methods=["GET", "POST"])
@login_required
def lost_and_found():
    if request.method == "POST":
        item = request.form.get("item_description")

        if not item:
            return apology("must provide item description",400)
        db = get_db()
             #Execute query safely
        cursor = db.execute( "INSERT INTO lost_and_found (user_id,item_description) VALUES (?, ?)",
            (session["user_id"],item))
        db.commit()
        return redirect("/lost_and_found")

    else:
        db = get_db()
             #Execute query safely
        cursor = db.execute( "SELECT lost_and_found.id, lost_and_found.item_description, lost_and_found.status, lost_and_found.date_reported, lost_and_found.user_id, userss.email, userss.name FROM lost_and_found JOIN userss ON lost_and_found.user_id = userss.id WHERE lost_and_found.status = 'lost'")
        rows = cursor.fetchall()
        return render_template("lost_found.html",rows=rows)
@app.route("/mark_found", methods=["POST"])
def mark_found():
    item_id = request.form.get("item_id")
    db = get_db()
    db.execute(
        "UPDATE lost_and_found SET status='found' WHERE id=?",
        (item_id,)
    )
    db.commit()
    return redirect("/lost_and_found")    


@app.route("/announcements",methods=["GET", "POST"])
@login_required
def announcements():
    if request.method == "POST":
        title = request.form.get("title")
        message = request.form.get("message")
        if not title or not message:
            return apology("no title - message :(")
        
        db = get_db()
        db.execute(
        "INSERT INTO announcements (title,message,user_id) VALUES (?,?,?)",
        (title,message,session["user_id"])
        )
        db.commit()
        return redirect("/announcements")
    else:
        db = get_db()
             #Execute query safely
        cursor = db.execute( "SELECT userss.dorm_number as dorm, announcements.id AS announcement_id, announcements.title, announcements.message, announcements.created_at, userss.name AS posted_by " \
        "FROM announcements JOIN userss ON announcements.user_id = userss.id WHERE userss.dorm_number = ? ORDER BY announcements.id DESC;",(session["dorm"],))
        rows = cursor.fetchall()
        rows_dicts = [dict(row) for row in rows]
        for row in rows_dicts:
         words = row["message"].split()        
         if len(words) > 10:
            row["preview"] = " ".join(words[:10]) + "..."
         else:
            row["preview"] = row["message"]
        return render_template("announcements.html",rows=rows_dicts)
@app.route("/announcement/<int:announcement_id>")
def announcement(announcement_id):
    db = get_db()

    row = db.execute(
        "SELECT * FROM announcements WHERE id = ?", (announcement_id,)
    ).fetchone()

    if row is None:
        return apology("Announcement not found", 404)

    # Pass the row to the template
    return render_template("announcements_detail.html", row=row)
@app.route("/announcement_delete", methods=["POST"])
def announcement_delete():
    announcement_id = request.form.get("announcement_id")
    if not announcement_id:
        return apology("could not find the announcement id")
    db = get_db()
    db.execute(
        "DELETE FROM announcements WHERE  id=?",
        (announcement_id,)
    )
    db.commit()
    return redirect("/announcements") 

# BY FAR THE HARDEST PART OF PROJECT - LAUNDRY RESERVATION
@app.route("/laundry", defaults={"day": "today"}, methods=["GET", "POST"])
@app.route("/laundry/<day>", methods=["GET", "POST"])
@login_required
def laundry(day):
    if request.method == "POST":
        return redirect("/")
    else:
        if day == "today":
             date = date.today()
        elif day == "tomorrow":
           date = date.today() + timedelta(days=1)
        elif day == "day_after_tomorrow":
              date = date.today() + timedelta(days=2)
        db = get_db()
        laundry_machines = db.execute(
            "SELECT * FROM laundry_machines WHERE dorm = (?)",(session['dorm'],)
        ).fetchall()
        # I should have store dorm_id in session not name :( 
        dorm_row = db.execute(
         "SELECT id FROM dormitories WHERE name = ?",    (session['dorm'],)).fetchone()
        dorm_id = dorm_row["id"]
        # all this since seaarching id is better than text 
        requests = db.execute(
            "SELECT * FROM laundry_requests WHERE dorm_id = ? AND date = ?",(dorm_id,date)
        ).fetchall()
        availability_dict = [] #gonna send this to web and create table based on this
        for machine in laundry_machines:
             availability_dict[machine["id"]] = {}  # inner dict: time_interval -> 1
             for time in laundry_time_intervals:
                  availability_dict[machine["id"]][time] = 1
        if not requests:
            return render_template("laundry.html",day=day,availability_dict=availability_dict)


        #checking availabaility for each time interval for each machine in selected date and dorm
        
                
                
        return render_template("laundry.html",laundry_time_intervals = laundry_time_intervals,rows=laundry_machines)
@app.route("/add_machine", methods=["POST"])
def add_machine():
    machine_name = request.form.get("machine_name")
    if not machine_name:
        return apology("machine name can not be empty")
    db = get_db()
    db.execute(
        "INSERT INTO laundry_machines(dorm,machine_name) values (?,?)",
        (session['dorm'],machine_name)
    )
    db.commit()
    return redirect("/laundry")     
@app.route("/change_status_laundry",methods=["POST"])
def change_status_laundry():
    machine_id = request.form.get("machine_id")
    if not machine_id:
        return apology("could not find the machine :(")
    db = get_db()
    db.execute(" UPDATE laundry_machines SET status = CASE  WHEN status = 'working' THEN 'broken'  ELSE 'working' END WHERE id = ?",(machine_id,))
    db.commit()
    return redirect("/laundry")
if __name__ == "__main__":
    app.run(debug=True)
    
