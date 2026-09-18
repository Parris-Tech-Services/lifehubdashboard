# ===========================
# TEXT ADVENTURE - PART 1 (Base Game)
# ===========================
from __future__ import annotations
from typing import Dict, List, Optional
import difflib
import random

# ---------- Data Models ----------

class Item:
    def __init__(self, id: str, name: str, desc: str, usable: bool = False):
        self.id = id
        self.name = name
        self.desc = desc
        self.usable = usable

    def __repr__(self) -> str:
        return f"Item({self.id})"


class Room:
    def __init__(self, id: str, name: str, desc: str):
        self.id = id
        self.name = name
        self.desc = desc
        self.items: List[Item] = []
        self.neighbors: Dict[str, str] = {}
        self.npcs: List[str] = []
        self.tag: Optional[str] = None

    def link(self, direction: str, other_room_id: str) -> None:
        self.neighbors[direction] = other_room_id



CANONICAL_NPCS = {
    "caretaker": {
        "id": "caretaker",
        "name": "Caretaker",
        "role": "Keeper of the Sanctum",
        "personality": "You are cryptic, slightly tired, but ultimately helpful. You speak in short, metaphor-heavy sentences. You know about the rusty key in the Sanctum, and the locked gate to the east.",
        "knowledge": ["The rusty key unlocks the east gate", "The forest lies beyond the gate", "You are the caretaker of this ancient sanctum"]
    },
    "trader": {
        "id": "trader",
        "name": "Trader",
        "role": "Merchant of the Wilds",
        "personality": "You are pragmatic, profit-driven, and straightforward. You crave fresh fish from the lake.",
        "knowledge": ["I buy fresh fish for 5 gold", "I can buy the lost ring for 6 gold", "I have the 'angler_aid' quest"]
    },
    "ranger": {
        "id": "ranger",
        "name": "Ranger",
        "role": "Guardian of the Camp",
        "personality": "You are rugged, watchful, and practical. You need ore to fix buckles and stove-pins.",
        "knowledge": ["I need two lumps of ore to fix things", "I have the 'mine_matters' quest", "The camp is a safe place to rest"]
    },
    "hermit": {
        "id": "hermit",
        "name": "Hermit",
        "role": "Wandering Alchemist",
        "personality": "You are eccentric, wise, and slightly disconnected from reality. You brew salves that need glowcaps.",
        "knowledge": ["I need three glowcaps to make my salve gleam", "I have the 'hermit_glow' quest", "Glowcaps grow in damp places like the mine or cellar"]
    }
}

class Player:
    def __init__(self):
        self.inv: Dict[str, Item] = {}
        self.hp: int = 10
        self.max_hp: int = 10

    def add_item(self, item: Item) -> None:
        self.inv[item.id] = item

    def remove_item(self, item_id: str) -> Optional[Item]:
        return self.inv.pop(item_id, None)


class World:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.start_room: str = ""

    def add_room(self, room: Room) -> None:
        self.rooms[room.id] = room

    def get(self, room_id: str) -> Room:
        return self.rooms[room_id]


# ---------- Game ----------

class Game:
    def __init__(self):
        self.world = World()
        self.player = Player()
        self.rng = random.Random(42)
        self.cur_room: str = ""
        self._built = False
        self._build()
        self._post_init_extensions()
        self._init_positions() # <-- add this

    def _build(self):
        if self._built:
            return
        sanctum = Room("sanctum", "Sanctum", "A quiet stone atrium with mossy pillars.")
        gate = Room("gate", "East Gate", "An iron gate bars the way east. A keyhole glints.")
        path = Room("path", "Forest Path", "A winding path through whispering trees.")
        wilds_stub = Room("wilds_stub", "Overgrown Verge", "Tall grass hints at wilder lands to the east.")
        wilds_stub.tag = "part2_hook"

# --- EXTRA MAP (optional) ---
        grove_n = Room("grove_n", "Northern Grove",
                       "Silver-barked trees and soft leaf litter.")
        cellar_s = Room("cellar_s", "Sunken Cellar",
                        "Damp stone, old crates, and a chill draft.")
        court_w = Room("court_w", "Ruined Courtyard",
                       "Broken statues and a dry fountain.")
        brook_ne = Room("brook_ne", "Brook Crossing",
                        "A shallow brook babbles over smooth stones.")
        thicket_se = Room("thicket_se", "Southern Thicket",
                          "Close-set shrubs tug at your sleeves.")

        # Items/NPCs (optional flavour)
        grove_n.items.append(Item("mint", "Wild Mint", "Smells fresh.", usable=False))
        cellar_s.items.append(Item("torch", "Old Torch", "Might still light.", usable=False))

        # Add to world
        for r in (grove_n, cellar_s, court_w, brook_ne, thicket_se):
            self.world.add_room(r)

