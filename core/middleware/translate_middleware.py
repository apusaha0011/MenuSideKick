from django.utils.deprecation import MiddlewareMixin
from core.utils.ai_translator import translate_text
import re

class OpenAITranslationMiddleware(MiddlewareMixin):
    """
    Automatically translate JSON API responses based on user's preferred language,
    but skip URLs, emails, numbers, and non-human-readable fields.
    """
    URL_PATTERN = re.compile(r'^https?://')
    EMAIL_PATTERN = re.compile(r'^[^@]+@[^@]+\.[^@]+$')

    def process_response(self, request, response):
        try:
            user = getattr(request, 'user', None)
            target_lang = getattr(user, 'language', 'English') if user and user.is_authenticated else 'English'

            # Only process JSON responses and non-English
            if (
                response.get('content-type', '').startswith('application/json')
                and target_lang.lower() != 'english'
                and hasattr(response, 'data')
            ):
                # Exclude scanned document and OCR endpoints from translation
                path = getattr(request, 'path', '')
                # Be permissive: skip any scanned-documents or ocr related endpoints
                if (
                    '/scanned-document' in path
                    or '/scanned-documents' in path
                    or '/ocr' in path
                    or '/auth/google/' in path
                ):
                    return response

                data = response.data

                # Fields to always skip translation
                # Add `extracted_text`, `ai_reply`, and 'sender' which are used by scanned documents / OCR / chat
                SKIP_FIELDS = {
                    'created_at', 'updated_at', 'uploaded_at',
                    'username', 'user_name', 'created', 'updated',
                    'extracted_text', 'ai_reply', 'sender'
                }

                def _should_translate(key, value):
                    """Decide if a string should be translated."""
                    if not isinstance(value, str):
                        return False
                    if (
                        key in SKIP_FIELDS
                        or self.URL_PATTERN.match(value)
                        or self.EMAIL_PATTERN.match(value)
                        or value.strip().isdigit()
                        or len(value.strip()) < 2
                    ):
                        return False
                    return True

                # Special handling for chat/conversation/message endpoints:
                chat_paths = [
                    '/chat/conversations',
                    '/chat/conversation',
                    '/chat/',
                ]
                is_chat = any(p in path for p in chat_paths)

                def _translate_chat_messages(obj):
                    # Only translate AI message content, not user message or sender field
                    if isinstance(obj, list):
                        return [_translate_chat_messages(item) for item in obj]
                    if isinstance(obj, dict):
                        # If this looks like a message dict, only translate content if sender == 'ai'
                        if 'sender' in obj and 'content' in obj:
                            new_obj = obj.copy()
                            if obj['sender'] == 'ai' and _should_translate('content', obj['content']):
                                new_obj['content'] = translate_text(obj['content'], target_lang)
                            # Never translate sender field
                            return new_obj
                        # Otherwise, recurse
                        return {k: _translate_chat_messages(v) for k, v in obj.items()}
                    return obj

                def _translate_fields(obj, parent_key=None):
                    if is_chat:
                        return _translate_chat_messages(obj)
                    if isinstance(obj, dict):
                        return {k: _translate_fields(v, k) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [_translate_fields(v, parent_key) for v in obj]
                    elif isinstance(obj, str) and _should_translate(parent_key, obj):
                        return translate_text(obj, target_lang)
                    return obj

                translated_data = _translate_fields(data)
                response.data = translated_data
                response._is_rendered = False
                response.render()

        except Exception as e:
            print("Translation Middleware Error:", e)

        return response
