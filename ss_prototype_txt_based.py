import time
import textwrap
import sys
import json
import os
from typing import Callable, Union, Dict, Any, Tuple

# --- Type Hinting for clarity ---
SceneFunction = Callable[[Dict[str, Any]], Union[Callable, str]]
PlayerState = Dict[str, Any]

# Global dictionary mapping function names (strings) to the functions themselves
SCENE_MAP: Dict[str, SceneFunction] = {} 

# --- Helper Functions ---

def force_save_prompt(player_state: PlayerState, current_scene_name: str, message: str):
    """Prompts the user to save the game after a major event, forcing them to press enter."""
    print_wrap("\n" + ("=" * 70), speed='fast')
    print_wrap(message, speed='fast')
    
    # Save automatically, but give the player a chance to see the message first
    input("Press Enter to save your progress...")
    save_game(player_state, current_scene_name, silent=False)
    print_wrap("=" * 70 + "\n", speed='fast')

def save_game(player_state: PlayerState, current_scene_name: str, silent: bool = False):
    """Saves the current player state and scene name to a JSON file."""
    try:
        data = {
            "player_state": player_state,
            "current_scene": current_scene_name
        }
        # Note: We must convert the 'flags' set to a list for JSON serialization
        data["player_state"]["flags"] = list(data["player_state"].get("flags", []))

        with open("sacred_stone_save.json", "w") as f:
            json.dump(data, f, indent=4)
            
        if not silent:
            print_wrap("\n--- Game Saved Successfully! ---", speed='fast')
    except Exception as e:
        print_wrap(f"Error saving game: {e}", speed='normal')

def load_game() -> Tuple[Union[PlayerState, None], Union[SceneFunction, None]]:
    """Loads the player state and scene from a JSON file."""
    try:
        if not os.path.exists("sacred_stone_save.json"):
            print_wrap("No save file found.", speed='normal')
            return None, None
            
        with open("sacred_stone_save.json", "r") as f:
            data = json.load(f)
            
        loaded_state: PlayerState = data["player_state"]
        scene_name = data["current_scene"]
        
        # Convert flags back to a set
        loaded_state["flags"] = set(loaded_state.get("flags", []))
            
        # Look up the function using the name from the SCENE_MAP
        if scene_name in SCENE_MAP:
            loaded_scene_func = SCENE_MAP[scene_name]
            print_wrap("\n--- Game Loaded Successfully! ---", speed='fast')
            return loaded_state, loaded_scene_func
        else:
            print_wrap(f"Error: Could not find scene '{scene_name}'. Starting new game.", speed='normal')
            return None, None

    except Exception as e:
        print_wrap(f"Error loading game: {e}. Starting new game.", speed='normal')
        return None, None

def print_wrap(text: str, width: int = 80, speed: str = 'normal'):
    """Prints text wrapped to the console with a typing effect."""
    if speed == 'normal':
        delay = 0.03
    elif speed == 'slow':
        delay = 0.08
    elif speed == 'fast':
        delay = 0.01
    elif speed == 'instant':
        delay = 0

    wrapped_text = textwrap.fill(text, width=width)
    
    if delay == 0:
        print(wrapped_text)
    else:
        for char in wrapped_text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

def get_choice(prompt: str, options: list[Tuple[str, SceneFunction]], allow_save: bool = False) -> Union[SceneFunction, str]:
    """Gets user input, validates it, and optionally allows saving the game."""
    all_options_count = len(options)
    
    print_wrap(prompt, speed='normal')
    
    for i, option in enumerate(options, 1):
        print_wrap(f"{i}: {option[0]}", speed='instant') 
        
    save_choice_number = -1
    if allow_save:
        save_choice_number = all_options_count + 1
        print_wrap(f"{save_choice_number}: Save Game", speed='instant')
        
    while True:
        valid_range_max = all_options_count
        
        if allow_save:
            choice_input = input(f"Enter number (1-{valid_range_max} or {save_choice_number} to save): ").strip()
        else:
            choice_input = input(f"Enter number (1-{valid_range_max}): ").strip()

        if not choice_input.isdigit():
            print("Invalid input. Please enter a number.")
            continue
            
        choice_number = int(choice_input)
        choice_index = choice_number - 1
        
        if allow_save and choice_number == save_choice_number:
            return "SAVE_GAME"
        
        if 0 <= choice_index < len(options):
            return options[choice_index][1]
        else:
            print(f"Invalid choice. Please enter a number between 1 and {valid_range_max}{f' or {save_choice_number}' if allow_save else ''}.")

