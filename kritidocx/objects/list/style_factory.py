"""
from kritidocx.utils.logger import logger
STYLE FACTORY MODULE (The Bullet Designer)
------------------------------------------
Responsibility:
Generates visual definitions for List Levels (0 to 8).
It acts as a configuration generator for `NumberingXml`.

Key Capabilities:
1. Bullet Cycling: Changes symbol based on depth (Disc -> Circle -> Square).
2. Number Rotation: Changes format based on depth (1 -> a -> i).
3. Legal Numbering: Supports complex hierarchical numbering (1.1, 1.2.1).
4. Font Protection: Ensures Bullets use 'Symbol' fonts to prevent 'tofu' boxes [].

Integration:
- Pulls visual defaults from 'config.theme.ThemeConfig'.
"""

from kritidocx.config.settings import AppConfig
from kritidocx.config.theme import ThemeConfig
from kritidocx.utils import logger

class StyleFactory:
    """
    Produces styling configurations for AbstractNumbering Definitions.
    """

    # XML Format Enums (Word Specific)
    FMT_DECIMAL = "decimal"
    FMT_LOWER_LETTER = "lowerLetter"
    FMT_LOWER_ROMAN = "lowerRoman"
    FMT_BULLET = "bullet"

    @classmethod
    def get_style_config(cls, style_type):
        """
        Main API. Returns a list of 9 dicts (one for each indentation level).
        
        Args:
            style_type (str): 'decimal', 'bullet', 'legal', 'checkbox'
        """
        if getattr(AppConfig, 'DEBUG_LISTS', False):
            logger.debug(f"   🎨 [StyleFactory]: Generating Config for Mode='{style_type}'")

        
        levels_config = []
        mode = style_type.lower()

        for level_idx in range(9): # Word supports max 9 levels
            
            # 1. Decide Configuration based on Type
            if mode == 'legal':
                config = cls._get_legal_style(level_idx)
            
            elif mode == 'decimal' or mode == 'ol':
                config = cls._get_decimal_nested_style(level_idx)
            
            elif mode == 'checkbox':
                config = cls._get_checkbox_style(level_idx)
            
            else: # Default Bullet (ul)
                config = cls._get_bullet_style(level_idx)

            # 2. Inject Common Alignment & Level Index
            config['level'] = level_idx
            config['align'] = 'left' # Text aligns left
            
            # Add to list
            levels_config.append(config)
            
        return levels_config

    # =========================================================================
    # 🎨 STYLE GENERATORS
    # =========================================================================

    @classmethod
    def _get_decimal_nested_style(cls, level):
        """
        Rotation: 1. -> a. -> i.
        """
        formats = [
            (cls.FMT_DECIMAL, "%1."),       # Level 0: 1.
            (cls.FMT_LOWER_LETTER, "%2."),  # Level 1: a.
            (cls.FMT_LOWER_ROMAN, "%3.")    # Level 2: i.
        ]
        
        # Cycle through formats based on level (Modulus math)
        fmt_type, text_mask = formats[level % len(formats)]
        
        # Dynamic Text Mask generation is complex for non-legal
        # Word needs hardcoded '%X' for the current level's number.
        # But 'a.' needs '%2.' because it's level 2 (index 1).
        # Fix: For simple nesting, just referencing current level's placeholder usually works:
        text_str = f"%{level + 1}."

        return {
            'format': fmt_type,
            'text': text_str,
            'font': {
                'name': ThemeConfig.FONTS_ASCII.get('body', 'Calibri'),
                'color': None # Inherit text color
            }
        }

    @classmethod
    def _get_bullet_style(cls, level):
        """
        Rotation: ● (Disc) -> ○ (Circle) -> ▪ (Square)
        [STEP 4 FIX]: Font Safety Strategy.
        'Symbol' और 'Wingdings' फोंट Unicode characters (जैसे ●) के साथ काम नहीं करते, 
        वे 'Square Box' (□) दिखाते हैं। 
        हम 'Calibri' का उपयोग करेंगे जो सभी Unicode बुलेट्स को सही रेंडर करता है।
        """
        # Patterns: (Character, FontName, SizeHalfPoints)
        patterns = [
            # Level 0: Disc (●) - Calibri Unicode के लिए सबसे सुरक्षित है
            (ThemeConfig.SYMBOLS['bullet_solid'],  'Calibri', 24),
            
            # Level 1: Circle (o) - Courier New का 'o' एक अच्छा hollow bullet लगता है
            (ThemeConfig.SYMBOLS['bullet_hollow'], 'Courier New', 20),
            
            # Level 2: Square (▪) - Calibri इसे सही रेंडर करता है
            (ThemeConfig.SYMBOLS['bullet_square'], 'Calibri', 20),
            
            # Level 3: Dash (–)
            ('–', 'Calibri', 20),
            
            # Level 4: Arrow (➤) - Unicode Arrow
            (ThemeConfig.SYMBOLS['arrow'], 'Calibri', 20) 
        ]
        
        char, font_name, size = patterns[level % len(patterns)]
             
        return {
            'format': cls.FMT_BULLET,
            'text': char,
            'font': {
                'name': font_name,
                'color': ThemeConfig.THEME_COLORS.get('brand_secondary'), # Make bullets slight blue/brand color?
                'hint': 'default',
                'size': size # Size is mostly managed by rPr/sz (half-points) in Factory
            }
        }

    @classmethod
    def _get_legal_style(cls, level):
        """
        Hierarchical: 1. -> 1.1. -> 1.1.1.
        """
        # Generates text like "%1.%2.%3."
        text_mask = ""
        for i in range(level + 1):
            text_mask += f"%{i+1}"
            if i < level: text_mask += "." # लेवल्स के बीच डॉट
        text_mask += "." # आखिरी डॉट

            
        return {
            'format': cls.FMT_DECIMAL,
            'text': text_mask,
            'font': {'name': ThemeConfig.FONTS_ASCII.get('body', 'Calibri')}
        }

    @classmethod
    def _get_checkbox_style(cls, level):
        """
        For Todo Lists: Uses Box Symbol.
        """
        # Unicode 2610 = ☐
        char = ThemeConfig.SYMBOLS['checkbox_unchecked']
        font = ThemeConfig.FONTS_COMPLEX['forms'] # MS Gothic required
        
        return {
            'format': cls.FMT_BULLET,
            'text': char,
            'font': {
                'name': font,
                'color': '595959', # Gray checkboxes
                'size': 24
            }
        }