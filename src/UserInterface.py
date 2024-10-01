import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()  # Aufruf des Konstruktors der Oberklasse
        self.setWindowTitle("Mein PyQt5 Fenster")
        self.setGeometry(0, 0, 400, 200)  # Fenstergröße setzen
        
        self.initUI()  # UI initialisieren
        self.center()  # Fenster zentrieren

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel("Willkommen in der Anwendung!")
        layout.addWidget(self.label)

        button = QPushButton("Klick mich!")
        button.clicked.connect(self.on_button_click)  # Funktion als Callback verbinden
        layout.addWidget(button)

        self.setLayout(layout)  # Layout für das Fenster-Widget setzen

    def center(self):
        # Berechne die Bildschirmgröße
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)  # Fensterposition setzen

    def on_button_click(self):
        self.label.setText("Button wurde geklickt!")

def main():
    app = QApplication(sys.argv)
    window = MyWindow()  # Erstelle eine Instanz der Klasse
    window.show()  # Zeige das Fenster
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
