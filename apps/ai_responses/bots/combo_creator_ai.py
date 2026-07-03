import json
from openai import OpenAI
from datetime import datetime
from typing import List, Dict, Any, Optional
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



class ComboCreator:
    """
    AI-powered food combo generator for platters.
    Creates ONE safe ingredient combination (4-7 items) based on dietary profile.
    """
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI client with configuration"""
        self.client = OpenAI(api_key=api_key)
        
        # Configuration
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.9)  # High creativity for variety
        self.max_tokens = self.config.get('max_tokens', 1000)
    
    def _build_system_prompt(self, eating_style: List[str], allergies: List[str], 
                            medical_conditions: List[str], magic_list: List[str]) -> str:
        """
        Build dynamic system prompt for combo generation.
        """
        prompt_parts = [
            f"""You are a creative and knowledgeable food platter designer and nutritionist AI.

🎯 YOUR MISSION:
Generate ONE beautiful, delicious, and SAFE food platter combo with 4-7 complementary ingredients.
The combo must respect the user's dietary restrictions and health requirements.

⚡ CREATIVITY REQUIREMENT:
BE CREATIVE! Generate DIFFERENT combinations each time. Don't repeat the same ingredients.
Think outside the box, explore various cuisines, and create unique pairings.
Each combo should feel fresh, exciting, and different from what you might have created before.

👤 USER DIETARY PROFILE:"""
        ]
        
        # Add eating styles
        if eating_style:
            prompt_parts.append(f"\n🥗 EATING STYLES:")
            for style in eating_style:
                prompt_parts.append(f"  • {style}")
            prompt_parts.append(f"  → Combo MUST align with these dietary preferences")
        
        # Add allergies (CRITICAL)
        if allergies:
            prompt_parts.append(f"\n⚠️ ALLERGIES (CRITICAL - ZERO TOLERANCE):")
            for allergy in allergies:
                prompt_parts.append(f"  • ❌ {allergy}")
            prompt_parts.append(f"  → NEVER include these allergens")
        
        # Add medical conditions
        if medical_conditions:
            prompt_parts.append(f"\n🏥 MEDICAL CONDITIONS:")
            for condition in medical_conditions:
                prompt_parts.append(f"  • {condition}")
            prompt_parts.append(f"  → Create health-conscious combo suitable for these conditions")
        
        # Add magic list (ingredients to avoid)
        if magic_list:
            prompt_parts.append(f"\n🚫 INGREDIENTS TO AVOID:")
            for item in magic_list:
                prompt_parts.append(f"  • {item}")
            prompt_parts.append(f"  → Do NOT use these ingredients")
        
        # Add creation guidelines
        prompt_parts.extend([
            f"""

🎨 COMBO CREATION RULES:

1. SAFETY FIRST:
   - NEVER use ingredients that contain user's allergens
   - Respect all eating styles (e.g., vegan combos have NO animal products)
   - Consider medical conditions (e.g., diabetic-friendly = low sugar)
   - Avoid all items in the magic list

2. COMBO STRUCTURE:
   - Create ONE beautiful platter combo with 4-7 complementary ingredients
   - Select ingredients that work well together
   - Include emojis for each ingredient to make it visual and appealing
   - Make combo practical and easy to assemble

3. PLATTER DESIGN PRINCIPLES:
   - Balance flavors: sweet, salty, savory, tangy
   - Mix textures: crunchy, creamy, soft, crispy
   - Include colors: make it visually appealing
   - Ensure ingredients pair well together
   - Consider portion balance

4. INGREDIENT SELECTION:
   - Choose 4-7 ingredients (random number in this range)
   - Select accessible, common ingredients
   - Avoid overly exotic items unless necessary
   - Ensure ingredients are widely available
   - Consider seasonality when possible

5. EMOJI USAGE:
   - Each ingredient MUST have an emoji
   - Use food emojis: 🥑🍅🥒🧀🥖🥕🫒🥜🌿🍋
   - Make it fun and visual
   - Help users visualize the platter

🎯 OUTPUT FORMAT (CRITICAL):
Return ONLY a valid JSON object with this EXACT structure:

{{
  "combo": [
    {{"name": "🥑 Avocado"}},
    {{"name": "🍅 Cherry Tomatoes"}},
    {{"name": "🥒 Cucumber"}},
    {{"name": "🫒 Olives"}},
    {{"name": "🌿 Fresh Basil"}}
  ]
}}

ONE combo with 4-7 complementary ingredients.
Each ingredient is an object with "name" field containing emoji + ingredient name.

⚠️ CRITICAL SAFETY RULES:
• Double-check EVERY ingredient against allergies
• If user is VEGAN: No meat, dairy, eggs, honey
• If user is VEGETARIAN: No meat, fish (dairy/eggs OK)
• If user is PESCATARIAN: No meat (fish/seafood OK)
• If user is KETO: Low-carb, high-fat ingredients
• If user is GLUTEN-FREE: No wheat, barley, rye
• If DIABETIC in conditions: Low glycemic index foods
• If HYPERTENSION in conditions: Low sodium options

🎨 CREATIVITY GUIDELINES:
• Think outside the box while staying safe
• Mix cuisines creatively (Mediterranean, Asian, Latin, etc.)
• Include unexpected but delicious pairings
• Make combo unique and exciting - AVOID repeating common combinations
• Focus on taste, health, and visual appeal
• Vary your selections - explore different food groups
• Consider seasonal and regional variations
• Be imaginative with flavor profiles

⭐ DIVERSITY GOAL:
Generate DIFFERENT ingredients each time, even with the same dietary profile.
Explore the full range of safe options available to create variety.

