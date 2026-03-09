"""
from kritidocx.utils.logger import logger
PARAGRAPH MANAGER MODULE (The Block Architect)
----------------------------------------------
Responsibility:
Manages all block-level properties of a paragraph.

Features:
1. Alignment (Justify, Distribute support).
2. Advanced Indentation (Calculates Hanging vs First Line logic).
3. Spacing & Leading (Line Height logic).
4. Block Borders (Applying pBdr via XmlBuilder).
5. Pagination Control (Widow/Orphan, Keep-With-Next).

Dependency:
- UnitConverter: To convert px/em/cm to Twips.
- XmlBuilder: For low-level properties (Borders/Shading).
"""

import re
from docx.shared import Pt, Twips
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING, WD_BREAK

from kritidocx.config.settings import AppConfig
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.basics.color_manager import ColorManager
from kritidocx.basics.border_parser import BorderParser
from kritidocx.utils import logger
from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.config.theme import ThemeConfig

class ParagraphManager:
    """
    Control logic for formatting standard Word Paragraphs.
    """

    # CSS Text-Align to Word Enum Mapping
    ALIGN_MAP = {
        'left': WD_PARAGRAPH_ALIGNMENT.LEFT,
        'right': WD_PARAGRAPH_ALIGNMENT.RIGHT,
        'center': WD_PARAGRAPH_ALIGNMENT.CENTER,
        'justify': WD_PARAGRAPH_ALIGNMENT.JUSTIFY,
        'distribute': WD_PARAGRAPH_ALIGNMENT.DISTRIBUTE
    }

    @staticmethod
    def apply_formatting(paragraph, style_data):
        """
        Master method to apply all block-level styles.
        """
        # [DEBUG LOG]
        # (Assuming AppConfig is imported as 'from kritidocx.config.settings import AppConfig')
        # या सीधे सुरक्षित तरीके से चेक करें
        if style_data and style_data.get('num_id'):
            logger.debug(f"   🎨 [ParaManager] APPLYING FORMATTING | NumID: {style_data.get('num_id')} | Level: {style_data.get('list_depth')}")

        
        
        if not style_data or not isinstance(style_data, dict): 
            return

        if not style_data: return

        # 1. Base Properties (Alignment)
        ParagraphManager._apply_alignment(paragraph, style_data)

        # 2. Dimensions (Indentation)
        ParagraphManager._apply_indentation(paragraph, style_data)

        # 3. Spacing (Before, After, Line Height)
        ParagraphManager._apply_spacing(paragraph, style_data)

        # 4. Background Shading
        ParagraphManager._apply_shading(paragraph, style_data)

        # 5. Borders (e.g. Box or Underline Heading)
        ParagraphManager._apply_borders(paragraph, style_data)

        # 6. Pagination Flow
        ParagraphManager._apply_pagination(paragraph, style_data)

        # 7. [FINAL FIX]: List Activation
        # Step 7 में हमने CSS Indent को रोका था, लेकिन लिस्ट का अपना XML (<w:numPr>) 
        # अप्लाई करना बाकी था। हम 'ListController' को कॉल करेंगे जो:
        # A. बुलेट/नंबर (<w:numId>) सेट करेगा (ताकि सिंबल दिखे)।
        # B. IndentMath (<w:ind>) सेट करेगा (ताकि सीढ़ी जैसा इंडेंट आए)।
        
        if style_data.get('num_id') is not None:
            # Lazy Import: सर्कुलर डिपेंडेंसी से बचने के लिए इसे फंक्शन के अंदर इम्पोर्ट करें
            from kritidocx.objects.list.list_controller import ListController
            ListController.apply_formatting(paragraph, style_data)
        # यदि यह सेल के अंदर का इकलौता पैराग्राफ है, 
        # तो Word का डिफ़ॉल्ट 'Margin Bottom 10pt' सेल को गंदा दिखाता है।
        # लेकिन 0pt मैथ को बॉर्डर से चिपकाता है।
        # संतुलन के लिए:
        if 'margin-bottom' not in style_data:
             # सेल के भीतर न्यूनतम 2pt का सुरक्षित गैप रखें
             paragraph.paragraph_format.space_after = Pt(2)
       
            
    # -------------------------------------------------------------------------
    # 📍 INTERNAL HANDLERS
    # -------------------------------------------------------------------------

    @classmethod
    def _apply_alignment(cls, paragraph, style):
        # [CRITICAL FIX]: Enum Safe Handling
        align = style.get('text-align') or style.get('align')
        
        if not align: return

        # केस 1: अगर यह स्ट्रिंग है (HTML CSS से)
        if isinstance(align, str):
            align_key = align.lower().strip()
            if align_key in cls.ALIGN_MAP:
                paragraph.alignment = cls.ALIGN_MAP[align_key]
        
        # केस 2: अगर यह पहले से Enum Object (int) है (Table/List logic से)
        # क्योंकि CellManager सीधा Enum पास कर रहा है
        elif isinstance(align, int):
            # यह सीधे WD_ENUM है, इसे असाइन करें
            paragraph.alignment = align
            
        # केस 3: अगर यह कोई और ऑब्जेक्ट है (Enum Object)
        elif hasattr(align, 'value'): # For robust enum checks
             paragraph.alignment = align

  
    @classmethod
    def _apply_indentation(cls, paragraph, style):
        # [STEP 7 FIX]: List Conflict Guard
        # यदि यह पैराग्राफ एक 'List Item' है (num_id मौजूद है), तो 
        # सामान्य इंडेंटेशन लॉजिक को छोड़ दें (Skip)।
        # कारण: लिस्ट का इंडेंटेशन 'IndentMath' और 'ListController' द्वारा 
        # सटीक तरीके से (<w:ind> टैग के जरिए) संभाला जाता है।
        if style.get('num_id') is not None or style.get('list_depth') is not None:
            return

        p_fmt = paragraph.paragraph_format
        
        # 1. Left/Right Indent
        left_css = style.get('margin-left') or style.get('padding-left')        
        # सुधार: प्राथमिकता स्थानीय CSS को दें, फिर संचित (accumulated) indent को
        if left_css:
            indent_twips = UnitConverter.to_twips(left_css)
        else:
            indent_pt = style.get('indent_pt', 0)
            indent_twips = int(indent_pt * 20)

        if indent_twips > 0:
            p_fmt.left_indent = Twips(indent_twips)

        # 2. Hanging Indent (text-indent)
        ti_str = style.get('text-indent')
        if ti_str:
            ti_twips = UnitConverter.to_twips(ti_str)
            # python-docx में नेगेटिव वैल्यू ऑटोमैटिकली Hanging Indent बनाती है
            p_fmt.first_line_indent = Twips(ti_twips)
        
        
  
    @classmethod
    def _apply_spacing(cls, paragraph, style):
        """
        [UPDATED FIX] Controls Line Height & Margin.
        Reverts 'Space After' to Theme Defaults unless CSS explicitly sets it to 0.
        """
        
        # -------------------------------------------------------------
        # 1. Spacing Calculation (Before/After) - BALANCED FIX
        # -------------------------------------------------------------
        
        m_top_str = style.get('margin-top') or style.get('padding-top')
        m_bot_str = style.get('margin-bottom') or style.get('padding-bottom')

        # SPACE BEFORE:
        if m_top_str is not None and str(m_top_str).strip() != "":
            before_twips = UnitConverter.to_twips(m_top_str, default=0)
        else:
            # Theme default (आमतौर पर 0 होता है)
            before_pt = ThemeConfig.PARAGRAPH_SPACING.get('space_before', 0)
            before_twips = int(before_pt * 20)

        # SPACE AFTER (Main Logic Update):
        # -------------------------------
        
        # [UPDATED FIX]: Visual Box Detection
        # चेक करें कि क्या बैकग्राउंड कलर या बॉर्डर मौजूद है।
        has_bg = style.get('background-color') or style.get('background') or style.get('highlight')
        has_border = style.get('border') or style.get('border-bottom') or style.get('border-top')
        is_visual_box = (has_bg and has_bg != 'transparent') or has_border

        if m_bot_str is not None and str(m_bot_str).strip() != "":
            # Case A: CSS मौजूद है (Explicit CSS) - उपयोगकर्ता के इनपुट का सम्मान करें
            after_twips = UnitConverter.to_twips(m_bot_str, default=0)
        else:
            # [REVISED FIX]: Visual Box Spacing
            # "New Line Removal" (Router.py) ने बॉक्स के अंदर की एक्स्ट्रा जगह हटा दी है।
            # अब हमें बॉक्स के बाहर (नीचे) स्पेस को 0 करने की जरूरत नहीं है, 
            # अन्यथा दो अलग-अलग बॉक्स आपस में चिपक जाते हैं (जैसा आपकी फोटो में हुआ)।
            
            # हम केवल तभी स्पेस 0 करेंगे जब यूजर ने 'margin: 0' या 'margin-bottom: 0' दिया हो।
            # अन्यथा Theme Default (10pt) का उपयोग करें।
            
            theme_pt = ThemeConfig.PARAGRAPH_SPACING.get('space_after', 10)
            after_twips = int(theme_pt * 20)
        # -------------------------------------------------------------
        # 2. Line Height Calculation (As-Is)
        # -------------------------------------------------------------
        lh = style.get('line-height') or style.get('line_height')
        
        # Default: Single Spacing
        line_val = 240      
        line_rule = 'auto'

        if lh:
            raw_lh = str(lh).strip().lower()
            if raw_lh == 'normal':
                pass 
            elif '%' in raw_lh:
                try:
                    pct = float(raw_lh.replace('%', ''))
                    line_val = int((pct / 100.0) * 240)
                    line_rule = 'auto'
                except: pass
            elif re.match(r'^[\d\.]+$', raw_lh):
                 try:
                    factor = float(raw_lh)
                    line_val = int(factor * 240)
                    line_rule = 'auto'
                 except: pass
            elif any(u in raw_lh for u in ['px', 'pt', 'cm', 'in']):
                exact_twips = UnitConverter.to_twips(raw_lh)
                if exact_twips > 0:
                    line_val = exact_twips
                    line_rule = 'exact'


        if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
            print(f"   📏 [ParaManager-Debug] Setting Space After to: {after_twips} Twips "
                  f"(Source: {m_bot_str})")

        # --- [PRO FIX UPDATED]: Vertical Bar Spacing Correction ---
        has_vertical_bar = any(k in style for k in ['border-left', 'border-right'])
        
        if has_vertical_bar:
            # 1. बॉर्डर टूटने से रोकने के लिए After Space कम करें
            # लेकिन इसे पूरा 0 न करें, नहीं तो हेडिंग के बाद टेक्स्ट चिपक जाता है।
            # अगर CSS में Margin-Bottom है तो उसका सम्मान करें, वरना थोड़ा गैप दें।
            if m_bot_str is None or str(m_bot_str).strip() == "":
                # 0 की बजाय छोटा गैप रखें ताकि लाइनें चिपके नहीं
                from docx.shared import Pt
                after_twips = int(Pt(4) * 20) 
            
            # 2. 🔥 CRITICAL CHANGE: EXACT HEIGHT REMOVAL
            # पहले हम यहाँ line_rule = 'exact' कर रहे थे, जो Padding वाले बॉक्स (H2) को काट रहा था।
            # अब हम इसे हटा देंगे या 'auto' (Single/1.15) रहने देंगे।
            
            # (नया सुरक्षित कोड:) ✅
            # अगर पैराग्राफ में पैडिंग है, तो फिक्स्ड हाइट न लगाएं
            has_padding = any('padding' in k for k in style.keys())
            
            if has_padding:
                # पैडिंग के साथ हाइट 'auto' होनी चाहिए ताकि बॉक्स बड़ा हो सके
                # डिफ़ॉल्ट values (line_val, line_rule) को ऊपर से आने दें (जो 'auto' हैं)
                pass 
            else:
                # केवल तभी टाइट करें जब पैडिंग न हो (जैसे कोट्स के लिए बॉर्डर)
                # यह हिंदी मात्राओं के लिए सेफ है लेकिन पैडिंग को नहीं काटेगा
                pass


        # -------------------------------------------------------------
        # 3. UNIFIED XML INJECTION
        # -------------------------------------------------------------
        XmlBuilder.set_paragraph_spacing(
            paragraph, 
            before=before_twips, 
            after=after_twips, 
            line=line_val, 
            line_rule=line_rule
        )
        
        
    @classmethod
    def _apply_shading(cls, paragraph, style):
        """Applies Block-level Background Color."""
        bg_color = style.get('block_bg') or style.get('background-color')
        
        # Filter transparent or 'none' logic via ColorManager internally? No, explicit check.
        if bg_color and bg_color != 'transparent' and 'none' not in str(bg_color):
            hex_val = ColorManager.get_hex(bg_color)
            if hex_val:
                # Call XML Builder
                XmlBuilder.set_paragraph_shading(paragraph, hex_val)

    @classmethod
    def _apply_borders(cls, paragraph, style):
        """
        Parses CSS Borders and creates <w:pBdr>.
        Supports individual sides.
        """
        # यदि यह पैराग्राफ किसी Table Cell के अंदर है, तो DIV का बॉर्डर खुद पर न लगायें
        if hasattr(paragraph, '_parent') and paragraph._parent.__class__.__name__ == '_Cell':
             # यहाँ सिर्फ तभी बॉर्डर लगायें जब CSS में EXPLICITLY P टैग पर बॉर्डर लिखा हो 
             # न कि वो ऊपर से आ रहा हो। (Context-check logic)
             return

        
        # Logic to parse borders is in Basics Layer, but here we detect IF needed
        sides = ['top', 'bottom', 'left', 'right']
        
        # Shortcut: Check global border string
        border_all = style.get('border')
        
        for side in sides:
            val_str = style.get(f'border-{side}') or border_all
            
            # BorderParser logic
            if val_str:
                b_props = BorderParser.parse(val_str)
                if b_props and b_props['sz'] > 0:
                    XmlBuilder.set_paragraph_border(
                        paragraph,
                        side=side,
                        size=b_props['sz'],
                        color=b_props['color'],
                        style=b_props['val']
                    )

    @classmethod
    def _apply_pagination(cls, paragraph, style):
        """Controls how text breaks across pages."""
        p_fmt = paragraph.paragraph_format
        
        # Page Break Before
        if 'page-break-before' in style or 'break-before' in style:
            val = style.get('page-break-before') or style.get('break-before')
            if 'always' in str(val) or 'page' in str(val):
                p_fmt.page_break_before = True

        # Keep Together (page-break-inside: avoid)
        p_in = style.get('page-break-inside') or style.get('break-inside')
        if p_in and 'avoid' in str(p_in):
            p_fmt.keep_together = True
            
        # Keep With Next (prevent heading orphans)
        # Heuristic: If this para looks like a header (h1-h6 in router sets formatting), force keep
        # Handled in HeadingManager, but safe to allow manual override here? Yes.