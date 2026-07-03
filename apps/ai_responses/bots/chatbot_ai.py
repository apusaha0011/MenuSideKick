import json
import re
from openai import OpenAI
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

from core.settings import OPENAI_API_KEY

# Configure logging to stderr
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(handler)



class MenuSidekickChatbot:
    """
    Fully dynamic and adaptive food conversation chatbot.
    Provides personalized guidance based on user's dietary profile,
    restrictions, preferences, and conversation context.
    """
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI client with dynamic configuration"""
        self.client = OpenAI(api_key=api_key)
        
        # Dynamic configuration
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.7)  # More creative for conversation
        self.max_tokens = self.config.get('max_tokens', 1000)
        self.presence_penalty = self.config.get('presence_penalty', 0.6)  # Encourage variety
        self.frequency_penalty = self.config.get('frequency_penalty', 0.3)  # Reduce repetition
        # Quiet mode: when enabled, suppress all logger output and return minimal reply-only responses
        self.quiet = bool(self.config.get('quiet', False))
        # Disable module logger output when quiet mode is requested
        if self.quiet:
            try:
                logger.disabled = True
            except Exception:
                # If logger can't be disabled for any reason, ignore and continue
                pass
    
    def _build_system_prompt(self, profile: Dict[str, Any]) -> str:
        """
        Build dynamic, personalized system prompt based on user profile.
        Fully adaptive to any profile data provided.
        """
        # Extract profile information dynamically
        profile_name = profile.get('profile_name', 'there')
        language = profile.get('preferred_language', 'English')
        country = profile.get('country', 'Unknown')
        date_of_birth = profile.get('date_of_birth', None)
        eating_styles = profile.get('eating_style', [])
        allergies = profile.get('allergies', [])
        medical_conditions = profile.get('medical_conditions', [])
        magic_list = profile.get('magic_list', [])
        strict_level = profile.get('strict_level', 'Balanced')
        
        # Calculate age if DOB provided
        age_info = ""
        if date_of_birth:
            try:
                from datetime import datetime
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
                age = (datetime.now() - dob).days // 365
                age_info = f"Age: {age} years old"
            except:
                age_info = f"Date of Birth: {date_of_birth}"
        
        # Build comprehensive system prompt
        prompt_parts = [
            f"""You are Menu Sidekick AI - a warm, friendly, and knowledgeable food & nutrition companion chatbot.

🎯 YOUR CORE IDENTITY:
- You are a supportive food guide, nutritionist, and motivational companion
- You speak naturally and conversationally in {language}
- You remember user context and provide personalized advice
- You're encouraging, positive, and genuinely care about the user's health journey
- You can discuss food, recipes, nutrition, meal planning, and healthy lifestyle
- You know about cuisines from around the world, especially from {country}

👤 USER PROFILE - {profile_name.upper()}:"""
        ]
        
        # Add profile details dynamically
        if age_info:
            prompt_parts.append(f"• {age_info}")
        
        if country and country != "Unknown":
            prompt_parts.append(f"• Location: {country}")
        
        if language:
            prompt_parts.append(f"• Preferred Language: {language}")
        
        if strict_level:
            prompt_parts.append(f"• Dietary Adherence Level: {strict_level}")
        
        # Add eating styles
        if eating_styles:
            prompt_parts.append(f"\n🥗 DIETARY PREFERENCES:")
            for style in eating_styles:
                prompt_parts.append(f"  • {style}")
            prompt_parts.append(f"  → Respect these dietary choices in all suggestions")
        
        # Add allergies (CRITICAL)
        if allergies:
            prompt_parts.append(f"\n⚠️ ALLERGIES (CRITICAL - NEVER SUGGEST):")
            for allergy in allergies:
                prompt_parts.append(f"  • ❌ {allergy}")
            prompt_parts.append(f"  → ABSOLUTE -+ORITY: Never suggest foods containing these allergens")
        
        # Add medical conditions
        if medical_conditions:
            prompt_parts.append(f"\n🏥 MEDICAL CONDITIONS:")
            for condition in medical_conditions:
                prompt_parts.append(f"  • {condition}")
            prompt_parts.append(f"  → Provide medically appropriate food suggestions")
        
        # Add magic list (ingredients to watch)
        if magic_list:
            prompt_parts.append(f"\n🔍 INGREDIENTS TO WATCH/AVOID:")
            magic_preview = magic_list[:10]  # Show first 10
            for item in magic_preview:
                prompt_parts.append(f"  • {item}")
            if len(magic_list) > 10:
                prompt_parts.append(f"  • ... and {len(magic_list) - 10} more")
            prompt_parts.append(f"  → Be mindful of these ingredients when making suggestions")
        
        # Add conversation guidelines
        prompt_parts.extend([
            f"""

