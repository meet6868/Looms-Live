from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                            QComboBox, QCheckBox, QDateEdit, QPushButton, QTableWidget,
                            QTableWidgetItem, QSpinBox, QHeaderView, QSizePolicy, QCalendarWidget)
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import QPainter,QFont
import pandas as pd
from datetime import datetime, timedelta
from utils.path_utils import get_data_path, get_resource_path
import os

class ReportsPage:
    def __init__(self, main_page):
        self.main_page = main_page
        self.logger = main_page.logger
        self.current_page = 1
        self.rows_per_page = 20
        self.total_pages = 1
        self.filtered_data = []

    def create_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Reports title
        title = QLabel("Machine Data Reports")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        # Filter section
        filter_frame = QFrame()
        filter_frame.setStyleSheet("QFrame { background-color: white; border-radius: 10px; border: 1px solid #e0e0e0; }")
        filter_layout = QVBoxLayout(filter_frame)
        
        # Date filter with range control
        date_layout = QHBoxLayout()
        self.date_checkbox = QCheckBox("Date Range")
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-1))  # Set to today
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd-MM-yyyy")
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())  # Set to today
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd-MM-yyyy")
        self.end_date.setEnabled(False)  # Initially disabled
        
        # Style calendar popup
        calendar_style = """
            QCalendarWidget QToolButton {
                color: #2c3e50;
                background-color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QCalendarWidget QMenu {
                background-color: white;
            }
            QCalendarWidget QSpinBox {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #ecf0f1;
            }
            QCalendarWidget QWidget#qt_calendar_calendarview {
                background-color: white;
            }
        """
        self.start_date.calendarWidget().setStyleSheet(calendar_style)
        self.end_date.calendarWidget().setStyleSheet(calendar_style)
        self.date_checkbox.stateChanged.connect(self.toggle_date_range)
        date_layout.addWidget(self.date_checkbox)
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.end_date)
        date_layout.addStretch()
        filter_layout.addLayout(date_layout)
        
        # Machine filter
        machine_layout = QHBoxLayout()
        self.machine_combo = QComboBox()
        self.machine_combo.addItem("All Machines")
        # Add machine numbers from database
        machines = self.main_page.local_db.get_machine_numbers()
        self.machine_combo.addItems(machines)
        machine_layout.addWidget(QLabel("Machine:"))
        machine_layout.addWidget(self.machine_combo)
        machine_layout.addStretch()
        filter_layout.addLayout(machine_layout)
        
        # Rows per page
        page_layout = QHBoxLayout()
        self.rows_combo = QComboBox()
        self.rows_combo.addItems(["20", "30", "50"])
        self.rows_combo.currentTextChanged.connect(self.change_rows_per_page)
        page_layout.addWidget(QLabel("Rows per page:"))
        page_layout.addWidget(self.rows_combo)
        
        # Export button
        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        page_layout.addStretch()
        page_layout.addWidget(self.export_btn)
        filter_layout.addLayout(page_layout)
        
        layout.addWidget(filter_frame)
        
        # Table with responsive height
        table_container = QFrame()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget { 
                border: 1px solid #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        self.setup_table()
        
        # Make table responsive
        table_container.setMinimumHeight(200)  # Minimum height
        table_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table_layout.addWidget(self.table)
        
        layout.addWidget(table_container)
        
        # Add real-time curve chart
        chart_frame = QFrame()
        chart_layout = QVBoxLayout(chart_frame)
        chart_frame.setStyleSheet("QFrame { background-color: white; border-radius: 10px; border: 1px solid #e0e0e0; }")
        
        # Create chart using PyQtChart
        self.chart_view = self.setup_chart()
        chart_layout.addWidget(self.chart_view)
        # layout.addWidget(chart_frame)
        
        # Pagination
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.page_label = QLabel("Page 1 of 1")
        self.prev_btn.clicked.connect(self.previous_page)
        self.next_btn.clicked.connect(self.next_page)
        
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)
        
        # Connect filter changes
        self.date_checkbox.stateChanged.connect(lambda: self.refresh_data())
        self.start_date.dateChanged.connect(lambda: self.refresh_data())
        self.end_date.dateChanged.connect(lambda: self.refresh_data())
        self.machine_combo.currentTextChanged.connect(lambda: self.refresh_data())
        
        # Initial data load
        self.refresh_data()
        
        return page

    def toggle_date_range(self, state):
        """Enable/disable end date based on checkbox state"""
        is_checked = state == Qt.Checked
        self.end_date.setEnabled(is_checked)
        if is_checked:
            self.end_date.setDate(QDate.currentDate())
            self.start_date.setDate(QDate.currentDate().addMonths(-1))
        else:
            self.start_date.setDate(QDate.currentDate().addDays(-1))
        self.refresh_data()

    def setup_chart(self):
        """Setup real-time efficiency chart"""
        from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
        from PyQt5.QtCore import Qt, QDateTime
        
        # Create chart
        chart = QChart()
        chart.setTitle("Machine Efficiency Trend")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create series for A and B shifts
        self.series_a = QLineSeries()
        self.series_b = QLineSeries()
        self.series_a.setName("A Shift Efficiency")
        self.series_b.setName("B Shift Efficiency")
        
        # Add series to chart
        chart.addSeries(self.series_a)
        chart.addSeries(self.series_b)
        
        # Create axes
        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd-MM-yyyy")
        axis_x.setTitleText("Date")
        chart.addAxis(axis_x, Qt.AlignBottom)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, 100)
        axis_y.setTitleText("Efficiency (%)")
        chart.addAxis(axis_y, Qt.AlignLeft)
        
        self.series_a.attachAxis(axis_x)
        self.series_a.attachAxis(axis_y)
        self.series_b.attachAxis(axis_x)
        self.series_b.attachAxis(axis_y)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(300)
        
        return chart_view

    def update_chart(self, data):
        """Update chart with new data"""
        self.series_a.clear()
        self.series_b.clear()
        
        for row in data:
            date = QDateTime.fromString(row['date'], "yyyy-MM-dd").toMSecsSinceEpoch()
            if row['A_Efficiency']:
                self.series_a.append(date, float(row['A_Efficiency']))
            if row['B_Efficiency']:
                self.series_b.append(date, float(row['B_Efficiency']))

    def refresh_data(self):
        try:
            filters = {
                'date_range': self.date_checkbox.isChecked(),
                'start_date': self.start_date.date().toPyDate(),
                'end_date': self.end_date.date().toPyDate() if self.date_checkbox.isChecked() else None,
                'machine': self.machine_combo.currentText() if self.machine_combo.currentText() != "All Machines" else None
            }
            
            self.filtered_data = self.main_page.local_db.get_machine_data(filters)
            self.total_pages = max(1, (len(self.filtered_data) + self.rows_per_page - 1) // self.rows_per_page)
            self.current_page = 1  # Reset to first page when filters change
            
            self.update_table_data()
            self.update_pagination()
            
        except Exception as e:
            self.logger.error(f"Error refreshing report data: {str(e)}")

    def setup_table(self):
        columns = ["Date", "Device Name", "Loom Num", 
                  "A_Production_FabricLength", "A_Production_Quantity", "A_Speed", "A_Efficiency",
                  "B_Production_FabricLength", "B_Production_Quantity", "B_Speed", "B_Efficiency",
                  "Total_Production_FabricLength", "Total_Production_Quantity", "Avg_Speed", "Avg_Efficiency"]
        
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Make the last row (summary) stick to the bottom
        self.table.verticalHeader().setStretchLastSection(True)

    def refresh_data(self):
        try:
            filters = {
                'date_range': self.date_checkbox.isChecked(),
                'start_date': self.start_date.date().toPyDate(),
                'end_date': self.end_date.date().toPyDate() if self.date_checkbox.isChecked() else None,
                'machine': self.machine_combo.currentText() if self.machine_combo.currentText() != "All Machines" else None
            }
            
            self.filtered_data = self.main_page.local_db.get_machine_data(filters)
            self.total_pages = max(1, (len(self.filtered_data) + self.rows_per_page - 1) // self.rows_per_page)
            self.current_page = min(self.current_page, self.total_pages)
            
            self.update_table_data()
            self.update_pagination()
            
        except Exception as e:
            self.logger.error(f"Error refreshing report data: {str(e)}")

    def update_table_data(self):
        start_idx = (self.current_page - 1) * self.rows_per_page
        end_idx = min(start_idx + self.rows_per_page, len(self.filtered_data))  # Ensure we don't exceed data length
        page_data = self.filtered_data[start_idx:end_idx]
        
        self.table.setRowCount(len(page_data) + 1)  # +1 for summary row
        
        # Fill data rows
        for row, data in enumerate(page_data):
            self.fill_table_row(row, data)
        
        # Add summary row at the very end
        self.update_summary_row(len(page_data))

    def fill_table_row(self, row, data):
        columns = ["date", "Device_Name", "Loom_Num", 
                  "A_Production_FabricLength", "A_Production_Quantity", "A_Speed", "A_Efficiency",
                  "B_Production_FabricLength", "B_Production_Quantity", "B_Speed", "B_Efficiency",
                  "Total_Production_FabricLength", "Total_Production_Quantity", "Avg_Speed", "Avg_Efficiency"]
        
        for col, key in enumerate(columns):
            item = QTableWidgetItem(str(data.get(key, '')))
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col, item)

    def update_summary_row(self, last_row):
        sum_columns = ["A_Production_FabricLength", "A_Production_Quantity",
                      "B_Production_FabricLength", "B_Production_Quantity",
                      "Total_Production_FabricLength", "Total_Production_Quantity"]
        
        avg_columns = ["A_Speed", "A_Efficiency", "B_Speed", "B_Efficiency",
                      "Avg_Speed", "Avg_Efficiency"]
        
        summary = {}
        for col in sum_columns:
            summary[col] = sum(float(d.get(col, 0) or 0) for d in self.filtered_data)
            
        for col in avg_columns:
            values = [float(d.get(col, 0) or 0) for d in self.filtered_data if float(d.get(col, 0) or 0) > 0]
            summary[col] = sum(values) / len(values) if values else 0
        
        # Fill summary row
        self.table.setItem(last_row, 0, QTableWidgetItem("Summary"))
        self.table.item(last_row, 0).setFont(QFont("Segoe UI", weight=QFont.Bold))
        
        for col, key in enumerate(["A_Production_FabricLength", "A_Production_Quantity",
                                 "A_Speed", "A_Efficiency",
                                 "B_Production_FabricLength", "B_Production_Quantity",
                                 "B_Speed", "B_Efficiency",
                                 "Total_Production_FabricLength", "Total_Production_Quantity",
                                 "Avg_Speed", "Avg_Efficiency"]):
            if key in summary:
                item = QTableWidgetItem(f"{summary[key]:.2f}")
                item.setFont(QFont("Segoe UI", weight=QFont.Bold))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(last_row, col + 3, item)

    def change_rows_per_page(self, value):
        self.rows_per_page = int(value)
        self.current_page = 1
        self.refresh_data()

    def previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_table_data()
            self.update_pagination()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_table_data()
            self.update_pagination()

    def update_pagination(self):
        self.page_label.setText(f"Page {self.current_page} of {self.total_pages}")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)

    def export_to_excel(self):
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            
            if not self.filtered_data:
                QMessageBox.warning(None, "No Data", "No data available to export.")
                return
            
            # Set default save location to user's Documents folder
            documents_path = os.path.join(os.path.expanduser('~'), 'Documents')
            default_name = f"machine_data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            default_path = os.path.join(documents_path, default_name)
            
            filename, _ = QFileDialog.getSaveFileName(
                None, "Save Excel Report", default_path,
                "Excel Files (*.xlsx);;All Files (*.*)"
            )
            
            if not filename:
                return
                
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            
            # Create DataFrame with filtered data
            excel_data = []
            for data in self.filtered_data:
                row_data = {
                    'Date': data.get('date', ''),
                    'Device Name': data.get('Device_Name', ''),
                    'Loom Num': data.get('Loom_Num', ''),
                    'A_Production_FabricLength': float(data.get('A_Production_FabricLength', 0) or 0),
                    'A_Production_Quantity': float(data.get('A_Production_Quantity', 0) or 0),
                    'A_Speed': float(data.get('A_Speed', 0) or 0),
                    'A_Efficiency': float(data.get('A_Efficiency', 0) or 0),
                    'B_Production_FabricLength': float(data.get('B_Production_FabricLength', 0) or 0),
                    'B_Production_Quantity': float(data.get('B_Production_Quantity', 0) or 0),
                    'B_Speed': float(data.get('B_Speed', 0) or 0),
                    'B_Efficiency': float(data.get('B_Efficiency', 0) or 0),
                    'Total_Production_FabricLength': float(data.get('Total_Production_FabricLength', 0) or 0),
                    'Total_Production_Quantity': float(data.get('Total_Production_Quantity', 0) or 0),
                    'Avg_Speed': float(data.get('Avg_Speed', 0) or 0),
                    'Avg_Efficiency': float(data.get('Avg_Efficiency', 0) or 0)
                }
                excel_data.append(row_data)
            
            df = pd.DataFrame(excel_data)
            
            # Calculate summary row
            summary = {
                'Date': 'Summary',
                'Device Name': '',
                'Loom Num': '',
                'A_Production_FabricLength': df['A_Production_FabricLength'].sum(),
                'A_Production_Quantity': df['A_Production_Quantity'].sum(),
                'A_Speed': df['A_Speed'].mean(),
                'A_Efficiency': df['A_Efficiency'].mean(),
                'B_Production_FabricLength': df['B_Production_FabricLength'].sum(),
                'B_Production_Quantity': df['B_Production_Quantity'].sum(),
                'B_Speed': df['B_Speed'].mean(),
                'B_Efficiency': df['B_Efficiency'].mean(),
                'Total_Production_FabricLength': df['Total_Production_FabricLength'].sum(),
                'Total_Production_Quantity': df['Total_Production_Quantity'].sum(),
                'Avg_Speed': df['Avg_Speed'].mean(),
                'Avg_Efficiency': df['Avg_Efficiency'].mean()
            }
            
            # Add summary row to DataFrame
            df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)
            
            # Export to Excel with proper formatting
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
                
                workbook = writer.book
                worksheet = writer.sheets['Report']
                
                # Formats
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#D3D3D3',
                    'border': 1,
                    'align': 'center'
                })
                
                cell_format = workbook.add_format({
                    'border': 1,
                    'align': 'center'
                })
                
                summary_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#F0F0F0',
                    'border': 1,
                    'align': 'center'
                })
                
                # Apply formats
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)
                
                # Write data rows
                for row_num, row_data in enumerate(df.values[:-1], start=1):  # All rows except last
                    for col_num, value in enumerate(row_data):
                        worksheet.write(row_num, col_num, value, cell_format)
                
                # Write summary row separately
                last_row = len(df)
                for col_num, value in enumerate(df.values[-1]):  # Last row (summary)
                    worksheet.write(last_row - 1, col_num, value, summary_format)
            
            QMessageBox.information(None, "Export Successful", 
                                  f"Report has been exported to:\n{filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {str(e)}")
            QMessageBox.critical(None, "Export Failed", 
                               f"Failed to export report:\n{str(e)}")