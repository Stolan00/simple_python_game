import sys
import os

# --- Game Data (Translated from JavaScript) ---

# Using dictionaries to represent state and player
state = {}
player = {"name": "Wanderer"}

def get_text_nodes():
    """
    Returns a dictionary mapping node IDs to functions that return node data.
    Using functions allows dynamic text/choices based on state.
    """
    # Need to access the global state and player variables
    global state
    global player

    return {
        "intro": lambda: {
            "id": "intro",
            "text": "Welcome! This is a tiny demonstration.\n\nPlease make  a choice.",
            "hide_back_button": True, # Not used in console, but kept for parity
            "choices": [
                {"text": "Next", "next_text": "askName"}
            ]
        },

        "askName": lambda: {
            "id": "askName",
            "text": "What is your name?",
            "input_prompt": "Enter your name: ", # Specific prompt for input
            "next_text": "greeting",
            "after_enter": lambda user_input: player.update({"name": user_input.strip() or "Wanderer"}) # Update player dict
        },

        "greeting": lambda: {
            "id": "greeting",
            "text": f"Hello, **{player['name']}**! You find yourself in a room with two doors.\nOne is *red*, the other is *blue*.",
            "choices": [
                {"text": "Open the red door", "next_text": "redRoom"},
                {"text": "Open the blue door", "next_text": "blueRoom"}
            ]
        },

        "redRoom": lambda: {
            "id": "redRoom",
            "text": "You enter a room that is entirely red. It feels warm.\nThere's nothing else obvious here.",
            "choices": [
                {"text": "Go back", "next_text": "greeting"},
                {
                    "text": "Check for secrets (requires key)",
                    "required_state": lambda current_state: current_state.get("hasKey", False) is True,
                    "next_text": "secretEnding"
                }
            ]
        },

        "blueRoom": lambda: {
            "id": "blueRoom",
            "text": (
                "You are back in the blue room. It feels cool.\nYou already took the small key."
                if state.get("hasKey") else
                "You enter a room that is entirely blue. It feels cool.\nYou find a small **key**!"
            ),
            "choices": (
                [
                    {"text": "Go back", "next_text": "greeting"}
                ] if state.get("hasKey") else
                [
                    {
                        "text": "Take the key and go back",
                        "set_state": {"hasKey": True},
                        "next_text": "greeting"
                    }
                ]
            )
        },

        "secretEnding": lambda: {
            "id": "secretEnding",
            "text": f"Using the key you found in the blue room, you unlock a hidden panel in the red room!\n\n**Congratulations, {player['name']}!** You found the secret exit!",
            "choices": [
                {"text": "Play Again?", "next_text": "restart"},
                {"text": "Quit", "next_text": "quit"}
            ]
        },

        "deadEnd": lambda: {
            "id": "deadEnd",
            "text": "You reached a dead end with no choices.",
            "choices": [] # Empty choices list
        }
    }

# --- Game Engine Logic ---

def clear_screen():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_text(text):
    """Basic formatting (replace markdown-like tags)."""
    return text.replace("**", "").replace("*", "")

def init_game():
    """Initializes the game state."""
    global state, player
    print("Simple Choice Game Initialized!")
    state = {}
    player = {"name": "Wanderer"} # Reset player name

def show_text_node(node_id):
    """Displays the text and choices for a given node."""
    global state # We might modify state via choices

    text_nodes = get_text_nodes() # Get the latest node definitions
    if node_id not in text_nodes:
        print(f"Error: Node '{node_id}' not found!")
        return None, None # Indicate error

    node_func = text_nodes[node_id]
    node = node_func() # Execute the function to get the node data

    clear_screen()
    print("--- The Simple Choice ---")
    print(format_text(node["text"]))
    print("-" * 25)

    # Handle direct input nodes
    if node.get("input_prompt"):
        user_input = input(node.get("input_prompt", "> "))
        if node.get("after_enter"):
            node["after_enter"](user_input)
        return node.get("next_text"), None # Return next node ID, no choice made

    # Handle choice-based nodes
    available_choices = []
    if "choices" in node:
        for i, choice in enumerate(node["choices"]):
            # Check if choice is conditional and condition met
            if "required_state" in choice:
                if not choice["required_state"](state):
                    continue # Skip this choice if condition not met
            available_choices.append(choice)
            print(f"{i + 1}. {format_text(choice['text'])}")

    if not available_choices:
         print("\nThere are no choices here.")
         print("Q. Quit")


    # Get player choice
    while True:
        selection = input("> ").strip().lower()
        if selection == 'q' and not available_choices:
             return "quit", None

        if selection.isdigit():
            choice_index = int(selection) - 1
            if 0 <= choice_index < len(available_choices):
                chosen_option = available_choices[choice_index]

                # Update state if specified by the choice
                if "set_state" in chosen_option:
                    state.update(chosen_option["set_state"])
                    print(f"(State updated: {chosen_option['set_state']})") # Debugging

                return chosen_option.get("next_text"), chosen_option # Return next node ID and the choice made
            else:
                print("Invalid choice number.")
        else:
            print("Please enter the number of your choice.")


# --- Main Game Loop ---

def main():
    """Runs the main game loop."""
    play_again = True
    while play_again:
        init_game()
        current_node_id = "intro" # Start node

        while current_node_id not in ["quit", "restart"]:
            next_node_id, choice_made = show_text_node(current_node_id)

            if next_node_id is None: # Handle node not found error
                 print("A problem occurred. Exiting game.")
                 current_node_id = "quit"
                 break

            if next_node_id == "restart":
                break # Exit inner loop to restart

            if next_node_id == "quit":
                current_node_id = "quit" # Ensure outer loop exits if player chooses quit
                break # Exit inner loop


            current_node_id = next_node_id

        # End of a game round
        if current_node_id == "quit":
            play_again = False
            print("\nThanks for playing!")
        else: # Assumed restart
             print("\nRestarting game...")
             # No need to ask, secretEnding choice leads directly to restart or quit

if __name__ == "__main__":
    main()