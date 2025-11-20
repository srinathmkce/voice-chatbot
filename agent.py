"""
Agent with tools for command detection and product addition.
"""
import difflib
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Available commands
COMMANDS = ["open", "close", "up", "down"]


def find_command(user_text: str) -> str:
    """
    Find a command from user text. Commands can be: open, close, up, or down.
    If the text matches 90% or more with any command, return that command.
    
    Args:
        user_text: The transcribed text from user voice input
        
    Returns:
        The matched command if similarity >= 90%, otherwise "no_match"
    """
    user_text_lower = user_text.lower().strip()
    
    # Check for exact match first
    if user_text_lower in COMMANDS:
        logger.info(f"Exact command match: {user_text_lower}")
        return user_text_lower
    
    # Check for partial matches (90% similarity threshold)
    best_match = None
    best_ratio = 0.0
    
    for command in COMMANDS:
        # Calculate similarity ratio
        ratio = difflib.SequenceMatcher(None, user_text_lower, command).ratio()
        
        # Also check if command is contained in user text
        if command in user_text_lower:
            ratio = max(ratio, 0.95)  # Boost if command word is found
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = command
    
    # Check if similarity meets 90% threshold
    if best_ratio >= 0.90:
        logger.info(f"Command matched: {best_match} (similarity: {best_ratio:.2%})")
        return best_match
    else:
        logger.info(f"No command match found (best: {best_match} with {best_ratio:.2%})")
        return "no_match"


def add_product(brand_name: str, product_name: str, sales_value: float, quantity: int) -> Dict[str, Any]:
    """
    Add a product with brand name, product name, sales value, and quantity.
    
    Args:
        brand_name: The brand name of the product
        product_name: The name of the product
        sales_value: The sales value (price) of the product
        quantity: The quantity of the product
        
    Returns:
        Dictionary with product information
    """
    product_info = {
        "brand_name": brand_name,
        "product_name": product_name,
        "sales_value": sales_value,
        "quantity": quantity
    }
    logger.info(f"Product added: {product_info}")
    return product_info


def intent_classification(user_text: str) -> str:
    """
    Classify user intent: check if user is trying to voice a command or add a product.
    
    Args:
        user_text: The transcribed text from user voice input
        
    Returns:
        "command" if user wants to execute a command, "add_product" if user wants to add a product
    """
    user_text_lower = user_text.lower().strip()
    
    # Keywords that suggest command intent
    command_keywords = ["open", "close", "up", "down", "move", "go", "turn", "switch", "activate"]
    
    # Keywords that suggest product addition intent
    product_keywords = ["add", "product", "brand", "sales", "quantity", "price", "item", "new product"]
    
    command_score = sum(1 for keyword in command_keywords if keyword in user_text_lower)
    product_score = sum(1 for keyword in product_keywords if keyword in user_text_lower)
    
    # Check if any command word appears
    for cmd in COMMANDS:
        if cmd in user_text_lower:
            command_score += 2  # Strong indicator
    
    if command_score > product_score:
        logger.info(f"Intent classified as: command (score: {command_score} vs {product_score})")
        return "command"
    elif product_score > command_score:
        logger.info(f"Intent classified as: add_product (score: {product_score} vs {command_score})")
        return "add_product"
    else:
        # Default to command if ambiguous
        logger.info(f"Intent ambiguous, defaulting to: command")
        return "command"




def process_user_input(user_text: str) -> Dict[str, Any]:
    """
    Process user input through the agent pipeline.
    
    Args:
        user_text: Transcribed text from user voice input
        
    Returns:
        Dictionary with result type and data
    """
    # Step 1: Classify intent
    intent = intent_classification(user_text)
    
    result = {
        "intent": intent,
        "transcribed_text": user_text
    }
    
    if intent == "command":
        # Step 2: Find the command
        command = find_command(user_text)
        if command != "no_match":
            result["type"] = "command"
            result["command"] = command
            result["message"] = f"Command detected: {command}"
        else:
            result["type"] = "error"
            result["message"] = "No matching command found. Available commands: open, close, up, down"
    
    elif intent == "add_product":
        # Step 3: Extract product information from text
        # This is a simplified extraction - in production, you'd use NLP or ask follow-up questions
        # For now, we'll try to extract from the text or return a message asking for more info
        result["type"] = "add_product"
        result["message"] = "To add a product, please provide: brand name, product name, sales value, and quantity. Please speak each piece of information clearly."
        
        # Try to extract basic info if present
        # This is a simple heuristic - in production, use proper NLP
        text_lower = user_text.lower()
        
        # Look for numbers that might be sales value or quantity
        numbers = re.findall(r'\d+\.?\d*', user_text)
        
        product_info = {
            "brand_name": None,
            "product_name": None,
            "sales_value": None,
            "quantity": None
        }
        
        # Simple keyword extraction (this is basic - production would need better NLP)
        if "brand" in text_lower:
            # Try to extract brand name after "brand"
            brand_idx = text_lower.find("brand")
            if brand_idx != -1:
                # Extract next few words
                words = user_text[brand_idx:].split()
                if len(words) > 1:
                    product_info["brand_name"] = words[1] if len(words) > 1 else None
        
        if numbers:
            if len(numbers) >= 2:
                product_info["sales_value"] = float(numbers[0])
                product_info["quantity"] = int(numbers[1])
            elif len(numbers) == 1:
                product_info["sales_value"] = float(numbers[0])
        
        # If we have some info, include it
        if any(product_info.values()):
            result["product_info"] = product_info
            result["message"] = f"Product information extracted: {product_info}. Please provide missing information if any."
    
    return result

