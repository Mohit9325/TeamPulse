import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Slot, Property

class DatabaseManager:
    def __init__(self, db_name="teampulse_v2.db"):
        self.db_path = Path(__file__).parent / db_name
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._initialize_tables()

    def _initialize_tables(self):
        # Users Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT CHECK(role IN ('manager', 'employee')) NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Shifts Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                clock_in_time TEXT,
                clock_out_time TEXT,
                status TEXT CHECK(status IN ('active', 'completed')) DEFAULT 'active',
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tasks Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                status TEXT CHECK(status IN ('pending', 'completed')) DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Location Logs Table (Audit & History)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                shift_id INTEGER,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (shift_id) REFERENCES shifts (id)
            )
        ''')

        # Seed initial admin if missing
        self.cursor.execute('SELECT COUNT(*) FROM users')
        if self.cursor.fetchone()[0] == 0:
            self.create_user("admin", "admin123", "manager")
            self.create_user("employee1", "emp123", "employee")

        self.conn.commit()

    def create_user(self, username, password, role):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            (username, hashed, role)
        )
        self.conn.commit()

    def execute_read(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def execute_write(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor.lastrowid

class AuthController(QObject):
    loginSuccess = Signal(str, int) # role, user_id
    loginFailed = Signal(str)
    logoutSuccess = Signal()

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.current_user_id = None
        self.current_role = None

    @Slot(str, str)
    def login(self, username, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        res = self.db.execute_read(
            'SELECT id, role FROM users WHERE username = ? AND password_hash = ?',
            (username, hashed)
        )
        if res:
            self.current_user_id = res[0][0]
            self.current_role = res[0][1]
            self.loginSuccess.emit(self.current_role, self.current_user_id)
        else:
            self.loginFailed.emit("Invalid credentials")

    @Slot()
    def logout(self):
        self.current_user_id = None
        self.current_role = None
        self.logoutSuccess.emit()

class TrackingController(QObject):
    def __init__(self, db_manager, auth_controller):
        super().__init__()
        self.db = db_manager
        self.auth = auth_controller

    @Slot(result=int)
    def clockIn(self):
        if not self.auth.current_user_id: return -1
        now = datetime.now().isoformat()
        shift_id = self.db.execute_write(
            'INSERT INTO shifts (user_id, clock_in_time) VALUES (?, ?)',
            (self.auth.current_user_id, now)
        )
        return shift_id

    @Slot(int)
    def clockOut(self, shift_id):
        now = datetime.now().isoformat()
        self.db.execute_write(
            "UPDATE shifts SET clock_out_time = ?, status = 'completed' WHERE id = ?",
            (now, shift_id)
        )

    @Slot(int, float, float)
    def logLocation(self, shift_id, latitude, longitude):
        if not self.auth.current_user_id: return
        now = datetime.now().isoformat()
        self.db.execute_write(
            'INSERT INTO location_logs (user_id, shift_id, latitude, longitude, timestamp) VALUES (?, ?, ?, ?, ?)',
            (self.auth.current_user_id, shift_id, latitude, longitude, now)
        )

    @Slot(result='QVariantList')
    def getLiveLocations(self):
        # Get the latest location for active shifts
        query = '''
            SELECT u.username, l.latitude, l.longitude, l.timestamp
            FROM location_logs l
            JOIN shifts s ON l.shift_id = s.id
            JOIN users u ON l.user_id = u.id
            WHERE s.status = 'active'
            AND l.timestamp = (
                SELECT MAX(timestamp) 
                FROM location_logs 
                WHERE shift_id = s.id
            )
        '''
        results = self.db.execute_read(query)
        data = []
        for row in results:
            data.append({
                "username": row[0],
                "latitude": row[1],
                "longitude": row[2],
                "last_seen": row[3]
            })
        return data

class AnalyticsController(QObject):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

    @Slot(result='QVariantList')
    def getWeeklyShiftHours(self):
        query = '''
            SELECT u.username, s.clock_in_time, s.clock_out_time
            FROM shifts s
            JOIN users u ON s.user_id = u.id
            WHERE s.status = 'completed'
        '''
        results = self.db.execute_read(query)
        hours_map = {}
        for row in results:
            user = row[0]
            start = datetime.fromisoformat(row[1])
            end = datetime.fromisoformat(row[2])
            duration = (end - start).total_seconds() / 3600.0
            
            # Very basic weekly filter: within last 7 days
            if (datetime.now() - start).days <= 7:
                hours_map[user] = hours_map.get(user, 0.0) + duration
                
        data = [{"username": k, "hours": round(v, 2)} for k, v in hours_map.items()]
        return data

    @Slot(result='QVariantList')
    def getTaskCompletionRates(self):
        query = '''
            SELECT u.username, 
                   COUNT(t.id) as total, 
                   SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM tasks t
            JOIN users u ON t.user_id = u.id
            GROUP BY u.id
        '''
        results = self.db.execute_read(query)
        data = []
        for row in results:
            total = row[1]
            completed = row[2]
            rate = (completed / total * 100) if total > 0 else 0
            data.append({
                "username": row[0],
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": round(rate, 1)
            })
        return data

if __name__ == '__main__':
    # Test suite
    import time
    print("Initializing Database...")
    db = DatabaseManager("teampulse_v2_test.db")
    auth = AuthController(db)
    tracker = TrackingController(db, auth)
    analytics = AnalyticsController(db)
    
    print("Testing Authentication...")
    auth.login("employee1", "emp123")
    assert auth.current_user_id is not None
    print("Employee logged in.")
    
    print("Testing Tracking (Clock In)...")
    shift_id = tracker.clockIn()
    print(f"Shift started: {shift_id}")
    
    print("Simulating Location Updates...")
    tracker.logLocation(shift_id, 37.7749, -122.4194)
    time.sleep(1)
    tracker.logLocation(shift_id, 37.7750, -122.4190)
    
    locations = tracker.getLiveLocations()
    print(f"Live Locations: {locations}")
    
    print("Testing Tracking (Clock Out)...")
    tracker.clockOut(shift_id)
    
    print("Simulating Tasks...")
    db.execute_write('INSERT INTO tasks (user_id, title, status) VALUES (?, ?, ?)', (auth.current_user_id, "Design API", "completed"))
    db.execute_write('INSERT INTO tasks (user_id, title, status) VALUES (?, ?, ?)', (auth.current_user_id, "Write QML", "pending"))
    
    print("Testing Analytics...")
    hours = analytics.getWeeklyShiftHours()
    rates = analytics.getTaskCompletionRates()
    print(f"Weekly Hours: {hours}")
    print(f"Task Rates: {rates}")
    
    print("Backend architecture validation successful!")
