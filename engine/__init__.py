"""BestIA game engine - deterministic state machine for Bestia card game."""
from .deck import Card, Deck, RANK_STRENGTH, compare_cards
from .smazzata import (
    Engine,
    Player,
    Buco,
    Actor,
    Action,
    Phase,
    GameState,
)

__all__ = [
    "Card",
    "Deck",
    "RANK_STRENGTH",
    "compare_cards",
    "Engine",
    "Player",
    "Buco",
    "Actor",
    "Action",
    "Phase",
    "GameState",
]
