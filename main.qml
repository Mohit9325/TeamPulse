import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material

// Root object to hold multiple windows
ApplicationWindow {
    id: window
    visible: true
    width: 400
    height: 850
    minimumWidth: 360
    maximumWidth: 500
    title: "TeamPulse Portal"
    
    // Global corporate theme properties
    QtObject {
        id: theme
        property color bgLight: "#F3F4F6"
        property color surfaceWhite: "#FFFFFF"
        property color brandRed: "#D32F2F"
        property color brandRedLight: "#FFEBEE"
        property color textDark: "#1F2937"
        property color textGray: "#6B7280"
        property color borderColor: "#E5E7EB"
        property string fontSans: "Segoe UI, Inter, Roboto, sans-serif"
    }
    
    color: theme.bgLight
    
    Material.theme: Material.Light
    Material.accent: theme.brandRed
    
    // Base font for the entire application
    font.family: "Segoe UI" // Fallback that is globally recognized

    StackView {
        id: stackView
        anchors.fill: parent
        initialItem: loginPage
    }

    // --- CUSTOM CORPORATE TEXT FIELD ---
    component CorporateTextField: TextField {
        id: control
        color: theme.textDark
        background: Rectangle {
            color: theme.surfaceWhite
            border.color: control.activeFocus ? theme.brandRed : theme.borderColor
            border.width: 1
            radius: 6
        }
    }

    // --- CUSTOM CORPORATE BUTTON ---
    component CorporateButton: Button {
        id: btn
        property color bgColor: theme.brandRed
        property color textColor: "#FFFFFF"
        contentItem: Text {
            text: btn.text
            font.bold: true
            color: btn.down ? Qt.darker(btn.textColor, 1.2) : btn.textColor
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            color: btn.down ? Qt.darker(btn.bgColor, 1.1) : (btn.hovered ? Qt.lighter(btn.bgColor, 1.1) : btn.bgColor)
            radius: 6
        }
    }

    // --- LOGIN SCREEN ---
    Component {
        id: loginPage
        Page {
            background: Rectangle { color: theme.bgLight }
            
            Image {
                anchors.fill: parent
                source: "file:logo.png"
                opacity: 0.15
                fillMode: Image.PreserveAspectFit
                z: 0
            }
            
            // Login Card
            Rectangle {
                id: loginCard
                z: 1
                width: 350
                height: 450
                anchors.centerIn: parent
                color: theme.surfaceWhite
                radius: 12
                border.color: theme.borderColor
                border.width: 1
                
                Column {
                    anchors.fill: parent
                    anchors.margins: 30
                    spacing: 20
                    
                    // Header Branding
                    Image {
                        source: "file:logo.png"
                        fillMode: Image.PreserveAspectFit
                        height: 50
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    
                    Text {
                        text: "TeamPulse"
                        font.pixelSize: 28
                        font.bold: true
                        color: theme.brandRed
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    
                    Text {
                        text: "Please log in to your account"
                        font.pixelSize: 13
                        color: theme.textGray
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                    
                    CorporateTextField {
                        id: usernameInput
                        placeholderText: "Username"
                        placeholderTextColor: theme.textGray
                        width: parent.width
                        Keys.onReturnPressed: loginButton.clicked()
                        Keys.onEnterPressed: loginButton.clicked()
                    }
                    
                    CorporateTextField {
                        id: passwordInput
                        placeholderText: "Password"
                        placeholderTextColor: theme.textGray
                        echoMode: showPasswordToggle.checked ? TextInput.Normal : TextInput.Password
                        width: parent.width
                        rightPadding: 40
                        Keys.onReturnPressed: loginButton.clicked()
                        Keys.onEnterPressed: loginButton.clicked()
                        
                        ToolButton {
                            id: showPasswordToggle
                            checkable: true
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            text: checked ? "🙈" : "👁️"
                            font.pixelSize: 16
                            background: Item {}
                        }
                    }
                    
                    // Options Row
                    Item {
                        width: parent.width
                        height: 30
                        CheckBox {
                            text: "Remember me"
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Text {
                            text: "Forgot Password?"
                            color: theme.brandRed
                            font.underline: true
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: forgotPasswordPopup.open()
                            }
                        }
                    }
                    
                    // Inline Error State
                    Rectangle {
                        id: errorBanner
                        visible: errorLabel.text !== ""
                        width: parent.width
                        height: 40
                        color: theme.brandRedLight
                        border.color: theme.brandRed
                        border.width: 1
                        radius: 6
                        
                        Item {
                            anchors.fill: parent
                            anchors.margins: 10
                            Text { 
                                id: errorLabel
                                text: "" 
                                color: theme.brandRed
                                font.bold: true
                                anchors.left: parent.left
                                anchors.right: errorCloseButton.left
                                anchors.verticalCenter: parent.verticalCenter
                                elide: Text.ElideRight
                            }
                            ToolButton {
                                id: errorCloseButton
                                text: "✕"
                                background: Item {}
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                onClicked: errorLabel.text = ""
                            }
                        }
                    }
                    
                    CorporateButton {
                        id: loginButton
                        text: "Log In"
                        width: parent.width
                        height: 44
                        onClicked: {
                            errorLabel.text = ""
                            authController.login(usernameInput.text, passwordInput.text)
                        }
                    }
                }
            }

            // Footer Info
            Row {
                z: 1
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottomMargin: 20
                spacing: 8
                
                Rectangle {
                    width: 8; height: 8; radius: 4
                    color: "#4CAF50"
                    anchors.verticalCenter: parent.verticalCenter
                }
                Text {
                    text: "v2.4.0 • Connected to Cloud"
                    color: theme.textGray
                    font.pixelSize: 12
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Connections {
                target: employeeController
                function onAutoPaused() {
                    globalToast.showMessage("Task auto-paused due to inactivity.");
                }
            }

            Connections {
                target: authController
                function onLoginResult(role, name, userId) {
                    if (role === "manager") {
                        stackView.push(managerDashboard)
                    } else {
                        employeeController.loadUser(userId)
                        stackView.push(employeeDashboard)
                    }
                }
                function onError(msg) { 
                    errorLabel.text = msg 
                }
            }
        }
    }

    // --- EMPLOYEE DASHBOARD ---
    Component {
        id: employeeDashboard
        Page {
            background: Rectangle { color: theme.bgLight }
            
            Image {
                anchors.fill: parent
                source: "file:logo.png"
                opacity: 0.15
                fillMode: Image.PreserveAspectFit
                z: 0
            }
            
            header: ToolBar {
                background: Rectangle { 
                    color: theme.surfaceWhite
                    border.color: theme.borderColor
                    border.width: 1
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 4
                    
                    ToolButton { 
                        text: "◁ Back"
                        contentItem: Text { text: parent.text; color: theme.textDark; font.bold: true }
                        onClicked: {
                            stackView.pop() 
                        }
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    Label { 
                        text: "Employee Portal"
                        font.bold: true
                        font.pixelSize: 16
                        color: theme.textDark
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    ToolButton { 
                        text: "Log Out"
                        contentItem: Text { text: parent.text; color: theme.brandRed; font.bold: true }
                        onClicked: {
                            stackView.pop(null) 
                        }
                    }
                }
            }
            
            ColumnLayout {
                z: 1
                anchors.fill: parent
                
                TabBar {
                    id: employeeTabBar
                    Layout.fillWidth: true
                    TabButton { text: "Dashboard" }
                    TabButton { text: "My Profile" }
                }
                
                StackLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: employeeTabBar.currentIndex
                    
                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 15
                
                Label {
                    text: employeeController.activeTimerText
                    font.pixelSize: 48
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                    color: employeeController.isTaskPaused ? theme.textGray : theme.brandRed
                }
                
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5
                    visible: employeeController.hasActiveTask
                    
                    Label { text: "Currently Active Task"; font.bold: true; font.pixelSize: 14; color: theme.textGray; Layout.alignment: Qt.AlignHCenter }
                    Label { text: employeeController.employeeStatus; font.bold: true; font.pixelSize: 18; color: theme.textDark; Layout.alignment: Qt.AlignHCenter }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    
                    CorporateButton {
                        text: employeeController.isTaskPaused ? "Resume Task" : "Pause Break"
                        Layout.fillWidth: true
                        visible: employeeController.hasActiveTask
                        bgColor: employeeController.isTaskPaused ? "#4CAF50" : "#FF9800"
                        onClicked: {
                            if (employeeController.isTaskPaused) employeeController.resumeTask()
                            else employeeController.pauseTask()
                        }
                    }
                    
                    CorporateButton {
                        text: "Request Extension"
                        Layout.fillWidth: true
                        visible: employeeController.hasActiveTask
                        bgColor: "#2196F3"
                        onClicked: requestExtensionPopup.open()
                    }
                    
                    CorporateButton {
                        text: "End Task"
                        Layout.fillWidth: true
                        bgColor: theme.brandRed
                        visible: employeeController.hasActiveTask
                        onClicked: completionNotesPopup.open()
                    }
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: theme.borderColor
                    Layout.topMargin: 10
                    Layout.bottomMargin: 10
                }
                
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 10
                    
                    Label {
                        text: "Manager Task Queue"
                        font.pixelSize: 20
                        font.bold: true
                        color: theme.brandRed
                    }
                    
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 10
                        model: employeeController.assignedTasksModel
                        
                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 100
                            color: theme.surfaceWhite
                            border.color: theme.borderColor
                            border.width: 1
                            radius: 8
                            
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 15
                                spacing: 15
                                
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Label { text: model.title; font.bold: true; font.pixelSize: 16; color: theme.textDark }
                                    Label { text: model.description; color: theme.textGray; font.pixelSize: 13; elide: Text.ElideRight; Layout.fillWidth: true }
                                    Label { text: "Allocated: " + model.allocated_time + " mins"; color: theme.brandRed; font.pixelSize: 12; font.bold: true }
                                }
                                
                                CorporateButton {
                                    text: "Start Task"
                                    bgColor: "#4CAF50"
                                    Layout.preferredWidth: 120
                                    Layout.preferredHeight: 36
                                    visible: !employeeController.hasActiveTask
                                    onClicked: employeeController.start_assigned_task(model.task_id, model.allocated_time, model.title)
                                }
                            }
                        }
                    }
                }
                    }
                    
                    // Profile Tab
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: availableWidth
                        clip: true
                        
                        ColumnLayout {
                            width: parent.width
                            spacing: 20
                            
                            // Extra top margin
                            Item { Layout.preferredHeight: 10 }
                            
                            // Header Section
                            ColumnLayout {
                                Layout.alignment: Qt.AlignHCenter
                                spacing: 10
                                
                                Rectangle {
                                    width: 80; height: 80
                                    radius: 40
                                    color: theme.brandRed
                                    Layout.alignment: Qt.AlignHCenter
                                    
                                    Label {
                                        text: employeeController.employeeName !== "" ? employeeController.employeeName.charAt(0).toUpperCase() : "U"
                                        color: "white"
                                        font.pixelSize: 36
                                        font.bold: true
                                        anchors.centerIn: parent
                                    }
                                }
                                
                                Label { text: employeeController.employeeName; font.pixelSize: 24; font.bold: true; color: theme.textDark; Layout.alignment: Qt.AlignHCenter }
                                Label { text: employeeController.employeeIdString; font.pixelSize: 14; color: theme.textGray; Layout.alignment: Qt.AlignHCenter }
                            }
                            
                            // Career & Stats Card
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredWidth: parent.width - 40
                                Layout.alignment: Qt.AlignHCenter
                                height: 100
                                radius: 12
                                color: theme.surfaceWhite
                                border.color: theme.borderColor
                                border.width: 1
                                
                                // Simple drop shadow effect using standard QML elements
                                Rectangle { anchors.fill: parent; anchors.margins: -1; anchors.topMargin: 2; z: -1; color: "#11000000"; radius: 12 }
                                
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Department"; font.pixelSize: 12; color: theme.textGray }
                                        Label { text: "Engineering"; font.pixelSize: 16; font.bold: true; color: theme.textDark }
                                    }
                                    Rectangle { width: 1; Layout.fillHeight: true; color: theme.borderColor }
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        Label { text: "Total Hours Logged"; font.pixelSize: 12; color: theme.textGray }
                                        Label { text: employeeController.totalHoursTodayText; font.pixelSize: 16; font.bold: true; color: theme.brandRed }
                                    }
                                }
                            }
                            
                            // Productivity Analytics Card
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredWidth: parent.width - 40
                                Layout.alignment: Qt.AlignHCenter
                                height: 110
                                radius: 12
                                color: theme.surfaceWhite
                                border.color: theme.borderColor
                                border.width: 1
                                
                                Rectangle { anchors.fill: parent; anchors.margins: -1; anchors.topMargin: 2; z: -1; color: "#11000000"; radius: 12 }
                                
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 15
                                    spacing: 8
                                    
                                    Label { text: "📊 Productivity Analytics"; font.bold: true; font.pixelSize: 14; color: theme.brandRed }
                                    
                                    RowLayout {
                                        Layout.fillWidth: true
                                        
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Label { text: "Completed"; font.pixelSize: 11; color: theme.textGray; Layout.alignment: Qt.AlignHCenter }
                                            Label { text: employeeController.completedTasksCount; font.pixelSize: 16; font.bold: true; color: theme.textDark; Layout.alignment: Qt.AlignHCenter }
                                        }
                                        Rectangle { width: 1; height: 30; color: theme.borderColor }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Label { text: "Avg Time"; font.pixelSize: 11; color: theme.textGray; Layout.alignment: Qt.AlignHCenter }
                                            Label { text: employeeController.avgTaskTimeText; font.pixelSize: 16; font.bold: true; color: theme.textDark; Layout.alignment: Qt.AlignHCenter }
                                        }
                                        Rectangle { width: 1; height: 30; color: theme.borderColor }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Label { text: "Adherence"; font.pixelSize: 11; color: theme.textGray; Layout.alignment: Qt.AlignHCenter }
                                            Label { text: employeeController.adherenceScoreText; font.pixelSize: 16; font.bold: true; color: "#4CAF50"; Layout.alignment: Qt.AlignHCenter }
                                        }
                                    }
                                }
                            }
                            
                            // Upcoming Tasks Card
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredWidth: parent.width - 40
                                Layout.alignment: Qt.AlignHCenter
                                implicitHeight: Math.max(120, upcomingTasksListView.contentHeight + 60)
                                radius: 12
                                color: theme.surfaceWhite
                                border.color: theme.borderColor
                                border.width: 1
                                
                                Rectangle { anchors.fill: parent; anchors.margins: -1; anchors.topMargin: 2; z: -1; color: "#11000000"; radius: 12 }
                                
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 15
                                    spacing: 10
                                    
                                    RowLayout {
                                        Label { text: "📅"; font.pixelSize: 16 }
                                        Label { text: "Upcoming Tasks"; font.bold: true; font.pixelSize: 16; color: theme.brandRed; Layout.fillWidth: true }
                                    }
                                    
                                    ListView {
                                        id: upcomingTasksListView
                                        Layout.fillWidth: true
                                        implicitHeight: contentHeight > 0 ? contentHeight : 60
                                        clip: true
                                        spacing: 8
                                        model: employeeController.assignedTasksModel
                                        delegate: Rectangle {
                                            width: ListView.view.width
                                            height: model.description && model.description !== "" ? 65 : 48
                                            color: theme.bgLight
                                            radius: 6
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 10
                                                spacing: 10
                                                ColumnLayout {
                                                    Layout.fillWidth: true
                                                    spacing: 2
                                                    Label { text: model.title; font.bold: true; font.pixelSize: 14; color: theme.textDark; Layout.fillWidth: true; elide: Text.ElideRight }
                                                    Label { text: model.description; font.pixelSize: 12; color: theme.textGray; Layout.fillWidth: true; elide: Text.ElideRight; visible: model.description && model.description !== "" }
                                                }
                                                Rectangle {
                                                    Layout.preferredWidth: 55
                                                    Layout.preferredHeight: 24
                                                    color: theme.brandRedLight
                                                    radius: 12
                                                    Label { text: model.allocated_time + "m"; anchors.centerIn: parent; font.pixelSize: 11; font.bold: true; color: theme.brandRed }
                                                }
                                                CorporateButton {
                                                    text: "Start"
                                                    bgColor: "#4CAF50"
                                                    Layout.preferredWidth: 60
                                                    Layout.preferredHeight: 28
                                                    visible: !employeeController.hasActiveTask
                                                    onClicked: employeeController.start_assigned_task(model.task_id, model.allocated_time, model.title)
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Task History Card
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredWidth: parent.width - 40
                                Layout.alignment: Qt.AlignHCenter
                                height: 200
                                radius: 12
                                color: theme.surfaceWhite
                                border.color: theme.borderColor
                                border.width: 1
                                
                                Rectangle { anchors.fill: parent; anchors.margins: -1; anchors.topMargin: 2; z: -1; color: "#11000000"; radius: 12 }
                                
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 15
                                    spacing: 10
                                    
                                    RowLayout {
                                        Label { text: "🕒"; font.pixelSize: 16 }
                                        Label { text: "Recent Task History"; font.bold: true; font.pixelSize: 16; color: theme.textDark; Layout.fillWidth: true }
                                    }
                                    
                                    ListView {
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        clip: true
                                        spacing: 10
                                        model: employeeController.recentTaskHistoryModel
                                        delegate: Rectangle {
                                            width: ListView.view.width
                                            height: 40
                                            color: "transparent"
                                            border.color: theme.borderColor
                                            border.width: 1
                                            radius: 6
                                            RowLayout {
                                                anchors.fill: parent
                                                anchors.margins: 10
                                                Label { text: model.taskType; font.bold: true; font.pixelSize: 13; color: theme.textDark; Layout.fillWidth: true }
                                                Label { text: model.date; font.pixelSize: 12; color: theme.textGray }
                                                Label { text: model.duration; font.bold: true; font.pixelSize: 13; color: theme.brandRed }
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Account Security Card
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredWidth: parent.width - 40
                                Layout.alignment: Qt.AlignHCenter
                                height: 260
                                radius: 12
                                color: theme.surfaceWhite
                                border.color: theme.borderColor
                                border.width: 1
                                
                                Rectangle { anchors.fill: parent; anchors.margins: -1; anchors.topMargin: 2; z: -1; color: "#11000000"; radius: 12 }
                                
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 20
                                    spacing: 15
                                    
                                    Label { text: "Account Security"; font.pixelSize: 16; font.bold: true; color: theme.textDark }
                                    
                                    CorporateTextField { id: currentPwInput; placeholderText: "Current Password"; echoMode: TextInput.Password; Layout.fillWidth: true }
                                    CorporateTextField { id: newPwInput; placeholderText: "New Password"; echoMode: TextInput.Password; Layout.fillWidth: true }
                                    CorporateTextField { id: confirmPwInput; placeholderText: "Confirm New Password"; echoMode: TextInput.Password; Layout.fillWidth: true }
                                    
                                    CorporateButton {
                                        text: "Update Password"
                                        Layout.fillWidth: true
                                        onClicked: {
                                            if (newPwInput.text !== confirmPwInput.text) {
                                                globalToast.showMessage("Passwords do not match!")
                                                return
                                            }
                                            var success = employeeController.update_employee_password(String(employeeController.emp_id), currentPwInput.text, newPwInput.text)
                                            if (success) {
                                                globalToast.showMessage("Password updated successfully.")
                                                currentPwInput.text = ""
                                                newPwInput.text = ""
                                                confirmPwInput.text = ""
                                            } else {
                                                globalToast.showMessage("Incorrect current password.")
                                            }
                                        }
                                    }
                                }
                            }
                            
                            Item { Layout.preferredHeight: 40 }
                        }
                    }
                }
            }
        }
    }

    // --- MANAGER DASHBOARD ---
    Component {
        id: managerDashboard
        Page {
            background: Rectangle { color: theme.bgLight }
            
            Image {
                anchors.fill: parent
                source: "file:logo.png"
                opacity: 0.15
                fillMode: Image.PreserveAspectFit
                z: 0
            }
            
            header: ToolBar {
                background: Rectangle { 
                    color: theme.surfaceWhite
                    border.color: theme.borderColor
                    border.width: 1
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 4
                    
                    ToolButton { 
                        text: "◁ Back"
                        contentItem: Text { text: parent.text; color: theme.textDark; font.bold: true }
                        onClicked: {
                            stackView.pop() 
                        }
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    Label { 
                        text: "Manager Dashboard"
                        font.bold: true
                        font.pixelSize: 16
                        color: theme.textDark
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    CorporateButton {
                        text: "Add Employee"
                        Layout.preferredHeight: 32
                        onClicked: addEmployeePopup.open()
                    }
                    
                    ToolButton { 
                        text: "Log Out"
                        contentItem: Text { text: parent.text; color: theme.brandRed; font.bold: true }
                        onClicked: {
                            stackView.pop(null) 
                        }
                    }
                }
            }

            ColumnLayout {


                z: 1


                anchors.fill: parent


                


                TabBar {


                    id: managerTabBar


                    Layout.fillWidth: true


                    TabButton { text: "Team Status" }


                    TabButton { text: "System Logs" }


                }


                


                StackLayout {


                    Layout.fillWidth: true


                    Layout.fillHeight: true


                    currentIndex: managerTabBar.currentIndex


                    


                    // Tab 1: Team Status


                    ColumnLayout {


                        Layout.fillWidth: true


                        Layout.fillHeight: true


                        spacing: 15


                        


                        // 1. Metric Cards


                        RowLayout {


                            Layout.fillWidth: true


                            spacing: 10


                            


                            // Active Panel


                            Rectangle {


                                Layout.fillWidth: true


                                Layout.preferredHeight: 70


                                color: theme.surfaceWhite


                                border.color: theme.borderColor


                                border.width: 1


                                radius: 8


                                MouseArea {


                                    id: ma1


                                    anchors.fill: parent


                                    onClicked: {


                                        detailPopup.titleText = "Active Employees"


                                        detailPopup.listModel = managerController.activeDetailsList


                                        detailPopup.open()


                                    }


                                }


                                ColumnLayout {


                                    anchors.centerIn: parent


                                    Label { text: managerController.activeNow; font.pixelSize: 24; font.bold: true; color: theme.brandRed; Layout.alignment: Qt.AlignHCenter }


                                    Label { text: "Active Now"; font.pixelSize: 12; color: theme.textGray; Layout.alignment: Qt.AlignHCenter }


                                }


                            }


                            


                            // Paused Panel


                            Rectangle {


                                Layout.fillWidth: true


                                Layout.preferredHeight: 70


                                color: theme.surfaceWhite


                                border.color: theme.borderColor


                                border.width: 1


                                radius: 8


                                MouseArea {


                                    id: ma2


                                    anchors.fill: parent


                                    onClicked: {


                                        detailPopup.titleText = "On Break"


                                        detailPopup.listModel = managerController.breakDetailsList


                                        detailPopup.open()


                                    }


                                }


                                ColumnLayout {


                                    anchors.centerIn: parent


                                    Label { text: managerController.onBreak; font.pixelSize: 24; font.bold: true; color: "#FF9800"; Layout.alignment: Qt.AlignHCenter }


                                    Label { text: "On Break"; font.pixelSize: 12; color: theme.textGray; Layout.alignment: Qt.AlignHCenter }


                                }


                            }


                            


                            // Completed Panel


                            Rectangle {


                                Layout.fillWidth: true


                                Layout.preferredHeight: 70


                                color: theme.surfaceWhite


                                border.color: theme.borderColor


                                border.width: 1


                                radius: 8


                                MouseArea {


                                    id: ma3


                                    anchors.fill: parent


                                    onClicked: {


                                        detailPopup.titleText = "Completed Today"


                                        detailPopup.listModel = managerController.completedDetailsList


                                        detailPopup.open()


                                    }


                                }


                                ColumnLayout {


                                    anchors.centerIn: parent


                                    Label { text: managerController.completedToday; font.pixelSize: 24; font.bold: true; color: "#4CAF50"; Layout.alignment: Qt.AlignHCenter }


                                    Label { text: "Completed"; font.pixelSize: 12; color: theme.textGray; Layout.alignment: Qt.AlignHCenter }


                                }


                            }


                        }


                        


                        // Live Employee Grid


                        ColumnLayout {


                            Layout.fillWidth: true


                            Layout.fillHeight: true


                            spacing: 10


                            


                            Label { text: "Live Employee Status"; font.pixelSize: 16; font.bold: true; color: theme.textDark }


                            


                            CorporateTextField {


                                id: searchEmployees


                                placeholderText: "Search employees..."


                                Layout.fillWidth: true


                                onTextChanged: managerController.employeeListModel.filter_employees(text)


                            }


                            


                            ListView {


                                Layout.fillWidth: true


                                Layout.fillHeight: true


                                clip: true


                                spacing: 10


                                model: managerController.employeeListModel


                                


                                delegate: Rectangle {


                                    width: ListView.view.width


                                    height: 120


                                    color: theme.surfaceWhite


                                    border.color: theme.borderColor


                                    border.width: 1


                                    radius: 8


                                    


                                    RowLayout {


                                        anchors.fill: parent


                                        anchors.margins: 10


                                        spacing: 10


                                        


                                        Rectangle {


                                            Layout.preferredWidth: 10


                                            Layout.preferredHeight: 10


                                            radius: 5


                                            color: model.status === "Active" ? theme.brandRed : (model.status === "Paused" ? "#FF9800" : theme.textGray)


                                        }


                                        


                                        ColumnLayout {


                                            Layout.fillWidth: true


                                            Label { text: model.name; font.bold: true; font.pixelSize: 16; color: theme.textDark; Layout.fillWidth: true; wrapMode: Text.Wrap }


                                            Label { text: model.currentTask; color: theme.textGray; font.pixelSize: 14; Layout.fillWidth: true; wrapMode: Text.Wrap }


                                            Label { 


                                                text: "Completed: " + model.completedTasksString


                                                color: theme.textGray


                                                font.pixelSize: 12


                                                Layout.fillWidth: true


                                            }


                                        }


                                        


                                        Label { 


                                            text: model.timer


                                            font.pixelSize: 16


                                            font.bold: true


                                            color: model.status === "Active" ? theme.brandRed : theme.textGray


                                        }


                                        


                                        ColumnLayout {


                                            Button {


                                                text: "Assign Task"


                                                Layout.preferredWidth: 80


                                                Layout.preferredHeight: 30


                                                background: Rectangle { color: "#2196F3"; radius: 4 }


                                                contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 10; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }


                                                onClicked: {


                                                    managerController.fetch_employee_history(model.emp_id)


                                                    employeeHistoryPopup.empName = model.name


                                                    employeeHistoryPopup.empId = String(model.emp_id)


                                                    employeeHistoryPopup.open()


                                                }


                                            }


                                            Button {


                                                text: "Reset PW"


                                                visible: model.resetRequested


                                                Layout.preferredWidth: 80


                                                Layout.preferredHeight: 30


                                                background: Rectangle { color: theme.brandRed; radius: 4 }


                                                contentItem: Text { text: parent.text; color: "white"; font.pixelSize: 10; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }


                                                onClicked: {


                                                    managerResetPopup.empId = String(model.emp_id)


                                                    managerResetPopup.open()


                                                }


                                            }


                                            Button {


                                                text: "Delete"


                                                Layout.preferredWidth: 80


                                                Layout.preferredHeight: 30


                                                background: Rectangle { color: "transparent"; border.color: theme.brandRedLight; border.width: 1; radius: 4 }


                                                contentItem: Text { text: parent.text; color: theme.brandRed; font.pixelSize: 11; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }


                                                onClicked: {


                                                    deleteEmployeePopup.empId = String(model.emp_id)


                                                    deleteEmployeePopup.empName = model.name


                                                    deleteEmployeePopup.open()


                                                }


                                            }


                                        }


                                    }


                                }


                            }


                        }


                    }


                    


                    // Tab 2: System Logs


                    Rectangle {


                        Layout.fillWidth: true


                        Layout.fillHeight: true


                        color: "#F9FAFB"


                        


                        ColumnLayout {


                            anchors.fill: parent


                            anchors.margins: 10


                            


                            RowLayout {


                                Layout.fillWidth: true


                                Label { text: "System Logs"; font.pixelSize: 14; font.bold: true; color: theme.textDark; Layout.fillWidth: true }


                                CorporateButton {


                                    text: "Export Logs"


                                    Layout.preferredHeight: 28


                                    Layout.preferredWidth: 100


                                    onClicked: {


                                        var path = managerController.export_logs()


                                        globalToast.showMessage("Logs exported to: " + path)


                                    }


                                }


                            }


                            


                            RowLayout {


                                Layout.fillWidth: true


                                spacing: 5


                                CorporateButton { text: "All"; Layout.preferredHeight: 24; onClicked: managerController.activityFeedModel.filterLogs("All") }


                                CorporateButton { text: "Tasks"; Layout.preferredHeight: 24; bgColor: theme.textGray; onClicked: managerController.activityFeedModel.filterLogs("Tasks") }


                                CorporateButton { text: "Admin"; Layout.preferredHeight: 24; bgColor: theme.brandRed; onClicked: managerController.activityFeedModel.filterLogs("Admin Actions") }


                            }


                            


                            ListView {


                                Layout.fillWidth: true


                                Layout.fillHeight: true


                                clip: true


                                spacing: 5


                                model: managerController.activityFeedModel


                                


                                onCountChanged: {


                                    if (count > 0) {


                                        positionViewAtEnd()


                                    }


                                }


                                


                                delegate: RowLayout {


                                    width: ListView.view.width


                                    Label { text: model.timestamp; color: theme.textGray; font.pixelSize: 12; Layout.preferredWidth: 60 }


                                    Label { 


                                        text: model.eventText


                                        font.pixelSize: 13


                                        color: theme.textDark


                                        Layout.fillWidth: true


                                        wrapMode: Text.WrapAnywhere 


                                    }


                                }


                            }


                        }


                    }


                }


            }


            


            // --- DETAIL POPUP ---
            Popup {
                id: detailPopup
                anchors.centerIn: parent
                width: parent.width * 0.9
                height: parent.height * 0.6
                modal: true
                focus: true
                padding: 15
                
                property string titleText: ""
                property var listModel: []
                
                background: Rectangle {
                    color: theme.surfaceWhite
                    border.color: theme.borderColor
                    border.width: 1
                    radius: 12
                }
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 15
                    
                    Label {
                        text: detailPopup.titleText
                        font.pixelSize: 18
                        font.bold: true
                        color: theme.textDark
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: detailPopup.listModel
                        spacing: 8
                        
                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 50
                            color: theme.bgLight
                            border.color: theme.borderColor
                            border.width: 1
                            radius: 6
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 5
                                Label { text: modelData.title; font.bold: true; font.pixelSize: 14; color: theme.textDark }
                                Label { text: modelData.subtitle; color: theme.textGray; font.pixelSize: 12 }
                            }
                        }
                    }
                    
                    CorporateButton {
                        text: "Close"
                        Layout.alignment: Qt.AlignHCenter
                        onClicked: detailPopup.close()
                    }
                }
            }
            
            // --- ADD EMPLOYEE POPUP ---
            Popup {
                id: addEmployeePopup
                anchors.centerIn: parent
                width: 400
                height: 350
                modal: true
                focus: true
                dim: true
                
                background: Rectangle {
                    color: theme.surfaceWhite
                    border.color: theme.borderColor
                    border.width: 1
                    radius: 12
                }
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 25
                    spacing: 15
                    
                    Label {
                        text: "Add New Employee"
                        font.pixelSize: 20
                        font.bold: true
                        color: theme.brandRed
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    CorporateTextField {
                        id: newEmpName
                        placeholderText: "Full Name"
                        Layout.fillWidth: true
                    }
                    
                    CorporateTextField {
                        id: newEmpId
                        placeholderText: "Employee ID (Username)"
                        Layout.fillWidth: true
                    }
                    
                    CorporateTextField {
                        id: newEmpPassword
                        placeholderText: "Password"
                        echoMode: TextInput.Password
                        Layout.fillWidth: true
                    }
                    
                    Item { Layout.fillHeight: true }
                    
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        CorporateButton {
                            text: "Cancel"
                            Layout.fillWidth: true
                            bgColor: theme.textGray
                            onClicked: addEmployeePopup.close()
                        }
                        
                        CorporateButton {
                            text: "Save Employee"
                            Layout.fillWidth: true
                            onClicked: {
                                if (newEmpName.text !== "" && newEmpId.text !== "" && newEmpPassword.text !== "") {
                                    managerController.create_employee(newEmpName.text, newEmpId.text, newEmpPassword.text)
                                    newEmpName.text = ""
                                    newEmpId.text = ""
                                    newEmpPassword.text = ""
                                    addEmployeePopup.close()
                                    globalToast.showMessage("Employee added successfully!")
                                }
                            }
                        }
                    }
                }
            }
            
            // --- DELETE EMPLOYEE POPUP ---
            Popup {
                id: deleteEmployeePopup
                property string empId: ""
                property string empName: ""
                
                anchors.centerIn: parent
                width: Math.min(350, parent.width - 20)
                height: 200
                modal: true
                focus: true
                dim: true
                
                background: Rectangle {
                    color: theme.surfaceWhite
                    border.color: theme.borderColor
                    border.width: 1
                    radius: 12
                }
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 25
                    spacing: 15
                    
                    Label {
                        text: "Confirm Deletion"
                        font.pixelSize: 18
                        font.bold: true
                        color: theme.brandRed
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Label {
                        text: "Are you sure you want to permanently remove " + deleteEmployeePopup.empName + "?"
                        color: theme.textDark
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        horizontalAlignment: Qt.AlignHCenter
                    }
                    
                    Item { Layout.fillHeight: true }
                    
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        
                        CorporateButton {
                            text: "Cancel"
                            Layout.fillWidth: true
                            bgColor: theme.textGray
                            onClicked: deleteEmployeePopup.close()
                        }
                        
                        CorporateButton {
                            text: "Delete"
                            Layout.fillWidth: true
                            onClicked: {
                                managerController.delete_employee(deleteEmployeePopup.empId)
                                deleteEmployeePopup.close()
                                globalToast.showMessage("Employee deleted.")
                            }
                        }
                    }
                }
            }

            // --- EMPLOYEE HISTORY POPUP ---
            Popup {
                id: employeeHistoryPopup
                property string empName: ""
                property string empId: ""
                anchors.centerIn: parent
                width: Math.min(400, parent.width - 40)
                height: Math.min(600, parent.height - 40)
                modal: true
                focus: true
                dim: true
                
                background: Rectangle {
                    color: theme.surfaceWhite
                    border.color: theme.borderColor
                    border.width: 1
                    radius: 12
                }
                
                ScrollView {

                
                    anchors.fill: parent

                
                    clip: true

                
                    contentWidth: parent.width

                
                    

                
                    ColumnLayout {

                
                        width: parent.width

                
                        spacing: 15

                
                        

                
                        RowLayout {

                
                            Layout.fillWidth: true

                
                            Layout.margins: 15

                
                            Label {

                
                                text: employeeHistoryPopup.empName + "'s Task History"

                
                                font.pixelSize: 18

                
                                font.bold: true

                
                                color: theme.brandRed

                
                                Layout.fillWidth: true

                
                            }

                
                            ToolButton {

                
                                text: "✕"

                
                                onClicked: employeeHistoryPopup.close()

                
                            }

                
                        }

                
                

                
                        // Assign New Task Section

                
                        Rectangle {

                
                            Layout.fillWidth: true

                
                            Layout.margins: 15

                
                            Layout.preferredHeight: 220

                
                            color: "transparent"

                
                            

                
                            ColumnLayout {

                
                                anchors.fill: parent

                
                                anchors.margins: 5

                
                                spacing: 12

                
                                

                
                                Label { text: "Assign New Task"; font.bold: true; font.pixelSize: 14; color: theme.brandRed }

                
                                

                
                                CorporateTextField { 

                
                                    id: assignTitleInput

                
                                    placeholderText: "Task Title (e.g. Q3 Budget Review)"

                
                                    Layout.fillWidth: true 

                
                                    background: Rectangle { color: theme.surfaceWhite; border.color: "transparent"; border.width: 0; Rectangle { width: parent.width; height: 1; color: theme.borderColor; anchors.bottom: parent.bottom } }

                
                                }

                
                                

                
                                CorporateTextField { 

                
                                    id: assignDescInput

                
                                    placeholderText: "Description"

                
                                    Layout.fillWidth: true 

                
                                    background: Rectangle { color: theme.surfaceWhite; border.color: "transparent"; border.width: 0; Rectangle { width: parent.width; height: 1; color: theme.borderColor; anchors.bottom: parent.bottom } }

                
                                }

                
                                

                
                                RowLayout {

                
                                    Layout.fillWidth: true

                
                                    spacing: 15

                
                                    Label { text: "Allocated Time (Minutes):"; color: theme.textGray; font.pixelSize: 13 }

                
                                    SpinBox {

                
                                        id: assignMinutesInput

                
                                        from: 5

                
                                        to: 480

                
                                        stepSize: 5

                
                                        value: 45

                
                                        editable: true

                
                                    }

                
                                }

                
                                CorporateButton {

                
                                    text: "Assign Task"

                
                                    Layout.fillWidth: true

                
                                    onClicked: {

                
                                        if (assignTitleInput.text.trim() === "") {

                
                                            globalToast.showMessage("Task title is required.")

                
                                            return

                
                                        }

                
                                        managerController.assign_task(employeeHistoryPopup.empId, assignTitleInput.text, assignDescInput.text, assignMinutesInput.value)
                                        managerController.fetch_employee_history(employeeHistoryPopup.empId)
                                        assignTitleInput.text = ""
                                        assignDescInput.text = ""
                                        assignMinutesInput.value = 45
                                        globalToast.showMessage("Task assigned successfully!")

                
                                    }

                
                                }

                
                            }

                
                        }

                
                        

                
                        Label { 

                
                            text: "Pending / Assigned Tasks"

                
                            font.bold: true

                
                            font.pixelSize: 16

                
                            color: theme.textDark

                
                            Layout.topMargin: 10

                
                            Layout.leftMargin: 15

                
                        }

                
                        

                
                        ListView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.max(100, contentHeight)
                            clip: true
                            spacing: 8
                            Layout.margins: 15
                            model: managerController.managerPendingTasksModel
                            
                            delegate: Rectangle {
                                width: ListView.view.width
                                height: model.description && model.description !== "" ? 85 : 65
                                color: theme.surfaceWhite
                                border.color: theme.borderColor
                                border.width: 1
                                radius: 8
                                
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 10
                                    
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 2
                                        Label { text: model.title; font.bold: true; font.pixelSize: 14; color: theme.textDark; Layout.fillWidth: true; elide: Text.ElideRight }
                                        Label { text: model.description; font.pixelSize: 12; color: theme.textGray; Layout.fillWidth: true; elide: Text.ElideRight; visible: model.description && model.description !== "" }
                                        Label { text: "Allocated: " + model.allocated_time + " mins"; color: theme.brandRed; font.pixelSize: 11; font.bold: true }
                                    }
                                    
                                    Button {
                                        text: "Delete"
                                        Layout.preferredWidth: 60
                                        Layout.preferredHeight: 28
                                        background: Rectangle { color: "transparent"; border.color: theme.brandRedLight; border.width: 1; radius: 4 }
                                        contentItem: Text { text: parent.text; color: theme.brandRed; font.pixelSize: 11; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                    }
                                }
                            }
                        }

                
                

                
                        Label { 

                
                            text: "Completed Tasks History"

                
                            font.bold: true

                
                            font.pixelSize: 16

                
                            color: theme.textDark

                
                            Layout.topMargin: 10

                
                            Layout.leftMargin: 15

                
                        }

                
                        

                
                        ListView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.max(100, contentHeight)
                            clip: true
                            spacing: 8
                            Layout.margins: 15
                            model: managerController.managerCompletedTasksModel
                            
                            delegate: Rectangle {
                                width: ListView.view.width
                                height: 50
                                color: index % 2 === 0 ? "transparent" : theme.bgLight
                                radius: 6
                                
                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 10
                                    
                                    Label { text: "✅"; font.pixelSize: 14 }
                                    Label { text: model.title !== undefined && model.title !== "" ? model.title : model.taskType; font.bold: true; font.pixelSize: 14; color: theme.textDark; Layout.fillWidth: true; elide: Text.ElideRight }
                                    Label { text: model.completion_time !== undefined && model.completion_time !== "" ? model.completion_time : model.date; color: theme.textGray; font.pixelSize: 12; Layout.preferredWidth: 80 }
                                    Label { text: model.duration; font.bold: true; font.pixelSize: 13; color: theme.brandRed }
                                }
                            }
                        }



                
                        Item { Layout.preferredHeight: 20 }

                
                    }

                }
            }
        }
    }
    // --- FORGOT PASSWORD POPUP ---
    Popup {
        id: forgotPasswordPopup
        anchors.centerIn: parent
        width: 300
        height: 200
        modal: true
        focus: true
        dim: true
        background: Rectangle { color: theme.surfaceWhite; border.color: theme.borderColor; border.width: 1; radius: 8 }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 15
            Label { text: "Forgot Password"; font.bold: true; font.pixelSize: 16; color: theme.textDark; Layout.alignment: Qt.AlignHCenter }
            CorporateTextField { id: resetEmpIdInput; placeholderText: "Employee ID"; Layout.fillWidth: true }
            CorporateButton {
                text: "Request Reset"
                Layout.fillWidth: true
                onClicked: {
                    authController.request_password_reset(resetEmpIdInput.text)
                    resetEmpIdInput.text = ""
                    forgotPasswordPopup.close()
                    globalToast.showMessage("Reset request sent to Manager.")
                }
            }
        }
    }
    
    // --- TASK COMPLETION NOTES POPUP ---
    Popup {
        id: completionNotesPopup
        anchors.centerIn: parent
        width: Math.min(350, parent.width - 40)
        height: 220
        modal: true
        focus: true
        dim: true
        background: Rectangle { color: theme.surfaceWhite; border.color: theme.borderColor; border.width: 1; radius: 10 }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            Label { text: "Task Completion Summary"; font.bold: true; font.pixelSize: 16; color: theme.brandRed; Layout.alignment: Qt.AlignHCenter }
            CorporateTextField {
                id: completionNotesInput
                placeholderText: "Notes / Summary (e.g. Completed unit tests)"
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                CorporateButton {
                    text: "Cancel"
                    Layout.fillWidth: true
                    bgColor: theme.textGray
                    onClicked: completionNotesPopup.close()
                }
                CorporateButton {
                    text: "Submit & Finish"
                    Layout.fillWidth: true
                    bgColor: "#4CAF50"
                    onClicked: {
                        var notesText = completionNotesInput.text.trim() === "" ? "Completed" : completionNotesInput.text.trim()
                        employeeController.complete_task_with_notes(notesText)
                        completionNotesInput.text = ""
                        completionNotesPopup.close()
                        globalToast.showMessage("Task marked as completed!")
                    }
                }
            }
        }
    }

    // --- REQUEST EXTENSION POPUP ---
    Popup {
        id: requestExtensionPopup
        anchors.centerIn: parent
        width: Math.min(350, parent.width - 40)
        height: 250
        modal: true
        focus: true
        dim: true
        background: Rectangle { color: theme.surfaceWhite; border.color: theme.borderColor; border.width: 1; radius: 10 }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            Label { text: "Request Time Extension"; font.bold: true; font.pixelSize: 16; color: theme.brandRed; Layout.alignment: Qt.AlignHCenter }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Label { text: "Extra Minutes:"; color: theme.textGray; font.pixelSize: 13 }
                SpinBox {
                    id: extensionMinutesInput
                    from: 5
                    to: 120
                    stepSize: 5
                    value: 15
                    editable: true
                }
            }
            CorporateTextField {
                id: extensionReasonInput
                placeholderText: "Reason for extra time (e.g. unexpected bug)"
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                CorporateButton {
                    text: "Cancel"
                    Layout.fillWidth: true
                    bgColor: theme.textGray
                    onClicked: requestExtensionPopup.close()
                }
                CorporateButton {
                    text: "Send Request"
                    Layout.fillWidth: true
                    bgColor: "#2196F3"
                    onClicked: {
                        employeeController.request_task_extension(extensionMinutesInput.value, extensionReasonInput.text)
                        extensionReasonInput.text = ""
                        requestExtensionPopup.close()
                        globalToast.showMessage("Extension request sent to Manager!")
                    }
                }
            }
        }
    }

    // --- MANAGER RESET POPUP ---
    Popup {
        id: managerResetPopup
        property string empId: ""
        anchors.centerIn: parent
        width: 300
        height: 200
        modal: true
        focus: true
        dim: true
        background: Rectangle { color: theme.surfaceWhite; border.color: theme.borderColor; border.width: 1; radius: 8 }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 15
            Label { text: "Reset Password"; font.bold: true; font.pixelSize: 16; color: theme.textDark; Layout.alignment: Qt.AlignHCenter }
            CorporateTextField { id: resetNewPwInput; placeholderText: "New Password"; echoMode: TextInput.Password; Layout.fillWidth: true }
            CorporateButton {
                text: "Save New Password"
                Layout.fillWidth: true
                onClicked: {
                    managerController.reset_employee_password(managerResetPopup.empId, resetNewPwInput.text)
                    resetNewPwInput.text = ""
                    managerResetPopup.close()
                    globalToast.showMessage("Password has been reset.")
                }
            }
        }
    }

    // --- GLOBAL TOAST COMPONENT ---
    Popup {
        id: globalToast
        width: 300
        height: 50
        x: (window.width - width) / 2
        y: window.height - height - 20
        modal: false
        focus: false
        closePolicy: Popup.NoAutoClose
        
        background: Rectangle {
            color: theme.brandRed
            radius: 8
            border.color: theme.brandRedLight
            border.width: 1
        }
        
        Label {
            id: toastLabel
            text: ""
            color: theme.surfaceWhite
            font.bold: true
            anchors.centerIn: parent
        }
        
        Timer {
            id: toastTimer
            interval: 3000
            onTriggered: globalToast.close()
        }
        
        enter: Transition {
            NumberAnimation { property: "y"; from: window.height; to: window.height - globalToast.height - 20; duration: 300; easing.type: Easing.OutBack }
            NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: 300 }
        }
        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; duration: 300 }
        }
        
        function showMessage(msg) {
            toastLabel.text = msg
            globalToast.open()
            toastTimer.restart()
        }
    }
}
