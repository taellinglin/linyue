from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter, QFileDialog, QListWidget, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QComboBox
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QWheelEvent, QFont
import numpy as np
import pypianoroll
import os
import shutil
class PianoRollWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.piano_keys = PianoKeysWidget(self)
        self.piano_roll = PianoRollGrid(self)
        layout.addWidget(self.piano_keys)
        layout.addWidget(self.piano_roll)
        self.setLayout(layout)


class PianoRollGrid(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.init_grid()

    def init_grid(self):
        num_keys = 88  # Number of piano keys
        key_height = 20
        time_length = 1000  # Arbitrary length for the time axis
        for i in range(num_keys):
            y = i * key_height
            rect = QRectF(0, y, time_length, key_height)
            grid_item = QGraphicsRectItem(rect)
            grid_item.setPen(QPen(Qt.lightGray))
            self.scene.addItem(grid_item)

    def wheelEvent(self, event):
        zoom_factor = 1.25
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1 / zoom_factor, 1 / zoom_factor)
        else:
            super().wheelEvent(event)
            
class PianoKeysWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.white_keys = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        self.black_keys = ['C#', 'D#', 'F#', 'G#', 'A#']
        self.key_height = 20  # Height of each key

    def paintEvent(self, event):
        painter = QPainter(self)
        self.draw_keys(painter)

    def draw_keys(self, painter):
        num_octaves = 7  # Number of octaves to display
        start_note = 21  # Starting MIDI note number (A0)
        white_key_width = self.width()
        black_key_width = white_key_width * 0.6
        black_key_height = self.key_height * 0.6

        for octave in range(num_octaves):
            for i, key in enumerate(self.white_keys):
                note_index = octave * 12 + i
                y = note_index * self.key_height
                rect = QRectF(0, y, white_key_width, self.key_height)
                painter.setBrush(Qt.white)
                painter.drawRect(rect)
                painter.setPen(Qt.black)
                painter.drawRect(rect)  # Draw border

                # Draw black keys
                if key in ['C', 'D', 'F', 'G', 'A']:
                    black_key_y = y + self.key_height - black_key_height / 2
                    black_rect = QRectF(white_key_width - black_key_width, black_key_y, black_key_width, black_key_height)
                    painter.setBrush(Qt.black)
                    painter.drawRect(black_rect)

import numpy as np
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QBrush, QPen, QWheelEvent, QPainter
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene

# Global sample array for loading patterns (this should be filled with actual MIDI patterns)
global_samples = []


# Define some constants for keyboard key colors (dark and light alternating)
KEY_COLORS = [
    QColor(255, 255, 255),  # White (for white keys)
    QColor(0, 0, 0),        # Black (for black keys)
]

# ROYGBIV colors for tracks
ROYGBIV_COLORS = [
    QColor(255, 0, 0),       # Red
    QColor(255, 165, 0),     # Orange
    QColor(255, 255, 0),     # Yellow
    QColor(0, 255, 0),       # Green
    QColor(0, 0, 255),       # Blue
    QColor(75, 0, 130),      # Indigo
    QColor(238, 130, 238)    # Violet
]

