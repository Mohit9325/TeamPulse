from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, Slot, Signal, Property

class EmployeeStatusModel(QAbstractListModel):
    NameRole = Qt.UserRole + 1
    TaskRole = Qt.UserRole + 2
    StatusRole = Qt.UserRole + 3
    TimerRole = Qt.UserRole + 4
    IdRole = Qt.UserRole + 5
    CompletedTasksRole = Qt.UserRole + 6
    ResetRequestedRole = Qt.UserRole + 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self._employees = [
            {"id": 2, "name": "Alex", "currentTask": "None", "status": "Offline", "timer": "00:00:00", "completed_list": []},
            {"id": 3, "name": "Sarah", "currentTask": "Client Meeting", "status": "Active", "timer": "00:45:12", "completed_list": []},
            {"id": 4, "name": "Michael", "currentTask": "Lunch", "status": "Paused", "timer": "00:30:00", "completed_list": []},
            {"id": 5, "name": "Jessica", "currentTask": "Design Review", "status": "Offline", "timer": "00:00:00", "completed_list": []}
        ]
        self._filtered = list(self._employees)

    def rowCount(self, parent=None):
        return len(self._filtered)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._filtered)):
            return None
        
        emp = self._filtered[index.row()]
        if role == self.NameRole: return emp["name"]
        elif role == self.TaskRole: return emp["currentTask"]
        elif role == self.StatusRole: return emp["status"]
        elif role == self.TimerRole: return emp["timer"]
        elif role == self.IdRole: return emp["id"]
        elif role == self.CompletedTasksRole:
            if not emp.get("completed_list"): return "None"
            return ", ".join(emp["completed_list"])
        elif role == self.ResetRequestedRole:
            return emp.get("reset_requested", False)
        return None

    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.TaskRole: b"currentTask",
            self.StatusRole: b"status",
            self.TimerRole: b"timer",
            self.IdRole: b"emp_id",
            self.CompletedTasksRole: b"completedTasksString",
            self.ResetRequestedRole: b"resetRequested"
        }

    from PySide6.QtCore import Slot
    @Slot(list)
    def syncEmployees(self, employee_list):
        self.beginResetModel()
        self._employees = employee_list
        self._filtered = list(self._employees)
        self.endResetModel()

    def updateEmployeeStatus(self, emp_id, task, status, completed_list=None):
        for i, emp in enumerate(self._employees):
            if emp["id"] == emp_id:
                emp["currentTask"] = task
                emp["status"] = status
                if completed_list is not None:
                    emp["completed_list"] = completed_list
                if status == "Offline":
                    emp["timer"] = "00:00:00"
                
                # Find in filtered and emit dataChanged
                for j, f_emp in enumerate(self._filtered):
                    if f_emp["id"] == emp_id:
                        idx = self.index(j, 0)
                        self.dataChanged.emit(idx, idx, [self.TaskRole, self.StatusRole, self.TimerRole, self.CompletedTasksRole])
                        break
                break

    def updateEmployeeTimer(self, emp_id, timer_text):
        for i, emp in enumerate(self._employees):
            if emp["id"] == emp_id:
                emp["timer"] = timer_text
                
                # Fast update for timer
                for j, f_emp in enumerate(self._filtered):
                    if f_emp["id"] == emp_id:
                        idx = self.index(j, 0)
                        self.dataChanged.emit(idx, idx, [self.TimerRole])
                        break
                break

    @Slot(str)
    def filter_employees(self, query):
        self.beginResetModel()
        if not query:
            self._filtered = list(self._employees)
        else:
            self._filtered = [e for e in self._employees if query.lower() in e.get("name", "").lower()]
        self.endResetModel()


