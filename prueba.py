from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aplicación Empresarial")
        self.setGeometry(100, 100, 800, 600)  # Tamaño de la ventana

        # Etiqueta de bienvenida
        label = QLabel("¡Bienvenido a la aplicación empresarial!", self)
        label.setFont(QFont("Arial", 18))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setGeometry(150, 200, 500, 100)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