# Links
        sanctum.link("n", "grove_n")
        sanctum.link("s", "cellar_s")
        sanctum.link("w", "court_w")
        sanctum.link("e", "gate")

        grove_n.link("s", "sanctum")
        grove_n.link("e", "brook_ne")
        brook_ne.link("w", "grove_n")

        cellar_s.link("n", "sanctum")
        cellar_s.link("e", "thicket_se")
        thicket_se.link("w", "cellar_s")

        court_w.link("e", "sanctum")

        gate.link("w", "sanctum")
        gate.link("e", "path")
        path.link("w", "gate")
        path.link("e", "wilds_stub")
        wilds_stub.link("w", "path")

        key = Item("rust_key", "Rusty Key", "Old key with a jagged bite.", usable=True)
        apple = Item("apple", "Apple", "A crisp, red apple.", usable=True)
        sanctum.items.append(key)
        path.items.append(apple)

        sanctum.npcs.append("Caretaker")

        for r in (sanctum, gate, path, wilds_stub):
            self.world.add_room(r)
        self.world.start_room = "sanctum"
        self.cur_room = self.world.start_room
        self._built = True
        self.active_conversation_npc_id = None
        self.conversation_room = None
        self.conversation_req_id = 0



    def _post_init_extensions(self):
        for fname in ("part2_post_init", "part3_post_init", "part4_post_init", "part5_post_init", "part6_post_init", "part7_post_init"):
            fn = globals().get(fname)
            if callable(fn):
                try:
                    fn(self)
                except Exception as e:
                    print(f"[Ignoring {fname} error] {e}")

    def _init_positions(self):
        """Assign grid coordinates for a visual map. Purely visual; gameplay links still rule."""
        self.pos = {}

        # Core spine (no collisions)
        self.pos["sanctum"] = (0, 0)
        self.pos["gate"] = (1, 0)
        self.pos["path"] = (2, 0)
        self.pos["wilds_stub"] = (3, 0)
        if "wilds" in self.world.rooms:
            self.pos["wilds"] = (4, 0)

        # Optional extra map around Sanctum
        if "grove_n" in self.world.rooms:     self.pos["grove_n"] = (0, -1)
        if "brook_ne" in self.world.rooms:    self.pos["brook_ne"] = (1, -1)
        if "cellar_s" in self.world.rooms:    self.pos["cellar_s"] = (0, 1)
        if "thicket_se" in self.world.rooms:  self.pos["thicket_se"] = (1, 1)
        if "court_w" in self.world.rooms:     self.pos["court_w"] = (-1, 0)

        # Part 7 Wilds expansion (place to avoid overlaps with wilds_stub)
        # Note: wilds_tower links 'w' of wilds; placing it NW avoids a visual overlap with wilds_stub.
        if "wilds_lake" in self.world.rooms: self.pos["wilds_lake"] = (4, -1)  # N of wilds
        if "wilds_mine" in self.world.rooms: self.pos["wilds_mine"] = (5, 0)  # E of wilds
        if "wilds_camp" in self.world.rooms: self.pos["wilds_camp"] = (4, 1)  # S of wilds
        if "wilds_post" in self.world.rooms: self.pos["wilds_post"] = (5, 1)  # E of camp
        if "wilds_tower" in self.world.rooms: self.pos["wilds_tower"] = (3, -1)  # visually W/NW of wilds
        if "wilds_hut" in self.world.rooms: self.pos["wilds_hut"] = (3, 1)  # near camp

        # Mark everything unknown with a fallback (won’t render unless positioned)
        # (Optional) You could auto-pack unknown rooms later if you add more areas.

    def say(self, msg: str) -> None:
        print(msg)

    def room(self) -> Room:
        return self.world.get(self.cur_room)

    def move(self, d: str) -> None:
        d = d.lower()
        aliases = {"north": "n", "south": "s", "east": "e", "west": "w"}
        d = aliases.get(d, d)
        if d not in ("n", "s", "e", "w"):
            self.say("Use: move n/s/e/w")
            return
        r = self.room()
        if d not in r.neighbors:
            self.say("You can't go that way.")
            return
        if r.id == "gate" and d == "e" and "rust_key" not in self.player.inv:
            self.say("The gate is locked. A keyhole awaits a fitting key.")
            return
            
        nxt = r.neighbors[d]
        if getattr(self, "active_conversation_npc_id", None):
            self.say(f"Your conversation with the {self.active_conversation_npc_id} ends.")
            self._end_conversation()
            
        self.cur_room = nxt
        self.look()

    def look(self) -> None:
        r = self.room()
        if not hasattr(r, "seen"):
            r.seen = True
        r.seen = True
        self.say(f"{r.name}\n{r.desc}")
        if r.items:
            self.say("Items here: " + ", ".join(i.name for i in r.items))
        if r.npcs:
            self.say("You see: " + ", ".join(r.npcs))
        exits = ", ".join(sorted(r.neighbors.keys()))
        self.say(f"Exits: {exits if exits else 'none'}")

 #   def map(self) -> None:
 #       here = self.room().name
 #       self.say(f"[Map] You are at: {here}. West: Sanctum. East: Woods.")

    def map(self) -> None:
        """Draw an ASCII tile map with @ for current position, · for visited/known tiles."""
        if not hasattr(self, "pos") or not self.pos:
            self.say("[Map] No layout yet.")
            return

        # Build reverse index of (x,y) -> room_id(s)
        grid = {}
        for rid, xy in self.pos.items():
            grid.setdefault(tuple(xy), []).append(rid)

        # Compute bounds from positioned rooms
        xs = [x for (x, y) in grid.keys()]
        ys = [y for (x, y) in grid.keys()]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)

        # Track “seen” rooms (visited at least once)
        # Mark current room as seen
        for r in self.world.rooms.values():
            if not hasattr(r, "seen"):
                r.seen = False
        self.world.get(self.cur_room).seen = True

        # Render
        lines = []
        for y in range(ymin, ymax + 1):
            row = []
            for x in range(xmin, xmax + 1):
                rids = grid.get((x, y), [])
                if not rids:
                    row.append("   ")  # empty tile
                    continue
                # If multiple rooms share a tile, prefer to show the current room if here.
                here_symbol = None
                if self.cur_room in rids:
                    here_symbol = "@"
                else:
                    # show · if any of these rooms have been seen
                    seen_any = any(self.world.rooms[rid].seen for rid in rids if rid in self.world.rooms)
                    here_symbol = "·" if seen_any else "?"

                row.append(f" {here_symbol} ")
            lines.append("".join(row))

        # Add a header and legend
        border = "+" + "-" * (3 * (xmax - xmin + 1)) + "+"
        self.say(border)
        for line in lines:
            self.say("|" + line + "|")
        self.say(border)
        self.say(f"You are at: {self.room().name}")
        self.say("Legend: @ you, · visited, ? known (unvisited), blank = off-map")

    def _end_conversation(self):
        if getattr(self, "active_conversation_npc_id", None):
            self.active_conversation_npc_id = None
            self.conversation_room = None
            self.conversation_req_id = getattr(self, "conversation_req_id", 0) + 1

    def _process_dialogue_command(self, cmd: str, args: list, line: str) -> None:
        room = self.room()
        npcs_here = list(getattr(room, "npcs", []))
        
        def find_npc(name: str):
            if not name: return None
            name = name.lower()
            for n in npcs_here:
                if name == n.lower() or name in n.lower() or n.lower() in name:
                    return n
            return None

        # Validate active conversation
        if getattr(self, "active_conversation_npc_id", None):
            if getattr(self, "conversation_room", None) != self.cur_room or not find_npc(self.active_conversation_npc_id):
                self._end_conversation()

        if cmd in ("talk", "hello", "hi", "greet", "greetings"):
            target_str = " ".join(args).lower().strip()
            if target_str.startswith("to "): target_str = target_str[3:]
            
            active_npc = getattr(self, "active_conversation_npc_id", None)
            
            # If greeting while already in a conversation with someone
            if cmd in ("hello", "hi", "greet", "greetings") and active_npc:
                # If target is specified and it's someone else, switch. Otherwise treat as speech.
                if target_str and find_npc(target_str) and find_npc(target_str) != active_npc:
                    pass # let it fall through to NPC switch logic below
                else:
                    self._emit_dialogue_request(active_npc, line)
                    return
            
            if not npcs_here:
                if cmd in ("hello", "hi", "greet", "greetings"):
                    self.say("There's nobody here to greet.")
                else:
                    self.say("There is no one here to talk to.")
                return
                
            actual_npc = None
            if not target_str:
                if len(npcs_here) == 1:
                    actual_npc = npcs_here[0]
                else:
                    verb = "greet" if cmd in ("hello", "hi", "greet", "greetings") else "talk to"
                    self.say(f"Who do you want to {verb}? " + ", ".join(npcs_here))
                    return
            else:
                actual_npc = find_npc(target_str)
                if not actual_npc:
                    verb = "greet" if cmd in ("hello", "hi", "greet", "greetings") else "talk to"
                    self.say(f"There is no one named '{target_str}' here to {verb}.")
                    return
            
            if active_npc == actual_npc:
                if cmd == "talk":
                    self.say(f"You're already talking with the {actual_npc}.")
                else:
                    self._emit_dialogue_request(actual_npc, line)
                return
            
            if active_npc and active_npc != actual_npc:
                self.say(f"You end your conversation with the {active_npc} and turn to the {actual_npc}.")
                self._end_conversation()
            else:
                self.say(f"You begin talking with the {actual_npc}.")
                
            self.active_conversation_npc_id = actual_npc
            self.conversation_room = self.cur_room
            self.conversation_req_id = getattr(self, "conversation_req_id", 0) + 1
            
            if cmd in ("hello", "hi", "greet", "greetings"):
                self._emit_dialogue_request(actual_npc, line)
            
        elif cmd == "say":
            if not getattr(self, "active_conversation_npc_id", None):
                self.say("You're not currently talking to anyone.")
                return
            actual_npc = find_npc(self.active_conversation_npc_id)
            if not actual_npc:
                self.say("They are no longer here.")
                self.active_conversation_npc_id = None
                return
            msg = " ".join(args)
            if not msg:
                self.say("Say what?")
                return
            self._emit_dialogue_request(actual_npc, msg)
            
        elif cmd == "ask":
            if not args:
                self.say("Ask who what?")
                return
            actual_npc = find_npc(args[0])
            if not actual_npc:
                self.say(f"There is no one named '{args[0]}' here to ask.")
                return
            msg = " ".join(args[1:])
            if not msg:
                self.say("Ask them what?")
                return
            self._emit_dialogue_request(actual_npc, msg)

    def _emit_dialogue_request(self, actual_npc: str, msg: str) -> None:
        room = self.room()
        npc_id = actual_npc.lower().replace(" ", "_")
        canonical = globals().get("CANONICAL_NPCS", {}).get(npc_id, {})
        
        self.conversation_req_id = getattr(self, "conversation_req_id", 0) + 1
        
        context = {
            "valid": True,
            "reqId": self.conversation_req_id,
            "npcId": npc_id,
            "npcName": actual_npc,
            "roomId": self.cur_room,
            "playerLocation": room.name,
            "npcsPresent": list(getattr(room, "npcs", [])),
            "promptText": msg,
            "npcLore": canonical.get("personality", ""),
            "npcKnowledge": canonical.get("knowledge", []),
            "worldContext": {
                "room_desc": room.desc,
                "inventory": [it.name for it in self.player.inv.values()],
                "hp": getattr(self.player, "hp", 10),
                "max_hp": getattr(self.player, "max_hp", 10)
            },
            "error": None
        }
        self.lifehub_dialogue_pending = context


    def take(self, name: str) -> None:
        r = self.room()
        wanted = self._normalize_item_query(name)
        for i, it in enumerate(r.items):
            if self._item_matches_query(it, wanted):
                self.player.add_item(it)
                r.items.pop(i)
                self.say(f"You take the {it.name}.")
                return
        self.say("No such item here.")

    def drop(self, name: str) -> None:
        wanted = self._normalize_item_query(name)
        it = None
        for k in list(self.player.inv.keys()):
            item = self.player.inv[k]
            if self._item_matches_query(item, wanted):
                it = self.player.remove_item(k)
                break
        if it:
            self.room().items.append(it)
            self.say(f"You drop the {it.name}.")
        else:
            self.say("You don't have that.")

    def use(self, name: str) -> None:
        inv = self.player.inv
        wanted = self._normalize_item_query(name)
        target = None
        for it in inv.values():
            if self._item_matches_query(it, wanted):
                target = it
                break
        if not target:
            self.say("You don't have that.")
            return
        if target.id == "rust_key" and self.cur_room == "gate":
            self.say("You turn the key. The gate creaks open eastward.")
        elif target.id == "apple":
            healed = 1 if self.player.hp < self.player.max_hp else 0
            self.player.hp = min(self.player.max_hp, self.player.hp + 1)
            self.say("You eat the apple." + (" (+1 HP)" if healed else ""))
            self.player.remove_item("apple")
        else:
            self.say("You're not sure how to use that.")

    def inv(self) -> None:
        items = list(self.player.inv.values())
        # Part 3 materials (only show ones with qty > 0)
        p3 = getattr(self, "_p3", None)
        mats = {k: v for k, v in (p3.get("mats", {}) if p3 else {}).items() if v > 0}

        if not items and not mats:
            self.say("Inventory: (empty)")
            return

        if items:
            self.say("Inventory: " + ", ".join(it.name for it in items))
        else:
            self.say("Inventory: (no items)")

        if mats:
            self.say("Materials: " + ", ".join(f"{k} x{v}" for k, v in mats.items()))

    # Example inventory printout
    def show_inventory(player):
        if not player.inv:
            print("Inventory empty.")
            return
        items = [f"{name} x{qty}" if qty > 1 else name for name, qty in player.inv.items()]
        print("Inventory: " + ", ".join(items))

    def stats(self) -> None:
        self.say(f"HP: {self.player.hp}/{self.player.max_hp}")

    def _normalize_item_query(self, raw: str) -> str:
        text = " ".join((raw or "").strip().lower().split())
        for prefix in ("the ", "a ", "an ", "my "):
            if text.startswith(prefix):
                text = text[len(prefix):]
        return text

    def _item_matches_query(self, item: Item, wanted: str) -> bool:
        if not wanted:
            return False
        id_l = item.id.lower().replace("_", " ")
        nm_l = item.name.lower()
        if wanted == id_l or wanted == nm_l:
            return True
        if wanted in id_l or wanted in nm_l:
            return True
        wanted_tokens = wanted.split()
        candidate_tokens = (id_l + " " + nm_l).split()
        return all(
            any(tok == cand or cand.startswith(tok) or tok in cand for cand in candidate_tokens)
            for tok in wanted_tokens
        )

    def help(self) -> None:
        self.say(
            "=== Commands ===\n"
            "MOVEMENT: n, s, e, w, move [dir]\n"
            "ACTIONS: take [item], drop [item], use [item], eat [item], inspect [item], equip [item], unequip [slot]\n"
            "DIALOGUE: talk [npc], ask [npc] [question], say [text], goodbye\n"
            "         (While actively talking to someone, normal sentences become dialogue)\n"
            "SURVIVAL: attack, rest, forage, hunt, fish, mine, harvest, cook, camp, craft [item]\n"
            "SHOPPING: buy [item], sell [item]\n"
            "PROGRESSION: quests, journal, bestiary, lore, note [text], notes\n"
            "INFO: look, inv, map, stats, help\n"
            "SYSTEM: save, load, options, quit\n"
        )

    def _suggest_command(self, cmd: str, args: List[str]) -> Optional[str]:
        aliases = {
            "inventory": "inv",
            "invetory": "inv",
            "invenotry": "inv",
            "bag": "inv",
            "backpack": "inv",
            "i": "inv",
            "inspect": "look",
            "l": "look",
            "speak": "talk",
            "talkto": "talk",
            "walk": "move",
            "tak": "take",
        }
        if cmd in aliases:
            target = aliases[cmd]
            return f"{target} {' '.join(args)}".strip()

        known = [
            "help", "look", "move", "go", "take", "drop", "use", "unlock", "open",
            "talk", "inv", "map", "stats", "n", "s", "e", "w",
        ]
        match = difflib.get_close_matches(cmd, known, n=1, cutoff=0.72)
        if match:
            target = match[0]
            return f"{target} {' '.join(args)}".strip()
        return None

    def dispatch(self, line: str) -> bool:
        parts = line.strip().split()
        if not parts:
            return True
        cmd, args = parts[0].lower(), parts[1:]

        ext = globals().get("ext_handle_command")
        if callable(ext):
            try:
                if ext(cmd, args, self):
                    return True
            except Exception as e:
                self.say(f"[Extension ignored] {e}")

        if cmd in ("quit", "exit", "q"):
            return False
        if cmd == "help":
            self.help()
            return True
        if cmd == "look":
            self.look()
            return True
        if cmd in ("n", "s", "e", "w", "north", "south", "east", "west"):
            self.move(cmd)
            return True
        if cmd in ("move", "go"):
            if args:
                self.move(args[0])
            else:
                self.say("Use: move n/s/e/w")
            return True
        if cmd in ("take", "get", "pickup", "pick"):
            if args and args[0] == "up": args = args[1:]
            self.take(" ".join(args))
            return True
        if cmd == "drop":
            self.drop(" ".join(args))
            return True
        if cmd in ("use", "eat", "consume"):
            wanted = " ".join(args).strip().lower()
            if cmd in ("eat", "consume") and "apple" not in wanted:
                self.say(f"You can't {cmd} the {wanted}.")
                return True
            self.use(" ".join(args))
            return True
        if cmd in ("unlock", "open"):
            if self.cur_room != "gate":
                self.say("There's nothing obvious to unlock here.")
                return True
            if "rust_key" not in self.player.inv:
                self.say("You need a key for this lock.")
                return True
            self.use("rust key")
            return True
        if cmd in ("talk", "ask", "say", "hello", "hi", "greet"):
            self._process_dialogue_command(cmd, args, line)
            return True
        if cmd == "inv":
            self.inv()
            return True
        if cmd == "map":
            self.map()
            return True
        if cmd == "stats":
            self.stats()
            return True

        # Explicit conversation exit
        full_line = line.lower().strip()
        if cmd in ("goodbye", "bye") or full_line in ("leave conversation", "end conversation"):
            if getattr(self, "active_conversation_npc_id", None):
                self.say(f"You end your conversation with the {self.active_conversation_npc_id}.")
                self._end_conversation()
            else:
                self.say("You aren't talking to anyone.")
            return True

        # Conversational fallback
        active_npc = getattr(self, "active_conversation_npc_id", None)
        if active_npc:
            room = self.room()
            npcs_here = list(getattr(room, "npcs", []))
            def find_npc(name):
                for n in npcs_here:
                    if name.lower() in n.lower() or n.lower() in name.lower(): return n
                return None
            if getattr(self, "conversation_room", None) == self.cur_room and find_npc(active_npc):
                self._emit_dialogue_request(active_npc, line)
                return True
            else:
                self._end_conversation()

        suggestion = self._suggest_command(cmd, args)
        if suggestion:
            self.say(f"Unknown command. Did you mean: {suggestion}")
        else:
            if "?" in line and not active_npc:
                self.say("You're not currently talking to anyone. Try `talk [npc]`.")
            else:
                self.say("Unknown command. Try 'help'.")
        return True

    def run(self) -> None:
        self.say("Welcome to the Whispering Wilds. Type 'help' for commands.")
        self.look()
        while True:
            try:
                line = input("> ")
            except EOFError:
                break
            if not self.dispatch(line):
                break

