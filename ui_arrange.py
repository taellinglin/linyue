import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer

class ArrangeTab(QWidget):
    def __init__(self):
        super().__init__()

        # === Main Layout: Left Sidebar + Grid + Right Sidebar ===
        main_layout = QHBoxLayout()

        # === LEFT SIDEBAR: PATTERN SELECTOR ===
        self.left_panel = self.create_sidebar('./projects/project_name/patterns', 'Patterns')
        main_layout.addWidget(self.left_panel, 2)

        # === MIDDLE: 12x12 SEQUENCER GRID ===
        self.setup_sequencer_grid(main_layout)

        # === RIGHT SIDEBAR: SAMPLE SELECTOR ===
        self.right_panel = self.create_sidebar('./projects/project_name/samples', 'Samples')
        main_layout.addWidget(self.right_panel, 2)

        self.setLayout(main_layout)

        # Sequencer State
        self.current_pattern = None
        self.current_sample = None
        self.pattern_data = [[None for _ in range(12)] for _ in range(12)]
        self.flash_state = [[False for _ in range(12)] for _ in range(12)]

        # Timer for flashing lights effect
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.flash_lights)
        self.flash_timer.start(500)  # Flash every 500ms

    def create_sidebar(self, directory, title):
        """Create a sidebar for patterns or samples."""
        panel = QWidget()
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.endswith('.pattern') or file.endswith('.wav'):
                    button = QPushButton(file)
                    button.setStyleSheet("background-color: #4682B4; color: white; padding: 5px;")
                    button.clicked.connect(lambda _, f=file: self.load_file(f, directory))
                    layout.addWidget(button)

        panel.setLayout(layout)
        return panel

    def load_file(self, file, directory):
        """Load a pattern or sample and set it as the current selection."""
        file_path = os.path.join(directory, file)
        if file.endswith('.pattern'):
            self.current_pattern = file_path
            print(f"Loaded pattern: {file}")
        elif file.endswith('.wav'):
            self.current_sample = file_path
            print(f"Loaded sample: {file}")

    def setup_sequencer_grid(self, main_layout):
        """Create a 12x12 grid for the sequencer."""
        self.grid_cells = []
        grid_layout = QVBoxLayout()

        for row in range(12):
            row_layout = QHBoxLayout()
            row_cells = []
            for col in range(12):
                cell_button = QPushButton("")
                cell_button.setFixedSize(50, 50)
                cell_button.clicked.connect(lambda _, r=row, c=col: self.cell_clicked(r, c))
                row_cells.append(cell_button)
                row_layout.addWidget(cell_button)
            self.grid_cells.append(row_cells)
            grid_layout.addLayout(row_layout)

        main_layout.addLayout(grid_layout, 8)

    def cell_clicked(self, row, col):
        """Assign the selected pattern or sample to a grid cell."""
        if self.current_pattern:
            self.pattern_data[row][col] = ('pattern', self.current_pattern)
            self.grid_cells[row][col].setStyleSheet("background-color: #FFFF00;")
        elif self.current_sample:
            self.pattern_data[row][col] = ('sample', self.current_sample)
            self.grid_cells[row][col].setStyleSheet("background-color: #FFA500;")

    def flash_lights(self):
        """Handle flashing effects based on playback state."""
        for row in range(12):
            for col in range(12):
                if self.pattern_data[row][col]:
                    cell_type, _ = self.pattern_data[row][col]
                    color = "#FF0000" if cell_type == 'sample' else "#0000FF"  # Red for sample, Blue for pattern
                    self.grid_cells[row][col].setStyleSheet(f"background-color: {color};")
