import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material

Page {
    id: employeePage
    background: Rectangle {
        color: "#F5F5F5"
    }

    Material.theme: Material.Light
    Material.accent: Material.Blue

    header: ToolBar {
        Material.background: Material.Blue
        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            
            Label {
                text: "TeamPulse - Employee Portal"
                color: "white"
                font.pixelSize: 20
                font.bold: true
                Layout.fillWidth: true
            }

            ToolButton {
                text: "Log Out"
                font.pixelSize: 14
                Material.foreground: "white"
                onClicked: {
                    if (typeof authController !== "undefined") {
                        authController.logout()
                    }
                }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        clip: true

        ColumnLayout {
            width: parent.width
            spacing: 20
            
            Item { Layout.preferredHeight: 20 } // top padding

            // 1. Welcome Card
            Rectangle {
                Layout.fillWidth: true
                Layout.margins: 20
                Layout.preferredHeight: welcomeLayout.implicitHeight + 40
                color: "white"
                radius: 8
                border.color: "#E0E0E0"

                ColumnLayout {
                    id: welcomeLayout
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 15

                    RowLayout {
                        Layout.fillWidth: true
                        
                        Label {
                            text: "Welcome back, " + (employeeController.userName !== "" ? employeeController.userName : "Employee") + "!"
                            font.pixelSize: 24
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        Rectangle {
                            color: "#FF9800"
                            radius: 12
                            Layout.preferredHeight: 24
                            Layout.preferredWidth: streakLabel.implicitWidth + 20
                            
                            Label {
                                id: streakLabel
                                anchors.centerIn: parent
                                text: "🔥 " + employeeController.streak + " Day Streak"
                                font.pixelSize: 12
                                font.bold: true
                                color: "white"
                            }
                        }
                    }
                }
            }

            // 2. Attendance Card
            Rectangle {
                Layout.fillWidth: true
                Layout.margins: 20
                Layout.preferredHeight: attendanceLayout.implicitHeight + 40
                color: "white"
                radius: 8
                border.color: "#E0E0E0"

                ColumnLayout {
                    id: attendanceLayout
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 15

                    Label {
                        text: "Today's Attendance"
                        font.pixelSize: 18
                        font.bold: true
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 20

                        Button {
                            text: "Clock In"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            Material.background: "#4CAF50"
                            Material.foreground: "white"
                            font.bold: true
                            font.pixelSize: 16
                            enabled: employeeController.clockInTime === ""
                            onClicked: employeeController.clockIn()
                        }

                        Button {
                            text: "Clock Out"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 50
                            Material.background: "#F44336"
                            Material.foreground: "white"
                            font.bold: true
                            font.pixelSize: 16
                            enabled: employeeController.clockInTime !== "" && employeeController.clockOutTime === ""
                            onClicked: employeeController.clockOut()
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 20
                        Label {
                            text: "Clock In: " + (employeeController.clockInTime !== "" ? employeeController.clockInTime : "--")
                            color: "gray"
                            Layout.fillWidth: true
                        }
                        Label {
                            text: "Clock Out: " + (employeeController.clockOutTime !== "" ? employeeController.clockOutTime : "--")
                            color: "gray"
                            Layout.fillWidth: true
                        }
                    }
                }
            }

            Item { Layout.fillHeight: true } // bottom spacer
        }
    }
}