# ===========================
# TEXT ADVENTURE - PART 2 (Wilds & Combat)
# ===========================
import random



def part2_post_init(game):
    game._p2 = {
        "xp": 0,
        "bandages": 1,
        "rng": random.Random(99),
    }
    # Add wilds room if base Part 1 world present
    if hasattr(game, "world") and "wilds_stub" in game.world.rooms:
        wilds = Room("wilds", "Whispering Wilds", "The wild lands teem with danger and chance.")
        game.world.add_room(wilds)
        game.world.rooms["wilds_stub"].link("e", "wilds")
        wilds.link("w", "wilds_stub")


# Capture the ext_handle_command that existed before this part was loaded.
P2_PREV_EXT = globals().get("ext_handle_command", None)

# Part 2 defines its own handler.  It stores a reference to the previous
# ext_handle_command in P2_PREV_EXT so it can delegate if needed.  After
# defining this function, we overwrite the module-level ext_handle_command
# to point here, forming a chain of responsibility.
def p2_ext_handle_command(cmd, args, game):
    # Avoid self-recursion by comparing against our own function name.
    prev = P2_PREV_EXT if P2_PREV_EXT is not p2_ext_handle_command else None

    if cmd == "attack":
        if not game or not hasattr(game, "player"):
            print("You flail at nothing. (Base game not loaded)")
            return True
        dmg = game._p2["rng"].randint(1, 3)
        game.say(f"You strike into the air. (Dealt {dmg} imaginary damage)")
        game._p2["xp"] += 1
        return True

    if cmd == "rest":
        if not game or not hasattr(game, "player"):
            print("You try to rest, but nothing happens. (Base game not loaded)")
            return True
        if game.player.hp < game.player.max_hp:
            game.player.hp = min(game.player.max_hp, game.player.hp + 2)
            game.say("You rest and recover 2 HP.")
        else:
            game.say("You rest, but you're already at full health.")
        return True


    if cmd == "stats":
        if game and hasattr(game, "_p2"):
            print(f"XP: {game._p2['xp']}  Bandages: {game._p2['bandages']}")
        return False

    if prev and prev(cmd, args, game):
        return True
    return False

# Overwrite the global ext_handle_command with this part's handler.  Future
# parts will capture this value in their own PREV variables.
ext_handle_command = p2_ext_handle_command



# ===========================
# TEXT ADVENTURE - PART 3 (Forage, Craft, Shop, Flags)
# ===========================
import random

P3_PREV_EXT = globals().get("ext_handle_command", None)


def part3_post_init(game):
    if not game or getattr(game, "_p3", None) is not None:
        return
    game._p3 = {
        "rng": random.Random(9001),
        "mats": {"fiber": 0, "herb": 0},
        "gold": 5,
        "flags": {},
        "prices": {"bandage": 3, "apple": 1},
    }
    _ = game._p3["rng"].random()

def _p3_forage(game):
    if not game or not hasattr(game, "_p3"):
        print("You poke around but find nothing. (Base game not loaded)")
        return
    rng = game._p3["rng"]
    found = "herb" if rng.random() < 0.5 else "fiber"
    game._p3["mats"][found] += 1
    game.say(f"You forage and find 1 {found}.")

