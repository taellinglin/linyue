# ui-mixer.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider

class MixerTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Example Mixer control
        layout.addWidget(QLabel("Mixer (coming soon!)"))
        layout.addWidget(QSlider())

        # Make layout stretchable
        layout.setStretch(0, 1)
        layout.setStretch(1, 3)

        self.setLayout(layout)
