#!/usr/bin/env python3
"""Demo script that runs one hand of Bestia with random legal actions."""
import random
from engine.smazzata import Engine, Player, Action, Phase
from engine.deck import Card


def print_state(engine: Engine):
    """Print current game state."""
    snapshot = engine.snapshot()
    print(f"\n=== Phase: {snapshot['phase']} ===")
    print(f"Pot: {snapshot['pot']} cents")
    print(f"Dealer: {snapshot['dealer']}")
    if snapshot['briscola_card']:
        print(f"Briscola: {snapshot['briscola_card']['value']} di {snapshot['briscola_card']['seed']}")
    
    if snapshot['current_actor']:
        actor = snapshot['current_actor']
        print(f"Current actor: {actor['kind']} {actor['id']}")
    
    print("\nPlayers:")
    for p in snapshot['players']:
        status = []
        if p['is_playing']:
            status.append("playing")
        if p['in_buco']:
            status.append("in_buco")
        status_str = " (" + ", ".join(status) + ")" if status else ""
        print(f"  {p['name']}: bankroll={p['bankroll']}, tricks={p['tricks_won']}, cards={p['num_cards']}{status_str}")
    
    if snapshot['buchi']:
        print("\nBuchi:")
        for b in snapshot['buchi']:
            print(f"  Buco {b['buco_id']}: players={b['player_names']}, tricks={b['tricks_won']}, cards={b['num_cards']}")
    
    if snapshot['current_trick']:
        print("\nCurrent trick:")
        for play in snapshot['current_trick']:
            actor = play['actor']
            card = play['card']
            print(f"  {actor['kind']} {actor['id']}: {card['value']} di {card['seed']}")
    
    print(f"Tricks completed: {snapshot['tricks_completed']}/3")


def get_random_action(engine: Engine) -> Action:
    """Get a random legal action."""
    legal = engine.legal_actions()
    if not legal:
        return None
    return random.choice(legal)


def print_action(action: Action):
    """Print action in readable format."""
    if action.kind == "keep":
        print("  -> KEEP")
    elif action.kind == "fold":
        print("  -> FOLD")
    elif action.kind == "servito":
        print("  -> SERVITO (no change)")
    elif action.kind == "change_card":
        print(f"  -> CHANGE 1 card (index {action.payload['index']})")
    elif action.kind == "change_cards":
        print(f"  -> CHANGE 2 cards (indices {action.payload['indices']})")
    elif action.kind == "take_buco":
        print("  -> TAKE BUCO")
    elif action.kind == "pass":
        print("  -> PASS")
    elif action.kind == "discard":
        card_idx = action.payload['card_index']
        print(f"  -> DISCARD card at index {card_idx}")
    elif action.kind == "play_card":
        card = action.payload['card']
        print(f"  -> PLAY {card.value} di {card.seed}")
    else:
        print(f"  -> {action.kind} {action.payload}")


def main():
    """Run one hand with random actions."""
    print("=" * 60)
    print("BestIA Engine Demo - One Hand with Random Actions")
    print("=" * 60)
    
    # Create players
    players = [
        Player("Alice", bankroll=1000),
        Player("Bob", bankroll=1000),
        Player("Charlie", bankroll=1000),
    ]
    
    # Create engine
    engine = Engine(players, pot=300, dealer=0, seed=12345)
    
    max_steps = 200  # Safety limit
    step_count = 0
    
    try:
        while engine.phase != Phase.FINE and step_count < max_steps:
            print_state(engine)
            
            actor = engine.current_actor()
            if actor is None:
                print("\nNo actor - engine should advance automatically...")
                # Force one more run
                engine._run_to_next_decision()
                continue
            
            # Show actor's hand if player
            if actor.kind == "player":
                hand = engine.get_player_hand(actor.id)
                print(f"\n{players[actor.id].name}'s hand:")
                for i, card in enumerate(hand):
                    print(f"  [{i}] {card.value} di {card.seed}")
            elif actor.kind == "buco":
                hand = engine.get_buco_hand(actor.id)
                print(f"\nBuco {actor.id}'s hand:")
                for i, card in enumerate(hand):
                    print(f"  [{i}] {card.value} di {card.seed}")
            
            # Get random action
            action = get_random_action(engine)
            if action is None:
                print("No legal actions available!")
                break
            
            print_action(action)
            
            # Apply action
            try:
                engine.step(action)
                step_count += 1
            except Exception as e:
                print(f"ERROR: {e}")
                break
            
            print()
        
        # Final state
        print("\n" + "=" * 60)
        print("FINAL STATE")
        print("=" * 60)
        print_state(engine)
        
        print("\nFinal bankrolls:")
        for p in players:
            print(f"  {p.name}: {p.bankroll} cents")
        print(f"Next pot: {engine.gs.pot} cents")
        print(f"Next dealer: Player {engine.gs.dealer} ({players[engine.gs.dealer].name})")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
