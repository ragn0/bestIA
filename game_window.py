"""Game window showing the table and game state."""
from pathlib import Path
import random
import math
from typing import Optional, Dict, List
from PySide6 import QtWidgets, QtCore, QtGui
from engine import Engine, Player, Action, Phase, Card
import logging
logger = logging.getLogger(__name__)


# Mapping engine values to sprite file numbers
VALUE_TO_SPRITE = {
    "Asso": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "Fante": "8",
    "Cavallo": "9",
    "Re": "10",
}

SEED_TO_SPRITE = {
    "Bastoni": "b",
    "Coppe": "c",
    "Denari": "d",
    "Spade": "s",
}


def card_to_sprite_path(card: Card) -> Path:
    """Convert engine Card to sprite file path."""
    sprite_dir = Path(__file__).parent / "sprites" / "cards"
    seed_char = SEED_TO_SPRITE[card.seed]
    value_num = VALUE_TO_SPRITE[card.value]
    return sprite_dir / f"{seed_char}{value_num}.png"


class PlayerWidget(QtWidgets.QWidget):
    """Widget representing a player at the table."""
    def __init__(self, player_data: dict, position: int, total_players: int, parent=None):
        super().__init__(parent)
        self.player_data = player_data
        self.position = position
        self.total_players = total_players
        
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(2)
        
        # Profile photo (compact)
        self.photo_label = QtWidgets.QLabel()
        self.photo_label.setFixedSize(44, 44)
        self.photo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet("""
            QLabel {
                border-radius: 22px;
                background-color: #ddd;
                border: 2px solid #3498db;
            }
        """)
        
        if player_data.get("photo_path"):
            pixmap = QtGui.QPixmap(player_data["photo_path"])
            if not pixmap.isNull():
                pixmap = pixmap.scaled(40, 40, QtCore.Qt.KeepAspectRatioByExpanding,
                                      QtCore.Qt.SmoothTransformation)
                circular = QtGui.QPixmap(40, 40)
                circular.fill(QtCore.Qt.GlobalColor.transparent)
                painter = QtGui.QPainter(circular)
                painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
                painter.setBrush(QtGui.QBrush(pixmap))
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.drawEllipse(0, 0, 40, 40)
                painter.end()
                self.photo_label.setPixmap(circular)
        
        self.layout.addWidget(self.photo_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        
        # Name (compact)
        self.name_label = QtWidgets.QLabel(player_data["name"])
        self.name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.name_label.setMaximumWidth(100)
        self.name_label.setWordWrap(True)
        self.name_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 10px;
                color: white;
                background-color: rgba(0, 0, 0, 140);
                padding: 2px 4px;
                border-radius: 3px;
            }
        """)
        self.layout.addWidget(self.name_label)
        
        # Bankroll (compact)
        self.bankroll_label = QtWidgets.QLabel(f"€{player_data['bankroll']:.2f}")
        self.bankroll_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.bankroll_label.setStyleSheet("font-size: 9px; color: #f39c12;")
        self.layout.addWidget(self.bankroll_label)
        
        # Cards container
        self.cards_container = QtWidgets.QWidget()
        self.cards_layout = QtWidgets.QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(2)
        self.layout.addWidget(self.cards_container)
        
        # Status label (compact)
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 9px; color: #95a5a6;")
        self.layout.addWidget(self.status_label)
        
        # Fixed max size so the widget doesn't grow
        self.setMaximumWidth(140)
    
    def update_cards(self, cards: List[Card], show_front: bool, back_path: Path):
        """Update displayed cards."""
        if not self.cards_layout:
            return
        
        # Clear existing cards safely
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
        
        # Card size: compact (38x56 visible)
        card_w, card_h = 38, 56
        for card in cards:
            if card is None:
                continue
                
            card_label = QtWidgets.QLabel()
            card_label.setFixedSize(card_w, card_h)
            card_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            card_label.setStyleSheet("""
                QLabel {
                    border: 1px solid #34495e;
                    border-radius: 3px;
                    background-color: white;
                }
            """)
            
            try:
                if show_front:
                    card_path = card_to_sprite_path(card)
                    if card_path.exists():
                        pixmap = QtGui.QPixmap(str(card_path))
                    else:
                        pixmap = QtGui.QPixmap()
                else:
                    if back_path.exists():
                        pixmap = QtGui.QPixmap(str(back_path))
                    else:
                        pixmap = QtGui.QPixmap()
                
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(card_w - 2, card_h - 2, QtCore.Qt.KeepAspectRatio,
                                          QtCore.Qt.SmoothTransformation)
                    card_label.setPixmap(pixmap)
            except Exception as e:
                print(f"Error loading card image: {e}")
            
            self.cards_layout.addWidget(card_label)
    
    def update_status(self, text: str):
        """Update status text."""
        self.status_label.setText(text)
    
    def update_bankroll(self, bankroll: float):
        """Update bankroll display."""
        self.bankroll_label.setText(f"€{bankroll:.2f}")


class GameWindow(QtWidgets.QMainWindow):
    """Main game window with table and players."""
    def __init__(self, players_data: List[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("BestIA - Game")
        self.setMinimumSize(1200, 800)
        
        # Store player data
        self.players_data = players_data
        self.player_widgets: Dict[int, PlayerWidget] = {}
        
        # Create engine players
        engine_players = [
            Player(p["name"], bankroll=int(p["bankroll"] * 100))  # Convert to cents
            for p in players_data
        ]
        
        # Create engine
        self.engine = Engine(engine_players, pot=300, dealer=0, seed=None)
        self.human_player_index = 0  # First player is human (can be made configurable)
        
        # Timer for actions
        self.action_timer = QtCore.QTimer()
        self.action_timer.timeout.connect(self.on_timer_timeout)
        self.timer_seconds = 60
        self.timer_label: Optional[QtWidgets.QLabel] = None
        
        # Central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar with timer and phase info
        top_bar = QtWidgets.QHBoxLayout()
        self.phase_label = QtWidgets.QLabel("Phase: DEAL_DECIDE")
        self.phase_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        top_bar.addWidget(self.phase_label)
        
        top_bar.addStretch()
        
        self.timer_label = QtWidgets.QLabel("30s")
        self.timer_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #e74c3c;
            padding: 5px 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        top_bar.addWidget(self.timer_label)
        
        main_layout.addLayout(top_bar)
        
        # Table scene
        self.table_scene = QtWidgets.QGraphicsScene()
        self.table_view = QtWidgets.QGraphicsView(self.table_scene)
        self.table_view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.table_view.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        main_layout.addWidget(self.table_view)
        
        # Bottom action area
        self.action_area = QtWidgets.QWidget()
        self.action_layout = QtWidgets.QHBoxLayout(self.action_area)
        self.action_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.action_area)
        
        # Load table image
        self.setup_table()
        
        # Setup players around table
        self.setup_players()
        
        # Briscola card display (center of table) - create after table is loaded
        self.briscola_label = None
        self.trick_label = None
        self.trick_cards_container = None  # Container for cards in current trick
        
        # Connect to engine updates
        self.update_from_engine()
        
        # Start action timer
        self.start_action_timer()
    
    def setup_table(self):
        """Load and display table image."""
        table_path = Path(__file__).parent / "sprites" / "table" / "table.png"
        if table_path.exists():
            pixmap = QtGui.QPixmap(str(table_path))
            if not pixmap.isNull():
                # Scale to fit view
                item = self.table_scene.addPixmap(pixmap)
                # Set scene rect to pixmap size
                self.table_scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())
                # Fit in view after a short delay to ensure view is sized
                QtCore.QTimer.singleShot(100, lambda: self.table_view.fitInView(
                    self.table_scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio))
    
    def setup_players(self):
        """Position players around an oval table."""
        n = len(self.players_data)
        scene_rect = self.table_scene.sceneRect()
        if scene_rect.isEmpty():
            center_x = 600
            center_y = 400
            table_w = 1200
            table_h = 800
        else:
            center_x = scene_rect.center().x()
            center_y = scene_rect.center().y()
            table_w = scene_rect.width()
            table_h = scene_rect.height()
        
        # Oval table: use different radii for width and height
        # Position players on the oval edge
        radius_x = table_w * 0.35  # Horizontal radius (wider)
        radius_y = table_h * 0.38  # Vertical radius (taller)
        widget_w, widget_h = 70, 90  # approximate half-size for centering
        
        for i, player_data in enumerate(self.players_data):
            # Angle around the oval
            angle = (2 * math.pi * i) / n - math.pi / 2
            
            # Calculate position on oval (parametric equation)
            x = center_x + radius_x * math.cos(angle) - widget_w
            y = center_y + radius_y * math.sin(angle) - widget_h
            
            player_widget = PlayerWidget(player_data, i, n)
            proxy = self.table_scene.addWidget(player_widget)
            if proxy:
                proxy.setZValue(5)
                proxy.setPos(x, y)
            
            self.player_widgets[i] = player_widget
    
    def update_from_engine(self):
        """Update GUI from engine state."""
        snapshot = self.engine.snapshot()
        logger.debug(f"Engine snapshot: {snapshot}")
        
        # Check if game is finished
        if self.engine.phase == Phase.FINE:
            self.action_timer.stop()
            self.show_game_over()
            return
        
        # Update phase label
        phase_name = snapshot["phase"].upper().replace("_", " ")
        logger.debug(f"Passing from phase: {self.phase_label.text()} to {phase_name}")
        self.phase_label.setText(f"Phase: {phase_name}")
        
        # Update briscola card (create if needed)
        if snapshot["briscola_card"]:
            if self.briscola_label is None:
                self.briscola_label = QtWidgets.QLabel()
                self.briscola_label.setFixedSize(52, 78)
                self.briscola_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.briscola_label.setStyleSheet("""
                    QLabel {
                        border: 2px solid #f39c12;
                        border-radius: 4px;
                        background-color: white;
                    }
                """)
                briscola_proxy = self.table_scene.addWidget(self.briscola_label)
                briscola_proxy.setZValue(1)
            
            briscola_card = snapshot["briscola_card"]
            card = Card(briscola_card["seed"], briscola_card["value"])
            card_path = card_to_sprite_path(card)
            if card_path.exists():
                pixmap = QtGui.QPixmap(str(card_path))
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(48, 74, QtCore.Qt.KeepAspectRatio,
                                          QtCore.Qt.SmoothTransformation)
                    self.briscola_label.setPixmap(pixmap)
            
            # Position briscola in center
            scene_rect = self.table_scene.sceneRect()
            if not scene_rect.isEmpty():
                center_x = scene_rect.center().x()
                center_y = scene_rect.center().y()
                for item in self.table_scene.items():
                    if item and item.widget() == self.briscola_label:
                        item.setPos(center_x - 26, center_y - 90)  # Above trick cards
                        break
        
        # Update current trick display with cards (create if needed)
        scene_rect = self.table_scene.sceneRect()
        if scene_rect.isEmpty():
            center_x = 600
            center_y = 400
        else:
            center_x = scene_rect.center().x()
            center_y = scene_rect.center().y()
        
        if snapshot["current_trick"] and len(snapshot["current_trick"]) > 0:
            # Create trick cards container if needed
            if self.trick_cards_container is None:
                self.trick_cards_container = QtWidgets.QWidget()
                self.trick_cards_container.setStyleSheet("background-color: transparent;")
                trick_layout = QtWidgets.QVBoxLayout(self.trick_cards_container)
                trick_layout.setContentsMargins(0, 0, 0, 0)
                trick_layout.setSpacing(5)
                
                # Title label
                self.trick_label = QtWidgets.QLabel("Current Trick")
                self.trick_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.trick_label.setStyleSheet("""
                    QLabel {
                        font-size: 11px;
                        font-weight: bold;
                        color: white;
                        background-color: rgba(0, 0, 0, 200);
                        padding: 4px 8px;
                        border-radius: 4px;
                    }
                """)
                trick_layout.addWidget(self.trick_label)
                
                # Cards container
                self.trick_cards_layout = QtWidgets.QHBoxLayout()
                self.trick_cards_layout.setContentsMargins(0, 0, 0, 0)
                self.trick_cards_layout.setSpacing(8)
                trick_layout.addLayout(self.trick_cards_layout)
                
                trick_proxy = self.table_scene.addWidget(self.trick_cards_container)
                if trick_proxy:
                    trick_proxy.setZValue(3)
            
            # Clear existing trick cards
            for i in reversed(range(self.trick_cards_layout.count())):
                item = self.trick_cards_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)
            
            # Add cards from current trick
            for play in snapshot["current_trick"]:
                try:
                    actor = play.get("actor", {})
                    card_data = play.get("card", {})
                    if not card_data:
                        continue
                    
                    card = Card(card_data["seed"], card_data["value"])
                    
                    # Create card widget with player name
                    card_widget = QtWidgets.QWidget()
                    card_widget.setFixedSize(55, 110)
                    card_layout = QtWidgets.QVBoxLayout(card_widget)
                    card_layout.setContentsMargins(0, 0, 0, 0)
                    card_layout.setSpacing(3)
                    
                    # Player name label
                    if actor.get("kind") == "player":
                        player_id = actor.get("id", 0)
                        if player_id < len(self.players_data):
                            player_name = self.players_data[player_id]["name"]
                        else:
                            player_name = f"Player {player_id}"
                    else:
                        player_name = f"Buco {actor.get('id', 0)}"
                    
                    name_label = QtWidgets.QLabel(player_name)
                    name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    name_label.setStyleSheet("""
                        QLabel {
                            font-size: 9px;
                            font-weight: bold;
                            color: white;
                            background-color: rgba(52, 73, 94, 220);
                            padding: 2px 4px;
                            border-radius: 3px;
                        }
                    """)
                    card_layout.addWidget(name_label)
                    
                    # Card image
                    card_label = QtWidgets.QLabel()
                    card_label.setFixedSize(50, 75)
                    card_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    card_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #2c3e50;
                            border-radius: 5px;
                            background-color: white;
                        }
                    """)
                    
                    card_path = card_to_sprite_path(card)
                    if card_path.exists():
                        pixmap = QtGui.QPixmap(str(card_path))
                        if not pixmap.isNull():
                            pixmap = pixmap.scaled(46, 71, QtCore.Qt.KeepAspectRatio,
                                                  QtCore.Qt.SmoothTransformation)
                            card_label.setPixmap(pixmap)
                    
                    card_layout.addWidget(card_label)
                    self.trick_cards_layout.addWidget(card_widget)
                except Exception as e:
                    print(f"Error creating trick card widget: {e}")
                    continue
            
            # Position trick container in center
            if self.trick_cards_container:
                for item in self.table_scene.items():
                    if item and item.widget() == self.trick_cards_container:
                        # Center the container horizontally, position below briscola
                        num_cards = len(snapshot["current_trick"])
                        container_w = 55 * num_cards + 8 * max(0, num_cards - 1)
                        item.setPos(center_x - container_w / 2, center_y + 20)  # Below briscola
                        break
        else:
            # Hide trick container if no trick
            if self.trick_cards_container:
                for item in self.table_scene.items():
                    if item and item.widget() == self.trick_cards_container:
                        item.setPos(-1000, -1000)  # Move off-screen
                        break
        
        # Update player displays
        for i, player_info in enumerate(snapshot["players"]):
            if i in self.player_widgets:
                widget = self.player_widgets[i]
                widget.update_bankroll(player_info["bankroll"] / 100.0)  # Convert cents to euros
                
                status_parts = []
                if player_info["tricks_won"] > 0:
                    status_parts.append(f"{player_info['tricks_won']} tricks")
                if player_info["is_playing"]:
                    status_parts.append("Playing")
                if player_info["in_buco"]:
                    status_parts.append("Buco")
                widget.update_status(", ".join(status_parts) if status_parts else "")
                
                # Update cards (with null safety)
                if widget and widget.cards_layout:
                    back_path = Path(__file__).parent / "sprites" / "back" / "back.png"
                    
                    if i == self.human_player_index:
                        # Show human player's cards
                        try:
                            hand = self.engine.get_player_hand(i)
                            if hand is not None:
                                widget.update_cards(hand, show_front=True, back_path=back_path)
                            else:
                                widget.update_cards([], show_front=False, back_path=back_path)
                        except Exception as e:
                            print(f"Error updating human player cards: {e}")
                            widget.update_cards([], show_front=False, back_path=back_path)
                    else:
                        # Show back for other players (compact size)
                        num_cards = player_info.get("num_cards", 0)
                        card_w, card_h = 38, 56
                        # Clear existing cards safely
                        for j in reversed(range(widget.cards_layout.count())):
                            item = widget.cards_layout.itemAt(j)
                            if item and item.widget():
                                w = item.widget()
                                w.setParent(None)
                                w.deleteLater()
                        
                        for j in range(num_cards):
                            card_label = QtWidgets.QLabel()
                            card_label.setFixedSize(card_w, card_h)
                            card_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                            card_label.setStyleSheet("""
                                QLabel {
                                    border: 1px solid #34495e;
                                    border-radius: 3px;
                                    background-color: white;
                                }
                            """)
                            if back_path.exists():
                                pixmap = QtGui.QPixmap(str(back_path))
                                if not pixmap.isNull():
                                    pixmap = pixmap.scaled(card_w - 2, card_h - 2, QtCore.Qt.KeepAspectRatio,
                                                          QtCore.Qt.SmoothTransformation)
                                    card_label.setPixmap(pixmap)
                            widget.cards_layout.addWidget(card_label)
        
        # Update action buttons
        self.update_action_buttons()
        
        # Auto-advance for non-human players (with safety check)
        try:
            actor = self.engine.current_actor()
            if actor is not None:
                if not (actor.kind == "player" and actor.id == self.human_player_index):
                    # Non-human player - take action after short delay
                    QtCore.QTimer.singleShot(500, lambda: self._safe_take_random_action())
        except Exception as e:
            print(f"Error in auto-advance: {e}")
    
    def _safe_take_random_action(self):
        """Safely take random action with error handling."""
        try:
            self.take_random_action()
        except Exception as e:
            print(f"Error taking random action: {e}")
    
    def update_action_buttons(self):
        """Update action buttons based on current phase and legal actions."""
        # Clear existing buttons
        for i in reversed(range(self.action_layout.count())):
            item = self.action_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        actor = self.engine.current_actor()
        if actor is None:
            return
        
        # Only show actions for human player
        if actor.kind == "player" and actor.id == self.human_player_index:
            legal = self.engine.legal_actions()
            for action in legal:
                btn = self.create_action_button(action)
                if btn:
                    self.action_layout.addWidget(btn)
        else:
            # Other players - will use random actions via timer
            pass
    
    def create_action_button(self, action: Action) -> Optional[QtWidgets.QPushButton]:
        """Create a button for an action."""
        if action.kind == "keep":
            btn = QtWidgets.QPushButton("Keep")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        elif action.kind == "fold":
            btn = QtWidgets.QPushButton("Fold")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        elif action.kind == "servito":
            btn = QtWidgets.QPushButton("No Change (Servito)")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        elif action.kind == "change_card":
            idx = action.payload["index"]
            btn = QtWidgets.QPushButton(f"Change Card {idx + 1}")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        elif action.kind == "change_cards":
            indices = action.payload["indices"]
            btn = QtWidgets.QPushButton(f"Change Cards {[i+1 for i in indices]}")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        elif action.kind == "take_buco":
            btn = QtWidgets.QPushButton("Take Buco")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        elif action.kind == "pass":
            btn = QtWidgets.QPushButton("Pass")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        elif action.kind == "discard":
            idx = action.payload["card_index"]
            btn = QtWidgets.QPushButton(f"Discard Card {idx + 1}")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        elif action.kind == "play_card":
            card = action.payload["card"]
            btn = QtWidgets.QPushButton(f"Play {card.value} di {card.seed}")
            btn.clicked.connect(lambda: self.on_action_clicked(action))
            return btn
        return None
    
    @QtCore.Slot()
    def on_action_clicked(self, action: Action):
        """Handle action button click."""
        try:
            if action is None:
                return
            logger.debug(f"Action clicked: {action}")
            self.engine.step(action)
            self.update_from_engine()
            self.start_action_timer()
        except Exception as e:
            print(f"Error in action click: {e}")
            QtWidgets.QMessageBox.warning(self, "Invalid Action", str(e))
    
    def start_action_timer(self):
        """Start/reset the 30 second timer."""
        self.timer_seconds = 30
        self.action_timer.stop()
        self.action_timer.start(1000)  # Update every second
        self.update_timer_display()
    
    def update_timer_display(self):
        """Update timer label."""
        if self.timer_label:
            self.timer_label.setText(f"{self.timer_seconds}s")
            if self.timer_seconds <= 5:
                self.timer_label.setStyleSheet("""
                    font-size: 18px;
                    font-weight: bold;
                    color: #e74c3c;
                    padding: 5px 15px;
                    background-color: #fadbd8;
                    border-radius: 5px;
                """)
            else:
                self.timer_label.setStyleSheet("""
                    font-size: 18px;
                    font-weight: bold;
                    color: #e74c3c;
                    padding: 5px 15px;
                    background-color: #ecf0f1;
                    border-radius: 5px;
                """)
    
    @QtCore.Slot()
    def on_timer_timeout(self):
        """Handle timer timeout."""
        try:
            logger.info("Timer timeout tick")
            actor = self.engine.current_actor()
            if actor is None:
                self.action_timer.stop()
                return
            
            # Only count down for human player
            if actor.kind == "player" and actor.id == self.human_player_index:
                self.timer_seconds -= 1
                self.update_timer_display()
                
                if self.timer_seconds <= 0:
                    # Time's up - take first legal action
                    legal = self.engine.legal_actions()
                    if legal:
                        # Auto-select first action
                        self.engine.step(legal[0])
                        self.update_from_engine()
                        self.start_action_timer()
                    else:
                        # No legal actions - should not happen
                        self.action_timer.stop()
            else:
                # For other players, take action immediately (no timer)
                self.take_random_action()
        except Exception as e:
            print(f"Error in timer timeout: {e}")
            self.action_timer.stop()
    
    def take_random_action(self):
        """Take a random legal action for non-human players."""
        try:
            actor = self.engine.current_actor()
            if actor is None:
                return
            
            legal = self.engine.legal_actions()
            if not legal:
                try:
                    self.engine._run_to_next_decision()
                    self.update_from_engine()
                    self.start_action_timer()
                except Exception as e:
                    print(f"Error running to next decision: {e}")
                return
            
            # Choose random action
            action = random.choice(legal)
            logger.debug(f"Random action for {actor.kind} {actor.id}: {action}")
            
            self.engine.step(action)
            self.update_from_engine()
            self.start_action_timer()
        except Exception as e:
            print(f"Error taking random action: {e}")
            # Try to advance anyway
            try:
                self.engine._run_to_next_decision()
                self.update_from_engine()
                self.start_action_timer()
            except Exception as e2:
                print(f"Error in fallback advance: {e2}")
    
    def show_game_over(self):
        """Show game over dialog."""
        snapshot = self.engine.snapshot()
        logger.debug(f"Game over snapshot: {snapshot}")
        msg = "Hand Complete!\n\nFinal Results:\n"
        for i, player_info in enumerate(snapshot["players"]):
            msg += f"{player_info['name']}: €{player_info['bankroll']/100:.2f} ({player_info['tricks_won']} tricks)\n"
        
        msg += f"\nNext Pot: €{snapshot['pot']/100:.2f}"
        
        reply = QtWidgets.QMessageBox.question(
            self, "Game Over", msg,
            QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel,
            QtWidgets.QMessageBox.StandardButton.Ok
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Ok:
            self.close()
