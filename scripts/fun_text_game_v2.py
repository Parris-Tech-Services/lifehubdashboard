# ===========================
# TEXT ADVENTURE V2 - STARSHIP HEIST (Deck Ops)
# ===========================
# A turn-based deck-building run set aboard a drifting corporate cruiser.
# Draft hacking/tech cards, breach three ship sectors, and beat security AIs.
# No walking rooms: just tactical encounters and upgrades between fights.

from __future__ import annotations
from typing import Dict, List, Optional, Set
import random
import json

# ---------- Card System ----------

class Card:
    """A single card with cost, effect, and rarity."""
    def __init__(
        self,
        id: str,
        name: str,
        cost: int,
        effect: str,  # "damage", "block", "draw", "heal", "double", "exhaust"
        value: int,
        rarity: str = "common",  # "common", "rare", "epic"
    ):
        self.id = id
        self.name = name
        self.cost = cost
        self.effect = effect
        self.value = value
        self.rarity = rarity

    def __repr__(self) -> str:
        return f"{self.name}({self.cost})"


class Deck:
    """Player's deck of cards."""
    def __init__(self):
        self.cards: List[Card] = []
        self.draw_pile: List[Card] = []
        self.hand: List[Card] = []
        self.discard_pile: List[Card] = []

    def add_card(self, card: Card) -> None:
        self.cards.append(card)
        self.draw_pile.append(card)

    def remove_card(self, card: Card) -> None:
        if card in self.cards:
            self.cards.remove(card)
        if card in self.draw_pile:
            self.draw_pile.remove(card)

    def shuffle_draw_pile(self) -> None:
        random.shuffle(self.draw_pile)

    def draw(self, count: int = 5) -> None:
        """Draw up to count cards into hand from draw pile."""
        for _ in range(count):
            if not self.draw_pile:
                # Reshuffle discard into draw
                if self.discard_pile:
                    self.draw_pile = self.discard_pile[:]
                    self.discard_pile = []
                    self.shuffle_draw_pile()
                else:
                    break
            if self.draw_pile:
                self.hand.append(self.draw_pile.pop(0))

    def discard_hand(self) -> None:
        """Move entire hand to discard pile."""
        self.discard_pile.extend(self.hand)
        self.hand = []

    def deck_size(self) -> int:
        return len(self.cards)


class Player:
    """Player state for deck roguelike."""
    def __init__(self):
        self.hp: int = 30
        self.max_hp: int = 30
        self.energy: int = 3
        self.max_energy: int = 3
        self.deck = Deck()
        self.run_score: int = 0
        self.zone: int = 1
        self.relics: List[str] = []  # relic IDs

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    def heal(self, amount: int) -> None:
        self.hp = min(self.max_hp, self.hp + amount)

    def gain_energy(self, amount: int) -> None:
        self.energy = min(self.max_energy, self.energy + amount)

    def spend_energy(self, amount: int) -> bool:
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False


class Enemy:
    """A single enemy encounter."""
    def __init__(self, id: str, name: str, hp: int, attacks: List[str]):
        self.id = id
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.attacks = attacks  # ["attack", "defend", "special"]
        self.next_attack_idx = 0

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - amount)

    def get_next_action(self) -> str:
        """Get enemy's next attack pattern."""
        action = self.attacks[self.next_attack_idx % len(self.attacks)]
        self.next_attack_idx += 1
        return action

    def is_alive(self) -> bool:
        return self.hp > 0


# ---------- Card Factory ----------

CARD_CATALOG = {
    # Common cards
    "zap": Card("zap", "Zap", 1, "damage", 6, "common"),
    "shield": Card("shield", "Pulse Shield", 1, "block", 4, "common"),
    "scan": Card("scan", "Packet Scan", 1, "draw", 2, "common"),
    "patch": Card("patch", "Auto-Patch", 2, "heal", 4, "common"),

    # Rare cards
    "overclock": Card("overclock", "Overclock", 2, "double", 1, "rare"),  # buff next hit
    "ion_blast": Card("ion_blast", "Ion Blast", 2, "damage", 12, "rare"),
    "phase_wall": Card("phase_wall", "Phase Wall", 2, "block", 8, "rare"),

    # Epic cards
    "lance": Card("lance", "Plasma Lance", 3, "damage", 20, "epic"),
    "nano_aegis": Card("nano_aegis", "Nano Aegis", 3, "block", 12, "epic"),
    "reboot": Card("reboot", "Reboot", 3, "heal", 8, "epic"),
}

