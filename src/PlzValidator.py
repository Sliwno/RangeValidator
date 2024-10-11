import sys
import logging
import os
import csv
from datetime import datetime
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QRadioButton, QLabel, QDialog, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

# Konfigurieren des Loggings
logging.basicConfig(level=logging.ERROR,  # Setzt das Log-Level auf ERROR
                    format='%(asctime)s - %(levelname)s - %(message)s')  # Format der Log-Nachrichten

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Import/Export")
       
        # Fenstergröße
        self.setFixedSize(300, 170)  

        # Dynamische Pfadsetzung für das Icon
        try:
            window_icon_path = self.find_icon('validierung.ico')
            self.setWindowIcon(QIcon(window_icon_path))
        except FileNotFoundError as e:
            print(e)
            
        # Layout an dem die Widgets von oben nach unten angeordnet werden
        layout = QVBoxLayout()

        # Initialisiere die Datenbank
        self.initialize_database()

        # Button zum Importieren der ersten CSV-Datei
        self.import_button_1 = QPushButton("CSV Vorlage", self)
        self.import_button_1.clicked.connect(self.import_csv_vorlage)
        layout.addWidget(self.import_button_1)

        self.label_btn1 = QLabel("Pfad: ", self)
        layout.addWidget(self.label_btn1)

        # Button zum Importieren der zweiten CSV-Datei
        self.import_button_2 = QPushButton("CSV zu Filtern", self)
        self.import_button_2.clicked.connect(self.import_csv_range)
        layout.addWidget(self.import_button_2)

        self.label_btn2 = QLabel("Pfad: ", self)
        layout.addWidget(self.label_btn2)

        # Horizontales Layout für Radio-Buttons und Einstellungsbutton
        radio_layout = QHBoxLayout()
        
        self.whitelist_radio = QRadioButton("Whitelist", self)
        self.blacklist_radio = QRadioButton("Blacklist", self)
        self.settings_button = QPushButton(self)

        # Icon für den Einstellungsbutton
        try:
            settings_icon_path = self.find_icon('die-einstellungen.ico')
            self.settings_button.setIcon(QIcon(settings_icon_path))
            self.settings_button.setIconSize(QSize(16, 16))
        except FileNotFoundError as e:
            print(e)
            self.settings_button.setText("Einstellungen")
  
        self.settings_button.clicked.connect(self.show_settings)
        self.settings_button.setFixedSize(20, 20)

        # Standardmäßig die Blacklist auswählen
        self.blacklist_radio.setChecked(True)

        # Füge die Radio-Buttons und den Einstellungsbutton zum Layout hinzu
        radio_layout.addWidget(self.whitelist_radio)
        radio_layout.addWidget(self.blacklist_radio)
        radio_layout.addWidget(self.settings_button)

        # Füge das horizontale Layout der Hauptlayout hinzu
        layout.addLayout(radio_layout)

        # Button zum Exportieren der CSV-Datei
        self.export_button = QPushButton("CSV exportieren", self)
        self.export_button.clicked.connect(self.export_csv)
        layout.addWidget(self.export_button)

        self.setLayout(layout)

    def find_icon(self, filename):
        if getattr(sys, 'frozen', False):
            # Wenn die Anwendung gebündelt ist (nach dem Build mit PyInstaller)
            bundle_dir = sys._MEIPASS
            return os.path.join(bundle_dir, filename)

        else:
            directory = os.walk(os.getcwd())
            for root, _, files in directory:
                for file in files:
                    if file == filename:
                        return os.path.join(root, file)
        
    def import_csv_vorlage(self):
        try:
            # Öffnet einen Datei-Dialog zum Auswählen der ersten CSV-Datei
            file_dialog = QFileDialog(self)
            file_path, _ = file_dialog.getOpenFileName(self, "CSV PLZ-Vorlage auswählen", "", "CSV-Dateien (*.csv)")
            self.label_btn1.setText(f"Pfad: {file_path}")

            if file_path:
                # Hier kann der Code zum Einlesen der ersten CSV-Datei platziert werden
                print(f"CSV 1 importiert: {file_path}")
                reader = self.read_csv(file_path)
                
                self.vorlage_numbers = []
                for item in reader:
                    try:
                        self.vorlage_numbers.append(int(item[0]))
                
                    except ValueError as ve:
                        error_message = f"Fehler beim Verarbeiten des Eintrags '{item[0]}'\nERROR: {ve} \n\nVerarbeitung wird fortgesetzt."
                        logging.error(error_message)
                        QMessageBox.critical(self,"Verarbeitungsfehler",error_message)  # Benutzerfeedback geben
                        continue  # Weiter mit dem nächsten Eintrag

                self.vorlage_numbers = list(set(self.vorlage_numbers))  # Duplikate entfernen
                self.vorlage_numbers.sort()  # Liste sortieren
                    
        except FileNotFoundError:
            logging.error("Die ausgewählte Datei wurde nicht gefunden.")
            QMessageBox.critical(self, "Fehler", "Die ausgewählte Datei wurde nicht gefunden.")

        except ValueError as e:
            logging.error("Fehler beim Konvertieren der CSV-Daten: %s", e)
            QMessageBox.critical(self, "Fehler", "Ungültige Daten in der CSV-Datei.")

        except Exception as e:
            logging.error("Ein unerwarteter Fehler ist aufgetreten: %s", e)
            QMessageBox.critical(self, "Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}")

    def import_csv_range(self):
        try: 
            # Öffnet einen Datei-Dialog zum Auswählen der zweiten CSV-Datei
            file_dialog = QFileDialog(self)
            file_path, _ = file_dialog.getOpenFileName(self, "CSV PLZ-Range auswählen", "", "CSV-Dateien (*.csv)")
            self.label_btn2.setText(f"Pfad: {file_path}")

            if file_path:
                print(f"CSV 2 importiert: {file_path}")
                reader = self.read_csv(file_path)
                
                # Entferne aus der Liste das "-" und fülle die zwischenzahlen mithilfe von range() in die Liste 
                self.range_numbers = []
                for item in reader:
                    try:
                        # Prüfen, ob der Eintrag ein Bereich ist (d.h. ob er einen Bindestrich enthält)
                        if "-" in item[0]:
                            start, end = map(int, item[0].split("-"))  # Split in Start und Ende
                            self.range_numbers.extend(range(start, end + 1))  # Den Bereich zur Liste hinzufügen
                        else:
                            # Wenn es sich um eine einzelne Zahl handelt, füge sie direkt hinzu
                            self.range_numbers.append(int(item[0]))
                    except ValueError as ve:
                        error_message = f"Fehler beim Verarbeiten des Eintrags '{item[0]}': {ve}"
                        logging.error(error_message)
                        QMessageBox.critical(self,"Verarbeitungsfehler", f"{error_message}")  # Benutzerfeedback geben
                        continue  # Weiter mit dem nächsten Eintrag

                self.range_numbers = list(set(self.range_numbers))  # Duplikate entfernen
                self.range_numbers.sort()  # Liste sortieren

        except Exception as e:
            error_message = f"Fehler: {str(e)}"
            logging.error(error_message)
            QMessageBox.critical(self, "Fehler: ", error_message)  # Benutzerfeedback geben

    def export_csv(self):
        try:   
            export_path = self.read_export_path()
            if export_path:
                if self.whitelist_radio.isChecked():
                    self.whitelist_filter()

                elif self.blacklist_radio.isChecked():
                    self.blacklist_filter()
                        
                else:
                    logging.error("Fehler: Filtermethode nicht ausgewählt.")
                    QMessageBox.critical(self,f"Fehler", "Filtermethode nicht ausgewählt.")
                
                self.export_file(export_path)
            else:
                logging.error("Exportpfad nicht festgelegt.")
                QMessageBox.critical(self,f"Fehler", "Exportpfad nicht festgelegt.")   

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Lesen der Datei: {str(e)}")

    def whitelist_filter(self):
        # Prüfen, ob beide CSV-Dateien importiert wurden
        if hasattr(self, 'vorlage_numbers') and hasattr(self, 'range_numbers'):
            # Filtere die Zahlen aus der Vorlage, die in der Range-Liste enthalten sind
            self.filtered_numbers = [num for num in self.vorlage_numbers 
                                if num in self.range_numbers]     
        else:
            logging.error("Fehler: CSV-Dateien nicht importiert.")
            QMessageBox.critical(self, f"Fehler", "CSV-Dateien nicht importiert.")

    def blacklist_filter(self):
        # Prüfen, ob beide CSV-Dateien importiert wurden
        if hasattr(self, 'vorlage_numbers') and hasattr(self, 'range_numbers'):
            # Filtere die Zahlen aus der Vorlage, die nicht in der Range-Liste enthalten sind
            self.filtered_numbers = [num for num in self.vorlage_numbers 
                                if num not in self.range_numbers]
        else:
            logging.error("Fehler: CSV-Dateien nicht importiert.")
            QMessageBox.critical(self,f"Fehler","CSV-Dateien nicht importiert.")

    def export_file(self, export_path):

        # Aktuelles Datum im Format 'YYYY-MM-DD'
        current_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Dateiname mit Datum
        filename = f"filtered_plz_{current_date}.csv"
        # Schreibe die gefilterten Zahlen in eine neue CSV-Datei
        
        with open(os.path.join(export_path, filename),'w',newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["PLZ"])  # Schreibe die Spaltenüberschrift
            for num in self.filtered_numbers:
                writer.writerow([num])
            self.show_success_message("CSV-Datei erfolgreich erstellt!")

    def show_success_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(message)
        msg_box.setWindowTitle("Erfolg")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def read_csv(self, file_path):
        try:
            csv_data = []
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    csv_data.append(row)
                
                # Entferne 'PLZ' aus der Liste
                if csv_data[0][0] == 'PLZ':
                    csv_data.pop(0)

                print(f"CSV_DATA:\n{csv_data}\n")
                print("CSV_DATA ERFOLGREICH IMPORTIERT\n")
                return csv_data
        except Exception as e:
            QMessageBox.critical(self,"Fehler",f"beim Lesen der Datei: {str(e)}")
    
    def initialize_database(self):
        # Pfad zur Datenbank
        filename='settings.db'
        db_path = self.find_db(filename) 
        if not db_path:
            db_path = os.path.join(os.getcwd(), filename)
            os.path.exists(db_path)

        # Verbindung zur Datenbank herstellen und die Tabelle "settings" erstellen, falls sie nicht existiert
        self.conn = sqlite3.connect(db_path)
        cursor = self.conn.cursor()

        # Erstelle die Tabelle für die Einstellungen
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            export_path TEXT
                        )''')
        self.conn.commit()

    def find_db(self, filename):
        if getattr(sys, 'frozen', False):
            # Wenn die Anwendung gebündelt ist (nach dem Build mit PyInstaller)
            bundle_dir = sys._MEIPASS
            return os.path.join(bundle_dir, filename)
        
        directory = os.walk(os.getcwd())
        for root, _, files in directory:
            print(root)
            for file in files:
                if file == (filename):
                    return os.path.join(root, file)
                
    def show_settings(self):
        # Erstelle ein neues Dialog-Fenster
        dialog = QDialog(self)
        dialog.setWindowTitle("Exportpfad festlegen")
        dialog.setFixedSize(200, 150)

        # Layout für das Dialog-Fenster
        layout = QVBoxLayout()

        # Label für die Beschreibung
        label = QLabel("Geben Sie den Exportpfad an:")
        layout.addWidget(label)

        # Eingabefeld für den Exportpfad
        self.path_input = QLineEdit(dialog)
        layout.addWidget(self.path_input)
        
        # Lese den Exportpfad aus der Datenbank
        export_path = self.read_export_path()
        if export_path:
            self.path_input.setText(export_path)

        # Button zum Durchsuchen eines Verzeichnisses
        browse_button = QPushButton("Durchsuchen", dialog)
        browse_button.clicked.connect(self.browse_export_path)
        layout.addWidget(browse_button)

        # Bestätigungsbutton
        confirm_button = QPushButton("Bestätigen", dialog)
        confirm_button.clicked.connect(lambda: self.save_export_path(dialog))  # Schließt den Dialog
        layout.addWidget(confirm_button)

        # Setzt das Layout für den Dialog
        dialog.setLayout(layout)

        # Öffnet den Dialog und wartet auf die Eingabe des Benutzers
        if dialog.exec_():
            export_path = self.path_input.text()
            print(f"Exportpfad festgelegt: {export_path}")

    def read_export_path(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT export_path FROM settings WHERE id = 1")  # Hier id entsprechend anpassen
        result = cursor.fetchone()  # Einzeln oder mit fetchall() für mehrere Zeilen

        if result:
            return result[0]  # Gibt den Exportpfad zurück, der in der ersten Spalte steht
        else:
            return None  # Gibt None zurück, wenn kein Ergebnis gefunden wurde

    def browse_export_path(self):
        # Datei-Dialog zum Auswählen eines Verzeichnisses
        dir_path = QFileDialog.getExistingDirectory(self, "Exportpfad auswählen")
        if dir_path:
            self.path_input.setText(dir_path)

    def save_export_path(self, dialog):
        export_path = self.path_input.text()

        if export_path:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM settings WHERE id = 1")
            exists = cursor.fetchone()[0]

            if exists:
                # Aktualisiere den vorhandenen Pfad
                cursor.execute("UPDATE settings SET export_path = ? WHERE id = 1", (export_path,))
            else:
                # Füge den Pfad als neuen Eintrag hinzu
                cursor.execute("INSERT INTO settings (id, export_path) VALUES (1, ?)", (export_path,))

            self.conn.commit()
        dialog.accept()

def main():    
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
