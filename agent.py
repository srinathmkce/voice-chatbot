"""
Agent with tools for command detection and product addition.
"""
import difflib
import re
from typing import Dict, Any, Optional
import logging
import os

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
    
    # Strong product addition phrases (check these first)
    product_phrases = [
        "add product", "add a product", "add new product", "add the product",
        "i want to add", "i need to add", "add item", "add new item",
        "create product", "new product", "register product"
    ]
    
    # Check for strong product phrases first
    for phrase in product_phrases:
        if phrase in user_text_lower:
            logger.info(f"Intent classified as: add_product (matched phrase: '{phrase}')")
            return "add_product"
    
    # Keywords that suggest command intent
    command_keywords = ["open", "close", "up", "down", "move", "go", "turn", "switch", "activate"]
    
    # Keywords that suggest product addition intent (individual words)
    product_keywords = ["add", "product", "brand", "sales", "quantity", "price", "item"]
    
    command_score = sum(1 for keyword in command_keywords if keyword in user_text_lower)
    product_score = sum(1 for keyword in product_keywords if keyword in user_text_lower)
    
    # Check if any command word appears (exact commands get priority)
    for cmd in COMMANDS:
        if cmd in user_text_lower:
            # Only boost if it's likely a command, not part of "add product" context
            if "product" not in user_text_lower and "add" not in user_text_lower:
                command_score += 2  # Strong indicator
    
    # Boost product score if "add" appears with product-related words
    if "add" in user_text_lower and ("product" in user_text_lower or "item" in user_text_lower):
        product_score += 3
    
    if product_score > command_score:
        logger.info(f"Intent classified as: add_product (score: {product_score} vs {command_score})")
        return "add_product"
    elif command_score > product_score:
        logger.info(f"Intent classified as: command (score: {command_score} vs {product_score})")
        return "command"
    else:
        # If scores are equal, check if it's one of the exact commands
        for cmd in COMMANDS:
            if cmd == user_text_lower.strip():
                logger.info(f"Intent classified as: command (exact match: '{cmd}')")
                return "command"
        # Default to add_product if ambiguous and contains product-related words
        if product_score > 0:
            logger.info(f"Intent ambiguous but has product keywords, defaulting to: add_product")
            return "add_product"
        # Otherwise default to command
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
        # Step 3: Handle product addition workflow
        result["type"] = "add_product"
        
        # Try to extract product information from the text
        text_lower = user_text.lower().strip()
        product_info = {
            "brand_name": None,
            "product_name": None,
            "sales_value": None,
            "quantity": None
        }
        
        # Check if this is the initial "add product" request
        is_initial_request = any(phrase in text_lower for phrase in [
            "add product", "add a product", "add new product", "i want to add", "i need to add",
            "add item", "create product", "new product"
        ])
        
        # Extract brand name - look for patterns like "brand is X", "brand X", "brand name X"
        # Also handle simple responses like just "Nike" when asked for brand (but only if no numbers)
        brand_patterns = [
            r"brand\s+(?:name\s+)?(?:is\s+)?([a-z]+(?:\s+[a-z]+)*)",
            r"brand\s+([a-z]+(?:\s+[a-z]+)*)",
        ]
        for pattern in brand_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted = match.group(1).strip()
                # Skip if it's a common word or number
                if extracted and extracted not in ["is", "the", "a", "an", "it", "this", "that"]:
                    # If it's just a number, don't treat it as brand name
                    if not re.match(r'^\d+\.?\d*$', extracted):
                        product_info["brand_name"] = extracted
                        break
        
        # If no brand found with patterns, and text is simple (no numbers, no product/sales keywords), 
        # and it's a reasonable length, treat it as brand name
        if not product_info["brand_name"] and not re.search(r'\d', text_lower):
            # Check if it's a simple phrase without product-related keywords
            if not any(kw in text_lower for kw in ["product", "item", "price", "sales", "value", "quantity", "qty"]):
                words = text_lower.split()
                if 1 <= len(words) <= 3:  # Reasonable brand name length
                    # Make sure it's not just common words
                    if not all(w in ["is", "the", "a", "an", "it", "this", "that", "please", "tell", "me"] for w in words):
                        product_info["brand_name"] = " ".join(words)
        
        # Extract product name - look for patterns like "product is X", "product name X", "item X"
        product_patterns = [
            r"product\s+(?:name\s+)?(?:is\s+)?([a-z]+(?:\s+[a-z]+)*)",
            r"item\s+(?:is\s+)?([a-z]+(?:\s+[a-z]+)*)",
            r"product\s+([a-z]+(?:\s+[a-z]+)*)",
        ]
        for pattern in product_patterns:
            match = re.search(pattern, text_lower)
            if match:
                extracted = match.group(1).strip()
                if extracted and extracted not in ["is", "the", "a", "an", "it", "this", "that"]:
                    product_info["product_name"] = extracted
                    break
        
        # Extract sales value - look for patterns like "sales value X", "price X", "value X", "$X"
        # Also handle simple number responses
        sales_patterns = [
            r"sales\s+value\s+(?:is\s+)?\$?(\d+\.?\d*)",
            r"price\s+(?:is\s+)?\$?(\d+\.?\d*)",
            r"value\s+(?:is\s+)?\$?(\d+\.?\d*)",
            r"\$(\d+\.?\d*)",
            r"^(\d+\.?\d*)\s*dollars?$",  # "50 dollars"
            r"^(\d+\.?\d*)$",  # Simple number (if no other context)
        ]
        for pattern in sales_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1))
                    # Only assign if reasonable (not a quantity)
                    if value > 0 and value < 1000000:  # Reasonable price range
                        product_info["sales_value"] = value
                        break
                except ValueError:
                    pass
        
        # Extract quantity - look for patterns like "quantity X", "qty X", "X units"
        quantity_patterns = [
            r"quantity\s+(?:is\s+)?(\d+)",
            r"qty\s+(?:is\s+)?(\d+)",
            r"(\d+)\s+units?",
            r"^(\d+)$",  # Simple number (if no sales value was found)
        ]
        for pattern in quantity_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    qty = int(match.group(1))
                    # Only assign if reasonable
                    if qty > 0 and qty < 1000000:
                        # If we already have sales_value and this is a simple number, 
                        # check if it makes more sense as quantity
                        if product_info["sales_value"] is None or qty < product_info.get("sales_value", 0):
                            product_info["quantity"] = qty
                            break
                except ValueError:
                    pass
        
        # Determine what information is missing and ask for it
        missing_fields = []
        if not product_info["brand_name"]:
            missing_fields.append(("brand_name", "brand name"))
        if not product_info["product_name"]:
            missing_fields.append(("product_name", "product name"))
        if not product_info["sales_value"]:
            missing_fields.append(("sales_value", "sales value"))
        if not product_info["quantity"]:
            missing_fields.append(("quantity", "quantity"))
        
        if is_initial_request and len(missing_fields) == 4:
            # First step: ask for brand name
            result["message"] = "I'll help you add a product. First, please tell me the brand name."
            result["next_field"] = "brand_name"
        elif missing_fields:
            # Ask for the next missing field
            next_field_key, next_field_display = missing_fields[0]
            result["message"] = f"Please provide the {next_field_display}."
            result["next_field"] = next_field_key
        else:
            # All information collected
            result["product_info"] = product_info
            result["message"] = f"Great! I've collected all the information. Brand: {product_info['brand_name']}, Product: {product_info['product_name']}, Sales Value: ${product_info['sales_value']}, Quantity: {product_info['quantity']}."
            result["status"] = "complete"
        
        # Include partial product info if we have some
        if any(product_info.values()):
            result["product_info"] = product_info
    
    return result


