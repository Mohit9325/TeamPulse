import os
import json
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ObjectProperty, ListProperty
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.metrics import dp
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from database_manager import DatabaseManager
from datetime import datetime

class TeamPulseEngine(EventDispatcher):
    def __init__(self, db_manager, **kwargs):
        self.register_event_type('on_activity_logged')
        self.register_event_type('on_employee_status_changed')
        self.register_event_type('on_employee_timer_updated')
        self.register_event_type('on_metrics_updated')
        self.register_event_type('on_employees_synced')
        self.register_event_type('on_activity_feed_changed')
        super().__init__(**kwargs)
        
        self.db = db_manager
        self.employees = {}
        self.db.signals.bind(
            on_employee_status_changed=self._on_db_users_updated,
            on_activity_feed_changed=self._on_db_activity_updated
        )
        Clock.schedule_interval(self._on_ui_tick, 1.0)
        
        # Initial boot fetch
        self.db._broadcast_employees()
        self.db._broadcast_activity()

    def _on_ui_tick(self, dt):
        for emp_id, emp_data in self.employees.items():
            if emp_data['status'] == 'Active' and emp_data['task'] != 'None':
                emp_data['acc_sec'] += 1
                self.db.update_user_status(emp_id, 'Active', emp_data['acc_sec'])
                
                allocated = emp_data.get('allocated_minutes', 0)
                if allocated > 0:
                    remaining = (allocated * 60) - emp_data['acc_sec']
                    if remaining <= 0:
                        task_id = self.db.get_active_task_id(emp_id)
                        if task_id:
                            self.db.end_task(task_id, emp_id, emp_data['acc_sec'], "Auto-completed (Time up)")
                            self.dispatch('on_employee_timer_updated', emp_id, "00:00:00")
                        continue
                    else:
                        time_str = self._format_time(remaining)
                else:
                    time_str = self._format_time(emp_data['acc_sec'])
                    
                self.dispatch('on_employee_timer_updated', emp_id, time_str)
            elif emp_data['status'] in ('On Break', 'Paused') and emp_data['task'] != 'None':
                allocated = emp_data.get('allocated_minutes', 0)
                if allocated > 0:
                    remaining = max(0, (allocated * 60) - emp_data['acc_sec'])
                    time_str = self._format_time(remaining)
                else:
                    time_str = self._format_time(emp_data['acc_sec'])
                self.dispatch('on_employee_timer_updated', emp_id, time_str)

    def _on_db_users_updated(self, instance, users_data):
        self.employees.clear()
        sync_list = []
        for user in users_data:
            emp_id = user['id']
            allocated = user.get('allocated_minutes', 0) or 0
            self.employees[emp_id] = {
                "name": user['name'],
                "status": user['status'],
                "task": user['current_task'],
                "acc_sec": user['acc_sec'],
                "completed_list": user['completed_list'],
                "role": user['role'],
                "department": user.get('department') or 'N/A',
                "allocated_minutes": allocated
            }
            if user['role'] != 'manager':
                sync_list.append(user)
            self.dispatch('on_employee_status_changed', emp_id, user['current_task'], user['status'], user['completed_list'])
            if allocated > 0:
                rem = max(0, (allocated * 60) - user['acc_sec'])
                t_display = self._format_time(rem)
            else:
                t_display = self._format_time(user['acc_sec'])
            self.dispatch('on_employee_timer_updated', emp_id, t_display)
        self.dispatch('on_employees_synced', sync_list)
        self._recalculate_metrics()

    def _on_db_activity_updated(self, instance, activity_data):
        self.dispatch('on_activity_feed_changed', activity_data)

    def _recalculate_metrics(self):
        emp_list = [e for e in self.employees.values() if e.get("role") != "manager"]
        active = sum(1 for e in emp_list if e.get("status") in ["Active", "in_progress", "In Progress"])
        paused = sum(1 for e in emp_list if e.get("status") in ["Paused", "on_break", "On Break", "Break"])
        total_completed = sum(len(e.get("completed_list", [])) for e in emp_list)
        self.dispatch('on_metrics_updated', active, paused, total_completed)

    def _format_time(self, seconds):
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def on_activity_logged(self, *args): pass
    def on_employee_status_changed(self, *args): pass
    def on_employee_timer_updated(self, *args): pass
    def on_metrics_updated(self, *args): pass
    def on_employees_synced(self, *args): pass
    def on_activity_feed_changed(self, *args): pass

