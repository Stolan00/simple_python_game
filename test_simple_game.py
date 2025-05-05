import unittest
from unittest.mock import patch, call
import io
import sys
import os

# Import the game script
import simple_game

# Use TestLoader for modern unittest compatibility
loader = unittest.TestLoader()

# --- Unit Test Class (Unchanged from previous version) ---
class TestSimpleGameUnit(unittest.TestCase):
    """Unit tests focusing on isolated functions."""
    # ... (keep all unit tests from the previous version) ...

    def test_format_text_bold(self):
        self.assertEqual(simple_game.format_text("Hello **World**!"), "Hello World!")
    def test_format_text_italic(self):
        self.assertEqual(simple_game.format_text("This is *important*."), "This is important.")
    def test_format_text_mixed(self):
        self.assertEqual(simple_game.format_text("**Bold** and *italic*."), "Bold and italic.")
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_init_game_resets_state(self, mock_stdout):
        simple_game.state = {"hasKey": True, "score": 10}
        simple_game.player = {"name": "OldName"}
        simple_game.init_game()
        self.assertEqual(simple_game.state, {})
        self.assertEqual(simple_game.player["name"], "Wanderer")
        self.assertIn("Simple Choice Game Initialized!", mock_stdout.getvalue())
    @patch('os.system')
    def test_clear_screen(self, mock_os_system):
        simple_game.clear_screen()
        if os.name == 'nt':
            mock_os_system.assert_called_once_with('cls')
        else:
            mock_os_system.assert_called_once_with('clear')
    def test_get_node_blue_room_no_key(self):
        simple_game.state = {}
        nodes = simple_game.get_text_nodes()
        blue_room_node = nodes["blueRoom"]()
        self.assertIn("find a small **key**!", blue_room_node["text"])
        self.assertEqual(len(blue_room_node["choices"]), 1)
        self.assertEqual(blue_room_node["choices"][0]["text"], "Take the key and go back")
        self.assertTrue(blue_room_node["choices"][0]["set_state"]["hasKey"])
    def test_get_node_blue_room_with_key(self):
        simple_game.state = {"hasKey": True}
        nodes = simple_game.get_text_nodes()
        blue_room_node = nodes["blueRoom"]()
        self.assertIn("already took the small key", blue_room_node["text"])
        self.assertEqual(len(blue_room_node["choices"]), 1)
        self.assertEqual(blue_room_node["choices"][0]["text"], "Go back")
        self.assertNotIn("set_state", blue_room_node["choices"][0])


