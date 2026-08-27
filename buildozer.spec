[app]
title = TeamPulse
package.name = teampulse
package.domain = org.teampulse
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db
source.exclude_dirs = desktop_backup,.git,.github,TeamPulse.dist,build,dist,deployment,__pycache__,.buildozer
source.exclude_patterns = *_desktop.py,build_package.py,run_web_preview.py,web_app.py,replace_manager.py,init_db.py,backend.py,pysidedeploy.spec,main.spec,nuitka-crash-report.xml,*.whl,*.whl.1
version = 0.1
requirements = python3,kivy,pyjnius,sqlite3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, ACCESS_NETWORK_STATE, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.accept_sdk_license = True
android.api = 33
android.minapi = 24
p4a.branch = master
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 1
warn_on_root = 1
