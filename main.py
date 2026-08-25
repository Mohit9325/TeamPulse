import os
import sys

from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QObject, Slot, Signal, Property, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine

from database_manager import DatabaseManager
from models import EmployeeStatusModel, ActivityFeedModel, TaskHistoryModel, AssignedTasksModel

class TeamPulseEngine(QObject):
    # Signals to broadcast state changes asynchronously to the main thread
    activityLogged = Signal(str, str) # eventText, timestamp
    employeeStatusChanged = Signal(int, str, str, list) # emp_id, task, status, completed_list
    employeeTimerUpdated = Signal(int, str) # emp_id, timer_text
    metricsUpdated = Signal(int, int, int) # active, paused, completed
    currentTimeChanged = Signal()
    employeesSynced = Signal(list)
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        # Initialize empty state
        self.employees = {}
        self.completed_today = 0
        self._current_time_str = datetime.now().strftime("%I:%M %p")
        
        # Connect Firestore background signals to main thread slots
        self.db.signals.employeeStatusChanged.connect(self._on_firestore_users_updated)
        self.db.signals.activityFeedChanged.connect(self._on_firestore_activity_updated)
        
        # 1-second UI Heartbeat Timer
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(1000)
        self.ui_timer.timeout.connect(self._on_ui_tick)
        self.ui_timer.start()

    @Property(str, notify=currentTimeChanged)
    def currentTime(self):
        return self._current_time_str

    @Slot()
    def _on_ui_tick(self):
        new_time = datetime.now().strftime("%I:%M %p")
        if new_time != self._current_time_str:
            self._current_time_str = new_time
            self.currentTimeChanged.emit()
            
        # Update elapsed time for active employees
        for emp_id, emp_data in self.employees.items():
            if emp_data["status"] == "Active":
                emp_data["acc_sec"] += 1
                self.employeeTimerUpdated.emit(emp_id, self._format_time(emp_data["acc_sec"]))

    @Slot()
    def initialize_heavy_data(self):
        """No more mock data or polling timers needed; Firestore streams the initial state."""
        print("Engine: Ready to receive Firestore data streams.")

    @Slot(list)
    def _on_firestore_users_updated(self, users_data):
        """Runs safely on the main thread when Firestore pushes a user update"""
        self.employees.clear()
        
        sync_list = []
        for user in users_data:
            try:
                emp_id = int(user.get('id', 0))
            except ValueError:
                continue
                
            firestore_acc = user.get('acc_sec', 0)
            existing_acc = self.employees.get(emp_id, {}).get('acc_sec', 0)
            current_task = user.get('current_task', 'None')
            existing_task = self.employees.get(emp_id, {}).get('task', 'None')
            
            # Preserve locally accumulated seconds if same task is running or paused
            if current_task == existing_task and current_task != 'None':
                acc_sec = max(firestore_acc, existing_acc)
            else:
                acc_sec = firestore_acc

            self.employees[emp_id] = {
                "name": user.get('name'),
                "status": user.get('status', 'Offline'),
                "task": current_task,
                "acc_sec": acc_sec,
                "completed_list": user.get('completed_list', []),
                "role": user.get('role', 'employee')
            }
            
            if user.get("role") != "manager":
                sync_list.append({
                    "id": emp_id,
                    "name": user.get('name', 'Unknown'),
                    "currentTask": current_task,
                    "status": user.get('status', 'Offline'),
                    "timer": self._format_time(acc_sec),
                    "completed_list": user.get('completed_list', [])
                })
            
            # Broadcast to local models
            self.employeeStatusChanged.emit(emp_id, self.employees[emp_id]["task"], self.employees[emp_id]["status"], self.employees[emp_id]["completed_list"])
            self.employeeTimerUpdated.emit(emp_id, self._format_time(self.employees[emp_id]["acc_sec"]))
            
        self.employeesSynced.emit(sync_list)
        self._recalculate_metrics()

    @Slot(list)
    def _on_firestore_activity_updated(self, activity_data):
        """Runs safely on the main thread when Firestore pushes a new activity log"""
        # (Optional) You can clear the feed model and rebuild, or just process new ones.
        pass # In this design, we will just rely on the existing direct connection or use this if needed

    def _recalculate_metrics(self):
        emp_list = [e for e in self.employees.values() if e.get("role") != "manager"]
        active = sum(1 for e in emp_list if e.get("status") in ["Active", "in_progress", "In Progress"])
        paused = sum(1 for e in emp_list if e.get("status") in ["Paused", "on_break", "On Break", "Break"])
        
        # Total completed tasks across all non-manager employees
        total_completed = sum(len(e.get("completed_list", [])) for e in emp_list)
        
        self.metricsUpdated.emit(active, paused, total_completed)

    def _format_time(self, seconds):
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def set_employee_state(self, emp_id, status, task="None"):
        """Delegate to Firestore which will then trigger the signal loop"""
        # Find active task id if any? In database_manager we made simple methods
        self.db.update_user_status(emp_id, status)
        if status == "Offline":
            self.db.update_user_status(emp_id, status, acc_sec=0)
            
    def log_activity(self, message):
        timestamp = datetime.now().strftime("%I:%M %p")
        # Write to firestore instead of local emit
        self.db.log_activity(message, timestamp)