# --- Integration Test Class (Updated) ---
class TestSimpleGameIntegration(unittest.TestCase):
    """Integration tests simulating game flow."""

    def setUp(self):
        with patch('sys.stdout', new_callable=io.StringIO):
             simple_game.init_game()

    @patch('builtins.input', side_effect=['1', 'TestPlayer', '1'])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_start_and_name_entry(self, mock_clear, mock_stdout, mock_input):
        """Integration Test 1: Start game, enter name, check greeting."""
        next_node_id, _ = simple_game.show_text_node("intro")
        self.assertEqual(next_node_id, "askName")
        next_node_id, _ = simple_game.show_text_node(next_node_id)
        self.assertEqual(next_node_id, "greeting")
        self.assertEqual(simple_game.player["name"], "TestPlayer")
        _, _ = simple_game.show_text_node(next_node_id)
        output = mock_stdout.getvalue()
        # --- *** FIX HERE *** ---
        self.assertIn("Hello, TestPlayer!", output) # Check for the formatted text
        # --- End of Fix ---
        self.assertIn("1. Open the red door", output)
        self.assertIn("2. Open the blue door", output)

    @patch('builtins.input', side_effect=['1'])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_get_key_from_blue_room(self, mock_clear, mock_stdout, mock_input):
        current_node_id = "blueRoom"
        self.assertFalse(simple_game.state.get("hasKey", False))
        next_node_id, choice_made = simple_game.show_text_node(current_node_id)
        self.assertTrue(simple_game.state.get("hasKey", False))
        self.assertEqual(next_node_id, "greeting")
        self.assertEqual(choice_made["text"], "Take the key and go back")
        output = mock_stdout.getvalue()
        self.assertIn("You find a small key!", output)
        self.assertIn("State updated: {'hasKey': True}", output)

    @patch('builtins.input', side_effect=['1'])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_red_room_without_key(self, mock_clear, mock_stdout, mock_input):
        simple_game.state = {}
        current_node_id = "redRoom"
        simple_game.show_text_node(current_node_id)
        output = mock_stdout.getvalue()
        self.assertIn("1. Go back", output)
        self.assertNotIn("Check for secrets", output)

    @patch('builtins.input', side_effect=['2'])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_red_room_with_key(self, mock_clear, mock_stdout, mock_input):
        simple_game.state = {"hasKey": True}
        current_node_id = "redRoom"
        next_node_id, choice_made = simple_game.show_text_node(current_node_id)
        output = mock_stdout.getvalue()
        self.assertIn("1. Go back", output)
        self.assertIn("2. Check for secrets (requires key)", output)
        self.assertEqual(next_node_id, "secretEnding")
        self.assertEqual(choice_made["text"], "Check for secrets (requires key)")

    @patch('builtins.input', side_effect=['1'])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_secret_ending_and_restart(self, mock_clear, mock_stdout, mock_input):
        simple_game.player["name"] = "Winner"
        simple_game.state = {"hasKey": True}
        current_node_id = "secretEnding"
        next_node_id, choice_made = simple_game.show_text_node(current_node_id)
        output = mock_stdout.getvalue()
        self.assertIn("Congratulations, Winner!", output)
        self.assertIn("1. Play Again?", output)
        self.assertIn("2. Quit", output)
        self.assertEqual(next_node_id, "restart")

    @patch('builtins.input', side_effect=['2', '1'])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_blue_door_first(self, mock_clear, mock_stdout, mock_input):
        simple_game.player["name"] = "BluePlayer"
        current_node_id = "greeting"
        next_node_id, choice_made = simple_game.show_text_node(current_node_id)
        self.assertEqual(next_node_id, "blueRoom")
        self.assertEqual(choice_made["text"], "Open the blue door")
        self.assertFalse(simple_game.state.get("hasKey", False))
        next_node_id, choice_made = simple_game.show_text_node(next_node_id)
        self.assertTrue(simple_game.state.get("hasKey", False))
        self.assertEqual(next_node_id, "greeting")
        self.assertEqual(choice_made["text"], "Take the key and go back")

    @patch('builtins.input', side_effect=['invalid', '99', '1'])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_invalid_choice_input(self, mock_clear, mock_stdout, mock_input):
        simple_game.player["name"] = "InputTester"
        current_node_id = "greeting"
        next_node_id, choice_made = simple_game.show_text_node(current_node_id)
        output = mock_stdout.getvalue()
        self.assertIn("Please enter the number of your choice.", output)
        self.assertIn("Invalid choice number.", output)
        self.assertEqual(next_node_id, "redRoom")
        self.assertEqual(choice_made["text"], "Open the red door")

    @patch('builtins.input', side_effect=['2'])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_quit_from_ending(self, mock_clear, mock_stdout, mock_input):
        simple_game.player["name"] = "Quitter"
        simple_game.state = {"hasKey": True}
        current_node_id = "secretEnding"
        next_node_id, choice_made = simple_game.show_text_node(current_node_id)
        output = mock_stdout.getvalue()
        self.assertIn("Congratulations, Quitter!", output)
        self.assertIn("1. Play Again?", output)
        self.assertIn("2. Quit", output)
        self.assertEqual(next_node_id, "quit")
        self.assertEqual(choice_made["text"], "Quit")


    @patch('builtins.input', side_effect=['q']) # Input 'q' to quit
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen')
    def test_integration_node_with_no_choices(self, mock_clear, mock_stdout, mock_input):
        """Integration Test (NEW): Cover node with no available choices."""
        # Ensure the deadEnd node exists in simple_game.py
        if "deadEnd" not in simple_game.get_text_nodes():
             self.skipTest("Skipping test: 'deadEnd' node not found in simple_game.py")

        current_node_id = "deadEnd"
        next_node_id, choice_made = simple_game.show_text_node(current_node_id)

        output = mock_stdout.getvalue()
        self.assertIn("You reached a dead end with no choices.", output)
        self.assertIn("There are no choices here.", output)
        self.assertIn("Q. Quit", output) # Check the fallback quit option display
        self.assertIsNone(choice_made) # No choice object should be returned
        self.assertEqual(next_node_id, "quit") # Should return 'quit' signal

    @patch('builtins.input', side_effect=[
        '1', 'MainPlayer', '2', '1', '1', '2', '2'
        # Intro 'Next', Name, Greeting 'Blue Door', BlueRoom 'Take Key',
        # Greeting 'Red Door', RedRoom 'Check Secrets', SecretEnding 'Quit'
    ])
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('simple_game.clear_screen') # Mock clear screen
    @patch('simple_game.init_game') # Mock init_game to prevent reset during main()
    def test_integration_full_playthrough_main(self, mock_init, mock_clear, mock_stdout, mock_input):
        """Integration Test (NEW): Test main game loop execution."""
        # Reset state manually since we mock init_game within main's scope
        simple_game.state = {}
        simple_game.player = {"name": "Wanderer"}

        simple_game.main() # Call the main function

        output = mock_stdout.getvalue()
        # Check for key phrases from the playthrough
        self.assertIn("Hello, MainPlayer!", output)
        self.assertIn("You find a small key!", output)
        self.assertIn("Congratulations, MainPlayer!", output)
        self.assertIn("Thanks for playing!", output) # Check the final quit message
        # Verify final state (optional, but good)
        self.assertTrue(simple_game.state.get("hasKey")) # Should have key at the end

