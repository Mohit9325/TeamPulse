import os
import time
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Cookie, Response, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from database_manager import DatabaseManager, hash_pw

app = FastAPI(title="TeamPulse Web Application", version="2.0")

# Initialize shared DatabaseManager instance
db_manager = DatabaseManager()

# Simple session storage for demo preview
SESSIONS = {}

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateEmployeeRequest(BaseModel):
    name: str
    emp_id: int
    password: str

class AssignTaskRequest(BaseModel):
    emp_id: int
    emp_name: str
    title: str
    description: str
    allocated_minutes: int

class StartTaskRequest(BaseModel):
    task_type: str
    notes: Optional[str] = "Web Portal Task"

class TaskStatusUpdateRequest(BaseModel):
    task_id: Optional[str] = None
    accumulated_seconds: int = 0

class CompleteTaskRequest(BaseModel):
    task_id: Optional[str] = None
    accumulated_seconds: int = 0
    notes: Optional[str] = "Completed via Web Portal"

class ResetPasswordRequest(BaseModel):
    new_password: str

class ExtensionRequest(BaseModel):
    extra_minutes: int
    reason: str

# Helper to verify active session
def get_current_user(session_id: Optional[str] = Cookie(None)):
    if not session_id or session_id not in SESSIONS:
        return None
    return SESSIONS[session_id]

# --- API ENDPOINTS ---

@app.post("/api/login")
def login(req: LoginRequest, response: Response):
    user_info = db_manager.authenticate_user(req.username, req.password)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user_id, role, name = user_info
    session_id = f"session_{user_id}_{int(time.time())}"
    user_data = {
        "id": user_id,
        "name": name,
        "role": role,
        "session_id": session_id
    }
    SESSIONS[session_id] = user_data
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return user_data

@app.post("/api/logout")
def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    if session_id in SESSIONS:
        del SESSIONS[session_id]
    response.delete_cookie("session_id")
    return {"status": "success"}

