from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtWidgets, QtCore, QtGui
import sys

class PlayerRow(QtWidgets.QWidget):
    # One row in the NewGameDialog for a single player.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.photo_path: str | None = None
        
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(8, 6, 8, 6)
        self.layout.setSpacing(10)

        # Photo preview
        self.photo_lbl = QtWidgets.QLabel()
        self.photo_lbl.setFixedSize(QtCore.QSize(64,64))
        self.photo_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.photo_lbl.setStyleSheet("border-radius:6px; background:#ddd;")
        self.layout.addWidget(self.photo_lbl)

        # Name
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Player Name")
        self.name_edit.setMinimumWidth(150)
        self.layout.addWidget(self.name_edit)
        
        # Bankroll
        self.buyin = QtWidgets.QDoubleSpinBox()
        self.buyin.setRange(0, 1_000)
        self.buyin.setDecimals(1)
        self.buyin.setSingleStep(2.5)
        self.buyin.setMinimumWidth(100)
        self.buyin.setPrefix("€")
        self.layout.addWidget(self.buyin)

        # Choose photo button
        self.cp_btn = QtWidgets.QPushButton("Choose Photo...")
        self.cp_btn.clicked.connect(self.on_choose_photo_clicked)
        self.layout.addWidget(self.cp_btn)

        # Remove player
        self.remove_btn = QtWidgets.QPushButton("Remove")
        self.remove_btn.setStyleSheet("background-color:#e74c3c; color:red;")
        self.layout.addWidget(self.remove_btn)

    @QtCore.Slot()
    def on_choose_photo_clicked(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Choose Player Photo",
            str(Path.home()),
            "Image Files (*.png *.jpg *.bmp)"
        )
        if not path:
            return
        self.photo_path = path
        pixmap = QtGui.QPixmap(path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(48,48,QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
            self.photo_lbl.setPixmap(pixmap)
    def to_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "bankroll": self.buyin.value(),
        "photo_path": self.photo_path
        }

class NewGameDialog(QtWidgets.QDialog):
    # Dialog to set up a new game.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Game Setup")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12,12,12,12)
        root.setSpacing(10)

        title = QtWidgets.QLabel("New Game Setup")
        title.setStyleSheet("font-size:18px; font-weight:700;")
        root.addWidget(title, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Add player area
        top = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Add Player +")
        self.add_btn.clicked.connect(self.on_add_player_clicked)
        top.addWidget(self.add_btn, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        top.addStretch(1)
        root.addLayout(top)

        # Scroll area for player rows
        self.list_container = QtWidgets.QWidget()
        self.list_layout = QtWidgets.QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0,0,0,0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_container)
        scroll.setStyleSheet("QScrollArea { border:1px; solid #ccc; border-radius: 8px;}")
        root.addWidget(scroll)
        
        # Confirm / Cancel
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setText("Confirm")
        self.buttons.button(QtWidgets.QDialogButtonBox.Cancel).setText("Cancel")
        self.buttons.buttons()[0].setStyleSheet("background-color:#27ae60; color:white;")
        self.buttons.buttons()[1].setStyleSheet("background-color:#e74c3c; color:white;")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)
        
        self.rows: list[PlayerRow] = []

        # We start by default with the minimum of 4 players
        for _ in range(4):
            self.on_add_player_clicked()
    
    @QtCore.Slot()
    def on_add_player_clicked(self):
        row = PlayerRow(self)
        row.remove_btn.clicked.connect(lambda: self.on_remove_player_clicked(row))

        self.list_layout.insertWidget(self.list_layout.count() - 1, row)
        self.rows.append(row)

    @QtCore.Slot()
    def on_remove_player_clicked(self, row: PlayerRow):
        if row in self.rows:
            self.rows.remove(row)
            self.list_layout.removeWidget(row)
            row.deleteLater()

    def get_players(self) -> list[dict]:
        return [row.to_data() for row in self.rows if row.to_data()["name"]]

    def on_confirm(self):
        players = self.get_players()

        players_valid = [p for p in players if p["name"] and p["bankroll"] > 0]
        if len(players_valid) < 4:
            QtWidgets.QMessageBox.warning(self, "Invalid Players", "Please add at least 4 players with valid names and bankrolls.")
            return 

        names = [p["name"] for p in players_valid]
        if len(names) != len(set(names)):
            QtWidgets.QMessageBox.warning(self, "Duplicate Names", "Please ensure all player names are unique.")
            return 
        self.accept() 

class Menu(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BestIA - Main Menu")
        
        # Title
        self.title = QtWidgets.QLabel("BestIA")
        title_font = QtGui.QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        self.title.setFont(title_font)
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Option Buttons
        self.play = QtWidgets.QPushButton("New Game")
        self.options = QtWidgets.QPushButton("Options")
        self.exit = QtWidgets.QPushButton("Exit")
        
        # Size and styling
        button_width = 200
        button_height = 50
        for button in [self.play, self.options, self.exit]:
            button.setMinimumSize(button_width, button_height)
            button.setMaximumSize(button_width, button_height)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 6px 12px;
                    }
                QPushButton:hover {
                    background-color: #45a049;
                    }
                QPushButton:pressed {
                    background-color: #3e8e41;
                    }

            """)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addStretch() 
        
        # Button layout 
        button_layout = QtWidgets.QVBoxLayout()
        button_layout.addWidget(self.title)
        button_layout.addSpacing(30)   
        button_layout.addWidget(self.play, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        button_layout.addSpacing(15) 
        button_layout.addWidget(self.options, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        button_layout.addSpacing(15)
        button_layout.addWidget(self.exit, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Center the button layout
        button_container = QtWidgets.QWidget()
        button_container.setLayout(button_layout)
        
        container_layout = QtWidgets.QHBoxLayout()
        container_layout.addStretch()
        container_layout.addWidget(button_container)
        container_layout.addStretch()
        
        main_layout.addLayout(container_layout)
        main_layout.addStretch()  # Lower space 
        
        # Connections
        self.exit.clicked.connect(self.on_exit_clicked)
        self.play.clicked.connect(self.on_new_game_clicked)

        self.setLayout(main_layout)
    @QtCore.Slot()
    def on_exit_clicked(self):
        QtWidgets.QApplication.quit()
    
    def on_new_game_clicked(self):
        dialog = NewGameDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            players_data = dialog.get_players()
            # TODO: Starting game logic
            print("Starting new game with players:", players_data)
        else: 
            print("New game canceled.")


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    window = Menu()
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())
