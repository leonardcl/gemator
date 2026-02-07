"""Text overlay compositor for manhwa translation."""

from PIL import Image, ImageDraw, ImageFont
import os


class TextCompositor:
    """Handles text rendering and image compositing."""

    FONT_SIZES = [16, 14, 12, 10]
    PADDING = 10

    # macOS system font paths
    SYSTEM_FONTS = {
        'normal': '/System/Library/Fonts/Helvetica.ttc',
        'shout': '/System/Library/Fonts/Helvetica.ttc',  # Will use bold via truetype index
        'whisper': '/System/Library/Fonts/Helvetica.ttc'
    }

    def __init__(self):
        """Initialize compositor with font loading."""
        self.fonts = self.SYSTEM_FONTS
        print(f"✓ Using system fonts: {self.fonts['normal']}")

    def draw_white_block(self, image, bubble):
        """
        Draw solid white block to hide Korean text (Pass 1).

        Args:
            image: PIL Image object (original manhwa page)
            bubble: dict with x, y, width, height

        Returns:
            PIL Image with white block applied
        """
        x = bubble['x']
        y = bubble['y']
        width = bubble['width']
        height = bubble['height']

        # Create solid white rectangle
        white_block = Image.new('RGB', (width, height), color=(255, 255, 255))

        # Paste white block onto image
        image.paste(white_block, (x, y))

        return image

    def draw_text_with_glass(self, image, bubble, text):
        """
        Draw text with semi-transparent glass background (Pass 2).

        Args:
            image: PIL Image object (with white blocks already drawn)
            bubble: dict with x, y, width, height, type, font_size
            text: str (translated English text)

        Returns:
            PIL Image with text overlay applied
        """
        x = bubble['x']
        y = bubble['y']
        width = bubble['width']
        height = bubble['height']
        bubble_type = bubble['type']
        base_font_size = bubble.get('font_size', 16)

        print(f"Drawing text: bubble size={width}x{height}, base_font_size={base_font_size}pt")

        # Create RGBA canvas with semi-transparent white glass effect
        glass = Image.new('RGBA', (width, height), color=(255, 255, 255, 0))  # Fully transparent initially

        # Render text on glass
        glass_with_text = self._render_text_on_glass(glass, text, bubble_type, width, height, base_font_size)

        # Extract region from image
        region = image.crop((x, y, x + width, y + height)).convert('RGBA')

        # Blend glass with text onto image
        blended = Image.alpha_composite(region, glass_with_text)

        # Paste back
        image.paste(blended.convert('RGB'), (x, y))

        return image

    def _wrap_text(self, text, font, max_width):
        """
        Wrap text into multiple lines to fit within max_width.

        Args:
            text: str (text to wrap)
            font: PIL ImageFont
            max_width: int (maximum width in pixels)

        Returns:
            list of str (lines of text)
        """
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            # Try adding this word to current line
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = bbox[2] - bbox[0]

            if test_width <= max_width:
                current_line.append(word)
            else:
                # Word doesn't fit, start new line
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)

        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]

    def _render_text_on_glass(self, glass, text, bubble_type, width, height, base_font_size):
        """
        Render text with semi-transparent glass background.

        Args:
            glass: PIL RGBA Image
            text: str (text to render)
            bubble_type: str (normal/shout/whisper)
            width: int (bubble width)
            height: int (bubble height)
            base_font_size: int (starting font size)

        Returns:
            PIL RGBA Image with text and glass background
        """
        draw = ImageDraw.Draw(glass)
        font_path = self.fonts.get(bubble_type, self.fonts['normal'])

        # Generate font sizes
        font_sizes = []
        current_size = base_font_size
        while current_size >= 16:
            font_sizes.append(current_size)
            current_size -= 4

        # Try each font size with text wrapping
        for size in font_sizes:
            try:
                font = ImageFont.truetype(font_path, size)

                # Wrap text into multiple lines
                max_text_width = width - (self.PADDING * 2)
                lines = self._wrap_text(text, font, max_text_width)

                # Calculate total height needed
                line_height = draw.textbbox((0, 0), "Ay", font=font)[3]
                total_height = line_height * len(lines)

                # Check if wrapped text fits in bubble height
                if total_height <= height - (self.PADDING * 2):
                    # Text fits! Draw semi-transparent glass behind text
                    text_x = 5
                    text_y = (height - total_height) // 2

                    # Calculate glass rectangle to cover all lines
                    max_line_width = max(
                        draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
                        for line in lines
                    )

                    glass_padding = 3
                    glass_rect = [
                        text_x - glass_padding,
                        text_y - glass_padding,
                        text_x + max_line_width + glass_padding,
                        text_y + total_height + glass_padding
                    ]

                    # Draw semi-transparent white glass background
                    draw.rectangle(glass_rect, fill=(255, 255, 255, 120))  # 120/255 = 47% opacity

                    # Draw each line of text
                    current_y = text_y
                    for line in lines:
                        draw.text((text_x, current_y), line, fill=(0, 0, 0, 255), font=font)
                        current_y += line_height

                    print(f"  → Rendered with {size}pt font, {len(lines)} lines, total_height={total_height}px")
                    return glass

            except Exception as e:
                print(f"  ! Failed to load font at {size}pt: {e}")
                continue

        # Fallback: use minimum size with wrapping
        try:
            font = ImageFont.truetype(font_path, 16)
            max_text_width = width - (self.PADDING * 2)
            lines = self._wrap_text(text, font, max_text_width)

            line_height = draw.textbbox((0, 0), "Ay", font=font)[3]
            text_y = self.PADDING

            for line in lines:
                draw.text((5, text_y), line, fill=(0, 0, 0, 255), font=font)
                text_y += line_height
                if text_y > height - self.PADDING:
                    break  # Stop if we run out of space

            print(f"  → Using fallback 16pt font with {len(lines)} lines (text too long)")
        except:
            # Emergency fallback
            font = ImageFont.truetype(font_path, 14)
            draw.text((5, height // 2), text[:50] + "...", fill=(0, 0, 0, 255), font=font)
            print(f"  → Emergency fallback: truncated text")

        return glass

    def compose_overlay(self, image, bubble, text):
        """
        Create text overlay on image for a single bubble.

        Args:
            image: PIL Image object (original manhwa page)
            bubble: dict with x, y, width, height, type, font_size
            text: str (translated English text)

        Returns:
            PIL Image with text overlay applied
        """
        x = bubble['x']
        y = bubble['y']
        width = bubble['width']
        height = bubble['height']
        bubble_type = bubble['type']
        # Use OCR-estimated font size, or default to 16
        base_font_size = bubble.get('font_size', 16)
        print(f"Compositing: bubble size={width}x{height}, base_font_size={base_font_size}pt")

        # STEP 1: Draw SOLID white background to block original Korean text
        # Create completely opaque white rectangle
        with_bg = Image.new('RGBA', (width, height), color=(255, 255, 255, 255))  # 100% solid white

        # STEP 2: Render text on top of white background
        # Render text with auto-shrinking from estimated size
        final = self._render_text(with_bg, text, bubble_type, width, height, base_font_size)

        # Paste result back to image
        image.paste(final.convert('RGB'), (x, y))

        return image

    def _render_text(self, overlay, text, bubble_type, width, height, base_font_size):
        """
        Render text on overlay with auto-shrinking and wrapping to fit.

        Args:
            overlay: PIL Image (RGBA image with white background)
            text: str (text to render)
            bubble_type: str (normal/shout/whisper)
            width: int (bubble width)
            height: int (bubble height)
            base_font_size: int (starting font size from OCR estimation)

        Returns:
            PIL Image with text rendered
        """
        draw = ImageDraw.Draw(overlay)
        font_path = self.fonts.get(bubble_type, self.fonts['normal'])

        # Generate font sizes: start from base_font_size and shrink minimally
        # Go down to minimum of 20pt (readable minimum)
        font_sizes = []
        current_size = base_font_size
        while current_size >= 20:
            font_sizes.append(current_size)
            current_size -= 5

        # Try each font size with text wrapping
        for size in font_sizes:
            try:
                # Load system font at this size
                font = ImageFont.truetype(font_path, size)

                # Wrap text into multiple lines
                max_text_width = width - (self.PADDING * 2)
                lines = self._wrap_text(text, font, max_text_width)

                # Calculate total height needed
                line_height = draw.textbbox((0, 0), "Ay", font=font)[3]
                total_height = line_height * len(lines)

                # Check if wrapped text fits in bubble height
                if total_height <= height - (self.PADDING * 2):
                    # Text fits! Render it centered vertically
                    text_y = (height - total_height) // 2

                    # Draw each line
                    current_y = text_y
                    for line in lines:
                        draw.text((5, current_y), line, fill=(0, 0, 0), font=font)
                        current_y += line_height

                    print(f"  → Rendered with {size}pt font, {len(lines)} lines, total_height={total_height}px")
                    return overlay

            except Exception as e:
                # Font loading failed, try next size
                print(f"  ! Failed to load font at {size}pt: {e}")
                continue

        # Fallback: use minimum size with wrapping, even if it overflows slightly
        try:
            font = ImageFont.truetype(font_path, 18)
            max_text_width = width - (self.PADDING * 2)
            lines = self._wrap_text(text, font, max_text_width)

            line_height = draw.textbbox((0, 0), "Ay", font=font)[3]
            text_y = self.PADDING

            for line in lines:
                if text_y > height - self.PADDING:
                    break  # Stop if we run out of space
                draw.text((5, text_y), line, fill=(0, 0, 0), font=font)
                text_y += line_height

            print(f"  → Fallback: 18pt font with {len(lines)} lines")
        except:
            # Emergency fallback: truncate
            try:
                font = ImageFont.truetype(font_path, 16)
                truncated = self._truncate_text(text, width - self.PADDING, font)
                draw.text((5, height // 2), truncated, fill=(0, 0, 0), font=font)
                print(f"  → Emergency fallback: truncated text")
            except:
                pass

        return overlay

    def _truncate_text(self, text, max_width, font):
        """
        Truncate text to fit within max_width, adding '...'.

        Args:
            text: str (original text)
            max_width: int (maximum pixel width)
            font: PIL ImageFont

        Returns:
            str (truncated text with '...')
        """
        draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))

        for i in range(len(text), 0, -1):
            truncated = text[:i] + "..."
            bbox = draw.textbbox((0, 0), truncated, font=font)
            if bbox[2] - bbox[0] <= max_width:
                return truncated

        return "..."
