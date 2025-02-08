import os
import json
import shutil
from tkinter import messagebox

class ProjectManager:
    def __init__(self, ui):
        self.ui = ui  # Reference to your GUI instance
        self.project_data = {}  # Holds the project metadata
        self.project_directory = None  # Path to the project directory
        self.project_files = {
            "samples": [],
            "patterns": [],
            "wavs": [],
            "project_file": None
        }

    def load_project(self, project_path):
        """Load project data from the specified directory"""
        if not os.path.exists(project_path):
            messagebox.showerror("Error", "Project directory not found.")
            return
        
        self.project_directory = project_path
        self.project_files = {
            "samples": [],
            "patterns": [],
            "wavs": [],
            "project_file": None
        }

        # Gather and sort the project files
        self.gather_project_files()

        # Load project metadata
        project_file_path = os.path.join(self.project_directory, "project.json")
        if os.path.exists(project_file_path):
            with open(project_file_path, 'r') as project_file:
                self.project_data = json.load(project_file)
        
        # Update the UI with the loaded data
        self.update_ui_from_project()

    def save_project(self):
        """Save the project data and files to the specified directory"""
        if not self.project_directory:
            messagebox.showerror("Error", "No project directory loaded.")
            return
        
        # Save project metadata
        project_file_path = os.path.join(self.project_directory, "project.json")
        with open(project_file_path, 'w') as project_file:
            json.dump(self.project_data, project_file, indent=4)
        
        # Update the UI with the saved data
        self.update_ui_from_project()

        messagebox.showinfo("Project Saved", "Project has been saved successfully.")

    def gather_project_files(self):
        """Gather and sort all the necessary project files (.wav, .sample, .pattern, .project)"""
        if not self.project_directory:
            return

        for root, dirs, files in os.walk(self.project_directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.wav'):
                    self.project_files["wavs"].append(file_path)
                elif file.endswith('.sample'):
                    self.project_files["samples"].append(file_path)
                elif file.endswith('.pattern'):
                    self.project_files["patterns"].append(file_path)
                elif file.endswith('.project'):
                    self.project_files["project_file"] = file_path
        
        # Sort files (optional)
        self.project_files["samples"].sort()
        self.project_files["patterns"].sort()
        self.project_files["wavs"].sort()

    def update_ui_from_project(self):
        """Update the GUI with the loaded project data"""
        # Update sample list in the UI
        self.ui.update_sample_list(self.project_files["samples"])
        
        # Update pattern list in the UI
        self.ui.update_pattern_list(self.project_files["patterns"])
        
        # Update wav files in the UI
        self.ui.update_wav_list(self.project_files["wavs"])

        # Update project name in the UI (if needed)
        project_name = self.project_data.get("name", "Untitled")
        self.ui.update_project_name(project_name)

    def create_new_project(self, project_path, project_name="Untitled"):
        """Create a new project from scratch"""
        self.project_directory = project_path
        self.project_data = {
            "name": project_name,
            "samples": [],
            "patterns": [],
            "wavs": []
        }

        # Create the project directory structure if it doesn't exist
        if not os.path.exists(self.project_directory):
            os.makedirs(self.project_directory)
            os.makedirs(os.path.join(self.project_directory, "samples"))
            os.makedirs(os.path.join(self.project_directory, "patterns"))
            os.makedirs(os.path.join(self.project_directory, "wavs"))

        # Save initial project data
        self.save_project()

    def add_sample(self, sample_data):
        """Add a new sample to the project"""
        sample_name = sample_data.get('name', 'Unnamed Sample')
        sample_path = os.path.join(self.project_directory, "samples", f"{sample_name}.sample")
        with open(sample_path, 'w') as sample_file:
            json.dump(sample_data, sample_file, indent=4)
        
        self.project_files["samples"].append(sample_path)
        self.project_data["samples"].append(sample_data)
        self.save_project()

    def add_pattern(self, pattern_data):
        """Add a new pattern to the project"""
        pattern_name = pattern_data.get('name', 'Unnamed Pattern')
        pattern_path = os.path.join(self.project_directory, "patterns", f"{pattern_name}.pattern")
        with open(pattern_path, 'w') as pattern_file:
            json.dump(pattern_data, pattern_file, indent=4)
        
        self.project_files["patterns"].append(pattern_path)
        self.project_data["patterns"].append(pattern_data)
        self.save_project()