class ActivityFeedModel(QAbstractListModel):
    EventRole = Qt.UserRole + 1
    TimeRole = Qt.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_events = []
        self._events = []
        self._current_filter = "All"

    def rowCount(self, parent=None):
        return len(self._events)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._events)):
            return None
        evt = self._events[index.row()]
        if role == self.EventRole: return evt["event"]
        elif role == self.TimeRole: return evt["time"]
        return None

    def roleNames(self):
        return {
            self.EventRole: b"eventText",
            self.TimeRole: b"timestamp"
        }

    def addEvent(self, event_text, timestamp):
        from PySide6.QtCore import QModelIndex
        idx = len(self._events)
        self.beginInsertRows(QModelIndex(), idx, idx)
        self._events.append({"event": event_text, "time": timestamp})
        self._all_events.append({"event": event_text, "time": timestamp})
        self.endInsertRows()

    @Slot(list)
    def setEvents(self, events):
        self._all_events = events
        self.applyFilter(self._current_filter)

    @Slot(str)
    def filterLogs(self, tag):
        self.applyFilter(tag)

    def applyFilter(self, tag):
        self.beginResetModel()
        self._current_filter = tag
        if tag == "All":
            self._events = list(self._all_events)
        elif tag == "Tasks":
            self._events = [e for e in self._all_events if "completed:" in e["event"] or "started:" in e["event"] or "paused" in e["event"] or "resumed" in e["event"]]
        elif tag == "Admin Actions":
            self._events = [e for e in self._all_events if "Manager created" in e["event"] or "deleted" in e["event"]]
        else:
            self._events = list(self._all_events)
        self.endResetModel()

class TaskHistoryModel(QAbstractListModel):
    TaskTypeRole = Qt.UserRole + 1
    NotesRole = Qt.UserRole + 2
    DurationRole = Qt.UserRole + 3
    DateRole = Qt.UserRole + 4
    TitleRole = Qt.UserRole + 5
    CompletionTimeRole = Qt.UserRole + 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []

    def rowCount(self, parent=None):
        return len(self._history)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._history)):
            return None
        task = self._history[index.row()]
        if role == self.TaskTypeRole or role == self.TitleRole: 
            return task.get("title", task.get("taskType", ""))
        elif role == self.NotesRole: 
            return task.get("notes", "")
        elif role == self.DurationRole: 
            return task.get("duration", "")
        elif role == self.DateRole or role == self.CompletionTimeRole: 
            return task.get("completion_time", task.get("date", ""))
        return None

    def roleNames(self):
        return {
            self.TaskTypeRole: b"taskType",
            self.TitleRole: b"title",
            self.NotesRole: b"notes",
            self.DurationRole: b"duration",
            self.DateRole: b"date",
            self.CompletionTimeRole: b"completion_time"
        }

    def addTask(self, task_type, notes, duration):
        from PySide6.QtCore import QModelIndex
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._history.insert(0, {"taskType": task_type, "notes": notes, "duration": duration})
        self.endInsertRows()

    from PySide6.QtCore import Slot
    @Slot(list)
    def setHistory(self, history_list):
        self.beginResetModel()
        self._history = history_list
        self.endResetModel()

class AssignedTasksModel(QAbstractListModel):
    IdRole = Qt.UserRole + 1
    TitleRole = Qt.UserRole + 2
    DescRole = Qt.UserRole + 3
    AllocatedRole = Qt.UserRole + 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tasks = []

    def rowCount(self, parent=None):
        return len(self._tasks)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._tasks)):
            return None
        task = self._tasks[index.row()]
        if role == self.IdRole: return task.get("id", "")
        elif role == self.TitleRole: return task.get("title", "")
        elif role == self.DescRole: return task.get("description", "")
        elif role == self.AllocatedRole: return task.get("allocated_minutes", 0)
        return None

    def roleNames(self):
        return {
            self.IdRole: b"task_id",
            self.TitleRole: b"title",
            self.DescRole: b"description",
            self.AllocatedRole: b"allocated_time"
        }

    @Slot(list)
    def setTasks(self, task_list):
        self.beginResetModel()
        self._tasks = task_list
        self.endResetModel()
