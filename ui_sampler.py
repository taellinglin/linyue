import pygame
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QSlider, QListWidget, QGraphicsView, QGraphicsScene, QSizePolicy, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QColor
from pydub import AudioSegment
import os
import numpy as np
import io
import json
import tempfile
import shutil

class SamplerTab(QWidget):
    def __init__(self, parent_node):
        super().__init__()

        self.project_name = parent_node.project_data.get("name")
        self.samples = parent_node.samples
        self.current_sample = None

        # Initialize pygame mixer
        pygame.mixer.init()

        # Load the project JSON
        self.project_data = parent_node.project_data
        

        # === Main Layout: Sidebar + Sample Display ===
        main_layout = QHBoxLayout()

        # === LEFT PANEL: SAMPLE SELECTOR ===
        self.left_panel = QWidget()
        self.left_panel_layout = QVBoxLayout()
        # New "Add Sample" Button
        self.add_button = QPushButton("Add Sample")
        self.add_button.clicked.connect(self.add_sample)
        

        self.sample_list = QListWidget()
        self.sample_list.itemClicked.connect(self.select_sample)
        self.load_samples(True)
        self.left_panel_layout.addWidget(self.add_button)
        self.left_panel_layout.addWidget(self.sample_list)
        self.left_panel.setLayout(self.left_panel_layout)
        main_layout.addWidget(self.left_panel, 2)

        # === RIGHT PANEL: SAMPLE CONTROLS ===
        self.right_panel = QVBoxLayout()
        self.waveform_label = QLabel("[Waveform Display]")

        # Create a fixed size for the waveform display panel
        self.waveform_view = QGraphicsView()
        self.waveform_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Stretch the view horizontally
        self.waveform_view.setFixedHeight(200)  # Double the height of the panel
        self.scene = QGraphicsScene()
        self.waveform_view.setScene(self.scene)

        self.play_button = QPushButton("Play")
        self.stop_button = QPushButton("Stop")
        self.microtuning_slider = QSlider(Qt.Horizontal)
        
        # Microtuning: -50 to +50 cents (100 cents per semitone)
        self.microtuning_slider.setMinimum(-50)
        self.microtuning_slider.setMaximum(50)
        self.microtuning_slider.setValue(0)  # Default to no microtuning adjustment

        self.root_note_dropdown = QComboBox()
        self.root_note_dropdown.addItems([
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
        ])
        self.root_note_dropdown.currentIndexChanged.connect(self.adjust_pitch)

        self.play_button.clicked.connect(self.play_sample)
        self.stop_button.clicked.connect(self.stop_sample)

        self.right_panel.addWidget(self.waveform_view)
        self.right_panel.addWidget(self.play_button)
        self.right_panel.addWidget(self.stop_button)
        self.right_panel.addWidget(QLabel("Root Note"))
        self.right_panel.addWidget(self.root_note_dropdown)
        self.right_panel.addWidget(QLabel("Microtuning"))
        self.right_panel.addWidget(self.microtuning_slider)

        main_layout.addLayout(self.right_panel, 8)
        self.setLayout(main_layout)

        self.playing = False
        self.start_time = 0
        self.playback_position = 0  # In seconds

        # Connect slider to change playback speed
        self.microtuning_slider.valueChanged.connect(self.adjust_pitch)
    def get_project_name_from_file(self):
        """Retrieves the project name by finding the first valid .project file in ./projects."""
        projects_dir = "projects"

        if not os.path.exists(projects_dir):
            os.makedirs(projects_dir, exist_ok=True)  # Ensure the projects folder exists
            return "Untitled"  # Default if no projects exist

        for folder in os.listdir(projects_dir):
            project_file = os.path.join(projects_dir, folder, f"{folder}.project")
            if os.path.exists(project_file):
                try:
                    with open(project_file, "r") as f:
                        project_data = json.load(f)
                    return project_data.get("name", folder)  # Use project name from file or folder name
                except Exception as e:
                    print(f"Error loading project data: {e}")

        return "Untitled"  # Default if no valid project is found


    def load_samples(self, force_reload=False):
        """Loads samples from the project's sample folder (only once per session)."""

        if not self.project_name:
            self.project_name = self.get_project_name_from_file()

        if not self.project_name:
            print("Error: Could not determine project name.")
            return  # Prevent incorrect folder access

        project_sample_dir = os.path.join("projects", self.project_name, "samples")
        os.makedirs(project_sample_dir, exist_ok=True)  # Ensure the directory exists

        # ✅ Avoid duplicates: Clear and reload only if necessary
        if not force_reload and getattr(self, "samples_loaded", False):
            print("Samples already loaded. Skipping duplicate load.")
            return  # Exit early to prevent reloading

        self.samples = {}  # Reset dictionary
        self.sample_list.clear()  # Reset UI sample list

        existing_files = [f for f in os.listdir(project_sample_dir) if f.endswith(".wav")]

        for filename in sorted(existing_files):
            sample_name, _ = os.path.splitext(filename)
            file_path = os.path.join(project_sample_dir, filename)

            metadata_filename = f"{sample_name}.sample"
            metadata_filepath = os.path.join(project_sample_dir, metadata_filename)

            if os.path.exists(metadata_filepath):
                try:
                    with open(metadata_filepath, "r") as f:
                        sample_metadata = json.load(f)
                except Exception as e:
                    print(f"Error reading metadata for {filename}: {e}")
                    continue
            else:
                print(f"Warning: Missing metadata for {filename}, skipping it.")
                continue

            # ✅ Store metadata and update UI
            self.samples[metadata_filename] = metadata_filepath
            self.sample_list.addItem(metadata_filename)

        # ✅ Mark samples as loaded to prevent duplicate loads
        self.samples_loaded = True
        print(f"Loaded {len(self.samples)} samples from {project_sample_dir}.")

    def add_sample(self):
        """Opens a file dialog to add a new sample and saves it to the project."""

        file_path, _ = QFileDialog.getOpenFileName(None, "Select Sample File", "", "WAV Files (*.wav)")

        if not file_path:
            return  # User canceled selection

        sample_name, _ = os.path.splitext(os.path.basename(file_path))

        project_sample_dir = os.path.join("projects", self.project_name, "samples")
        os.makedirs(project_sample_dir, exist_ok=True)

        new_file_path = os.path.join(project_sample_dir, os.path.basename(file_path))

        # ✅ Prevent duplicate additions
        if os.path.exists(new_file_path):
            print(f"Sample '{sample_name}' already exists in project. Skipping duplicate.")
            return

        shutil.copy(file_path, new_file_path)  # Copy file to project

        # Generate metadata
        audio = AudioSegment.from_wav(new_file_path)
        sample_metadata = {
            "name": sample_name,
            "filename": os.path.basename(new_file_path),
            "root_note": 60,
            "micropitch": 0,
            "length": len(audio),
            "frame_count": audio.frame_count(),
            "loop_start": 0,
            "loop_end": 0,
            "format": {
                "bit_depth": audio.sample_width * 8,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels
            },
            "wav_filename": os.path.basename(new_file_path)
        }

        metadata_filename = f"{sample_name}.sample"
        metadata_filepath = os.path.join(project_sample_dir, metadata_filename)

        with open(metadata_filepath, "w") as f:
            json.dump(sample_metadata, f, indent=4)

        # ✅ Update UI
        self.samples[metadata_filename] = metadata_filepath
        self.sample_list.addItem(metadata_filename)

        print(f"Added new sample: {sample_name}")


    def update_project_name(self, project_name):
        self.project_name = project_name



    def select_sample(self, item):
        """Select a sample from the list and display its name."""
        filename = item.text()

        if filename in self.samples:
            metadata_filepath = self.samples[filename]
            print(f"DEBUG: metadata_filepath for {filename}: {metadata_filepath} (type: {type(metadata_filepath)})")  # Debugging

            if isinstance(metadata_filepath, str):  # Check if it's a string (path to the .sample file)
                try:
                    with open(metadata_filepath, "r") as f:
                        sample_data = json.load(f)  # Read metadata from the .sample file
                    print(f"DEBUG: sample_data loaded: {sample_data} (type: {type(sample_data)})")
                except Exception as e:
                    print(f"Error loading metadata from {metadata_filepath}: {e}")
                    return
            else:
                print(f"Error: metadata filepath should be a string, but got {type(metadata_filepath)}")
                return

            wav_file_path = self.get_wav_from_sample(sample_data)  # Extract .wav path

            if wav_file_path and os.path.exists(wav_file_path):
                self.current_sample = wav_file_path
                self.waveform_label.setText(f"Loaded: {filename}")
                self.draw_waveform(self.current_sample)
            else:
                print(f"Error: WAV file not found at {wav_file_path}")
        else:
            print(f"Error: Sample {filename} not found in self.samples")



    def get_wav_from_sample(self, sample_data):
        """Ensure the sample path is absolute."""
        wav_path = sample_data.get("wav_filename")
        if wav_path:
            print(self.project_name)
            # Construct the absolute path by including the project directory
            self.update_project_name(self.project_name)
        
            project_sample_dir = os.path.join("projects", self.project_name, "samples")
            absolute_wav_path = os.path.join(project_sample_dir, wav_path.lstrip('./'))
            return os.path.abspath(absolute_wav_path)
        return None

    def load_project_data(self):
        """Loads project-related data from the correct path."""
        project_file = os.path.join("projects", self.project_name, f"{self.project_name}.project")

        if not os.path.exists(project_file):
            print(f"Project file not found: {project_file}")
            return {}  # Return empty data if the file doesn't exist

        try:
            with open(project_file, "r", encoding="utf-8") as f:
                return json.load(f)  # Load project data
        except json.JSONDecodeError:
            print(f"Error: Failed to parse JSON in {project_file}")
            return {}  # Return empty dict if JSON is corrupted
        except Exception as e:
            print(f"Error loading project data: {e}")
            return {}  # Handle unexpected errors

    def save_project_data(self):
        """Saves project-related data and sample files to the correct path."""
        project_folder = os.path.join("projects", self.project_name)
        samples_folder = os.path.join(project_folder, "samples")
        project_file = os.path.join(project_folder, f"{self.project_name}.project")

        # Ensure necessary directories exist
        os.makedirs(samples_folder, exist_ok=True)

        # Save project metadata
        try:
            with open(project_file, "w", encoding="utf-8") as f:
                json.dump(self.project_data, f, indent=4)  # Save data with pretty formatting
            print(f"Project saved: {project_file}")
        except Exception as e:
            print(f"Error saving project data: {e}")

        # Save sample files
        for sample_name, sample_path in self.samples.items():
            if os.path.exists(sample_path):  # Ensure sample exists
                ext = os.path.splitext(sample_path)[1]  # Get file extension
                if ext in [".wav", ".sample"]:  # Only save valid file types
                    dest_path = os.path.join(samples_folder, f"{sample_name}{ext}")
                    try:
                        shutil.copy(sample_path, dest_path)  # Copy file to project
                        print(f"Saved sample: {dest_path}")
                    except Exception as e:
                        print(f"Error saving sample '{sample_name}': {e}")
            else:
                print(f"Warning: Sample file '{sample_path}' not found, skipping.")
    def draw_waveform(self, sample):
        """Draw the waveform of the selected sample."""
        # Prepare the waveform data
        audio = AudioSegment.from_wav(sample)
        sample_data = np.array(audio.get_array_of_samples())
        width = self.waveform_view.width()
        height = self.waveform_view.height()

        # Normalize the sample data
        max_amplitude = np.max(np.abs(sample_data))
        waveform = (sample_data / max_amplitude) * (height / 2) + (height / 2)

        # Downsampling: Only plot every Nth sample to speed up rendering
        downsample_factor = 10  # Adjust this factor for desired rendering speed
        downsampled_waveform = waveform[::downsample_factor]
        
        # Create a simple waveform view using horizontal lines
        self.scene.clear()  # Clear previous waveform
        pen = QPen(QColor(255, 0, 0))  # Red color for waveform

        # Disable scrollbars in QGraphicsView
        self.waveform_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.waveform_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Draw the waveform as simple horizontal lines
        step = 1
        for i in range(0, len(downsampled_waveform) - step):
            x1 = (i) * (width / len(downsampled_waveform))
            y1 = height - downsampled_waveform[i]
            x2 = (i + step) * (width / len(downsampled_waveform))
            y2 = height - downsampled_waveform[i + step]
            self.scene.addLine(x1, y1, x2, y2, pen)

    def adjust_pitch(self):
        """Adjust pitch based on the root note and microtuning slider."""
        if self.current_sample:
            root_note = self.root_note_dropdown.currentText()
            microtuning = self.microtuning_slider.value()

            # Calculate the frequency of the root note
            note_freq = self.get_note_frequency(root_note)

            # Apply microtuning in cents (100 cents = 1 semitone)
            tuned_freq = note_freq * (2 ** (microtuning / 1200))

            # Resample the audio with the new frequency (pitch adjustment)
            resample_factor = tuned_freq / 440.0  # Reference A4 = 440 Hz
            self.resampled_audio = self.resample_audio(self.current_sample, resample_factor)

            # Update playback
            if self.playing:
                pygame.mixer.music.stop()  # Stop current playback
                pygame.mixer.music.load(self.resampled_audio)  # Load the newly resampled audio
                pygame.mixer.music.play(start=self.playback_position)  # Start playback from the current position
                self.playing = True  # Set the playing state

    def get_note_frequency(self, note):
        """Return the frequency of a given note."""
        # A4 = 440 Hz, calculate the frequency for each note
        note_freqs = {
            "C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13,
            "E": 329.63, "F": 349.23, "F#": 369.99, "G": 392.00,
            "G#": 415.30, "A": 440.00, "A#": 466.16, "B": 493.88
        }
        return note_freqs.get(note, 440.00)  # Default to A4 if note not found

    def resample_audio(self, sample, resample_factor):
        """Resample the audio at the given factor."""
        audio = AudioSegment.from_wav(sample)

        # Calculate the new frame rate
        new_frame_rate = int(audio.frame_rate * resample_factor)

        # Ensure the frame rate is within a reasonable range to avoid invalid values
        # For example, you can set a minimum frame rate of 1000 Hz and a maximum of 96000 Hz
        min_frame_rate = 1000  # Lower bound of frame rate
        max_frame_rate = 96000  # Upper bound of frame rate
        new_frame_rate = max(min_frame_rate, min(max_frame_rate, new_frame_rate))

        # Adjust the playback rate (tempo) by resampling
        resampled_audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": new_frame_rate
        })

        # Use BytesIO to store the resampled audio in memory
        audio_buffer = io.BytesIO()
        resampled_audio.export(audio_buffer, format="wav")
        audio_buffer.seek(0)  # Rewind to the beginning of the buffer

        return audio_buffer

    def play_sample(self):
        """Play the selected sample."""
        if self.current_sample:
            # Resample the audio
            resampled_audio_buffer = self.resample_audio(self.current_sample, (self.microtuning_slider.value()/24)+1)

            # Load and play the resampled sample from memory
            pygame.mixer.music.load(resampled_audio_buffer)
            pygame.mixer.music.play()  # Play sample
            self.playing = True

    def stop_sample(self):
        """Stop the playback."""
        pygame.mixer.music.stop()
        self.playing = False
        self.playback_position = 0

