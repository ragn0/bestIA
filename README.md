# Bestia (Local Variant) — Rules Specification

This repository models a local Italian gambling card game commonly known as **Bestia**.  
For the record, the model will be called **bestIA**, because I'm a genius (in italian, IA is Intelligenza Artificiale, the translation of AI).
Because the game has many regional variants, this project **fixes a single, precise rule set** (the one used locally by the author) to enable reproducible simulation, self-play reinforcement learning, and ISMCTS evaluation.

> Note: Italian terms are intentionally preserved (e.g., **Bestia**, **Buco/Bambino**, **Briscola**, **piatto**, **presa**) because the game is italian and we avoid ambiguity across dialectal names.

---

## 1. Components

### 1.1 Deck
- Standard **Italian 40-card deck** (e.g., Napoletane/Piacentine/Siciliane).
- **Suits**: 4 traditional suits.
- **Rank order (high → low)** follows Briscola hierarchy:
  **Asso (Ace) > 3 > Re (King) > Cavallo (Knight) > Fante (Jack) > 7 > 6 > 5 > 4 > 2**.

### 1.2 Players
- **3 to 10 players**.
- Turn direction is **counter-clockwise** (right → left).

### 1.3 Piatto (Pot)
- Each hand (“smazzata”) is associated with a **piatto** (money pot).
- A hand contains exactly **3 prese** (grabs) (each participant plays 3 cards, therefore only 3 prese can be done), so the default unit is:
  - **1 grab = 1/3 of the pot**, **2 grabs = 2/3**, **3 grabs = all** (unless “piatto salvo” applies; see below).

---

## 2. Setup and Dealer Procedure

### 2.1 Cutting the deck
- The dealer must allow the player to the dealer’s **left** to **cut** (“alzare”) the deck.
- If the dealer forgets to allow the cut, it is considered a human mistake and (in live play) the dealer:
  - **adds an amount equal to the current pot into the pot**, and the hand is redealt.

> In simulation and ML training, this “human mistake” will not be considered because machines don't do those silly mistakes, other rules like that apply, but they all introduce human fallacy. 

### 2.2 Briscola (Trump suit)
Before dealing to players, the dealer reveals the **top card** of the deck and places it face-up at the center of the table (“carta in mezzo”):
- The suit of this card is the **Briscola suit** for the whole hand.
- The card remains **visible** for the entire hand.

---

## 3. Hand Structure (Smazzata)