🎭 YOUR PERSONALITY & TONE:
• Warm, friendly, and approachable - like a knowledgeable friend
• Encouraging and motivational - celebrate small wins
• Patient and understanding - dietary changes are challenging
• Culturally aware - respect {country}'s food culture and traditions
• Use emojis occasionally to keep conversation light and engaging
• Address user as "{profile_name}" when appropriate (but not too often)

💬 CONVERSATION STYLE:
• Be conversational and natural - avoid sounding robotic or formal
• Keep responses concise (2-4 paragraphs typically)
• Ask follow-up questions to understand user needs better
• Provide specific, actionable suggestions when asked
• Share interesting food facts, tips, or recipe ideas
• Adapt your language complexity based on user's messages
• If user seems confused, simplify and clarify
• If user is enthusiastic, match their energy!

🍽️ WHEN SUGGESTING FOODS/RECIPES:
• ALWAYS check against allergies first (non-negotiable)
• Respect their eating style preferences ({', '.join(eating_styles) if eating_styles else 'no specific restrictions'})
• Consider their strictness level: {strict_level}
• Be mindful of ingredients in their watch list
• Consider {country}'s local ingredients and food availability
• Suggest practical, accessible options
• Provide alternatives if primary suggestion doesn't fit
• Explain WHY a food is good for them (nutritional benefits)

🌟 SPECIAL CAPABILITIES:
• Recipe suggestions (breakfast, lunch, dinner, snacks)
• Meal planning advice
• Ingredient substitutions
• Nutrition education
• Food prep tips
• Restaurant/takeout guidance
• Grocery shopping help
• Motivation and support
• Cultural food discussions
• Cooking techniques

⚠️ SAFETY GUIDELINES:
• NEVER suggest foods with their allergens - this is critical for safety
• Be conservative with medical conditions - encourage medical consultation for serious health questions
• Don't diagnose or prescribe - you're a guide, not a doctor
• If strictness is high, be more careful with suggestions
• If strictness is flexible, you can be more relaxed

🎯 CONVERSATION SCENARIOS:

If user asks for food suggestions:
→ Provide 3-5 specific, personalized options with brief descriptions
→ Explain why each fits their profile
→ Ask if they want recipes or more details

If user shares a meal/food:
→ Acknowledge it positively
→ Check if it aligns with their profile (gently)
→ Suggest improvements or alternatives if needed
→ Celebrate good choices!

If user asks "what can I eat?":
→ Provide categories and examples
→ Reassure them they have plenty of options
→ Focus on what they CAN eat, not restrictions

If user seems discouraged:
→ Be extra encouraging
→ Share success stories or tips
→ Remind them of their "why"
→ Suggest small, achievable steps

If user asks general questions:
→ Answer naturally and conversationally
→ Tie back to food/health when relevant
→ Be helpful and informative

If user says hello/hi/hey:
→ Greet warmly using their name
→ Ask how you can help today
→ Keep it brief and friendly

🔥 REMEMBER:
• You're having a conversation, not giving a lecture
• Personalization is key - use their profile data
• Safety first - especially with allergies
• Be encouraging - dietary changes are hard
• Have fun with it - food should be enjoyable!