# Custom Widget Models
class CorporateButton(Button):
    bg_color = ListProperty([0.827, 0.184, 0.184, 1])

class MetricCard(BoxLayout):
    label_text = StringProperty('')
    value_text = StringProperty('')
    accent = ListProperty([0.827, 0.184, 0.184, 1])

class EmployeeCard(BoxLayout):
    emp_id = NumericProperty(0)
    emp_name = StringProperty('')
    emp_status = StringProperty('Offline')
    emp_task = StringProperty('')
    emp_timer = StringProperty('')
    
    def status_color(self):
        if self.emp_status == 'Active':
            return [0.298, 0.686, 0.314, 1]
        elif self.emp_status in ('On Break', 'Paused'):
            return [1.0, 0.596, 0.0, 1]
        return [0.42, 0.447, 0.502, 1]

class ActivityItem(BoxLayout):
    message = StringProperty('')
    timestamp = StringProperty('')

class AssignedTaskItem(BoxLayout):
    title = StringProperty('')
    description = StringProperty('')
    allocated_time = NumericProperty(0)
    task_id = NumericProperty(0)
    
    def start_assigned_task(self):
        app = App.get_running_app()
        if hasattr(app, 'employee_screen'):
            app.employee_screen.start_assigned_task(self.task_id, self.allocated_time, self.title)

class CompletedTaskItem(BoxLayout):
    task_title = StringProperty('')
    task_duration = StringProperty('')
    task_date = StringProperty('')

# Popups
class CompletionNotesPopup(Popup):
    def do_complete(self, notes):
        app = App.get_running_app()
        app.employee_screen.execute_end_task(notes)
        self.dismiss()

class AddEmployeePopup(Popup):
    def do_add(self, name, username, department, password):
        if name and username and password:
            App.get_running_app().db.create_employee(name, username, password, department)
        self.dismiss()

class AssignTaskPopup(Popup):
    emp_id = NumericProperty(0)
    def do_assign(self, title, desc, minutes, priority="Medium"):
        print(f"[AssignTaskPopup] Assigning task to emp_id={self.emp_id}, Title='{title}', Desc='{desc}', Mins='{minutes}', Priority='{priority}'")
        if title:
            try:
                # Sanitize input
                cleaned_mins = str(minutes).strip().replace('\n', '')
                try:
                    mins = int(cleaned_mins) if cleaned_mins else 0
                except ValueError:
                    mins = 0
                
                app = App.get_running_app()
                app.db.assign_task(self.emp_id, title, desc, mins, priority)
                if app.sm.current == 'manager_dashboard':
                    app.manager_screen._load_all_assigned_tasks()
            except Exception as e:
                print(f"[AssignTaskPopup Error] {e}")
                from kivy.uix.label import Label
                Popup(title="Database Error", content=Label(text=str(e)), size_hint=(0.8, 0.4)).open()
        self.dismiss()

