import sqlite3
DATABASE = "dormapp.db"
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
            user_id INTEGER NOT NULL,
            title TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES userss(id)
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
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS dormitories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
    );""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS laundry_machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dorm text,
    machine_name TEXT,
    status TEXT DEFAULT 'working'
    );""")
   
    cursor.execute("""CREATE TABLE IF NOT EXISTS laundry_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dorm_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    machine_id INTEGER NOT NULL,
    time_interval_id INTEGER NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES userss(id),
    FOREIGN KEY (dorm_id) REFERENCES dormitories(id),
    FOREIGN KEY (machine_id) REFERENCES laundry_machines(id),
    UNIQUE (dorm_id, machine_id, time_interval_id, date)
    );""")

    cursor.execute("""CREATE TRIGGER IF NOT EXISTS cleanup_old_rows
    AFTER INSERT ON laundry_requests
    BEGIN DELETE FROM laundry_requests
    WHERE date < DATE('now', '-30 day');
    END;""")

    db.commit()
    db.close()