Now, engage in a natural, helpful conversation with {profile_name}!
"""
        ])
        
        return "\n".join(prompt_parts)
    
    def _prepare_conversation_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert backend history format to OpenAI message format.
        Handles any history structure dynamically.
        
        Backend format: [{"role": "user", "content": "..."}, {"role": "ai", "content": "..."}]
        OpenAI format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        openai_messages = []
        
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Convert 'ai' role to 'assistant' for OpenAI
            if role.lower() in ['ai', 'assistant', 'bot']:
                openai_role = 'assistant'
            elif role.lower() in ['user', 'human']:
                openai_role = 'user'
            else:
                # Unknown role, default to user
                openai_role = 'user'
            
            if content.strip():  # Only add non-empty messages
                openai_messages.append({
                    'role': openai_role,
                    'content': content.strip()
                })
        
        return openai_messages
    
    def _validate_inputs(self, history: List[Dict], user_message: str, profile: Dict) -> tuple[bool, Optional[str]]:
        """Validate input structure dynamically"""
        try:
            # Check user_message
            if not user_message or not isinstance(user_message, str):
                return False, "user_message must be a non-empty string"
            
            if not user_message.strip():
                return False, "user_message cannot be empty or whitespace only"
            
            # Check history
            if not isinstance(history, list):
                return False, "history_payload must be a list"
            
            # Validate history structure
            for i, msg in enumerate(history):
                if not isinstance(msg, dict):
                    return False, f"history[{i}] must be a dictionary"
                if 'role' not in msg or 'content' not in msg:
                    return False, f"history[{i}] must have 'role' and 'content' keys"
            
            # Check profile
            if not isinstance(profile, dict):
                return False, "profile_payload must be a dictionary"
            
            # Profile can have any fields, we're flexible
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    # New helper: clean markdown and unwrap JSON-like responses to plain text
    def _clean_reply(self, text: str) -> str:
        """Remove Markdown formatting and unwrap JSON payloads; return single-line text preserving emojis"""
        try:
            if not isinstance(text, str):
                return str(text)
            # Unwrap triple backtick code blocks (```lang\ncontent``` -> content)
            text = re.sub(r"```(?:[\w+-]*\n)?(.*?)```", r"\1", text, flags=re.DOTALL)
            # Unwrap triple tilde fences
            text = re.sub(r"~~~(?:[\w+-]*\n)?(.*?)~~~", r"\1", text, flags=re.DOTALL)
            # Inline code `code` -> code
            text = re.sub(r"`([^`]+)`", r"\1", text)
            # Links [text](url) -> text
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
            # Remove common markdown headings markers at line starts
            text = re.sub(r'(?m)^\s{0,3}#{1,6}\s*', '', text)
            # Replace markdown bullets with simple dash + space
            text = re.sub(r'(?m)^\s*[-*+]\s+', '- ', text)
            # Remove bold/italic markers (**text**, __text__, *text*, _text_)
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'__(.*?)__', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'\*(.*?)\*', r'\1', text, flags=re.DOTALL)
            text = re.sub(r'_(.*?)_', r'\1', text, flags=re.DOTALL)
            # Remove numbered list markers at line starts (Latin and Bengali digits)
            text = re.sub(r'(?m)^\s*[\d০১২৩৪৫৬৭৮৯]+[.)]\s*', '', text)
            # Collapse line breaks into single spaces to produce a clean single-line paragraph
            text = re.sub(r'\s*\n+\s*', ' ', text)
            # Collapse excessive whitespace
            text = re.sub(r'\s{2,}', ' ', text)
            text = text.strip()
            # If AI returned JSON text, try to parse and extract meaningful text
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    # Prefer 'reply' key if present
                    if 'reply' in parsed and isinstance(parsed['reply'], str):
                        text = parsed['reply'].strip()
                    else:
                        # Fallback: pretty-print dict as text (preserve emojis)
                        text = json.dumps(parsed, ensure_ascii=False, indent=2)
                elif isinstance(parsed, list):
                    text = " ".join([str(item) for item in parsed])
            except Exception:
                # Not JSON, keep cleaned markdown text
                pass
            # Final trim and return
            return text.strip()
        except Exception:
            return text

    def generate_reply(self, history: List[Dict[str, str]], user_message: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI reply based on conversation history, current message, and user profile.
        Fully dynamic and adaptive to any input.
        
        Args:
            history: List of previous messages [{"role": "user/ai", "content": "..."}]
            user_message: Current user message
            profile: User profile dict with dietary info, preferences, etc.
        
        Returns:
            Dict with AI response and metadata
        """
        start_time = datetime.now()
        
        try:
            # Validate inputs
            is_valid, error_msg = self._validate_inputs(history, user_message, profile)
            if not is_valid:
                raise ValueError(f"Invalid input: {error_msg}")
            
            logger.info("="*70)
            logger.info("🤖 Menu Sidekick Chatbot - Generating Response")
            logger.info("="*70)
            logger.info(f"User: {profile.get('profile_name', 'Unknown')}")
            logger.info(f"Message: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
            logger.info(f"History: {len(history)} previous messages")
            
            # Build dynamic system prompt based on profile
            system_prompt = self._build_system_prompt(profile)
            
            # Prepare conversation history
            conversation_messages = self._prepare_conversation_history(history)
            
            # Build complete message array for OpenAI
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            messages.extend(conversation_messages)
            messages.append({"role": "user", "content": user_message})
            
            logger.info(f"Calling OpenAI API ({self.model})...")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty
            )
            
            # Extract response (raw)
            ai_reply = response.choices[0].message.content.strip()

            # Clean markdown and unwrap JSON to plain text while preserving emojis
            clean_reply = self._clean_reply(ai_reply)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ Response generated in {processing_time:.2f}s")
            logger.info(f"Response length: {len(clean_reply)} characters")
            logger.info("="*70)
            
            # Build response using cleaned reply
            response = {
                'success': True,
                'reply': clean_reply,
                'metadata': {
                    'model_used': self.model,
                    'processing_time_seconds': round(processing_time, 2),
                    'generated_at': datetime.now().isoformat(),
                    'message_length': len(clean_reply),
                    'conversation_depth': len(history),
                    'user_profile': profile.get('profile_name', 'Unknown')
                }
            }

            # If quiet mode is enabled, return only the minimal reply payload (cleaned)
            if self.quiet:
                return {'success': True, 'reply': clean_reply}

            return response
            
        except Exception as e:
            logger.error(f"❌ Error generating reply: {e}")
            logger.exception("Full traceback:")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Minimal error response; if quiet mode, strip extra fields
            base_error = {
                'success': False,
                'reply': "I apologize, but I'm having trouble processing your message right now. Please try again in a moment.",
                'error': str(e),
                'error_type': type(e).__name__,
                'metadata': {
                    'processing_time_seconds': round(processing_time, 2),
                    'generated_at': datetime.now().isoformat()
                }
            }

            if self.quiet:
                return {'success': False, 'reply': base_error['reply'], 'error': base_error['error']}

            return base_error


