import random
from typing import Optional

SEEDS = ["Bastoni", "Coppe", "Denari", "Spade"]
VALUES = ["2", "3", "4", "5", "6", "7", "Fante", "Cavallo", "Re", "Asso"]

# Briscola rank order: Asso > 3 > Re > Cavallo > Fante > 7 > 6 > 5 > 4 > 2
RANK_STRENGTH = {
    "Asso": 10,
    "3": 9,
    "Re": 8,
    "Cavallo": 7,
    "Fante": 6,
    "7": 5,
    "6": 4,
    "5": 3,
    "4": 2,
    "2": 1,
}


class Card:
    def __init__(self, seed: str, value: str):
        self.seed = seed
        self.value = value

    def __str__(self):
        return f"{self.value} di {self.seed}"
    
    def __repr__(self):
        return f"Card({self.seed!r}, {self.value!r})"
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.seed == other.seed and self.value == other.value
    
    def __hash__(self):
        return hash((self.seed, self.value))


def compare_cards(trick_lead_suit: Optional[str], briscola_suit: str, card_a: Card, card_b: Card) -> int:
    """
    Compare two cards in the context of a trick.
    Returns: -1 if card_a < card_b, 0 if equal, 1 if card_a > card_b
    
    Rules:
    - Any briscola beats non-briscola
    - Among briscolas, highest rank wins
    - Among non-briscolas of the led suit, highest rank wins
    """
    a_is_briscola = card_a.seed == briscola_suit
    b_is_briscola = card_b.seed == briscola_suit
    
    # Briscola always beats non-briscola
    if a_is_briscola and not b_is_briscola:
        return 1
    if not a_is_briscola and b_is_briscola:
        return -1
    
    # Both briscola or both non-briscola
    if a_is_briscola and b_is_briscola:
        # Compare by rank strength
        strength_a = RANK_STRENGTH[card_a.value]
        strength_b = RANK_STRENGTH[card_b.value]
        if strength_a > strength_b:
            return 1
        elif strength_a < strength_b:
            return -1
        else:
            return 0
    
    # Both non-briscola - must be same suit to compare
    if trick_lead_suit is None:
        # No lead suit yet, can't compare meaningfully
        return 0
    
    if card_a.seed != trick_lead_suit or card_b.seed != trick_lead_suit:
        # Cards not of led suit - shouldn't happen in valid play
        return 0
    
    # Both of led suit, compare by rank
    strength_a = RANK_STRENGTH[card_a.value]
    strength_b = RANK_STRENGTH[card_b.value]
    if strength_a > strength_b:
        return 1
    elif strength_a < strength_b:
        return -1
    else:
        return 0


def get_card_strength(card: Card, briscola_suit: str) -> int:
    """Get absolute strength of a card (for sorting/ordering purposes)."""
    base_strength = RANK_STRENGTH[card.value]
    if card.seed == briscola_suit:
        return base_strength + 100  # Briscolas are always stronger
    return base_strength


class Deck:
    def __init__(self, seed: Optional[int] = None):
        self.cards = [Card(seed, value) for seed in SEEDS for value in VALUES]
        self._rng = random.Random(seed) if seed is not None else random
    
    def shuffle(self):
        self._rng.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            raise RuntimeError("Cannot draw from empty deck")
        return self.cards.pop()
    
    def __len__(self):
        return len(self.cards)
    
    def __getitem__(self, index):
        return self.cards[index]
    
    def __setitem__(self, index, value):
        self.cards[index] = value
