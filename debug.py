import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session,g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from helpers import dormitories, dormitory_names, laundry_time_intervals
from datetime import date,timedelta,datetime


conn = sqlite3.connect("dormapp.db")
cursor = conn.cursor()



laundry_machines = cursor.execute("SELECT lm.machine_name as name, COUNT(*) as count FROM laundry_requests lr JOIN laundry_machines lm ON lr.machine_id = lm.id WHERE lr.date = ? AND lm.dorm = 'Dormitory 8' GROUP BY lm.id",(date.today(),)).fetchall()

conn.commit()
conn.close()

print(laundry_machines)