ENEMY_CATALOG = {
    "drone": Enemy("drone", "Sentinel Drone", 15, ["attack", "attack"]),
    "android": Enemy("android", "Boarding Android", 25, ["attack", "defend", "attack"]),
    "turret": Enemy("turret", "Plasma Turret", 30, ["defend", "attack", "attack"]),
    "warden": Enemy("warden", "Core Warden AI", 40, ["attack", "special", "attack"]),
}


# ---------- Game ----------

class Game:
    """Main deck roguelike game."""
    def __init__(self):
        self.player = Player()
        self.deck_pool: Dict[str, Card] = CARD_CATALOG.copy()
        self.enemy_pool: Dict[str, Enemy] = ENEMY_CATALOG.copy()
        self.current_battle: Optional[Battle] = None
        self.run_active: bool = False
        self.run_won: bool = False
        self.run_lost: bool = False
        self.turn_count: int = 0
        self.seed = random.randint(0, 999999)
        self.rng = random.Random(self.seed)

    def say(self, msg: str) -> None:
        print(msg)

    def intro(self) -> None:
        self.say("=== STARSHIP HEIST: DECK OPS ===")
        self.say("You and a crew of two AIs board a drifting corporate cruiser.")
        self.say("Draft hacking tools, breach 3 ship sectors, and outplay security AIs.")
        self.say("Type 'start' to begin a new run.")

    def start_run(self) -> None:
        """Begin a new roguelike run."""
        self.player = Player()
        self.run_active = True
        self.run_won = False
        self.run_lost = False
        self.turn_count = 0
        self.player.zone = 1

        # Start with 3 basic cards
        for _ in range(3):
            self.player.deck.add_card(CARD_CATALOG["zap"])
            self.player.deck.add_card(CARD_CATALOG["shield"])

        self.say("🚀 NEW HEIST RUN STARTED 🚀")
        self.say(f"Seed: {self.seed}")
        self.say(f"Starting deck: {self.player.deck.deck_size()} cards")
        self.say(f"Suit integrity: {self.player.hp}/{self.player.max_hp}")
        self.say("")
        self.say("Commands: start, battle, draft, deck, stats, quit")

    def draft_choice(self, idx: int) -> None:
        """Player picks from 3 random cards to add to deck."""
        if not self.run_active:
            self.say("No active run.")
            return

        # Generate 3 random cards
        options = []
        for _ in range(3):
            rarity = self.rng.choices(
                ["common", "rare", "epic"],
                weights=[60, 30, 10],
                k=1
            )[0]
            card_options = [c for c in self.deck_pool.values() if c.rarity == rarity]
            if card_options:
                options.append(self.rng.choice(card_options))

        if idx < 1 or idx > 3:
            self.say("Choose 1, 2, or 3:")
            for i, c in enumerate(options, 1):
                print(f"  {i}. {c.name} ({c.rarity}) – {c.effect}({c.value}) [{c.cost} energy]")
            return

        choice = options[idx - 1]
        self.player.deck.add_card(choice)
        self.say(f"✓ Added {choice.name} to deck ({choice.rarity})")
        self.say(f"Deck size: {self.player.deck.deck_size()}")

    def show_deck(self) -> None:
        """Display player's current deck."""
        deck = self.player.deck.cards
        if not deck:
            self.say("Deck is empty.")
            return

        # Count by rarity
        by_rarity = {}
        for card in deck:
            by_rarity.setdefault(card.rarity, []).append(card)

        for rarity in ["common", "rare", "epic"]:
            if rarity in by_rarity:
                cards_list = by_rarity[rarity]
                names = [c.name for c in cards_list]
                print(f"[{rarity.upper()}] {', '.join(names)}")

        print(f"\nTotal: {len(deck)} cards")

    def start_battle(self) -> None:
        """Start a battle with a random enemy."""
        if not self.run_active:
            self.say("No active run.")
            return

        # Pick random enemy scaled to zone
        if self.player.zone == 1:
            choices = ["drone", "android"]
        elif self.player.zone == 2:
            choices = ["android", "turret"]
        else:
            choices = ["warden", "turret"]

        enemy_id = self.rng.choice(choices)
        enemy_def = ENEMY_CATALOG[enemy_id]
        enemy = Enemy(enemy_def.id, enemy_def.name, enemy_def.hp, enemy_def.attacks)

        self.current_battle = Battle(self.player, enemy)
        self.say(f"\n⚔️  BATTLE: {enemy.name} (HP: {enemy.hp})")
        self.say(f"Suit integrity: {self.player.hp}/{self.player.max_hp}")
        self.say("")
        self.say("Commands: play [num], end (end turn), quit")

    def handle_battle_turn(self) -> None:
        """Execute one turn of battle."""
        if not self.current_battle:
            self.say("No active battle.")
            return

        battle = self.current_battle
        enemy = battle.enemy

        # Enemy's turn
        action = enemy.get_next_action()
        damage = 0
        if action == "attack":
            damage = self.rng.randint(5, 10)
            self.say(f"{enemy.name} attacks for {damage} damage!")
        elif action == "defend":
            self.say(f"{enemy.name} braces for impact (gain block)")
            battle.enemy_block += 5
        elif action == "special":
            damage = self.rng.randint(8, 15)
            self.say(f"{enemy.name} uses a special attack for {damage} damage!")

        # Apply damage to player
        if damage > 0:
            mitigated = min(damage, battle.player_block)
            actual = damage - mitigated
            battle.player_block = max(0, battle.player_block - damage)
            self.player.take_damage(actual)
            if mitigated > 0:
                self.say(f"  {mitigated} blocked, {actual} damage taken!")
            else:
                self.say(f"  {actual} damage taken!")

        battle.player_block = 0  # Reset block after turn

        # Check battle state
        if self.player.hp <= 0:
            self.say(f"\n💀 DEFEAT! {enemy.name} defeated you.")
            self.run_lost = True
            self.run_active = False
            self.current_battle = None
        elif enemy.hp <= 0:
            self.say(f"\n✨ VICTORY! {enemy.name} defeated.")
            reward = 50 * self.player.zone
            self.player.run_score += reward
            self.say(f"Reward: +{reward} score")
            self.current_battle = None

            # Advance zone every 3 wins
            wins = self.player.run_score // 50
            if wins % 3 == 0 and wins > 0:
                self.player.zone += 1
                self.say(f"🌟 Advanced to Zone {self.player.zone}!")

    def dispatch(self, line: str) -> bool:
        """Parse and execute a command."""
        parts = line.strip().split()
        if not parts:
            return True

        cmd, args = parts[0].lower(), parts[1:]

        # Friendly aliases
        if cmd in ("inventory", "inv", "backpack", "bag", "pack"):
            cmd = "deck"
        if cmd in ("hand", "cards"):
            cmd = "hand"

        if cmd in ("quit", "exit", "q"):
            return False

        if cmd == "help":
            self.say("Commands: start, battle, play [1-5], auto, hand, end, draft, deck/inventory, stats, map, help advanced, quit")
            return True
        if cmd == "help" and args and args[0] == "advanced":
            self.say("Advanced: auto (play first affordable), hand (show current hand), draft [slot], deck, stats, map, tips")
            return True

        if cmd == "tips":
            self.say("Tips: Draft shields early; turrets hit hard. Overclock before big hits. Zone change after 3 wins.")
            return True

        if cmd == "start":
            self.start_run()
            return True

        if cmd == "battle":
            self.start_battle()
            return True

        if cmd == "stats":
            self.say(f"HP: {self.player.hp}/{self.player.max_hp}  Zone: {self.player.zone}  Score: {self.player.run_score}")
            self.say(f"Deck size: {self.player.deck.deck_size()}")
            return True

        if cmd == "hand":
            if not self.current_battle:
                self.say("You need to start a battle first.")
                return True
            hand_list = ", ".join(f"{idx+1}:{card.name}" for idx, card in enumerate(self.current_battle.hand)) or "(empty)"
            self.say(f"Hand: {hand_list}")
            return True

        if cmd == "deck":
            self.show_deck()
            return True

        if cmd == "draft":
            idx = int(args[0]) if args and args[0].isdigit() else 0
            self.draft_choice(idx)
            return True

        if cmd == "auto":
            if not self.current_battle:
                self.say("Start a battle first.")
                return True
            for idx, card in enumerate(self.current_battle.hand):
                if card.cost <= self.current_battle.energy:
                    if self.current_battle.play_card(card, self.player):
                        self.current_battle.hand.pop(idx)
                        self.say(f"Auto-played {card.name}")
                    else:
                        self.say(f"Not enough energy for {card.name}")
                    break
            else:
                self.say("No affordable cards this turn.")
            return True

        if cmd == "map":
            self.say("🗺️  SHIP SECTORS")
            self.say("Zone 1 (Drift Deck): Sentinel Drone, Boarding Android")
            self.say("Zone 2 (Engine Ring): Boarding Android, Plasma Turret")
            self.say("Zone 3 (Core Vault): Core Warden AI, Plasma Turret")
            return True

        if self.current_battle:
            if cmd == "play":
                idx = int(args[0]) - 1 if args and args[0].isdigit() else -1
                if 0 <= idx < len(self.current_battle.hand):
                    card = self.current_battle.hand[idx]
                    if self.current_battle.play_card(card, self.player):
                        self.current_battle.hand.pop(idx)
                        self.say(f"Played {card.name}")
                    else:
                        self.say(f"Not enough energy for {card.name}")
                else:
                    self.say("Invalid card number.")
                return True

            if cmd == "end":
                self.handle_battle_turn()
                if self.current_battle:
                    self.current_battle.display_hand()
                return True

            self.say("In battle. Use 'play [1-5]' or 'end' turn")
            return True

        self.say("Unknown command. Type 'help'")
        return True

    def run(self) -> None:
        """Main game loop."""
        self.say("=== STARSHIP HEIST: DECK OPS ===")
        self.say("Draft hacking tools, breach 3 ship sectors, and outplay security AIs.")
        self.say("Type 'start' to begin a new run.\n")

        while True:
            try:
                if self.current_battle:
                    prompt = f"[Battle {self.current_battle.turn}]> "
                elif self.run_active:
                    prompt = f"[Zone {self.player.zone}]> "
                else:
                    prompt = "> "

                line = input(prompt).strip()
                if not self.dispatch(line):
                    break
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.say(f"Error: {e}")


