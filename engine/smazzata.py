from .deck import Deck, Card
from dataclasses import dataclass
from typing import Optional, Literal

ActorType = Literal["player", "buco"]
DEAL, CAMBI, BUCHI, GIOCO, DIVISIONE, FINE = range(6)

class Player:
    def __init__(self, name: str, bankroll: int = 50):
        self.name = name
        self.cards = []
        self.bankroll = bankroll
        
        self.is_playing = False
        self.in_buco = False

    def remove_card(self, card: Card):
        if card in self.cards:
            self.cards.remove(card)
        else:
            raise ValueError(f"Card {card} not found in player {self.name}'s cards")

    def get_cards(self) -> list[Card]:
        return self.cards

class Buco:
    def __init__(self, players: list[Player]):
        self.players = players
        self.cards = []

    def add_card(self, card: Card):
        self.cards.append(card)

@dataclass(frozen=True)
class Actor: 
    kind: ActorType
    id: int
@dataclass(frozen=True)
class Action: 
    kind: str # e.g., "play_card", "fold", etc. 
    payload: dict | None = None


class GameState:
    def __init__(self, deck: Deck, players: list[Player], pot: int = 0):
        self.deck = deck
        self.players = players
        self.n_players = len(players)
        self.state = DEAL
        self.current_player = 0
        self.pot = pot
        self.briscola = self.deck.draw()

        self.playing_players = []
        self.buchi = []
        self.winners = []
        
    def set_state(self, state: int):
        self.state = state
        return self

    def get_state(self) -> int:
        return self.state

    def get_current_player(self) -> int:
        return self.current_player

    def get_playing_players(self) -> list[Player]:
        return self.playing_players
    
    def get_buchi(self) -> list[Buco]:
        return self.buchi

    def play(self, player: Player):
        self.playing_players.append(player)

    def add_buchi(self, buco: Buco):
        self.buchi.append(buco)

    def get_winners(self) -> list[Player]:
        return self.winners

    def get_briscola(self) -> Card:
        return self.briscola
    
    def get_deck(self) -> Deck:
        return self.deck

class Engine:
    def __init__(self, gs: GameState):
        self.gs = gs
        self.dealt = []
        self.current_actor: Optional[Actor]
        self.played_cards = []
        
    def legal_actions(self):
        if self.gs.state == DEAL:
            return ["play", "fold"]
        elif self.gs.state == CAMBI:
            return ["change_x_cards", "servito"]
        elif self.gs.state == BUCHI:
            return ["declare_buco", "pass"]
        elif self.gs.state == GIOCO:
            return ["play_card"]
        elif self.gs.state == DIVISIONE:
            return ["divide_pot"]
        elif self.gs.state == FINE:
            return ["end_game"]
        else:
            return []

    def step(self, action: str, **kwargs):
        if action not in self.legal_actions():
            raise ValueError(f"Action {action} is not legal in state {self.gs.state}")
        if self.gs.state == DEAL:
            self._step_deal_decide(action)
        elif self.gs.state == CAMBI:
            self._step_cambi(action, **kwargs)
        elif self.gs.state == BUCHI:
            self._step_buchi(action, **kwargs)
        elif self.gs.state == GIOCO:
            self._step_gioco(action, **kwargs)
        elif self.gs.state == DIVISIONE:
            self._step_divisione(action, **kwargs)
        else:
            raise RuntimeError("Unknown phase")
        
        # Function for dealing with actions that don't require player input
        self._run_next_decision()
    
    def _run_next_decision(self):
        while True:
            if self.gs.state == DEAL:
                pid = self.gs.get_current_player()

                if pid not in self.dealt:
                    self.gs.players[pid].cards = [self.gs.deck.draw() for _ in range(3)]
                    self.dealt.append(pid)
                self.current_actor = Actor("player", pid)
                return
            if self.phase == PLAY:
                # Resolve grab and continue loop
                if len(self.played_cards) == self.gs.n_players:
                    self._resolve_play()
                    continue
                # Else wait for player input
                self.current_actor = Actor("player", self.gs.get_current_player())
                return
        # Continue... TODO

    def next_phase(self):
        if self.gs.state < FINE:
            self.gs.set_state(self.gs.state + 1)
        else:
            self.gs.set_state(DEAL)
        return self.gs.get_state()
    def next_player(self):
        self.gs.current_player = (self.gs.current_player + 1) % self.gs.n_players
        return self.gs.current_player