def _p3_craft(game, what):
    if not game or not hasattr(game, "_p3"):
        print("You lack the know-how to craft. (Base game not loaded)")
        return
    what = (what or "").strip().lower()
    if what in ("bandage", "bandages"):
        if game._p3["mats"]["fiber"] >= 1:
            game._p3["mats"]["fiber"] -= 1
            # Store bandages in Part 2 if present; otherwise just note success
            if hasattr(game, "_p2"):
                game._p2["bandages"] = game._p2.get("bandages", 0) + 1
                game.say("You craft a bandage (+1).")
            else:
                game.say("You craft a bandage, but have nowhere to store it yet.")
        else:
            game.say("Not enough fiber to craft a bandage.")
    else:
        game.say("You don't know how to craft that.")

def _p3_buy(game, item):
    if not game or not hasattr(game, "_p3"):
        print("No merchant here. (Base game not loaded)")
        return
    it = (item or "").strip().lower()
    prices = game._p3["prices"]
    if it not in prices:
        game.say("That item isn't for sale.")
        return
    cost = prices[it]
    if game._p3["gold"] < cost:
        game.say("Not enough gold.")
        return
    game._p3["gold"] -= cost
    if it == "bandage":
        if hasattr(game, "_p2"):
            game._p2["bandages"] = game._p2.get("bandages", 0) + 1
            game.say("You buy a bandage. (+1)")
        else:
            game.say("You buy a bandage, but have nowhere to put it yet.")
    elif it == "apple":
        try:
            game.player.add_item(Item("apple", "Apple", "A crisp, red apple.", usable=True))
            game.say("You buy an apple.")
        except Exception:
            game.say("You pay for an apple, but it vanishes into the void. (Base not loaded)")

def _p3_sell(game, item):
    if not game or not hasattr(game, "_p3"):
        print("No buyer here. (Base game not loaded)")
        return
    it = (item or "").strip().lower()
    if it == "apple":
        if "apple" in game.player.inv:
            game.player.remove_item("apple")
            game._p3["gold"] += 1
            game.say("Sold an apple for 1 gold.")
        else:
            game.say("You don't have an apple.")
    elif it in ("bandage", "bandages"):
        if hasattr(game, "_p2") and game._p2.get("bandages", 0) > 0:
            game._p2["bandages"] -= 1
            game._p3["gold"] += 1
            game.say("Sold a bandage for 1 gold.")
        else:
            game.say("You have no bandages.")
    elif it in ("fiber", "herb"):
        if game._p3["mats"].get(it, 0) > 0:
            game._p3["mats"][it] -= 1
            game._p3["gold"] += 1
            game.say(f"Sold 1 {it} for 1 gold.")
        else:
            game.say(f"You have no {it}.")
    else:
        game.say("No one wants that.")

def _p3_stats_overlay(game):
    if game and hasattr(game, "_p3"):
        mats = game._p3["mats"]
        print(f"Gold: {game._p3['gold']}  Mats: fiber={mats['fiber']} herb={mats['herb']}")

def p3_ext_handle_command(cmd, args, game):
    # Use the captured previous handler if it isn't ourselves
    prev = P3_PREV_EXT if P3_PREV_EXT is not p3_ext_handle_command else None


    if cmd == "forage":
        _p3_forage(game)
        return True

    if cmd == "craft":
        _p3_craft(game, " ".join(args))
        return True

    if cmd == "buy":
        _p3_buy(game, " ".join(args))
        return True

    if cmd == "sell":
        _p3_sell(game, " ".join(args))
        return True

    if cmd == "stats":
        _p3_stats_overlay(game)
        if prev and prev(cmd, args, game):
            return True
        return False

    if prev and prev(cmd, args, game):
        return True
    return False

# Register this part's handler as the new ext_handle_command.  The next
# part will capture this handler in its own PREV variable.
ext_handle_command = p3_ext_handle_command


                
# ===========================
# TEXT ADVENTURE - PART 4 (Journal, Options, Save/Load)
# ===========================
import json as _p4_json
import base64 as _p4_b64

P4_PREV_EXT = globals().get("ext_handle_command", None)


def part4_post_init(game):
    if not game:
        return
    if getattr(game, "_p4", None) is not None:
        return
    game._p4 = {
        "journal": [],
        "options": {"hardmode": False},
    }

def _p4_note(game, text: str) -> None:
    if not game:
        print("(mock) Noted.")
        return
    p4 = getattr(game, "_p4", None)
    if not p4:
        print("You have no journal.")
        return
    text = (text or "").strip()
    if not text:
        game.say("Note what?")
        return
    p4["journal"].append(text)
    game.say("Noted.")

def _p4_journal(game) -> None:
    if not game:
        print("(mock) Journal empty.")
        return
    p4 = getattr(game, "_p4", None)
    if not p4:
        game.say("You have no journal.")
        return
    if not p4["journal"]:
        game.say("Journal is empty.")
        return
    game.say("Journal:")
    for i, line in enumerate(p4["journal"], 1):
        game.say(f"  {i}. {line}")

def _p4_erase(game, idx_str: str) -> None:
    if not game:
        print("(mock) Nothing erased.")
        return
    p4 = getattr(game, "_p4", None)
    if not p4 or not p4["journal"]:
        game.say("Nothing to erase.")
        return
    try:
        idx = int(idx_str) - 1
    except ValueError:
        game.say("Erase which number?")
        return
    if 0 <= idx < len(p4["journal"]):
        removed = p4["journal"].pop(idx)
        game.say(f"Erased: {removed}")
    else:
        game.say("No such entry.")

def _p4_option(game, key: str, value: str) -> None:
    if not game:
        print("(mock) Option toggled.")
        return
    p4 = getattr(game, "_p4", None)
    if not p4:
        game.say("Options unavailable.")
        return
    key = (key or "").lower()
    if key not in ("hardmode",):
        game.say("Unknown option.")
        return
    if (value or "").lower() in ("on", "true", "1"):
        p4["options"][key] = True
    elif (value or "").lower() in ("off", "false", "0"):
        p4["options"][key] = False
    else:
        game.say("Use: options hardmode on/off")
        return
    game.say(f"{key} set to {p4['options'][key]}")

def _p4_save(game) -> None:
    state = {
        "cur_room": getattr(game, "cur_room", None) if game else None,
        "inv": [it.id for it in getattr(getattr(game, "player", None), "inv", {}).values()] if game else [],
        "hp": getattr(getattr(game, "player", None), "hp", None) if game else None,
        "max_hp": getattr(getattr(game, "player", None), "max_hp", None) if game else None,
    }
    if game and getattr(game, "_p2", None) is not None:
        state["p2"] = {
            "xp": game._p2.get("xp", 0),
            "bandages": game._p2.get("bandages", 0),
        }
    if game and getattr(game, "_p3", None) is not None:
        state["p3"] = {
            "gold": game._p3.get("gold", 0),
            "mats": game._p3.get("mats", {"fiber": 0, "herb": 0}),
            "flags": game._p3.get("flags", {}),
        }
    if game and getattr(game, "_p4", None) is not None:
        state["p4"] = {
            "journal": list(game._p4.get("journal", [])),
            "options": dict(game._p4.get("options", {})),
        }
    payload = _p4_json.dumps(state, separators=(",", ":")).encode("utf-8")
    code = _p4_b64.b64encode(payload).decode("ascii")
    print("SAVE CODE:")
    print(code)

def _p4_load(game, code: str) -> None:
    try:
        data = _p4_json.loads(_p4_b64.b64decode((code or "").encode("ascii")).decode("utf-8"))
    except Exception:
        print("Bad code.")
        return
    if not game:
        print("Loaded (mock). Paste Part 1 to apply in-game.")
        return
    if "cur_room" in data and data["cur_room"] in game.world.rooms:
        game.cur_room = data["cur_room"]
    if "hp" in data and "max_hp" in data:
        game.player.max_hp = int(data["max_hp"])
        game.player.hp = max(0, min(game.player.max_hp, int(data["hp"])))
    if "inv" in data:
        game.player.inv.clear()
        for iid in data["inv"]:
            if iid == "rust_key":
                game.player.add_item(Item("rust_key", "Rusty Key", "Old key with a jagged bite.", usable=True))
            elif iid == "apple":
                game.player.add_item(Item("apple", "Apple", "A crisp, red apple.", usable=True))
            else:
                game.player.add_item(Item(iid, iid, "Recovered item."))
    if getattr(game, "_p2", None) is not None and "p2" in data:
        if "xp" in data["p2"]:
            game._p2["xp"] = int(data["p2"]["xp"])
        if "bandages" in data["p2"]:
            game._p2["bandages"] = int(data["p2"]["bandages"])
    if getattr(game, "_p3", None) is not None and "p3" in data:
        if "gold" in data["p3"]:
            game._p3["gold"] = int(data["p3"]["gold"])
        if "mats" in data["p3"]:
            mats = data["p3"]["mats"]
            for k in ("fiber", "herb"):
                if k in mats:
                    game._p3["mats"][k] = int(mats[k])
        if "flags" in data["p3"]:
            game._p3["flags"] = dict(data["p3"]["flags"])
    if getattr(game, "_p4", None) is not None and "p4" in data:
        if "journal" in data["p4"]:
            game._p4["journal"] = list(data["p4"]["journal"])
        if "options" in data["p4"]:
            game._p4["options"] = dict(data["p4"]["options"])
    print("Game loaded.")

