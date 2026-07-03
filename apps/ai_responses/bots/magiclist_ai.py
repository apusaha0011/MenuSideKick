import json
from openai import OpenAI
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

from core.settings import OPENAI_API_KEY

# Configure logging to stderr so stdout remains available for JSON output
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(handler)



class DynamicMagicListGenerator:
    """
    Fully dynamic and adaptive food recommendation generator.
    Works with ANY input format that follows the basic structure:
    - eating_style: list of dietary preferences with strictness levels
    - allergies: list of allergens to avoid
    - medical_conditions: list of health conditions to consider
    
    The bot dynamically adapts to ANY values, not hardcoded keywords.
    """
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI client with dynamic configuration"""
        self.client = OpenAI(api_key=api_key)
        
        # All configuration is dynamic and can be overridden
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-4.1')
        self.temperature = self.config.get('temperature', 0.1)
        self.seed = self.config.get('seed', 42)
        self.max_tokens = self.config.get('max_tokens', 1500)
        self.max_items = self.config.get('max_items', 10)  # Minimum 20 ingredients
        self.max_name_words = self.config.get('max_name_words', 4)
        self.output_filename = self.config.get('output_filename', 'magic_list_output.json')
    
    # fetch_user_preferences and post_user_preferences methods removed - not needed for backend integration
    
    def _build_dynamic_system_prompt(self) -> str:
        """Build fully dynamic system prompt that adapts to any input"""
        return """You are an expert AI nutritionist and dietary consultant with comprehensive knowledge of:
- ALL types of diets and eating styles (vegan, keto, paleo, Mediterranean, carnivore, raw food, etc.)
- ALL types of food allergies and intolerances
- ALL medical conditions that require dietary modifications
- Global cuisines and food cultures
- Modern and traditional dietary practices

YOUR CORE MISSION:
Generate safe, healthy, and personalized food recommendations that STRICTLY adhere to ALL provided restrictions.

CRITICAL SAFETY PRINCIPLES (NON-NEGOTIABLE):
1. ABSOLUTE PRIORITY: User safety comes first, always
2. If you receive an allergy, NEVER recommend foods containing that allergen or any cross-reactive foods
3. If you receive a medical condition, recommend ONLY foods that are medically appropriate
4. If you receive a dietary preference, respect it according to the strictness level provided
5. When multiple restrictions overlap, find the safe intersection - never compromise safety for variety
6. If restrictions are extremely limiting, provide fewer but SAFE options rather than risky ones

DYNAMIC ADAPTATION:
- You will receive dietary preferences, allergies, and medical conditions
- These can be ANYTHING - common or uncommon, standard or unique
- DO NOT assume you know what they mean - use your full knowledge base
- Research and apply current nutritional science for each restriction
- Consider cultural, regional, and personal variations in dietary practices

STRICTNESS LEVELS (adapt your recommendations accordingly):
- STRICT: Follow the restriction absolutely, no exceptions, no flexibility
- BALANCED: Follow the restriction with some practical flexibility for modern life
- FLEXIBLE: General adherence to the spirit of the restriction, occasional exceptions acceptable

OUTPUT REQUIREMENTS:
- Provide 8-15 specific, actionable food items or simple dishes
- Each item should be practical and accessible
- Include variety in nutrients, flavors, and food groups
- Consider meal diversity (proteins, vegetables, grains, snacks, etc.)
- Make recommendations culturally diverse when appropriate
- Ensure all items are clearly described (e.g., "Grilled salmon with herbs" not just "fish")

RESPONSE FORMAT:
Return ONLY a valid JSON object:
{
  "magic_list": ["item 1", "item 2", ..., "item N"]
}

