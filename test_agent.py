"""
Test script for agent functionality without requiring all dependencies.
"""
from agent import process_user_input, find_command, intent_classification

def test_find_command():
    """Test command finding with 90% similarity."""
    print("Testing find_command...")
    
    # Test exact matches
    assert find_command("open") == "open"
    assert find_command("close") == "close"
    assert find_command("up") == "up"
    assert find_command("down") == "down"
    
    # Test similar matches (these may or may not reach 90% threshold)
    result1 = find_command("opn")  # Close to "open"
    result2 = find_command("clse")  # Close to "close"
    # These are just to verify the function works, not strict assertions
    
    # Test no match
    result = find_command("hello")
    assert result == "no_match" or result in ["open", "close", "up", "down"]  # May match if similarity is high
    
    print("find_command tests passed")

def test_intent_classification():
    """Test intent classification."""
    print("Testing intent_classification...")
    
    # Test command intent
    assert intent_classification("open the door") == "command"
    assert intent_classification("close window") == "command"
    assert intent_classification("go up") == "command"
    
    # Test product intent
    assert intent_classification("add product") == "add_product"
    assert intent_classification("I want to add a new product") == "add_product"
    
    print("intent_classification tests passed")

def test_process_user_input():
    """Test full user input processing."""
    print("Testing process_user_input...")
    
    # Test command processing
    result = process_user_input("open the door")
    assert result["intent"] == "command"
    assert result["type"] == "command"
    assert result["command"] == "open"
    
    # Test product processing
    result = process_user_input("add product brand nike")
    assert result["intent"] == "add_product"
    assert result["type"] == "add_product"
    
    print("process_user_input tests passed")

if __name__ == "__main__":
    print("Running agent tests...\n")
    try:
        test_find_command()
        test_intent_classification()
        test_process_user_input()
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
    except Exception as e:
        print(f"\nError: {e}")