# --- Test Execution Block (Unchanged) ---
if __name__ == '__main__':
    # ... (keep the execution block from the previous version) ...
    print("--- Discovering and running tests ---")
    suite = unittest.TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(TestSimpleGameUnit))
    suite.addTest(loader.loadTestsFromTestCase(TestSimpleGameIntegration))
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    print("\n--- Measuring and reporting coverage ---")
    try:
        from coverage import Coverage
        cov = Coverage(source=['simple_game'])
        cov.erase()
        cov.start()
        print("--- Re-running tests under coverage measurement (output suppressed) ---")
        suite_for_coverage = unittest.TestSuite()
        suite_for_coverage.addTest(loader.loadTestsFromTestCase(TestSimpleGameUnit))
        suite_for_coverage.addTest(loader.loadTestsFromTestCase(TestSimpleGameIntegration))
        runner_for_coverage = unittest.TextTestRunner(stream=io.StringIO())
        runner_for_coverage.run(suite_for_coverage)
        cov.stop()
        cov.save()
        print("\nCoverage Report:")
        coverage_percent = cov.report(show_missing=True, file=sys.stdout)
        html_report_dir = 'htmlcov'
        cov.html_report(directory=html_report_dir)
        print(f"\nHTML coverage report generated in '{html_report_dir}/index.html'")
        if coverage_percent is not None and coverage_percent >= 75.0:
            print(f"\nCoverage target of 75% MET ({coverage_percent:.2f}%)")
        elif coverage_percent is not None:
            print(f"\nCoverage target of 75% NOT MET ({coverage_percent:.2f}%)")
        else:
            print("\nCould not determine coverage percentage from report.")
    except ImportError:
        print("\nCoverage check skipped: 'coverage' package not installed.")
        print("Install it using: pip install coverage")
    except Exception as e:
        print(f"\nCould not run coverage: {e}")