Do not include explanations, notes, or additional text. Only the JSON object."""

    def _analyze_and_build_context(self, preferences: Dict) -> str:
        """
        Dynamically analyze input and build context for OpenAI.
        This method doesn't rely on hardcoded mappings - it builds
        intelligent context from whatever input is provided.
        """
        eating_styles = preferences.get('eating_style', [])
        allergies = preferences.get('allergies', [])
        medical_conditions = preferences.get('medical_conditions', [])
        
        context_parts = []
        
        # Dynamic header
        context_parts.append("🔍 USER PROFILE ANALYSIS")
        context_parts.append("=" * 60)
        
        # Process eating styles dynamically
        if eating_styles:
            context_parts.append("\n📊 DIETARY PREFERENCES:")
            for i, style in enumerate(eating_styles, 1):
                name = style.get('name', 'unspecified')
                strictness = style.get('strict_level', 'balanced')
                
                context_parts.append(f"\n{i}. {name.upper()} Diet")
                context_parts.append(f"   Strictness Level: {strictness.upper()}")
                context_parts.append(f"   Interpretation: Apply all principles of '{name}' dietary practice")
                context_parts.append(f"   Flexibility: {self._interpret_strictness(strictness)}")
        else:
            context_parts.append("\n📊 DIETARY PREFERENCES: No specific diet specified (omnivore default)")
        
        # Process allergies dynamically
        if allergies:
            context_parts.append("\n\n⚠️ CRITICAL ALLERGEN RESTRICTIONS:")
            context_parts.append("These items and ALL related products MUST be completely avoided:")
            for i, allergy in enumerate(allergies, 1):
                allergy_clean = str(allergy).strip()
                context_parts.append(f"\n{i}. ❌ {allergy_clean.upper()}")
                context_parts.append(f"   Action Required: Exclude {allergy_clean} and all derivatives")
                context_parts.append(f"   Cross-contamination: Consider risk and avoid")
                context_parts.append(f"   Label reading: Check all processed foods for traces")
        else:
            context_parts.append("\n\n⚠️ ALLERGEN RESTRICTIONS: None reported")
        
        # Process medical conditions dynamically
        if medical_conditions:
            context_parts.append("\n\n🏥 MEDICAL DIETARY CONSIDERATIONS:")
            context_parts.append("Recommendations must support management of these conditions:")
            for i, condition in enumerate(medical_conditions, 1):
                condition_clean = str(condition).strip()
                context_parts.append(f"\n{i}. {condition_clean.upper()}")
                context_parts.append(f"   Requirement: Follow evidence-based dietary guidelines for {condition_clean}")
                context_parts.append(f"   Approach: Conservative, medically sound recommendations")
        else:
            context_parts.append("\n\n🏥 MEDICAL CONDITIONS: None reported")
        
        # Add dynamic instructions
        context_parts.append("\n\n" + "=" * 60)
        context_parts.append("📋 YOUR TASK:")
        context_parts.append("=" * 60)
        
        # Build dynamic requirements list
        requirements = []
        
        if eating_styles:
            requirements.append(f"✓ Align with ALL {len(eating_styles)} dietary preference(s) specified")
        
        if allergies:
            requirements.append(f"✓ Completely avoid ALL {len(allergies)} allergen(s) - ZERO tolerance")
        
        if medical_conditions:
            requirements.append(f"✓ Support dietary needs for ALL {len(medical_conditions)} medical condition(s)")
        
        requirements.extend([
            "✓ Provide 8-15 specific, practical food items or simple dishes",
            "✓ Ensure nutritional variety and balance",
            "✓ Make items accessible and easy to prepare",
            "✓ Consider taste, culture, and modern lifestyle",
            "✓ Prioritize whole, unprocessed foods when restrictions are strict"
        ])
        
        context_parts.append("\nGenerate a personalized magic list that:")
        for req in requirements:
            context_parts.append(req)
        
        context_parts.append("\n⚠️ SAFETY REMINDER: When in doubt, be conservative. Better to provide fewer safe options than risk user health.")
        context_parts.append("\n🎯 OUTPUT: Return ONLY the JSON object with magic_list array. No explanations.")
        
        return "\n".join(context_parts)
    
    def _interpret_strictness(self, strictness: str) -> str:
        """Dynamically interpret any strictness level"""
        strictness_lower = str(strictness).lower().strip()
        
        # Dynamic interpretation based on common patterns
        if any(word in strictness_lower for word in ['strict', 'rigid', 'absolute', 'complete', 'total', 'full']):
            return "Follow exactly with no exceptions or flexibility"
        elif any(word in strictness_lower for word in ['balanced', 'moderate', 'regular', 'normal', 'standard']):
            return "Follow consistently with practical flexibility for real-life situations"
        elif any(word in strictness_lower for word in ['flexible', 'loose', 'casual', 'relaxed', 'light']):
            return "Follow general principles with significant flexibility and occasional exceptions"
        else:
            # Unknown strictness - be conservative
            return f"Apply '{strictness}' level adherence (interpreted conservatively for safety)"
    
    def _validate_input_structure(self, preferences: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate input structure dynamically without enforcing specific values.
        Only checks that the format is correct, not the content.
        """
        try:
            # Check if it's a dictionary
            if not isinstance(preferences, dict):
                return False, "Input must be a JSON object/dictionary"
            
            # Check for required keys
            required_keys = ['eating_style', 'allergies', 'medical_conditions']
            missing_keys = [key for key in required_keys if key not in preferences]
            
            if missing_keys:
                return False, f"Missing required keys: {', '.join(missing_keys)}"
            
            # Validate eating_style structure
            eating_style = preferences['eating_style']
            if not isinstance(eating_style, list):
                return False, "'eating_style' must be an array"
            
            for i, style in enumerate(eating_style):
                if not isinstance(style, dict):
                    return False, f"eating_style[{i}] must be an object"
                
                if 'name' not in style:
                    return False, f"eating_style[{i}] missing 'name' field"
                
                if 'strict_level' not in style:
                    return False, f"eating_style[{i}] missing 'strict_level' field"
            
            # Validate allergies structure
            allergies = preferences['allergies']
            if not isinstance(allergies, list):
                return False, "'allergies' must be an array"
            
            # Validate medical_conditions structure
            medical_conditions = preferences['medical_conditions']
            if not isinstance(medical_conditions, list):
                return False, "'medical_conditions' must be an array"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def generate_magic_list(self, preferences: Dict) -> Dict:
        """
        Generate magic list using OpenAI with fully dynamic processing.
        This method adapts to ANY input values automatically.
        """
        try:
            # Validate structure (not content)
            is_valid, error_msg = self._validate_input_structure(preferences)
            if not is_valid:
                raise ValueError(f"Invalid input structure: {error_msg}")
            
            logger.info("Generating magic list with dynamic processing...")
            
            # Build prompts dynamically
            system_prompt = self._build_dynamic_system_prompt()
            user_context = self._analyze_and_build_context(preferences)
            
            logger.info(f"Processing dynamic input with {len(preferences.get('eating_style', []))} eating styles, "
                       f"{len(preferences.get('allergies', []))} allergies, "
                       f"{len(preferences.get('medical_conditions', []))} medical conditions")
            
            # Call OpenAI API with dynamic parameters
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context}
                ],
                temperature=self.temperature,
                seed=self.seed,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            logger.info(f"Received OpenAI response: {len(content)} characters")
            
            result = json.loads(content)
            
            # Validate response structure
            if 'magic_list' not in result:
                raise ValueError("OpenAI response missing 'magic_list' key")
            
            if not isinstance(result['magic_list'], list):
                raise ValueError("'magic_list' must be an array")
            
            if len(result['magic_list']) == 0:
                raise ValueError("Magic list is empty - please review restrictions")
            
            # Log success with dynamic details
            logger.info(f"✅ Successfully generated {len(result['magic_list'])} personalized food items")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            raise Exception("OpenAI returned invalid JSON format")
        
        except Exception as e:
            logger.error(f"Error in magic list generation: {e}")
            raise
    
    def process_request(self, preferences: Dict) -> Dict:
        """
        Complete dynamic workflow: accept ANY valid input format,
        process it intelligently, and return personalized results.
        """
        start_time = datetime.now()
        
        try:
            logger.info("="*60)
            logger.info("🚀 Starting dynamic magic list generation")
            logger.info("="*60)
            
            # Generate magic list (fully dynamic)
            magic_list_result = self.generate_magic_list(preferences)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Build comprehensive response
            response = {
                'success': True,
                'magic_list': magic_list_result['magic_list'],
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'processing_time_seconds': round(processing_time, 2),
                    'model_used': self.model,
                    'input_summary': {
                        'eating_styles': [
                            f"{style['name']} ({style['strict_level']})" 
                            for style in preferences.get('eating_style', [])
                        ],
                        'allergies': preferences.get('allergies', []),
                        'medical_conditions': preferences.get('medical_conditions', []),
                    },
                    'output_summary': {
                        'total_items': len(magic_list_result['magic_list']),
                        'items_preview': magic_list_result['magic_list'][:3] if len(magic_list_result['magic_list']) > 3 else magic_list_result['magic_list']
                    }
                },
                'warnings': self._generate_dynamic_warnings(preferences)
            }
            
            logger.info(f"✅ Request processed successfully in {processing_time:.2f}s")
            logger.info("="*60)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing request: {e}")
            logger.exception("Full traceback:")
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'magic_list': [],
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'processing_time_seconds': (datetime.now() - start_time).total_seconds()
                }
            }
    
    def _generate_dynamic_warnings(self, preferences: Dict) -> List[str]:
        """Generate dynamic warnings based on input complexity"""
        warnings = []
        
        eating_styles = preferences.get('eating_style', [])
        allergies = preferences.get('allergies', [])
        medical_conditions = preferences.get('medical_conditions', [])
        
        # Check for complex combinations
        total_restrictions = len(eating_styles) + len(allergies) + len(medical_conditions)
        
        if total_restrictions == 0:
            warnings.append("No restrictions specified - recommendations will be general")
        
        if total_restrictions > 10:
            warnings.append("High number of restrictions may limit variety - recommendations will be conservative")
        
        if len(eating_styles) > 3:
            warnings.append("Multiple eating styles detected - ensuring compatibility")
        
        if len(allergies) > 5:
            warnings.append("Multiple allergies detected - recommendations will be extra cautious")
        
        # Check for strict levels
        strict_count = sum(1 for style in eating_styles 
                          if 'strict' in str(style.get('strict_level', '')).lower())
        
        if strict_count > 0:
            warnings.append(f"{strict_count} strict dietary preference(s) - following exact guidelines")
        
        return warnings

    def _sanitize_magic_items(self, raw_items: List[Any], max_items: Optional[int] = None) -> List[str]:
        """Sanitize and normalize a raw list of items coming from the model or API.

        - Accepts lists of strings or single long strings.
        - Splits numbered or newline-delimited paragraphs into separate items.
        - Strips whitespace, removes empty lines, deduplicates while preserving order.
        - Caps to max_items (dynamic, from config).
        """
        if max_items is None:
            max_items = self.max_items
            
        items: List[str] = []

        def push(candidate: str):
            cand = candidate.strip()
            if not cand:
                return
            # collapse internal whitespace
            cand = " ".join(cand.split())
            if cand not in items:
                items.append(cand)

        if isinstance(raw_items, list):
            for entry in raw_items:
                if entry is None:
                    continue
                if isinstance(entry, str):
                    # split by newlines if paragraph-like
                    parts = [p.strip() for p in entry.splitlines() if p.strip()]
                    for part in parts:
                        # remove leading numbering like '1. ' or '1) '
                        part = part.lstrip(' \t')
                        if part and (part[0].isdigit() or (part[0] in '-•')):
                            # try to remove common bullet/number prefixes
                            import re
                            part = re.sub(r'^\s*\d+[\.)\-:\s]*', '', part)
                            part = re.sub(r'^[-•\*\s]+', '', part)
                        push(part)
                else:
                    # non-string, coerce to str
                    push(str(entry))
        elif isinstance(raw_items, str):
            parts = [p.strip() for p in raw_items.splitlines() if p.strip()]
            for part in parts:
                import re
                part = re.sub(r'^\s*\d+[\.)\-:\s]*', '', part)
                part = re.sub(r'^[-•\*\s]+', '', part)
                push(part)
        else:
            # fall back to stringifying
            push(str(raw_items))

        # cap to dynamic max_items
        return items[:max_items]

    def _shorten_name(self, full_name: str, max_words: Optional[int] = None) -> str:
        """Create a shorter, UI-friendly label from a longer dish name.

        - Removes parenthetical clauses and long trailing clauses after commas.
        - Keeps the first `max_words` words (dynamic from config), joining with spaces.
        - Converts 'and' to '&' for compactness.
        """
        import re
        
        if max_words is None:
            max_words = self.max_name_words

        if not isinstance(full_name, str):
            return str(full_name)

        # remove parenthetical content
        s = re.sub(r"\([^)]*\)", "", full_name)
        # drop after a long clause separator like ' - ' or ' — '
        s = re.split(r"\s[-—–]\s", s)[0]
        # drop trailing comma clauses
        s = s.split(',')[0]
        # collapse whitespace
        s = " ".join(s.split())
        # replace ' and ' with ' & '
        s = re.sub(r"\band\b", "&", s, flags=re.IGNORECASE)

        words = s.split()
        if len(words) <= max_words:
            return s
        return " ".join(words[:max_words]) + "..."

    def build_ingredient_magic_list(self, preferences: Dict) -> List[Dict[str, Any]]:
        """Build a fully dynamic ingredient 'magic list' from user preferences.

        This extracts FOOD INGREDIENTS to watch (Dairy, Gluten, Nuts, etc.) 
        based on the user's allergies, diet preferences, and medical conditions.
        NOT the conditions themselves - the actual food ingredients!
        """
        allergies = [str(a).strip().lower() for a in preferences.get('allergies', []) if a]
        eating_styles = preferences.get('eating_style', [])
        medical_conditions = [str(c).strip().lower() for c in preferences.get('medical_conditions', []) if c]

        ui_items: List[Dict[str, Any]] = []
        seen = set()

        # Dynamic ingredient knowledge base - maps user inputs to food ingredients
        # This is built dynamically based on what we know about diets/allergies/conditions
        ingredient_mapping = {
            # Common allergens (if user reports them, we track these ingredients)
            'gluten': {'name': 'Gluten', 'category': 'grain', 'reason': 'allergy'},
            'dairy': {'name': 'Dairy', 'category': 'animal_product', 'reason': 'allergy'},
            'milk': {'name': 'Dairy', 'category': 'animal_product', 'reason': 'allergy'},
            'nuts': {'name': 'Nuts', 'category': 'allergen', 'reason': 'allergy'},
            'tree nuts': {'name': 'Tree Nuts', 'category': 'allergen', 'reason': 'allergy'},
            'peanuts': {'name': 'Peanuts', 'category': 'allergen', 'reason': 'allergy'},
            'shellfish': {'name': 'Shellfish', 'category': 'seafood', 'reason': 'allergy'},
            'fish': {'name': 'Fish', 'category': 'seafood', 'reason': 'allergy'},
            'eggs': {'name': 'Eggs', 'category': 'animal_product', 'reason': 'allergy'},
            'soy': {'name': 'Soy', 'category': 'legume', 'reason': 'allergy'},
            'sesame': {'name': 'Sesame', 'category': 'seed', 'reason': 'allergy'},
            
            # Diet-based ingredient restrictions
            'keto': [
                {'name': 'Sugar', 'category': 'sweetener', 'reason': 'keto_restricted'},
                {'name': 'Grains', 'category': 'carbohydrate', 'reason': 'keto_restricted'},
                {'name': 'High-Carb Foods', 'category': 'carbohydrate', 'reason': 'keto_restricted'}
            ],
            'paleo': [
                {'name': 'Grains', 'category': 'processed', 'reason': 'paleo_restricted'},
                {'name': 'Dairy', 'category': 'animal_product', 'reason': 'paleo_restricted'},
                {'name': 'Legumes', 'category': 'plant', 'reason': 'paleo_restricted'},
                {'name': 'Processed Foods', 'category': 'processed', 'reason': 'paleo_restricted'}
            ],
            'vegan': [
                {'name': 'Meat', 'category': 'animal_product', 'reason': 'vegan_restricted'},
                {'name': 'Dairy', 'category': 'animal_product', 'reason': 'vegan_restricted'},
                {'name': 'Eggs', 'category': 'animal_product', 'reason': 'vegan_restricted'},
                {'name': 'Honey', 'category': 'animal_product', 'reason': 'vegan_restricted'}
            ],
            'vegetarian': [
                {'name': 'Meat', 'category': 'animal_product', 'reason': 'vegetarian_restricted'},
                {'name': 'Fish', 'category': 'animal_product', 'reason': 'vegetarian_restricted'},
                {'name': 'Poultry', 'category': 'animal_product', 'reason': 'vegetarian_restricted'}
            ],
            
            # Medical condition-based restrictions
            'diabetes': [
                {'name': 'Sugar', 'category': 'sweetener', 'reason': 'diabetes_restricted'},
                {'name': 'High-Carb Foods', 'category': 'carbohydrate', 'reason': 'diabetes_restricted'},
                {'name': 'Refined Grains', 'category': 'carbohydrate', 'reason': 'diabetes_restricted'}
            ],
            'celiac': [
                {'name': 'Gluten', 'category': 'grain', 'reason': 'celiac_restricted'}
            ],
            'lactose intolerance': [
                {'name': 'Dairy', 'category': 'animal_product', 'reason': 'lactose_restricted'}
            ]
        }

        def add_ingredient(name: str, category: str, reason: str, source: str):
            """Helper to add ingredient avoiding duplicates"""
            if name.lower() in seen:
                return
            seen.add(name.lower())
            
            ui_items.append({
                'name': name,
                'full_name': name,
                'meta': {
                    'category': category,
                    'reason': reason,
                    'source': source
                }
            })

        # Process allergies - these are usually direct ingredient names
        for allergy in allergies:
            if allergy in ingredient_mapping and isinstance(ingredient_mapping[allergy], dict):
                ing = ingredient_mapping[allergy]
                add_ingredient(ing['name'], ing['category'], ing['reason'], 'user_allergy')
            else:
                # Unknown allergy - add it directly as an ingredient to watch
                add_ingredient(allergy.title(), 'unknown', 'allergy', 'user_reported')

        # Process eating styles - extract restricted ingredients from each diet
        for style in eating_styles:
            style_name = style.get('name', '').strip().lower()
            strictness = style.get('strict_level', 'balanced').strip()
            
            if style_name in ingredient_mapping and isinstance(ingredient_mapping[style_name], list):
                for ing in ingredient_mapping[style_name]:
                    add_ingredient(
                        ing['name'], 
                        ing['category'], 
                        f"{ing['reason']}_{strictness.lower()}", 
                        f'diet_{style_name}'
                    )

        # Process medical conditions - extract restricted ingredients
        for condition in medical_conditions:
            if condition in ingredient_mapping and isinstance(ingredient_mapping[condition], list):
                for ing in ingredient_mapping[condition]:
                    add_ingredient(
                        ing['name'], 
                        ing['category'], 
                        ing['reason'], 
                        f'medical_{condition}'
                    )

        # Dynamic limit based on config
        max_ingredients = self.config.get('max_ingredients', self.max_items * 2)
        return ui_items[:max_ingredients]


