from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QLabel, 
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QSizePolicy, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QScrollArea, QComboBox, QSizePolicy)

class SequencerTab(QWidget):
    def __init__(self, parent_node):
        super().__init__()

        self.samples = parent_node.samples  # List of samples to populate the dropdown
        self.patterns = parent_node.patterns  # Placeholder for pattern data
        
        # === Main Layout: Left Sidebar + Right Section ===
        main_layout = QHBoxLayout()

        # === LEFT PANEL: PATTERN SELECTOR (20% width, scrollable) ===
        self.left_panel = QWidget()
        self.left_panel_layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #333; padding: 10px; color: white;")

        self.pattern_widget = QWidget()
        self.pattern_layout = QVBoxLayout()

        # Create pattern list
        self.create_pattern_list()

        self.pattern_widget.setLayout(self.pattern_layout)
        self.scroll_area.setWidget(self.pattern_widget)
        self.left_panel_layout.addWidget(self.scroll_area)
        self.left_panel.setLayout(self.left_panel_layout)

        main_layout.addWidget(self.left_panel, 2)  # 20% width

        # === RIGHT SECTION: Vertical Layout (Playback Panel + Sequencer Grid) ===
        right_section = QVBoxLayout()

        # === TOP PANEL: PLAYBACK CONTROLS ===
        self.playback_panel = QWidget()
        self.playback_layout = QHBoxLayout()

        self.play_button = QPushButton("Play")
        self.play_button.setStyleSheet("background-color: #00FF00; color: white; padding: 10px;")

        self.pause_button = QPushButton("Pause")
        self.pause_button.setStyleSheet("background-color: #FF4500; color: white; padding: 10px;")

        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("background-color: #DC143C; color: white; padding: 10px;")

        self.rewind_button = QPushButton("Rewind")
        self.rewind_button.setStyleSheet("background-color: #0000FF; color: white; padding: 10px;")

        self.fast_forward_button = QPushButton("Fast Forward")
        self.fast_forward_button.setStyleSheet("background-color: #0000FF; color: white; padding: 10px;")

        # Sample selection dropdown
        self.sample_dropdown = QComboBox()
        self.sample_dropdown.addItems(self.samples)  # Add sample names to the dropdown
        self.sample_dropdown.setStyleSheet("background-color: #333; color: white; padding: 10px;")
        
        self.playback_layout.addWidget(self.play_button)
        self.playback_layout.addWidget(self.pause_button)
        self.playback_layout.addWidget(self.stop_button)
        self.playback_layout.addWidget(self.rewind_button)
        self.playback_layout.addWidget(self.fast_forward_button)
        self.playback_layout.addWidget(self.sample_dropdown)  # Add the dropdown next to buttons

        self.playback_panel.setLayout(self.playback_layout)
        self.playback_panel.setFixedHeight(60)  # Fixed height for playback controls
        right_section.addWidget(self.playback_panel)

        # === BOTTOM PANEL: SEQUENCER GRID (Resizable, Scrollable) ===
        self.sequencer_panel = QWidget()
        self.sequencer_layout = QVBoxLayout()

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()

        # Create a black & gray grid (1 row, 16+ columns)
        for col in range(16):  # Expandable grid
            cell = QPushButton()
            cell.setFixedSize(50, 50)
            cell.setStyleSheet("background-color: #222; border: 1px solid #444;")
            cell.setToolTip(f"Step {col+1}")
            self.grid_layout.addWidget(cell, 0, col)

        self.grid_widget.setLayout(self.grid_layout)
        self.grid_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Scrollable area for the sequencer grid
        grid_scroll_area = QScrollArea()
        grid_scroll_area.setWidget(self.grid_widget)
        grid_scroll_area.setWidgetResizable(True)
        grid_scroll_area.setStyleSheet("background-color: black;")

        self.sequencer_layout.addWidget(grid_scroll_area)
        self.sequencer_panel.setLayout(self.sequencer_layout)
        right_section.addWidget(self.sequencer_panel)

        # === ADD RIGHT SECTION TO MAIN LAYOUT ===
        main_layout.addLayout(right_section, 8)  # Remaining 80% width

        self.setLayout(main_layout)

    def create_pattern_list(self):
        """Create sample pattern list with numbered buttons."""
        self.pattern_buttons = []  # List to hold pattern buttons
        colors = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082', '#9400D3']
        
        # Add sample patterns (up to 7 initially, or dynamically based on project data)
        for i in range(7):  # Add 7 sample patterns initially
            pattern_button = QPushButton(f"[{i:02}]")
            pattern_button.setStyleSheet(f"background-color: {colors[i % len(colors)]}; color: white; padding: 10px;")
            self.pattern_layout.addWidget(pattern_button)
            self.pattern_buttons.append(pattern_button)

        # "Add Pattern" button at bottom
        self.add_pattern_button = QPushButton("[+] Add Pattern")
        self.add_pattern_button.setStyleSheet("background-color: #4682B4; color: white; padding: 10px; margin-top: 10px;")
        self.pattern_layout.addWidget(self.add_pattern_button)

    def update_patterns(self, patterns):
        """Update the pattern list when a project is loaded."""
        # Clear the current pattern list
        for button in self.pattern_buttons:
            button.deleteLater()
        
        self.pattern_buttons = []

        # Add patterns from the loaded project
        colors = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082', '#9400D3']
        for i, pattern in enumerate(patterns):  # Load patterns dynamically from the project
            pattern_button = QPushButton(pattern['name'])  # Use the pattern name here
            pattern_button.setStyleSheet(f"background-color: {colors[i % len(colors)]}; color: white; padding: 10px;")
            self.pattern_layout.addWidget(pattern_button)
            self.pattern_buttons.append(pattern_button)

    def update_sequencer_grid(self, grid_data):
        """Update the sequencer grid with steps based on loaded project data."""
        for i, cell in enumerate(self.grid_layout.itemAt(i).widget() for i in range(self.grid_layout.count())):
            cell.setStyleSheet("background-color: #222; border: 1px solid #444;")  # Reset colors

        for i, step in enumerate(grid_data):  # Assuming grid_data contains a list of step states
            cell = self.grid_layout.itemAt(i).widget()
            if step:  # If the step is active
                cell.setStyleSheet("background-color: #00FF00; border: 1px solid #444;")  # Active step color