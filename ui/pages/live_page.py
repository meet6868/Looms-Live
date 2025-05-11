from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                           QComboBox, QRadioButton, QPushButton, QScrollArea,
                           QGridLayout, QButtonGroup)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QPixmap, QImage
import sqlite3
from datetime import datetime, timedelta
import os
from PyQt5.QtWidgets import QSizePolicy
from utils.path_utils import get_db_path

class LivePage:
    def __init__(self, main_page):
        self.main_page = main_page
        self.logger = main_page.logger
        self.current_view = 'grid'  # 'grid' or 'single'
        self.grid_size = 4  # Default grid size
        self.current_page = 0
        self.machine_buttons = []
        self.view_timers = {}
        self.db_path = get_db_path()
        self.machine_info = None  # Initialize the label reference

    def create_page(self):
        page = QWidget()
        self.main_layout = QVBoxLayout(page)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # Header section
        self.setup_header()
        
        # Content section
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Main content layout
        self.content_layout = QHBoxLayout(self.content_frame)
        
        # Setup grid view container
        self.setup_grid_container()
        
        # Setup machine buttons panel
        self.setup_machine_buttons()
        
        self.main_layout.addWidget(self.content_frame)
        
        # Start update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_views)
        self.update_timer.start(1000)  # Update every second
        
        # Initial load of machines
        self.update_grid_view()
        
        return page

    def setup_header(self):
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left side with title
        title = QLabel("Live View")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        
        # Machine status info
        self.machine_info = QLabel()  # Create the label
        self.machine_info.setStyleSheet("""
            color: #666;
            font-size: 14px;
            margin-left: 20px;
            padding: 8px 15px;
            background: #f5f5f5;
            border-radius: 4px;
        """)
        self.update_machine_info()  # Initial update
        
        # View controls
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Grid/Single view selector
        self.view_group = QButtonGroup()
        self.grid_radio = QRadioButton("Grid View")
        self.single_radio = QRadioButton("Single View")
        self.grid_radio.setChecked(True)
        self.view_group.addButton(self.grid_radio)
        self.view_group.addButton(self.single_radio)
        
        # Grid size selector
        self.size_combo = QComboBox()
        self.size_combo.addItems(['2x2', '3x3', '4x4'])
        self.size_combo.setCurrentText('2x2')
        
        controls_layout.addWidget(self.grid_radio)
        controls_layout.addWidget(self.single_radio)
        controls_layout.addWidget(QLabel("Grid Size:"))
        controls_layout.addWidget(self.size_combo)
        
        # Assemble header layout
        header_layout.addWidget(title)
        header_layout.addWidget(self.machine_info)
        header_layout.addStretch()
        header_layout.addWidget(controls)
        
        # Connect signals
        self.grid_radio.toggled.connect(self.toggle_view)
        self.size_combo.currentTextChanged.connect(self.change_grid_size)
        
        self.main_layout.addWidget(header)

    def update_machine_info(self):
        """Update machine count information"""
        if self.machine_info:  # Check if label exists
            try:
                machines = self.main_page.local_db.get_machine_list()
                total_machines = len(machines) if machines else 0
                online_count = sum(1 for m in machines if self.is_machine_online(m))
                self.machine_info.setText(f"Total Machines: {total_machines} | Online: {online_count}")
            except Exception as e:
                self.logger.error(f"Error updating machine info: {str(e)}")

    def update_views(self):
        """Update the current view based on view mode"""
        self.update_machine_info()  # Update machine count
        
        if self.current_view == 'grid':
            self.update_grid_view()
        else:
            self.update_single_view()

    def setup_grid_container(self):
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        
        # Navigation buttons with improved styling
        self.prev_btn = QPushButton("<")
        self.next_btn = QPushButton(">")
        nav_button_style = """
            QPushButton {
                max-width: 30px;
                min-height: 200px;
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        self.prev_btn.setStyleSheet(nav_button_style)
        self.next_btn.setStyleSheet(nav_button_style)
        self.prev_btn.clicked.connect(self.previous_page)
        self.next_btn.clicked.connect(self.next_page)
        
        self.content_layout.addWidget(self.prev_btn)
        self.content_layout.addWidget(self.grid_container)
        self.content_layout.addWidget(self.next_btn)

    def setup_machine_buttons(self):
        # Create scroll area for buttons
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: white;
                border-left: 1px solid #e0e0e0;
            }
            QPushButton {
                text-align: left;
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: white;
            }
            QPushButton:checked {
                background: #e8f0fe;
                border-color: #1a73e8;
            }
        """)
        
        button_panel = QFrame()
        button_panel.setFixedWidth(180)  # Increased width
        button_layout = QVBoxLayout(button_panel)
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(10, 10, 10, 10)  # Added padding
        
        # Add machine buttons
        machines = self.main_page.local_db.get_machine_list()
        for machine in machines:
            btn = QPushButton(machine)
            btn.setCheckable(True)  # Make buttons checkable initially
            btn.clicked.connect(lambda checked, m=machine: self.load_machine(m))
            btn.setMinimumHeight(30)
            self.machine_buttons.append(btn)
            button_layout.addWidget(btn)
        
        button_layout.addStretch()
        scroll_area.setWidget(button_panel)
        self.button_panel = scroll_area
        self.button_panel.setVisible(False)  # Initially hidden
        self.content_layout.addWidget(scroll_area)

    def toggle_view(self, checked):
        """Handle view mode toggle between grid and single view"""
        self.current_view = 'grid' if self.grid_radio.isChecked() else 'single'
        
        # Enable/disable grid size selector based on view mode
        self.size_combo.setEnabled(self.current_view == 'grid')
        
        # Show/hide navigation buttons and button panel based on view mode
        is_grid = self.current_view == 'grid'
        self.prev_btn.setVisible(is_grid)
        self.next_btn.setVisible(is_grid)
        self.button_panel.setVisible(not is_grid)
        
        # When switching to single view, select first button
        if not is_grid and self.machine_buttons:
            for btn in self.machine_buttons:
                btn.setChecked(False)
            self.machine_buttons[0].setChecked(True)
            self.load_machine(self.machine_buttons[0].text())
        
        # Update the view
        self.update_views()

    def load_machine_view(self, machine_key):
        try:
            view_data = self.main_page.local_db.get_machine_view(machine_key)
            
            if view_data:
                # Create main container with fixed minimum size
                image_widget = QFrame()
                if self.current_view == 'single':
                    image_widget.setMinimumSize(1200, 800)  # Larger fixed size for single view
                    image_widget.setMaximumSize(1920, 1080)  # Maximum size limit
                else:
                    image_widget.setMinimumSize(400, 300)
                    image_widget.setMaximumSize(800, 600)
                
                image_layout = QVBoxLayout(image_widget)
                image_layout.setContentsMargins(5, 5, 5, 5)
                
                image_data = view_data['image_data']
                updated_at = view_data['updated_at']
                
                # Header with machine info
                header = QWidget()
                header.setFixedHeight(30)
                header_layout = QHBoxLayout(header)
                header_layout.setContentsMargins(5, 0, 5, 0)
                
                key_label = QLabel(machine_key.replace('machine_', 'Machine '))
                key_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 12px;")
                
                updated_time = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                is_online = datetime.now() - updated_time < timedelta(minutes=1)
                status_label = QLabel("🟢 Online" if is_online else "🔴 Offline")
                status_label.setStyleSheet("""
                    background-color: """ + ("#28a745" if is_online else "#dc3545") + """;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 15px;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 2px;
                """)
                
                header_layout.addWidget(key_label)
                header_layout.addStretch()
                header_layout.addWidget(status_label)
                
                # Image container with size constraints
                # Adjust image container for better scaling
                image_container = QLabel()
                image_container.setAlignment(Qt.AlignCenter)
                image_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                try:
                    from base64 import b64decode
                    image_bytes = b64decode(image_data) if isinstance(image_data, str) else image_data
                    
                    if QPixmap().loadFromData(image_bytes, 'PNG'):
                        pixmap = QPixmap()
                        pixmap.loadFromData(image_bytes, 'PNG')
                        # debug_dir = os.path.join('e:', 'MCGS', 'MCGS Web', 'debug', 'screenshots')
                        # if not os.path.exists(debug_dir):
                        #     os.makedirs(debug_dir)
                        # filename = f"{machine_key}.png"
                        # save_path = os.path.join(debug_dir, filename)
                        # print(f"Image saved to: {save_path}")
                        # pixmap.save(save_path, 'PNG')
                        
                        # Skip top 10% and keep the rest
                        skip_height = int(pixmap.height() * 0.1)
                        remaining_height = pixmap.height() - skip_height
                        
                        cropped = pixmap.copy(
                            0, skip_height,
                            pixmap.width(), remaining_height
                        )
                        
                        # Fixed scaling sizes based on view mode
                        if self.current_view == 'single':
                            scaled = cropped.scaled(
                                1200,  # Fixed width for single view
                                800,   # Fixed height for single view
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                        else:
                            scaled = cropped.scaled(
                                750,
                                550,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                        
                        image_container.setPixmap(scaled)
                    
                except Exception as e:
                    self.logger.error(f"Image processing error: {str(e)}")
                    image_container.setText("Error loading image")
                
                image_layout.addWidget(header)
                image_layout.addWidget(image_container, 1)
                
                return image_widget
                
        except Exception as e:
            self.logger.error(f"Error loading machine view: {str(e)}")
            return QLabel("Error loading view")

    def change_grid_size(self, size_text):
        self.grid_size = int(size_text[0]) ** 2
        self.current_page = 0
        self.update_grid_view()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_grid_view()

    def next_page(self):
        self.current_page += 1
        self.update_grid_view()

    def update_single_view(self):
        """Update the single view with selected machine"""
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Find selected machine
        selected_machine = None
        for btn in self.machine_buttons:
            if btn.isChecked():
                selected_machine = btn.text()
                break
        
        if selected_machine:
            # Load and display selected machine
            machine_view = self.load_machine_view(selected_machine)
            self.grid_layout.addWidget(machine_view, 0, 0)
        else:
            # Show message to select a machine
            no_selection = QLabel("Please select a machine from the right panel")
            no_selection.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 16px;
                    padding: 20px;
                }
            """)
            no_selection.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_selection, 0, 0)

    def load_machine(self, machine_key):
        """Handle machine selection in single view"""
        if self.current_view == 'single':
            # Uncheck other buttons
            for btn in self.machine_buttons:
                if btn.text() != machine_key:
                    btn.setChecked(False)
                else:
                    btn.setChecked(True)
            self.update_single_view()

    def is_machine_online(self, machine_key):
        """Check if machine is online"""
        try:
            view_data = self.main_page.local_db.get_machine_view(machine_key)
            if view_data and 'updated_at' in view_data:
                updated_time = datetime.strptime(view_data['updated_at'], '%Y-%m-%d %H:%M:%S')
                return datetime.now() - updated_time < timedelta(minutes=1)
        except Exception:
            pass
        return False

    def update_grid_view(self):
        """Update the grid view with machine views"""
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        machines = self.main_page.local_db.get_machine_list()
        
        if not machines:
            # Show message when no machines are available
            no_data_label = QLabel("No machines available")
            no_data_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 16px;
                    padding: 20px;
                }
            """)
            no_data_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_data_label, 0, 0)
            return
            
        start_idx = self.current_page * self.grid_size
        
        # Update navigation buttons
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(start_idx + self.grid_size < len(machines))
        
        # Fill grid
        for i in range(self.grid_size):
            idx = start_idx + i
            if idx < len(machines):
                machine_view = self.load_machine_view(machines[idx])
                row = i // 2
                col = i % 2
                self.grid_layout.addWidget(machine_view, row, col)