def p4_ext_handle_command(cmd, args, game):
    # Use the captured previous handler if it isn't ourselves
    prev = P4_PREV_EXT if P4_PREV_EXT is not p4_ext_handle_command else None


    if cmd == "note":
        _p4_note(game, " ".join(args))
        return True

    if cmd == "journal":
        _p4_journal(game)
        return True

    if cmd == "erase":
        _p4_erase(game, args[0] if args else "")
        return True

    if cmd == "options":
        if len(args) >= 2:
            _p4_option(game, args[0], args[1])
        else:
            print("Options: hardmode on/off")
        return True

    if cmd == "save":
        _p4_save(game)
        return True

    if cmd == "load":
        _p4_load(game, " ".join(args))
        return True

    if prev and prev(cmd, args, game):
        return True
    return False

# Register this part's handler as the new ext_handle_command.
ext_handle_command = p4_ext_handle_command



# ===========================
# TEXT ADVENTURE - PART 5 (Dynamic Encounters & Bestiary)
# ===========================
import random

P5_PREV_EXT = globals().get("ext_handle_command", None)


def part5_post_init(game):
    if not game or getattr(game, "_p5", None) is not None:
        return
    game._p5 = {
        "rng": random.Random(5150),
        "rate": 0.35,            # chance to trigger on a qualifying move
        "encounter": None,       # {"name": str, "hp": int, "max_hp": int}
        "seen": set(),           # creatures seen
        "bestiary": {
            "Whisper Wolf": {
                "hp": (2, 4),
                "lore": "Once guardians of the grove, now restless and thin as mist."
            },
            "Bramble Wight": {
                "hp": (3, 5),
                "lore": "A tangle of thorn and memory that hates the sound of steel."
            },
            "Glimmer Moth": {
                "hp": (1, 2),
                "lore": "Shy lights of the old road. Their dust remembers voices."
            },
            "Bog Shade": {
                "hp": (4, 6),
                "lore": "A cold echo wearing the shape of fear. It drinks warmth."
            },
        },
    }
    # gentle seed touch
    _ = game._p5["rng"].random()

def _p5_in_wilds(game):
    r = getattr(game, "room", lambda: None)()
    if not r:
        return False
    rid = getattr(r, "id", "")
    name = getattr(r, "name", "")
    return (
        rid.startswith("wilds")
        or rid in ("wilds_stub", "wilds_e1", "wilds_e2")
        or "Wild" in name
        or "Bramble" in name
    )

def _p5_spawn(game, forced=False):
    p5 = getattr(game, "_p5", None)
    if not p5 or p5["encounter"] is not None:
        return
    if not forced:
        if not _p5_in_wilds(game):
            return
        if p5["rng"].random() > p5["rate"]:
            return
    # pick a creature
    name = p5["rng"].choice(list(p5["bestiary"].keys()))
    hp_low, hp_high = p5["bestiary"][name]["hp"]
    hp = p5["rng"].randint(hp_low, hp_high)
    p5["encounter"] = {"name": name, "hp": hp, "max_hp": hp}
    first_time = name not in p5["seen"]
    p5["seen"].add(name)
    game.say(f"A {name} emerges!")
    if first_time:
        game.say("(New entry added to your bestiary.)")

def _p5_end_encounter(game):
    p5 = getattr(game, "_p5", None)
    if p5:
        p5["encounter"] = None

def _p5_player_hit(game, foe):
    p5 = game._p5
    rng = p5["rng"]
    hit = rng.random() < 0.7
    if not hit:
        game.say(f"You miss the {foe['name']}.")
        return False
    dmg = rng.randint(1, 3)
    foe["hp"] = max(0, foe["hp"] - dmg)
    game.say(f"You hit the {foe['name']} (-{dmg} HP).")
    return True

def _p5_enemy_hit(game, foe):
    p5 = game._p5
    rng = p5["rng"]
    if rng.random() < 0.5:
        dmg = rng.randint(1, 2)
        game.player.hp = max(0, game.player.hp - dmg)
        game.say(f"The {foe['name']} strikes you (-{dmg} HP).")
        if game.player.hp == 0:
            game.say("You collapse and awaken at the Sanctum.")
            game.player.hp = game.player.max_hp
            game.cur_room = game.world.start_room
            _p5_end_encounter(game)
            return True
    return False

def _p5_reward(game, foe):
    # Grant XP if Part 2 exists; maybe drop mats if Part 3 exists
    if getattr(game, "_p2", None) is not None:
        game._p2["xp"] = game._p2.get("xp", 0) + 1
        game.say("(+1 XP)")
    # 30% drop herb or fiber if Part 3 exists
    if getattr(game, "_p3", None) is not None:
        rng = game._p5["rng"]
        if rng.random() < 0.3:
            drop = "herb" if rng.random() < 0.5 else "fiber"
            game._p3["mats"][drop] = game._p3["mats"].get(drop, 0) + 1
            game.say(f"The {foe['name']} drops a {drop}.")

def _p5_handle_attack(game, args):
    p5 = getattr(game, "_p5", None)
    if not p5 or p5["encounter"] is None:
        return False
    foe = p5["encounter"]
    _p5_player_hit(game, foe)
    if foe["hp"] <= 0:
        game.say(f"The {foe['name']} dissipates.")
        _p5_reward(game, foe)
        _p5_end_encounter(game)
        return True
    if _p5_enemy_hit(game, foe):
        return True
    # report status
    game.say(f"{foe['name']} HP: {foe['hp']}/{foe['max_hp']}")
    return True

def _p5_bestiary(game):
    p5 = getattr(game, "_p5", None)
    if not p5:
        print("No bestiary available. (Base game not loaded)")
        return
    if not p5["seen"]:
        print("Bestiary is empty.")
        return
    print("Bestiary:")
    for name in sorted(p5["seen"]):
        lore = p5["bestiary"].get(name, {}).get("lore", "")
        print(f"- {name}: {lore}")

def _p5_lore(game, name):
    p5 = getattr(game, "_p5", None)
    if not p5:
        print("No lore available. (Base game not loaded)")
        return
    name = (name or "").strip()
    if not name:
        print("Use: lore [creature name]")
        return
    data = p5["bestiary"].get(name)
    if not data:
        print("No such creature.")
        return
    print(f"{name}: {data['lore']}")

def p5_ext_handle_command(cmd, args, game):
    # Use the captured previous handler if it isn't ourselves
    prev = P5_PREV_EXT if P5_PREV_EXT is not p5_ext_handle_command else None


    # If attacking during our encounter, we handle it; else defer to Part 2.
    if cmd == "attack":
        if getattr(game, "_p5", None) and game and game._p5["encounter"]:
            return _p5_handle_attack(game, args)
        if prev and prev(cmd, args, game):
            return True
        return False

    # Prevent resting while something is attacking
    if cmd == "rest":
        if getattr(game, "_p5", None) and game and game._p5["encounter"]:
            game.say("Too dangerous to rest while engaged!")
            return True
        if prev and prev(cmd, args, game):
            return True
        return False

    # Intercept move to inject post-move encounter checks
    if cmd in ("move", "go"):
        # Do the move using base Game
        # If base not present, fall back to previous ext or fail silently
        if game and hasattr(game, "move"):
            if args:
                game.move(args[0])
            else:
                game.say("Use: move n/s/e/w")
            _p5_spawn(game, forced=False)
            return True
        if prev and prev(cmd, args, game):
            return True
        return False

    # Force an encounter where possible
    if cmd == "hunt":
        if not game:
            print("You prowl the void. (Base game not loaded)")
            return True
        if getattr(game, "_p5", None) and game._p5["encounter"]:
            game.say("You are already engaged!")
            return True
        _p5_spawn(game, forced=True)
        if getattr(game, "_p5", None) and game._p5["encounter"] is None:
            game.say("Nothing answers your challenge.")
        return True

    if cmd == "bestiary":
        _p5_bestiary(game)
        return True

    if cmd == "lore":
        _p5_lore(game, " ".join(args))
        return True

    if prev and prev(cmd, args, game):
        return True
    return False

# Register this part's handler as the new ext_handle_command.
ext_handle_command = p5_ext_handle_command



# ===========================
# TEXT ADVENTURE - PART 6 (Dialogue Trees & NPC Quests)
# ===========================
import random

P6_PREV_EXT = globals().get("ext_handle_command", None)



def part6_post_init(game):
    """Initialise dialogue/quest state. Gentle RNG touch."""
    if not game or getattr(game, "_p6", None) is not None:
        return
    game._p6 = {
        "rng": random.Random(6006),
        "dialog": None,  # {"npc": str, "options": [(text, action_id), ...]}
        "quests": {
            "heal_grove": {
                "title": "Heal the Grove",
                "state": "new",     # new -> offered -> accepted -> completed -> turned_in
                "need": {"herb": 2},
                "lore": "The northern grove is ailing. Brew a simple remedy.",
                "reward": {"gold": 3, "xp": 1},
            }
        },
    }
    _ = game._p6["rng"].random()

# -------- helpers --------

def _p6_journal_add(game, line: str):
    p4 = getattr(game, "_p4", None)
    if p4 is not None:
        try:
            p4["journal"].append(line)
        except Exception:
            pass

