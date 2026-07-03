import json
from openai import OpenAI
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from core.settings import OPENAI_API_KEY

# Configure logging
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(handler)




class OCRMenuAnalyzer:
    """
    Fully dynamic OCR menu analyzer using OpenAI.
    Analyzes restaurant menus and food items based on user's dietary profile.
    """
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI client with configuration"""
        self.client = OpenAI(api_key=api_key)
        
        # Dynamic configuration
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.3)  # Lower for consistency
        self.max_tokens = self.config.get('max_tokens', 4000)
    
    def _build_system_prompt(self, profile: Dict[str, Any]) -> str:
        """
        Build dynamic system prompt for menu analysis based on user profile.
        """
        profile_name = profile.get('profile_name', 'User')
        eating_styles = profile.get('eating_style', [])
        allergies = profile.get('allergies', [])
        medical_conditions = profile.get('medical_conditions', [])
        magic_list = profile.get('magic_list', [])
        strict_level = profile.get('strict_level', 'Balanced')
        
        prompt_parts = [
            f"""You are an expert food safety and nutrition AI assistant analyzing restaurant menus for {profile_name}.

🎯 YOUR MISSION:
Analyze menu items from OCR-extracted text and determine if each dish is SAFE, CAUTION, or UNSAFE based on the user's dietary profile.

👤 USER PROFILE - {profile_name.upper()}:
• Dietary Strictness: {strict_level}"""
        ]
        
        # Add eating styles
        if eating_styles:
            prompt_parts.append(f"\n🥗 DIETARY PREFERENCES:")
            for style in eating_styles:
                prompt_parts.append(f"  • {style}")
        
        # Add allergies (CRITICAL)
        if allergies:
            prompt_parts.append(f"\n⚠️ ALLERGIES (CRITICAL - ZERO TOLERANCE):")
            for allergy in allergies:
                prompt_parts.append(f"  • ❌ {allergy}")
            prompt_parts.append("  → If ANY trace of these allergens exists, mark as UNSAFE")
        
        # Add medical conditions
        if medical_conditions:
            prompt_parts.append(f"\n🏥 MEDICAL CONDITIONS:")
            for condition in medical_conditions:
                prompt_parts.append(f"  • {condition}")
        
        # Add magic list
        if magic_list:
            prompt_parts.append(f"\n🔍 INGREDIENTS TO WATCH:")
            magic_preview = magic_list[:15]
            for item in magic_preview:
                prompt_parts.append(f"  • {item}")
            if len(magic_list) > 15:
                prompt_parts.append(f"  • ... and {len(magic_list) - 15} more")
        
        prompt_parts.extend([
            f"""

📋 ANALYSIS RULES:

1. DOCUMENT VALIDATION & TITLE:
   - First, determine if this is a restaurant menu by looking for food items and menu structure
   - If it's not a menu, set document_title to "Not a restaurant menu" and return empty food_items array
   - If it is a menu:
     a) Try to extract the restaurant name from header/branding/title
     b) If no restaurant name found, generate a descriptive title based on:
        * Type of cuisine (Italian, French, Asian, etc.)
        * Type of menu (Breakfast, Lunch, Dinner, etc.)
        * Restaurant type (Bistro, Cafe, Fine Dining, etc.)
        * Menu section focus (Dessert Menu, Wine List, etc.)
     c) Examples of AI-generated titles:
        * "French Bistro Dinner Menu"
        * "Italian Fine Dining Selection"
        * "Asian Fusion Lunch Menu"
        * "Cafe Breakfast and Brunch Menu"
        * "Mediterranean Restaurant Menu"
   
2. FOOD ITEM DETECTION:
   - Extract ALL food/drink items from the OCR text
   - Include appetizers, entrees, sides, desserts, beverages
   - Ignore prices, phone numbers, addresses
   - Detect items even if formatting is messy
   - Keep in mind that french name must be present in the output as it's a French app

2. INGREDIENT ANALYSIS:
   - For each food item, identify key ingredients based on common recipes
   - Match ingredients against user's restrictions (allergies, diet, magic list)
   - Be thorough - consider hidden ingredients (sauces, cooking oils, garnishes)

3. SAFETY MARKING:
   - UNSAFE: Contains user's allergens OR severely conflicts with medical conditions
   - CAUTION: Contains ingredients from magic list OR conflicts with eating style
   - SAFE: No concerning ingredients detected

