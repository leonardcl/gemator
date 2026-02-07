"""Gemini API integration for manhwa translation."""

import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import time

load_dotenv()


class TranslationEngine:
    """Handles translation via Gemini API."""

    BATCH_SIZE = 10  # Translate 10 bubbles at once

    PROMPTS = {
        'normal': (
            "Translate this Korean speech bubble to natural "
            "conversational English. Return ONLY the translation."
        ),
        'shout': (
            "Translate this Korean speech bubble to English. "
            "This is shouted/emphasized dialogue - use energetic "
            "language. Return ONLY the translation."
        ),
        'whisper': (
            "Translate this Korean speech bubble to English. "
            "This is internal thought or whisper - use softer, "
            "reflective language. Return ONLY the translation."
        )
    }

    BATCH_PROMPT = """TASK: Translate {count} Korean text strings to English.

INPUT: You will receive {count} Korean text strings, numbered [1] to [{count}].

OUTPUT REQUIREMENTS (STRICT):
1. You MUST return EXACTLY {count} translations
2. Each translation MUST be on its own line
3. Each line MUST start with the number in brackets: [N]
4. Do NOT combine multiple inputs into one translation
5. Do NOT skip any numbers
6. Translate even single words like "네" → [N] Yes

EXAMPLE:
If I give you:
[1] Korean: 안녕
[2] Korean: 네
[3] Korean: 뭐야?

You MUST return:
[1] Hello
[2] Yes
[3] What?

NOT:
[1] Hello, yes, what?  ❌ WRONG - combined
[1] Hello  ❌ WRONG - only 1 of 3

NOW TRANSLATE THESE {count} KOREAN TEXTS:"""

    def __init__(self):
        """Initialize Gemini API with credentials."""
        api_key = os.getenv('GEMINI_API_KEY')

        # Test mode: set GEMINI_API_KEY=TEST to skip API calls
        self.test_mode = (api_key == 'TEST')

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment. "
                "Create .env file with your API key."
            )

        if not self.test_mode:
            genai.configure(api_key=api_key)
            # Use Gemini 2.5 Flash (latest stable multimodal model)
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        else:
            print("⚠️  TEST MODE: Using dummy translations (no API calls)")

    def translate_bubbles_batch(self, bubble_crops, korean_texts, full_image):
        """
        Translate multiple bubbles in a single API call.

        Args:
            bubble_crops: List of PIL Images (cropped bubble regions)
            korean_texts: List of str (OCR-detected Korean text for each bubble)
            full_image: PIL Image (full page for context)

        Returns:
            Tuple[List[str], dict]: (Translated texts, debug info)
        """
        # Test mode: return dummy text
        if self.test_mode:
            return ["Test Translation"] * len(bubble_crops), {
                'prompt': 'TEST MODE',
                'response': 'Test translations',
                'count': len(bubble_crops),
                'korean_texts': korean_texts
            }

        count = len(bubble_crops)
        prompt = self.BATCH_PROMPT.format(count=count)

        print("\n" + "="*80, flush=True)
        print("GEMINI API PROMPT:", flush=True)
        print("="*80, flush=True)
        print(prompt, flush=True)
        print("="*80, flush=True)
        print(f"Sending: 1 full page + {count} bubbles with Korean text:", flush=True)
        for i, korean in enumerate(korean_texts):
            print(f"  [{i+1}] Korean: {korean}", flush=True)
        print("="*80 + "\n", flush=True)

        try:
            # Build content list: prompt + all bubble images + full page context
            content = [prompt]

            # Add full page for context first
            content.append("\nFull manhwa page for context:")
            content.append(full_image)

            # Add each bubble with its Korean text and image
            for i, (crop, korean_text) in enumerate(zip(bubble_crops, korean_texts)):
                content.append(f"\n[{i+1}] Korean text: {korean_text}")
                content.append(f"[{i+1}] Image:")
                content.append(crop)

            print(f"  ⏳ Calling Gemini API with {count} bubbles...", flush=True)

            # Single API call for all bubbles
            response = self.model.generate_content(
                content,
                generation_config={
                    'temperature': 0.2,  # Lower temperature for more consistent format
                    'max_output_tokens': 2000  # More tokens for longer responses
                }
            )

            # Parse response: extract [1], [2], [3] translations
            text = response.text.strip()

            print("\n" + "="*80, flush=True)
            print("GEMINI API RESPONSE:", flush=True)
            print("="*80, flush=True)
            print(text, flush=True)
            print("="*80 + "\n", flush=True)

            translations = self._parse_batch_response(text, count)

            print("PARSED TRANSLATIONS:", flush=True)
            for i, trans in enumerate(translations):
                print(f"  [{i+1}] → '{trans}'", flush=True)
            print("", flush=True)

            # Return translations and debug info
            debug_info = {
                'prompt': prompt,
                'response': text,
                'count': count,
                'translations': translations
            }
            return translations, debug_info

        except Exception as e:
            print(f"[ERROR] Batch translation failed: {type(e).__name__}: {e}", flush=True)
            # Fallback to individual translations
            debug_info = {
                'prompt': prompt,
                'response': f'ERROR: {str(e)}',
                'count': count,
                'translations': ["[Translation failed]"] * count
            }
            return ["[Translation failed]"] * count, debug_info

    def _parse_batch_response(self, text, expected_count):
        """Parse batch translation response into individual translations."""
        import re

        translations = []
        # Find all [N] translation patterns
        pattern = r'\[(\d+)\]\s*(.+?)(?=\[\d+\]|$)'
        matches = re.findall(pattern, text, re.DOTALL)

        for num, translation in matches:
            translations.append(translation.strip())

        # Ensure we have the right count
        while len(translations) < expected_count:
            translations.append("[Translation failed]")

        return translations[:expected_count]

    def translate_bubble(self, crop_image, full_image, bubble_type):
        """
        Translate a single bubble using Gemini API.

        Args:
            crop_image: PIL Image (cropped bubble region)
            full_image: PIL Image (full page for context)
            bubble_type: str (normal/shout/whisper)

        Returns:
            str: Translated English text
        """
        # Test mode: return dummy text to test font sizing
        if self.test_mode:
            return "Test Translation"

        prompt = self.PROMPTS.get(bubble_type, self.PROMPTS['normal'])

        try:
            # Send both crop and full context to Gemini
            response = self.model.generate_content(
                [
                    prompt,
                    crop_image,
                    "Full page context:",
                    full_image
                ],
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 100
                }
            )

            text = response.text.strip()
            if not text:
                return "[No text detected]"

            return text

        except Exception as e:
            print(f"[ERROR] Gemini API error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Retry once after 2 seconds
            time.sleep(2)

            try:
                response = self.model.generate_content(
                    [prompt, crop_image],
                    generation_config={
                        'temperature': 0.3,
                        'max_output_tokens': 100
                    }
                )
                return response.text.strip() or "[No text detected]"

            except Exception as retry_error:
                print(f"[ERROR] Gemini retry failed: {type(retry_error).__name__}: {retry_error}")
                import traceback
                traceback.print_exc()
                return "[Translation failed]"
