import os
import json
import zipfile
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget, QSlider, QLabel, QPushButton,
                             QMenuBar, QMenu, QAction, QFileDialog, QLineEdit, QSpinBox, QComboBox, QFormLayout)
from ui_sequencer import SequencerTab
from ui_composer import ComposerTab
from ui_mixer import MixerTab
from ui_sampler import SamplerTab
from ui_arrange import ArrangeTab
from PyQt5.QtCore import Qt, QMimeData, QEvent
from PyQt5.QtGui import QPixmap, QPainter, QDrag

from PyQt5.QtWidgets import QPushButton
import glob
class DraggableButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)

    def mousePressEvent(self, event):
        """Start the drag when mouse is pressed."""
        if event.button() == Qt.LeftButton:
            mime_data = QMimeData()
            mime_data.setText(self.text())  # Store the button's text as data

            drag = QDrag(self)
            drag.setMimeData(mime_data)
            
            # Optionally, set a pixmap to represent the dragged button
            pixmap = self.grab()
            drag.setPixmap(pixmap)

            # Start the drag
            drag.exec_(Qt.MoveAction)

        # Call base class's mousePressEvent to keep the normal button behavior
        super().mousePressEvent(event)

class TrackerDAWUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tracker DAW")
        self.setGeometry(0, 0, 1920, 1080)  # Full-screen dimensions
        self.samples = {}
        self.patterns = []
        self.project_name = "Untitled"  # Default to an empty string instead of None
        self.time_signature = "4/4"
        self.samples = self.get_sample_list()    # Initialize Tabs
        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)
        
        # Project Settings Tab (first tab)
        self.project_tab = QWidget()
        self.tabs.addTab(self.project_tab, "Project Settings")
        self.setup_project_settings()
        self.project_data = self.get_project_data()
        print(enumerate(self.project_data.get("samples")))
        self.samples = self.get_sample_list()
        
        # Add other Tabs
        self.arrange_tab = ArrangeTab()
        self.tabs.addTab(self.arrange_tab, "Arrange")
        
        self.sequencer_tab = SequencerTab(self.samples, self.get_patterns_data())
        self.tabs.addTab(self.sequencer_tab, "Sequencer")
        
        self.composer_tab = ComposerTab(self.samples, self.get_patterns_data(), self.project_name, self.time_signature)
        self.tabs.addTab(self.composer_tab, "Composer")
        
        self.mixer_tab = MixerTab()
        self.tabs.addTab(self.mixer_tab, "Mixer")

        # Ensure self.project_name is not None when passing it to SamplerTab
        self.sampler_tab = SamplerTab(self.samples, self.project_name or "Untitled")
        self.tabs.addTab(self.sampler_tab, "Sampler")
        
        # Setup Menu Bar
        self.menu_bar = self.menuBar()
        self.setup_menu()

        # Connect the tabChanged signal to the function that updates the SamplerTab
        self.tabs.currentChanged.connect(self.update_sampler_tab)

        self.current_project = {}
    def load_sample_files(self):
        """Scans the project's sample folder and updates self.samples with .sample files."""
        samples_folder = os.path.join("projects", self.project_name, "samples")

        if not os.path.exists(samples_folder):
            print(f"Samples folder not found: {samples_folder}")
            return

        sample_files = glob.glob(os.path.join(samples_folder, "*.sample"))

        for sample_path in sample_files:
            sample_name = os.path.splitext(os.path.basename(sample_path))[0]
            
            # Ensure sample_name is valid
            if not sample_name or sample_name.strip() == "":
                print(f"Skipping invalid sample file: {sample_path}")
                continue

            self.samples[sample_name] = sample_path  # Ensure self.samples is a dictionary

        print(f"Loaded {len(self.samples)} sample files.")
    def initialize_tabs(self):
        # Ensure project name is not None or empty when passing to tabs
        project_name = self.project_name or "Untitled"
        time_signature = self.time_signature
        # Add other Tabs
        self.arrange_tab = ArrangeTab()
        self.tabs.addTab(self.arrange_tab, "Arrange")

        self.sequencer_tab = SequencerTab(self.samples, self.get_patterns_data())
        self.tabs.addTab(self.sequencer_tab, "Sequencer")

        self.composer_tab = ComposerTab(self.samples, self.get_patterns_data(), self.project_name, time_signature)
        self.tabs.addTab(self.composer_tab, "Composer")

        self.mixer_tab = MixerTab()
        self.tabs.addTab(self.mixer_tab, "Mixer")

        # Pass the correct project name to the SamplerTab
        self.sampler_tab = SamplerTab(self.samples, project_name)
        self.tabs.addTab(self.sampler_tab, "Sampler")

    def update_sampler_tab(self):
        """Update the SamplerTab with the current project name."""
        # Whenever the "Samples" tab is clicked, update its project name
        if self.tabs.currentIndex() == 4:  # Check if the "Samples" tab is selected (index 4)
            self.sampler_tab.update_project_name(self.project_name)

        
    def get_sample_list(self):
        # Retrieve the list of samples from the project's data
        # For example, if samples are stored as dictionaries with 'name' keys:
        return [sample['name'] for sample in self.samples]

    def setup_project_settings(self):
        layout = QFormLayout()
        
        self.project_name_input = QLineEdit()
        layout.addRow("Project Name:", self.project_name_input)
        
        self.bpm_input = QSpinBox()
        self.bpm_input.setRange(30, 300)
        self.bpm_input.setValue(120)
        layout.addRow("BPM:", self.bpm_input)
        
        self.time_signature = QComboBox()
        self.time_signature.addItems(["4/4", "3/4", "6/8", "5/4", "7/8"])
        layout.addRow("Time Signature:", self.time_signature)
        
        self.key_signature = QComboBox()
        self.key_signature.addItems(["C Major", "G Major", "D Major", "A Minor", "E Minor"])
        layout.addRow("Key Signature:", self.key_signature)
        
        self.project_tab.setLayout(layout)
    
    def setup_menu(self):
        file_menu = self.menu_bar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As", self)
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        load_action = QAction("Load", self)
        load_action.triggered.connect(self.load_project)
        file_menu.addAction(load_action)
        
        pack_action = QAction("Pack Project", self)
        pack_action.triggered.connect(self.pack_project)
        file_menu.addAction(pack_action)
    
    def new_project(self):
        self.project_name_input.clear()
        self.bpm_input.setValue(120)
        self.time_signature.setCurrentIndex(0)
        self.key_signature.setCurrentIndex(0)
        self.current_project = {}
        self.project_name = None
        print("New project initialized")
    
    def save_project(self):
        """Save the project to a predefined or new location."""
        project_name = self.project_name_input.text()
        self.project_name = project_name
        
        # Check if project name is valid
        if not project_name:
            print("Project name is required to save.")
            return
        
        project_folder = f"./projects/{project_name}"
        
        # Create project folder if it doesn't exist
        if not os.path.exists(project_folder):
            os.makedirs(project_folder)  # Create project directory
        
        # Create subfolders for samples and patterns
        samples_folder = os.path.join(project_folder, "samples")
        patterns_folder = os.path.join(project_folder, "patterns")
        
        if not os.path.exists(samples_folder):
            os.makedirs(samples_folder)  # Create samples folder
        
        if not os.path.exists(patterns_folder):
            os.makedirs(patterns_folder)  # Create patterns folder
        
        # Define the project file path
        project_file_path = os.path.join(project_folder, f"{project_name}.project")
        
        # Prepare project data
        project_data = self.get_project_data()  # Get existing project data
        
        # Add sample names to project data (assuming self.samples holds the sample data)
        project_data['samples'] = self.save_samples(samples_folder)  # Save samples in the new folder
        project_data['patterns'] = self.save_patterns(patterns_folder)  # Save patterns in the new folder
        
        # Save project data to the project file
        try:
            with open(project_file_path, 'w') as file:
                json.dump(project_data, file, indent=4)
            print(f"Project saved in {project_file_path}")
        except Exception as e:
            print(f"Error saving project: {e}")




    def save_project_as(self):
        """Prompt the user to choose a new name and save the project."""
        folder_name = self.project_name_input.text()
        
        # Check if folder name is valid
        if not folder_name:
            print("Project name is required to save.")
            return
        
        project_folder = f"./projects/{folder_name}"
        
        # Create project folder if it doesn't exist
        if not os.path.exists(project_folder):
            os.makedirs(project_folder)  # Create project directory
        
        # Create subfolders for samples and patterns
        samples_folder = os.path.join(project_folder, "samples")
        patterns_folder = os.path.join(project_folder, "patterns")
        
        if not os.path.exists(samples_folder):
            os.makedirs(samples_folder)  # Create samples folder
        
        if not os.path.exists(patterns_folder):
            os.makedirs(patterns_folder)  # Create patterns folder
        
        # Define the project file path
        project_file_path = os.path.join(project_folder, f"{folder_name}.project")
        
        # Save project data to the project file
        try:
            project_data = self.get_project_data()  # Get existing project data
            
            # Add sample names to project data
            project_data['samples'] = self.save_samples(samples_folder)  # Save samples
            project_data['patterns'] = self.save_patterns(patterns_folder)  # Save patterns
            
            with open(project_file_path, 'w') as file:
                json.dump(project_data, file, indent=4)
            print(f"Project saved as {project_file_path}")
        except Exception as e:
            print(f"Error saving project: {e}")

    def save_samples(self, samples_folder):
        """Save the samples to the specified folder."""
        saved_sample_paths = []
        
        for sample in self.samples:
            # Assuming sample is an object that has a `filename` and `data`
            sample_path = os.path.join(samples_folder, os.path.basename(sample['filename']))
            
            # Copy the actual sample file to the new location
            try:
                shutil.copy(sample['filename'], sample_path)
                saved_sample_paths.append(sample_path)  # Track the saved path for project data
            except Exception as e:
                print(f"Error saving sample {sample['filename']}: {e}")
        
        return saved_sample_paths

    def save_patterns(self, patterns_folder):
        """Save the patterns to the specified folder."""
        saved_pattern_paths = []
        
        for pattern in self.patterns:
            # Assuming pattern is an object that has a `filename` or `data`
            pattern_path = os.path.join(patterns_folder, os.path.basename(pattern['filename']))
            
            # Save the pattern file to the new location (or you could copy it, depending on data)
            try:
                shutil.copy(pattern['filename'], pattern_path)
                saved_pattern_paths.append(pattern_path)  # Track the saved path for project data
            except Exception as e:
                print(f"Error saving pattern {pattern['filename']}: {e}")
        
        return saved_pattern_paths

    def load_project(self):
        """Load a project file and update the UI."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "Project Files (*.project)")
        
        if file_name:
            try:
                # Open and load project data
                with open(file_name, 'r') as file:
                    data = json.load(file)

                # Ensure the project has a name before proceeding
                self.project_name = self.get_project_name_from_file(data)  # Set the project name
                if not self.project_name:
                    print("Error: Project file is missing a name!")
                    return  # Exit early to prevent errors
                
                # Load project samples and other data
                self.samples = self.load_samples(file_name)  # Load samples from the project file
                
                # Reinitialize tabs with the correct project name
                self.initialize_tabs()

                print(f"Project loaded: {self.project_name}")  # Debugging output

                # Populate the sample dropdown and update other UI elements
                sample_names = self.get_sample_list()
                self.composer_tab.populate_sample_dropdown(sample_names)
                self.sampler_tab.update_project_name(self.project_name)

                self.set_project_data(data)  # Populate UI with loaded project data
                self.current_project = data  # Store loaded project data
                
            except Exception as e:
                print(f"Error loading project: {e}")  # Handle loading errors

            
    def rename_project(self, new_project_name):
        self.project_name = new_project_name  # Set the new project name
        
        # Reinitialize tabs with the new project name
        self.initialize_tabs()


    
    def pack_project(self):
        # Ask for location to save the packed file
        packed_filename, _ = QFileDialog.getSaveFileName(self, "Pack Project", "", "Project Files (*.project)")
        if packed_filename:
            zip_filename = packed_filename + ".zip"
            
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                # Save the .song project data
                song_data = self.get_project_data()
                zipf.writestr("project.song", json.dumps(song_data, indent=4))
                
                # Pack .pattern files (you need to collect all pattern files in your project)
                for pattern_filename in self.collect_pattern_files():
                    zipf.write(pattern_filename, os.path.basename(pattern_filename))
                
                # Pack sample files (you need to collect all sample files)
                for sample_filename in self.collect_sample_files():
                    zipf.write(sample_filename, os.path.basename(sample_filename))
            
            print(f"Project packed into {zip_filename}")
    
    def collect_pattern_files(self):
        # Collect all pattern files (.pattern) used in the project
        pattern_files = []
        for pattern in self.current_project.get('patterns', []):
            pattern_files.append(pattern['filename'])
        return pattern_files
    
    def collect_sample_files(self):
        # Collect all sample files (.wav) used in the project
        sample_files = []
        for sample in self.current_project.get('samples', []):
            sample_files.append(sample['filename'])
        return sample_files
    
    def get_project_data(self):
        # Collect and return project data including patterns and samples
        return {
            "name": self.project_name_input.text(),
            "bpm": self.bpm_input.value(),
            "time_signature": self.time_signature.currentText(),
            "key_signature": self.key_signature.currentText(),
            "patterns": self.get_patterns_data(),
            "samples": self.get_samples_data()
        }
    
    def get_patterns_data(self):
        # Collect patterns data (stub, adjust based on how patterns are managed in your project)
        return [{"name": "Pattern 1", "filename": "pattern1.pattern"}]
    
    def get_samples_data(self):
        # Collect samples data (stub, adjust based on how samples are managed in your project)
        return [{"name": "Sample 1", "filename": "sample1.wav"}]
    
    def set_project_data(self, data):
        """Populate the GUI with loaded project data."""
        # Update Project Properties
        self.project_name_input.setText(data.get("name", ""))
        self.bpm_input.setValue(data.get("bpm", 120))
        self.time_signature.setCurrentText(data.get("time_signature", "4/4"))
        self.key_signature.setCurrentText(data.get("key_signature", "C Major"))
        
        # Update the Sample List (if using a QListWidget to display samples)
        self.update_sample_list(data.get("samples", []))
        
        # Update the Pattern List (if using a QListWidget to display patterns)
        self.update_pattern_list(data.get("patterns", []))
        
        # Update the Sequencer Data
        self.update_sequencer(data.get("patterns", []))  # Assuming patterns are part of sequencer
        
        print("Project data populated in the UI")

    def update_sample_list(self, samples):
        """Update the UI with the loaded sample list."""
        # Assuming you have a QListWidget or a similar widget to display samples
        self.sampler_tab.sample_list.clear()  # Clear previous list
        for sample in samples:
            self.sampler_tab.sample_list.addItem(sample['name'])  # Assuming sample has a 'name'
            self.composer_tab.compose_sample_list.addItem(sample['name'])  # Assuming sample has a 'name'
            

    def update_pattern_list(self, patterns):
        """Update the pattern list in the UI."""
    
        # Clear previous list by removing widgets from the layout
        for i in reversed(range(self.sequencer_tab.pattern_layout.count())):
            widget = self.sequencer_tab.pattern_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Add new pattern buttons
        for pattern in patterns:
            # Assuming 'name' is a key in the pattern dictionary
            pattern_name = pattern.get("name", "Unnamed Pattern")  # Default value if no "name" key
            pattern_button = QPushButton(pattern_name)
            self.sequencer_tab.pattern_layout.addWidget(pattern_button)



    def update_sequencer(self, patterns):
        """Update the sequencer with the loaded patterns."""
        # Assuming you have a method in the sequencer tab to add patterns to the sequencer
        self.update_pattern_list(patterns)  # Implement this method in SequencerTab


