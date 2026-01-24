import random

SEEDS = ["Bastoni", "Coppe", "Denari", "Spade"]
VALUES = ["Asso", "2", "3", "4", "5", "6", "7", "Fante", "Cavallo", "Re"]

class Card:
    def __init__(self, seed, value):
        self.seed = seed
        self.value = value

    def __str__(self):
        return f"{self.value} di {self.seed}"

class Deck:
    def __init__(self):
        self.cards = [Card(seed, value) for seed in SEEDS for value in VALUES]
    
    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()
    
    def __len__(self):
        return len(self.cards)
    
    def __getitem__(self, index):
        return self.cards[index]
    
    def __setitem__(self, index, value):
        self.cards[index] = value