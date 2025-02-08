# Lin Yue - DJ Controller Interface

Lin Yue is a DJ controller interface designed for seamless interaction with audio files. This Python-based project features a user-friendly UI with drag-and-drop functionality, allowing users to load, sync, and adjust the playback of audio tracks. It includes essential features like tempo and key adjustment, volume control, and sync capabilities between decks.

## Features

- **File Box**: Drag and drop mptm files to load audio tracks.
- **Waveform Display**: View the waveform of the loaded tracks.
- **Pitch/Tempo Slider**: Adjust the tempo of the audio.
- **Key Counter Box**: Display the key of the loaded track.
- **Crossfader**: Horizontal slider to blend between Deck A and Deck B.
- **Volume Sliders**: Individual vertical volume sliders for Deck A and Deck B.
- **Deck Sync**: Synchronize Deck A and Deck B to a global tempo.
- **Deck Eject**: Eject files from Deck A and Deck B.

## Requirements

- Python 3.x
- PyQt5 or PySide2 (for the GUI)
- pydub (for audio analysis)
- mptm file support

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lin-yue.git
   cd ./lin-yue/
   ```

2. Make new Virtual Environment:
```
python -m venv .venv
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```
4. Run the Program:
```
python main.py
```