4. INGREDIENT MARKS WITH MATCHING EMOJIS:
   - List each detected ingredient with its safety mark and matching emoji
   - ingredient: emoji + name of the ingredient
   - EMOJI MATCHING RULES - Use the emoji that best describes the ACTUAL INGREDIENT:
     * 🥬 vegetables (lettuce, spinach, broccoli, etc.)
     * 🍅 tomato and tomato products
     * 🥕 orange vegetables (carrots, sweet potato, pumpkin)
     * 🧅 onion, garlic, leeks
     * 🌶️ spicy ingredients (chili, hot peppers, sriracha)
     * 🥔 potatoes and starchy vegetables
     * 🍚 rice and grains
     * 🌾 wheat, barley, gluten-containing grains
     * 🍖 meat, beef, pork, poultry (chicken, turkey, duck)
     * 🐟 fish and seafood
     * 🦐 shellfish (shrimp, crab, lobster, mussels)
     * 🥚 eggs
     * 🥛 milk, cream, dairy products
     * 🧀 cheese
     * 🥜 peanuts
     * 🌰 tree nuts (almonds, walnuts, cashews)
     * 🥥 coconut
     * 🫘 beans and legumes (lentils, chickpeas)
     * 🍌 fruits
     * 🍯 honey, sugar, sweeteners
     * 🧈 butter, oils, fats
     * 🌱 vegan/plant-based alternatives
     * ❌ allergen (user's specific allergen)
     * ⚠️ watch ingredient (from magic list)
   - mark: "unsafe" | "caution" | "safe"
   - Example: "🦐 Shrimp" not "🍖 Shrimp"
   - Example: "🌾 Wheat flour" not "🍖 Wheat flour"

5. AI RECOMMENDATIONS WITH EMOJI:
   - Start with relevant emoji matching the overall assessment:
     * ✨ for SAFE items - perfect match
     * 🌿 for SAFE items - healthy/aligned option
     * ⚠️ for CAUTION items - needs modification
     * ❌ for UNSAFE items - must avoid
   - Provide brief, personalized guidance for the user
   - If UNSAFE: Use ❌ emoji and clearly warn about allergen risk
   - If CAUTION: Use ⚠️ emoji and explain the concern with suggestions
   - If SAFE: Use ✨ or 🌿 emoji and confirm alignment with their profile
   - Example formats:
     * "✨ Perfect match for your dietary needs! This gluten-free preparation aligns perfectly with your profile."
     * "⚠️ Almost safe, just tweak it a little - ask the chef to prepare without butter."
     * "❌ Not a match for you - contains peanuts which you're allergic to."

6. TIPS WITH EMOJI:
   - Start with 💡 emoji
   - Provide practical advice for ordering this item
   - Suggest questions to ask the server
   - Recommend modifications if applicable
   - Example: "💡 Ask the kitchen to prepare without the cream sauce and use olive oil instead."

7. FRENCH NAME (if applicable):
   - If the dish has a French/international name, include it
   - Leave empty string if not applicable

8. SAFETY TOTALS:
   - Count and track the following totals:
     * total_safe_items: Number of food items marked as "safe"
     * total_unsafe_items: Number of food items marked as "unsafe"
     * total_caution_items: Number of food items marked as "caution"
   - Base these counts on the final food_mark for each item
   - Include these totals in the response even if they are 0

🎯 OUTPUT FORMAT (CRITICAL):
Return ONLY a valid JSON object with this EXACT structure:

{{
  "document_title": "Descriptive title generated by AI (e.g., 'Italian Restaurant Menu', 'French Bistro Dinner Menu', 'Cafe Breakfast Selection', etc.)",
  "total_safe_items": 0,
  "total_unsafe_items": 0,
  "total_caution_items": 0,
  "food_items": [
    {{
      "food_title": "Dish Name",
      "french_name": "French name must be present, if not applicable translate real name to french",
      "ingredients_marks": [
        {{
          "ingredient": "🦐 shrimp",
          "mark": "safe" | "caution" | "unsafe"
        }},
        {{
          "ingredient": "🌾 wheat",
          "mark": "safe" | "caution" | "unsafe"
        }}
      ],
      "ai_recommendations": "✨ Perfect match for your dietary needs! This dish aligns perfectly with your profile.",
      "tips": "💡 Ask the kitchen to prepare without butter for a safer preparation.",
      "food_mark": "safe" | "caution" | "unsafe"
    }}
  ]
}}

⚠️ CRITICAL SAFETY RULES:
• ALWAYS mark items with user's allergens as "unsafe"
• Be conservative - if unsure, mark as "caution"
• Don't guess - if ingredients are unclear, note in recommendations
• Prioritize user safety over variety
• Consider cross-contamination risks for severe allergies
• Always include appropriate MATCHING emojis in ingredient names, ai_recommendations, and tips
• The emoji MUST match the actual ingredient (e.g., 🦐 for shrimp, not 🍖)

🔥 REMEMBER:
• Analyze EVERY food/drink item found in the text
• Be thorough with ingredient detection
• Provide actionable, personalized guidance with correct emojis
• Safety is the absolute priority
• Return ONLY valid JSON - no extra text
• Match emojis to actual ingredients accurately

Now analyze the menu for {profile_name}!
"""
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_user_prompt(self, extracted_text: str) -> str:
        """Build the user prompt with OCR text"""
        return f"""Analyze this restaurant menu (extracted via OCR):

---OCR TEXT START---
{extracted_text}
---OCR TEXT END---

Extract all food and beverage items, analyze each against my dietary profile, and return the JSON response.
"""
    
    def _validate_inputs(self, profile: Dict, extracted_text: str) -> tuple[bool, Optional[str]]:
        """Validate input structure"""
        try:
            if not isinstance(profile, dict):
                return False, "profile_payload must be a dictionary"
            
            if not isinstance(extracted_text, str):
                return False, "extracted_text must be a string"
            
            if not extracted_text.strip():
                return False, "extracted_text cannot be empty"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def analyze_menu(self, profile: Dict[str, Any], extracted_text: str) -> Dict[str, Any]:
        """
        Analyze OCR-extracted menu text against user profile.
        
        Args:
            profile: User profile with eating_style, allergies, medical_conditions, magic_list
            extracted_text: OCR-extracted text from menu image
        
        Returns:
            Dict with ai_reply array containing analyzed food items
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            is_valid, error_msg = self._validate_inputs(profile, extracted_text)
            if not is_valid:
                raise ValueError(f"Invalid input: {error_msg}")
            
            logger.info("="*70)
            logger.info("🍽️  OCR Menu Analyzer - Starting Analysis")
            logger.info("="*70)
            logger.info(f"Profile: {profile.get('profile_name', 'Unknown')}")
            logger.info(f"OCR Text Length: {len(extracted_text)} characters")
            logger.info(f"Eating Styles: {profile.get('eating_style', [])}")
            logger.info(f"Allergies: {profile.get('allergies', [])}")
            logger.info(f"Medical Conditions: {profile.get('medical_conditions', [])}")
            
            # Build prompts
            system_prompt = self._build_system_prompt(profile)
            user_prompt = self._build_user_prompt(extracted_text)
            
            logger.info(f"Calling OpenAI API ({self.model})...")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            logger.info(f"Received OpenAI response: {len(content)} characters")
            
            result = json.loads(content)
            
            # Validate response structure
            required_fields = ['document_title', 'total_safe_items', 'total_unsafe_items', 'total_caution_items', 'food_items']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"OpenAI response missing '{field}' key")
            
            if not isinstance(result['food_items'], list):
                raise ValueError("'food_items' must be an array")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Analysis complete in {processing_time:.2f}s")
            logger.info(f"Found {len(result['food_items'])} food items")
            logger.info(f"Safety Summary: {result['total_safe_items']} safe, {result['total_unsafe_items']} unsafe, {result['total_caution_items']} caution")
            logger.info("="*70)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            return {
                "document_title": "Error: Failed to Parse Menu",
                "total_safe_items": 0,
                "total_unsafe_items": 0,
                "total_caution_items": 0,
                "food_items": [],
                "error": "Failed to parse AI response",
                "detail": str(e)
            }
        
        except Exception as e:
            logger.error(f"Error in menu analysis: {e}")
            logger.exception("Full traceback:")
            return {
                "document_title": "Error: Menu Analysis Failed",
                "total_safe_items": 0,
                "total_unsafe_items": 0,
                "total_caution_items": 0,
                "food_items": [],
                "error": "Menu analysis failed",
                "detail": str(e)
            }