class EditTaskPopup(Popup):
    task_id = NumericProperty(0)
    emp_options = ListProperty(["Keep Current"])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = App.get_running_app()
        emps = app.db.get_all_employees()
        self.emp_options = ["Keep Current"] + [f"{e['id']} - {e['name']}" for e in emps]
        
    def do_save(self, title, desc, minutes, priority="Medium", reassign="Keep Current"):
        print(f"[EditTaskPopup] Saving task_id={self.task_id}, Title='{title}', Desc='{desc}', Mins='{minutes}', Priority='{priority}'")
        if title:
            try:
                # Sanitize input
                cleaned_mins = str(minutes).strip().replace('\n', '')
                try:
                    mins = int(cleaned_mins) if cleaned_mins else 0
                except ValueError:
                    mins = 0
                
                app = App.get_running_app()
                app.db.update_assigned_task(self.task_id, title, desc, mins, priority)
                
                if reassign != "Keep Current":
                    new_id = int(reassign.split(' - ')[0])
                    app.db.reassign_task(self.task_id, new_id)
                
                if hasattr(app, 'manager_screen') and app.sm.current == 'manager_dashboard':
                    app.manager_screen._load_all_assigned_tasks()
                if hasattr(app, 'employee_screen') and app.sm.current == 'employee_portal':
                    app.employee_screen._load_assigned_tasks()
                app.db._broadcast_employees()
            except Exception as e:
                print(f"[EditTaskPopup Error] {e}")
                from kivy.uix.label import Label
                Popup(title="Database Error", content=Label(text=str(e)), size_hint=(0.8, 0.4)).open()
        self.dismiss()

class ForgotPasswordPopup(Popup):
    def do_reset(self, username, new_password):
        if username and new_password:
            app = App.get_running_app()
            success = app.db.update_employee_password(username, new_password)
            if success:
                print(f"[ForgotPassword] Reset successful for {username}")
                from kivy.uix.label import Label
                Popup(title="Success", content=Label(text="Password reset successfully!"), size_hint=(0.8, 0.4)).open()
            else:
                print(f"[ForgotPassword] User {username} not found")
                from kivy.uix.label import Label
                Popup(title="Error", content=Label(text="User not found!"), size_hint=(0.8, 0.4)).open()
        self.dismiss()

class ForceStatusPopup(Popup):
    emp_id = NumericProperty(0)
    def set_status(self, new_status):
        app = App.get_running_app()
        app.db.force_employee_status(self.emp_id, new_status)
        self.dismiss()

    def reset_timer(self):
        app = App.get_running_app()
        app.db.reset_employee_timer(self.emp_id)
        self.dismiss()

class AdminUserItem(BoxLayout):
    emp_id = NumericProperty(0)
    username = StringProperty('')
    role = StringProperty('')

class ManagerTaskItem(BoxLayout):
    task_id = NumericProperty(0)
    emp_name = StringProperty('')
    title = StringProperty('')
    description = StringProperty('')
    allocated_time = NumericProperty(0)
    status = StringProperty('')

# Screens
class LoginScreen(Screen):
    error_text = StringProperty('')
    
    def do_login(self):
        username = self.ids.username_input.text
        password = self.ids.password_input.text
        remember = self.ids.remember_me.active
        app = App.get_running_app()
        user_info = app.db.authenticate_user(username, password)
        if user_info:
            user_id, role, name = user_info
            
            if remember:
                try:
                    with open('session.json', 'w') as f:
                        json.dump({'user_id': user_id, 'role': role, 'username': username}, f)
                except Exception as e:
                    print("Error saving session:", e)
                    
            if role in ('manager', 'admin'):
                app.sm.current = 'manager_dashboard'
            else:
                app.employee_screen.load_user(user_id)
                app.sm.current = 'employee_portal'
            self.ids.password_input.text = ''
        else:
            self.error_text = 'Invalid credentials.'

