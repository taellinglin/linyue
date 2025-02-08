# main.py

import sys
from PyQt5.QtWidgets import QApplication
from ui import TrackerDAWUI

def main():
    app = QApplication(sys.argv)
    window = TrackerDAWUI()
    window.showFullScreen()  # Make it full screen
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
