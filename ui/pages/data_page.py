from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QScrollArea, QFrame, QGridLayout,
                           QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor  # Added QFont import
from datetime import datetime, timedelta  # Add this import at the top
from PyQt5.QtCore import QThread, pyqtSignal
import time

class MachineCard(QFrame):
    def __init__(self, data):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #D1E4E8;
                padding: 10px;
                margin: 3px;
            }
            QLabel {
                color: #2C3E50;
                background: transparent;
                padding: 1px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setFixedHeight(500)  # Reduced height
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

    
        
        # Header container with status
        header_container = QHBoxLayout()
        header_container.setSpacing(10)
        
        # Machine header
        header = QLabel(f"{data.get('Loom_Num', '')}")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet("color: #2980B9; padding: 3px; background: transparent;")
        
        # Status indicator
        status = QLabel()
        try:
            if data.get('updated_at'):
                updated_str = data['updated_at'].split('+')[0].split('.')[0].replace('T', ' ')
                updated_time = datetime.strptime(updated_str, '%Y-%m-%d %H:%M:%S')
                now = datetime.now()
                
                if now - updated_time < timedelta(minutes=1):
                    status.setText(f"🟢 Online ")
                    status.setStyleSheet("""
                        color: #27AE60;
                        font-size: 12px;
                        padding: 2px 8px;
                        font-weight: bold;
                        background: #E8F5E9;
                        border-radius: 10px;
                    """)
                else:
                    status.setText(f"🔴 Offline ")
                    status.setStyleSheet("""
                        color: #E74C3C;
                        font-size: 12px;
                        padding: 2px 8px;
                        font-weight: bold;
                        background: #FFEBEE;
                        border-radius: 10px;
                    """)
            else:
                status.setText("🔴 Offline Time Not Available")
                status.setStyleSheet("""
                    color: #E74C3C;
                    font-size: 12px;
                    padding: 2px 8px;
                    font-weight: bold;
                    background: #FFEBEE;
                    border-radius: 10px;
                """)
        except Exception:
            status.setText("🔴 Offline Error")
            status.setStyleSheet("""
                color: #E74C3C;
                font-size: 12px;
                padding: 2px 8px;
                font-weight: bold;
                background: #FFEBEE;
                border-radius: 10px;
            """)
        
        header_container.addWidget(header)
        header_container.addWidget(status)
        header_container.addStretch()
        layout.addLayout(header_container)
        
        # Data grid
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setContentsMargins(3, 5, 3, 3)

        # Add data fields
        self.add_field(grid, 0, 0, "Device Name:", data.get('Device_Name', ''))
        self.add_field(grid, 0, 1, "Weaving Length:", data.get('Weaving_Length', ''))
        self.add_field(grid, 1, 0, "Warp Remain:", data.get('Warp_Remain', ''), self.get_warp_color(data.get('Warp_Remain', 0)))
        self.add_field(grid, 1, 1, "Warp Length:", data.get('Warp_Length', ''))
        self.add_field(grid, 2, 0, "Speed:", str(data.get('Speed', '')))
        self.add_field(grid, 2, 1, "Production Length:", str(data.get('Production_FabricLength', '')))
        self.add_field(grid, 3, 0, "Production Qty:", str(data.get('Production_Quantity', '')))
        
       
        # Efficiency
        try:
            efficiency = float(data.get('Efficiency', 0))
            efficiency_color = "#27AE60" if efficiency >= 80 else "#E74C3C"
            self.add_field(grid, 3, 1, "Efficiency:", f"{efficiency}%", efficiency_color)
        except (ValueError, TypeError):
            self.add_field(grid, 3, 1, "Efficiency:", "N/A", "#E74C3C")

         # Row 4: merged info display
        # Create the label part
        # Add merged field in a clean separate row (e.g., row 6 to avoid overlap)
        # Row 4: merged info display
        merged_label = QLabel("H1 : H2 : Wrap : Other : Total")
        merged_label.setStyleSheet("""
            color: #576574;
            font-size: 14px;
            background: transparent;
            padding: 1px;
            margin-bottom: 1px;
            font-weight: bold;
        """)

        # Safe conversion function for time values
        def safe_time_get(key):
            try:
                value = data.get(key, 0)
                return str(int(float(value))) if value else "0"
            except (ValueError, TypeError):
                return "0"

        merged_value = QLabel(
            f"{safe_time_get('H1Time')} : {safe_time_get('H2Time')} : "
            f"{safe_time_get('WrapTime')} : {safe_time_get('OtherTime')} : {safe_time_get('TotalTime')}"
        )
        merged_value.setFont(QFont("Segoe UI", 12, QFont.Bold))
        merged_value.setStyleSheet("""
            color: #2C3E50;
            background: transparent;
            font-weight: bold;
            padding: 1px;
            margin-top: 1px;
        """)

        # Add merged field to grid - remove duplicate additions
        row_index = 6
        grid.addWidget(merged_label, row_index * 2, 0, 1, 2)      # span 2 columns
        grid.addWidget(merged_value, row_index * 2 + 1, 0, 1, 2)  # span 2 columns

        # Remove this duplicate line
        # grid.addWidget(merged_label, 4, 0, 1, 2)  # This was causing the duplicate label
        
        layout.addLayout(grid)

    def get_warp_color(self, warp_value):
        try:
            warp = float(warp_value)
            if warp < 500:
                return "#E74C3C"  # Red
            elif warp < 1000:
                return "#F39C12"  # Orange
            return "#2C3E50"  # Default color
        except (ValueError, TypeError):
            return "#2C3E50"  # Default color for invalid values

    def add_field(self, grid, row, col, label_text, value_text, value_color=None):
        label = QLabel(label_text)
        label.setStyleSheet("""
            color: #576574;
            font-size: 14px;
            background: transparent;
            padding: 1px;
            margin-bottom: 1px;
            font-weight: bold;
        """)
        
        # Safe conversion of numeric values
        try:
            if isinstance(value_text, (int, float)):
                value_text = str(round(float(value_text), 2))
            else:
                value_text = str(value_text)
        except (ValueError, TypeError):
            value_text = "N/A"
        
        value = QLabel(value_text)
        value.setFont(QFont("Segoe UI", 12, QFont.Bold))
        
        # Special color handling for efficiency values
        if label_text == "Efficiency:":
            try:
                efficiency_value = float(str(value_text).replace('%', ''))
                value_color = "#27AE60" if efficiency_value >= 80 else "#E74C3C"
            except (ValueError, TypeError):
                value_color = "#E74C3C"
        
        style = f"""
            color: {value_color if value_color else '#2C3E50'};
            background: transparent;
            font-weight: bold;
            padding: 1px;
            margin-top: 1px;
        """
        value.setStyleSheet(style)
        
        grid.addWidget(label, row * 2, col)
        grid.addWidget(value, row * 2 + 1, col)

    

# Add this new thread class at the top level
class DataFetchThread(QThread):
    data_fetched = pyqtSignal(object)  # Changed to object type
    
    def __init__(self, local_db):
        super().__init__()
        self.local_db = local_db
        self.running = True
        
    def run(self):
        while self.running:
            try:
                data = self.local_db.get_temp_data()
                if data:
                    # print("Fetched data:", data)
                    self.data_fetched.emit(data)
            except Exception as e:
                self.local_db.logger.error(f"Error fetching data: {e}")
            time.sleep(1)

class DataPage:
    def __init__(self, main_window):
        self.main_window = main_window
        self.app_controller = main_window.app_controller
        self.fetch_thread = None
        self.machine_cards = {}  # Dictionary to store cards by Loom_Num

    def refresh_data(self, data=None):
        try:
            if data is None:
                data = self.main_window.local_db.get_temp_data()

            if data:
                # Clear removed machines
                current_looms = {machine.get('Loom_Num', '') for machine in data}
                for loom_num in list(self.machine_cards.keys()):
                    if loom_num not in current_looms:
                        card = self.machine_cards.pop(loom_num)
                        card.deleteLater()

                # Update or create cards
                sorted_data = sorted(data, key=lambda x: str(x.get('Loom_Num', '')))
                cols = 3
                
                # Remove all widgets from layout but don't delete them
                while self.cards_layout.count():
                    self.cards_layout.takeAt(0)

                # Add/Update cards in layout
                for i, machine_data in enumerate(sorted_data):
                    loom_num = machine_data.get('Loom_Num', '')
                    
                    # Get existing card or create new one
                    if loom_num not in self.machine_cards:
                        self.machine_cards[loom_num] = MachineCard(machine_data)
                    else:
                        # Update existing card with new data
                        card = self.machine_cards[loom_num]
                        self._update_card_data(card, machine_data)

                    # Add to layout
                    row = i // cols
                    col = i % cols
                    self.cards_layout.addWidget(self.machine_cards[loom_num], row, col)

                self.cards_widget.update()

        except Exception as e:
            self.main_window.logger.error(f"Error refreshing data: {e}")

    def _update_card_data(self, card, data):
        """Update existing card with new data"""
        try:
            # Update header and status
            header = card.findChild(QLabel, "header")
            if header:
                header.setText(f"{data.get('Loom_Num', '')}")

            # Update all fields in the grid
            grid = card.findChild(QGridLayout)
            if grid:
                self._update_field(grid, 0, 0, "Device Name:", data.get('Device_Name', ''))
                self._update_field(grid, 0, 1, "Weaving Length:", data.get('Weaving_Length', ''))
                self._update_field(grid, 1, 0, "Warp Remain:", data.get('Warp_Remain', ''))
                self._update_field(grid, 1, 1, "Warp Length:", data.get('Warp_Length', ''))
                self._update_field(grid, 2, 0, "Speed:", str(data.get('Speed', '')))
                self._update_field(grid, 2, 1, "Production Length:", str(data.get('Production_FabricLength', '')))
                self._update_field(grid, 3, 0, "Production Qty:", str(data.get('Production_Quantity', '')))
                
                # Update efficiency
                try:
                    efficiency = float(data.get('Efficiency', 0))
                    efficiency_color = "#27AE60" if efficiency >= 80 else "#E74C3C"
                    self._update_field(grid, 3, 1, "Efficiency:", f"{efficiency}%", efficiency_color)
                except (ValueError, TypeError):
                    self._update_field(grid, 3, 1, "Efficiency:", "N/A", "#E74C3C")

                # Update time values
                def safe_time_get(key):
                    try:
                        value = data.get(key, 0)
                        return str(int(float(value))) if value else "0"
                    except (ValueError, TypeError):
                        return "0"

                # Update both label and value for time display
                row_index = 6
                merged_label = grid.itemAtPosition(row_index * 2, 0).widget()
                merged_value = grid.itemAtPosition(row_index * 2 + 1, 0).widget()
                
                if merged_label and merged_value:
                    merged_label.setText("H1 : H2 : Wrap : Other : Total")
                    time_text = (f"{safe_time_get('H1Time')} : {safe_time_get('H2Time')} : "
                               f"{safe_time_get('WrapTime')} : {safe_time_get('OtherTime')} : "
                               f"{safe_time_get('TotalTime')}")
                    merged_value.setText(time_text)

        except Exception as e:
            self.main_window.logger.error(f"Error updating card: {e}")

    def _update_field(self, grid, row, col, label_text, value_text, value_color=None):
        """Update existing field in grid"""
        value_widget = grid.itemAtPosition(row * 2 + 1, col).widget()
        if value_widget:
            value_widget.setText(str(value_text))
            if value_color:
                value_widget.setStyleSheet(f"color: {value_color}; font-weight: bold;")

    def _update_merged_field(self, grid, time_text):
        """Update merged time field"""
        merged_value = grid.itemAtPosition(12, 0).widget()  # Adjust position as needed
        if merged_value:
            merged_value.setText(time_text)

    def create_page(self):
        self.main_window.logger.info("Creating DataPage")
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QLabel("Machine Status")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet("color: #2C3E50;")
        layout.addWidget(header)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #F0F0F0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #B0B0B0;
                border-radius: 5px;
            }
        """)

        # Container for cards
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(20)
        scroll.setWidget(self.cards_widget)
        layout.addWidget(scroll)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        layout.addLayout(button_layout)

        self.refresh_data()  # Load initial data
        # Start the data fetch thread
        if self.fetch_thread is None:
            self.fetch_thread = DataFetchThread(self.main_window.local_db)
            self.fetch_thread.data_fetched.connect(lambda x: self.refresh_data(x), Qt.QueuedConnection)
            self.fetch_thread.start()
            self.main_window.logger.info("Data fetch thread started")

        return container

    def stop_thread(self):
        """Method to be called when page is actually being closed"""
        try:
            if self.fetch_thread is not None:
                self.fetch_thread.stop()
                self.fetch_thread = None
                self.main_window.logger.info("Data fetch thread stopped")
        except Exception as e:
            self.main_window.logger.error(f"Error stopping data fetch thread: {e}")

    # Remove cleanup and __del__ methods as they're stopping the thread too early