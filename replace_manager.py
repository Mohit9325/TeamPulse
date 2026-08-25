import sys

with open("main.qml", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_content = """    Component {
        id: managerDashboardComponent
        Page {
            id: managerPage
            background: Item {}

            // Enable Professional Material Styling
            Material.theme: Material.Light
            Material.accent: Material.Teal 

            // 1. The Slide-Out Menu (Drawer)
            Drawer {
                id: sideMenu
                width: window.width * 0.75
                height: window.height

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        height: 140
                        color: Material.accentColor
                        Label {
                            text: "Manager Options"
                            color: "white"
                            font.pixelSize: 20
                            font.bold: true
                            anchors.bottom: parent.bottom
                            anchors.left: parent.left
                            anchors.margins: 16
                        }
                    }
                    ItemDelegate { text: "⚙️ Settings"; Layout.fillWidth: true; onClicked: sideMenu.close() }
                    ItemDelegate { text: "📊 Export Data"; Layout.fillWidth: true; onClicked: sideMenu.close() }
                    Item { Layout.fillHeight: true } // Pushes content up
                }
            }

            // 2. Fixed Top Toolbar (Fixes your overlapping title)
            header: ToolBar {
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 4
                    
                    ToolButton {
                        text: "☰" // Menu Button
                        font.pixelSize: 22
                        onClicked: sideMenu.open()
                    }
                    
                    Label {
                        text: "Manager Dashboard"
                        Layout.fillWidth: true
                        horizontalAlignment: Qt.AlignHCenter
                        font.pixelSize: 18
                        font.bold: true
                    }
                    
                    ToolButton {
                        text: "Log Out"
                        font.pixelSize: 14
                        onClicked: {
                            if (typeof authController !== "undefined") {
                                authController.logout()
                            }
                        }
                    }
                }
            }

            // 3. Main Content Area (Swipeable Tabs)
            SwipeView {
                id: managerSwipeView
                anchors.fill: parent
                currentIndex: managerTabBar.currentIndex

                // Tab 1: Radar Page
                Page {
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 20
                        
                        Button {
                            text: "Refresh Radar"
                            Layout.alignment: Qt.AlignHCenter
                            Material.background: "#E91E63" // The pink from your screenshot
                            Material.foreground: "white"
                            onClicked: console.log("Refreshing Radar...")
                        }
                        
                        Label {
                            text: "Radar Map View Component"
                            color: "gray"
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }

                // Tab 2: Completed & History Page
                Page {
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 16

                        Label {
                            text: "Task History"
                            font.pixelSize: 22
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        // Mock Data List for History
                        ListView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            spacing: 5
                            
                            model: ListModel {
                                ListElement { taskName: "Store Inspection"; date: "Today, 10:00 AM"; status: "Recently Completed" }
                                ListElement { taskName: "Inventory Check"; date: "Yesterday, 4:30 PM"; status: "History" }
                                ListElement { taskName: "Submit Timesheets"; date: "Aug 17, 2026"; status: "History" }
                            }
                            
                            delegate: ItemDelegate {
                                width: ListView.view.width
                                contentItem: ColumnLayout {
                                    Label { text: model.taskName; font.bold: true; font.pixelSize: 16 }
                                    RowLayout {
                                        Label { text: model.date; color: "gray"; font.pixelSize: 12; Layout.fillWidth: true }
                                        Label { 
                                            text: model.status; 
                                            color: model.status === "History" ? "gray" : "#4CAF50"; // Green for recent, gray for old
                                            font.pixelSize: 12 
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Tab 3: Timeline Page
                Page {
                    Label {
                        text: "Timeline Integration Goes Here"
                        anchors.centerIn: parent
                        color: "gray"
                    }
                }
            }

            // 4. Bottom Tab Navigation
            footer: TabBar {
                id: managerTabBar
                currentIndex: managerSwipeView.currentIndex
                TabButton { text: "Radar" }
                TabButton { text: "Completed" }
                TabButton { text: "Timeline" }
            }
        }
    }
"""

with open("main.qml", "w", encoding="utf-8") as f:
    f.writelines(lines[:121])
    f.write(new_content)
    f.writelines(lines[505:])
