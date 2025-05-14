from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QGridLayout, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy # Add QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QCursor, QPixmap
from datetime import datetime, timedelta
import os
import base64 # Import base64 for decoding

class DataUpdateThread(QThread):
    data_updated = pyqtSignal(list, dict)  # Signal for data updates

    def __init__(self, local_db):
        super().__init__()
        self.local_db = local_db
        self.running = True

    def run(self):
        while self.running:
            try:
                # Get temp data
                temp_data = self.local_db.get_temp_data()
                if not temp_data:
                    temp_data = []
                
                # Get tab views data with proper key mapping
                tab_views_data = {}
                for data in temp_data:
                    loom_num = data.get('Loom_Num', '')
                    if loom_num:
                        # Format key as machine_M1, machine_M2, etc.
                        machine_key = f"machine_{loom_num}"
                        view = self.local_db.get_machine_view(machine_key)
                        if view:
                            # Store with simple key (M1, M2) for easier matching
                            tab_views_data[loom_num] = view['updated_at']

                # Sort data by machine number
                temp_data.sort(key=lambda x: int(x.get('Loom_Num', 'M0')[1:]))
                
                self.data_updated.emit(temp_data, tab_views_data)
            except Exception as e:
                print(f"Error in data update thread: {e}")
            
            self.msleep(1000)  # Update every second

    def stop(self):
        self.running = False

class LiveViewUpdateThread(QThread):
    """Thread to continuously fetch and decode the live view image."""
    # Update signal definition to handle optional types
    live_view_updated = pyqtSignal(object, object)  # Changed from bytes, str to object, object

    def __init__(self, local_db):
        super().__init__()
        self.local_db = local_db
        self.running = True
        self._logger = None

    def set_logger(self, logger):
        self._logger = logger

    def run(self):
        while self.running:
            image_bytes = None
            timestamp_str = None
            try:
                view_data = self.local_db.get_tab_view('machine_tab')
                if view_data:
                    base64_image = view_data.get('image_data')
                    timestamp_str = view_data.get('updated_at')

                    if base64_image:
                        try:
                            image_bytes = base64.b64decode(base64_image)
                        except Exception as e:
                            if self._logger:
                                self._logger.error(f"Error decoding image: {e}")
                            image_bytes = b''  # Empty bytes instead of None
                
                # Emit signal with empty bytes if no image
                self.live_view_updated.emit(image_bytes if image_bytes is not None else b'', timestamp_str)

            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error in LiveViewUpdateThread: {e}")
                # Emit empty bytes instead of None
                self.live_view_updated.emit(b'', None)

            self.msleep(1000)  # Update every second

    def stop(self):
        self.running = False