class PianoRollView(QGraphicsView):
    def __init__(self, parent=None, time_signature="4/4"):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self._pan = True
        self._panStartX = 0
        self._panStartY = 0
    
        # Initialize scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Piano roll properties
        self.time_signature = time_signature # Default time signature
        self.time_resolution = 16  # 16th notes (resolution of the grid)
        self.grid_height = 128  # Total rows for 128 possible notes (C0 to B8)
        self.note_height = 32  # Height of each note in pixels
        self.note_width = 32  # Width of each note in pixels (adjust as needed)

        self.track = pypianoroll.Track(name="Melody", program=0, is_drum=False)
        self.multi_track = pypianoroll.Multitrack(tracks=[self.track])
        if self.track.pianoroll is None or self.track.pianoroll.size == 0:
            num_time_steps = 128  # Set this to your desired number
            num_pitches = 128  # Typically 128 for MIDI notes from 0 to 127
            self.track.pianoroll = np.zeros((num_time_steps, num_pitches), dtype=np.uint8)

        self.update_grid_size()
        self.draw_piano_roll()

    def update_grid_size(self):
        """Dynamically adjust grid size based on time signature."""
        beats_per_measure = int(self.time_signature.split('/')[0])
        self.grid_width = beats_per_measure * self.time_resolution  # Number of time subdivisions in one bar

        # Apply the scene rect with clamping for panning
        self.setSceneRect(0, 0, self.grid_width * self.note_width, self.grid_height * self.note_height)

    def wheelEvent(self, event: QWheelEvent):
        zoomFactor = 1.25
        # Zoom clamping
        if event.modifiers() == Qt.ShiftModifier:
            # Horizontal Zoom
            if event.angleDelta().y() > 0:
                self.scale(zoomFactor, 1)
            else:
                self.scale(1 / zoomFactor, 1)
        else:
            # Vertical Zoom
            if event.angleDelta().y() > 0:
                self.scale(1, zoomFactor)
            else:
                self.scale(1, 1 / zoomFactor)

        # Clamp zooming limits (horizontal and vertical)
        self.setTransform(self.transform().scale(min(max(self.transform().m11(), 0.5), 2), min(max(self.transform().m22(), 0.5), 2)))

    def wheelEvent(self, event: QWheelEvent):
        """Restrict the zoom factor to a specific range to avoid excessive zooming."""
        zoom_factor = 1.1
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

        # Limit the zoom level to prevent over-zooming
        scale_x = self.transform().m11()
        scale_y = self.transform().m22()
        scale_x = min(max(scale_x, 0.5), 3)  # Adjust the scale limits
        scale_y = min(max(scale_y, 0.5), 3)
        self.setTransform(self.transform().scale(scale_x, scale_y))

    def wheelEvent(self, event: QWheelEvent):
        """Override the wheel event to clamp the zoom and pan."""
        super().wheelEvent(event)
        self.set_scene_rect_clamp()

    def set_scene_rect_clamp(self):
        """Clamp the view to avoid zooming or panning past the piano roll."""
        current_rect = self.sceneRect()

        # Clamp the horizontal scrolling, only allow scrolling to the right side
        max_scroll_x = self.grid_width * self.note_width - current_rect.width()
        min_scroll_x = 0
        current_scroll_x = self.horizontalScrollBar().value()

        # Ensure the scroll remains within bounds
        if current_scroll_x < min_scroll_x:
            self.horizontalScrollBar().setValue(min_scroll_x)
        elif current_scroll_x > max_scroll_x:
            self.horizontalScrollBar().setValue(max_scroll_x)
            
        # Optional: clamp vertical scrolling similarly if desired
        # max_scroll_y = self.grid_height * self.note_height - current_rect.height()
        # self.verticalScrollBar().setValue(min(current_scroll_y, max_scroll_y))


    def clear(self):
        """Clear the piano roll and reset the track."""
        self.track.pianoroll = np.zeros_like(self.track.pianoroll)
        self.draw_piano_roll()

    def set_time_signature(self, time_signature):
        """Update grid and note playback based on time signature."""
        self.time_signature = time_signature
        self.update_grid_size()
        self.draw_piano_roll()

    def update_grid_size(self):
        """Dynamically adjust grid size based on time signature."""
        if isinstance(self.time_signature, QComboBox):  
            time_signature_text = self.time_signature.currentText()  # Get selected time signature
        else:
            time_signature_text = self.time_signature  # If already a string, use it directly

        try:
            beats_per_measure = int(time_signature_text.split('/')[0])  # Extract beats per measure
        except (ValueError, AttributeError, IndexError):
            beats_per_measure = 4  # Default to 4/4 if parsing fails

        self.grid_width = beats_per_measure * self.time_resolution  # Total time subdivisions in one measure
        self.setSceneRect(0, 0, self.grid_width * self.note_width + 50, self.grid_height * self.note_height)  # Add space for keys
    def load_sample_files(self):
        """Scans the samples folder and updates self.samples with .sample files."""
        samples_folder = os.path.join("projects", self.project_name, "samples")

        if not os.path.exists(samples_folder):
            print(f"Samples folder not found: {samples_folder}")
            return  # Exit if folder doesn't exist

        # Find all .sample files
        sample_files = glob.glob(os.path.join(samples_folder, "*.sample"))

        for sample_path in sample_files:
            sample_name = os.path.splitext(os.path.basename(sample_path))[0]  # Extract filename without extension
            self.samples[sample_name] = sample_path  # Store in self.samples

        print(f"Loaded {len(sample_files)} sample files.")

    def load_notes(self, pianoroll):
        """Load a pianoroll matrix into the canvas."""
        self.track.pianoroll = pianoroll
        self.draw_piano_roll()

    def draw_piano_roll(self):
        """Draw the entire piano roll, including grid and notes."""
        self.scene.clear()
        self.draw_background()
        self.draw_grid()
        self.draw_notes()
        self.draw_keys()
        self.draw_timeline()

    def draw_background(self):
        """Draw the background of the piano roll."""
        self.scene.setBackgroundBrush(QColor(30, 30, 30))  # Dark background

    def draw_grid(self):
        """Draw the piano roll grid with alternating dark and light backgrounds for time signature."""
        pen = QPen(QColor(50, 50, 50), 1)

        # Draw vertical lines (time divisions)
        for i in range(self.grid_width):
            x = i * self.note_width + 50  # Offset for the key section
            if i % self.time_resolution == 0:  # Bar line
                color = QColor(40, 40, 40) if (i // self.time_resolution) % 2 == 0 else QColor(50, 50, 50)
                self.scene.addRect(QRectF(x, 0, self.note_width, self.height()), pen, QBrush(color))
            elif i % (self.time_resolution // 4) == 0:  # Beat line
                self.scene.addLine(x, 0, x, self.height(), pen)

        # Draw horizontal lines (pitch divisions) with WBWBWWBWBWB pattern and alternating keyboard keys
        for i in range(self.grid_height):
            y = i * self.note_height
            color = QColor(100, 100, 100)  # Default white for other lines
            self.scene.addLine(50, y, self.width(), y, pen)  # Start drawing after the keys

    def draw_keys(self):
        """Draw the piano keys vertically stacked on the left side."""
        white_key_height = self.grid_height * self.note_height / 128
        black_key_height = white_key_height * 0.6  # Black keys are shorter

        for i in range(128):
            y = i * white_key_height
            if i % 12 in [0, 2, 4, 5, 7, 9, 11]:  # White key positions
                self.scene.addRect(0, y, 50, white_key_height, QPen(Qt.NoPen), QBrush(QColor(255, 255, 255)))  # White key
            else:  # Black key positions
                black_y = y + white_key_height * 0.25
                self.scene.addRect(30, black_y, 20, black_key_height, QPen(Qt.NoPen), QBrush(QColor(0, 0, 0)))  # Black key

    def draw_timeline(self):
        """Draw the timeline with numbers at the top of the grid."""
        font = QFont("Daemon", 11)
        
        for i in range(0, self.grid_width, self.time_resolution):
            # Create text item and set the font
            text_item = self.scene.addText(str(i // self.time_resolution + 1), font)
            
            # Set the color separately
            text_item.setDefaultTextColor(QColor(255, 255, 255))
            
            # Position the text at the appropriate place on the timeline
            x = i * self.note_width
            text_item.setPos(x, 0)

    def draw_notes(self):
        """Draw each note as a colored block."""
        if self.track.pianoroll is None or np.count_nonzero(self.track.pianoroll) == 0:
            # If the pianoroll is empty, return early or handle accordingly
            return

        brush = QBrush(QColor(255, 0, 0))  # Red color for notes

        # Find the min and max time and pitch for proper scaling, ensuring the pianoroll is not empty
        nonzero_indices = np.where(self.track.pianoroll > 0)
        min_time = np.min(nonzero_indices[0])
        max_time = np.max(nonzero_indices[0])
        min_pitch = np.min(nonzero_indices[1])
        max_pitch = np.max(nonzero_indices[1])

        # Scale time and pitch to fit within the panel
        time_range = max_time - min_time
        pitch_range = max_pitch - min_pitch

        # Adjust time scaling (stretch the notes to fit horizontally)
        time_scaling = self.width() / time_range if time_range > 0 else 1
        pitch_scaling = self.height() / pitch_range if pitch_range > 0 else 1

        # Iterate through the pianoroll and draw notes
        for time in range(self.track.pianoroll.shape[0]):  # Iterate through time
            for pitch in range(self.track.pianoroll.shape[1]):  # Iterate through pitches
                if self.track.pianoroll[time, pitch] > 0:  # If the note is active
                    # Calculate the position and size based on scaled time and pitch
                    x = (time - min_time) * time_scaling + 50  # X position based on time scaling, offset by 50 for keys
                    y = (127 - pitch) * pitch_scaling  # Y position based on pitch scaling
                    note_width = time_scaling  # Note width is proportional to time
                    note_height = pitch_scaling  # Note height is proportional to pitch

                    # Draw the note as a rectangle
                    self.scene.addRect(QRectF(x, y, note_width, note_height), QPen(Qt.NoPen), brush)

    def wheelEvent(self, event: QWheelEvent):
        zoomFactor = 1.25
        if event.modifiers() == Qt.ShiftModifier:
            # Horizontal Zoom
            if event.angleDelta().y() > 0:
                self.scale(zoomFactor, 1)
            else:
                self.scale(1 / zoomFactor, 1)
        else:
            # Vertical Zoom
            if event.angleDelta().y() > 0:
                self.scale(1, zoomFactor)
            else:
                self.scale(1, 1 / zoomFactor)

    def update_midi_track_from_pattern(self, pattern_index):
        """Update the MIDI track based on the selected pattern from the global_samples array."""
        if pattern_index < len(global_samples):
            self.track.pianoroll = global_samples[pattern_index]
            self.draw_piano_roll()


# Example: Assume global_samples is populated with various MIDI pattern arrays
# global_samples = [np.random.randint(0, 2, (128, 128)), np.random.randint(0, 2, (128, 128))]




from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QComboBox, QSplitter, QFileDialog
from PyQt5.QtCore import Qt
import pypianoroll  # Assuming pypianoroll is used for MIDI file handling

import pygame
import glob
# Initialize pygame mixer
pygame.mixer.init()

class TimelineView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create scene and set it for the view
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.playhead = QGraphicsRectItem(0, 0, 2, 20)  # 2x20 pixel playhead
        self.playhead.setBrush(QColor(255, 0, 0))  # Red color for the playhead
        self.scene.addItem(self.playhead)

        # Create the timeline bar
        self.timeline_bar = QGraphicsRectItem(0, 0, 1000, 20)  # Example width
        self.timeline_bar.setBrush(QColor(100, 100, 100))  # Dark grey for timeline
        self.scene.addItem(self.timeline_bar)

        self.playhead_position = 0  # Track the current position

        # Set a timer to update the playhead position
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_playhead)
        self.timer.start(100)  # Update every 100ms

    def update_playhead(self):
        """Update playhead position based on current time."""
        self.playhead_position += 1  # Simulate playhead moving by 1 unit

        # Check if the playhead has reached the end of the timeline
        if self.playhead_position >= self.timeline_bar.rect().width():
            self.playhead_position = 0  # Loop back to the beginning

        # Update the playhead position
        self.playhead.setPos(self.playhead_position, 0)

    def set_playhead_position(self, position):
        """Set the playhead position manually."""
        self.playhead_position = position
        self.playhead.setPos(position, 0)


import os
import pygame
import numpy as np
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QSplitter, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from pypianoroll import read as pypianoroll_read


class ComposerTab(QWidget):
    def __init__(self, parent_node):
        super().__init__()
        self.project_name = parent_node.project_data.get("name")
        self.time_signature = parent_node.time_signature
        self.samples = parent_node.samples
        self.patterns = parent_node.patterns
        self.pianoroll = PianoRollView(self.time_signature)
        layout = QVBoxLayout()

        # Playback Controls (Play, Pause, Stop)
        playback_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.compose_sample_list = QListWidget()

        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.pause_button)
        playback_layout.addWidget(self.stop_button)
        playback_layout.addWidget(self.compose_sample_list)

        layout.addLayout(playback_layout)

        # Splitter to separate sidebar (pattern list) and piano roll
        self.splitter = QSplitter(Qt.Horizontal)

        # Sidebar - Pattern selection list (Docked to left)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()

        # Load MIDI Button at the top
        load_button = QPushButton("Load MIDI")
        sidebar_layout.addWidget(load_button)

        # Pattern List (updated dynamically after loading MIDI)
        self.pattern_list = QListWidget()
        sidebar_layout.addWidget(QLabel("Select Pattern:"))
        sidebar_layout.addWidget(self.pattern_list)

        sidebar.setLayout(sidebar_layout)

        # Add the sidebar to the splitter (will occupy 20% of the space)
        self.splitter.addWidget(sidebar)

        # Create the Timeline View for pattern representation
        self.timeline_view = TimelineView(self)
        self.splitter.addWidget(self.timeline_view)
        self.splitter.setStretchFactor(1, 1)  # Ensure the timeline stretches

        layout.addWidget(self.splitter)  # Add the splitter to the main layout

        # Set the main layout
        self.setLayout(layout)

        # Connect buttons to their respective functions
        load_button.clicked.connect(self.load_midi)
        
        # Connect the pattern list item clicked signal to update the timeline
        self.pattern_list.itemClicked.connect(self.on_pattern_selected)
        self.compose_sample_list.itemClicked.connect(self.on_item_clicked)

        # Populate sample dropdown with sample names
        self.populate_sample_dropdown(parent_node.samples)

        # Connect playback buttons to their functions
        self.play_button.clicked.connect(self.playback_start)
        self.pause_button.clicked.connect(self.playback_pause)
        self.stop_button.clicked.connect(self.playback_stop)

    def on_item_clicked(self, item):
        """Handle click on a sample item in the list."""
        print(f"Sample clicked: {item.text()}")
        sample_name = item.text()
        self.load_sample(sample_name)

    def load_sample(self, sample_name):
        """Load the sample based on the item clicked."""
        sample_path = os.path.join("projects", self.project_name, "samples", f"{sample_name}.wav")
        if os.path.exists(sample_path):
            pygame.mixer.music.load(sample_path)
            pygame.mixer.music.play()
            print(f"Playing sample: {sample_name}")
        else:
            print(f"Sample file not found: {sample_path}")

    def playback_start(self):
        """Start the playback."""
        sample_name = self.compose_sample_list.currentItem().text()  # Use text instead of currentIndex()
        sample_path = os.path.join("projects", self.project_name, "samples", f"{sample_name}.wav")

        if os.path.exists(sample_path):
            pygame.mixer.music.load(sample_path)
            pygame.mixer.music.play()
            print(f"Playing sample: {sample_name}")
        else:
            print(f"Sample file not found: {sample_path}")

    def playback_pause(self):
        """Pause the playback."""
        pygame.mixer.music.pause()

    def playback_stop(self):
        """Stop the playback."""
        pygame.mixer.music.stop()

    def populate_sample_dropdown(self, sample_names):
        """Populate the sample dropdown with sample names."""
        self.compose_sample_list.clear()  # Clear existing items
        if sample_names:
            for sample in sample_names:
                self.compose_sample_list.addItem(sample)  # Add each sample name

    def on_pattern_selected(self, item):
        """Handle selection of a track pattern from the pattern list."""
        print(f"Selected pattern: {item.text()}")

        # Update the timeline based on the selected pattern
        track_index = self.pattern_list.row(item)  # Get the index of the selected item
        self.timeline_view.set_playhead_position(0)  # Reset playhead

        # Assuming you can load the pattern and calculate the pattern length
        # Here, we'll assume it's a predefined length for simplicity
        pattern_length = 1000  # Adjust based on actual pattern length (in ms or steps)
        self.timeline_view.timeline_bar.setRect(0, 0, pattern_length, 20)

    def load_midi(self):
        """Load a MIDI file into the piano roll and populate the pattern list."""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open MIDI File", "", "MIDI Files (*.mid *.midi);;All Files (*)", options=options
        )
        if file_path:
            # Read the MIDI file into a Multitrack object
            multitrack = pypianoroll_read(file_path)
            
            if multitrack.tracks:
                # Load the notes for the first track into the piano roll
                self.pianoroll.load_notes(multitrack.tracks[0].pianoroll)
                
                # Populate pattern list based on track data or other MIDI properties
                self.pattern_list.clear()
                for idx, track in enumerate(multitrack.tracks):
                    pattern_name = f"Track {idx + 1} - {track.name if track.name else 'Unnamed'}"
                    self.pattern_list.addItem(pattern_name)

                    # Save the track pattern data to the patterns directory
                    self.save_pattern(track, idx + 1)
                
                # Store the multitrack for later use
                self.pianoroll.multi_track = multitrack
            else:
                print("No tracks found in the MIDI file.")

    def save_pattern(self, track, track_index):
        """Save a MIDI track pattern to a .pattern file in the patterns directory."""
        project_path = f"./projects/{self.project_name}/patterns"
        
        if not os.path.exists(project_path):
            os.makedirs(project_path)

        pattern_name = f"{track_index:02d}_{track.name if track.name else 'Unnamed'}"
        pattern_file_path = os.path.join(project_path, f"{pattern_name}.pattern")
        
        try:
            with open(pattern_file_path, 'wb') as f:
                np.save(f, track.pianoroll)
            print(f"Pattern saved to {pattern_file_path}")
        except Exception as e:
            print(f"Error saving pattern: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save pattern: {str(e)}")