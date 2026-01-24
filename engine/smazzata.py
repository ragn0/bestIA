import deck

DEAL, CAMBI, BUCHI, GIOCO, DIVISIONE = range(5)

class Player:
    def __init__(self, name: str, bankroll: int = 50):
        self.name = name
        self.cards = []
        self.bankroll = bankroll
        self.buchi = []
        self.winners = []
        self.score = 0
        self.is_playing = False
        self.in_buco = False
    def add_card(self, card: deck.Card):
        self.cards.append(card)

    def remove_card(self, card: deck.Card):
        if card in self.cards:
            self.cards.remove(card)
        else:
            raise ValueError(f"Card {card} not found in player {self.name}'s cards")

    def get_cards(self) -> list[deck.Card]:
        return self.cards

class Buco:
    def __init__(self, players: list[Player]):
        self.players = players
        self.cards = []

    def add_card(self, card: deck.Card):
        self.cards.append(card)

class GameState:
    def __init__(self, deck: deck.Deck, players: list[Player]):
        self.deck = deck
        self.players = players
        self.state = DEAL
        self.current_player = 0

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
    
    def get_buchi(self) -> list[Player]:
        return self.buchi

    def play(self, player: Player):
        self.playing_players.append(player)

    def add_buchi(self, buco: Buco):
        self.buchi.append(buco)

    def get_winners(self) -> list[Player]:
        return self.winners
    
    def get_deck(self) -> deck.Deck:
        return self.deck