class Battle:
    """A single battle state."""
    def __init__(self, player: Player, enemy: Enemy):
        self.player = player
        self.enemy = enemy
        self.hand: List[Card] = []
        self.player_block: int = 0
        self.enemy_block: int = 0
        self.turn: int = 1
        self.played_cards: List[Card] = []

        # Start battle: draw 5 cards and reset energy
        self.player.energy = self.player.max_energy
        self.player.deck.draw(5)
        self.hand = self.player.deck.hand[:]

    def play_card(self, card: Card, player: Player) -> bool:
        """Play a card from hand. Return True if successful."""
        if not player.spend_energy(card.cost):
            return False

        # Apply card effect
        if card.effect == "damage":
            self.enemy.take_damage(card.value)
        elif card.effect == "block":
            self.player_block += card.value
        elif card.effect == "draw":
            self.player.deck.draw(card.value)
        elif card.effect == "heal":
            player.heal(card.value)
        elif card.effect == "double":
            # Next attack deals 2x (simplified: just boost next damage by 50%)
            pass  # Would need state tracking for full implementation

        self.played_cards.append(card)
        return True

    def display_hand(self) -> None:
        """Show hand of cards."""
        if not self.hand:
            print("Hand is empty.")
            return
        print(f"\nEnergy: {self.player.energy}/{self.player.max_energy}")
        print("Hand:")
        for i, card in enumerate(self.hand, 1):
            print(f"  {i}. {card.name} – {card.effect}({card.value}) [{card.cost}⚡]")


# ===========================
# RUNNER
# ===========================
if __name__ == "__main__":
    try:
        Game().run()
    except Exception as e:
        print(f"Error: {e}")