def _p6_show_dialog(game, npc: str, options):
    game._p6["dialog"] = {"npc": npc, "options": options}
    game.say(f"{npc} listens. Choose:")
    for i, (text, _aid) in enumerate(options, 1):
        game.say(f"  {i}. {text}")
    game.say("Say a number with: say [n]")

def _p6_open_caretaker_dialog(game):
    q = game._p6["quests"]["heal_grove"]
    state = q["state"]
    if state in ("new", "offered"):
        opts = [
            ("Who are you?", "ct_intro"),
            ("What is this place?", "ct_place"),
            ("Tell me about the Whispering Wilds.", "ct_wilds"),
            ("What threats lie beyond these walls?", "ct_threats"),
            ("Is there any work I can do?", "ct_offer_quest"),
            ("What can you tell me about the grove?", "ct_grove_lore"),
            ("Goodbye.", "ct_bye"),
        ]
    elif state == "accepted":
        opts = [
            ("Remind me about the remedy.", "ct_remind"),
            ("Where can I find herbs?", "ct_herb_tips"),
            ("Tell me more about the grove's illness.", "ct_grove_sick"),
            ("Goodbye.", "ct_bye"),
        ]
    elif state == "completed":
        opts = [
            ("I have what you asked for.", "ct_turnin"),
            ("Goodbye.", "ct_bye"),
        ]
    else:  # turned_in
        opts = [
            ("How fares the grove now?", "ct_after"),
            ("Do you have any other tasks?", "ct_more_work"),
            ("Tell me a story.", "ct_story"),
            ("Goodbye.", "ct_bye"),
        ]
    _p6_show_dialog(game, "Caretaker", opts)

def _p6_eval_requirements(game, need: dict) -> bool:
    """Check if player has required items/mats. Uses Part 3 mats if present."""
    p3 = getattr(game, "_p3", None)
    if not p3:
        return False
    mats = p3.get("mats", {})
    for k, v in need.items():
        if mats.get(k, 0) < v:
            return False
    return True

def _p6_consume_requirements(game, need: dict) -> None:
    p3 = getattr(game, "_p3", None)
    if not p3:
        return
    for k, v in need.items():
        p3["mats"][k] = max(0, p3["mats"].get(k, 0) - v)

def _p6_apply_reward(game, reward: dict) -> None:
    # Gold (Part 3)
    if "gold" in reward and getattr(game, "_p3", None) is not None:
        game._p3["gold"] = game._p3.get("gold", 0) + int(reward["gold"])
        game.say(f"(+{int(reward['gold'])} gold)")
    # XP (Part 2)
    if "xp" in reward and getattr(game, "_p2", None) is not None:
        game._p2["xp"] = game._p2.get("xp", 0) + int(reward["xp"])
        game.say(f"(+{int(reward['xp'])} XP)")

def _p6_do_action(game, action_id: str):
    q = game._p6["quests"]["heal_grove"]

    if action_id == "ct_intro":
        game.say('Caretaker: "A watcher of thresholds. I keep small fires lit."')
        return
    if action_id == "ct_place":
        game.say('Caretaker: "These halls are called the Sanctum. The Wilds press close."')
        return
    if action_id == "ct_offer_quest":
        q["state"] = "offered"
        _p6_journal_add(game, "Caretaker offered a task: Heal the Grove (bring 2 herbs).")
        game.say('Caretaker: "The northern grove is sick. Bring me 2 herbs for a remedy."')
        game.say("Type: accept heal_grove   (or talk caretaker again for details)")
        return
    if action_id == "ct_remind":
        need = ", ".join(f"{v} {k}" for k, v in q["need"].items())
        game.say(f'Caretaker: "Gather {need}. The grove north of here is fading."')
        return
    if action_id == "ct_turnin":
        if q["state"] != "completed":
            game.say('Caretaker: "You seem unready yet."')
            return
        # Finalise in turnin command to consume + reward
        game.say('Caretaker: "If you are certain, give them here."')
        game.say("Use: turnin heal_grove")
        return
    if action_id == "ct_after":
        game.say('Caretaker: "The grove breathes easier. Thank you."')
        return
    if action_id == "ct_bye":
        game.say("You end the conversation.")
        game._p6["dialog"] = None
        return

# -------- commands --------

def _p6_cmd_talk(game, args) -> bool:
    """Open dialogue tree for known NPCs; otherwise defer/base."""
    who = " ".join(args).strip().lower()
    if not game:
        print("You speak into the void. (Base game not loaded)")
        return True
    return False  # let base or earlier parts handle

def _p6_cmd_say(game, args) -> bool:
    if not game:
        print("Your words vanish. (Base game not loaded)")
        return True
    return False

def _p6_cmd_accept(game, args) -> bool:
    if not game:
        print("Nothing to accept here. (Base game not loaded)")
        return True
    if not args:
        game.say("Accept what? Try: accept heal_grove")
        return True
    key = args[0].lower()
    if key != "heal_grove":
        game.say("No such offer.")
        return True
    q = game._p6["quests"]["heal_grove"]
    if q["state"] not in ("new", "offered"):
        game.say("You have already decided.")
        return True
    q["state"] = "accepted"
    _p6_journal_add(game, "Accepted quest: Heal the Grove (bring 2 herbs).")
    game.say("Quest accepted: Heal the Grove.")
    return True

def _p6_cmd_turnin(game, args) -> bool:
    if not game:
        print("You turn in nothing to no one. (Base game not loaded)")
        return True
    if not args:
        game.say("Turn in which quest? Try: turnin heal_grove")
        return True
    key = args[0].lower()
    if key != "heal_grove":
        game.say("No such quest.")
        return True
    q = game._p6["quests"]["heal_grove"]
    # Check requirements via Part 3 mats
    if q["state"] not in ("accepted", "completed"):
        game.say("You haven't accepted this quest.")
        return True
    if not _p6_eval_requirements(game, q["need"]):
        game.say("You lack the needed herbs.")
        return True
    # Consume and reward
    _p6_consume_requirements(game, q["need"])
    _p6_apply_reward(game, q["reward"])
    q["state"] = "turned_in"
    _p6_journal_add(game, "Turned in: Heal the Grove. The grove feels calmer.")
    game.say("You hand over the herbs. The remedy is mixed; the grove will recover.")
    return True

def _p6_cmd_quests(game) -> bool:
    if not game:
        print("No quests to list. (Base game not loaded)")
        return True
    qs = getattr(game, "_p6", {}).get("quests", {})
    if not qs:
        game.say("No quests.")
        return True
    game.say("Quests:")
    for key, q in qs.items():
        title = q["title"]
        state = q["state"]
        line = f"- {title}: {state}"
        # Show progress if Part 3 present
        if getattr(game, "_p3", None) is not None and "need" in q and state in ("accepted", "completed"):
            need = q["need"]
            mats = game._p3.get("mats", {})
            prog = ", ".join(f"{k} {mats.get(k,0)}/{v}" for k, v in need.items())
            line += f" ({prog})"
            if _p6_eval_requirements(game, q["need"]):
                q["state"] = "completed"
        game.say(line)
    return True

def p6_ext_handle_command(cmd, args, game):
    # Use the captured previous handler if it isn't ourselves
    prev = P6_PREV_EXT if P6_PREV_EXT is not p6_ext_handle_command else None


    if cmd == "talk":
        if _p6_cmd_talk(game, args):
            return True
        if prev and prev(cmd, args, game):
            return True
        return False

    if cmd == "say":
        return _p6_cmd_say(game, args)

    if cmd == "quests":
        return _p6_cmd_quests(game)

    if cmd == "accept":
        return _p6_cmd_accept(game, args)

    if cmd == "turnin":
        return _p6_cmd_turnin(game, args)

    # Defer unknowns to previous extensions
    if prev and prev(cmd, args, game):
        return True
    return False

# Register this part's handler as the new ext_handle_command.
ext_handle_command = p6_ext_handle_command


# ===========================
# TEXT ADVENTURE - PART 7 (Frontier Expansion: Places, NPCs, Quests, Activities)
# ===========================
import random as _p7_rand

P7_PREV_EXT = globals().get("ext_handle_command", None)