def generate_magic_list_json(preferences: Dict, config: Optional[Dict] = None) -> Dict:
    """
    Backend function to generate magic list from user preferences using AI.
    Uses a FIXED list of options and toggles them ON (1) or OFF (0) based on
    user's dietary needs (allergies, diets, medical conditions).
    
    Args:
        preferences: User preferences dict with eating_style, allergies, medical_conditions
        config: Optional configuration overrides
    
    Returns:
        Python dict: {"magic_list": [{"Item Name": 1}, {"Other Item": 0}, ...]}
    """
    if config is None:
        config = {
            'model': 'gpt-4o',
            'temperature': 0.0,
            'max_tokens': 1000,
        }
        
    FIXED_ITEMS = [
        "Gluten 🌾",
        "Dairy 🥛",
        "Nuts 🥜",
        "Shellfish 🦐",
        "Eggs 🥚",
        "Beef 🥩",
        "Chicken 🍗",
        "Pork 🐖",
        "Fish 🐟",
        "Garlic 🧄",
        "Onions 🧅",
        "Mushrooms 🍄",
        "Tomatoes 🍅",
        "Fried / Breaded 🍤",
        "Creamy / Cheesy 🧀",
        "Buttered 🧈",
        "Sesame ⚪",
        "Alcohol 🍷"
    ]
    
    generator = DynamicMagicListGenerator(api_key=OPENAI_API_KEY, config=config)
    
    try:
        # Build prompt
        system_prompt = """You are an expert nutritionist. Your task is to review a user's dietary profile and toggle items from a FIXED list known as the "Magic List".

For each item in the fixed list, determine if it should be marked as "Active" (1) or "Inactive" (0) based on the user's Eating Style, Allergies, and Medical Conditions.

RULES FOR TOGGLING (1 = ON/AVOID/WATCH, 0 = OFF/SAFE):
- Set to 1 if the item contains an allergen the user has.
- Set to 1 if the item is restricted by the user's diet (e.g., 'Beef' is 1 for Vegan).
- Set to 1 if the item is incompatible with the user's medical conditions.
- Set to 1 if the user explicitly mentions avoiding this food.
- Otherwise, set to 0.

You MUST include EVERY item from the provided fixed list in the output, in the exact same order. Do not add new items. Do not change the item names/emojis.

Response Format:
Return a JSON object with a "magic_list" key containing a list of objects. Each object should have the item string as the key and the status (0 or 1) as the value.
Example:
{
  "magic_list": [
    {"Gluten 🌾 (...)": 1},
    {"Dairy 🥛 (...)": 0},
    ...
  ]
}"""

        # Build user context
        context_parts = ["Analyze this user profile and toggle the fixed list items:\n"]
        
        eating_styles = preferences.get('eating_style', [])
        if eating_styles:
            context_parts.append("Dietary Preferences:")
            for style in eating_styles:
                name = style.get('name', 'unspecified')
                strictness = style.get('strict_level', 'balanced')
                context_parts.append(f"- {name} ({strictness})")
                
        allergies = preferences.get('allergies', [])
        if allergies:
            context_parts.append("\nAllergies:")
            for allergy in allergies:
                context_parts.append(f"- {allergy}")
                
        medical_conditions = preferences.get('medical_conditions', [])
        if medical_conditions:
            context_parts.append("\nMedical Conditions:")
            for condition in medical_conditions:
                context_parts.append(f"- {condition}")

        context_parts.append("\nFIXED LIST TO EVALUATE:")
        for item in FIXED_ITEMS:
            context_parts.append(f"- {item}")
            
        user_context = "\n".join(context_parts)
        
        logger.info("Calling OpenAI API for fixed magic list generation...")
        
        # Use simple chat completion
        response = generator.client.chat.completions.create(
            model=config.get('model', 'gpt-4o'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context}
            ],
            temperature=0.0,
            seed=42,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        magic_list = result.get('magic_list', [])
        
        # Validation and re-ordering to ensure strict adherence to fixed list
        final_list = []
        ai_map = {}
        
        # Parse AI response into a map
        for entry in magic_list:
            if isinstance(entry, dict):
                for k, v in entry.items():
                    # Normalize key slightly just in case (though we asked for exact)
                    ai_map[k.strip()] = v
            elif isinstance(entry, list) and len(entry) == 2:
                 # Handle [key, value] case just in case
                 ai_map[str(entry[0]).strip()] = entry[1]

        # Reconstruct list safely
        for item in FIXED_ITEMS:
            # Default to 0
            val = ai_map.get(item, 0)
            try:
                val = int(val)
                if val not in [0, 1]:
                    val = 1 if val > 0 else 0
            except:
                val = 0
            final_list.append({item: val})
            
        logger.info(f"✅ Generated fixed magic list with {len(final_list)} items")
        return {"magic_list": final_list}

    except Exception as e:
        logger.exception("Error generating fixed magic list")
        # Fallback: all zeros or safe default code
        fallback_list = [{item: 0} for item in FIXED_ITEMS]
        return {"magic_list": fallback_list, "error": str(e)}
