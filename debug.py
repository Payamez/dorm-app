import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session,g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from helpers import dormitories, dormitory_names, laundry_time_intervals
from sql import init_db


conn = sqlite3.connect("dormapp.db")
cursor = conn.cursor()



laundry_machines = cursor.execute(
            "SELECT * FROM laundry_machines WHERE dorm = 'Dormitory 8'").fetchall()

conn.commit()
conn.close()

print(laundry_machines)