def part7_post_init(game):
    """Add new areas branching from the Wilds, NPCs, and extra creatures."""
    if not game:
        return

    # ---------- Map expansions ----------
    w = game.world
    add = w.add_room
    rooms = w.rooms

    # Create when the core Wilds exist (Part 2 adds 'wilds')
    if "wilds" in rooms:
        # Lake, Mine, Ranger Camp, Hermit's Hut, Trader Post, Old Tower
        lake = Room("wilds_lake", "Moonlit Lake",
                    "A cold, glassy lake. Ripples reveal darting shapes.")
        mine = Room("wilds_mine", "Abandoned Mine",
                    "Timbers groan above a vein of dull ore.")
        camp = Room("wilds_camp", "Ranger Camp",
                    "A tidy camp with a banked fire and supple bows.")
        hut  = Room("wilds_hut", "Hermit's Hut",
                    "Bundles of herbs hang from the rafters.")
        post = Room("wilds_post", "Trader's Post",
                    "A makeshift counter piled with oddments.")
        tower= Room("wilds_tower", "Old Watchtower",
                    "Cracked stairs spiral into shadow; graffiti marks the stone.")

        # NPCs
        camp.npcs.append("Ranger")
        hut.npcs.append("Hermit")
        post.npcs.append("Trader")

        # Links
        rooms["wilds"].link("n", "wilds_lake")
        rooms["wilds"].link("e", "wilds_mine")
        rooms["wilds"].link("s", "wilds_camp")
     #   rooms["wilds"].link("w", "wilds_tower")
        # Put the Old Watchtower off the Overgrown Verge (wilds_stub) to avoid stealing Wilds' west exit
        rooms["wilds_stub"].link("n", "wilds_tower")
        tower.link("s", "wilds_stub")

        lake.link("s", "wilds")
        mine.link("w", "wilds")
        camp.link("n", "wilds")
        tower.link("e", "wilds")

        # Link the Hermit's Hut off the tower
        tower.link("s", "wilds_hut")
        hut.link("n", "wilds_tower")

        # Trader off the camp
        camp.link("e", "wilds_post")
        post.link("w", "wilds_camp")

        for r in (lake, mine, camp, hut, post, tower):
            add(r)

    # ---------- Ensure Part 3 mats can hold new resources ----------
    if getattr(game, "_p3", None) is not None:
        mats = game._p3.setdefault("mats", {})
        for k in ("fish", "ore", "glowcap", "coal"):
            mats.setdefault(k, 0)

    # ---------- Ensure Part 6 quest container exists, inject new quests ----------
    if getattr(game, "_p6", None) is None:
        # Create a minimal Part 6 state so we can use its quest list
        game._p6 = {"rng": _p7_rand.Random(7007), "dialog": None, "quests": {}}

    q = game._p6.setdefault("quests", {})
    q.setdefault("angler_aid", {
        "title": "Angler's Aid",
        "state": "new",
        "need": {"fish": 2},
        "lore": "The Trader craves fresh fish. He pays fairly.",
        "reward": {"gold": 5, "xp": 1},
    })
    q.setdefault("mine_matters", {
        "title": "Mine Matters",
        "state": "new",
        "need": {"ore": 2},
        "lore": "The Ranger needs ore to fix buckles and stove-pins.",
        "reward": {"gold": 4, "xp": 1},
    })
    q.setdefault("hermit_glow", {
        "title": "Hermit's Glow",
        "state": "new",
        "need": {"glowcap": 3},
        "lore": "The Hermit brews a salve that needs glowcaps from damp places.",
        "reward": {"gold": 3, "xp": 1},
    })

    # ---------- Enrich the bestiary if Part 5 is present ----------
    if getattr(game, "_p5", None) is not None:
        best = game._p5.setdefault("bestiary", {})
        best.setdefault("Fen Serpent", {
            "hp": (3, 5),
            "lore": "A patient coil beneath still water. Its breath smells of bog."
        })
        best.setdefault("Stone Gnaw", {
            "hp": (2, 4),
            "lore": "A pale burrower that chews ore for the iron taste."
        })
        best.setdefault("Camp Raider", {
            "hp": (3, 6),
            "lore": "A desperate soul with wild eyes, quick to flee."
        })

# ---------- Local helpers ----------
def _p7_here(game, *ids) -> bool:
    return getattr(game, "cur_room", None) in ids

def _p7_has_p3(game) -> bool:
    return getattr(game, "_p3", None) is not None

def _p7_add_mat(game, name: str, qty: int = 1):
    if not _p7_has_p3(game):  # fall back: drop as inventory item
        game.player.add_item(Item(name, name.title(), f"{qty} {name}"))
        return
    mats = game._p3.setdefault("mats", {})
    mats[name] = mats.get(name, 0) + qty

def _p7_take_mat(game, name: str, qty: int) -> bool:
    if not _p7_has_p3(game):
        return False
    mats = game._p3["mats"]
    if mats.get(name, 0) >= qty:
        mats[name] -= qty
        return True
    return False

def _p7_rng(game):
    r = getattr(getattr(game, "_p6", None), "get", lambda *_: None)("rng")
    return r if r else _p7_rand.Random(777)

# ---------- Activities ----------
#def _p7_fish(game):
    #   if not game or getattr(game, "room", None) is None:
    #   print("You cast into the void. (Base game not loaded)")
    #   return
    #    room = game.room()
    # if room.name != "Moonlit Lake":
    #   game.say("You can only fish at the Moonlit Lake.")
    #   return

    #    rng = random.Random()
    #  roll = rng.random()

    #   if roll < 0.2:
    #     game.say("Nothing bites.")
    #    return
    #  elif roll < 0.95:
    #    fish_item = Item("fish", "Fresh Fish", "A slippery, fresh-caught fish.", usable=False)
    #    game.player.add_item(fish_item)
    #    game.say("You catch a small fish! (Added to inventory)")
    #  else:
    #   ring_item = Item("lost_ring", "Lost Ring", "An old ring dredged from the depths.", usable=False)
    #   game.player.add_item(ring_item)
    #   game.say("Glint! You dredge up a Lost Ring.")

    # Optional: track catch for Trader quest
    p7 = getattr(game, "_p7", None)
    if p7:
        q = p7["quests"].get("angler_aid")
        if q and q["state"] == "accepted":
            q["caught"] = q.get("caught", 0) + 1
            if q["caught"] >= 2:
                q["state"] = "completed"
                game.say("Quest update: You’ve caught enough fish for the Trader!")


def _p7_cmd_mine(game, args) -> bool:
    if not game:
        print("You swing at nothing. (Base game not loaded)")
        return True
    if not _p7_here(game, "wilds_mine"):
        game.say("You need a rock face to mine.")
        return True
    r = _p7_rng(game)
    got = 1 if r.random() < 0.85 else 0
    if got:
        _p7_add_mat(game, "ore", 1)
        game.say("You chip out a lump of ore.")
        if r.random() < 0.25:
            _p7_add_mat(game, "coal", 1)
            game.say("You find a chunk of coal.")
    else:
        game.say("Your pick glances off crumbly stone.")
    return True

def _p7_cmd_harvest(game, args) -> bool:
    # Glowcaps from damp places: Hut (stored), Tower base (mossy), Mine seams (rare)
    if not game:
        print("You harvest nothing. (Base game not loaded)")
        return True
    r = _p7_rng(game)
    room = getattr(game, "cur_room", "")
    chance = 0.0
    if room in ("wilds_hut",):       # the Hermit tends them → common
        chance = 0.75
    elif room in ("wilds_mine",):    # damp seams → uncommon
        chance = 0.35
    elif room in ("wilds_tower",):   # mossy shade → uncommon
        chance = 0.45
    else:
        game.say("You see nothing special to harvest here.")
        return True

    if r.random() < chance:
        _p7_add_mat(game, "glowcap", 1)
        game.say("You pluck a faintly glowing cap.")
    else:
        game.say("You search, but find only scraps.")
    return True

def _p7_cmd_cook(game, args) -> bool:
    if not game:
        print("Cooking imaginary food... (Base game not loaded)")
        return True
    if not _p7_here(game, "wilds_camp"):
        game.say("You need a safe fire to cook.")
        return True
    if not _p7_has_p3(game) or game._p3["mats"].get("fish", 0) <= 0:
        game.say("You have no fish to cook.")
        return True
    _p7_take_mat(game, "fish", 1)
    game.player.add_item(Item("meal", "Cooked Fish", "Hot and flaky. Restores more health.", usable=True))
    game.say("You grill a fish over the coals. (Gained Cooked Fish)")
    return True

def _p7_cmd_camp(game, args) -> bool:
    if not game:
        print("You nap in nowhere. (Base game not loaded)")
        return True
    # Safer rest at the Ranger Camp; elsewhere just a short rest
    if _p7_here(game, "wilds_camp"):
        heal = 4
        game.player.hp = min(game.player.max_hp, game.player.hp + heal)
        game.say(f"You rest at the camp and recover {heal} HP.")
    else:
        heal = 2
        game.player.hp = min(game.player.max_hp, game.player.hp + heal)
        game.say(f"You take a careful rest and recover {heal} HP.")
    return True

# Let cooked fish actually do something extra
def _p7_use_patch(game, name: str) -> bool:
    name = (name or "").lower()
    if name in ("meal", "cooked fish"):
        before = game.player.hp
        game.player.hp = min(game.player.max_hp, game.player.hp + 4)
        game.say(f"You eat the cooked fish. (+{game.player.hp - before} HP)")
        # remove item
        for k, it in list(game.player.inv.items()):
            if it.id == "meal" or it.name.lower() == "cooked fish":
                game.player.inv.pop(k, None)
                break
        return True
    return False

# ---------- NPC talk & quest offers (simple) ----------
def _p7_cmd_talk(game, args) -> bool:
    return False

