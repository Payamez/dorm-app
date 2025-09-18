import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session,g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from helpers import dormitories, dormitory_names, laundry_time_intervals
from sql import init_db
from datetime import date,timedelta,datetime

conn = sqlite3.connect("dormapp.db")
cursor = conn.cursor()




conn.commit()
conn.close()

now = datetime.now()
current_hour = now.hour
print(current_hour)