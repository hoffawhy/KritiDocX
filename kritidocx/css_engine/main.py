import logging
from functools import lru_cache
from .tokenizer import CssTokenizer

# [UPDATED CODE]: Imports added here
from .handlers.box_model import BoxModelHandler
from .handlers.dimensions import DimensionHandler
from .handlers.border_handler import BorderHandler
from .handlers.text_handler import TextHandler

logger = logging.getLogger("MyDocX_CssEngine")

class CssEngine:
    @staticmethod
    @lru_cache(maxsize=4096)
    def parse(style_str):
        
        # Step 1: Lexical Analysis
        raw_tokens = CssTokenizer.parse_inline_styles(style_str)
        if not raw_tokens: return {}

        final_attributes = {}

        # Step 2: Processing Loop (Distribution Logic)
        for prop, value in raw_tokens.items():
            
            # [UPDATED CODE]: Check for Box Model (Margin/Padding)
            if prop in ['margin', 'padding']:
                # यह 4 दिशाओं में expand करेगा
                BoxModelHandler.process(prop, value, final_attributes)
                # Shorthand भी रखें ताकि future checks fail न हों
                final_attributes[prop] = value
                continue

            # [UPDATED CODE]: Dimensions, Position & Transformation
            # Added: 'transform', 'top', 'left', 'z-index'
            elif prop in ['width', 'height', 'max-width', 'min-width', 
                          'transform', 'top', 'left', 'right', 'bottom', 'z-index', 'position']:
                DimensionHandler.process(prop, value, final_attributes)
                # Keep position logic for Layout triggers
                if prop == 'position':
                    final_attributes[prop] = value
                continue

            # Border Interception logic
            elif 'border' in prop:
                # 'border', 'border-top', etc.
                BorderHandler.process(prop, value, final_attributes)
                continue

            # Text & Typography Interception
            elif prop in ['text-decoration', 'text-align', 'align', 
                          'font-family', 'font-size', 'font-weight', 'font-style',
                          'color', 'line-height', 'text-shadow', 'letter-spacing','text-glow', 'text-outline', 'text-reflection', 'text-gradient',
                          'font-stretch', 'vertical-align', 'background-shading']:
                TextHandler.process(prop, value, final_attributes)
                continue

            # Default Passthrough
            final_attributes[prop] = value

        return final_attributes