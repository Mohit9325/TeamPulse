import subprocess
import sys
import shutil
from pathlib import Path

def build_application():
    print("=== TeamPulse Application Local Packaging Wrapper ===")
    project_dir = Path(__file__).parent.resolve()
    
    print(f"[*] Project Directory: {project_dir}")
    print("[*] Validating entry points and assets...")
    
    required_files = [
        "main.py",
        "main.qml",
        "EmployeeView.qml",
        "ManagerView.qml",
        "database_manager.py",
        "models.py",
        "backend.py",
        "logo.png",
        "firebase_credentials.json"
    ]
    
    missing = [f for f in required_files if not (project_dir / f).exists()]
    if missing:
        print(f"[!] Error: Missing required source files/assets: {missing}")
        sys.exit(1)
        
    print("[+] All entry points and assets validated.")
    print("[*] Invoking PySide6 deployment tool (pyside6-deploy)...")
    
    cmd = [
        "pyside6-deploy",
        "-c", str(project_dir / "pysidedeploy.spec"),
        "-f"
    ]
    
    try:
        res = subprocess.run(cmd, cwd=project_dir, check=True)
        print("[+] Packaging process executed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"[!] Build process returned exit code: {e.returncode}")
    except Exception as e:
        print(f"[!] Execution failed: {e}")

if __name__ == "__main__":
    build_application()