def print_inventory(player_state: PlayerState) -> Union[SceneFunction, str]:
    """Prints the player's current inventory and allows saving."""
    print_wrap("\n--- INVENTORY ---", speed='instant')
    if not player_state["inventory"]:
        print_wrap("Your inventory is empty.", speed='instant')
    else:
        for item in player_state["inventory"]:
            print_wrap(f"- {item}", speed='instant')
    print_wrap(f"Sacred Shards: {player_state['shards']}/3", speed='instant')
    print_wrap("-----------------\n", speed='instant')
    
    choices = [
        ("Return to Map Hub", lambda: main_map_hub(player_state)),
    ]
    
    next_action = get_choice("Inventory Management", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def print_cutscene(lines: list[str], default_speed: str = 'slow'):
    """Prints lines of a cutscene one by one."""
    print("\n" + ("-" * 70))
    for line in lines:
        line_speed = default_speed
        pause = 1.0
        
        if line.startswith("*") and line.endswith("*"):
            line_speed = 'fast'
            pause = 0.5
        elif "..." in line or (line.startswith("𝘩") and line.endswith("??")):
            line_speed = 'slow'
            pause = 1.5
        elif line.isspace() or line == "--cutscene--":
            line_speed = 'instant'
            pause = 0.5
        
        print_wrap(line, speed=line_speed)
        time.sleep(pause)
    print(("-" * 70) + "\n")

# --- Game Logic Functions (Scenes) ---

def tutorial_hell(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("You adapt your eyes to the environment. Red skies, rivers of magma... you are definitely in hell.")
    print_wrap("You see a path forward, littered with obstacles and screeching demons in the distance.")
    
    choices = [
        ("Struggle forward towards a large, ominous structure (Satan's Lair).", lambda: satan_lair(player_state)),
        ("Stay put and weep.", lambda: game_over("You stayed still, and a horde of demons quickly overwhelmed you."))
    ]
    next_action = get_choice("What do you do?", choices, allow_save=True) 
    
    if next_action == "SAVE_GAME":
        return next_action 
    return next_action()

def satan_lair(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("\nYou push through the hostile land and arrive at a massive, obsidian fortress: 'Satan's Lair'. The gates creak open for you.")
    print_wrap("Inside, the air is thick with sulfur. You find yourself in a room with a series of levers and two doors: one marked with a 'Sun' (Light) and one with a 'Flame'.")
    print_wrap("A riddle is etched on the wall: 'I consume all, but drink no water. I fear the light, but am born from the dark. What am I?' (Answer: Fire)", speed='slow')
    
    choices = [
        ("Pull the lever under the 'Sun' door (Based on 'Fire fears light').", lambda: satan_fight(player_state)),
        ("Pull the lever under the 'Flame' door.", lambda: game_over("You pull the Flame lever. The riddle was a trick! A trapdoor opens, and you fall into magma.")),
    ]
    next_action = get_choice("Which lever do you pull?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def satan_fight(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("\nThe 'Sun' door opens! You enter a massive throne room. A towering, horned figure sits on a throne of bones.")
    print_wrap("'So, Nnog's cursed plaything arrives,' Satan bellows. 'You are not meant to be here! Begone!'", speed='fast')
    print_wrap("He leaps at you, claws extended!", speed='fast')
    print_wrap("You dodge and weave, using your wits and agility. You spot a loose stalactite above the throne.")
    
    choices = [
        ("Try to taunt Satan and lure him under the stalactite.", lambda: satan_escapes(player_state)),
        ("Attack him head-on.", lambda: game_over("You charge forward. Satan swats you aside like a fly. You are no match for him in a direct fight."))
    ]
    next_action = get_choice("How do you fight back?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def satan_escapes(player_state: PlayerState) -> Union[SceneFunction, str]:
    # Major Event - Victory/Acquisition
    print_wrap("\nYou lure Satan back to his throne. With a well-aimed rock, you strike the base of the stalactite. It crashes down!", speed='fast')
    print_wrap("Satan roars as it strikes his shoulder. He smashes a fist into the ground, creating a dark portal, and escapes through it.", speed='fast')
    print_wrap("Where he was standing, a glowing, pulsing object remains. You pick it up.")
    print_wrap(">>> Acquired: Shard of the Sacred Stone (1) <<<")
    player_state["shards"] += 1
    player_state["inventory"].append("Satan's Sacred Shard")
    
    # FORCED SAVE AFTER MAJOR EVENT
    force_save_prompt(player_state, "satan_escapes", "Satan has fled and you acquired the first Shard. Saving progress now!")

    print_wrap("The ground where Satan struck his portal crumbles away, revealing a massive, swirling vortex of wind below. It seems to be pulling you... upwards? Out of hell?")
    
    choices = [
        ("Leap into the vortex (Skydive).", lambda: skydive_to_castle(player_state)),
        ("Stay in hell.", lambda: game_over("You decide to stay. Eventually, Satan returns, and he is not happy to see you."))
    ]
    next_action = get_choice("What do you do?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def skydive_to_castle(player_state: PlayerState) -> SceneFunction:
    print_wrap("\nYou jump into the vortex. You are flung upwards, through rock and darkness, until you burst into a bright, blue sky. You are falling!", speed='fast')
    print_wrap("Below you is a massive green land. You aim for the courtyard of the **Central Castle (Imanu's Capital)** in the center of the world.")
    print_wrap("You land hard, but you are alive. You are back in the land of the living. Villagers and guards rush out.")
    print_wrap("You explain your story. An elder steps forward. 'If you seek to defeat Nnog, you must restore the Sacred Stone. We have hidden a key. It opens the path **EAST** to the Deep Forest where the Witch of the Woods resides. This path is your only way out to the wider world.'")
    print_wrap(">>> Acquired: Key to Deep Forest <<<")
    player_state["inventory"].append("Key to Deep Forest")
    
    # FORCED SAVE AFTER MAJOR EVENT
    force_save_prompt(player_state, "skydive_to_castle", "You have returned to Imanu and acquired the first key. Saving progress now!")
    
    return main_map_hub(player_state)

def main_map_hub(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("\nYou stand in the Central Castle Courtyard. You look upon the map of Imanu.")
    print_wrap("Your current objective is to collect all three Sacred Shards to confront Nnog.")
    
    choices: list[Tuple[str, SceneFunction]] = []
    
    # --- Check for Forest Cleared Flag ---
    forest_cleared = "defeated_dragon" in player_state["flags"]
    
    # --- EAST: Deep Forest (The Mandatory First Path) ---
    if not forest_cleared:
        # If the forest is NOT cleared, this is the only movement option (EAST)
        if "Key to Deep Forest" in player_state["inventory"]:
            choices.append(("Go **EAST** to the Deep Forest (Requires Key - Your only way forward).", lambda: deep_forest(player_state)))
        else:
            # If they somehow lost the key (or a bug), they're still forced East
            choices.append(("Go **EAST** (The path to the wider world is blocked by an Ancient Gate - You need the Key to Deep Forest).", lambda: main_map_hub(player_state)))
    else:
        # If the forest IS cleared, the other paths open up.
        
        # --- EAST (Already Cleared) ---
        choices.append(("Go **EAST** to the Deep Forest (Cleared).", lambda: main_map_hub(player_state)))

        # --- NORTH: Desert & Warp Shard's Lake ---
        if "defeated_water_eel" not in player_state["flags"]:
            choices.append(("Go **NORTH** towards the Desert and Warp Shard's Lake.", lambda: water_city_path(player_state)))
        else:
            choices.append(("Go **NORTH** (Path to Warp Shard's Lake is cleared).", lambda: main_map_hub(player_state)))

        # --- SOUTH: Foggy Forest & Mountains ---
        if "Key to Lightning Tower Area" in player_state["inventory"]:
            choices.append(("Go **SOUTH** towards the Foggy Forest and the mountains (Path is unlocked).", lambda: lightning_tower(player_state)))
        else:
            choices.append(("Go **SOUTH** towards the Foothills (Need to solve the 'screech' puzzle to advance).", lambda: explore_foothills(player_state)))
        
    # --- NORTH-EAST: Nnog's Volcanic Lair (Always visible, but locked by Shards) ---
    if player_state["shards"] >= 3:
        choices.append(("Go **NORTH-EAST** to Nnog's Volcanic Lair (Final Confrontation).", lambda: nnog_approach(player_state)))
    else:
        choices.append((f"Go **NORTH-EAST** to Nnog's Volcanic Lair (Requires {3 - player_state['shards']} more Shards).", lambda: nnog_approach(player_state)))
        
    # Utility
    choices.append(("[Check Inventory]", lambda: print_inventory(player_state)))
    
    next_action = get_choice("Where will you go?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()


def explore_foothills(player_state: PlayerState) -> SceneFunction:
    print_wrap("\nYou head south towards the Foggy Forest. You find ruined villages and a high population of monsters.")
    
    if "Key to Lightning Tower Area" in player_state["inventory"]:
        # Should not get here if the key is in inventory, but acts as a travel point
        print_wrap("The path to the mountains is now clear.")
        return main_map_hub(player_state)

    print_wrap("You see a path leading further south-east, towards a blizzard-covered mountain range, but a powerful force pushes you back. You need a key to proceed.")
    
    if "found_screech_poem" not in player_state["flags"]:
        print_wrap("You also find a small, ruined temple. Inside, a poem is etched on a stone:")
        print_wrap("'For the screech, requires a puzzle... For the biomes, in which it holds a key to a world in the sky.'", speed='slow')
        player_state["flags"].add("found_screech_poem")
        
    # After exploration, you go back to the hub to choose a new path.
    return main_map_hub(player_state)


def deep_forest(player_state: PlayerState) -> Union[SceneFunction, str]:
    if "Key to Deep Forest" in player_state["inventory"]:
        player_state["inventory"].remove("Key to Deep Forest")
        print_wrap("\nYou use the key to unlock a large, vine-covered gate. You enter the Deep Forest. It's a disorienting maze of identical-looking trees.")
        print_wrap("You wander for what feels like hours...", speed='slow')
        
        choices = [
            ("Follow the path with glowing mushrooms to the Witch's House.", lambda: meet_witch(player_state)),
            ("Follow the sound of running water.", lambda: game_over("You follow the water to a cliff. You slip on the moss and fall.")),
        ]
        next_action = get_choice("Which path do you take through the maze?", choices, allow_save=True)
        
        if next_action == "SAVE_GAME":
            return next_action
        return next_action()
    else:
        print_wrap("You need the Key to Deep Forest to enter this area.")
        return main_map_hub(player_state)


def meet_witch(player_state: PlayerState) -> Union[SceneFunction, str]:
    if "met_witch" not in player_state["flags"]:
        player_state["flags"].add("met_witch")
        print_wrap("\nYou follow the path and arrive in a clearing. A small, crooked hut sits in the center. An old woman, the witch, steps out.")
        print_wrap("'So, the one from the sky arrives,' she cackles. 'I have been waiting.'")
        print_wrap("She gives you a simple, but sharp, sword and potions. 'Take this. Beyond this is the Dragon's Maze. Good luck.'")
        print_wrap(">>> Acquired: Simple Sword, Health Potions <<<")
        player_state["inventory"].append("Simple Sword")
        player_state["inventory"].append("Health Potions")

        # FORCED SAVE AFTER MAJOR EVENT
        force_save_prompt(player_state, "meet_witch", "The Witch has given you weapons for the Dragon's Maze. Saving progress now!")

    else:
        print_wrap("You return to the Witch's House. She nods at you. 'Be careful in the maze.'")
    
    choices = [
        ("Enter the Dragon's Maze.", lambda: dragon_maze(player_state)),
        ("Return to the main map.", lambda: main_map_hub(player_state))
    ]
    next_action = get_choice("What will you do?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def dragon_maze(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("\nYou enter the second maze. It's darker, more menacing. You find skeletons of past 'sacrifices'.")
    print_wrap("You reach the center: a large, charred cavern. A sleeping dragon rests on a pile of gold.", speed='slow')
    
    choices = [
        ("Attack the dragon while it sleeps.", lambda: dragon_fight_win(player_state)),
        ("Try to sneak past the dragon.", lambda: game_over("You try to sneak. Your foot kicks a loose stone. The dragon awakens and incinerates you in a single breath.")),
    ]
    next_action = get_choice("The dragon is sleeping. What do you do?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def dragon_fight_win(player_state: PlayerState) -> SceneFunction:
    # Major Event - Victory/Acquisition
    player_state["flags"].add("defeated_dragon")
    print_wrap("\nYou charge forward, sword in hand, and plunge the blade deep into a gap in its scales. The dragon collapses, defeated.", speed='fast')
    print_wrap("Among the dragon's hoard, you find a strange, sand-colored key.")
    print_wrap(">>> Acquired: Key to the Desert <<<")
    player_state["inventory"].append("Key to the Desert")
    
    # FORCED SAVE AFTER MAJOR EVENT
    force_save_prompt(player_state, "dragon_fight_win", "The Dragon is defeated and you have the Key to the Desert. Saving progress now! The world map is now open.")
    
    print_wrap("\nA hidden tunnel leads back out of the forest.")
    return main_map_hub(player_state)

def water_city_path(player_state: PlayerState) -> Union[SceneFunction, str]:
    # Check added for completeness, but main_map_hub should handle the lock
    if "Key to the Desert" not in player_state["inventory"]:
        print_wrap("You need the Key to the Desert to pass the massive gate into the north.")
        return main_map_hub(player_state)
    
    if "defeated_water_eel" in player_state["flags"]:
        print_wrap("\nYou return to the Desert. The path is clear.")
        return main_map_hub(player_state)
        
    print_wrap("\nYou use the Key to the Desert to open the large northern gate. You trek through a vast desert, following a dried-up riverbed towards the **Warp Shard's Lake**.")
    print_wrap("You reach the Lake. Out in the water, you see a strange barrier of churning clouds.")
    print_wrap("You notice a small shrine on the beach. It has a slot... shaped just like Satan's Sacred Shard.")
    
    choices = [
        ("Place Satan's Sacred Shard into the shrine (1/3).", lambda: water_city(player_state)),
        ("Turn back.", lambda: main_map_hub(player_state))
    ]
    next_action = get_choice("What do you do?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def water_city(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("\nYou place the shard in the slot. It hums, and the barrier parts, revealing a path to a beautiful city under a glass dome: The Water City.")
    print_wrap("They tell you of the Ancient Water Eel that lives in a dungeon sealed by the 'Eel Tribe's' magic, which is based on their language (numbers).")
    print_wrap("An elder gives you a notepad. 'The dungeon is full of their trials. Notes: Fi (1), Ve (5), Na (9), To (2)'")
    print_wrap(">>> Acquired: Eel Tribe Language Notes <<<")
    player_state["inventory"].append("Eel Tribe Language Notes")
    
    choices = [
        ("Enter the Water Eel's dungeon.", lambda: water_dungeon(player_state)),
        ("Return to the surface.", lambda: main_map_hub(player_state))
    ]
    next_action = get_choice("Will you help them?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def water_dungeon(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("\nYou enter the dungeon. You reach a large, sealed door.")
    print_wrap("A carving says: 'Order the sacred numbers from least to greatest.'")
    print_wrap("There are four pedestals, labeled: Ve, To, Fi, Na")
    
    choices = [
        ("Press them in the order: Fi, To, Ve, Na (1, 2, 5, 9)", lambda: water_eel_fight(player_state)),
        ("Press them in the order: Ve, To, Fi, Na (5, 2, 1, 9)", lambda: game_over("Incorrect. The pedestals unleash a torrent of water, drowning you.")),
    ]
    next_action = get_choice("You check your notes (Fi=1, Ve=5, Na=9, To=2). How do you press the pedestals?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def water_eel_fight(player_state: PlayerState) -> SceneFunction:
    # Major Event - Victory/Acquisition
    print_wrap("\nThe door slides open! The Ancient Water Eel bursts from the sand, electricity crackling around it.", speed='fast')
    print_wrap("You fight the beast, striking when it's vulnerable. It shrieks and thrashes, smashing a hole in the southern wall and escaping into the open ocean.", speed='fast')
    print_wrap("In the sand where it was nested, you find another shard.")
    print_wrap(">>> Acquired: Shard of the Sacred Stone (2) <<<")
    player_state["shards"] += 1
    player_state["inventory"].append("Water Eel's Sacred Shard")
    player_state["flags"].add("defeated_water_eel")
    
    print_wrap("\nYou return to the Water City. The elder gives you a note: 'To the direction of it that has escaped, shall lead to the screech.' (Hint: South)")
    player_state["flags"].add("found_screech_note")
    
    # FORCED SAVE AFTER MAJOR EVENT
    force_save_prompt(player_state, "water_eel_fight", "The Water Eel is defeated and you have the second Shard. Saving progress now!")

    return main_map_hub(player_state)

def lightning_tower_path(player_state: PlayerState) -> Union[SceneFunction, str]:
    if "Key to Lightning Tower Area" in player_state["inventory"]:
        return lightning_tower(player_state)
    
    if "found_screech_note" not in player_state["flags"] or "found_screech_poem" not in player_state["flags"]:
        print_wrap("A powerful magical barrier blocks the path to the snowy mountains.")
        return main_map_hub(player_state)

    print_wrap("\nYou follow the clue: the path to the south (where the Eel escaped) leads back to the ruined temple in the foothills ('the screech').")
    print_wrap("You re-read the poem: 'For the screech, requires a puzzle... For the biomes, in which it holds a key to a world in the sky.'")
    
    choices = [
        ("The 'biomes' are the places I've been: Hell (Fire), Forest, Water. That must be the puzzle order.", lambda: lightning_key_maze(player_state)),
        ("I don't understand. I'll come back later.", lambda: main_map_hub(player_state))
    ]
    next_action = get_choice("What do you make of the poem?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def lightning_key_maze(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("\nYou notice three stones on the temple floor: one fiery red, one leafy green, one deep blue.")
    print_wrap("A plaque says: 'Press them in the order of your journey.' (Hell, Forest, Water)")
    
    choices = [
        ("Press: Red (Hell), Green (Forest), Blue (Water)", lambda: lightning_key_get(player_state)),
        ("Press: Green (Forest), Blue (Water), Red (Hell)", lambda: game_over("Incorrect. The stones shock you violently.")),
    ]
    next_action = get_choice("What is the order?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def lightning_key_get(player_state: PlayerState) -> SceneFunction:
    # Major Event - Acquisition
    print_wrap("\nCorrect! A hidden compartment opens. Inside is a key shaped like a thunderbolt.")
    print_wrap(">>> Acquired: Key to Lightning Tower Area <<<")
    player_state["inventory"].append("Key to Lightning Tower Area")
    
    print_wrap("\nYou use the key on the magical barrier. It dissipates, opening the path to the blizzard-covered mountains.")
    print_wrap("You find an ancient launcher device. It launches you straight up into the clouds! You land on a solid cloud, a city of marble floats in the sky.")
    
    # FORCED SAVE AFTER MAJOR EVENT
    force_save_prompt(player_state, "lightning_key_get", "You solved the Biome Puzzle and reached the Cloud City. Saving progress now!")

    choices = [
        ("Explore the cloud city and the Lightning Tower.", lambda: lightning_tower(player_state)),
        ("Try to jump back down.", lambda: game_over("You jump off the cloud. You fall for a very, very long time."))
    ]
    next_action = get_choice("You've arrived. What now?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def lightning_tower(player_state: PlayerState) -> SceneFunction:
    if "defeated_thunder_bird" in player_state["flags"]:
        print_wrap("The Lightning Tower is quiet. The Thunder Bird's nest is empty.")
        return main_map_hub(player_state)
        
    print_wrap("\nYou traverse the cloud bridges to the Lightning Tower, a massive spire crackling with energy.")
    print_wrap("You reach the peak. A massive **Thunder Bird**, crackling with lightning, descends from the sky.", speed='fast')
    print_wrap("You fight the powerful bird, using skill and agility to land the final blow. The bird explodes into a shower of sparks.", speed='fast')
    print_wrap("Where it fell, the final shard of the Sacred Stone appears.")
    print_wrap(">>> Acquired: Shard of the Sacred Stone (3) <<<")
    player_state["shards"] += 1
    player_state["inventory"].append("Thunder Bird's Sacred Shard")
    player_state["flags"].add("defeated_thunder_bird")
    
    # FORCED SAVE AFTER MAJOR EVENT
    force_save_prompt(player_state, "lightning_tower", "The Thunder Bird is defeated! You have all three Shards. Saving progress now!")

    print_wrap("You have all three shards. You feel a powerful pull towards **Nnog's Volcanic Lair**.")
    return main_map_hub(player_state)

def nnog_approach(player_state: PlayerState) -> Union[SceneFunction, str]:
    if player_state["shards"] < 3:
        if "tried_nnog_early" not in player_state["flags"]:
            print_wrap("\nYou travel to the top-right, to Nnog's Volcanic Lair. A massive, dark gate blocks your path. It has three empty slots.")
            print_wrap("You feel a powerful, dark energy pushing you back. You are not strong enough. The gate seems to require the three Sacred Shards.")
            player_state["flags"].add("tried_nnog_early")
        else:
            print_wrap("\nYou return to Nnog's gate. It still requires the three Sacred Shards to open.")
        return main_map_hub(player_state)
        
    print_wrap("\nYou have all three Sacred Shards. The path to Nnog's volcanic lair is open.")
    
    choices = [
        ("Place the three Sacred Shards into the gate.", lambda: nnog_castle(player_state)),
        ("Leave and prepare more. (Return to main map)", lambda: main_map_hub(player_state))
    ]
    next_action = get_choice("The final battle awaits. Are you ready?", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def nnog_castle(player_state: PlayerState) -> Union[SceneFunction, str]:
    print_wrap("\nThe shards click into place. The gate dissolves. The path to Nnog's castle is open. You fight your way through the darkness.")
    print_wrap("You finally reach the throne room. There, **Nnog**, a horrifying creature of shadow and spider-like legs, awaits.", speed='slow')
    
    # FORCED SAVE BEFORE FINAL BATTLE
    force_save_prompt(player_state, "nnog_castle", "You have found Nnog! This is your last chance to save before the final confrontation.")

    choices = [
        ("Face Nnog. (Final Battle)", lambda: nnog_fight(player_state)),
        ("Turn and run.", lambda: game_over("You turn to run, but Nnog is too fast. A web hits your back. Your story ends where it began."))
    ]
    next_action = get_choice("This is it. The end.", choices, allow_save=True)
    
    if next_action == "SAVE_GAME":
        return next_action
    return next_action()

def nnog_fight(player_state: PlayerState) -> SceneFunction:
    # Major Event - Victory
    print_wrap("\n'So, the cursed one returns,' Nnog hisses. 'You should have stayed in hell.'", speed='slow')
    print_wrap("You charge! You fight through the powerful attacks and spot the source of his power: a dark crystal in his chest.", speed='fast')
    print_wrap("With a final, desperate leap, you plunge your sword into the crystal.", speed='fast')
    print_wrap("Nnog screams and explodes into nothingness. He is defeated. You collapse, exhausted, but victorious.")
    
    # FORCED SAVE AFTER FINAL VICTORY
    force_save_prompt(player_state, "nnog_fight", "Nnog is defeated! You have saved Imanu! Saving progress now.")

    return end_game(player_state)

def end_game(player_state: PlayerState) -> str:
    """Credits and post-credit scene."""
    # ... (Credit scene logic remains the same)
    print_wrap("\nYou have saved the land of Imanu. Zen's curse is broken.")
    
    print_wrap("\n\n--- CREDITS ---", speed='normal')
    time.sleep(1)
    print_wrap("A Game by GamingGlobe 2025", speed='normal')
    time.sleep(1)
    print_wrap("Original Story by: [Your Name Here]", speed='normal')
    time.sleep(1)
    print_wrap("Text-Based Prototype by: Yusuf Shihab (and Gemini)", speed='normal')
    time.sleep(2)
    print_wrap("\n--- THE END ---", speed='normal')
    time.sleep(3)
    
    # Post-credit scene
    print_wrap("\n...\n...\n", speed='slow')
    print_wrap("After the credits finish, the screen is black.")
    print_wrap("You hear a rumbling sound...", speed='slow')
    print_wrap("A single line of text appears:")
    print_wrap("'The castle... it's... it's shaking...'", speed='slow')
    print_wrap("...Lava begins to rise from the cracks in Nnog's throne room...", speed='slow')
    print_wrap("\n(Hinting at Sacred Stone 2)")
    time.sleep(4)
    
    print_wrap("\nThank you for playing Sacred Stone Prototype!")
    input("Press Enter to return to the Title Screen...")
    return "MENU"

def game_over(message: str) -> str:
    """Prints a game over message and returns to menu."""
    print_wrap("\n" + ("#" * 70), speed='fast')
    print_wrap("GAME OVER", speed='fast')
    print_wrap(message, speed='normal')
    print_wrap(("#" * 70) + "\n", speed='fast')
    input("Press Enter to return to the Title Screen...")
    return "MENU"

# --- Main Game Execution ---

def _populate_scene_map():
    """Dynamically populates the SCENE_MAP with all scene functions."""
    global SCENE_MAP
    all_objects = globals()
    scene_functions = {name: func for name, func in all_objects.items() 
                       if callable(func) and not name.startswith('_') and name not in ['main_menu', 'run_game', 'game_over', 'end_game', 'print_wrap', 'get_choice', 'print_inventory', 'print_cutscene', 'save_game', 'load_game', 'force_save_prompt']}
    SCENE_MAP = scene_functions

def run_game(loaded_state: Union[PlayerState, None] = None, loaded_scene_func: Union[SceneFunction, None] = None):
    """Initializes and runs the main game loop."""
    
    if loaded_state and loaded_scene_func:
        player_state: PlayerState = loaded_state
        current_action: Union[SceneFunction, str] = loaded_scene_func
    else:
        player_state = {
            "inventory": [],
            "shards": 0,
            "flags": set()
        }
        
        print_cutscene([
            "𝒵𝑒𝓃 .. 𝒵𝑒𝓃 .. 𝒵𝐸N",
            "You hear a voice... You open your eyes... you are definitely in hell...",
            "Your last memory is of Nnog's web striking you...",
            "Nnog's curse echoes: 'You will not find peace in heaven, boy! You will know only the fire!'",
            "----------------------------------------------------------------------",
            "This brings us back to now — where Zen is."
        ])
        
        current_action = lambda: tutorial_hell(player_state)
    
    while current_action:
        if callable(current_action):
             current_scene_name = current_action.__name__
        else:
             current_scene_name = "Unknown" 

        if callable(current_action):
            next_action_result = current_action()
        elif current_action == "SAVE_GAME":
            next_action_result = "SAVE_GAME"
        else:
            print(f"Error: Unexpected non-callable action: {current_action}. Returning to menu.")
            break
            
        if next_action_result == "SAVE_GAME":
            # Saves and then returns to the current scene function
            save_game(player_state, current_scene_name, silent=False)
            
            if current_scene_name in SCENE_MAP:
                current_action = SCENE_MAP[current_scene_name]
            elif current_scene_name == "print_inventory":
                 current_action = lambda: main_map_hub(player_state)
            continue
        
        if next_action_result == "MENU":
            break
            
        current_action = next_action_result
        if not callable(current_action):
            # This handles end_game returning 'MENU' and game_over returning 'MENU'
            break
            
    print_wrap("\nReturning to menu...\n", speed='instant')


def main_menu():
    """The main menu loop with new Load Game option."""
    _populate_scene_map()
    
    print_wrap("Welcome to Sacred Stone Prototype (Text-Based Edition)!", speed='instant')
    print_wrap("You must be a developer to continue.\n", speed='instant')

    while True:
        has_save = os.path.exists("sacred_stone_save.json")
        
        print_wrap("Would you like to:", speed='instant')
        print_wrap("1: Start New Game", speed='instant')
        
        if has_save:
            print_wrap("2: Load Last Save", speed='instant')
            print_wrap("3: View Credits", speed='instant')
            print_wrap("4: Quit the game", speed='instant')
            max_option = 4
            load_option_number = 2
            credits_option_number = 3
        else:
            print_wrap("2: View Credits", speed='instant')
            print_wrap("3: Quit the game", speed='instant')
            max_option = 3
            load_option_number = -1
            credits_option_number = 2

        choice = input(f"Enter 1{f'-{max_option}' if max_option > 1 else ''}: ").strip()

        if choice == "1":
            print_wrap("\nStarting new game... (Prototype loading...)\n", speed='normal')
            run_game()
        
        elif choice == str(load_option_number) and has_save:
            loaded_state, loaded_scene_func = load_game()
            if loaded_state and loaded_scene_func:
                run_game(loaded_state, loaded_scene_func)
        
        elif choice == str(credits_option_number):
            print_wrap("\n© GamingGlobe 2025: All Rights Reserved", speed='instant')
            print_wrap("Coder/Developer: Yusuf Shihab\n", speed='instant')

            back = input("Would you like to return to the menu? (Yes/No): ").strip().lower()
            if back in ["no", "n"]:
                print_wrap("Exiting game... Goodbye!", speed='instant')
                break
            else:
                print_wrap("\nReturning to menu...\n", speed='instant')
        
        elif choice == str(max_option):
            print_wrap("\nExiting game... Goodbye!", speed='instant')
            break
            
        else:
            print_wrap("\nInvalid choice. Please enter a valid number.\n", speed='instant')

if __name__ == "__main__":
    main_menu()