def generate_response_text(agent_result: Dict[str, Any]) -> str:
    """
    Generate human-like response text based on agent result using OpenAI.
    For commands, generates text like "Running Open command".
    For product addition, generates appropriate confirmation text.
    
    Args:
        agent_result: Dictionary containing agent processing result
        
    Returns:
        Human-like response text string
    """
    result_type = agent_result.get("type", "unknown")
    
    # Try to use OpenAI if available and API key is set
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=openai_api_key)
            
            # Build context for OpenAI
            if result_type == "command":
                command = agent_result.get("command", "")
                if not command:
                    # Fallback for error case
                    return agent_result.get("message", "Command recognized, executing now")
                
                prompt = f"""You are a helpful voice assistant. The user just gave the command "{command}". 
Generate a natural, conversational response that confirms you're executing the command. 
Keep it short (one sentence, max 15 words) and friendly. 
Example: "Running Open command" or "Executing the Close command now"."""
                
            elif result_type == "add_product":
                product_info = agent_result.get("product_info", {})
                user_text = agent_result.get("transcribed_text", "")
                prompt = f"""You are a helpful voice assistant. The user is trying to add a product.
User said: "{user_text}"
Extracted product info: {product_info}
Generate a natural, conversational response that confirms what you understood or asks for missing information.
Keep it short (one sentence, max 20 words) and friendly."""
                
            else:
                # Fallback to simple response for errors
                return agent_result.get("message", "I apologize, but I couldn't process that request.")
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant. Be concise and natural in your responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.7
            )
            
            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Generated response text using OpenAI: {generated_text}")
            return generated_text
            
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {str(e)}. Using fallback response.")
            # Fall through to return simple response below
    
    # Fallback responses if OpenAI is not available or not configured
    if result_type == "command":
        command = agent_result.get("command", "")
        if command:
            return f"Running {command.capitalize()} command"
        else:
            return "Command recognized, executing now"
    
    elif result_type == "add_product":
        # Check if product addition is complete
        status = agent_result.get("status", "in_progress")
        if status == "complete":
            product_info = agent_result.get("product_info", {})
            brand = product_info.get("brand_name", "Unknown")
            product = product_info.get("product_name", "product")
            value = product_info.get("sales_value")
            quantity = product_info.get("quantity")
            
            response = f"Perfect! I've added the product: {product}"
            if brand and brand != "Unknown":
                response += f" from {brand}"
            if value:
                response += f" with sales value ${value}"
            if quantity:
                response += f" and quantity {quantity}"
            return response
        else:
            # Product addition in progress - use the message from agent_result
            return agent_result.get("message", "I'm ready to add a product. Please provide the brand name, product name, sales value, and quantity.")
    
    elif result_type == "error":
        return agent_result.get("message", "I apologize, but I couldn't process that request.")
    
    # Default fallback
    return agent_result.get("message", "I apologize, but I couldn't process that request.")

