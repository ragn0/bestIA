from .deck import Deck, Card, compare_cards, RANK_STRENGTH
from dataclasses import dataclass, field
from typing import Optional, Literal, List, Dict, Any
from enum import Enum
import random


# Backward compatibility constants
DEAL, CAMBI, BUCHI, GIOCO, DIVISIONE, FINE = range(6)


class Phase(Enum):
    """Game phases as state machine states."""
    DEAL_DECIDE = "deal_decide"  # Deal 3 to one player, wait for Keep/Fold
    CAMBI = "cambi"  # Card exchange phase (0/1/2 swaps)
    BUCHI_ENTRY = "buchi_entry"  # Discarders can take Buco or pass
    BUCHI_DISCARD = "buchi_discard"  # Buco player discards 1 of 4 cards
    PLAY = "play"  # 3 tricks phase
    SETTLE = "settle"  # Settlement and pot distribution
    FINE = "fine"  # Hand complete


ActorType = Literal["player", "buco"]


@dataclass(frozen=True)
class Actor:
    """Represents who must act next."""
    kind: ActorType
    id: int  # Player index or Buco index


@dataclass(frozen=True)
class Action:
    """Action that can be taken by an actor."""
    kind: str
    payload: Dict[str, Any] = field(default_factory=dict)


class Player:
    def __init__(self, name: str, bankroll: int = 50):
        self.name = name
        self.cards: List[Card] = []
        self.bankroll = bankroll
        self.is_playing = False  # Kept their cards
        self.in_buco = False
        self.tricks_won = 0

    def remove_card(self, card: Card):
        if card in self.cards:
            self.cards.remove(card)
        else:
            raise ValueError(f"Card {card} not found in player {self.name}'s cards")

    def get_cards(self) -> List[Card]:
        return self.cards.copy()


class Buco:
    """Represents a Buco/Bambino entity (can be società)."""
    def __init__(self, players: List[Player], buco_id: int):
        self.players = players
        self.cards: List[Card] = []
        self.buco_id = buco_id
        self.tricks_won = 0
        self.discard_pending = False  # True when waiting for discard decision

    def add_card(self, card: Card):
        self.cards.append(card)


class GameState:
    """Internal game state (not directly exposed to GUI)."""
    def __init__(self, deck: Deck, players: List[Player], pot: int = 0, dealer: int = 0):
        self.deck = deck
        self.players = players
        self.n_players = len(players)
        self.pot = pot
        self.dealer = dealer
        self.briscola_card: Optional[Card] = None  # "carta in mezzo"
        self.briscola_suit: Optional[str] = None
        
        self.playing_players: List[Player] = []  # Players who kept
        self.buchi: List[Buco] = []
        self.tricks: List[List[tuple]] = []  # Each trick is list of (actor, card)
        self.current_trick: List[tuple] = []
        self.trick_lead_suit: Optional[str] = None
        self.trick_winner: Optional[tuple] = None  # (Actor, card)
        
        # Deal tracking
        self.dealt_to: List[int] = []  # Player indices who received cards
        self.decisions: Dict[int, bool] = {}  # Player index -> kept (True) or folded (False)
        
        # Cambi tracking
        self.cambi_done: List[int] = []  # Player indices who already changed their cards
        
        # Buco tracking
        self.buchi_entry_done: List[int] = []  # Player indices who decided on buco entry
        self.next_buco_id = 0


