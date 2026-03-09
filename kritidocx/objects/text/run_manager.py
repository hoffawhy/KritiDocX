"""
from kritidocx.utils.logger import logger
RUN MANAGER MODULE (The Inline Artist)
--------------------------------------
Responsibility:
Creates and Styles 'Run' objects within a paragraph.
Applies: Fonts, Colors, Shading, Spacing, and Scripts (Sub/Superscript).

Special Handling:
1. Hindi/Asian Fonts: Maps correct font slots (ascii vs cs).
2. Language ID: Sets appropriate proofing language (en-US vs hi-IN).
3. Hybrid Background: Chooses between <w:highlight> and <w:shd> automatically.
"""

from docx.shared import Pt, RGBColor
from docx.enum.text import WD_COLOR_INDEX, WD_UNDERLINE

from kritidocx.config.settings import AppConfig
from kritidocx.basics.border_parser import BorderParser
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.basics.color_manager import ColorManager
from kritidocx.basics.font_handler import FontHandler
from kritidocx.basics.css_parser import CssParser
from kritidocx.utils import logger
from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.config.theme import ThemeConfig

class RunManager:
    """
    Advanced text formatter. 
    Interacts with python-docx 'Run' objects and uses XmlBuilder for missing features.
    """

    # Mapping common highlight names to Word Enum
    HIGHLIGHT_MAP = {
        'yellow': WD_COLOR_INDEX.YELLOW,
        'green': WD_COLOR_INDEX.BRIGHT_GREEN,
        'cyan': WD_COLOR_INDEX.TURQUOISE,
        'magenta': WD_COLOR_INDEX.PINK,
        'blue': WD_COLOR_INDEX.BLUE,
        'red': WD_COLOR_INDEX.RED,
        'dark_blue': WD_COLOR_INDEX.DARK_BLUE,
        'teal': WD_COLOR_INDEX.TEAL,
        'gray': WD_COLOR_INDEX.GRAY_25,
        'black': WD_COLOR_INDEX.BLACK
    }

    # Standard Word Underscore styles mapping
    UNDERLINE_MAP = {
        'solid': True,
        'double': WD_UNDERLINE.DOUBLE,
        'dotted': WD_UNDERLINE.DOTTED,
        'dashed': WD_UNDERLINE.DASH,
        'wavy': WD_UNDERLINE.WAVY,
        'thick': WD_UNDERLINE.THICK
    }

    @staticmethod
    def create_run(paragraph, text_content, style_data=None):
        """
        Master factory method to create a formatted Run.
        
        Args:
            paragraph: Parent docx paragraph.
            text_content (str): Raw string.
            style_data (dict): {'bold': True, 'color': 'red', ...}
            
        Returns:
            The created Run object.
        """
        # 1. Validation
        if text_content is None: return None
        text_str = str(text_content)
        if not text_str: return None

        if style_data is None: style_data = {}

        # यह सुनिश्चित करता है कि CSS Parser से आए 'text-align' को सिस्टम पहचान सके
        if 'text-align' in style_data and 'align' not in style_data:
            style_data['align'] = style_data['text-align']


        # 2. Create Base Run with space preservation
        run = paragraph.add_run(text_str)
        
        # [NEW FIX]: Leading Spaces Preservation
        # Word डिफ़ॉल्ट रूप से कोड के आगे के खाली स्पेस को काट देता है। 
        # उसे रोकने के लिए 'xml:space="preserve"' सेट करना अनिवार्य है।
        from docx.oxml.ns import qn
        t_tag = run._r.xpath("w:t")
        if t_tag:
            t_tag[0].set(qn('xml:space'), 'preserve')
        
        # [FIX] Do not return early. Even if style_data is empty, 
        # we need to proceed to check for Content-based Logic (Hindi/Symbols fonts).
        if style_data is None: 
            style_data = {}

        # -----------------------------------------------
        # 3. APPLY FORMATTING
        # -----------------------------------------------        
        # A. Boolean Toggles
        if style_data.get('bold'): run.bold = True
        if style_data.get('italic'): run.italic = True
        
        # [ADVANCED UNDERLINE FIX - v2]
        # CSS "underline wavy blue" को Word के "wave" स्टाइल में बदलना।
        u_raw = style_data.get('text-decoration') or style_data.get('underline')
        
        if u_raw:
            u_str = str(u_raw).lower()
            if 'underline' in u_str or u_str == 'true':
                # 1. स्टाइल पहचानें (Word XML Acceptable values)
                # डिफ़ॉल्ट 'single'
                target_style = 'single'
                
                # CSS keywords -> Word XML keywords mapping
                style_map = {
                    'double': 'double',
                    'dotted': 'dotted',
                    'dashed': 'dashed',
                    'wavy':   'wave',   # [CRITICAL]: CSS wavy = Word wave
                    'thick':  'thick'
                }
                
                for css_key, word_val in style_map.items():
                    if css_key in u_str:
                        target_style = word_val
                        break
                
                # 2. रंग पहचानें (Extraction logic)
                target_color = None
                words = u_str.split()
                for word in words:
                    # 'underline' और स्टाइल शब्दों को छोड़कर बाकी रंग हो सकते हैं
                    if word not in ['underline', 'none'] and word not in style_map:
                        found_hex = ColorManager.get_hex(word)
                        if found_hex and found_hex != '000000':
                            target_color = found_hex
                            break

                # 3. XML में इंजेक्ट करें
                XmlBuilder.set_run_underline_advanced(run, target_style, target_color)
                
        if style_data.get('strike') or style_data.get('strikethrough'): 
            run.font.strike = True
        if style_data.get('double_strike'):
            run.font.double_strike = True
            
        # Script positioning
        if style_data.get('sub'): run.font.subscript = True
        if style_data.get('sup'): run.font.superscript = True

        # Caps / Small Caps
        if style_data.get('caps') or style_data.get('uppercase'):
            run.font.all_caps = True
        if style_data.get('small_caps'):
            run.font.small_caps = True

        # B. Typography (Fonts & Size)
        RunManager._apply_fonts(run, text_str, style_data)


        if style_data.get('gradient_dict'):
            # यदि ग्रेडिएंट मौजूद है, तो साधारण 'color' को रोक दें 
            # ताकि वर्ड कंफ्यूज न हो और ग्रेडिएंट साफ़ दिखे।
            style_data['color'] = None 

        # C. Color (Foreground)
        text_color = style_data.get('color')
        if text_color:
            hex_col = ColorManager.get_hex(text_color)
         
            if getattr(AppConfig, 'DEBUG', False) and text_content and "MyDocX" in str(text_content):
                # सिर्फ हेडर/फूटर के टेक्स्ट को फिल्टर करके प्रिंट करें
                logger.debug(f"      📝 [RUN MANAGER] Text: '{text_content[:15]}...' -> Applying HEX: {hex_col}")

         
            if hex_col:
                # Word Run needs RGB Tuple
                r, g, b = int(hex_col[:2], 16), int(hex_col[2:4], 16), int(hex_col[4:], 16)
                run.font.color.rgb = RGBColor(r, g, b)

        # D. Backgrounds (Highlight vs Shading)
        RunManager._apply_backgrounds(run, style_data)

        # [FIX]: Apply Inline Borders (HTML span border)
        # यह सुनिश्चित करेगा कि <span> का बॉर्डर पैराग्राफ की तरह नहीं फैले, 
        # बल्कि टेक्स्ट के चारों ओर टाइट फिट हो।
        RunManager._apply_inline_border(run, style_data)

        # E. Advanced XML Effects (Spacing/Shadow)
        RunManager._apply_advanced_effects(run, style_data)

        return run

    # =========================================================================
    # 🕵️ INTERNAL LOGIC HANDLERS
    # =========================================================================

    @staticmethod
    def _apply_fonts(run, text, style_data):
        """
        Handles size, family and now scaling.
        """
        # --- 1. Size Logic (पुराना कोड) ---
        fs_raw = style_data.get('font-size') or style_data.get('font_size')
        if fs_raw:
            hps = UnitConverter.to_half_points(str(fs_raw))
            if hps > 0:
                run.font.size = Pt(hps / 2)

        # --- 2. Font Family Resolver (पुराना कोड) ---
        font_config = FontHandler.resolve_font_config(style_data, text)
        if font_config.get('ascii'):
            run.font.name = font_config['ascii']

        # --- 3. XML Injection (पुराना कोड) ---
        XmlBuilder.set_run_fonts(run, font_config)

        # =========================================================
        # यहाँ पर नया "Stretch/Scaling" लॉजिक जोड़ें 👇
        # =========================================================
        stretch = style_data.get('font-stretch') or style_data.get('font_stretch')
        if stretch:
            # Word को सिर्फ नंबर चाहिए (उदा. 150), '150%' नहीं। 
            # इसलिए हम सिर्फ डिजिट्स निकालेंगे।
            import re
            nums = re.findall(r'\d+', str(stretch))
            if nums:
                scale_val = int(nums[0])
                # XmlBuilder को कॉल करें
                XmlBuilder.set_run_scaling(run, scale_val)
        # =========================================================

    @staticmethod
    def _apply_backgrounds(run, style_data):
        """
        Smartly chooses between Highlighter (Neon) and Shading (Hex).
        """
        bg_val = style_data.get('background-color') or style_data.get('highlight')
        if not bg_val or bg_val == 'transparent' or 'none' in str(bg_val):
            return

        clean_val = str(bg_val).strip().lower()

        # 1. नाम से चेक करें ("yellow")
        if clean_val in RunManager.HIGHLIGHT_MAP:
            run.font.highlight_color = RunManager.HIGHLIGHT_MAP[clean_val]
            return

        if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
            logger.debug(f"   🖍️ [RunManager-Debug] BG Input: '{bg_val}'")


        hex_val = ColorManager.get_hex(clean_val)
        if hex_val:
            # ✅ सुधार: hex_val को Uppercase में बदलें ताकि Constants से मैच हो सके
            hex_key = hex_val.upper() 

            if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
                logger.debug(f"   🖍️ [RunManager-Debug] Resolved HEX: '{hex_key}'")

            from kritidocx.config.constants import DocConstants 
            # ✅ सुधार: अब 'hex_key' का उपयोग करें
            if hex_key in DocConstants.HEX_TO_HIGHLIGHT:
                run.font.highlight_color = DocConstants.HEX_TO_HIGHLIGHT[hex_key]
                return
            
            # अगर हाईलाइटर नहीं है, तो साधारण शेडिंग (Paint Bucket) करें
            XmlBuilder.set_run_shading(run, hex_key)

            
            
    @staticmethod
    def _apply_advanced_effects(run, style_data):
        """
        Features: Kerning, Shadows, Glow, and Outline (Typography Hub)
        """
        # 1. Spacing (Kerning)
        ls_raw = style_data.get('letter-spacing') or style_data.get('spacing_val')
        val_twips = UnitConverter.to_twips(str(ls_raw)) if ls_raw else 0

        pos_offset = style_data.get('text_position')
        if pos_offset is not None:
            # यह XmlBuilder के माध्यम से <w:position> को कॉल करेगा
            XmlBuilder.set_run_position(run, pos_offset)

        shading_data = style_data.get('shading_dict')
        if shading_data:
            XmlBuilder.set_run_shading_advanced(run, shading_data)

        # 2. Extract Typography Effects
        shadow_val = style_data.get('shadow_dict') or style_data.get('shadow', False)
        glow_val = style_data.get('glow_dict')
        outline_val = style_data.get('outline_dict')
        r_data = style_data.get('reflection_dict')
        g_data = style_data.get('gradient_dict')
        
        # --- DEBUG LOGGING ---
        if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
            # Shadow Log
            if shadow_val:
                logger.debug(f"   🎨 [RunManager] Shadow Active for: '{run.text[:10]}...'")
            # Glow Log
            if glow_val:
                logger.debug(f"   🌟 [RunManager] Applying GLOW: Rad={glow_val['rad']} EMUs")
            # Outline Log
            if outline_val:
                logger.debug(f"   🖋️ [RunManager] Applying OUTLINE: Width={outline_val['w']} EMUs")
                
            # reflection Log
            if r_data:
             logger.debug(f"   🌊 [RunManager] Transferring Reflection to XmlBuilder for: '{run.text[:10]}...'")


        # 3. XML Builder को अपडेटेड पैरामीटर्स के साथ कॉल करें
        XmlBuilder.set_run_effects(
            run, 
            spacing=val_twips, 
            shadow=shadow_val, 
            glow=glow_val,     
            outline=outline_val, 
            reflection=r_data,
            gradient=g_data
        )
          
    @staticmethod
    def _apply_inline_border(run, style_data):
        """
        Parses 'border' css specifically for Inline Text runs.
        """
        border_str = style_data.get('border')
        if not border_str or border_str == 'none': 
            return

        # Reuse existing BorderParser (It handles '1px solid green' -> dict)
        b_props = BorderParser.parse(border_str)
        
        if b_props and b_props['sz'] > 0:
            # Word Run Borders don't allow separate sides (top/left).
            # <w:bdr> applies to all 4 sides of the text.
            XmlBuilder.set_run_border(
                run,
                size=b_props['sz'],
                val=b_props['val'],
                color=b_props['color']
            )