def generate_ai_reply(history_payload: List[Dict[str, str]], 
                      user_message: str, 
                      profile_payload: Dict[str, Any],
                      config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    
    try:
        """
        Backend integration function for Django views.
        Generate personalized AI reply based on conversation history and user profile.
        
        Args:
            history_payload: Conversation history [{"role": "user/ai", "content": "..."}]
            user_message: Current user message
            profile_payload: User profile with dietary info, preferences, allergies, etc.
            config: Optional configuration overrides
        
        Returns:
            Dict with 'reply' key containing AI response:
            {
                "success": True,
                "reply": "AI response text...",
                "metadata": {...}
            }
        
        Example:
            history = [
                {"role": "user", "content": "hello"},
                {"role": "ai", "content": "Hi there! How can I help?"}
            ]
            profile = {
                "profile_name": "John",
                "eating_style": ["keto"],
                "allergies": ["gluten"]
            }
            result = generate_ai_reply(history, "suggest breakfast", profile)
            ai_response = result['reply']
        """
        if config is None:
            config = {
                'model': 'gpt-4.1',
                'temperature': 0.7,
                'max_tokens': 1000,
                'presence_penalty': 0.6,
                'frequency_penalty': 0.3
            }
        # Ensure quiet flag is forwarded to chatbot config
        chatbot = MenuSidekickChatbot(api_key=OPENAI_API_KEY, config=config)
        result = chatbot.generate_reply(history_payload, user_message, profile_payload)
    except Exception as e:
        result = {"reply": "I'm sorry, something went wrong on the server."}
    return result