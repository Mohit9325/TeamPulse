import hashlib
from datetime import datetime
import threading
from PySide6.QtCore import QObject, Signal

import firebase_admin
from firebase_admin import credentials, firestore

def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()

class DatabaseSignals(QObject):
    # Signals to broadcast updates safely to the main thread
    employeeStatusChanged = Signal(list)
    activityFeedChanged = Signal(list)

class DatabaseManager:
    def __init__(self):
        self.signals = DatabaseSignals()
        
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate("firebase_credentials.json")
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"Error initializing Firebase: {e}")
                
        # Initialize Firestore pointing to default database
        self.db = firestore.client()
        self.active_listeners = {}
        self.seed_initial_data()
        self._setup_listeners()

    def seed_initial_data(self):
        # Seed employees if they don't exist
        emp_ref = self.db.collection('employees')
        docs = emp_ref.limit(1).get()
        if not docs:
            # Add default users with integer document IDs as strings
            default_employees = [
                {"id": 1, "name": "Admin", "role": "manager", "password": hash_pw("admin123"), "status": "Offline", "current_task": "None", "acc_sec": 0, "completed_list": []},
                {"id": 2, "name": "Alex", "role": "employee", "password": hash_pw("emp123"), "status": "Offline", "current_task": "None", "acc_sec": 0, "completed_list": []},
                {"id": 3, "name": "Sarah", "role": "employee", "password": hash_pw("emp123"), "status": "Offline", "current_task": "None", "acc_sec": 0, "completed_list": []},
                {"id": 4, "name": "Michael", "role": "employee", "password": hash_pw("emp123"), "status": "Offline", "current_task": "None", "acc_sec": 0, "completed_list": []},
                {"id": 5, "name": "Jessica", "role": "employee", "password": hash_pw("emp123"), "status": "Offline", "current_task": "None", "acc_sec": 0, "completed_list": []}
            ]
            for emp in default_employees:
                emp_ref.document(str(emp['id'])).set(emp, merge=True)

    def _setup_listeners(self):
        # We start the listeners in a separate thread/callback provided by firebase_admin
        self.emp_watch = self.db.collection('employees').on_snapshot(self._on_employees_snapshot)
        self.activity_watch = self.db.collection('activity_feed').order_by('timestamp_raw', direction=firestore.Query.DESCENDING).limit(50).on_snapshot(self._on_activity_snapshot)

    def _on_employees_snapshot(self, col_snapshot, changes, read_time):
        emp_data = []
        for doc in col_snapshot:
            data = doc.to_dict()
            emp_data.append(data)
        
        # Emit to main thread
        self.signals.employeeStatusChanged.emit(emp_data)

    def _on_activity_snapshot(self, col_snapshot, changes, read_time):
        activity_data = []
        for doc in col_snapshot:
            data = doc.to_dict()
            activity_data.append(data)
        
        self.signals.activityFeedChanged.emit(activity_data)

    def authenticate_user(self, username, password):
        hashed = hash_pw(password)
        emp_ref = self.db.collection('employees')
        query = emp_ref.where(filter=firestore.FieldFilter('name', '==', username)).where(filter=firestore.FieldFilter('password', '==', hashed)).get()
        if query:
            doc = query[0]
            data = doc.to_dict()
            return (data.get('id'), data.get('role'), data.get('name'))
        return None

    def start_task(self, user_id, task_type, notes="Assigned from manager queue"):
        now = datetime.now().isoformat()
        task_data = {
            'user_id': user_id,
            'task_type': task_type,
            'notes': notes,
            'status': 'InProgress',
            'start_time': now,
            'accumulated_seconds': 0
        }
        _, doc_ref = self.db.collection('tasks').add(task_data)
        
        # Update user's live status
        self.db.collection('employees').document(str(user_id)).set({
            'status': 'Active',
            'current_task': task_type
        }, merge=True)
        
        return doc_ref.id

    def update_task_accumulated_time(self, task_id, seconds):
        if not task_id: return
        self.db.collection('tasks').document(task_id).set({
            'accumulated_seconds': seconds
        }, merge=True)

    def end_task(self, task_id, user_id, accumulated_seconds, notes="Completed"):
        if task_id:
            now = datetime.now().isoformat()
            self.db.collection('tasks').document(task_id).set({
                'status': 'Completed',
                'end_time': now,
                'accumulated_seconds': accumulated_seconds,
                'notes': notes
            }, merge=True)
            
        # Update user status
        emp_ref = self.db.collection('employees').document(str(user_id))
        emp_doc = emp_ref.get()
        if emp_doc.exists:
            data = emp_doc.to_dict()
            completed_list = data.get('completed_list', [])
            current_task = data.get('current_task', 'None')
            if current_task != 'None':
                completed_list.append(current_task)
            emp_ref.set({
                'status': 'Offline',
                'current_task': 'None',
                'acc_sec': 0,
                'completed_list': completed_list
            }, merge=True)

    def update_user_status(self, user_id, status, acc_sec=None):
        update_data = {'status': status}
        if acc_sec is not None:
            update_data['acc_sec'] = acc_sec
        self.db.collection('employees').document(str(user_id)).set(update_data, merge=True)

    def log_activity(self, message, timestamp):
        # We store raw timestamp for sorting
        now = datetime.now().isoformat()
        self.db.collection('activity_feed').add({
            'message': message,
            'timestamp': timestamp,
            'timestamp_raw': now
        })

    def get_user_tasks(self, user_id):
        docs_query = self.db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id)).stream()
        docs = [doc for doc in docs_query]
        docs.sort(key=lambda x: x.to_dict().get('start_time', ''), reverse=True)
        tasks = []
        for doc in docs:
            d = doc.to_dict()
            tasks.append((doc.id, d.get('task_type'), d.get('notes'), d.get('status'), d.get('start_time'), d.get('end_time'), d.get('accumulated_seconds')))
        return tasks

    def get_user_tasks_for_date(self, user_id, date_str):
        docs_query = self.db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id)).stream()
        docs = [doc for doc in docs_query if doc.to_dict().get('start_time', '').startswith(date_str)]
        docs.sort(key=lambda x: x.to_dict().get('start_time', ''), reverse=True)
        tasks = []
        for doc in docs:
            d = doc.to_dict()
            tasks.append((doc.id, d.get('task_type'), d.get('notes'), d.get('status'), d.get('start_time'), d.get('end_time'), d.get('accumulated_seconds')))
        return tasks

    def get_assigned_tasks(self, user_id):
        docs_query = self.db.collection('assigned_tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id)).stream()
        docs = [doc.to_dict() for doc in docs_query]
        if not docs:
            # Seed mock tasks
            mock_tasks = [
                {'user_id': user_id, 'title': 'Q3 Budget Review', 'description': 'Analyze departmental spending for Q3.', 'allocated_minutes': 45, 'status': 'pending'},
                {'user_id': user_id, 'title': 'Team Sync Presentation', 'description': 'Prepare slides for Friday sync.', 'allocated_minutes': 60, 'status': 'pending'}
            ]
            for mt in mock_tasks:
                self.db.collection('assigned_tasks').add(mt)
            return mock_tasks
        return docs

    def get_pending_assigned_tasks(self, emp_id):
        str_id = str(emp_id)
        try:
            int_id = int(emp_id)
            search_ids = [str_id, int_id]
        except (ValueError, TypeError):
            search_ids = [str_id]
            
        docs_query = self.db.collection('assigned_tasks').where(filter=firestore.FieldFilter('emp_id', 'in', search_ids)).where(filter=firestore.FieldFilter('status', '==', 'pending')).stream()
        tasks = []
        for doc in docs_query:
            d = doc.to_dict()
            d['id'] = doc.id
            tasks.append(d)
        return tasks

    def listen_to_assigned_tasks(self, emp_id, callback):
        # cancel any existing listener for this emp_id
        if str(emp_id) in self.active_listeners:
            self.active_listeners[str(emp_id)].unsubscribe()
        
        def snapshot_callback(col_snapshot, changes, read_time):
            tasks = []
            for doc in col_snapshot:
                data = doc.to_dict()
                data['id'] = doc.id
                tasks.append(data)
            callback(tasks)
            
        query = self.db.collection('assigned_tasks').where(filter=firestore.FieldFilter('emp_id', '==', str(emp_id))).where(filter=firestore.FieldFilter('status', '==', 'pending'))
        self.active_listeners[str(emp_id)] = query.on_snapshot(snapshot_callback)

    def get_recent_completed_tasks(self, user_id, limit=20):
        str_id = str(user_id)
        try:
            int_id = int(user_id)
            search_ids = [str_id, int_id]
        except (ValueError, TypeError):
            search_ids = [str_id]

        docs_query = self.db.collection('tasks').where(filter=firestore.FieldFilter('user_id', 'in', search_ids)).where(filter=firestore.FieldFilter('status', '==', 'Completed')).stream()
        docs = [doc.to_dict() for doc in docs_query]
        docs.sort(key=lambda x: x.get('end_time', ''), reverse=True)
        
        recent = docs[:limit]
        tasks = []
        for d in recent:
            end_val = d.get('end_time', '')
            date_part = end_val.split('T')[0] if 'T' in end_val else end_val.split(' ')[0]
            acc_sec = d.get('accumulated_seconds', 0)
            h, rem = divmod(acc_sec, 3600)
            m, s = divmod(rem, 60)
            duration_str = f"{int(h)}h {int(m)}m" if h > 0 else f"{int(m)}m {int(s)}s"
            
            tasks.append({
                'taskType': d.get('task_type', 'Task'),
                'title': d.get('task_type', 'Task'),
                'notes': d.get('notes', ''),
                'duration': duration_str,
                'date': date_part,
                'completion_time': date_part
            })
        return tasks

    def request_password_reset(self, emp_id):
        self.db.collection('employees').document(str(emp_id)).set({
            'reset_requested': True
        }, merge=True)

    def manager_reset_password(self, emp_id, new_password):
        hashed = hash_pw(new_password)
        self.db.collection('employees').document(str(emp_id)).set({
            'password': hashed,
            'reset_requested': False
        }, merge=True)
        self.log_activity(f"Manager reset password for Employee ID: {emp_id}", datetime.now().strftime("%I:%M %p"))

    def update_employee_password(self, emp_id, current_pw, new_pw):
        emp_ref = self.db.collection('employees').document(str(emp_id))
        doc = emp_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if data.get('password') == hash_pw(current_pw):
                emp_ref.set({
                    'password': hash_pw(new_pw)
                }, merge=True)
                return True
        return False

    def get_active_task_id(self, user_id):
        docs = self.db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id)).where(filter=firestore.FieldFilter('status', '==', 'InProgress')).get()
        if docs:
            return docs[0].id
        return None

    def create_employee(self, name, emp_id, password):
        hashed = hash_pw(password)
        emp_data = {
            "id": int(emp_id),
            "name": name,
            "role": "employee",
            "password": hashed,
            "status": "Offline",
            "current_task": "None",
            "acc_sec": 0,
            "completed_list": []
        }
        self.db.collection('employees').document(str(emp_id)).set(emp_data)
        self.log_activity(f"Manager created new employee: {name}", datetime.now().strftime("%I:%M %p"))

    def delete_employee(self, emp_id):
        # Find documents where the field 'id' equals the requested ID
        # (Check both string and integer versions to be safe)
        try:
            int_id = int(emp_id)
        except ValueError:
            int_id = emp_id
            
        # Use a list to catch both string and integer formats
        docs = self.db.collection('employees').where(filter=firestore.FieldFilter('id', 'in', [str(emp_id), int_id])).stream()

        deleted_count = 0
        for doc in docs:
            doc.reference.delete()
            deleted_count += 1

        if deleted_count > 0:
            self.log_activity(f"Manager deleted employee ID: {emp_id}", datetime.now().strftime("%I:%M %p"))

    def get_productivity_stats(self, emp_id):
        str_id = str(emp_id)
        try:
            int_id = int(emp_id)
            search_ids = [str_id, int_id]
        except (ValueError, TypeError):
            search_ids = [str_id]

        docs_query = self.db.collection('tasks').where(filter=firestore.FieldFilter('user_id', 'in', search_ids)).where(filter=firestore.FieldFilter('status', '==', 'Completed')).stream()
        tasks = [doc.to_dict() for doc in docs_query]
        
        total_completed = len(tasks)
        if total_completed == 0:
            return {
                "total_completed": "0",
                "avg_time": "0m",
                "adherence": "0%"
            }
            
        total_seconds = sum(t.get('accumulated_seconds', 0) for t in tasks)
        avg_seconds = total_seconds // total_completed
        avg_m, avg_s = divmod(avg_seconds, 60)
        avg_h, avg_m = divmod(avg_m, 60)
        
        if avg_h > 0:
            avg_time_str = f"{avg_h}h {avg_m}m"
        else:
            avg_time_str = f"{avg_m}m"
            
        adherent_count = 0
        for t in tasks:
            allocated = t.get('allocated_minutes', 0)
            acc_sec = t.get('accumulated_seconds', 0)
            if allocated <= 0 or acc_sec <= (allocated * 60):
                adherent_count += 1
                
        adherence_pct = int((adherent_count / total_completed) * 100)
        
        return {
            "total_completed": str(total_completed),
            "avg_time": avg_time_str,
            "adherence": f"{adherence_pct}%"
        }

    def request_task_extension(self, emp_id, extra_minutes, reason):
        emp_ref = self.db.collection('employees').document(str(emp_id)).get()
        emp_name = "Employee"
        current_task = "Task"
        if emp_ref.exists:
            d = emp_ref.to_dict()
            emp_name = d.get('name', 'Employee')
            current_task = d.get('current_task', 'Task')
            
        msg = f"⚠️ EXTENSION REQUEST: {emp_name} requested +{extra_minutes}m for '{current_task}' (Reason: {reason})"
        now = datetime.now().strftime("%I:%M %p")
        self.log_activity(msg, now)