class AuthController(QObject):
    loginResult = Signal(str, str, int) # role, name, user_id
    error = Signal(str)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager

    @Slot(str, str)
    def login(self, username, password):
        user = self.db.authenticate_user(username, password)
        if user:
            user_id, role, name = user
            self.loginResult.emit(role, name, int(user_id))
        else:
            self.error.emit("Invalid credentials.")

    @Slot(str)
    def request_password_reset(self, emp_id):
        self.db.request_password_reset(emp_id)



import ctypes
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

def get_idle_time():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        return millis / 1000.0
    return 0

class EmployeeController(QObject):
    hasActiveTaskChanged = Signal()
    isTaskPausedChanged = Signal()
    activeTimerTextChanged = Signal()
    totalHoursChanged = Signal()
    autoPaused = Signal()
    assignedTasksSync = Signal(list)
    statsChanged = Signal()

    def __init__(self, engine, history_model, emp_id=2):
        super().__init__()
        self.engine = engine
        self.emp_id = emp_id
        self._history_model = history_model
        self._assigned_tasks_model = AssignedTasksModel()
        self._recent_history_model = TaskHistoryModel()
        self._total_seconds = 0
        
        self.engine.employeeTimerUpdated.connect(self._on_global_timer)
        self.engine.employeeStatusChanged.connect(self._on_status_changed)
        self.assignedTasksSync.connect(self._on_assigned_tasks_sync)

        self.idle_timer = QTimer(self)
        self.idle_timer.setInterval(60000)
        self.idle_timer.timeout.connect(self._check_idle)
        self.idle_timer.start()

    @Slot()
    def _check_idle(self):
        if self.hasActiveTask and not self.isTaskPaused:
            if get_idle_time() > 15 * 60:
                self.pauseTask()
                self.autoPaused.emit()

    @Slot(list)
    def _on_assigned_tasks_sync(self, tasks):
        self._assigned_tasks_model.setTasks(tasks)

    @Slot(int)
    def loadUser(self, emp_id):
        self.emp_id = emp_id
        
        # Load tasks for today
        date_str = datetime.now().strftime("%Y-%m-%d")
        tasks = self.engine.db.get_user_tasks_for_date(self.emp_id, date_str)
        history_list = []
        total_sec = 0
        for task in tasks:
            _, t_type, notes, status, start, end, acc_sec = task
            if status == "Completed":
                total_sec += acc_sec
                history_list.append({"taskType": t_type, "notes": notes, "duration": self.engine._format_time(acc_sec)})
        self._history_model.setHistory(history_list)
        self._total_seconds = total_sec
        
        # Trigger initial fetch and listen for assigned tasks
        pending_initial = self.engine.db.get_pending_assigned_tasks(self.emp_id)
        self._assigned_tasks_model.setTasks(pending_initial)
        self.engine.db.listen_to_assigned_tasks(self.emp_id, lambda tasks: self.assignedTasksSync.emit(tasks))
        
        recent = self.engine.db.get_recent_completed_tasks(self.emp_id)
        self._recent_history_model.setHistory(recent)

        self.hasActiveTaskChanged.emit()
        self.isTaskPausedChanged.emit()
        self.activeTimerTextChanged.emit()
        self.totalHoursChanged.emit()

    @Slot(int, str)
    def _on_global_timer(self, emp_id, timer_str):
        if emp_id == self.emp_id:
            self.activeTimerTextChanged.emit()

    @Slot(int, str, str, list)
    def _on_status_changed(self, emp_id, task, status, completed_list):
        if emp_id == self.emp_id:
            self.hasActiveTaskChanged.emit()
            self.isTaskPausedChanged.emit()

    @Slot(str, int, str)
    def start_assigned_task(self, task_id, allocated_time, title):
        # Mark as in_progress
        self.engine.db.db.collection('assigned_tasks').document(task_id).set({
            'status': 'in_progress'
        }, merge=True)
        
        # Stop current task if any
        if self.hasActiveTask:
            self.endTask()
            
        # Start new task
        self.engine.db.start_task(self.emp_id, title)
        
        # Note: 'allocated_time' is now passed, we could store it to a local property for a countdown timer, 
        # but for now we'll just log it or pass it if the backend supports it.
        emp_name = self.engine.employees[self.emp_id]["name"] if self.emp_id in self.engine.employees else "Employee"
        self.engine.db.log_activity(f"▶️ {emp_name} started assigned task: {title} ({allocated_time}m)", datetime.now().strftime("%I:%M %p"))
        
        self.hasActiveTaskChanged.emit()
        self.isTaskPausedChanged.emit()

    @Slot(str, str)
    def startTask(self, task_type, notes):
        if self.emp_id not in self.engine.employees: return
        emp_name = self.engine.employees[self.emp_id]["name"]
        
        # Real Firestore mutation
        self.engine.db.start_task(self.emp_id, task_type, notes)
        self.engine.db.log_activity(f"▶️ {emp_name} started: {task_type}", datetime.now().strftime("%I:%M %p"))

    @Slot()
    def pauseTask(self):
        if self.emp_id not in self.engine.employees: return
        emp_name = self.engine.employees[self.emp_id]["name"]
        curr_acc_sec = self.engine.employees[self.emp_id]["acc_sec"]
        
        self.engine.db.update_user_status(self.emp_id, "Paused", acc_sec=curr_acc_sec)
        self.engine.db.log_activity(f"⏸️ {emp_name} paused task", datetime.now().strftime("%I:%M %p"))

    @Slot()
    def resumeTask(self):
        if self.emp_id not in self.engine.employees: return
        emp_name = self.engine.employees[self.emp_id]["name"]
        curr_acc_sec = self.engine.employees[self.emp_id]["acc_sec"]
        
        self.engine.db.update_user_status(self.emp_id, "Active", acc_sec=curr_acc_sec)
        self.engine.db.log_activity(f"▶️ {emp_name} resumed task", datetime.now().strftime("%I:%M %p"))

    @Slot()
    def endTask(self):
        self.complete_task_with_notes("Completed")

    @Slot(str)
    def complete_task_with_notes(self, notes="Completed"):
        if self.emp_id not in self.engine.employees: return
        emp_name = self.engine.employees[self.emp_id]["name"]
        task = self.engine.employees[self.emp_id]["task"]
        sec = self.engine.employees[self.emp_id]["acc_sec"]
        
        duration_text = self.engine._format_time(sec)
        self._total_seconds += sec
        
        task_id = self.engine.db.get_active_task_id(self.emp_id)
        if task_id:
            self.engine.db.end_task(task_id, self.emp_id, sec, notes=notes)
            
        self._history_model.addTask(task, notes, duration_text)
        note_str = f" ({notes})" if notes and notes != "Completed" else ""
        self.engine.db.log_activity(f"✅ {emp_name} completed: {task} ({duration_text}){note_str}", datetime.now().strftime("%I:%M %p"))
        self.totalHoursChanged.emit()
        self.statsChanged.emit()

    @Slot(int, str)
    def request_task_extension(self, extra_minutes, reason):
        self.engine.db.request_task_extension(self.emp_id, extra_minutes, reason)

    @Property(str, notify=statsChanged)
    def completedTasksCount(self):
        stats = self.engine.db.get_productivity_stats(self.emp_id)
        return stats["total_completed"]

    @Property(str, notify=statsChanged)
    def avgTaskTimeText(self):
        stats = self.engine.db.get_productivity_stats(self.emp_id)
        return stats["avg_time"]

    @Property(str, notify=statsChanged)
    def adherenceScoreText(self):
        stats = self.engine.db.get_productivity_stats(self.emp_id)
        return stats["adherence"]

    @Slot(str, str, str, result=bool)
    def update_employee_password(self, emp_id, current_pw, new_pw):
        return self.engine.db.update_employee_password(emp_id, current_pw, new_pw)

    @Property(bool, notify=hasActiveTaskChanged)
    def hasActiveTask(self):
        if self.emp_id not in self.engine.employees: return False
        return self.engine.employees[self.emp_id]["status"] in ["Active", "Paused"]

    @Property(bool, notify=isTaskPausedChanged)
    def isTaskPaused(self):
        if self.emp_id not in self.engine.employees: return False
        return self.engine.employees[self.emp_id]["status"] == "Paused"

    @Property(str, notify=activeTimerTextChanged)
    def activeTimerText(self):
        if self.emp_id not in self.engine.employees: return "00:00:00"
        sec = self.engine.employees[self.emp_id]["acc_sec"]
        return self.engine._format_time(sec)

    @Property(str, notify=totalHoursChanged)
    def totalHoursTodayText(self):
        h, rem = divmod(self._total_seconds, 3600)
        m, s = divmod(rem, 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m {s}s"

    @Property(str, notify=hasActiveTaskChanged)
    def employeeName(self):
        if self.emp_id in self.engine.employees:
            return self.engine.employees[self.emp_id]["name"]
        return "Employee"

    @Property(str, notify=hasActiveTaskChanged)
    def employeeStatus(self):
        if self.emp_id in self.engine.employees:
            return self.engine.employees[self.emp_id]["task"]
        return "None"

    @Property(str, notify=hasActiveTaskChanged)
    def employeeIdString(self):
        return f"EMP-{self.emp_id:04d}"

    @Property(QObject, constant=True)
    def assignedTasksModel(self):
        return self._assigned_tasks_model
        
    @Property(QObject, constant=True)
    def recentTaskHistoryModel(self):
        return self._recent_history_model

    @Property(QObject, constant=True)
    def taskHistoryModel(self):
        return self._history_model

class ManagerController(QObject):
    metricsChanged = Signal()

    def __init__(self, engine, emp_model, feed_model):
        super().__init__()
        self.engine = engine
        self._emp_model = emp_model
        self.feed_model = feed_model
        self._employee_history_model = TaskHistoryModel()
        self._employee_history_model.setParent(self)
        self._manager_pending_tasks_model = AssignedTasksModel()
        self._manager_pending_tasks_model.setParent(self)
        
        self.active_count = 1
        self.paused_count = 1
        self.completed_count = 15

        # Bind to engine signals
        self.engine.employeeStatusChanged.connect(self._emp_model.updateEmployeeStatus)
        self.engine.employeeTimerUpdated.connect(self._emp_model.updateEmployeeTimer)
        self.engine.employeesSynced.connect(self._emp_model.syncEmployees)
        self.engine.metricsUpdated.connect(self._on_metrics_updated)
        
        # Bind directly to Firestore feed signal
        self.engine.db.signals.activityFeedChanged.connect(self._on_feed_updated)

    @Slot(list)
    def _on_feed_updated(self, activity_data):
        # In a real app we'd carefully diff, but we can just clear and add or rely on the model API
        self.feed_model._events.clear()
        self.feed_model.beginResetModel()
        for doc in reversed(activity_data): # Show newest at top depending on how model displays it
            self.feed_model._events.insert(0, {"event": doc.get('message'), "time": doc.get('timestamp')})
        self.feed_model.endResetModel()

    @Slot(str, str)
    def reset_employee_password(self, emp_id, new_password):
        self.engine.db.manager_reset_password(emp_id, new_password)

    @Slot(int, int, int)
    def _on_metrics_updated(self, active, paused, completed):
        self.active_count = active
        self.paused_count = paused
        self.completed_count = completed
        self.metricsChanged.emit()

    @Property(int, notify=metricsChanged)
    def activeNow(self): return self.active_count

    @Property(int, notify=metricsChanged)
    def onBreak(self): return self.paused_count

    @Property(int, notify=metricsChanged)
    def completedToday(self): return self.completed_count

    @Property(int, notify=metricsChanged)
    def activeCount(self): return self.active_count

    @Property(int, notify=metricsChanged)
    def breakCount(self): return self.paused_count

    @Property(int, notify=metricsChanged)
    def completedCount(self): return self.completed_count

    @Property(QObject, constant=True)
    def employeeListModel(self):
        return self._emp_model

    @Property(QObject, constant=True)
    def activityFeedModel(self):
        return self.feed_model

    @Property(QObject, constant=True)
    def employeeHistoryModel(self):
        return self._employee_history_model

    @Property(QObject, constant=True)
    def managerCompletedTasksModel(self):
        return self._employee_history_model

    @Property(QObject, constant=True)
    def managerPendingTasksModel(self):
        return self._manager_pending_tasks_model

    @Slot(int)
    def fetch_employee_history(self, emp_id):
        recent = self.engine.db.get_recent_completed_tasks(str(emp_id), limit=20)
        self._employee_history_model.setHistory(recent)
        
        pending = self.engine.db.get_pending_assigned_tasks(str(emp_id))
        self._manager_pending_tasks_model.setTasks(pending)

    @Property(list, notify=metricsChanged)
    def activeDetailsList(self):
        return [{"title": emp["name"], "subtitle": emp["task"]} for emp in self.engine.employees.values() if emp["status"] == "Active"]

    @Property(list, notify=metricsChanged)
    def breakDetailsList(self):
        return [{"title": emp["name"], "subtitle": emp["task"]} for emp in self.engine.employees.values() if emp["status"] == "Paused"]

    @Property(list, notify=metricsChanged)
    def completedDetailsList(self):
        res = []
        for emp in self.engine.employees.values():
            for task in emp["completed_list"]:
                res.append({"title": f"✅ {emp['name']}", "subtitle": task})
        
        # Add mock completed tasks to match the '15' default count
        if len(res) == 0:
            for i in range(15):
                res.append({"title": "✅ System", "subtitle": f"Archived Task #{i+1}"})
                
        return res

    @Slot(str, str, str)
    def create_employee(self, name, emp_id, password):
        self.engine.db.create_employee(name, emp_id, password)

    @Slot(str, str, str, int)
    def assign_task(self, emp_id, title, description, allocated_time):
        from firebase_admin import firestore
        try:
            if not emp_id or not title:
                print("Error: Missing Employee ID or Title")
                return
            task_data = {
                'emp_id': str(emp_id),
                'user_id': str(emp_id),
                'title': title,
                'description': description,
                'allocated_minutes': allocated_time,
                'status': 'pending',
                'created_at': firestore.SERVER_TIMESTAMP
            }
            self.engine.db.db.collection('assigned_tasks').add(task_data)
            self.engine.db.log_activity(f"Manager assigned task '{title}' ({allocated_time}m) to Employee ID: {emp_id}", datetime.now().strftime("%I:%M %p"))
            print(f"Success: Task '{title}' assigned to {emp_id}")
        except Exception as e:
            print(f"CRITICAL ERROR assigning task: {e}")

    @Slot(str)
    def delete_employee(self, emp_id):
        self.engine.db.delete_employee(emp_id)

    @Slot(result=str)
    def export_logs(self):
        import csv
        import os
        from firebase_admin import firestore
        filename = "activity_logs.csv"
        docs = self.engine.db.collection('activity_feed').order_by('timestamp_raw', direction=firestore.Query.DESCENDING).get()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Message"])
            for doc in docs:
                data = doc.to_dict()
                writer.writerow([data.get('timestamp', ''), data.get('message', '')])
        return os.path.abspath(filename)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    def handle_qml_error(obj, url):
        if obj is None:
            print(f"CRITICAL ERROR: Failed to load QML file: {url.toString()}")
            sys.exit(-1)
            
    engine.objectCreated.connect(handle_qml_error)
    
    # Instantiate the Database and Auth
    db_manager = DatabaseManager()
    auth_controller = AuthController(db_manager)
    
    # Instantiate the Global State Engine
    tp_engine = TeamPulseEngine(db_manager)
    tp_engine.setParent(app)
    
    # Instantiate Models
    emp_model = EmployeeStatusModel()
    emp_model.setParent(app)
    feed_model = ActivityFeedModel()
    feed_model.setParent(app)
    history_model = TaskHistoryModel()
    history_model.setParent(app)
    
    # Instantiate Controllers connected to the Engine
    employee_controller = EmployeeController(tp_engine, history_model)
    employee_controller.setParent(app)
    manager_controller = ManagerController(tp_engine, emp_model, feed_model)
    manager_controller.setParent(app)
    
    # Expose to QML before rendering
    engine.rootContext().setContextProperty("authController", auth_controller)
    engine.rootContext().setContextProperty("employeeController", employee_controller)
    engine.rootContext().setContextProperty("managerController", manager_controller)
    engine.rootContext().setContextProperty("employeeStatusModel", emp_model)
    engine.rootContext().setContextProperty("activityFeedModel", feed_model)
    
    qml_file = str((Path(__file__).parent / "main.qml").resolve())
    engine.load(qml_file)
    
    if not engine.rootObjects():
        print("CRITICAL ERROR: No root objects found.")
        sys.exit(-1)
        
    QTimer.singleShot(100, tp_engine.initialize_heavy_data)
    
    sys.exit(app.exec())