class Engine:
    """
    Deterministic state machine engine for Bestia game.
    Implements run-to-next-decision: after step(), automatically advances
    through automatic transitions until next player decision is required.
    """
    
    def __init__(self, players: List[Player], pot: int = 0, dealer: int = 0, seed: Optional[int] = None):
        self.rng = random.Random(seed) if seed is not None else random
        deck = Deck(seed=seed if seed is not None else None)
        deck.shuffle()
        
        self.gs = GameState(deck, players, pot, dealer)
        self.phase = Phase.DEAL_DECIDE
        self._current_actor: Optional[Actor] = None
        
        # Initialize: draw briscola card
        self.gs.briscola_card = self.gs.deck.draw()
        self.gs.briscola_suit = self.gs.briscola_card.seed
        
        # Start first decision
        self._run_to_next_decision()
    
    def current_actor(self) -> Optional[Actor]:
        """Return the actor who must act next, or None if no decision needed."""
        return self._current_actor
    
    def legal_actions(self) -> List[Action]:
        """Return list of legal actions for current actor."""
        if self._current_actor is None:
            return []
        
        actor = self._current_actor
        
        if self.phase == Phase.DEAL_DECIDE:
            if actor.kind == "player":
                return [
                    Action("keep", {}),
                    Action("fold", {})
                ]
        
        elif self.phase == Phase.CAMBI:
            if actor.kind == "player":
                player = self.gs.players[actor.id]
                actions = [Action("servito", {})]  # Change 0 cards
                # Change 1 card
                for i in range(3):
                    actions.append(Action("change_card", {"index": i}))
                # Change 2 cards
                for i in range(3):
                    for j in range(i + 1, 3):
                        actions.append(Action("change_cards", {"indices": [i, j]}))
                return actions
        
        elif self.phase == Phase.BUCHI_ENTRY:
            if actor.kind == "player":
                player = self.gs.players[actor.id]
                if not player.is_playing:  # Only discarders can take buco
                    return [
                        Action("take_buco", {}),
                        Action("pass", {})
                    ]
        
        elif self.phase == Phase.BUCHI_DISCARD:
            if actor.kind == "buco":
                buco = self.gs.buchi[actor.id]
                if len(buco.cards) == 4:
                    # Discard one of the 4 cards
                    return [
                        Action("discard", {"card_index": i})
                        for i in range(4)
                    ]
        
        elif self.phase == Phase.PLAY:
            if actor.kind == "player":
                player = self.gs.players[actor.id]
                return self._legal_play_actions(player)
            elif actor.kind == "buco":
                buco = self.gs.buchi[actor.id]
                # Buco plays like a player (use first player in buco for card access)
                if buco.players:
                    return self._legal_play_actions_for_cards(buco.cards, buco.players[0])
        
        elif self.phase == Phase.SETTLE:
            return []  # Automatic
        
        return []
    
    def _legal_play_actions(self, player: Player) -> List[Action]:
        """Get legal play actions for a player, considering palo/briscola/ammazzare rules."""
        return self._legal_play_actions_for_cards(player.cards, player)
    
    def _legal_play_actions_for_cards(self, cards: List[Card], player: Player) -> List[Action]:
        """Helper to get legal actions given a hand of cards."""
        if not cards:
            return []
        
        # If leading the trick
        if len(self.gs.current_trick) == 0:
            legal = []
            # Check "di mano" obligations
            must_play = self._get_mandatory_lead(player, cards)
            if must_play:
                return [Action("play_card", {"card": must_play})]
            
            # Can play any card when leading
            for card in cards:
                legal.append(Action("play_card", {"card": card}))
            return legal
        
        # Not leading - must follow rules
        lead_suit = self.gs.trick_lead_suit
        briscola_suit = self.gs.briscola_suit
        
        # Find cards that can be played
        can_play = []
        must_play = []
        
        # Check if can follow suit
        suit_cards = [c for c in cards if c.seed == lead_suit]
        briscola_cards = [c for c in cards if c.seed == briscola_suit]
        
        if suit_cards:
            # Must follow suit
            can_play = suit_cards
        elif briscola_cards:
            # Must play briscola
            can_play = briscola_cards
        else:
            # Can play any card
            can_play = cards
        
        # Now check "ammazzare sempre" - must beat current winner if possible
        if self.gs.trick_winner:
            winning_card = self.gs.trick_winner[1]
            beating_cards = [
                c for c in can_play
                if compare_cards(lead_suit, briscola_suit, c, winning_card) > 0
            ]
            if beating_cards:
                # Must play a card that beats
                must_play = beating_cards
            else:
                must_play = can_play
        else:
            must_play = can_play
        
        return [Action("play_card", {"card": card}) for card in must_play]
    
    def _get_mandatory_lead(self, player: Player, cards: List[Card]) -> Optional[Card]:
        """Check 'di mano' obligations when leading."""
        briscola_suit = self.gs.briscola_suit
        
        # Check if this is the first card of the play phase (di mano)
        # Di mano = first trick of play phase, first card
        is_di_mano = (
            len(self.gs.tricks) == 0 and
            len(self.gs.current_trick) == 0
        )
        
        if not is_di_mano:
            return None
        
        # Rule: If leading (di mano) and you have Asso of Briscola, you must play it
        asso_briscola = next((c for c in cards if c.seed == briscola_suit and c.value == "Asso"), None)
        if asso_briscola:
            return asso_briscola
        
        # Rule: If briscola card in middle is Asso and di mano and you have 3 of briscola, must lead 3
        if self.gs.briscola_card and self.gs.briscola_card.value == "Asso":
            tre_briscola = next((c for c in cards if c.seed == briscola_suit and c.value == "3"), None)
            if tre_briscola:
                return tre_briscola
        
        return None
    
    def step(self, action: Action) -> None:
        """Apply an action and run to next decision point."""
        if self._current_actor is None:
            raise RuntimeError("No current actor - cannot step")
        
        legal = self.legal_actions()
        if action not in legal:
            raise ValueError(f"Action {action} is not legal. Legal actions: {legal}")
        
        # Apply action based on phase
        if self.phase == Phase.DEAL_DECIDE:
            self._step_deal_decide(action)
        elif self.phase == Phase.CAMBI:
            self._step_cambi(action)
        elif self.phase == Phase.BUCHI_ENTRY:
            self._step_buchi_entry(action)
        elif self.phase == Phase.BUCHI_DISCARD:
            self._step_buchi_discard(action)
        elif self.phase == Phase.PLAY:
            self._step_play(action)
        elif self.phase == Phase.SETTLE:
            # Should not happen - settle is automatic
            pass
        
        # Run to next decision
        self._run_to_next_decision()
    
    def _step_deal_decide(self, action: Action):
        """Handle Keep/Fold decision."""
        if action.kind == "keep":
            player_idx = self._current_actor.id
            player = self.gs.players[player_idx]
            player.is_playing = True
            self.gs.playing_players.append(player)
            self.gs.decisions[player_idx] = True
        elif action.kind == "fold":
            player_idx = self._current_actor.id
            self.gs.decisions[player_idx] = False
    
    def _step_cambi(self, action: Action):
        """Handle card exchange."""
        player_idx = self._current_actor.id
        player = self.gs.players[player_idx]
        
        if action.kind == "servito":
            # No change
            pass
        elif action.kind == "change_card":
            idx = action.payload["index"]
            old_card = player.cards[idx]
            player.remove_card(old_card)
            new_card = self.gs.deck.draw()
            player.cards.insert(idx, new_card)
        elif action.kind == "change_cards":
            indices = sorted(action.payload["indices"], reverse=True)  # Remove from high to low
            for idx in indices:
                old_card = player.cards[idx]
                player.remove_card(old_card)
            # Add new cards in order
            for idx in sorted(action.payload["indices"]):
                new_card = self.gs.deck.draw()
                player.cards.insert(idx, new_card)
        
        self.gs.cambi_done.append(player_idx)
    
    def _step_buchi_entry(self, action: Action):
        """Handle Buco entry decision."""
        player_idx = self._current_actor.id
        player = self.gs.players[player_idx]
        
        if action.kind == "take_buco":
            if player.is_playing:
                raise ValueError(f"Player {player.name} already kept cards, cannot take buco")
            
            buco = Buco([player], self.gs.next_buco_id)
            self.gs.next_buco_id += 1
            self.gs.buchi.append(buco)
            player.in_buco = True
            
            # Draw 4 cards for buco
            for _ in range(4):
                buco.add_card(self.gs.deck.draw())
            buco.discard_pending = True
        elif action.kind == "pass":
            pass
        
        self.gs.buchi_entry_done.append(player_idx)
    
    def _step_buchi_discard(self, action: Action):
        """Handle Buco discard (discard 1 of 4 cards)."""
        if action.kind == "discard":
            buco = self.gs.buchi[self._current_actor.id]
            card_idx = action.payload["card_index"]
            discarded = buco.cards.pop(card_idx)
            buco.discard_pending = False
    
    def _step_play(self, action: Action):
        """Handle playing a card in a trick."""
        if action.kind == "play_card":
            card = action.payload["card"]
            
            if self._current_actor.kind == "player":
                player = self.gs.players[self._current_actor.id]
                if card not in player.cards:
                    raise ValueError(f"Player {player.name} does not have card {card}")
                player.remove_card(card)
                self.gs.current_trick.append((self._current_actor, card))
            elif self._current_actor.kind == "buco":
                buco = self.gs.buchi[self._current_actor.id]
                if card not in buco.cards:
                    raise ValueError(f"Buco {self._current_actor.id} does not have card {card}")
                buco.cards.remove(card)
                self.gs.current_trick.append((self._current_actor, card))
            
            # Set lead suit if first card
            if len(self.gs.current_trick) == 1:
                self.gs.trick_lead_suit = card.seed
            
            # Update current winner
            self._update_trick_winner()
    
    def _update_trick_winner(self):
        """Update who is winning the current trick."""
        if not self.gs.current_trick:
            self.gs.trick_winner = None
            return
        
        lead_suit = self.gs.trick_lead_suit
        briscola_suit = self.gs.briscola_suit
        
        winner = self.gs.current_trick[0]
        for actor, card in self.gs.current_trick[1:]:
            if compare_cards(lead_suit, briscola_suit, card, winner[1]) > 0:
                winner = (actor, card)
        
        self.gs.trick_winner = winner
    
    def _run_to_next_decision(self):
        """Run automatic transitions until next player decision is needed."""
        while True:
            if self.phase == Phase.DEAL_DECIDE:
                # Deal to next player who hasn't been dealt
                next_player = self._next_player_to_deal()
                if next_player is not None:
                    # Deal 3 cards
                    player = self.gs.players[next_player]
                    player.cards = [self.gs.deck.draw() for _ in range(3)]
                    self.gs.dealt_to.append(next_player)
                    self._current_actor = Actor("player", next_player)
                    return
                else:
                    # All players dealt and decided, move to CAMBI
                    self.phase = Phase.CAMBI
                    continue
            
            elif self.phase == Phase.CAMBI:
                # Find next player who kept and hasn't done cambi
                next_player = self._next_player_for_cambi()
                if next_player is not None:
                    self._current_actor = Actor("player", next_player)
                    return
                else:
                    # All cambi done, move to BUCHI_ENTRY
                    self.phase = Phase.BUCHI_ENTRY
                    continue
            
            elif self.phase == Phase.BUCHI_ENTRY:
                # Find next discarder who hasn't decided
                next_player = self._next_player_for_buchi_entry()
                if next_player is not None:
                    self._current_actor = Actor("player", next_player)
                    return
                else:
                    # Check if any buco needs discard
                    pending_buco = self._next_buco_for_discard()
                    if pending_buco is not None:
                        self.phase = Phase.BUCHI_DISCARD
                        self._current_actor = Actor("buco", pending_buco)
                        return
                    else:
                        # All buchi resolved, move to PLAY
                        self.phase = Phase.PLAY
                        self._start_play_phase()
                        continue
            
            elif self.phase == Phase.BUCHI_DISCARD:
                # After discard, check if more buchi need discard
                pending_buco = self._next_buco_for_discard()
                if pending_buco is not None:
                    self._current_actor = Actor("buco", pending_buco)
                    return
                else:
                    # All buchi resolved, move to PLAY
                    self.phase = Phase.PLAY
                    self._start_play_phase()
                    continue
            
            elif self.phase == Phase.PLAY:
                # Check if trick is complete
                if len(self.gs.current_trick) == self._num_active_participants():
                    # Resolve trick
                    self._resolve_trick()
                    # Check if all tricks done
                    if len(self.gs.tricks) == 3:
                        self.phase = Phase.SETTLE
                        continue
                    else:
                        # Start next trick
                        self._start_next_trick()
                        continue
                else:
                    # Need next player to play
                    next_actor = self._next_actor_to_play()
                    if next_actor is not None:
                        self._current_actor = next_actor
                        return
                    else:
                        # Should not happen
                        raise RuntimeError("No actor to play but trick not complete")
            
            elif self.phase == Phase.SETTLE:
                # Automatic settlement
                self._settle()
                self.phase = Phase.FINE
                self._current_actor = None
                return
            
            elif self.phase == Phase.FINE:
                self._current_actor = None
                return
    
    def _next_player_to_deal(self) -> Optional[int]:
        # Start from dealer's right, go counter-clockwise
        start_idx = (self.gs.dealer + 1) % self.gs.n_players
        for offset in range(self.gs.n_players):
            idx = (start_idx + offset) % self.gs.n_players
            if idx not in self.gs.dealt_to:
                return idx
        return None
    
    def _next_player_for_cambi(self) -> Optional[int]:
        # Order: first kept player to dealer's right, then counter-clockwise from him
        start_idx = (self.gs.dealer + 1) % self.gs.n_players
        for offset in range(self.gs.n_players):
            idx = (start_idx + offset) % self.gs.n_players
            player = self.gs.players[idx]
            if player.is_playing and idx not in self.gs.cambi_done:
                return idx
        return None
    
    def _next_player_for_buchi_entry(self) -> Optional[int]:
        """Find next discarder who needs to decide on buco entry."""
        start_idx = (self.gs.dealer + 1) % self.gs.n_players
        for offset in range(self.gs.n_players):
            idx = (start_idx + offset) % self.gs.n_players
            player = self.gs.players[idx]
            if not player.is_playing and idx not in self.gs.buchi_entry_done:
                return idx
        return None
    
    def _next_buco_for_discard(self) -> Optional[int]:
        """Find next buco that needs discard decision."""
        for i, buco in enumerate(self.gs.buchi):
            if buco.discard_pending and len(buco.cards) == 4:
                return i
        return None
    
    def _start_play_phase(self):
        """Initialize play phase - determine who leads first trick."""
        # Reset trick state
        self.gs.current_trick = []
        self.gs.trick_lead_suit = None
        self.gs.trick_winner = None
    
    def _start_next_trick(self):
        """Start next trick - winner of previous trick leads."""
        # Reset trick state
        self.gs.current_trick = []
        self.gs.trick_lead_suit = None
        self.gs.trick_winner = None
    
    def _next_actor_to_play(self) -> Optional[Actor]:
        """Get next actor who should play in current trick."""
        if len(self.gs.current_trick) == 0:
            # Leading - determine who leads
            if not self.gs.tricks:
                # First trick of play phase
                if self.gs.buchi:
                    # First buco taken leads (buchi are in order of creation)
                    return Actor("buco", 0)
                else:
                    # First active player to dealer's right
                    start_idx = (self.gs.dealer + 1) % self.gs.n_players
                    for offset in range(self.gs.n_players):
                        idx = (start_idx + offset) % self.gs.n_players
                        player = self.gs.players[idx]
                        if player.is_playing:
                            return Actor("player", idx)
            else:
                # Subsequent trick - previous winner leads
                last_trick = self.gs.tricks[-1]
                winner_actor, _ = self._get_trick_winner(last_trick)
                return winner_actor
        else:
            # Continue counter-clockwise
            last_actor = self.gs.current_trick[-1][0]
            return self._next_actor_ccw(last_actor)
    
    def _next_actor_ccw(self, actor: Actor) -> Optional[Actor]:
        """Get next actor counter-clockwise."""
        # Get all active participants in order
        active_participants = []
        
        # Start from dealer's right, go CCW
        start_idx = (self.gs.dealer + 1) % self.gs.n_players
        for offset in range(self.gs.n_players):
            idx = (start_idx + offset) % self.gs.n_players
            player = self.gs.players[idx]
            
            if player.is_playing:
                active_participants.append(Actor("player", idx))
            elif player.in_buco:
                # Find which buco this player is in
                for buco_idx, buco in enumerate(self.gs.buchi):
                    if player in buco.players:
                        # Only add buco once (if first player in buco)
                        if buco.players[0] == player:
                            active_participants.append(Actor("buco", buco_idx))
                        break
        
        # Find current actor in list
        try:
            current_idx = active_participants.index(actor)
            next_idx = (current_idx + 1) % len(active_participants)
            return active_participants[next_idx]
        except ValueError:
            # Actor not found (shouldn't happen)
            return None
    
    def _num_active_participants(self) -> int:
        """Count active participants (kept players + buchi)."""
        return len(self.gs.playing_players) + len(self.gs.buchi)
    
    def _resolve_trick(self):
        """Resolve current trick and record winner."""
        if not self.gs.current_trick:
            return
        
        winner_actor, winner_card = self.gs.trick_winner
        self.gs.tricks.append(self.gs.current_trick.copy())
        
        # Award trick to winner
        if winner_actor.kind == "player":
            player = self.gs.players[winner_actor.id]
            player.tricks_won += 1
        elif winner_actor.kind == "buco":
            buco = self.gs.buchi[winner_actor.id]
            buco.tricks_won += 1
    
    def _get_trick_winner(self, trick: List[tuple]) -> tuple:
        """Determine winner of a completed trick."""
        if not trick:
            raise ValueError("Empty trick")
        
        lead_suit = trick[0][1].seed
        briscola_suit = self.gs.briscola_suit
        
        winner = trick[0]
        for actor, card in trick[1:]:
            if compare_cards(lead_suit, briscola_suit, card, winner[1]) > 0:
                winner = (actor, card)
        
        return winner
    
    def _settle(self):
        """Handle settlement: pot distribution, bestia payments, dealer fee."""
        participants = self.gs.playing_players + [
            p for buco in self.gs.buchi for p in buco.players
        ]
        participant_tricks = [
            (p, p.tricks_won) for p in self.gs.playing_players
        ] + [
            (buco, buco.tricks_won) for buco in self.gs.buchi
        ]
        
        # Check piatto salvo
        num_participants = len(participant_tricks)
        if num_participants >= 3:
            all_one_trick = all(tricks == 1 for _, tricks in participant_tricks)
            if all_one_trick:
                # Piatto salvo - pot rolls over
                # Still add dealer fee and rotate dealer
                self.gs.pot += 30  # €0.30 = 30 cents
                self.gs.dealer = (self.gs.dealer + 1) % self.gs.n_players
                return
        
        # Normal payout: each trick = 1/3 of pot
        trick_value = self.gs.pot // 3
        for entity, tricks in participant_tricks:
            if isinstance(entity, Player):
                payout = tricks * trick_value
                entity.bankroll += payout
            elif isinstance(entity, Buco):
                # Split among buco players
                payout_per_player = (tricks * trick_value) // len(entity.players)
                for player in entity.players:
                    player.bankroll += payout_per_player
        
        # Bestia payments: 0 tricks = pay pot amount into next pot
        bestia_payments = 0
        for entity, tricks in participant_tricks:
            if tricks == 0:
                if isinstance(entity, Player):
                    entity.bankroll -= self.gs.pot
                    bestia_payments += self.gs.pot
                elif isinstance(entity, Buco):
                    # Split payment among buco players
                    payment_per_player = self.gs.pot // len(entity.players)
                    for player in entity.players:
                        player.bankroll -= payment_per_player
                    bestia_payments += self.gs.pot
        
        # New pot = bestia payments
        self.gs.pot = bestia_payments
        
        # Dealer fee and rotation
        self.gs.pot += 30  # €0.30
        self.gs.dealer = (self.gs.dealer + 1) % self.gs.n_players
    
    def get_player_hand(self, player_id: int) -> List[Card]:
        """Get cards for a specific player (for GUI display)."""
        if player_id < 0 or player_id >= len(self.gs.players):
            raise ValueError(f"Invalid player_id: {player_id}")
        return self.gs.players[player_id].get_cards()
    
    def get_buco_hand(self, buco_id: int) -> List[Card]:
        """Get cards for a specific buco (for GUI display)."""
        if buco_id < 0 or buco_id >= len(self.gs.buchi):
            raise ValueError(f"Invalid buco_id: {buco_id}")
        return self.gs.buchi[buco_id].cards.copy()
    
    def snapshot(self) -> Dict[str, Any]:
        """Return JSON-serializable snapshot of current state for GUI."""
        return {
            "phase": self.phase.value,
            "current_actor": {
                "kind": self._current_actor.kind,
                "id": self._current_actor.id
            } if self._current_actor else None,
            "pot": self.gs.pot,
            "dealer": self.gs.dealer,
            "briscola_card": {
                "seed": self.gs.briscola_card.seed,
                "value": self.gs.briscola_card.value
            } if self.gs.briscola_card else None,
            "briscola_suit": self.gs.briscola_suit,
            "players": [
                {
                    "name": p.name,
                    "bankroll": p.bankroll,
                    "is_playing": p.is_playing,
                    "in_buco": p.in_buco,
                    "tricks_won": p.tricks_won,
                    "num_cards": len(p.cards),
                }
                for p in self.gs.players
            ],
            "buchi": [
                {
                    "buco_id": b.buco_id,
                    "player_names": [p.name for p in b.players],
                    "tricks_won": b.tricks_won,
                    "num_cards": len(b.cards),
                }
                for b in self.gs.buchi
            ],
            "current_trick": [
                {
                    "actor": {"kind": actor.kind, "id": actor.id},
                    "card": {"seed": card.seed, "value": card.value}
                }
                for actor, card in self.gs.current_trick
            ],
            "tricks_completed": len(self.gs.tricks),
        }
