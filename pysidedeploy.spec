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
icon = logo.png
input_file = pysidedeploy.spec
exec_directory = .

[python]

# python executable
python_path = C:\Users\mohit\AppData\Local\Programs\Python\Python313\python.exe

# python packages directory
packages_path = C:\Users\mohit\AppData\Local\Programs\Python\Python313\Lib\site-packages
packages = PySide6

[qt]

# qml files directory
qml_files = main.qml,EmployeeView.qml,ManagerView.qml

# excluded qml plugin modules
excluded_qml_plugins = QtCharts,QtSensors,QtWebEngine

# qt modules
modules = Core,Qml,Quick,QuickControls2,Widgets

# qt plugins
plugins = qmllint,qmltooling,scenegraph,styles,vectorimageformats

[nuitka]

# nuitka build mode (onefile / standalone)
mode = standalone

# extra nuitka options (automatic download prompt confirmation)
extra_args = --assume-yes-for-downloads --enable-plugin=pyside6

[android]

# path to android ndk
ndk_path = 

# path to android sdk
sdk_path = 

# android permissions required by your app
permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# package name
package_name = org.teampulse.app

[build]

# extra modules to include
modules = 

# extra data files to package
extra_data = main.qml,EmployeeView.qml,ManagerView.qml,logo.png,database_manager.py,models.py,backend.py

