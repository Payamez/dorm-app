import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session,g
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash


conn = sqlite3.connect("dormapp.db")
cursor = conn.cursor()

# Drop tables completely



conn.commit()
conn.close()