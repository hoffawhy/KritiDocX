"""
CHECKBOX HANDLER MODULE (The Toggle Logic)
------------------------------------------
Responsibility:
Handles input[type="checkbox"] logic.
Prepares Unicode Symbols, Fonts, and States for the XML Factory.

Problem:
Word treats Checkbox symbols like text. If the font (e.g. Calibri) doesn't
support the glyph '☑' (U+2611), it shows an empty square box.

Solution:
Force use of 'MS Gothic' or 'Segoe UI Symbol' which are guaranteed to have these glyphs on Windows.
"""
from kritidocx.config.settings import AppConfig
from kritidocx.utils.logger import logger

from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.config.theme import ThemeConfig
from kritidocx.basics.css_parser import CssParser
from kritidocx.basics.color_manager import ColorManager

class CheckboxHandler:
    """
    Controller for Checkbox Form Controls.
    """

    @classmethod
    def add_checkbox(cls, node, paragraph, context=None):
        """
        Main logic to parse HTML node and inject SDT Checkbox.
        
        Args:
            node: BeautifulSoup tag (<input type="checkbox"...>)
            paragraph: The Docx paragraph object to insert into.
        """
        
        # 1. Determine State
        # Check standard HTML attributes
        is_checked = node.has_attr('checked') or (node.get('value', '').lower() == 'true')
        
        # 2. COLOR STRATEGY
        from kritidocx.basics.css_parser import CssParser
        from kritidocx.basics.color_manager import ColorManager
        
        # Inline Style
        inline_css = CssParser.parse(node.get('style', ''))
        raw_color = inline_css.get('color')
        
        # Inherit from Parent Context if inline missing
        if not raw_color and context:
            raw_color = context.get('color')
            
        # इससे यह सुनिश्चित हो जाएगा कि आपकी इमेज जैसा दिखे
        if not raw_color:
            raw_color = '#2E74B5'  # Theme Blue    
            
            
        symbol_color = ColorManager.get_hex(raw_color)

        # [DEBUG LOG UPDATE]
        if getattr(AppConfig, 'DEBUG_FORMS', False):
            logger.debug(f"🔳 [CHECKBOX INHERITANCE]")
            logger.debug(f"   ➤ Parent Color Context: {context.get('color') if context else 'None'}")
            logger.debug(f"   ➤ Final Applied Hex: {symbol_color}")


        # 3. Resolve Font (CRITICAL)
        # Use Theme config to get safe fonts (e.g., 'MS Gothic')
        # Priority: Config > Default Fallback
        font_name = ThemeConfig.FONTS_COMPLEX.get('forms', 'MS Gothic')

        # 4. Resolve Symbol Character (Unicode)
        # Use Theme definitions for consistency
        if is_checked:
            # Handle special data attribute: data-style="x" -> ☒
            box_style = node.get('data-style', 'check')
            if box_style == 'x':
                # Ballot Box with X
                symbol_char = "\u2612" 
            else:
                # Default: Ballot Box with Check (Theme default)
                symbol_char = ThemeConfig.SYMBOLS.get('checkbox_checked', "\u2611")
        else:
            # Empty Box
            symbol_char = ThemeConfig.SYMBOLS.get('checkbox_unchecked', "\u2610")

        font_size = 24


        # 5. Delegate to XML Factory
        # Pass the pre-calculated safe font and correct unicode symbol.
        XmlBuilder.insert_sdt_checkbox(
            paragraph=paragraph,
            checked=is_checked,
            symbol_char=symbol_char,
            font_name=font_name,
            hex_color=symbol_color,
            font_size=font_size 
        )
        
        # Future enhancement: If XmlBuilder.insert_sdt_checkbox allows passing 'hex_color',
        # pass 'symbol_color' there. Currently, standard forms use default run color.