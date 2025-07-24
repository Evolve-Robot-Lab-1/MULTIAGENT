#!/usr/bin/env python3
"""
DocAI Native - Operation Tracker GUI
A native desktop application for tracking file operations and implementation progress
"""

import sys
import json
import webbrowser
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton,
                            QLabel, QTextEdit, QSplitter, QGroupBox, QProgressBar,
                            QTabWidget, QMenuBar, QMenu, QAction, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QColor, QFont

class OperationTrackerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle("DocAI Native - Operation Tracker & Completion Status")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Stats panel
        stats_widget = self.create_stats_panel()
        main_layout.addWidget(stats_widget)
        
        # Create tab widget for different views
        self.tabs = QTabWidget()
        
        # Tree view tab
        tree_tab = self.create_tree_view_tab()
        self.tabs.addTab(tree_tab, "🌳 Tree View")
        
        # Progress view tab
        progress_tab = self.create_progress_view_tab()
        self.tabs.addTab(progress_tab, "📊 Progress View")
        
        # Details view tab
        details_tab = self.create_details_view_tab()
        self.tabs.addTab(details_tab, "📋 Details View")
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Apply stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QTreeWidget::item {
                padding: 5px;
                margin: 2px;
            }
            QTreeWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        export_action = QAction('Export Report', self)
        export_action.triggered.connect(self.export_report)
        file_menu.addAction(export_action)
        
        refresh_action = QAction('Refresh', self)
        refresh_action.triggered.connect(self.refresh_data)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        expand_all_action = QAction('Expand All', self)
        expand_all_action.triggered.connect(self.expand_all_trees)
        view_menu.addAction(expand_all_action)
        
        collapse_all_action = QAction('Collapse All', self)
        collapse_all_action.triggered.connect(self.collapse_all_trees)
        view_menu.addAction(collapse_all_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        open_html_action = QAction('Open HTML Version', self)
        open_html_action.triggered.connect(self.open_html_version)
        help_menu.addAction(open_html_action)
        
    def create_stats_panel(self):
        stats_group = QGroupBox("📊 Overall Progress")
        stats_layout = QHBoxLayout()
        
        # Create stat cards
        self.stat_labels = {}
        stats = [
            ('total', 'Total Operations', '#17a2b8'),
            ('complete', 'Completed', '#28a745'),
            ('progress', 'In Progress', '#ffc107'),
            ('pending', 'Pending', '#dc3545')
        ]
        
        for key, label, color in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout()
            
            label_widget = QLabel(label)
            label_widget.setAlignment(Qt.AlignCenter)
            
            value_widget = QLabel("0")
            value_widget.setAlignment(Qt.AlignCenter)
            value_widget.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            self.stat_labels[key] = value_widget
            
            stat_layout.addWidget(label_widget)
            stat_layout.addWidget(value_widget)
            stat_widget.setLayout(stat_layout)
            
            stats_layout.addWidget(stat_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        stats_layout.addWidget(self.progress_bar)
        
        stats_group.setLayout(stats_layout)
        return stats_group
        
    def create_tree_view_tab(self):
        widget = QWidget()
        layout = QHBoxLayout()
        
        # File operations tree
        file_ops_group = QGroupBox("📁 File Operations")
        file_ops_layout = QVBoxLayout()
        
        # Filter buttons
        filter_layout = QHBoxLayout()
        self.filter_buttons = {}
        for filter_type in ['All', 'Keep', 'Remove', 'Modify']:
            btn = QPushButton(filter_type)
            btn.clicked.connect(lambda checked, f=filter_type.lower(): self.filter_tree(f))
            self.filter_buttons[filter_type.lower()] = btn
            filter_layout.addWidget(btn)
        filter_layout.addStretch()
        file_ops_layout.addLayout(filter_layout)
        
        self.file_ops_tree = QTreeWidget()
        self.file_ops_tree.setHeaderLabels(['Operation', 'Status', 'Action'])
        self.file_ops_tree.itemSelectionChanged.connect(self.on_file_ops_selection)
        file_ops_layout.addWidget(self.file_ops_tree)
        
        file_ops_group.setLayout(file_ops_layout)
        
        # Implementation tree
        impl_group = QGroupBox("✅ Implementation Progress")
        impl_layout = QVBoxLayout()
        
        self.impl_tree = QTreeWidget()
        self.impl_tree.setHeaderLabels(['Task', 'Status', 'Progress'])
        self.impl_tree.itemSelectionChanged.connect(self.on_impl_selection)
        impl_layout.addWidget(self.impl_tree)
        
        impl_group.setLayout(impl_layout)
        
        # Add to layout with splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(file_ops_group)
        splitter.addWidget(impl_group)
        splitter.setSizes([700, 700])
        
        layout.addWidget(splitter)
        widget.setLayout(layout)
        
        return widget
        
    def create_progress_view_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Phase progress bars
        phases = [
            ('Phase 1: Fix PyWebView API', 20),
            ('Phase 2: Clean Frontend', 0),
            ('Phase 3: Connect Frontend/Backend', 0),
            ('Phase 4: Test & Verify', 0),
            ('Phase 5: Polish & Error Handling', 0)
        ]
        
        for phase_name, progress in phases:
            phase_group = QGroupBox(phase_name)
            phase_layout = QVBoxLayout()
            
            progress_bar = QProgressBar()
            progress_bar.setValue(progress)
            progress_bar.setTextVisible(True)
            phase_layout.addWidget(progress_bar)
            
            phase_group.setLayout(phase_layout)
            layout.addWidget(phase_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        return widget
        
    def create_details_view_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 10))
        
        layout.addWidget(self.details_text)
        widget.setLayout(layout)
        
        return widget
        
    def load_data(self):
        """Load operation data and populate trees"""
        # File operations data
        self.populate_file_ops_tree()
        self.populate_impl_tree()
        self.update_stats()
        
    def populate_file_ops_tree(self):
        """Populate file operations tree with data"""
        self.file_ops_tree.clear()
        
        # Frontend operations
        frontend = QTreeWidgetItem(self.file_ops_tree, ['Frontend File Operations', '', ''])
        
        # index.html
        index_html = QTreeWidgetItem(frontend, ['index.html', '', ''])
        
        web_picker = QTreeWidgetItem(index_html, 
            ['handleWebOpenFile (Lines 156-275)', '❌ Broken', '🗑️ Remove'])
        web_picker.setData(0, Qt.UserRole, {
            'issue': 'FileReader.onload never fires in PyWebView',
            'recommendation': 'Replace with native file picker'
        })
        
        router_func = QTreeWidgetItem(index_html,
            ['handleOpenFile Router (Line 273)', '⚠️ Needs Fix', '✏️ Modify'])
        
        # native-integration.js
        native_int = QTreeWidgetItem(frontend, ['native-integration.js', '', ''])
        
        native_open = QTreeWidgetItem(native_int,
            ['handleNativeOpenFile', '✅ Working', '✅ Keep'])
        native_open.setData(0, Qt.UserRole, {
            'issue': 'None - Properly implemented',
            'recommendation': 'This is the correct implementation'
        })
        
        # Backend operations
        backend = QTreeWidgetItem(self.file_ops_tree, ['Backend File Operations', '', ''])
        
        # main.py
        main_py = QTreeWidgetItem(backend, ['main.py', '', ''])
        api_reg = QTreeWidgetItem(main_py,
            ['API Registration (Line 216)', '🔴 Critical Bug', '✏️ Fix'])
        api_reg.setData(0, Qt.UserRole, {
            'issue': 'Using dict instead of class instance',
            'recommendation': 'Use SimpleNativeAPI instance immediately'
        })
        
        # Expand all by default
        self.file_ops_tree.expandAll()
        
        # Adjust column widths
        for i in range(3):
            self.file_ops_tree.resizeColumnToContents(i)
            
    def populate_impl_tree(self):
        """Populate implementation progress tree"""
        self.impl_tree.clear()
        
        # Phase 1
        phase1 = QTreeWidgetItem(self.impl_tree, 
            ['Phase 1: Fix PyWebView API Registration', '🔄 In Progress', '20%'])
        
        tasks = [
            ('Fix Import Statement', '⏳ Pending'),
            ('Create API Instance', '⏳ Pending'),
            ('Set Window Reference', '⏳ Pending'),
            ('Enable Debug Mode', '⏳ Pending'),
            ('Verify API Injection', '⏳ Pending')
        ]
        
        for task, status in tasks:
            QTreeWidgetItem(phase1, [task, status, ''])
        
        # Phase 2-5
        phases = [
            'Phase 2: Clean Up Frontend File Operations',
            'Phase 3: Connect Frontend to Backend',
            'Phase 4: Test & Verify',
            'Phase 5: Polish & Error Handling'
        ]
        
        for phase in phases:
            QTreeWidgetItem(self.impl_tree, [phase, '⏸️ Not Started', '0%'])
        
        self.impl_tree.expandAll()
        
        # Adjust column widths
        for i in range(3):
            self.impl_tree.resizeColumnToContents(i)
            
    def update_stats(self):
        """Update statistics display"""
        total = 15  # Total tasks
        complete = 0
        in_progress = 1
        pending = 14
        
        self.stat_labels['total'].setText(str(total))
        self.stat_labels['complete'].setText(str(complete))
        self.stat_labels['progress'].setText(str(in_progress))
        self.stat_labels['pending'].setText(str(pending))
        
        # Update progress bar
        progress = int((complete / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        
    def on_file_ops_selection(self):
        """Handle file operations tree selection"""
        selected = self.file_ops_tree.selectedItems()
        if selected:
            item = selected[0]
            data = item.data(0, Qt.UserRole)
            if data:
                details = f"**{item.text(0)}**\n\n"
                details += f"Status: {item.text(1)}\n"
                details += f"Action: {item.text(2)}\n\n"
                if 'issue' in data:
                    details += f"Issue: {data['issue']}\n\n"
                if 'recommendation' in data:
                    details += f"Recommendation: {data['recommendation']}\n"
                self.details_text.setPlainText(details)
                self.tabs.setCurrentIndex(2)  # Switch to details tab
                
    def on_impl_selection(self):
        """Handle implementation tree selection"""
        selected = self.impl_tree.selectedItems()
        if selected:
            item = selected[0]
            details = f"**{item.text(0)}**\n\n"
            details += f"Status: {item.text(1)}\n"
            if item.text(2):
                details += f"Progress: {item.text(2)}\n"
            self.details_text.setPlainText(details)
            self.tabs.setCurrentIndex(2)  # Switch to details tab
            
    def filter_tree(self, filter_type):
        """Filter file operations tree"""
        # Update button states
        for key, btn in self.filter_buttons.items():
            btn.setStyleSheet("")
        self.filter_buttons[filter_type].setStyleSheet("background-color: #007bff; color: white;")
        
        # Apply filter
        root = self.file_ops_tree.invisibleRootItem()
        self.filter_tree_recursive(root, filter_type)
        
    def filter_tree_recursive(self, item, filter_type):
        """Recursively filter tree items"""
        for i in range(item.childCount()):
            child = item.child(i)
            
            if filter_type == 'all':
                child.setHidden(False)
            else:
                action = child.text(2).lower()
                should_show = False
                
                if filter_type == 'keep' and 'keep' in action:
                    should_show = True
                elif filter_type == 'remove' and 'remove' in action:
                    should_show = True
                elif filter_type == 'modify' and ('modify' in action or 'fix' in action):
                    should_show = True
                
                child.setHidden(not should_show)
            
            # Recurse
            self.filter_tree_recursive(child, filter_type)
            
    def expand_all_trees(self):
        """Expand all tree widgets"""
        self.file_ops_tree.expandAll()
        self.impl_tree.expandAll()
        
    def collapse_all_trees(self):
        """Collapse all tree widgets"""
        self.file_ops_tree.collapseAll()
        self.impl_tree.collapseAll()
        
    def refresh_data(self):
        """Refresh all data"""
        self.load_data()
        self.statusBar().showMessage("Data refreshed", 2000)
        
    def export_report(self):
        """Export report to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Report", "docai_tracker_report.txt", "Text Files (*.txt)")
        
        if filename:
            with open(filename, 'w') as f:
                f.write("DocAI Native - Operation Tracker Report\n")
                f.write("=" * 50 + "\n\n")
                f.write("Overall Progress:\n")
                f.write(f"Total Operations: {self.stat_labels['total'].text()}\n")
                f.write(f"Completed: {self.stat_labels['complete'].text()}\n")
                f.write(f"In Progress: {self.stat_labels['progress'].text()}\n")
                f.write(f"Pending: {self.stat_labels['pending'].text()}\n")
                f.write(f"Progress: {self.progress_bar.value()}%\n")
                f.write("\nSee HTML version for detailed tree view.\n")
            
            self.statusBar().showMessage(f"Report exported to {filename}", 3000)
            
    def open_html_version(self):
        """Open HTML version in browser"""
        html_path = Path(__file__).parent / "operation_tracker_gui.html"
        if html_path.exists():
            webbrowser.open(str(html_path))
        else:
            self.statusBar().showMessage("HTML file not found", 3000)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DocAI Operation Tracker")
    
    # Set application icon if available
    # app.setWindowIcon(QIcon('icon.png'))
    
    window = OperationTrackerGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()