import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Controls.Material

Page {
    id: managerPage
    background: Rectangle { color: "#F5F5F5" }

    Material.theme: Material.Light
    Material.accent: Material.Teal

    // Top Toolbar
    header: ToolBar {
        Material.background: Material.Teal
        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            
            Label {
                text: "Manager Dashboard"
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

    SwipeView {
        id: swipeView
        anchors.fill: parent
        currentIndex: tabBar.currentIndex

        // Tab 1: Live Activity
        Page {
            background: Item {}
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20
                
                Label {
                    text: "Live Activity"
                    font.pixelSize: 22
                    font.bold: true
                }
                
                ListView {
                    id: liveTasksList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 10
                    
                    // We bind the model dynamically
                    model: []
                    
                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 70
                        radius: 8
                        color: "white"
                        border.color: "#E0E0E0"
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            
                            ColumnLayout {
                                Layout.fillWidth: true
                                Label { text: modelData.emp_name; font.bold: true; font.pixelSize: 16 }
                                Label { text: modelData.task_name; color: "gray"; font.pixelSize: 14 }
                            }
                            
                            Rectangle {
                                color: "#2196F3"
                                radius: 4
                                width: 80
                                height: 24
                                Label {
                                    anchors.centerIn: parent
                                    text: "In Progress"
                                    color: "white"
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                            }
                        }
                    }
                }
            }
            
            Component.onCompleted: {
                if (typeof managerController !== "undefined") {
                    liveTasksList.model = managerController.getLiveTasks()
                }
            }
        }

        // Tab 2: Completed History
        Page {
            background: Item {}
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20

                Label {
                    text: "Task History"
                    font.pixelSize: 22
                    font.bold: true
                }

                ListView {
                    id: completedTasksList
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    spacing: 10
                    
                    model: []
                    
                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 70
                        radius: 8
                        color: "white"
                        border.color: "#E0E0E0"
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            
                            ColumnLayout {
                                Layout.fillWidth: true
                                Label { text: modelData.emp_name + " - " + modelData.task_name; font.bold: true; font.pixelSize: 16 }
                                Label { text: "Completed on: " + modelData.date; color: "gray"; font.pixelSize: 14 }
                            }
                            
                            Rectangle {
                                color: "#4CAF50"
                                radius: 4
                                width: 70
                                height: 24
                                Label {
                                    anchors.centerIn: parent
                                    text: "Done"
                                    color: "white"
                                    font.pixelSize: 12
                                    font.bold: true
                                }
                            }
                        }
                    }
                }
            }
            
            Component.onCompleted: {
                if (typeof managerController !== "undefined") {
                    completedTasksList.model = managerController.getCompletedTasks()
                }
            }
        }
    }

    footer: TabBar {
        id: tabBar
        currentIndex: swipeView.currentIndex
        TabButton { text: "Live Activity" }
        TabButton { text: "Completed Tasks" }
    }
}
