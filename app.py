import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session,g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, is_it_passed
from helpers import dormitories, dormitory_names, laundry_time_intervals
from sql import init_db
from datetime import date,timedelta,datetime
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
    if session["role"] == "Officer":
        db = get_db()
        report_info = db.execute( "SELECT SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_reports FROM problems WHERE dorm = ?",(session["dorm"],)).fetchall()
        users_info = db.execute( "SELECT COUNT(*) as total_users FROM userss WHERE dorm_number = ?",(session["dorm"],)).fetchall()
        user_info = db.execute( "SELECT * FROM userss WHERE id = ?",(session["user_id"],)).fetchone()
        laundry_requests = db.execute("SELECT COUNT(*) as total_requests FROM laundry_requests WHERE date = ?",(date.today(),)).fetchone()
        laundry_requests_grouped = db.execute("SELECT lm.machine_name,  COUNT(*) as count FROM laundry_requests lr JOIN laundry_machines lm ON lr.machine_id = lm.id WHERE lr.date BETWEEN (?) and (?) AND lm.dorm = ? GROUP BY lm.id",(date.today(),date.today() + timedelta(days=7),session["dorm"],)).fetchall()
        laundry_machines = db.execute("SELECT  COUNT(*) as total_machine, SUM(CASE WHEN status = 'working' THEN 1 ELSE 0 END) as working_machines FROM laundry_machines WHERE dorm = ?",(session["dorm"],)).fetchall()
        return render_template("index.html",report_info=report_info,users_info=users_info,user_info=user_info,laundry_requests=laundry_requests,laundry_requests_grouped=laundry_requests_grouped,laundry_machines=laundry_machines) 
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
    else:    
            db = get_db()
             #Execute query safely
            cursor = db.execute( "SELECT problems.id as id, problems.title as title, problems.description as description, problems.status as status, problems.date_reported as date_reported,userss.email as email FROM problems JOIN userss ON userss.id = problems.user_id  WHERE dorm= ? ORDER BY problems.date_reported DESC  ",(session["dorm"],))
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
        db = get_db()
        if day == "today":
            selected_date = date.today()
        elif day == "tomorrow":
            selected_date = date.today() + timedelta(days=1)
        elif day == "after_tomorrow":
            selected_date = date.today() + timedelta(days=2)
        machine_id = request.form.get("machine_id")
        machine_status = db.execute("SELECT status from laundry_machines WHERE id = (?)",(machine_id,)).fetchone()
        if not machine_status or machine_status["status"] == "broken":
            return apology("somehow you have booked from a broken machine, if you are not a hacker, please contact us regard the topic")

        time_id = request.form.get("time_id")
        other_reservations = db.execute("SELECT * from laundry_requests WHERE user_id = (?) and date BETWEEN (?) and (?)",
                                        (session['user_id'],date.today(),date.today() + timedelta(days=2))).fetchall()
        if len(other_reservations) > 3:
            return apology("you can only reserve 3 times in 3 days :(")
        try:
            dorm_row = db.execute(
            "SELECT id FROM dormitories WHERE name = ?",(session['dorm'],)).fetchone()
            dorm_id = dorm_row["id"]
            db.execute("INSERT INTO laundry_requests (dorm_id,user_id,machine_id,time_interval_id,date) VALUES (?,?,?,?,?)",(dorm_id,session['user_id'],machine_id,time_id,selected_date)
            )
            db.commit()
        except sqlite3.IntegrityError:
            return apology("it is alreaday reserved :(")
        return redirect("/laundry")
    else:
        #building info for card-grid 
        if day == "today":
             selected_date = date.today()
        elif day == "tomorrow":
           selected_date = date.today() + timedelta(days=1)
        elif day == "after_tomorrow":
              selected_date = date.today() + timedelta(days=2)
        db = get_db()
        laundry_machines = db.execute(
            "SELECT * FROM laundry_machines WHERE dorm = (?)",(session['dorm'],)
        ).fetchall()
        # I should have store dorm_id in session not name :( 
        dorm_row = db.execute(
         "SELECT id FROM dormitories WHERE name = ?",(session['dorm'],)).fetchone()
        dorm_id = dorm_row["id"]
        # all this since seaarching id is better than text 
        requests = db.execute(
            "SELECT * FROM laundry_requests WHERE dorm_id = ? AND date = ?",(dorm_id,selected_date)
        ).fetchall()
        availability_dict = {} #gonna send this to web and create table based on this
        for machine in laundry_machines:
             availability_dict[machine["id"]] = {}  
             for time in laundry_time_intervals:
                starting_time = int(laundry_time_intervals[time][0:2])
                if is_it_passed(date.today(),starting_time):
                    availability_dict[machine["id"]][time] = 2 #passed :(
                else:
                    availability_dict[machine["id"]][time] = 1 #spot is free

        for r in requests:
            if r["machine_id"] in availability_dict: 
                availability_dict[r["machine_id"]][r["time_interval_id"]] = 0 #available
        
        # building users all past/current reservation table
        user_requests = db.execute(
            "SELECT r.id, r.date, r.time_interval_id, r.machine_id, m.machine_name,m.status FROM laundry_requests r JOIN laundry_machines m ON r.machine_id = m.id WHERE r.user_id = ? ORDER BY r.date DESC , r.time_interval_id DESC",(session["user_id"],)
        ).fetchall()
        return render_template("laundry.html",user_requests = user_requests, intervals = laundry_time_intervals,machines=laundry_machines,availability=availability_dict,is_it_passed=is_it_passed)

@app.route("/cancel_reservation", methods=["POST"])
def cancel_reservation():
    request_id = request.form.get("request_id")
    if not request_id:
        return apology("error , try again")
    db = get_db()
    cursor = db.execute("DELETE FROM laundry_requests where id = ?",(request_id,))
    db.commit()
    if cursor.rowcount == 0:
        apology("could not delete the reservation.")
    return redirect("/laundry")


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
    