A **smazzata** consists of:
1. **Selection phase** (who wants to play the hand with the cards they're dealt, and who throws them away)
2. **Card exchange** (limited swaps for those who keep their initial hand)
3. **Buco/Bambino phase** (optional entry for those who discarded)
4. **Play phase** (3 grabs)
5. **Settlement** (pot distribution + Bestia payments)

All actions follow counter-clockwise order unless stated otherwise.

---

## 4. Selection Phase: Keep or Discard

### 4.1 Initial deal
- Each player receives **3 cards**.

### 4.2 Keep vs Discard decision
After viewing:
- their 3 cards, and
- the **Briscola suit** shown by the “carta in mezzo”,

each player decides:
- **Keep**: keep the 3 cards and enter the hand; or
- **Discard**: throw away all 3 cards into the middle and remain out of the hand *until* they have the chance to take a **buco**.

### 4.3 Players who fully stay out
If a player **discards** and later on decides to **not take Buco/Bambino**, they are:
- completely **inactive** for the current hand,
- do not win any share of the pot,
- and cannot be forced into **Bestia** payments.

---

## 5. Exchange Phase (Changing up to 2 cards)

Players who **kept** their 3 cards may change cards:
- Each player who kept the 3 cards may change **0, 1, or 2** cards.
- Exchanges occur in a **fixed order starting from the first player who kept to the dealer’s right**, then continuing counter-clockwise among the players who kept.
- Replacement cards come **from the top of the remaining deck** (the undealt stack), in order.

---

## 6. Buco/Bambino Phase (Optional Entry)

After all exchanges are complete, players who discarded their initial 3 cards may choose to enter via **Buco/Bambino**.

### 6.1 Taking a Buco/Bambino
- A Buco/Bambino consists of drawing **4 cards** from the **top of the remaining deck**.
- The Buco player must **discard 1** of those 4 cards.
- The remaining **3 cards** become the Buco player’s hand for the play phase.

### 6.2 Buco as a full participant
A Buco/Bambino entrant is a **full participant** in the hand:
- They play 3 cards, take grabs, and are forced into Bestia payments if they take 0 grabs.

### 6.3 Multiple Buco
- Multiple Buco/Bambino entrants are allowed (the choice is usually made on how many players are in and how many cards they exchange, and when there are enough cards to do so).

### 6.4 Buco “in società” (shared Buco)
Two or more players may form a **società** and take **one single Buco** together:
- The società jointly becomes one “participant entity” in the hand.
- If the società takes **0 grabs**, the **Bestia payment is split** among the members.
- If the società takes **1+ grabs**, the pot share is **split** among the members.

> For RL/ISMCTS modeling, a società is typically represented as one agent/entity to avoid internal coordination complexity.

### 6.5 Turn priority for Buco
When the play phase begins:
- If there is at least one Buco, the **first Buco taken** plays first.
- After that, play continues counter-clockwise from that point.
- If no Buco exists, play starts from the first active player to the dealer’s right (counter-clockwise order).

---

## 7. Play Phase (3 Grabs)

### 7.1 Core mechanics
- The hand consists of exactly **3 grabs**.
- Each active participant (players who kept + any Buco entities) plays **one card per grab**.

### 7.2 Following suit (palo)
Players must obey strict constraints:

1. **Follow suit**: If you have at least one card of the suit led in the grab, you must play that suit.
   - This applies even if the led suit is the Briscola suit.

2. **Otherwise play Briscola**: If you cannot follow suit, but you have at least one Briscola, you must play a Briscola.

3. **Otherwise** (no led suit, no Briscola): you may play any card.

### 7.3 “Ammazzare sempre” (must overtake when possible)
This variant enforces **ammazzare sempre** (“always kill/overtake”) as a rule:
- If, under the constraints above, you can play a card that **beats** the currently winning card in the grab, you **must** do so.
- Example:
  - Briscola suit is Denari.
  - A player is forced to play Briscola; if they can beat the best Briscola already played, they must, otherwise they play a lower Briscola.

Violating a mandatory rule (e.g., not following suit, not playing Briscola when required, or failing to ammazzare) is an error and (in live play) is penalized by paying the pot.

### 7.4 Grab winner
Grab resolution follows standard **Briscola** rules:
- If at least one Briscola is played in the grab, the highest Briscola wins.
- Otherwise, the highest card of the led suit wins, using the Briscola card game rank order.

---

## 8. “Di mano” tactical obligation (local convention, may vary based on zone/region)

### 8.1 Asso di Briscola when leading
If the player who **leads a grab** (“di mano”, so the player who play first in the entire play phase) holds the **Asso of Briscola**, they are required to play it.

### 8.2 3 of Briscola when the Briscola card-in-the-middle is the Ace
If the visible Briscola card (“carta in mezzo”) is the **Asso** of the Briscola suit, then:
- the player who is **di mano** and holds the **3 of Briscola** must lead with the **3 of Briscola**.

> If the player is not leading (i.e., not di mano), they follow normal constraints (follow suit, Briscola obligation, ammazzare, etc.).  
> After winning a grab, playing a remaining high Briscola is typically optimal but not always enforced (again, this varies based on zone/region) as a strict rule unless explicitly stated above.

---

## 9. Commitments and “Bestia” Payments

### 9.1 Commitment: must take at least one grab
Any participant who enters the play phase (kept players + Buco entities) is committed to taking **at least one grab**.

### 9.2 Bestia
If a participant takes **0 grabs**, they are “in Bestia” and must:
- pay an amount equal to the **current pot** into the pot for the **next hand**.

If multiple participants take 0 grabs, each pays the full pot amount (so the pot can multiply quickly).

---

## 10. Pot Settlement (“Piatto salvo” and payouts)

### 10.1 Normal payout
Unless “piatto salvo” applies:
- Each grab is worth **1/3 of the pot**.
- A participant taking `t` grabs receives `(t/3) * pot`.

### 10.2 Piatto salvo (3+ participants, 1 grab each)
If **3 or more participants** play the hand and **each participant takes exactly 1 grab**, then:
- **the pot is not paid out** (no one takes money),
- the pot **rolls over intact** to the next hand,
- and the next dealer adds the dealer fee on top (see below).
- this also applies to situations when 4 players are in, the grabs are 1-1-1-0, the players who grabbed may agree to not split the pot and keep it intact, doubling the amount of the pot with the payment of the 4th player;

> Optionally, the group may agree on a **threshold** above which the pot *is* paid out even in the 1–1–1 case.

---

## 11. Dealer fee and turn rotation

At the end of each hand:
- The dealer role passes to the player on the dealer’s **right**.
- The new dealer adds **€0.30** to the pot as the “dealer fee” to start the next hand.

---

## 12. “Bestia scesa” (pot reset)

“La Bestia è scesa” means the pot has effectively returned to **0** and the game restarts from the agreed startup mode.

Typical cases:
- A full pot payout occurs (no rollover), and no Bestia payments recreate the pot.
- Or the group explicitly agrees to split a very large pot even in the 1–1–1 case (threshold rule), resetting the pot.

When the pot is reset, the group restarts according to the chosen startup mode (e.g., low/medium/high stakes, giro chiuso vs optional entry).

---

## 13. Notes for Simulation / ML

This project treats the above as the canonical rules for:
- rule-accurate simulation,
- multi-agent RL self-play training,
- ISMCTS evaluation under imperfect information (determinization).

Implementation details such as action legality checks, “ammazzare sempre” enforcement, and the handling of Buco “in società” are specified in code to match this README.

