import pygame
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton, QGroupBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPainter

class VuMeter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.level = 0  # Audio amplitude (0-1)

    def set_level(self, level):
        self.level = level
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        height = self.height()
        width = self.width()

        # Draw the Vu meter as a vertical bar
        painter.setBrush(QColor(0, 255, 0))  # Green for normal
        if self.level > 0.75:
            painter.setBrush(QColor(255, 0, 0))  # Red for high level
        elif self.level > 0.5:
            painter.setBrush(QColor(255, 255, 0))  # Yellow for medium level

        # Fill the bar based on the audio level
        painter.drawRect(0, height - int(self.level * height), width, int(self.level * height))

class MixerTab(QWidget):
    def __init__(self, parent_node):
        super().__init__(parent_node)
        self.layout = QVBoxLayout()

        # Master Channel
        self.master_channel = self.create_channel("Master Channel")
        self.layout.addWidget(self.master_channel)

        # Example of adding more channels
        self.channel1 = self.create_channel("Channel 1")
        self.layout.addWidget(self.channel1)

        # Set Layout
        self.setLayout(self.layout)

        # Set up pygame for audio
        pygame.mixer.init()

        # Timer for updating Vu meter levels
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_vu_meters)
        self.timer.start(100)

    def create_channel(self, name):
        group_box = QGroupBox(name)
        layout = QVBoxLayout()

        # Channel Number
        layout.addWidget(QLabel(f"Channel: {name}"))

        # Volume Slider
        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setValue(50)
        layout.addWidget(QLabel("Volume"))
        layout.addWidget(volume_slider)

        # Panning Slider
        pan_slider = QSlider(Qt.Horizontal)
        pan_slider.setRange(-50, 50)
        pan_slider.setValue(0)
        layout.addWidget(QLabel("Panning"))
        layout.addWidget(pan_slider)

        # Mute/Solo Buttons
        mute_button = QPushButton("Mute")
        solo_button = QPushButton("Solo")
        layout.addWidget(mute_button)
        layout.addWidget(solo_button)

        # Vu Meter
        vu_meter = VuMeter(self)
        layout.addWidget(QLabel("VU Meter"))
        layout.addWidget(vu_meter)

        group_box.setLayout(layout)

        return group_box

    def update_vu_meters(self):
        # Simulate getting audio levels (normally this would come from the actual pygame mixer)
        # Update the VU meters with random levels for demonstration
        for widget in self.findChildren(VuMeter):
            widget.set_level(pygame.mixer.music.get_volume())  # Use pygame music volume as an example

    def play_audio(self, file_path):
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(-1)  # Loop the music
        pygame.mixer.music.set_volume(0.5)  # Set global volume (could also be controlled by the master slider)
