from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog, QHBoxLayout, QListWidget, QAbstractItemView, QListWidgetItem, QSizePolicy
from PyQt5.QtGui import QColor, QBrush, QFont, QFontDatabase
from PyQt5.QtCore import Qt, QTimer, QSize
import mido
import os
import wave
import numpy as np
from pydub import AudioSegment
import soundfile as sf
import time
import pygame
from pydub.effects import speedup
import mido
import json
import re
    # Initialize pygame mixer
pygame.mixer.init()
PATTERN_SIZE = 16  # Define how many rows per pattern

class TrackerTab(QWidget):
    def __init__(self, parent_node):
        super().__init__(parent_node)
        self.parent_node = parent_node
        self.project_name = parent_node.project_data.get("name")
        self.samples = parent_node.samples  # Store the samples passed from the parent
        self.layout = QVBoxLayout()
        self.project_path = f"./projects/{self.project_name}/"

        # 🔹 Sequencer Row (Pattern Playback Order)
        self.sequencer_layout = QHBoxLayout()

        self.btn_prev = QPushButton("<")
        self.btn_prev.clicked.connect(self.prev_pattern)

        self.btn_next = QPushButton(">")
        self.btn_next.clicked.connect(self.next_pattern)

        self.sequencer_list = QListWidget()
        self.sequencer_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.sequencer_list.setDragDropMode(QAbstractItemView.InternalMove)  # Allow reordering
        self.sequencer_list.setFlow(QListWidget.LeftToRight)  # Make it horizontal
        self.sequencer_list.setWrapping(False)  # Prevent it from wrapping into multiple rows
        self.sequencer_list.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)  # Smooth scrolling
        self.sequencer_list.setFixedHeight(60)  # Adjust height
        self.sequencer_list.setFixedWidth(500)  # Adjust width
        self.sequencer_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Allow width expansion
        self.sequencer_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide vertical scrollbar

        # Populate sequencer with default pattern order
        for i in range(8):  # Default 8 patterns
            item = QListWidgetItem(f"{i:02}")
            item.setTextAlignment(Qt.AlignCenter)
            item.setSizeHint(QSize(50, 50))  # Square-sized items
            self.sequencer_list.addItem(item)

        # Connect the item click signal
        self.sequencer_list.itemClicked.connect(self.load_selected_pattern)

        # Add elements to sequencer row
        self.sequencer_layout.addWidget(QLabel("Seq:"))
        self.sequencer_layout.addWidget(self.btn_prev)
        self.sequencer_layout.addWidget(self.sequencer_list)
        self.sequencer_layout.addWidget(self.btn_next)

        self.layout.addLayout(self.sequencer_layout)


        # 🔹 Tracker Table (16 Channels)
        self.num_channels = 16
        self.create_table()

        # 🔹 Playback Controls
        self.play_button = QPushButton("Play")
        self.stop_button = QPushButton("Stop")
        self.import_midi_button = QPushButton("Import MIDI")

        self.play_button.clicked.connect(self.start_playback)
        self.stop_button.clicked.connect(self.stop_playback)
        self.import_midi_button.clicked.connect(self.import_midi)

        self.layout.addWidget(self.play_button)
        self.layout.addWidget(self.stop_button)
        self.layout.addWidget(self.import_midi_button)

        # 🔹 Vertical Playhead
        self.playhead_position = 0
        self.playhead_timer = QTimer()
        self.playhead_timer.timeout.connect(self.move_playhead)

        self.setLayout(self.layout)

        self.sequencer_playhead = 0  # Track current pattern in sequence

    def load_selected_pattern(self, item=None):
        """Loads the pattern selected in the sequencer."""
        if item is None:  # In case item is passed (like through itemClicked signal)
            item = self.sequencer_list.currentItem()

        # Get the index of the clicked item
        pattern_index = self.sequencer_list.row(item)
        
        self.sequencer_playhead = pattern_index
        project_path = f"./projects/{self.project_name}/patterns"
        self.load_pattern(pattern_index, project_path)

    def load_pattern(self, pattern_index, project_path):
        """Loads pattern data from a file based on the pattern_index"""
        # Load the pattern data from the file (e.g., parse the pattern file)
        pattern_file_path = f"{project_path}/pattern_{pattern_index:02d}.pattern"
        pattern_data = self.parse_pattern_file(pattern_file_path)
        return pattern_data

    def parse_pattern_file(self, file_path):
        """Parse the pattern file into a dictionary of pattern data"""
        # Open the file and read its contents
        try:
            with open(file_path, 'r') as file:
                pattern_data = json.load(file)
            
            # Return the parsed JSON data (which will be in the form of a dictionary)
            return pattern_data
        
        except FileNotFoundError:
            print(f"Error: The file at {file_path} was not found.")
            return {}  # Return an empty dictionary if the file is not found
        
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from the file at {file_path}.")
            return {}  # Return an empty dictionary if there's an error decoding the JSON



    def add_note_to_table(self, row, note, velocity):
        """Add a single note to the table at the specified row."""
        try:
            # Ensure row and note are integers
            row = int(row)
            note = int(note)  # Ensure the note is an integer
        except ValueError as e:
            print(f"Invalid value for row or note: {e}")
            return

        # Insert the note at the appropriate column in the row
        self.table.setItem(row, note, QTableWidgetItem(str(velocity)))  # Update with velocity




        
    def prev_pattern(self):
        """Move sequencer playhead left"""
        if self.sequencer_playhead > 0:
            self.sequencer_playhead -= 1
            self.update_sequencer_playback()

    def next_pattern(self):
        """Move sequencer playhead right"""
        if self.sequencer_playhead < self.sequencer_list.count() - 1:
            self.sequencer_playhead += 1
            self.update_sequencer_playback()

    
    def update_sequencer_playback(self):
        """Loads and plays the pattern at the current sequencer playhead position"""
        project_path = f"./projects/{self.project_name}/patterns"
        pattern_item = self.sequencer_list.item(self.sequencer_playhead)
        pattern_index = int(pattern_item.text())
        
        # Load the pattern data
        pattern_data = self.load_pattern(pattern_index, project_path)
        
        # Assuming `self.sequencer_table` is the table widget holding the sequencer
        self.update_sequencer_with_pattern(pattern_data)

    def update_sequencer_with_pattern(self, pattern):
        """Updates the sequencer with the given pattern."""
        for row, notes in pattern.items():
            for note_data in notes:
                note_name, instrument_id, velocity = note_data  # Unpack correctly

                # ✅ Ensure instrument_id is within valid range
                if instrument_id < 1 or instrument_id > len(self.samples):
                    print(f"Warning: Instrument {instrument_id} not found. Skipping note {note_name}.")
                    continue  # Skip this note to prevent crashes

                print(f"Playing {note_name} with instrument {instrument_id} and velocity {velocity}")

                # ✅ Adjust for 0-based index safely
                sample = self.samples[instrument_id - 1]  
                self.play_sample(note_name, velocity, sample)




    def advance_sequencer(self):
        """Advances the sequencer when a pattern ends"""
        if self.sequencer_playhead < self.sequencer_list.count() - 1:
            self.sequencer_playhead += 1
        else:
            self.sequencer_playhead = 0  # Loop back to first pattern
        
        self.update_sequencer_playback()


    def create_table(self):
        """Creates the tracker table dynamically based on the number of channels."""
        self.table = QTableWidget(64, self.num_channels + 1)  # 64 rows, 1 row label + channels
        self.table.setHorizontalHeaderLabels(["Row"] + [f"Ch {i+1}" for i in range(self.num_channels)])
        self.table.setStyleSheet("background-color: black; color: white; font-family: Daemon_Full_Working_Regular;")
        
        font_id = QFontDatabase.addApplicationFont("font/daemon.otf")
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]  # Get the font name
            font = QFont(font_family, 8)
        else:
            print("Failed to load font.")
            font = QFont("Arial", 8)  # Fallback font
                
        for i in range(64):
            item = QTableWidgetItem(f"{i:02X}")
            item.setForeground(QBrush(QColor("white")))
            item.setFont(font)
            self.table.setItem(i, 0, item)
            for j in range(1, self.num_channels + 1):
                note = QTableWidgetItem("--- -- ---")
                note.setForeground(QBrush(QColor("white")))
                note.setFont(font)
                self.table.setItem(i, j, note)
        
        self.layout.addWidget(self.table)
        
    def change_pattern(self, index):
        print(f"Switched to Pattern {index+1}")
        
    def start_playback(self):
        self.playhead_position = 0
        self.playhead_timer.start(200)
        
    def stop_playback(self):
        self.playhead_timer.stop()
        
    def move_playhead(self):
        if self.playhead_position < 64:
            self.table.selectRow(self.playhead_position)
            self.play_sample_for_row(self.playhead_position)  # Play the sample for the current row
            self.playhead_position += 1
        else:
            self.stop_playback()
        
    def get_project_name_from_file(self):
        # Assuming the function is supposed to load the project name from a file
        print("Attempting to get project name from file...")
        # Add your actual file loading logic here
        try:
            # Example of reading a file (replace with your actual logic)
            with open('path/to/project/file', 'r') as file:
                project_name = file.readline().strip()
                print(f"Found project name in file: {project_name}")
                return project_name
        except FileNotFoundError:
            print("Error: Project file not found.")
            return None


    

    def import_midi(self, midi_file):
        """Loads a MIDI file and processes it for the sequencer."""
        project_name = self.project_name or self.get_project_name_from_file()

        print(f"Project name from self.project_name: {self.project_name}")
        print(f"Project name from self.get_project_name_from_file(): {self.get_project_name_from_file()}")
        print(f"Final project_name: {project_name}")

        if not project_name:
            print("Error: No project loaded.")
            return

        self.parent_node.sampler_tab.load_samples(force_reload=True)  # Call from sampler module

        try:
            from mido import MidiFile
            midi = MidiFile(midi_file)

            print(f"Loaded MIDI file: {midi_file}")
            self.process_midi(midi, project_name)

        except Exception as e:
            print(f"Error importing MIDI: {e}")







    def midi_to_tracker_note(self, midi_note):
        """Converts MIDI note number to tracker note format (e.g., 'C-4')."""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1  # Calculate octave (e.g., MIDI note 60 is C4, which is octave 4)
        note_name = note_names[midi_note % 12]  # Get note name (C, D, etc.)
        return f"{note_name}-{octave}"

    # Helper function to clamp MIDI velocity to tracker format (00-99)
    def clamp_velocity(self, velocity):
        """Clamps MIDI velocity (0-127) to tracker velocity (00-99)."""
        return max(0, min(99, velocity))

    # Main MIDI processing function
    # Main MIDI processing function
    def process_midi(self, midi, project_name):
        """Splits MIDI into patterns and saves them in ./projects/{project_name}/patterns."""
        print("Processing MIDI file...")

        max_channels = 1
        row_data = {}
        ticks_per_row = midi.ticks_per_beat // 4
        time_counter = 0

        # Convert MIDI to row-based format
        for track in midi.tracks:
            track_time = 0
            for msg in track:
                track_time += msg.time
                row = track_time // ticks_per_row  # Convert ticks to row

                if msg.type == 'note_on' and msg.velocity > 0:
                    # Convert MIDI note to tracker format (note name)
                    note_name = self.midi_to_tracker_note(msg.note)
                    # Clamp velocity to the range 00-99
                    velocity = self.clamp_velocity(msg.velocity)
                    # Convert MIDI channel to instrument ID
                    instrument_id = msg.channel + 1  # Simple conversion (0 -> instrument 1, 1 -> instrument 2, etc.)
                    # Store as a tuple (note, instrument, velocity)
                    note_tuple = (note_name, instrument_id, velocity)

                    if row not in row_data:
                        row_data[row] = []
                    row_data[row].append(note_tuple)

                    # If multiple notes exist on the same row, increase channels
                    max_channels = max(max_channels, len(row_data[row]))

        # Split rows into patterns
        patterns = {}
        for row, notes in row_data.items():
            pattern_index = row // PATTERN_SIZE
            pattern_row = row % PATTERN_SIZE

            if pattern_index not in patterns:
                patterns[pattern_index] = {}

            patterns[pattern_index][pattern_row] = notes

        # Ensure the project folder exists
        project_path = f"./projects/{project_name}/patterns"
        os.makedirs(project_path, exist_ok=True)

        # Save patterns as .pattern files (basically JSON)
        for pattern_index, pattern_data in patterns.items():
            pattern_file = os.path.join(project_path, f"pattern_{pattern_index:02}.pattern")
            with open(pattern_file, "w") as f:
                json.dump(pattern_data, f, indent=4)

        print(f"Saved {len(patterns)} patterns to {project_path}")

        # Update the UI to reflect pattern-based sequencing
        self.num_channels = max_channels
        self.load_pattern(0, project_path)  # Load the first pattern automatically

        # Call update_sequencer_with_pattern directly
        self.update_sequencer_with_pattern(patterns[0])  # Update the sequencer with the first pattern



    def update_sequencer_with_pattern(self, pattern):
        """Updates the sequencer with the given pattern."""
        for row, notes in pattern.items():
            for note_data in notes:
                note_name, instrument_id, velocity = note_data  # Unpack correctly

                # Now, use note_name, instrument_id, velocity
                print(f"Playing {note_name} with instrument {instrument_id} and velocity {velocity}")
                
                # Call the function to play the note (adjust to fit your logic)
                self.play_sample(note_name, velocity, self.samples[instrument_id - 1])  # Adjust for 0-based indexing





    def refresh_sequencer_and_editor(self, project_path):
        """Refresh the sequencer and editor after processing MIDI."""
        self.sequencer_list.clear()  # Clear the existing sequencer list

        # Iterate through files in the project patterns directory
        for file in os.listdir(project_path):
            # Check if the file matches the expected pattern filename format (with .pattern extension)
            match = re.match(r'pattern_(\d+)\.pattern', file)  # Match the .pattern extension
            if match:
                pattern_index = int(match.group(1))  # Extract pattern index from the filename
                item = QListWidgetItem(f"Pattern {pattern_index:02}")
                self.sequencer_list.addItem(item)
            else:
                print(f"Skipping non-pattern file: {file}")  # Optionally log skipped files

        # Refresh the pattern editor with the first pattern
        self.load_pattern(0, project_path)  # Load the first pattern by default









    def play_sample_for_row(self, row):
        """Plays the sample corresponding to the MIDI notes in the current row."""
        for col in range(1, self.num_channels + 1):
            item = self.table.item(row, col)
            if item and item.text() != "--- -- ---":
                note_info = item.text().split()
                if len(note_info) >= 2:  # Expecting note and velocity
                    note_name = note_info[0]
                    velocity = int(note_info[1], 16) / 99.0  # Convert from 0-99 scale to 0.0-1.0

                    print(f"Attempting to play {note_name} with velocity {velocity}")

                    # Search for the sample matching the note_name
                    sample = None
                    for sample_obj in self.samples:
                        if sample_obj.name == note_name:  # Assuming each sample has a 'name' attribute
                            sample = sample_obj
                            break

                    if not sample:
                        print("Loading default sample...")
                        sample = self.load_default_sample()

                    if sample:
                        # Get the frequency for the note
                        note_frequency = self.note_to_frequency(note_name)  # Convert note name to frequency
                        sample_frequency = 440  # Default to A4 frequency (440 Hz) for unmodified samples
                        
                        # Calculate the pitch ratio
                        pitch_ratio = note_frequency / sample_frequency
                        
                        # Adjust the sample to match the pitch without altering frame rate
                        adjusted_sample = self.resample_to_pitch(sample, pitch_ratio)
                        
                        # Play the adjusted sample once
                        self.play_sample(note_name, velocity, adjusted_sample)

    def resample_to_pitch(self, sample, pitch_ratio):
        """Resample the sample to the desired pitch without altering the frame rate."""
        # Resample the AudioSegment based on the pitch ratio
        new_sample = sample._spawn(sample.raw_data)
        
        # Use the pydub method for resampling: change the frame rate to match the pitch
        new_frame_rate = int(sample.frame_rate * pitch_ratio)
        resampled_sample = new_sample.set_frame_rate(new_frame_rate)
        
        return resampled_sample

    def play_sample(self, note_name, velocity, sample):
        """Plays the sample for the given note with velocity adjustment and pitch correction."""
        print(f"Playing sample for {note_name} with velocity {velocity}")

        # Convert AudioSegment to raw data
        raw_data = sample.raw_data
        sample_rate = sample.frame_rate

        # Create a pygame Sound object from the raw data
        pygame_sample = pygame.mixer.Sound(buffer=raw_data)

        # Set the volume based on velocity (0-99 scale converted to 0.0-1.0)
        pygame_sample.set_volume(velocity)

        # Play the sample once
        pygame_sample.play()

    def load_default_sample(self):
        """Loads the default sample."""
        if os.path.exists("./default.wav"):
            print("Loading default sample...")
            return AudioSegment.from_wav("./default.wav")
        else:
            print("Default sample not found.")
            return None

    def note_to_frequency(self, note_name):
        """Converts note name (e.g., 'C-4', 'D-4') to frequency in Hz."""
        note_frequencies = {
            "C-0": 16.35, "C#0": 17.32, "D-0": 18.35, "D#0": 19.45, "E-0": 20.60, "F-0": 21.83, "F#0": 23.12, "G-0": 24.50, "G#0": 25.96, "A-0": 27.50, "A#0": 29.14, "B-0": 30.87,
            "C-1": 32.70, "C#1": 34.65, "D-1": 36.71, "D#1": 38.89, "E-1": 41.20, "F-1": 43.65, "F#1": 46.25, "G-1": 49.00, "G#1": 51.91, "A-1": 55.00, "A#1": 58.27, "B-1": 61.74,
            "C-2": 65.41, "C#2": 69.30, "D-2": 73.42, "D#2": 77.78, "E-2": 82.41, "F-2": 87.31, "F#2": 92.50, "G-2": 98.00, "G#2": 103.83, "A-2": 110.00, "A#2": 116.54, "B-2": 123.47,
            "C-3": 130.81, "C#3": 138.59, "D-3": 146.83, "D#3": 155.56, "E-3": 164.81, "F-3": 174.61, "F#3": 185.00, "G-3": 196.00, "G#3": 207.65, "A-3": 220.00, "A#3": 233.08, "B-3": 246.94,
            "C-4": 261.63, "C#4": 277.18, "D-4": 293.66, "D#4": 311.13, "E-4": 329.63, "F-4": 349.23, "F#4": 369.99, "G-4": 392.00, "G#4": 415.30, "A-4": 440.00, "A#4": 466.16, "B-4": 493.88,
            "C-5": 523.25, "C#5": 554.37, "D-5": 587.33, "D#5": 622.25, "E-5": 659.26, "F-5": 698.46, "F#5": 739.99, "G-5": 783.99, "G#5": 830.61, "A-5": 880.00, "A#5": 932.33, "B-5": 987.77,
            "C-6": 1046.50, "C#6": 1108.73, "D-6": 1174.66, "D#6": 1244.51, "E-6": 1318.51, "F-6": 1396.91, "F#6": 1479.98, "G-6": 1567.98, "G#6": 1661.22, "A-6": 1760.00, "A#6": 1864.66, "B-6": 1975.53,
            "C-7": 2093.00, "C#7": 2217.46, "D-7": 2349.32, "D#7": 2491.02, "E-7": 2637.02, "F-7": 2793.83, "F#7": 2959.96, "G-7": 3135.96, "G#7": 3322.44, "A-7": 3520.00, "A#7": 3729.31, "B-7": 3951.07,
            "C-8": 4186.01, "C#8": 4434.92, "D-8": 4698.64, "D#8": 4978.04, "E-8": 5274.04, "F-8": 5587.65, "F#8": 5919.92, "G-8": 6271.93, "G#8": 6644.88, "A-8": 7040.00, "A#8": 7458.62, "B-8": 7902.13
        }

        return note_frequencies.get(note_name, 440.00)  # Default to A4 if note not found


        
    # Helper function to convert MIDI note number to note name
    def midi_to_note_name(self, midi_note):
        # MIDI note values: C-1 to B-8 (0-127)
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1  # Octave calculation
        note = note_names[midi_note % 12]
        return f"{note}-{octave}"


    def get_pitch_ratio(self, note_name):
        """Returns the pitch ratio for a given note name, relative to a reference note."""
        # Assuming reference note is C-4 (MIDI note 60)
        midi_notes = {
            "C-4": 60, "C#4": 61, "D-4": 62, "D#4": 63, "E-4": 64, "F-4": 65, "F#4": 66,
            "G-4": 67, "G#4": 68, "A-4": 69, "A#4": 70, "B-4": 71, "C-5": 72, "C#5": 73,
            "D-5": 74, "D#5": 75, "E-5": 76, "F-5": 77, "F#5": 78, "G-5": 79, "G#5": 80,
            "A-5": 81, "A#5": 82, "B-5": 83
        }

        reference_midi = 60  # C-4
        target_midi = midi_notes.get(note_name, reference_midi)

        # Calculate the ratio for pitch adjustment
        ratio = 2 ** ((target_midi - reference_midi) / 12.0)
        return ratio

    def note_to_frequency(self, note_name):
        """Converts note name (e.g., 'C-4', 'D#3') to frequency in Hz."""
        note_frequencies = {
            "C-4": 261.63, "C#4": 277.18, "D-4": 293.66, "D#4": 311.13, "E-4": 329.63,
            "F-4": 349.23, "F#4": 369.99, "G-4": 392.00, "G#4": 415.30, "A-4": 440.00,
            "A#4": 466.16, "B-4": 493.88,
            # Add more notes as needed
            "D-3": 146.83,  # Example lower note frequency
            "F-3": 174.61,  # Example lower note frequency
            # You can add more notes to this mapping
        }
        return note_frequencies.get(note_name, 440.00)  # Default to A4 if note not found

    def stretch_sample_to_pitch(self, sample, pitch_ratio):
        """Stretches or shrinks the sample based on the pitch_ratio."""
        original_frame_rate = sample.frame_rate

        # Calculate the new frame rate based on the pitch ratio
        new_frame_rate = int(original_frame_rate * pitch_ratio)
        
        # If pitch_ratio is greater than 1, it means we need to speed up the sample, otherwise slow it down
        if pitch_ratio > 1:
            # Speed up the sample (increases pitch)
            stretched_sample = sample._spawn(sample.raw_data, overrides={'frame_rate': new_frame_rate})
        elif pitch_ratio < 1:
            # Slow down the sample (lowers pitch)
            stretched_sample = sample._spawn(sample.raw_data, overrides={'frame_rate': new_frame_rate})
        else:
            # If pitch_ratio is exactly 1, return the sample unchanged
            stretched_sample = sample

        # Reset to original frame rate for consistency
        stretched_sample = stretched_sample.set_frame_rate(original_frame_rate)
        
        return stretched_sample


    def play_sample(self, note_name, velocity, sample):
        """Plays the sample for the given note with velocity adjustment."""
        print(f"Playing sample for {note_name} with velocity {velocity}")

        # Convert AudioSegment to raw data
        raw_data = sample.raw_data
        sample_rate = sample.frame_rate

        # Create a pygame Sound object from the raw data
        pygame_sample = pygame.mixer.Sound(buffer=raw_data)

        # Set the volume based on velocity (0-127 scale)
        pygame_sample.set_volume(velocity / 127.0)

        # Play the sample
        pygame_sample.play()

    def load_default_sample(self):
        """Loads the default sample."""
        if os.path.exists("./default.wav"):
            print("Loading default sample...")
            return AudioSegment.from_wav("./default.wav")
        else:
            print("Default sample not found.")
            return None

    def midi_note_to_name(self, note_number):
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (note_number // 12) - 1
        note = note_names[note_number % 12]
        return f"{note}-{octave}"  # Example: C-4, A#-3, G-5
