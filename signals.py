from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class Emitter(QObject):
    # Define a signal without arguments
    simple_signal = pyqtSignal()
    
    # Define a signal with arguments
    data_signal = pyqtSignal(int, str)
    
    def __init__(self):
        super().__init__()
    
    def emit_signals(self):
        self.simple_signal.emit()
        self.data_signal.emit(42, "Hello")

class Receiver:
    @pyqtSlot()
    def handle_simple_signal(self):
        print("Simple signal received!")
    
    @pyqtSlot(int, str)
    def handle_data_signal(self, number, text):
        print(f"Data signal received with number: {number} and text: {text}")
