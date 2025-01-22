import sys
import asyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PySide6.QtCore import QThread, Signal
from funcs import app  # Import your async function from funcs.py


import sys

class CustomLogger:
    def __init__(self, log_signal):
        self.log_signal = log_signal
        self.buffer = ""

    def write(self, message):
        if message.strip():  # Ignore empty messages
            self.log_signal.emit(message.strip())  # Emit each message immediately

    def flush(self):
        pass  # No need to implement flush for this use case



from PySide6.QtCore import QThread, Signal
import asyncio

class AsyncFunctionThread(QThread):
    log_signal = Signal(str)  # Signal to send logs to the GUI

    def __init__(self, func):
        super().__init__()
        self.func = func  # Pass the function to be executed
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.run_app())

    async def run_app(self):
        logger = CustomLogger(self.log_signal)  # Redirect logs to the GUI
        original_stdout = sys.stdout
        sys.stdout = logger  # Redirect stdout to our custom logger

        try:
            await self.func()  # Run the passed async function
        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
        finally:
            sys.stdout = original_stdout  # Restore stdout


from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from PySide6.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self, func):
        super().__init__()
        self.setWindowTitle("Async Function Runner")
        self.setGeometry(100, 100, 800, 600)

        self.max_logs = 3000

        # Text box to display logs
        # Use QPlainTextEdit instead of QTextEdit
        self.text_display = QPlainTextEdit()
        self.text_display.setReadOnly(True)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.text_display)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Async Thread
        self.thread = AsyncFunctionThread(func)
        self.thread.log_signal.connect(self.display_logs)
        self.thread.start()

        # System Tray
        self.tray_icon = QSystemTrayIcon(QIcon("icon.png"), self)
        tray_menu = QMenu()

        # Show Window Action
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        # Exit Action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        """Override the close event to hide the window instead of exiting."""
        event.ignore()
        self.hide()

    def display_logs(self, logs):
        self.text_display.appendPlainText(logs)

        # Limit the number of lines
        if self.text_display.blockCount() > self.max_logs:
            # Get all lines as a list, keep only the last 1000 lines
            lines = self.text_display.toPlainText().split('\n')
            self.text_display.setPlainText('\n'.join(lines[-1000:]))

        self.text_display.ensureCursorVisible()

    def exit_app(self):
        """Stop the background thread and quit the application."""
        self.thread.terminate()  # Terminate the async thread
        QApplication.quit()



def run_gui():
    qt_app = QApplication(sys.argv)
    qt_app.setWindowIcon(QIcon("icon.png"))  # Set the icon for the app
    window = MainWindow(app)  # Pass the `app` function
    window.show()
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    run_gui()