# ---------- Quest helpers piggybacking Part 6 ----------
def _p7_cmd_give(game, args) -> bool:
    """give [item/mat] [npc]  -- supports fish/ore/glowcap and lost_ring to Trader."""
    if not args:
        return False
    text = " ".join(args).lower()
    # crude parse
    words = text.split()
    if len(words) < 2:
        game.say("Give what to whom? (e.g., give fish trader)")
        return True
    # assume last token is npc, the rest is item
    npc = words[-1]
    item = " ".join(words[:-1])

    # convenience map
    alias = {"the": "", "to": "", "a": "", "an": ""}
    item = " ".join([w for w in item.split() if w not in alias])

    # Trader quest & ring
    if npc in ("trader",):
        # Ring: trade for gold
        had_ring = None
        for k, it in list(game.player.inv.items()):
            if it.id == "lost_ring":
                had_ring = k
                break
        if had_ring:
            game.player.inv.pop(had_ring, None)
            if _p7_has_p3(game):
                game._p3["gold"] = game._p3.get("gold", 0) + 6
            game.say('Trader: "A lucky dredge! Here, 6 gold for your trouble."')
            return True
        # Fish for quest
        if item.startswith("fish"):
            q = game._p6["quests"].get("angler_aid")
            need = q["need"]["fish"]
            have = game._p3["mats"].get("fish", 0) if _p7_has_p3(game) else 0
            if q["state"] not in ("accepted", "completed"):
                game.say('Trader: "Ask proper-like: accept angler_aid."')
                return True
            if have < need:
                game.say('Trader: "Bring me two; this won’t do."')
                return True
            _p7_take_mat(game, "fish", need)
            q["state"] = "turned_in"
            # reward via Part 6 helper style
            if _p7_has_p3(game):
                game._p3["gold"] = game._p3.get("gold", 0) + 5
            if getattr(game, "_p2", None) is not None:
                game._p2["xp"] = game._p2.get("xp", 0) + 1
            game.say("You hand over the fish. The Trader pays in clinking coin. (+5g, +1 XP)")
            return True

    # Ranger: ore
    if npc in ("ranger",):
        if item.startswith("ore"):
            q = game._p6["quests"].get("mine_matters")
            need = q["need"]["ore"]
            have = game._p3["mats"].get("ore", 0) if _p7_has_p3(game) else 0
            if q["state"] not in ("accepted", "completed"):
                game.say('Ranger: "Say the word: accept mine_matters."')
                return True
            if have < need:
                game.say('Ranger: "Not enough ore yet."')
                return True
            _p7_take_mat(game, "ore", need)
            q["state"] = "turned_in"
            if _p7_has_p3(game):
                game._p3["gold"] = game._p3.get("gold", 0) + 4
            if getattr(game, "_p2", None) is not None:
                game._p2["xp"] = game._p2.get("xp", 0) + 1
            game.say("You pass over the ore. The Ranger nods, satisfied. (+4g, +1 XP)")
            return True

    # Hermit: glowcaps
    if npc in ("hermit",):
        if item.startswith("glowcap"):
            q = game._p6["quests"].get("hermit_glow")
            need = q["need"]["glowcap"]
            have = game._p3["mats"].get("glowcap", 0) if _p7_has_p3(game) else 0
            if q["state"] not in ("accepted", "completed"):
                game.say('Hermit: "Ask it right: accept hermit_glow."')
                return True
            if have < need:
                game.say('Hermit: "Not yet. The salve will not shine."')
                return True
            _p7_take_mat(game, "glowcap", need)
            q["state"] = "turned_in"
            if _p7_has_p3(game):
                game._p3["gold"] = game._p3.get("gold", 0) + 3
            if getattr(game, "_p2", None) is not None:
                game._p2["xp"] = game._p2.get("xp", 0) + 1
            game.say("The Hermit grins, mixing a gleaming paste. (+3g, +1 XP)")
            return True

    game.say("Nothing comes of that gift.")
    return True

# ---------- Hook into Part 6's quest acceptance text ----------
def _p7_cmd_accept(game, args) -> bool:
    if not game or not args:
        return False
    key = args[0].lower()
    if key in ("angler_aid", "mine_matters", "hermit_glow"):
        q = game._p6["quests"][key]
        if q["state"] in ("new", "offered"):
            q["state"] = "accepted"
            # Journal entry if Part 4 exists
            p4 = getattr(game, "_p4", None)
            if p4 is not None:
                p4["journal"].append(f"Accepted quest: {q['title']}.")
            game.say(f"Quest accepted: {q['title']}.")
            return True
    return False

def _p7_cmd_turnin(game, args) -> bool:
    """Support: turnin angler_aid — consumes 2 fish from mats or inventory."""
    if not game:
        print("You turn in nothing to no one. (Base game not loaded)")
        return True
    if not args:
        game.say("Turn in which quest? Try: turnin angler_aid")
        return True

    key = args[0].lower()
    if key != "angler_aid":
        return False  # let previous parts handle their own turn-ins

    # The new quests are stored in Part 6's quest list
    q = getattr(game, "_p6", {}).get("quests", {}).get("angler_aid")
    if not q:
        game.say("No such quest.")
        return True
    if q["state"] not in ("accepted", "completed"):
        game.say("You haven't accepted this quest.")
        return True

    # Count fish from Part 3 mats AND from inventory (if your fishing adds an item)
    mats_fish = game._p3["mats"].get("fish", 0) if getattr(game, "_p3", None) else 0
    inv_fish_keys = [k for k, it in game.player.inv.items()
                     if k == "fish" or it.name.lower() in ("fish", "fresh fish", "small fish")]

    total = mats_fish + len(inv_fish_keys)
    if total < 2:
        game.say("You haven’t caught enough fish yet.")
        return True

    # Consume 2 fish: prefer mats first, then inventory
    need = 2
    if getattr(game, "_p3", None) and mats_fish > 0:
        take = min(need, mats_fish)
        _p7_take_mat(game, "fish", take)
        need -= take
    while need > 0 and inv_fish_keys:
        game.player.remove_item(inv_fish_keys.pop())
        need -= 1

    # Reward (uses Part 6 helper; quest already defines reward {"gold":5,"xp":1})
    _p6_apply_reward(game, q.get("reward", {"gold": 5, "xp": 1}))
    q["state"] = "turned_in"
    game.say("You hand over the fish. The Trader pays in clinking coin.")
    return True

#def _p7_cmd_fish(game, args) -> bool:
#    """Wrapper for fishing at Moonlit Lake."""
 #   _p7_fish(game)
#    return True

# ---------- Fishing ----------
# ---------- Fishing ----------
def _p7_cmd_fish(game, args):
    # Must be at Moonlit Lake
    if not game or game.room().id != "wilds_lake":
        game.say("You can only fish at the Moonlit Lake.")
        return True

    import random
    roll = random.random()

    if roll < 0.20:
        game.say("Nothing bites.")
        return True
    elif roll < 0.95:
        # Prefer stackable materials (Part 3)
        if getattr(game, "_p3", None) is not None:
            mats = game._p3.setdefault("mats", {})
            mats["fish"] = mats.get("fish", 0) + 1
            game.say("You catch a small fish. (Fish +1)")
        else:
            # Fallback: add as an item if Part 3 isn't available
            game.player.add_item(Item("fish", "Fresh Fish", "A slippery, fresh-caught fish.", usable=False))
            game.say("You catch a small fish! (Added to inventory)")
    else:
        # Rare ring
        game.player.add_item(Item("lost_ring", "Lost Ring", "An old ring dredged from the depths.", usable=False))
        game.say("Glint! You dredge up a Lost Ring.")
    return True



# ---------- Dispatcher ----------
def p7_ext_handle_command(cmd, args, game):
    prev = P7_PREV_EXT if P7_PREV_EXT is not p7_ext_handle_command else None

    # Activities first
    if cmd == "fish":
        return _p7_cmd_fish(game, args)
    if cmd == "mine":
        return _p7_cmd_mine(game, args)
    if cmd == "harvest":
        return _p7_cmd_harvest(game, args)
    if cmd == "cook":
        return _p7_cmd_cook(game, args)
    if cmd == "camp":
        return _p7_cmd_camp(game, args)

    # NPC talk & giving
    if cmd == "talk":
        if _p7_cmd_talk(game, args):
            return True
        return prev(cmd, args, game) if prev else False

    if cmd == "give":
        return _p7_cmd_give(game, args)

    # Accept our new quests (coexists with Part 6 accept)
    if cmd == "accept":
        if _p7_cmd_accept(game, args):
            return True
        return prev(cmd, args, game) if prev else False

    # Enhance 'use' so cooked meals heal more
    if cmd == "use":
        if game and _p7_use_patch(game, " ".join(args)):
            return True
        return prev(cmd, args, game) if prev else False


    # Accept our new quests (coexists with Part 6 accept)
    if cmd == "accept":
        if _p7_cmd_accept(game, args):
            return True
        return prev(cmd, args, game) if prev else False

    # NEW: Turn in our quests (coexists with Part 6 turnin)
    if cmd == "turnin":
        if _p7_cmd_turnin(game, args):
            return True
        return prev(cmd, args, game) if prev else False


    # Fall through to previous parts
    return prev(cmd, args, game) if prev else False

# Register this part's handler as the new dispatcher
ext_handle_command = p7_ext_handle_command


# ===========================
# SINGLE RUNNER (place at end of file)
# ===========================
if __name__ == "__main__":
    try:
        Game().run()
    except NameError:
        # Fallback mini shell if Part 1 isn't present
        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                break
            if line in ("quit", "exit", "q"):
                break
            parts = line.split()
            if not parts:
                continue
            cmd, args = parts[0].lower(), parts[1:]
            handled = False
            if "ext_handle_command" in globals():
                try:
                    handled = ext_handle_command(cmd, args, None)
                except Exception as e:
                    print(f"[Extension error ignored] {e}")
            if not handled:
                print("Base game not loaded. Paste Part 1 to play.")