def generate_ocr_analysis(profile_payload: Dict[str, Any], 
                          extracted_text: str,
                          config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Backend integration function for Django OCR view.
    Analyzes OCR-extracted menu text against user's dietary profile.
    
    Args:
        profile_payload: User profile dict with eating_style, allergies, medical_conditions, etc.
        extracted_text: OCR-extracted text from restaurant menu
        config: Optional configuration overrides
    
    Returns:
        Dict containing analyzed menu with document title and food items:
        {
            "document_title": "French Bistro Dinner Menu",
            "total_safe_items": 5,
            "total_unsafe_items": 2,
            "total_caution_items": 3,
            "food_items": [
                {
                    "food_title": "Grilled Salmon",
                    "french_name": "Saumon Grillé",
                    "ingredients_marks": [
                        {"ingredient": "fish", "mark": "safe"}
                    ],
                    "ai_recommendations": "This dish appears compatible...",
                    "tips": "Ask about cooking method...",
                    "food_mark": "safe"
                },
                ...
            ]
        }
    
    Example:
        profile = {
            "eating_style": ["vegetarian"],
            "allergies": ["peanuts", "shellfish"],
            "medical_conditions": ["diabetes"],
            "magic_list": ["Sugar", "High-Carb Foods"],
            "profile_name": "John",
            "strict_level": "Balanced"
        }
        
        ocr_text = "MENU\\nGrilled Salmon - $18.99\\nChicken Parmesan - $16.99..."
        
        result = generate_ocr_analysis(profile, ocr_text)
        ai_reply = result['ai_reply']  # Array of analyzed food items
    """
    if config is None:
        config = {
            'model': 'gpt-4o-mini',
            'temperature': 0.3,
            'max_tokens': 8000
        }
    
    analyzer = OCRMenuAnalyzer(api_key=OPENAI_API_KEY, config=config)
    result = analyzer.analyze_menu(profile_payload, extracted_text)
    
    return result