import sqlite3
import hashlib
import json
from datetime import datetime
from kivy.event import EventDispatcher

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

class DatabaseSignals(EventDispatcher):
    def __init__(self, **kwargs):
        self.register_event_type('on_employee_status_changed')
        self.register_event_type('on_activity_feed_changed')
        super().__init__(**kwargs)

    def on_employee_status_changed(self, *args): pass
    def on_activity_feed_changed(self, *args): pass

class DatabaseManager:
    def __init__(self, db_path='teampulse.db'):
        self.db_path = db_path
        self.signals = DatabaseSignals()
        self._init_db()
        self.seed_initial_data()
        self.active_listeners = {}

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    role TEXT,
                    password TEXT,
                    status TEXT,
                    current_task TEXT,
                    acc_sec INTEGER,
                    completed_list TEXT
                )
            ''')
            try:
                c.execute("ALTER TABLE employees ADD COLUMN username TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                c.execute("ALTER TABLE employees ADD COLUMN department TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                c.execute("ALTER TABLE employees ADD COLUMN allocated_minutes INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            
            # Default username mapping for older records
            c.execute("UPDATE employees SET username = name WHERE username IS NULL")
            c.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    task_type TEXT,
                    notes TEXT,
                    status TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    accumulated_seconds INTEGER,
                    allocated_minutes INTEGER DEFAULT 0
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS assigned_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emp_id INTEGER,
                    title TEXT,
                    description TEXT,
                    allocated_minutes INTEGER,
                    status TEXT,
                    created_at TEXT
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS activity_feed (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    timestamp TEXT,
                    timestamp_raw TEXT
                )
            ''')
            try:
                c.execute("ALTER TABLE assigned_tasks ADD COLUMN priority TEXT DEFAULT 'Medium'")
            except sqlite3.OperationalError:
                pass
            conn.commit()

    def seed_initial_data(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM employees")
            if c.fetchone()[0] == 0:
                default_employees = [
                    (1, "Admin", "manager", hash_pw("admin123"), "Offline", "None", 0, "[]"),
                    (2, "Alex", "employee", hash_pw("emp123"), "Offline", "None", 0, "[]"),
                    (3, "Sarah", "employee", hash_pw("emp123"), "Offline", "None", 0, "[]"),
                    (4, "Michael", "employee", hash_pw("emp123"), "Offline", "None", 0, "[]"),
                    (5, "Jessica", "employee", hash_pw("emp123"), "Offline", "None", 0, "[]")
                ]
                c.executemany("INSERT INTO employees VALUES (?,?,?,?,?,?,?,?)", default_employees)
                conn.commit()
                self._broadcast_employees()

    def _broadcast_employees(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM employees")
            rows = c.fetchall()
            
        emp_data = []
        for r in rows:
            d = dict(r)
            d['completed_list'] = json.loads(d['completed_list'])
            emp_data.append(d)
            
        self.signals.dispatch('on_employee_status_changed', emp_data)

    def _broadcast_activity(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM activity_feed ORDER BY timestamp_raw DESC LIMIT 50")
            rows = c.fetchall()
            
        activity_data = [dict(r) for r in rows]
        self.signals.dispatch('on_activity_feed_changed', activity_data)

    def authenticate_user(self, username, password):
        hashed = hash_pw(password)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT id, role, name FROM employees WHERE username=? AND password=?", (username, hashed))
            row = c.fetchone()
            if row:
                return (row['id'], row['role'], row['name'])
        return None

    def start_task(self, user_id, task_type, notes="Assigned from manager queue", allocated_minutes=0):
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO tasks (user_id, task_type, notes, status, start_time, accumulated_seconds, allocated_minutes)
                VALUES (?, ?, ?, 'InProgress', ?, 0, ?)
            """, (user_id, task_type, notes, now, allocated_minutes))
            task_id = c.lastrowid
            
            c.execute("UPDATE employees SET status='Active', current_task=?, allocated_minutes=? WHERE id=?", (task_type, allocated_minutes, user_id))
            
            # If it was assigned, mark assigned task as active or just let the caller handle it.
            # We'll just leave it.
            conn.commit()
            
        self._broadcast_employees()
        return task_id

    def update_task_accumulated_time(self, task_id, seconds):
        if not task_id: return
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE tasks SET accumulated_seconds=? WHERE id=?", (seconds, task_id))
            conn.commit()

    def end_task(self, task_id, user_id, accumulated_seconds, notes="Completed"):
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if task_id:
                c.execute("""
                    UPDATE tasks SET status='Completed', end_time=?, accumulated_seconds=?, notes=?
                    WHERE id=?
                """, (now, accumulated_seconds, notes, task_id))
            
            c.execute("SELECT current_task, completed_list FROM employees WHERE id=?", (user_id,))
            row = c.fetchone()
            if row:
                current_task = row[0]
                completed_list = json.loads(row[1])
                if current_task != 'None':
                    completed_list.append(current_task)
                
                c.execute("""
                    UPDATE employees SET status='Offline', current_task='None', acc_sec=0, completed_list=?, allocated_minutes=0
                    WHERE id=?
                """, (json.dumps(completed_list), user_id))
            conn.commit()
            
        self._broadcast_employees()

    def update_user_status(self, user_id, status, acc_sec=None):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if acc_sec is not None:
                c.execute("UPDATE employees SET status=?, acc_sec=? WHERE id=?", (status, acc_sec, user_id))
            else:
                c.execute("UPDATE employees SET status=? WHERE id=?", (status, user_id))
            conn.commit()
        self._broadcast_employees()

    def log_activity(self, message, timestamp):
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO activity_feed (message, timestamp, timestamp_raw) VALUES (?,?,?)", (message, timestamp, now))
            conn.commit()
        self._broadcast_activity()

    def get_user_tasks_for_date(self, user_id, date_str):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM tasks WHERE user_id=? AND start_time LIKE ? ORDER BY start_time DESC", (user_id, f"{date_str}%"))
            rows = c.fetchall()
            tasks = []
            for d in rows:
                tasks.append((d['id'], d['task_type'], d['notes'], d['status'], d['start_time'], d['end_time'], d['accumulated_seconds']))
            return tasks

    def assign_task(self, emp_id, title, description, allocated_minutes, priority="Medium"):
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO assigned_tasks (emp_id, title, description, allocated_minutes, status, created_at, priority)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
            """, (emp_id, title, description, allocated_minutes, now, priority))
            conn.commit()
        self.log_activity(f"Assigned task '{title}' [{priority}] to Employee ID {emp_id}", datetime.now().strftime("%I:%M %p"))

    def get_assigned_tasks(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM assigned_tasks WHERE emp_id=?", (user_id,))
            return [dict(r) for r in c.fetchall()]

    def get_all_assigned_tasks(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
                SELECT t.id, t.emp_id, t.title, t.description, t.allocated_minutes, t.status, t.created_at, e.name as emp_name
                FROM assigned_tasks t
                LEFT JOIN employees e ON t.emp_id = e.id
                ORDER BY t.created_at DESC
            """)
            return [dict(r) for r in c.fetchall()]

    def update_assigned_task(self, task_id, title, description, allocated_minutes, priority="Medium"):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE assigned_tasks
                SET title = ?, description = ?, allocated_minutes = ?, priority = ?
                WHERE id = ?
            """, (title, description, allocated_minutes, priority, task_id))
            conn.commit()
        self.log_activity(f"Updated task ID {task_id}: {title} (Priority: {priority})", datetime.now().strftime("%I:%M %p"))
        self._broadcast_employees()

    def delete_assigned_task(self, task_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM assigned_tasks WHERE id=?", (task_id,))
            conn.commit()
        self.log_activity(f"Manager deleted assigned task ID: {task_id}", datetime.now().strftime("%I:%M %p"))
        self._broadcast_employees()

    def get_pending_assigned_tasks(self, emp_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM assigned_tasks WHERE emp_id=? AND status='pending'", (emp_id,))
            return [dict(r) for r in c.fetchall()]

    def listen_to_assigned_tasks(self, emp_id, callback):
        # Local DB doesn't have live listeners, so we just call it once for now.
        # Real Kivy implementation can poll if needed.
        tasks = self.get_pending_assigned_tasks(emp_id)
        callback(tasks)

    def get_recent_completed_tasks(self, user_id, limit=20):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM tasks WHERE user_id=? AND status='Completed' ORDER BY end_time DESC LIMIT ?", (user_id, limit))
            rows = c.fetchall()
            
        tasks = []
        for d in rows:
            end_val = d['end_time'] or ''
            date_part = end_val.split('T')[0] if 'T' in end_val else end_val.split(' ')[0]
            acc_sec = d['accumulated_seconds'] or 0
            h, rem = divmod(acc_sec, 3600)
            m, s = divmod(rem, 60)
            duration_str = f"{int(h)}h {int(m)}m" if h > 0 else f"{int(m)}m {int(s)}s"
            
            tasks.append({
                'taskType': d['task_type'],
                'title': d['task_type'],
                'notes': d['notes'],
                'duration': duration_str,
                'date': date_part,
                'completion_time': date_part
            })
        return tasks

    def manager_reset_password(self, emp_id, new_password):
        hashed = hash_pw(new_password)
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE employees SET password=? WHERE id=?", (hashed, emp_id))
            conn.commit()
        self.log_activity(f"Manager reset password for Employee ID: {emp_id}", datetime.now().strftime("%I:%M %p"))

    def update_employee_password(self, emp_id, current_pw, new_pw):
        hashed_current = hash_pw(current_pw)
        hashed_new = hash_pw(new_pw)
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM employees WHERE id=? AND password=?", (emp_id, hashed_current))
            if c.fetchone():
                c.execute("UPDATE employees SET password=? WHERE id=?", (hashed_new, emp_id))
                conn.commit()
                return True
        return False

    def get_active_task_id(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM tasks WHERE user_id=? AND status='InProgress'", (user_id,))
            row = c.fetchone()
            if row: return row[0]
        return None

    def create_employee(self, name, username, password, department):
        hashed = hash_pw(password)
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO employees (name, username, department, role, password, status, current_task, acc_sec, completed_list)
                VALUES (?, ?, ?, 'employee', ?, 'Offline', 'None', 0, '[]')
            """, (name, username, department, hashed))
            conn.commit()
        self.log_activity(f"Manager created new employee: {name}", datetime.now().strftime("%I:%M %p"))
        self._broadcast_employees()

    def delete_employee(self, emp_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
            conn.commit()
        self.log_activity(f"Deleted Employee ID {emp_id}", datetime.now().strftime("%I:%M %p"))
        self._broadcast_employees()

    def get_productivity_stats(self, emp_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM tasks WHERE user_id=? AND status='Completed'", (emp_id,))
            tasks = c.fetchall()
            
        total_completed = len(tasks)
        if total_completed == 0:
            return {"total_completed": "0", "avg_time": "0m", "adherence": "0%"}
            
        total_seconds = sum(t['accumulated_seconds'] for t in tasks)
        avg_seconds = total_seconds // total_completed
        avg_m, avg_s = divmod(avg_seconds, 60)
        avg_h, avg_m = divmod(avg_m, 60)
        
        avg_time_str = f"{avg_h}h {avg_m}m" if avg_h > 0 else f"{avg_m}m"
            
        adherent_count = 0
        for t in tasks:
            allocated = t['allocated_minutes'] or 0
            acc_sec = t['accumulated_seconds'] or 0
            if allocated <= 0 or acc_sec <= (allocated * 60):
                adherent_count += 1
                
        adherence_pct = int((adherent_count / total_completed) * 100)
        
        return {
            "total_completed": str(total_completed),
            "avg_time": avg_time_str,
            "adherence": f"{adherence_pct}%"
        }

    def update_employee_password(self, username, new_password):
        hashed = hash_pw(new_password)
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE employees SET password=? WHERE username=?", (hashed, username))
            updated = c.rowcount > 0
            conn.commit()
        if updated:
            self.log_activity(f"Password reset for user '{username}'", datetime.now().strftime("%I:%M %p"))
        return updated

    def force_employee_status(self, emp_id, new_status):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            if new_status == 'Offline':
                c.execute("UPDATE employees SET status=?, current_task='None', acc_sec=0 WHERE id=?", (new_status, emp_id))
            else:
                c.execute("UPDATE employees SET status=? WHERE id=?", (new_status, emp_id))
            conn.commit()
        self.log_activity(f"Manager forced status of Employee ID {emp_id} to '{new_status}'", datetime.now().strftime("%I:%M %p"))
        self._broadcast_employees()

    def reassign_task(self, task_id, new_emp_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE assigned_tasks SET emp_id=? WHERE id=?", (new_emp_id, task_id))
            conn.commit()
        self.log_activity(f"Task ID {task_id} reassigned to Employee ID {new_emp_id}", datetime.now().strftime("%I:%M %p"))
        self._broadcast_employees()

    def export_logs_to_file(self, filepath):
        import csv
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, message, timestamp, timestamp_raw FROM activity_feed ORDER BY timestamp_raw DESC")
            rows = c.fetchall()
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Message", "Timestamp", "Raw Timestamp"])
                writer.writerows(rows)

    def get_all_employees(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, username, department, role FROM employees")
            return [{"id": r[0], "name": r[1], "username": r[2], "department": r[3], "role": r[4]} for r in c.fetchall()]

    def get_active_employees_count(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM employees WHERE status='Active'")
            return c.fetchone()[0]

    def get_on_break_employees_count(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM employees WHERE status IN ('On Break', 'Paused')")
            return c.fetchone()[0]

    def get_total_completed_tasks(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM assigned_tasks WHERE status='Completed'")
            return c.fetchone()[0]

    def force_complete_task(self, task_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE assigned_tasks SET status='Completed' WHERE id=?", (task_id,))
            conn.commit()
        self.log_activity(f"Task ID {task_id} manually forced to Completed by Manager", datetime.now().strftime("%I:%M %p"))
        self._broadcast_employees()

    def reset_employee_timer(self, emp_id):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE employees SET accumulated_seconds=0 WHERE id=?", (emp_id,))
            conn.commit()
        self.log_activity(f"Timer reset for Employee ID {emp_id}", datetime.now().strftime("%I:%M %p"))
        self._broadcast_employees()
