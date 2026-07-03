"""
Menu Sidekick Avoid List Generator - AI-Powered Safety Summary
================================================================

Generates personalized "Avoid List" summaries with quick tips based on dietary restrictions.
Creates simple, clear safety summaries for users to keep meals safe and joyful.

Backend Integration:
    from platter_designer import avoid_list_json
    
    response = avoid_list_json(
        eating_style=["Vegan"],
        allergies=["Nuts", "Dairy"],
        medical_conditions=["Diabetes"],
        magic_list=["Sugar", "Gluten"]
    )
    
    # Returns avoid list summary + quick tip
"""

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



class AvoidListGenerator:
    """
    AI-powered avoid list generator for creating personalized safety summaries.
    Generates creative avoid lists and quick tips based on dietary restrictions.
    """
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI client with configuration"""
        self.client = OpenAI(api_key=api_key)
        
        # Configuration
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.9)  # High creativity
        self.max_tokens = self.config.get('max_tokens', 1200)
    
    def _build_system_prompt(self, eating_style: List[str], allergies: List[str], 
                            medical_conditions: List[str], magic_list: List[str]) -> str:
        """
        Build dynamic system prompt for avoid list generation.
        """
        prompt_parts = [
            f"""You are a helpful food safety assistant creating personalized "Avoid List" summaries.

� YOUR MISSION:
Generate a clear, friendly "Avoid List (Summary for Quick Reference)" with 4-6 items to avoid.
Create a helpful "Quick Tip" that guides the user toward safe, delicious food choices.

⚡ CREATIVITY REQUIREMENT:
BE CREATIVE! Generate DIFFERENT avoid lists and tips each time based on the dietary profile.
Make it personal, warm, and helpful - like a friend helping them stay safe.

👤 USER DIETARY PROFILE:"""
        ]
        
        # Add eating styles
        if eating_style:
            prompt_parts.append(f"\n🥗 EATING STYLES:")
            for style in eating_style:
                prompt_parts.append(f"  • {style}")
        
        # Add allergies
        if allergies:
            prompt_parts.append(f"\n⚠️ ALLERGIES:")
            for allergy in allergies:
                prompt_parts.append(f"  • {allergy}")
        
        # Add medical conditions
        if medical_conditions:
            prompt_parts.append(f"\n🏥 MEDICAL CONDITIONS:")
            for condition in medical_conditions:
                prompt_parts.append(f"  • {condition}")
        
        # Add magic list
        if magic_list:
            prompt_parts.append(f"\n🚫 AVOID:")
            for item in magic_list:
                prompt_parts.append(f"  • {item}")
        
        # Add creation guidelines
        prompt_parts.extend([
            f"""

🎨 CREATION RULES:

1. AVOID LIST CREATION:
   - Generate 4-6 specific items to avoid based on the profile
   - Be clear and specific (e.g., "Dairy & milk (cheese, cream, butter)")
   - Group related items together
   - Use emojis (❌) for each avoid item
   - Make it easy to scan and remember

2. QUICK TIP CREATION:
   - Write ONE helpful tip (1-2 sentences)
   - Guide toward safe, delicious alternatives
   - Be warm, friendly, and encouraging
   - Include practical food suggestions
   - Use emoji (🌿 or ✨) to make it friendly

3. TONE & STYLE:
   - Friendly and supportive
   - Clear and simple
   - Safety-focused but positive
   - Helpful and practical

🎯 OUTPUT FORMAT (CRITICAL):
Return ONLY a valid JSON object with this EXACT structure:

{{
  "avoid_list": [
    "Dairy & milk (cheese, cream, butter)",
    "Meat, poultry, fish, eggs, honey",
    "Peanuts & peanut oils",
    "Shellfish (shrimp, crab, lobster)",
    "Refined sugar / sugary sauces"
  ],
  "quick_tip": "Stick to plant-based, dairy-free meals. Use olive oil, herbs, veggies, and grains—safe, fresh, and glowing ✨."
}}

REQUIRED FIELDS:
- avoid_list: Array of 4-6 specific items to avoid (strings)
- quick_tip: One helpful tip (1-2 sentences as a string)

⚠️ SAFETY GUIDELINES:
• If VEGAN: Avoid all animal products
• If VEGETARIAN: Avoid meat/fish
• If allergies present: Include those allergens prominently
• If DIABETIC: Mention sugar/refined carbs
• If HYPERTENSION: Mention high sodium items
• If GLUTEN-FREE: Mention wheat/gluten products

🎨 CREATIVITY GUIDELINES:
• Vary the avoid list items based on profile
• Create different quick tips each time
• Use different food suggestions (olive oil, herbs, grains, fruits, etc.)
• Keep it fresh, safe, and joyful
• Think about what would help THIS specific user

⭐ DIVERSITY GOAL:
Generate DIFFERENT avoid lists and tips each time!
Make each one feel personalized and helpful.

Now, create a helpful avoid list summary and quick tip for this user!
"""
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_user_prompt(self, eating_style: List[str], allergies: List[str],
                          medical_conditions: List[str], magic_list: List[str]) -> str:
        """Build user prompt with profile summary"""
        summary = f"""Create a personalized avoid list summary and quick tip for this profile:

Eating Styles: {', '.join(eating_style) if eating_style else 'None'}
Allergies: {', '.join(allergies) if allergies else 'None'}
Medical Conditions: {', '.join(medical_conditions) if medical_conditions else 'None'}
Avoid: {', '.join(magic_list) if magic_list else 'None'}

