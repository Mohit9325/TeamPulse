[app]
# title of your application
title = TeamPulse
# project name
project_name = teampulse
# app source directory
project_dir = .
# application entry point
entry_point = main.py
# icon path
icon = 
input_file = pysidedeploy.spec
exec_directory = .

[python]
# python executable
python_path = C:\Users\mohit\AppData\Local\Programs\Python\Python313\python.exe
# python packages directory
packages_path = C:\Users\mohit\AppData\Local\Programs\Python\Python313\Lib\site-packages
packages = PySide6, firebase_admin

[qt]
# qml files directory
qml_files = main.qml
# excluded qml plugin modules
excluded_qml_plugins = 
# qt modules
modules = Core, Gui, Qml, Quick, Controls
# qt plugins
plugins = 

[nuitka]
# nuitka build mode (onefile / standalone)
mode = onefile
# extra nuitka options (automatic download prompt confirmation)
extra_args = --assume-yes-for-downloads

[android]
# path to android ndk
ndk_path = 
# path to android sdk
sdk_path = 
# android permissions required by your app
permissions = INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION
# package name
package_name = org.teampulse.app

[build]
# extra modules to include
modules = 
# extra data files to package
extra_data = main.qml, database_manager.py, models.py