Now, create ONE amazing, beautifully decorated, and SAFE food platter combo for this user!
"""
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_user_prompt(self, eating_style: List[str], allergies: List[str],
                          medical_conditions: List[str], magic_list: List[str]) -> str:
        """Build user prompt with profile summary"""
        summary = f"""Generate ONE unique food platter combo with 4-7 complementary ingredients based on this profile:

Eating Styles: {', '.join(eating_style) if eating_style else 'None'}
Allergies: {', '.join(allergies) if allergies else 'None'}
Medical Conditions: {', '.join(medical_conditions) if medical_conditions else 'None'}
Avoid: {', '.join(magic_list) if magic_list else 'None'}

Create a diverse, delicious, and SAFE combination!
"""
        return summary
    
    def _validate_inputs(self, eating_style, allergies, medical_conditions, magic_list) -> tuple[bool, Optional[str]]:
        """Validate input structure"""
        try:
            # Ensure all inputs are lists
            if not isinstance(eating_style, list):
                return False, "eating_style must be a list"
            if not isinstance(allergies, list):
                return False, "allergies must be a list"
            if not isinstance(medical_conditions, list):
                return False, "medical_conditions must be a list"
            if not isinstance(magic_list, list):
                return False, "magic_list must be a list"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def generate_combo(self, eating_style: List[str], allergies: List[str],
                       medical_conditions: List[str], magic_list: List[str]) -> Dict[str, Any]:
        """
        Generate ONE safe food combo for platter with 4-7 ingredients.
        
        Args:
            eating_style: List of dietary preferences (e.g., ["Vegan", "Keto"])
            allergies: List of allergens to avoid (e.g., ["Nuts", "Dairy"])
            medical_conditions: List of health conditions (e.g., ["Diabetes"])
            magic_list: List of ingredients to avoid (e.g., ["Sugar", "Gluten"])
        
        Returns:
            Dict with combo array containing 4-7 food ingredients
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            is_valid, error_msg = self._validate_inputs(eating_style, allergies, medical_conditions, magic_list)
            if not is_valid:
                raise ValueError(f"Invalid input: {error_msg}")
            
            logger.info("="*70)
            logger.info("🍽️  Combo Creator - Generating Platter Combo")
            logger.info("="*70)
            logger.info(f"Eating Styles: {eating_style}")
            logger.info(f"Allergies: {allergies}")
            logger.info(f"Medical Conditions: {medical_conditions}")
            logger.info(f"Magic List (Avoid): {magic_list}")
            
            # Build prompts
            system_prompt = self._build_system_prompt(eating_style, allergies, medical_conditions, magic_list)
            user_prompt = self._build_user_prompt(eating_style, allergies, medical_conditions, magic_list)
            
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
            if 'combo' not in result:
                raise ValueError("OpenAI response missing 'combo' key")
            
            if not isinstance(result['combo'], list):
                raise ValueError("'combo' must be an array")
            
            combo_length = len(result['combo'])
            if combo_length < 4 or combo_length > 7:
                logger.warning(f"Expected 4-7 ingredients, got {combo_length}")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Generated combo with {combo_length} ingredients in {processing_time:.2f}s")
            logger.info("="*70)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            return {
                "combo": [],
                "error": "Failed to parse AI response",
                "detail": str(e)
            }
        
        except Exception as e:
            logger.error(f"Error generating combo: {e}")
            logger.exception("Full traceback:")
            return {
                "combo": [],
                "error": "Combo generation failed",
                "detail": str(e)
            }


def combo_created_json(eating_style: List[str], 
                       allergies: List[str],
                       medical_conditions: List[str],
                       magic_list: List[str],
                       config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Backend integration function for Django views.
    Generate ONE safe food platter combo with 4-7 ingredients based on dietary restrictions.
    
    Args:
        eating_style: List of dietary preferences (e.g., ["Vegan", "Pescatarian"])
        allergies: List of allergens to avoid (e.g., ["Nuts", "Dairy"])
        medical_conditions: List of health conditions (e.g., ["Diabetes", "Hypertension"])
        magic_list: List of ingredients to avoid (e.g., ["Dairy", "Gluten"])
        config: Optional configuration overrides
    
    Returns:
        Dict with 'combo' array containing 4-7 food ingredients:
        {
            "combo": [
                {"name": "🍅 Cherry Tomatoes"},
                {"name": "🥒 Cucumber"},
                {"name": "🥑 Avocado"},
                {"name": "🫒 Olives"},
                {"name": "🌿 Fresh Basil"}
            ]
        }
    
    Example Usage:
        profile = {
            "eating_style": ["Vegan", "Pescatarian"],
            "allergies": ["Nuts", "Dairy"],
            "medical_conditions": ["Diabetes", "Hypertension"],
            "magic_list": ["Dairy", "Gluten"]
        }
        
        result = combo_created_json(
            eating_style=profile['eating_style'],
            allergies=profile['allergies'],
            medical_conditions=profile['medical_conditions'],
            magic_list=profile['magic_list']
        )
        
        # Access combo
        combo = result['combo']
        print("Platter Combo:")
        for ingredient in combo:
            print(f"  {ingredient['name']}")
    """
    if config is None:
        config = {
            'model': 'gpt-4o',
            'temperature': 0.9,  # High creativity for variety
            'max_tokens': 1000
        }
    
    creator = ComboCreator(api_key=OPENAI_API_KEY, config=config)
    result = creator.generate_combo(eating_style, allergies, medical_conditions, magic_list)
    
    return result


