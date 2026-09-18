import sys
import unittest
from pathlib import Path

# Add scripts directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from fun_text_game_base import Game

class TestFunTextGame(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_initial_state(self):
        self.assertEqual(self.game.cur_room, "sanctum")
        self.assertIn("rust_key", [item.id for item in self.game.room().items])

    def test_movement_and_navigation(self):
        # Move North from Sanctum to Northern Grove
        self.game.move("n")
        self.assertEqual(self.game.cur_room, "grove_n")
        # Move South back to Sanctum
        self.game.move("s")
        self.assertEqual(self.game.cur_room, "sanctum")

    def test_item_pickup_and_inventory(self):
        # Pick up rusty key from Sanctum
        room = self.game.room()
        key_item = next((it for it in room.items if it.id == "rust_key"), None)
        self.assertIsNotNone(key_item)
        self.game.player.add_item(key_item)
        self.assertIn("rust_key", self.game.player.inv)

    def test_locked_gate_mechanic(self):
        # Move East to gate
        self.game.move("e")
        self.assertEqual(self.game.cur_room, "gate")
        
        # Without key, moving East should stay at gate
        self.game.move("e")
        self.assertEqual(self.game.cur_room, "gate")

        # Give key and move East -> should reach path
        sanctum = self.game.world.get("sanctum")
        key_item = next((it for it in sanctum.items if it.id == "rust_key"), None)
        if key_item:
            self.game.player.add_item(key_item)
        self.game.move("e")
        self.assertEqual(self.game.cur_room, "path")

if __name__ == "__main__":
    unittest.main()
