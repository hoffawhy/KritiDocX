"""
from kritidocx.utils.logger import logger
INDENT MATH MODULE (The Geometry of Lists)
------------------------------------------
Responsibility:
Calculates exact indentation values (Left margin & Hanging indent) for List Items.

Logic:
MS Word lists work on 'Hanging Indent' logic:
1. 'Left' moves the entire paragraph text body to the right.
2. 'Hanging' moves the first line (the bullet/number) BACK to the left.

Formula:
Bullet Position = Left_Value - Hanging_Value
Text Position   = Left_Value

Target Unit: Twips (1/1440 inch).
"""

from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.config.constants import DocConstants
# Debugging Switch
from kritidocx.config.settings import AppConfig
from kritidocx.utils import logger

class IndentMath:
    """
    Calculator engine for list spacing hierarchy.
    """

    # --- DEFAULTS (Based on Standard Professional Documents) ---
    
    # प्रत्येक लेवल पर कितना अंदर जाना है (0.5 inch standard = 720 Twips)
    STEP_INDENT_TWIPS = 720 
    
    # बुलेट और टेक्स्ट के बीच की दूरी (0.25 inch = 360 Twips)
    DEFAULT_HANGING_TWIPS = 360

    @classmethod
    def calculate(cls, level_idx, style_overrides=None):
        """
        Main calculation API.
        
        विशेषता: CSS की मैन्युअल पैडिंग (e.g. 1.25in) को वर्ड के डिफ़ॉल्ट पर प्राथमिकता देता है।
        यह 'padding', 'margin' और 'text-indent' सभी का विश्लेषण करता है।
        
        Args:
            level_idx (int): Current nesting level (0, 1, 2...).
            style_overrides (dict): CSS dict from parser (optional).
            
        Returns:
            tuple(int, int): (left_indent_twips, hanging_twips)
        """
        if not style_overrides: style_overrides = {}

        # 1. Base Defaults (Level-based auto calculation)
        # लेवल 0 = 720, लेवल 1 = 1440...
        base_left = cls.STEP_INDENT_TWIPS * (level_idx + 1)
        
        # Dynamic Hanging Indent (Level 2+ पर थोड़ा बड़ा गैप नंबरों के लिए)
        if level_idx >= 2:
            base_hanging = cls.DEFAULT_HANGING_TWIPS + (level_idx * 90)
        else:
            base_hanging = cls.DEFAULT_HANGING_TWIPS

        # -------------------------------------------------------------
        # 2. CUSTOM CSS LOGIC (Manual Override)
        # -------------------------------------------------------------
        # [UPDATED FIX]: Additive Logic (Margin + Padding)
        # समस्या समाधान: 'or' ऑपरेटर के कारण यदि padding '0px' थी, तो margin ignore हो रहा था।
        # HTML लेआउट में तत्व की पोजीशन = Margin + Padding दोनों का योग होती है।
        
        # A. Get Raw Values independently
        pad_val = style_overrides.get('padding-left') or style_overrides.get('padding_left')
        mar_val = style_overrides.get('margin-left') or style_overrides.get('margin_left') or style_overrides.get('left')

        # B. Convert both to Twips (0 if missing/invalid)
        p_twips = UnitConverter.to_twips(str(pad_val)) if pad_val else 0
        m_twips = UnitConverter.to_twips(str(mar_val)) if mar_val else 0
        
        # C. Total Custom Offset
        total_custom_twips = p_twips + m_twips

        final_left = base_left
        final_hanging = base_hanging

        # यदि उपयोगकर्ता ने कस्टम इंडेंटेशन दिया है (Padding या Margin किसी भी रूप में)
        if total_custom_twips > 0:
            
            # पिछले लेवल्स का आधार (Parent's indentation base)
            prev_levels_offset = cls.STEP_INDENT_TWIPS * level_idx
            
            # नई पोजीशन = पैरेंट का आधार + करंट कस्टम गैप
            final_left = int(prev_levels_offset + total_custom_twips)
            
            if getattr(AppConfig, 'DEBUG', False):
                logger.debug(f"   📏 Indent Math: Base={prev_levels_offset} + Custom({total_custom_twips}) -> {final_left}")

        # -------------------------------------------------------------
        # 3. HANGING OVERRIDE (Text Indent)
        # -------------------------------------------------------------
        # CSS 'text-indent' (-0.25in) hanging को कंट्रोल करता है
        raw_ti = style_overrides.get('text-indent') or style_overrides.get('text_indent')
        
        if raw_ti:
            ti_twips = UnitConverter.to_twips(str(raw_ti))
            
            # हैंगिंग के लिए Negative इंडेंट चाहिए होता है
            if ti_twips < 0:
                hanging_val = abs(ti_twips)
                # Safety Clamp: हैंगिंग लेफ्ट मार्जिन से ज्यादा नहीं होनी चाहिए
                final_hanging = min(hanging_val, final_left)
                
            elif ti_twips > 0:
                # पॉजिटिव इंडेंट मतलब First Line Indent (Bullet text के साथ खिसकेगी)
                # इसके लिए हम hanging को reduce करते हैं (Logic varies, sticking to safety)
                pass

        # -------------------------------------------------------------
        # 4. FINAL SAFETY CHECKS
        # -------------------------------------------------------------
        # Hanging indent कभी भी Left Indent से बड़ा नहीं होना चाहिए, 
        # वरना बुलेट पेज के मार्जिन से बाहर चली जाएगी।
        if final_hanging > final_left:
            final_hanging = final_left 

        return int(final_left), int(final_hanging)

    @classmethod
    def get_numbering_tab_stop(cls, left_indent, hanging_val):
        """
        Numbering Definitions के लिए टैब स्टॉप पोजिशन।
        आमतौर पर यह टेक्स्ट की शुरुआत (Left Indent) पर होता है।
        """
        return int(left_indent)