class EmployeeScreen(Screen):
    current_tab = NumericProperty(0)
    employee_name = StringProperty('')
    employee_id_str = StringProperty('')
    employee_department = StringProperty('')
    timer_text = StringProperty('00:00:00')
    has_active_task = BooleanProperty(False)
    is_paused = BooleanProperty(False)
    current_task_name = StringProperty('None')
    completed_count = StringProperty('0')
    avg_time_text = StringProperty('0m')
    adherence_text = StringProperty('0%')
    emp_id = NumericProperty(0)
    
    def on_pre_enter(self):
        self.current_tab = 0
        if self.emp_id:
            self.load_user(self.emp_id)

    def on_enter(self):
        from kivy.clock import Clock
        self.poll_event = Clock.schedule_interval(self._poll_employee_data, 2)

    def on_leave(self):
        if hasattr(self, 'poll_event') and self.poll_event:
            self.poll_event.cancel()

    def _poll_employee_data(self, dt):
        if self.emp_id:
            self._load_assigned_tasks()
            self._refresh_stats()
            self._update_ui_state()

    def on_current_tab(self, instance, value):
        if 'sm' in self.ids:
            self.ids.sm.current = 'dashboard' if value == 0 else 'profile'

    def load_user(self, emp_id):
        self.emp_id = emp_id
        app = App.get_running_app()
        if emp_id in app.engine.employees:
            emp = app.engine.employees[emp_id]
            self.employee_name = emp['name']
            self.employee_id_str = f"EMP-{emp_id:04d}"
            self.employee_department = emp.get('department') or 'N/A'
            self._update_ui_state()
        self._refresh_stats()
        self._load_assigned_tasks()

    def _load_assigned_tasks(self):
        app = App.get_running_app()
        tasks = app.db.get_pending_assigned_tasks(self.emp_id)
        if 'assigned_tasks_container' in self.ids:
            container = self.ids.assigned_tasks_container
            container.clear_widgets()
            for t in tasks:
                item = AssignedTaskItem(
                    title=t.get('title', 'Task'),
                    description=t.get('description', ''),
                    allocated_time=t.get('allocated_minutes', 0),
                    task_id=t.get('id', 0)
                )
                container.add_widget(item)

    def _update_ui_state(self):
        app = App.get_running_app()
        if self.emp_id in app.engine.employees:
            emp = app.engine.employees[self.emp_id]
            self.has_active_task = emp['status'] in ['Active', 'Paused', 'On Break'] and emp['task'] != 'None'
            self.is_paused = emp['status'] in ['Paused', 'On Break']
            self.current_task_name = emp['task']
            allocated = emp.get('allocated_minutes', 0)
            if allocated > 0:
                remaining = max(0, (allocated * 60) - emp['acc_sec'])
                self.timer_text = app.engine._format_time(remaining)
            else:
                self.timer_text = app.engine._format_time(emp['acc_sec'])

    def pause_task(self):
        App.get_running_app().db.update_user_status(self.emp_id, "On Break")
    
    def resume_task(self):
        App.get_running_app().db.update_user_status(self.emp_id, "Active")

    def open_end_task_popup(self):
        popup = CompletionNotesPopup()
        popup.open()

    def execute_end_task(self, notes="Completed"):
        app = App.get_running_app()
        sec = app.engine.employees[self.emp_id]["acc_sec"]
        task_id = app.db.get_active_task_id(self.emp_id)
        if task_id:
            app.db.end_task(task_id, self.emp_id, sec, notes)
        self._refresh_stats()
        self._load_assigned_tasks()

    def start_assigned_task(self, task_id, allocated_time, title):
        app = App.get_running_app()
        if self.has_active_task:
            self.execute_end_task("Ended to start new task")
        app.db.start_task(self.emp_id, title, allocated_minutes=allocated_time)
        
        import sqlite3
        with sqlite3.connect(app.db.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE assigned_tasks SET status='in_progress' WHERE id=?", (task_id,))
            conn.commit()
        
        self._load_assigned_tasks()

    def _refresh_stats(self):
        app = App.get_running_app()
        stats = app.db.get_productivity_stats(self.emp_id)
        self.completed_count = stats['total_completed']
        self.avg_time_text = stats['avg_time']
        self.adherence_text = stats['adherence']
        
        # Load completed tasks
        recent = app.db.get_recent_completed_tasks(self.emp_id, limit=5)
        if 'task_history_container' in self.ids:
            container = self.ids.task_history_container
            container.clear_widgets()
            for t in recent:
                item = CompletedTaskItem(
                    task_title=t.get('title', ''),
                    task_duration=t.get('duration', ''),
                    task_date=t.get('date', '')
                )
                container.add_widget(item)

class ManagerScreen(Screen):
    current_tab = NumericProperty(0)
    active_count = NumericProperty(0)
    break_count = NumericProperty(0)
    completed_count = NumericProperty(0)
    
    def on_pre_enter(self):
        self.current_tab = 0
        app = App.get_running_app()
        app.db._broadcast_employees()
        app.db._broadcast_activity()
        self._load_all_assigned_tasks()
        self._poll_dashboard_data(0)
        
    def on_enter(self):
        from kivy.clock import Clock
        self.poll_event = Clock.schedule_interval(self._poll_dashboard_data, 2)
        
    def on_leave(self):
        if hasattr(self, 'poll_event') and self.poll_event:
            self.poll_event.cancel()
            
    def _poll_dashboard_data(self, dt):
        app = App.get_running_app()
        self.active_count = app.db.get_active_employees_count()
        self.break_count = app.db.get_on_break_employees_count()
        self.completed_count = app.db.get_total_completed_tasks()
        app.db._broadcast_employees()
        self._load_all_assigned_tasks()
        
    def _load_all_assigned_tasks(self):
        app = App.get_running_app()
        tasks = app.db.get_all_assigned_tasks()
        container = self.ids.manager_assigned_tasks_container
        container.clear_widgets()
        for t in tasks:
            item = ManagerTaskItem(
                task_id=t.get('id', 0),
                emp_name=t.get('emp_name') or 'Unknown',
                title=t.get('title', 'Task'),
                description=t.get('description', ''),
                allocated_time=t.get('allocated_minutes', 0),
                status=t.get('status', 'pending')
            )
            container.add_widget(item)
            
    def on_current_tab(self, instance, value):
        if 'manager_sm' in self.ids:
            if value == 0:
                self.ids.manager_sm.current = 'team_status'
            elif value == 1:
                self.ids.manager_sm.current = 'task_management'
            elif value == 2:
                self.ids.manager_sm.current = 'system_logs'
            elif value == 3:
                self.ids.manager_sm.current = 'admin_control'

class TeamPulseApp(App):
    def build(self):
        self.db = DatabaseManager()
        self.engine = TeamPulseEngine(self.db)
        
        self.engine.bind(
            on_employee_timer_updated=self._on_timer_updated,
            on_employee_status_changed=self._on_status_changed,
            on_metrics_updated=self._on_metrics_updated,
            on_employees_synced=self._on_employees_synced,
            on_activity_feed_changed=self._on_activity_feed_changed
        )
        
        self.sm = ScreenManager()
        
        self.login_screen = LoginScreen(name='login_screen')
        self.employee_screen = EmployeeScreen(name='employee_portal')
        self.manager_screen = ManagerScreen(name='manager_dashboard')
        
        self.sm.add_widget(self.login_screen)
        self.sm.add_widget(self.employee_screen)
        self.sm.add_widget(self.manager_screen)
        
        # Auto-login if remember me session exists
        if os.path.exists('session.json'):
            try:
                with open('session.json', 'r') as f:
                    session = json.load(f)
                role = session.get('role')
                user_id = session.get('user_id')
                if role in ('manager', 'admin'):
                    self.sm.current = 'manager_dashboard'
                else:
                    self.employee_screen.load_user(user_id)
                    self.sm.current = 'employee_portal'
            except Exception as e:
                print("Error loading session:", e)
                
        return self.sm

    def logout(self):
        self.sm.current = 'login_screen'
        if os.path.exists('session.json'):
            try:
                os.remove('session.json')
            except:
                pass
        
    def open_forgot_password(self):
        ForgotPasswordPopup().open()
        
    def open_force_status_popup(self, emp_id):
        popup = ForceStatusPopup()
        popup.emp_id = emp_id
        popup.open()
        
    def export_logs(self):
        try:
            filepath = "activity_logs_export.csv"
            self.db.export_logs_to_file(filepath)
            print(f"[Export] Logs exported to {filepath}")
            from kivy.uix.label import Label
            Popup(title="Success", content=Label(text=f"Logs exported to {filepath}"), size_hint=(0.8, 0.4)).open()
        except Exception as e:
            print(f"[Export Error] {e}")
            from kivy.uix.label import Label
            Popup(title="Error", content=Label(text=str(e)), size_hint=(0.8, 0.4)).open()
        
    def open_add_user_popup(self):
        popup = AddEmployeePopup()
        popup.open()
        
    def assign_task(self, emp_id):
        popup = AssignTaskPopup()
        popup.emp_id = emp_id
        popup.open()
        
    def edit_assigned_task(self, task_id, title, desc, mins):
        popup = EditTaskPopup()
        popup.task_id = task_id
        popup.ids.task_title.text = title
        popup.ids.task_desc.text = desc
        popup.ids.task_mins.text = str(mins)
        popup.open()
        
    def force_complete_task(self, task_id):
        self.db.force_complete_task(task_id)
        if hasattr(self, 'manager_screen') and self.sm.current == 'manager_dashboard':
            self.manager_screen._load_all_assigned_tasks()
        if hasattr(self, 'employee_screen') and self.sm.current == 'employee_portal':
            self.employee_screen._load_assigned_tasks()
        self.db._broadcast_employees()

    def delete_assigned_task_manager(self, task_id):
        self.db.delete_assigned_task(task_id)
        if hasattr(self, 'manager_screen') and self.sm.current == 'manager_dashboard':
            self.manager_screen._load_all_assigned_tasks()
        if hasattr(self, 'employee_screen') and self.sm.current == 'employee_portal':
            self.employee_screen._load_assigned_tasks()
        self.db._broadcast_employees()
        
    def delete_employee(self, emp_id):
        self.db.delete_employee(emp_id)

    def _on_timer_updated(self, instance, emp_id, timer_text):
        if self.sm.current == 'employee_portal' and self.employee_screen.emp_id == emp_id:
            self.employee_screen.timer_text = timer_text
            
        # Update specific employee card on manager screen dynamically
        if hasattr(self, 'manager_screen') and 'employee_list' in self.manager_screen.ids:
            for card in self.manager_screen.ids.employee_list.children:
                if getattr(card, 'emp_id', None) == emp_id:
                    card.emp_timer = timer_text

    def _on_status_changed(self, instance, emp_id, task, status, completed_list):
        if self.sm.current == 'employee_portal' and self.employee_screen.emp_id == emp_id:
            self.employee_screen._update_ui_state()

    def _on_metrics_updated(self, instance, active, paused, completed):
        if hasattr(self, 'manager_screen'):
            self.manager_screen.active_count = active
            self.manager_screen.break_count = paused
            self.manager_screen.completed_count = completed

    def _on_employees_synced(self, instance, users_data):
        if not hasattr(self, 'manager_screen'):
            return
        if 'employee_list' in self.manager_screen.ids:
            emp_list = self.manager_screen.ids.employee_list
            emp_list.clear_widgets()
            for user in users_data:
                acc_sec = user['acc_sec']
                allocated = user.get('allocated_minutes', 0) or 0
                if allocated > 0:
                    rem = max(0, (allocated * 60) - acc_sec)
                    t_str = self.engine._format_time(rem)
                else:
                    t_str = self.engine._format_time(acc_sec)
                card = EmployeeCard(
                    emp_id=user['id'],
                    emp_name=user['name'],
                    emp_status=user.get('status', 'Offline'),
                    emp_task=user.get('current_task', 'None'),
                    emp_timer=t_str
                )
                emp_list.add_widget(card)
            
        if 'admin_user_list' in self.manager_screen.ids:
            admin_list = self.manager_screen.ids.admin_user_list
            admin_list.clear_widgets()
            all_emps = self.db.get_all_employees()
            for emp in all_emps:
                item = AdminUserItem(
                    emp_id=emp['id'],
                    username=emp['username'],
                    role=emp['role']
                )
                admin_list.add_widget(item)

    def _on_activity_feed_changed(self, instance, activity_data):
        if hasattr(self, 'manager_screen') and 'activity_feed' in self.manager_screen.ids:
            feed = self.manager_screen.ids.activity_feed
            feed.clear_widgets()
            for act in activity_data:
                item = ActivityItem(
                    message=act.get('message', ''),
                    timestamp=act.get('timestamp', '')
                )
                feed.add_widget(item)

if __name__ == '__main__':
    TeamPulseApp().run()