class DashboardPage:
    def __init__(self, main_page):
        self.main_page = main_page
        self.logger = main_page.logger

        # Initialize status variables
        self.admin_status = '--'
        self.client_status = '--'
        self.client_login = '--'
        self.admin_connected = '--'
        self.client_connected = '--'
        self.vm_running = '--'
        
        # Initialize summary_labels dictionary
        self.summary_labels = {}

        # --- Initialize UI elements for live view HERE ---
        self.live_view_label = QLabel("Loading Live View...")
        self.live_view_label.setAlignment(Qt.AlignCenter)
        self.live_view_label.setStyleSheet("background-color: #e0e0e0; color: #555; border-radius: 5px;")
        self.live_view_status_label = QLabel("Status: --")
        self.live_view_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.live_view_status_label.setStyleSheet("font-size: 10px; color: #7f8c8d; margin-right: 5px;")
        # --- End Initialization ---

        # Initialize table first
        self.create_machine_table()

        # Initialize timers and threads
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_labels)
        self.status_timer.start(10000)  # Update system status every 10 seconds

        # Initialize update thread for table data
        self.update_thread = None
        self.start_update_thread() # For table data

        # --- Initialize and start live view update thread AFTER labels exist ---
        self.live_view_thread = LiveViewUpdateThread(self.main_page.local_db)
        self.live_view_thread.set_logger(self.logger) # Pass logger
        self.live_view_thread.live_view_updated.connect(self._handle_live_view_update)
        self.live_view_thread.start()
        # --- End Thread Start ---

    def start_update_thread(self):
        """Initialize and start the update thread"""
        if self.update_thread is None:
            self.update_thread = DataUpdateThread(self.main_page.local_db)
            self.update_thread.data_updated.connect(self.update_table_data)
            self.update_thread.start()

    
    def create_machine_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(16)  # Updated column count
        headers = [
            "Loom","Status",
            "Production Qty", "Production Length", "Speed", "Efficiency",
            "Pre-Production Qty", "Pre-Production Length", "Pre-Speed", "Pre-Efficiency",
            "Weaving Length", "Cut Length", "Weaving Forecast",
            "Warp Remain", "Warp Length", "Warp Forecast"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setMinimumHeight(350)
        self.table.setMaximumHeight(600)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                margin: 10px;
            }
            QHeaderView::section {
                background-color: #f5f6fa;
                padding: 8px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #f0f0f0;
            }
        """)
        
        # Fix first column
        header = self.table.horizontalHeader()
        self.table.setColumnWidth(0, 80)  # Fixed width for Loom column
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for i in range(2, 10):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
        
        # Store headers as instance variable for use in other methods
        self.table_headers = headers

    
    def create_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Dashboard title
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        # Single scroll area for all content
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QFrame.NoFrame)
        
        # Main container for all cards
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(20)
        
        # Add live view card
        live_view_card = QFrame()
        live_view_card.setObjectName("liveViewCard")
        live_view_card.setMinimumHeight(400)
        live_view_card.setStyleSheet("""
            #liveViewCard {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                padding: 5px;
            }
        """)
        live_view_layout = QVBoxLayout(live_view_card)
        live_view_layout.setContentsMargins(5, 2, 5, 5)
        live_view_layout.setSpacing(2)

        # Status label container
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addStretch(1)
        status_layout.addWidget(self.live_view_status_label)
        live_view_layout.addWidget(status_container)

        # Add the live view label
        self.live_view_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        live_view_layout.addWidget(self.live_view_label, 1)

        main_layout.addWidget(live_view_card)
        
        # Content grid for system info and machine data
        content_grid = QWidget()
        content_layout = QGridLayout(content_grid)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(20)
        
        # Add all other cards to content_layout
        data_card = QFrame()
        data_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                padding: 15px;
            }
        """)
        data_layout = QVBoxLayout(data_card)
        
        data_title = QLabel("System Information")
        data_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        data_title.setStyleSheet("color: #2c3e50;")
        data_layout.addWidget(data_title)
        
        # Create status labels with proper layout
        system_info_layout = QVBoxLayout()
        system_info_layout.setSpacing(8)
        
        # Create and add status labels with unified style
        status_labels_config = {
            'admin_status_label': "Admin Service",
            'client_status_label': "Client Service",
            'client_login_label': "Client Login",
            'admin_connected_label': "Admin Connection",
            'client_connected_label': "Client Connection",
            'vm_status_label': "VM Status"  # Changed from vm_running_label to vm_status_label
        }
        
        status_style = """
            QLabel {
                color: #2c3e50;
                font-size: 15px;
                padding: 5px;
                background-color: #f8f9fa;
                border-radius: 4px;
                margin: 2px;
            }
        """
        
        # Create status labels only once
        for attr_name, label_text in status_labels_config.items():
            label = QLabel(f"{label_text}: --")
            label.setStyleSheet(status_style)
            setattr(self, attr_name, label)
            system_info_layout.addWidget(label)
        
        data_layout.addLayout(system_info_layout)
        
        # Remove loading message
        # self.main_page.dashboard_info_label = ... (remove this section)
        
        content_layout.addWidget(data_card, 0, 0)
        
        # Machine Data card
        machine_card = QFrame()
        machine_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        machine_layout = QVBoxLayout(machine_card)
        
        # Machine Data Section
        machine_data_title = QLabel("Machine Data Monitor")
        machine_data_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        machine_data_title.setStyleSheet("color: #2c3e50;")
        machine_layout.addWidget(machine_data_title)
        
        # Add shift information at the top
        self.shift_label = QLabel("Current Shift: -- | Time: --")
        self.shift_label.setFont(QFont("Segoe UI", 12))
        self.shift_label.setStyleSheet("color: #2c3e50; margin: 5px;")
        machine_layout.addWidget(self.shift_label)
        
        # Add the machine data table
        machine_layout.addWidget(self.table)  # Add this line to display the table
        
        # Modified summary section with two cards
        summary_container = QVBoxLayout()
        
        # Current Production Card
        current_frame = QFrame()
        current_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        current_layout = QVBoxLayout(current_frame)
        current_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins
        current_layout.setSpacing(5)  # Reduce spacing
        
        # Current Production Label
        current_title = QLabel("Current Production")
        current_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 16px; margin-bottom: 1px;")
        current_layout.addWidget(current_title)
        
        # Current values layout
        current_values = QGridLayout()
        current_values.setSpacing(5)  # Reduce spacing
        current_values.setContentsMargins(2, 2, 2, 2)  # Minimal margins
        
        # Value label style
        value_style = """
            color: #2c3e50;
            font-size: 14px;
            font-weight: bold;
            padding: 3px;
            background-color: white;
            border-radius: 4px;
            min-width: 80px;
        """
        
        # Header label style
        header_style = """
            color: #2c3e50;
            font-size: 11px;
            padding: 2px;
        """
        
        # Add current production values with optimized spacing
        current_headers = ["Production Qty", "Production Length", "Speed", "Efficiency"]
        for i, header in enumerate(current_headers):
            label = QLabel(header)
            # label.setStyleSheet(header_style)
            value = QLabel("0")
            value.setStyleSheet(value_style)
            value.setAlignment(Qt.AlignCenter)
            current_values.addWidget(label, 0, i)
            current_values.addWidget(value, 1, i)
            self.summary_labels[header] = value
        
        current_layout.addLayout(current_values)  # Add this line
        summary_container.addWidget(current_frame) # Add this line to add the current frame to the container
        
        # Apply the same optimizations to Previous Production section
        previous_frame = QFrame()
        previous_frame.setStyleSheet(current_frame.styleSheet())
        previous_layout = QVBoxLayout(previous_frame)
        previous_layout.setContentsMargins(5, 5, 5, 5)
        previous_layout.setSpacing(5)
        
        previous_title = QLabel("Previous Production")
        previous_title.setStyleSheet(current_title.styleSheet())
        previous_layout.addWidget(previous_title)
        
        previous_values = QGridLayout()
        previous_values.setSpacing(5)
        previous_values.setContentsMargins(2, 2, 2, 2)
        
        # Add previous production values
        for i, header in enumerate(current_headers):
            pre_header = f"Pre-{header}"
            label = QLabel(header)
            value = QLabel("0")
            value.setStyleSheet("""
                color: #2c3e50;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
                background-color: white;
                border-radius: 4px;
                min-width: 100px;
            """)
            value.setAlignment(Qt.AlignCenter)
            previous_values.addWidget(label, 0, i)
            previous_values.addWidget(value, 1, i)
            self.summary_labels[pre_header] = value
        
        previous_layout.addLayout(previous_values)
        summary_container.addWidget(previous_frame)
        
        machine_layout.addLayout(summary_container)
        content_layout.addWidget(machine_card, 0, 1)
        
        # Quick actions card
        actions_card = QFrame()
        actions_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        actions_layout = QVBoxLayout(actions_card)
        
        actions_title = QLabel("Quick Actions")
        actions_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        actions_title.setStyleSheet("color: #2c3e50;")
        actions_layout.addWidget(actions_title)
        
        
        view_analytics_btn = QPushButton("View Analytics")
        view_analytics_btn.setIcon(QIcon("icons/analytics.png"))
        view_analytics_btn.setCursor(QCursor(Qt.PointingHandCursor))
        view_analytics_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        view_analytics_btn.clicked.connect(lambda: self.main_page.switch_page(2))
        actions_layout.addWidget(view_analytics_btn)
        
        content_layout.addWidget(actions_card, 1, 0)
        
      
        # Remove these problematic lines
        # content.setWidget(content_widget)  # Remove this
        # layout.addWidget(content)  # Remove this
        
        # Add content grid to main layout
        main_layout.addWidget(content_grid)
        
        # Set the main container as the scroll area widget
        main_scroll.setWidget(main_container)
        layout.addWidget(main_scroll)
        
        return page

    def cleanup(self):
        """Stop the status update timer"""
        if self.status_timer:
            self.status_timer.stop()

    def update_status_labels(self):
        try:
            # Get all status values at once
            # In update_status_labels method, update the dictionary key
            status_values = {
                'admin_status': self.main_page.local_db.get_core_value("admin_service_status"),
                'client_status': self.main_page.local_db.get_core_value("client_service_status"),
                'client_login': self.main_page.local_db.get_core_value("client_login_status"),
                'admin_connected': "Connected" if self.main_page.local_db.get_value("admin_connected") == "1" else "Disconnected",
                'client_connected': "Connected" if self.main_page.local_db.get_value("client_connected") == "1" else "Disconnected",
                'vm_status': "Running" if self.main_page.local_db.get_value("vm_running") == "1" else "Stopped",  # Changed from vm_running to vm_status
            }
            
            # Update labels and their styles in one pass
            for status_name, value in status_values.items():
                label = getattr(self, f"{status_name}_label")
                label_text = f"{label.text().split(':')[0]}: {value or '--'}"
                label.setText(label_text)
                
                # Set color based on status
                if value in ['Connected', 'Running', 'true','starting','Processing...','Starting']:
                    color = "#27ae60"  # green
                elif value in ['Disconnected', 'Stopped', 'false',"Error"]:
                    color = "#c0392b"  # red
                else:
                    color = "#7f8c8d"  # gray
                
                label.setStyleSheet(f"""
                    QLabel {{
                        color: {color};
                        font-size: 13px;
                        padding: 5px;
                        background-color: #f8f9fa;
                        border-radius: 4px;
                        margin: 2px;
                    }}
                """)

        except Exception as e:
            self.logger.error(f"Error updating status labels: {e}")

    def update_table_data(self, temp_data, tab_views_data):
        try:
            self.table.setRowCount(len(temp_data))
            
            # Initialize summary values
            sum_prod_qty = sum_prod_len = sum_pre_prod_qty = sum_pre_prod_len = 0
            sum_speed = sum_eff = sum_pre_speed = sum_pre_eff = 0
            count = 0

            for row, data in enumerate(temp_data):
                loom_num = data.get('Loom_Num', '')
                
                # Check if data is within 1 minute
                temp_updated = datetime.strptime(data.get('updated_at', ''), '%Y-%m-%d %H:%M:%S')
                tab_updated_str = tab_views_data.get(loom_num, '')
                tab_updated = datetime.strptime(tab_updated_str, '%Y-%m-%d %H:%M:%S') if tab_updated_str else temp_updated
                now = datetime.now()
                
                # Create items for the row
                loom_item = QTableWidgetItem(loom_num)
                
                # # Set background color based on status
                # if (now - temp_updated < timedelta(minutes=1) and 
                #     now - tab_updated < timedelta(minutes=1)):
                #     loom_item.setBackground(Qt.green)
                # else:
                #     loom_item.setBackground(Qt.red)
                
                # # Set table items
                # self.table.setItem(row, 0, loom_item)
                # self.table.setItem(row, 1, QTableWidgetItem(str(data.get('Production_Quantity', 0))))
                # self.table.setItem(row, 2, QTableWidgetItem(str(data.get('Production_FabricLength', 0))))
                # self.table.setItem(row, 3, QTableWidgetItem(str(data.get('Speed', 0))))
                # self.table.setItem(row, 4, QTableWidgetItem(str(data.get('Efficiency', 0))))
                # self.table.setItem(row, 5, QTableWidgetItem(str(data.get('Pre_Production_Quantity', 0))))
                # self.table.setItem(row, 6, QTableWidgetItem(str(data.get('Pre_Production_FabricLength', 0))))
                # self.table.setItem(row, 7, QTableWidgetItem(str(data.get('Pre_Speed', 0))))
                # self.table.setItem(row, 8, QTableWidgetItem(str(data.get('Pre_Efficiency', 0))))
                # self.table.setItem(row, 9, QTableWidgetItem(str(data.get('Weaving_Length', ''))))
                # self.table.setItem(row, 10, QTableWidgetItem(str(data.get('Cut_Length', ''))))
                # self.table.setItem(row, 11, QTableWidgetItem(str(data.get('Weaving_Forecast', ''))))
                # self.table.setItem(row, 12, QTableWidgetItem(str(data.get('Warp_Remain', ''))))
                # self.table.setItem(row, 13, QTableWidgetItem(str(data.get('Warp_Length', ''))))
                # self.table.setItem(row, 14, QTableWidgetItem(str(data.get('Warp_Forecast', ''))))
                status_flag=0
                status_item = QTableWidgetItem()
                if (now - temp_updated < timedelta(minutes=1) or 
                    now - tab_updated < timedelta(minutes=1)):
                    status_flag=1
                    status_item.setText(" 🟢 ")
                    # status_item.setBackground(QBrush(QColor("#90EE90")))  # Light green
                elif now - temp_updated < timedelta(minutes=1):
                    status_flag=1
                    status_item.setText(" 🟡 ")
                else:
                    status_item.setText(" 🔴 ")
                    # status_item.setBackground(QBrush(QColor("#FFB6C1")))  # Light red
                status_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 1, status_item)
                
                # Set table items
                self.table.setItem(row, 0, loom_item)
                self.table.setItem(row, 2, QTableWidgetItem(str(data.get('Production_Quantity', 0))))
                self.table.setItem(row, 3, QTableWidgetItem(str(data.get('Production_FabricLength', 0))))
                self.table.setItem(row, 4, QTableWidgetItem(str(data.get('Speed', 0))))
                self.table.setItem(row, 5, QTableWidgetItem(str(data.get('Efficiency', 0))))
                self.table.setItem(row, 6, QTableWidgetItem(str(data.get('Pre_Production_Quantity', 0))))
                self.table.setItem(row, 7, QTableWidgetItem(str(data.get('Pre_Production_FabricLength', 0))))
                self.table.setItem(row, 8, QTableWidgetItem(str(data.get('Pre_Speed', 0))))
                self.table.setItem(row, 9, QTableWidgetItem(str(data.get('Pre_Efficiency', 0))))
                self.table.setItem(row, 10, QTableWidgetItem(str(data.get('Weaving_Length', ''))))
                self.table.setItem(row, 11, QTableWidgetItem(str(data.get('Cut_Length', ''))))
                self.table.setItem(row, 12, QTableWidgetItem(str(data.get('Weaving_Forecast', ''))))
                self.table.setItem(row, 13, QTableWidgetItem(str(data.get('Warp_Remain', ''))))
                self.table.setItem(row, 14, QTableWidgetItem(str(data.get('Warp_Length', ''))))
                self.table.setItem(row, 15, QTableWidgetItem(str(data.get('Warp_Forecast', ''))))


                # Update summary values
                try:
                    if status_flag==1:
                        sum_prod_qty += float(data.get('Production_Quantity', 0))
                        sum_prod_len += float(data.get('Production_FabricLength', 0))
                        sum_speed += float(data.get('Speed', 0))
                        sum_eff += float(data.get('Efficiency', 0))
                        sum_pre_prod_qty += float(data.get('Pre_Production_Quantity', 0))
                        sum_pre_prod_len += float(data.get('Pre_Production_FabricLength', 0))
                        sum_pre_speed += float(data.get('Pre_Speed', 0))
                        sum_pre_eff += float(data.get('Pre_Efficiency', 0))
                        count += 1
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid numeric data for row {row}")
                    continue

            # Update summary labels
            if count > 0:
                # Current Production
                self.summary_labels["Production Qty"].setText(f"{sum_prod_qty:.0f}")
                self.summary_labels["Production Length"].setText(f"{sum_prod_len:.2f}")
                self.summary_labels["Speed"].setText(f"{sum_speed/count:.2f}")
                self.summary_labels["Efficiency"].setText(f"{sum_eff/count:.2f}")

                # Previous Production (Check keys used during creation)
                self.summary_labels["Pre-Production Qty"].setText(f"{sum_pre_prod_qty:.0f}")
                self.summary_labels["Pre-Production Length"].setText(f"{sum_pre_prod_len:.2f}")
                self.summary_labels["Pre-Speed"].setText(f"{sum_pre_speed/count:.2f}")
                self.summary_labels["Pre-Efficiency"].setText(f"{sum_pre_eff/count:.2f}")


                # Update shift information
                current_shift = temp_data[0].get('Shift', '--') if temp_data else '--'
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.shift_label.setText(f"Current Shift: {current_shift} | Time: {current_time}")

        except Exception as e:
            self.logger.error(f"Error updating table: {e}")
    
    def __del__(self):
        """Cleanup method"""
        try:
            self.cleanup()
        except:
            pass

    def cleanup(self):
        """Cleanup method for proper thread handling"""
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        if hasattr(self, 'live_view_thread') and self.live_view_thread is not None:
            self.live_view_thread.stop()
            self.live_view_thread.wait()
            self.live_view_thread = None
        if hasattr(self, 'update_thread') and self.update_thread is not None:
            self.update_thread.stop()
            self.update_thread.wait()
            self.update_thread = None

    def _handle_live_view_update(self, image_bytes, timestamp_str):
        """Slot to handle updates from the LiveViewUpdateThread."""
        try:
            # Check if the label still exists
            if not hasattr(self, 'live_view_label') or not self.live_view_label:
                return

            # Update Image
            if image_bytes:
                pixmap = QPixmap()
                loaded = pixmap.loadFromData(image_bytes)
                if loaded:
                    # Crop the image
                    original_height = pixmap.height()
                    top_crop = int(original_height * 0.065)
                    bottom_crop = int(original_height * 0.40)
                    
                    try:
                        cropped_pixmap = pixmap.copy(
                            0,
                            top_crop,
                            pixmap.width(),
                            original_height - (top_crop + bottom_crop)
                        )

                        # Scale the cropped image
                        if self.live_view_label and self.live_view_label.size().width() > 0:
                            label_size = self.live_view_label.size()
                            scaled_pixmap = cropped_pixmap.scaled(
                                label_size,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                            self.live_view_label.setPixmap(scaled_pixmap)
                        else:
                            self.live_view_label.setPixmap(cropped_pixmap)

                        self.live_view_label.setStyleSheet("background-color: white; border-radius: 5px;")
                    except RuntimeError:
                        # Widget was deleted during processing
                        return
                else:
                    if self.live_view_label:
                        self.live_view_label.setText("Error loading image data")
                        self.live_view_label.setStyleSheet("background-color: #ffe0e0; color: #c0392b; border-radius: 5px;")
            else:
                if self.live_view_label:
                    self.live_view_label.setText("No image data available")
                    self.live_view_label.setStyleSheet("background-color: #e0e0e0; color: #555; border-radius: 5px;")

            # Check if status label exists before updating
            if not hasattr(self, 'live_view_status_label') or not self.live_view_status_label:
                return

            # Update Status with enhanced styling
            if timestamp_str:
                try:
                    last_update_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    now = datetime.now()
                    if now - last_update_time < timedelta(minutes=1):
                        status_text = "🟢 Online"
                        status_color = "#28a745"
                    else:
                        status_text = f"🔴 Offline (Last: {last_update_time.strftime('%H:%M:%S')})"
                        status_color = "#dc3545"
                except ValueError:
                    status_text = "⚠️ Invalid Timestamp"
                    status_color = "#ffc107"
            else:
                status_text = "⚫ No Data"
                status_color = "#6c757d"

            if self.live_view_status_label:
                self.live_view_status_label.setText(status_text)
                self.live_view_status_label.setStyleSheet(f"""
                    font-size: 14px;
                    font-weight: bold;
                    color: white;
                    background-color: {status_color};
                    padding: 4px 12px;
                    border-radius: 15px;
                    margin: 2px 5px;
                """)

        except Exception as e:
            self.logger.error(f"Error handling live view update: {e}")
            # Ensure labels are updated even on error
            if hasattr(self, 'live_view_label'):
                self.live_view_label.setText("Error displaying live view")
                self.live_view_label.setStyleSheet("background-color: #ffe0e0; color: #c0392b; border-radius: 5px;")
            if hasattr(self, 'live_view_status_label'):
                self.live_view_status_label.setText("Status: Error")
                self.live_view_status_label.setStyleSheet("font-size: 10px; color: #c0392b; margin-right: 5px;")


    # Remove the old update_live_view method if it exists


    
        