@app.get("/api/me")
def get_me(session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.get("/api/metrics")
def get_metrics(session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Query live employees from Firestore
    emp_docs = db_manager.db.collection('employees').stream()
    employees = [doc.to_dict() for doc in emp_docs]
    
    active_count = sum(1 for e in employees if e.get('status') == 'Active')
    paused_count = sum(1 for e in employees if e.get('status') == 'Paused')
    
    # Calculate completed today
    today_str = datetime.now().strftime("%Y-%m-%d")
    task_docs = db_manager.db.collection('tasks').where(filter=db_manager.db.FieldFilter('status', '==', 'Completed')).stream()
    completed_today = sum(1 for doc in task_docs if doc.to_dict().get('end_time', '').startswith(today_str))
    
    return {
        "active_employees": active_count,
        "paused_employees": paused_count,
        "completed_today": completed_today,
        "total_employees": len(employees)
    }

@app.get("/api/employees")
def get_employees(session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    emp_docs = db_manager.db.collection('employees').stream()
    employees = [doc.to_dict() for doc in emp_docs]
    employees.sort(key=lambda x: x.get('id', 0))
    return employees

@app.post("/api/employees")
def create_employee(req: CreateEmployeeRequest, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    db_manager.create_employee(req.name, req.emp_id, req.password)
    return {"status": "success", "message": f"Employee {req.name} created."}

@app.delete("/api/employees/{emp_id}")
def delete_employee(emp_id: int, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    db_manager.delete_employee(emp_id)
    return {"status": "success", "message": f"Employee {emp_id} deleted."}

@app.post("/api/employees/{emp_id}/reset-password")
def reset_password(emp_id: int, req: ResetPasswordRequest, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    db_manager.manager_reset_password(emp_id, req.new_password)
    return {"status": "success", "message": f"Password reset for employee {emp_id}."}

@app.get("/api/employees/{emp_id}/stats")
def get_employee_stats(emp_id: int, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return db_manager.get_productivity_stats(emp_id)

@app.post("/api/tasks/assign")
def assign_task(req: AssignTaskRequest, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user or user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Manager access required")
    
    task_data = {
        'emp_id': str(req.emp_id),
        'user_id': str(req.emp_id),
        'title': req.title,
        'description': req.description,
        'allocated_minutes': req.allocated_minutes,
        'status': 'pending',
        'assigned_at': datetime.now().isoformat()
    }
    db_manager.db.collection('assigned_tasks').add(task_data)
    db_manager.log_activity(f"Manager assigned task '{req.title}' to {req.emp_name}", datetime.now().strftime("%I:%M %p"))
    return {"status": "success", "message": "Task dispatched."}

@app.get("/api/tasks/assigned")
def get_assigned(session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return db_manager.get_pending_assigned_tasks(user["id"])

@app.post("/api/tasks/start")
def start_task(req: StartTaskRequest, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    task_id = db_manager.start_task(user["id"], req.task_type, req.notes)
    db_manager.log_activity(f"{user['name']} started task: {req.task_type}", datetime.now().strftime("%I:%M %p"))
    return {"status": "success", "task_id": task_id}

@app.post("/api/tasks/pause")
def pause_task(req: TaskStatusUpdateRequest, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if req.task_id:
        db_manager.update_task_accumulated_time(req.task_id, req.accumulated_seconds)
    db_manager.update_user_status(user["id"], "Paused", req.accumulated_seconds)
    db_manager.log_activity(f"{user['name']} paused task execution", datetime.now().strftime("%I:%M %p"))
    return {"status": "success"}

@app.post("/api/tasks/resume")
def resume_task(session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db_manager.update_user_status(user["id"], "Active")
    db_manager.log_activity(f"{user['name']} resumed task execution", datetime.now().strftime("%I:%M %p"))
    return {"status": "success"}

@app.post("/api/tasks/complete")
def complete_task(req: CompleteTaskRequest, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    task_id = req.task_id or db_manager.get_active_task_id(user["id"])
    db_manager.end_task(task_id, user["id"], req.accumulated_seconds, req.notes)
    db_manager.log_activity(f"{user['name']} completed task", datetime.now().strftime("%I:%M %p"))
    return {"status": "success"}

@app.post("/api/tasks/extension")
def request_extension(req: ExtensionRequest, session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    db_manager.request_task_extension(user["id"], req.extra_minutes, req.reason)
    return {"status": "success"}

@app.get("/api/tasks/history")
def get_history(session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return db_manager.get_recent_completed_tasks(user["id"])

@app.get("/api/activity")
def get_activity(session_id: Optional[str] = Cookie(None)):
    user = get_current_user(session_id)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    docs = db_manager.db.collection('activity_feed').order_by('timestamp_raw', direction=db_manager.db.Query.DESCENDING).limit(30).stream()
    activities = [d.to_dict() for d in docs]
    return activities

# --- FRONTEND SINGLE PAGE APP (SPA) ROUTE ---

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_CONTENT

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TeamPulse Enterprise Web Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
            --card-bg: rgba(30, 41, 59, 0.7);
            --card-border: rgba(255, 255, 255, 0.1);
            --accent-primary: #6366f1;
            --accent-hover: #4f46e5;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
        }

        body {
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .navbar {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--card-border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 700;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .user-menu {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .role-badge {
            background: rgba(99, 102, 241, 0.2);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .btn {
            background: var(--accent-primary);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-main);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .btn-danger {
            background: var(--danger);
        }

        .btn-danger:hover {
            background: #dc2626;
        }

        .container {
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1.5rem;
            flex: 1;
            width: 100%;
        }

        /* Auth Screen */
        .auth-card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 2.5rem;
            max-width: 440px;
            margin: 4rem auto;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        }

        .auth-card h2 {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
            text-align: center;
        }

        .auth-card p {
            color: var(--text-muted);
            text-align: center;
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }

        .form-group {
            margin-bottom: 1.25rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .form-control {
            width: 100%;
            padding: 0.75rem 1rem;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            color: white;
            font-size: 0.95rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .form-control:focus {
            border-color: var(--accent-primary);
        }

        .demo-auth-box {
            margin-top: 2rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px dashed var(--card-border);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }

        .demo-auth-box p {
            margin-bottom: 0.75rem;
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .demo-buttons {
            display: flex;
            gap: 0.5rem;
            justify-content: center;
        }

        /* Metrics Row */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .metric-card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .metric-val {
            font-size: 2.25rem;
            font-weight: 700;
            margin-top: 0.25rem;
        }

        .metric-label {
            color: var(--text-muted);
            font-size: 0.85rem;
        }

        /* Table & Lists */
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }

        .card-title {
            font-size: 1.15rem;
            font-weight: 600;
        }

        .table {
            width: 100%;
            border-collapse: collapse;
        }

        .table th, .table td {
            padding: 0.85rem 1rem;
            text-align: left;
            border-bottom: 1px solid var(--card-border);
            font-size: 0.9rem;
        }

        .table th {
            color: var(--text-muted);
            font-weight: 500;
        }

        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }

        .status-Active { background: var(--success); }
        .status-Paused { background: var(--warning); }
        .status-Offline { background: var(--text-muted); }

        /* Employee Workbench Live Timer Card */
        .workbench-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.9) 100%);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 2.5rem;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .timer-display {
            font-size: 3.5rem;
            font-weight: 800;
            font-family: monospace;
            margin: 1rem 0;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .action-bar {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1.5rem;
        }

        .hidden { display: none !important; }

        /* Modal Styles */
        .modal {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7);
            backdrop-filter: blur(8px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .modal-content {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 2rem;
            width: 100%;
            max-width: 480px;
        }
    </style>
</head>
<body>

    <nav class="navbar">
        <div class="brand">
            ⚡ TeamPulse Dashboard
        </div>
        <div class="user-menu" id="userMenu">
            <span id="userName">Not Logged In</span>
            <span id="userRole" class="role-badge">Guest</span>
            <button class="btn btn-secondary hidden" id="logoutBtn" onclick="handleLogout()">Logout</button>
        </div>
    </nav>

    <div class="container">
        <!-- Auth View -->
        <div id="authView" class="auth-card">
            <h2>Welcome Back</h2>
            <p>Sign in to access your TeamPulse workspace</p>
            <form onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="username" class="form-control" placeholder="Admin or Alex" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" class="form-control" placeholder="••••••••" required>
                </div>
                <button type="submit" class="btn" style="width:100%;">Sign In</button>
            </form>

            <div class="demo-auth-box">
                <p>Quick Demo Quick-Login Credentials:</p>
                <div class="demo-buttons">
                    <button class="btn btn-secondary" style="font-size:0.8rem;" onclick="quickLogin('Admin', 'admin123')">👑 Manager Demo</button>
                    <button class="btn btn-secondary" style="font-size:0.8rem;" onclick="quickLogin('Alex', 'emp123')">👷 Employee Demo</button>
                </div>
            </div>
        </div>

        <!-- Manager View -->
        <div id="managerView" class="hidden">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div>
                        <div class="metric-label">Active Staff</div>
                        <div class="metric-val" id="mActiveCount" style="color:var(--success);">0</div>
                    </div>
                    <span style="font-size:2rem;">🟢</span>
                </div>
                <div class="metric-card">
                    <div>
                        <div class="metric-label">Paused Staff</div>
                        <div class="metric-val" id="mPausedCount" style="color:var(--warning);">0</div>
                    </div>
                    <span style="font-size:2rem;">⏸️</span>
                </div>
                <div class="metric-card">
                    <div>
                        <div class="metric-label">Completed Tasks Today</div>
                        <div class="metric-val" id="mCompletedCount" style="color:var(--accent-primary);">0</div>
                    </div>
                    <span style="font-size:2rem;">🎯</span>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">Live Staff Directory & Status</div>
                    <div>
                        <button class="btn btn-secondary" onclick="showAddEmployeeModal()">+ Add Employee</button>
                        <button class="btn" onclick="showAssignTaskModal()">+ Dispatch Task</button>
                    </div>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Employee ID</th>
                            <th>Name</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Current Task</th>
                            <th>Timer</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="managerEmpTable">
                        <!-- Populated by JS -->
                    </tbody>
                </table>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">System Activity Stream</div>
                </div>
                <div id="activityStream" style="max-height: 250px; overflow-y: auto;">
                    <!-- Populated by JS -->
                </div>
            </div>
        </div>

        <!-- Employee View -->
        <div id="employeeView" class="hidden">
            <div class="workbench-card">
                <h3 id="empCurrentTaskTitle">No Task In Progress</h3>
                <div class="timer-display" id="empTimer">00:00:00</div>
                <div class="action-bar">
                    <button class="btn" id="startBtn" onclick="handleStartTask()">Start Working</button>
                    <button class="btn btn-secondary hidden" id="pauseBtn" onclick="handlePauseTask()">Pause</button>
                    <button class="btn btn-secondary hidden" id="resumeBtn" onclick="handleResumeTask()">Resume</button>
                    <button class="btn btn-danger hidden" id="completeBtn" onclick="handleCompleteTask()">Complete Task</button>
                    <button class="btn btn-secondary hidden" id="extBtn" onclick="showExtensionModal()">Request Extra Time</button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">Assigned Work Queue</div>
                </div>
                <div id="assignedQueueList">
                    <!-- Populated by JS -->
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">Completed Work Log</div>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Task Title</th>
                            <th>Duration</th>
                            <th>Date Completed</th>
                        </tr>
                    </thead>
                    <tbody id="empHistoryTable">
                        <!-- Populated by JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Modals -->
    <div id="addEmpModal" class="modal hidden">
        <div class="modal-content">
            <h3 style="margin-bottom:1rem;">Add New Employee</h3>
            <div class="form-group">
                <label>Employee Name</label>
                <input type="text" id="newEmpName" class="form-control">
            </div>
            <div class="form-group">
                <label>Employee ID Number</label>
                <input type="number" id="newEmpId" class="form-control">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="newEmpPw" class="form-control">
            </div>
            <div style="display:flex; gap:0.5rem; justify-content:flex-end;">
                <button class="btn btn-secondary" onclick="closeModal('addEmpModal')">Cancel</button>
                <button class="btn" onclick="submitAddEmployee()">Create Staff</button>
            </div>
        </div>
    </div>

    <div id="assignTaskModal" class="modal hidden">
        <div class="modal-content">
            <h3 style="margin-bottom:1rem;">Dispatch Task to Employee</h3>
            <div class="form-group">
                <label>Select Employee</label>
                <select id="assignTargetEmp" class="form-control"></select>
            </div>
            <div class="form-group">
                <label>Task Title</label>
                <input type="text" id="assignTitle" class="form-control" placeholder="Q4 Financial Review">
            </div>
            <div class="form-group">
                <label>Allocated Minutes</label>
                <input type="number" id="assignMins" class="form-control" value="30">
            </div>
            <div style="display:flex; gap:0.5rem; justify-content:flex-end;">
                <button class="btn btn-secondary" onclick="closeModal('assignTaskModal')">Cancel</button>
                <button class="btn" onclick="submitAssignTask()">Dispatch Task</button>
            </div>
        </div>
    </div>

    <div id="extensionModal" class="modal hidden">
        <div class="modal-content">
            <h3 style="margin-bottom:1rem;">Request Task Time Extension</h3>
            <div class="form-group">
                <label>Extra Minutes Needed</label>
                <input type="number" id="extMins" class="form-control" value="15">
            </div>
            <div class="form-group">
                <label>Reason</label>
                <input type="text" id="extReason" class="form-control" placeholder="Unexpected database lock issue">
            </div>
            <div style="display:flex; gap:0.5rem; justify-content:flex-end;">
                <button class="btn btn-secondary" onclick="closeModal('extensionModal')">Cancel</button>
                <button class="btn" onclick="submitExtension()">Send Request</button>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let timerInterval = null;
        let timerSeconds = 0;
        let isRunning = false;
        let currentTaskId = null;

        // Check authentication status on load
        window.addEventListener('DOMContentLoaded', async () => {
            try {
                const res = await fetch('/api/me');
                if (res.ok) {
                    currentUser = await res.json();
                    setupDashboard();
                }
            } catch (e) {}
        });

        async function handleLogin(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            await doLogin(username, password);
        }

        async function quickLogin(u, p) {
            await doLogin(u, p);
        }

        async function doLogin(u, p) {
            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: u, password: p})
                });
                if (res.ok) {
                    currentUser = await res.json();
                    setupDashboard();
                } else {
                    alert('Invalid login credentials');
                }
            } catch(e) {
                alert('Connection error');
            }
        }

        async function handleLogout() {
            await fetch('/api/logout', {method: 'POST'});
            currentUser = null;
            clearInterval(timerInterval);
            location.reload();
        }

        function setupDashboard() {
            document.getElementById('authView').classList.add('hidden');
            document.getElementById('logoutBtn').classList.remove('hidden');
            document.getElementById('userName').textContent = currentUser.name;
            document.getElementById('userRole').textContent = currentUser.role;

            if (currentUser.role === 'manager') {
                document.getElementById('managerView').classList.remove('hidden');
                refreshManagerData();
                setInterval(refreshManagerData, 3000);
            } else {
                document.getElementById('employeeView').classList.remove('hidden');
                refreshEmployeeData();
                setInterval(refreshEmployeeData, 3000);
            }
        }

        // Manager Logic
        async function refreshManagerData() {
            const metricsRes = await fetch('/api/metrics');
            if (metricsRes.ok) {
                const m = await metricsRes.json();
                document.getElementById('mActiveCount').textContent = m.active_employees;
                document.getElementById('mPausedCount').textContent = m.paused_employees;
                document.getElementById('mCompletedCount').textContent = m.completed_today;
            }

            const empRes = await fetch('/api/employees');
            if (empRes.ok) {
                const emps = await empRes.json();
                const tbody = document.getElementById('managerEmpTable');
                tbody.innerHTML = '';
                
                const select = document.getElementById('assignTargetEmp');
                select.innerHTML = '';

                emps.forEach(emp => {
                    if (emp.role === 'employee') {
                        const opt = document.createElement('option');
                        opt.value = emp.id;
                        opt.textContent = `${emp.name} (ID: ${emp.id})`;
                        select.appendChild(opt);
                    }

                    const tr = document.createElement('tr');
                    const sec = emp.acc_sec || 0;
                    const h = Math.floor(sec / 3600);
                    const m = Math.floor((sec % 3600) / 60);
                    const s = sec % 60;
                    const timeStr = `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;

                    tr.innerHTML = `
                        <td>${emp.id}</td>
                        <td><strong>${emp.name}</strong></td>
                        <td>${emp.role}</td>
                        <td><span class="status-dot status-${emp.status}"></span>${emp.status}</td>
                        <td>${emp.current_task || 'None'}</td>
                        <td style="font-family:monospace;">${timeStr}</td>
                        <td>
                            <button class="btn btn-secondary" style="padding:0.3rem 0.6rem; font-size:0.8rem;" onclick="handleResetPw(${emp.id})">Reset PW</button>
                            ${emp.role !== 'manager' ? `<button class="btn btn-danger" style="padding:0.3rem 0.6rem; font-size:0.8rem;" onclick="handleDeleteEmp(${emp.id})">Delete</button>` : ''}
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            const actRes = await fetch('/api/activity');
            if (actRes.ok) {
                const acts = await actRes.json();
                const stream = document.getElementById('activityStream');
                stream.innerHTML = acts.map(a => `
                    <div style="padding:0.5rem 0; border-bottom:1px solid var(--card-border); font-size:0.85rem; display:flex; justify-content:space-between;">
                        <span>${a.message}</span>
                        <span style="color:var(--text-muted); font-size:0.75rem;">${a.timestamp}</span>
                    </div>
                `).join('');
            }
        }

        // Employee Logic
        async function refreshEmployeeData() {
            const queueRes = await fetch('/api/tasks/assigned');
            if (queueRes.ok) {
                const queue = await queueRes.json();
                const list = document.getElementById('assignedQueueList');
                if (queue.length === 0) {
                    list.innerHTML = '<p style="color:var(--text-muted); font-size:0.9rem;">No pending tasks assigned.</p>';
                } else {
                    list.innerHTML = queue.map(t => `
                        <div style="background:rgba(15,23,42,0.6); padding:1rem; border-radius:8px; margin-bottom:0.75rem; display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <h4 style="font-size:0.95rem;">${t.title}</h4>
                                <p style="color:var(--text-muted); font-size:0.8rem;">Allocated: ${t.allocated_minutes}m</p>
                            </div>
                            <button class="btn" style="padding:0.4rem 0.8rem; font-size:0.85rem;" onclick="startAssignedTask('${t.title}')">Start Work</button>
                        </div>
                    `).join('');
                }
            }

            const histRes = await fetch('/api/tasks/history');
            if (histRes.ok) {
                const hist = await histRes.json();
                const tbody = document.getElementById('empHistoryTable');
                tbody.innerHTML = hist.map(h => `
                    <tr>
                        <td>${h.title}</td>
                        <td style="color:var(--accent-primary); font-weight:600;">${h.duration}</td>
                        <td>${h.date}</td>
                    </tr>
                `).join('');
            }
        }

        function updateTimerUI() {
            const h = Math.floor(timerSeconds / 3600);
            const m = Math.floor((timerSeconds % 3600) / 60);
            const s = timerSeconds % 60;
            document.getElementById('empTimer').textContent = 
                `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
        }

        async function handleStartTask() {
            const taskName = prompt("Enter Task Title / Type:", "Project Development");
            if (!taskName) return;
            await startAssignedTask(taskName);
        }

        async function startAssignedTask(title) {
            const res = await fetch('/api/tasks/start', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_type: title})
            });
            if (res.ok) {
                const data = await res.json();
                currentTaskId = data.task_id;
                document.getElementById('empCurrentTaskTitle').textContent = title;
                timerSeconds = 0;
                isRunning = true;
                
                clearInterval(timerInterval);
                timerInterval = setInterval(() => {
                    if (isRunning) {
                        timerSeconds++;
                        updateTimerUI();
                    }
                }, 1000);

                document.getElementById('startBtn').classList.add('hidden');
                document.getElementById('pauseBtn').classList.remove('hidden');
                document.getElementById('completeBtn').classList.remove('hidden');
                document.getElementById('extBtn').classList.remove('hidden');
            }
        }

        async function handlePauseTask() {
            isRunning = false;
            await fetch('/api/tasks/pause', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: currentTaskId, accumulated_seconds: timerSeconds})
            });
            document.getElementById('pauseBtn').classList.add('hidden');
            document.getElementById('resumeBtn').classList.remove('hidden');
        }

        async function handleResumeTask() {
            isRunning = true;
            await fetch('/api/tasks/resume', {method: 'POST'});
            document.getElementById('resumeBtn').classList.add('hidden');
            document.getElementById('pauseBtn').classList.remove('hidden');
        }

        async function handleCompleteTask() {
            isRunning = false;
            clearInterval(timerInterval);
            await fetch('/api/tasks/complete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: currentTaskId, accumulated_seconds: timerSeconds})
            });
            
            alert('Task Completed Successfully!');
            document.getElementById('empCurrentTaskTitle').textContent = "No Task In Progress";
            timerSeconds = 0;
            updateTimerUI();
            
            document.getElementById('startBtn').classList.remove('hidden');
            document.getElementById('pauseBtn').classList.add('hidden');
            document.getElementById('resumeBtn').classList.add('hidden');
            document.getElementById('completeBtn').classList.add('hidden');
            document.getElementById('extBtn').classList.add('hidden');

            refreshEmployeeData();
        }

        // Modals
        function showAddEmployeeModal() { document.getElementById('addEmpModal').classList.remove('hidden'); }
        function showAssignTaskModal() { document.getElementById('assignTaskModal').classList.remove('hidden'); }
        function showExtensionModal() { document.getElementById('extensionModal').classList.remove('hidden'); }
        function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

        async function submitAddEmployee() {
            const name = document.getElementById('newEmpName').value;
            const emp_id = document.getElementById('newEmpId').value;
            const password = document.getElementById('newEmpPw').value;

            const res = await fetch('/api/employees', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, emp_id: parseInt(emp_id), password})
            });
            if (res.ok) {
                closeModal('addEmpModal');
                refreshManagerData();
            }
        }

        async function submitAssignTask() {
            const emp_id = document.getElementById('assignTargetEmp').value;
            const title = document.getElementById('assignTitle').value;
            const allocated_minutes = parseInt(document.getElementById('assignMins').value);

            const res = await fetch('/api/tasks/assign', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({emp_id: parseInt(emp_id), emp_name: "Staff", title, description: title, allocated_minutes})
            });
            if (res.ok) {
                closeModal('assignTaskModal');
                refreshManagerData();
            }
        }

        async function submitExtension() {
            const extra_minutes = parseInt(document.getElementById('extMins').value);
            const reason = document.getElementById('extReason').value;

            const res = await fetch('/api/tasks/extension', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({extra_minutes, reason})
            });
            if (res.ok) {
                alert('Extension request sent to manager feed.');
                closeModal('extensionModal');
            }
        }

        async function handleDeleteEmp(empId) {
            if (confirm(`Delete employee ID ${empId}?`)) {
                await fetch(`/api/employees/${empId}`, {method: 'DELETE'});
                refreshManagerData();
            }
        }

        async function handleResetPw(empId) {
            const newPw = prompt("Enter new password for employee:");
            if (newPw) {
                await fetch(`/api/employees/${empId}/reset-password`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({new_password: newPw})
                });
                alert("Password reset successfully.");
            }
        }
    </script>
</body>
</html>
"""