Generate a helpful, friendly avoid list and tip to keep meals safe and joyful!
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
    
    def generate_avoid_list(self, eating_style: List[str], allergies: List[str],
                           medical_conditions: List[str], magic_list: List[str]) -> Dict[str, Any]:
        """
        Generate personalized avoid list summary with quick tip.
        
        Args:
            eating_style: List of dietary preferences (e.g., ["Vegan"])
            allergies: List of allergens to avoid (e.g., ["Nuts", "Dairy"])
            medical_conditions: List of health conditions (e.g., ["Diabetes"])
            magic_list: List of ingredients to avoid (e.g., ["Sugar", "Gluten"])
        
        Returns:
            Dict with avoid_list array and quick_tip string
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            is_valid, error_msg = self._validate_inputs(eating_style, allergies, medical_conditions, magic_list)
            if not is_valid:
                raise ValueError(f"Invalid input: {error_msg}")
            
            logger.info("="*70)
            logger.info("🚫 Avoid List Generator - Creating Safety Summary")
            logger.info("="*70)
            logger.info(f"Eating Styles: {eating_style}")
            logger.info(f"Allergies: {allergies}")
            logger.info(f"Medical Conditions: {medical_conditions}")
            logger.info(f"Avoid List: {magic_list}")
            
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
            if 'avoid_list' not in result:
                raise ValueError("OpenAI response missing 'avoid_list' key")
            if 'quick_tip' not in result:
                raise ValueError("OpenAI response missing 'quick_tip' key")
            
            if not isinstance(result['avoid_list'], list):
                raise ValueError("'avoid_list' must be an array")
            
            avoid_count = len(result['avoid_list'])
            if avoid_count < 4 or avoid_count > 6:
                logger.warning(f"Expected 4-6 avoid items, got {avoid_count}")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Generated avoid list with {avoid_count} items in {processing_time:.2f}s")
            logger.info("="*70)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            return {
                "avoid_list": [],
                "quick_tip": "",
                "error": "Failed to parse AI response",
                "detail": str(e)
            }
        
        except Exception as e:
            logger.error(f"Error generating avoid list: {e}")
            logger.exception("Full traceback:")
            return {
                "avoid_list": [],
                "quick_tip": "",
                "error": "Avoid list generation failed",
                "detail": str(e)
            }


def avoid_list_json(eating_style: List[str], 
                   allergies: List[str],
                   medical_conditions: List[str],
                   magic_list: List[str],
                   config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Backend integration function for Django views.
    Generate personalized avoid list summary with quick tip.
    
    Args:
        eating_style: List of dietary preferences (e.g., ["Vegan"])
        allergies: List of allergens to avoid (e.g., ["Nuts", "Dairy"])
        medical_conditions: List of health conditions (e.g., ["Diabetes"])
        magic_list: List of ingredients to avoid (e.g., ["Sugar", "Gluten"])
        config: Optional configuration overrides
    
    Returns:
        Dict with avoid list and quick tip:
        {
            "avoid_list": [
                "Dairy & milk (cheese, cream, butter)",
                "Meat, poultry, fish, eggs, honey",
                "Peanuts & peanut oils",
                "Shellfish (shrimp, crab, lobster)",
                "Refined sugar / sugary sauces"
            ],
            "quick_tip": "Stick to plant-based, dairy-free meals. Use olive oil, herbs, veggies, and grains—safe, fresh, and glowing ✨."
        }
    
    Example Usage:
        profile = {
            "eating_style": ["Vegan"],
            "allergies": ["Nuts", "Dairy"],
            "medical_conditions": ["Diabetes"],
            "magic_list": ["Sugar", "Gluten"]
        }
        
        result = avoid_list_json(
            eating_style=profile['eating_style'],
            allergies=profile['allergies'],
            medical_conditions=profile['medical_conditions'],
            magic_list=profile['magic_list']
        )
        
        # Access avoid list
        print("🚫 Avoid List:")
        for item in result['avoid_list']:
            print(f"  ❌ {item}")
        print(f"\n🌿 Quick Tip: {result['quick_tip']}")
    """
    if config is None:
        config = {
            'model': 'gpt-4o',
            'temperature': 0.9,  # High creativity
            'max_tokens': 800
        }
    
    generator = AvoidListGenerator(api_key=OPENAI_API_KEY, config=config)
    result = generator.generate_avoid_list(eating_style, allergies, medical_conditions, magic_list)
    
    return result


# Test function
if __name__ == "__main__":
    # Example test
    print("🚫 Testing Avoid List Generator...")
    print("="*70)
    
    test_profile = {
        "eating_style": ["Vegan"],
        "allergies": ["Nuts", "Dairy"],
        "medical_conditions": ["Diabetes"],
        "magic_list": ["Sugar", "Gluten"]
    }
    
    result = avoid_list_json(
        eating_style=test_profile['eating_style'],
        allergies=test_profile['allergies'],
        medical_conditions=test_profile['medical_conditions'],
        magic_list=test_profile['magic_list']
    )
    
    print("\n📊 RESULT:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('avoid_list'):
        print(f"\n✅ Successfully generated avoid list!")
        print(f"\n🚫 Avoid List (Summary for Quick Reference)")
        for item in result['avoid_list']:
            print(f"❌ {item}")
        print(f"\n🌿 Quick Tip")
        print(f'"{result["quick_tip"]}"')
        print(f"\nThanks for helping keep this meal safe and joyful 💛")
    else:
        print("\n❌ No avoid list generated")
        if 'error' in result:
            print(f"Error: {result['error']}")
