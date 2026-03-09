"""
from kritidocx.utils.logger import logger
TEXT XML FACTORY (The Typographer's Tool)
-----------------------------------------
Responsibility:
Generates XML elements for Paragraph Properties (pPr) and Run Properties (rPr).

Core Functions:
1. Shading & Borders (Backgrounds).
2. Numbering (List association).
3. Fonts & Scripts (Complex script handling).
4. Indentation & Spacing logic.

Safety Mechanism:
Calls `XmlBase.sort_element_children` after every insertion to ensure
the file remains valid according to Word Schema.
"""

from docx.oxml.ns import qn

from kritidocx.config.settings import AppConfig
from kritidocx.utils import logger
from .base import XmlBase

class TextXml(XmlBase):
    """
    Low-level XML writer for Text elements.
    """

    # =========================================================================
    # 1. 🧢 RUN PROPERTIES (rPr) - Character Level
    # =========================================================================

    @staticmethod
    def _get_or_create_rPr(run_element):
        """Helper to safely fetch rPr from a Run element."""
        rPr = run_element.find(qn('w:rPr'))
        if rPr is None:
            rPr = XmlBase.create_element('w:rPr')
            run_element.insert(0, rPr)
        return rPr

    @classmethod
    def set_run_fonts(cls, run, font_config):
        """
        [ADVANCED] Sets generic and complex script fonts simultaneously.
        font_config = {'ascii': 'Calibri', 'cs': 'Mangal', 'hint': 'default', ...}
        """
        rPr = cls._get_or_create_rPr(run._element)
        
        # Upsert: Delete old w:rFonts if exists
        cls.upsert_child(rPr, None, order_list=None) # Clears collision if we find logic to remove specific tag
        
        # Create fresh w:rFonts tag
        rFonts = cls.create_element('w:rFonts')
        
        # Apply attributes safely
        if font_config.get('ascii'):
            cls.create_attribute(rFonts, 'w:ascii', font_config['ascii'])
            cls.create_attribute(rFonts, 'w:hAnsi', font_config['ascii'])
            
        if font_config.get('cs'):
            # Complex Script (Hindi/Arabic)
            cls.create_attribute(rFonts, 'w:cs', font_config['cs'])
            
        if font_config.get('eastAsia'):
            # CJK (Chinese/Japanese)
            cls.create_attribute(rFonts, 'w:eastAsia', font_config['eastAsia'])
            
        if font_config.get('hint'):
            # Render hint ('eastAsia' helps checkbox rendering)
            cls.create_attribute(rFonts, 'w:hint', font_config['hint'])

        # Insert using Base safe updater logic
        cls.upsert_child(rPr, rFonts, cls.R_PR_ORDER)

    @classmethod
    def set_run_color(cls, run, hex_color):
        """Sets text color."""
        rPr = cls._get_or_create_rPr(run._element)
        
        color_tag = cls.create_element('w:color')
        cls.create_attribute(color_tag, 'w:val', hex_color)
        
        cls.upsert_child(rPr, color_tag, cls.R_PR_ORDER)

    @classmethod
    def set_underline_advanced(cls, run, style='single', hex_color=None):
        """Sets underline style and optional color via XML."""
        rPr = cls._get_or_create_rPr(run._element)
        u_tag = cls.create_element('w:u')
        
        # Style setting (single, double, wavy, etc.)
        cls.create_attribute(u_tag, 'w:val', style)
        
        # Color setting (Optional)
        if hex_color:
            cls.create_attribute(u_tag, 'w:color', hex_color)
            
        cls.upsert_child(rPr, u_tag, cls.R_PR_ORDER)


    @classmethod
    def set_run_shading(cls, run, hex_color):
        """Sets text highlight/shading background (Not standard Highlighter)."""
        rPr = cls._get_or_create_rPr(run._element)
        
        shd = cls.create_element('w:shd')
        cls.create_attribute(shd, 'w:val', 'clear')
        cls.create_attribute(shd, 'w:fill', hex_color)
        
        cls.upsert_child(rPr, shd, cls.R_PR_ORDER)

    @classmethod
    def set_run_border(cls, run, size=4, val='single', color='auto'):
        """
        [NEW FEATURE]: Text Inline Border (Span Border).
        Creates <w:bdr> inside <w:rPr>.
        This makes the border hug the text content perfectly.
        """
        rPr = cls._get_or_create_rPr(run._element)
        
        # Word XML allows a single 'bdr' tag for run properties
        bdr = cls.create_element('w:bdr')
        cls.create_attribute(bdr, 'w:val', val)
        cls.create_attribute(bdr, 'w:sz', str(size))
        cls.create_attribute(bdr, 'w:space', '0')
        cls.create_attribute(bdr, 'w:color', color)
        
        cls.upsert_child(rPr, bdr, cls.R_PR_ORDER)

          
    @classmethod
    def set_run_effects(cls, run, spacing=0, shadow=None, glow=None, outline=None, reflection=None,gradient=None,shading_advanced=None):
        """
        Master Method: Distributes formatting tasks to specialized helpers.
        """
        rPr = cls._get_or_create_rPr(run._element)
        
        # 1. Spacing (Letter Spacing)
        if spacing and int(spacing) != 0:
            cls._set_spacing_xml(rPr, spacing)
            
        # 2. Shadow (Legacy or Modern)
        if shadow:
            if isinstance(shadow, dict):
                cls._set_modern_shadow_xml(rPr, shadow)
            elif shadow is True:
                cls._set_legacy_shadow_xml(rPr)

        # 3. Glow Effect
        if glow:
            cls._set_glow_xml(rPr, glow)

        # 4. Text Outline (Stroke)
        if outline:
            cls._set_outline_xml(rPr, outline)  
           
           
        # 5. reflection   
        if reflection:
             if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
                logger.debug(f"   🏗️ [TextXml] CALLING Reflection Helper Method")

             cls._set_reflection_xml(rPr, reflection)        
           
        # 6. reflection     
        if gradient:
            cls._set_gradient_xml(rPr, gradient)   
        
        # 7. shading advanced
        if shading_advanced:
            cls._set_shading_advanced_xml(rPr, shading_advanced)

       
    @classmethod
    def _set_spacing_xml(cls, rPr, val_twips):
        """
        अक्षरों के बीच की दूरी (Letter Spacing) को नियंत्रित करता है।
        XML: <w:spacing w:val="20"/>
        """
        spacing = cls.create_element('w:spacing')
        # Word को ट्विप्स में वैल्यू चाहिए होती है
        cls.create_attribute(spacing, 'w:val', str(val_twips))
        cls.upsert_child(rPr, spacing, cls.R_PR_ORDER)

    @classmethod
    def _set_legacy_shadow_xml(cls, rPr):
        """
        पुराने स्टाइल की साधारण शैडो (Classic Shadow)।
        XML: <w:shadow/>
        """
        shadow = cls.create_element('w:shadow')
        # यह सिर्फ टैग की उपस्थिति से ही काम करता है (Boolean effect)
        cls.upsert_child(rPr, shadow, cls.R_PR_ORDER)

    @classmethod
    def set_run_element_color(cls, run_element, hex_color):
        """सीधे XML एलिमेंट (जैसे Math run) का रंग बदलने के लिए।"""
        # इसमें 'run' object नहीं, सीधा 'element' आता है
        rPr = cls._get_or_create_rPr(run_element)
        color_tag = cls.create_element('w:color')
        cls.create_attribute(color_tag, 'w:val', hex_color.replace('#', ''))
        cls.upsert_child(rPr, color_tag, cls.R_PR_ORDER)
    
        
    @classmethod
    def _set_modern_shadow_xml(cls, rPr, shadow):
        """
        Specialized Helper for Modern Office 2010 Shadow Effects (w14:shadow).
        Expects: shadow dict with {dist, dir, blurRad, color}
        """
        # 1. मुख्य शैडो कंटेनर तैयार करें
        # यह टैग Word के 'Text Effects' पैनल में दिखाई देने वाली सेटिंग्स को नियंत्रित करता है
        shd_tag = cls.create_element('w14:shadow')
        
        # 2. बुनियादी ज्यामिति (Basic Geometry)
        # blurRad, dist और dir 'ShadowParser' से EMUs और Angle units में आते हैं
        cls.create_attribute(shd_tag, 'w14:blurRad', shadow.get('blurRad', 0))
        cls.create_attribute(shd_tag, 'w14:dist', shadow.get('dist', 0))
        cls.create_attribute(shd_tag, 'w14:dir', shadow.get('dir', 0))
        
        # 3. स्थिरता गुण (Consistency Properties)
        # sx, sy (Scale 100%) और kx, ky (Skew 0) वर्ड के मानक मान हैं। 
        # ये टैग्स मौजूद न होने पर वर्ड कभी-कभी शैडो को गलत तरीके से स्ट्रेच कर देता है।
        cls.create_attribute(shd_tag, 'w14:sx', '100000') # 100.000%
        cls.create_attribute(shd_tag, 'w14:sy', '100000') # 100.000%
        cls.create_attribute(shd_tag, 'w14:kx', '0')
        cls.create_attribute(shd_tag, 'w14:ky', '0')
        cls.create_attribute(shd_tag, 'w14:algn', 'tl')  # Top-Left Alignment

        # 4. रंग और पारदर्शिता (Color & Transparency)
        # HEX कोड से '#' हटाएं
        clean_color = str(shadow.get('color', '000000')).replace('#', '')
        srgb = cls.create_element('w14:srgbClr')
        cls.create_attribute(srgb, 'w14:val', clean_color)

        # वर्ड की डिफॉल्ट परछाई थोड़ी ट्रांसपेरेंट (Opacity) होती है। 
        # हमने इसे 50% (50000) रखा है जैसा आपके वर्ड उदाहरण में था।
        alpha = cls.create_element('w14:alpha')
        cls.create_attribute(alpha, 'w14:val', '50000') 
        srgb.append(alpha)

        shd_tag.append(srgb)

        # 5. अंतिम XML इंजेक्शन
        # R_PR_ORDER सुनिश्चित करता है कि 'w14:shadow' अपनी सही जगह पर जाए
        cls.upsert_child(rPr, shd_tag, cls.R_PR_ORDER)       
             
             
    @classmethod
    def _set_glow_xml(cls, rPr, glow):
        """
        Specialized Helper for Modern Glow Effects (w14:glow).
        Input 'glow' dict: {'rad': EMUs, 'color': HEX}
        """
        # 1. मुख्य ग्लो कंटेनर तैयार करें
        # 'w14:rad' टैग ग्लो के फैलाव (Radius) को तय करता है
        glow_tag = cls.create_element('w14:glow')
        
        # 'rad' को EMUs में सेट करें। 
        # (उदाहरण: CSS 8px ग्लो ≈ 762000 EMUs के बराबर हो सकता है)
        cls.create_attribute(glow_tag, 'w14:rad', glow.get('rad', 0))

        # 2. रंग निर्धारण (Color Specification)
        # CSS हेक्स कलर को साफ करें (Remove # if present)
        clean_color = str(glow.get('color', '000000')).replace('#', '')
        
        # ग्लो के लिए हम 'w14:srgbClr' का उपयोग करते हैं
        srgb = cls.create_element('w14:srgbClr')
        cls.create_attribute(srgb, 'w14:val', clean_color)

        # 3. पारदर्शिता और जीवंतता (Alpha/Transparency)
        # ग्लो को 'सॉफ्ट' दिखाने के लिए उसमें अल्फा (Alpha) जोड़ना ज़रूरी है। 
        # 60000 (60% opacity) एक संतुलित मान है।
        alpha = cls.create_element('w14:alpha')
        cls.create_attribute(alpha, 'w14:val', '60000') 
        srgb.append(alpha)

        # रंग को ग्लो टैग के अंदर डालें
        glow_tag.append(srgb)

        # 4. XML ट्री में इन्जेक्ट करें
        # सुनिश्चित करें कि R_PR_ORDER में 'w14:glow' परिभाषित है
        cls.upsert_child(rPr, glow_tag, cls.R_PR_ORDER)
        
       
    @classmethod
    def _set_outline_xml(cls, rPr, outline):
        """
        Specialized Helper for Text Outline (Stroke) via w14:textOutline.
        Input 'outline' dict: {'w': EMUs, 'color': HEX}
        """
        # 1. मुख्य आउटलाइन कंटेनर तैयार करें
        # 'w' एट्रिब्यूट लाइन की चौड़ाई (Stroke Weight) को EMUs में तय करता है।
        out_tag = cls.create_element('w14:textOutline')
        
        # आउटलाइन की चौड़ाई (Width)
        cls.create_attribute(out_tag, 'w14:w', outline.get('w', 9525)) # Default 0.75pt approx
        
        # लाइन कैप और कंपाउंड स्टाइल (Standard Settings)
        cls.create_attribute(out_tag, 'w14:cap', 'flat') # कैप स्टाइल
        cls.create_attribute(out_tag, 'w14:cmpd', 'sng') # सिंगल लाइन (Simple)
        cls.create_attribute(out_tag, 'w14:algn', 'ctr') # अलाइनमेंट: सेंटर

        # 2. सॉलिड फिल निर्धारण (Solid Fill & Color)
        # आउटलाइन के अंदर रंग भरने के लिए 'w14:solidFill' आवश्यक है
        fill_tag = cls.create_element('w14:solidFill')
        
        srgb = cls.create_element('w14:srgbClr')
        clean_color = str(outline.get('color', '000000')).replace('#', '')
        cls.create_attribute(srgb, 'w14:val', clean_color)
        
        # कलर को फिल टैग में डालें
        fill_tag.append(srgb)
        # फिल को मुख्य आउटलाइन टैग में डालें
        out_tag.append(fill_tag)

        # 3. डैश और जॉइन स्टाइल (Styling Extras)
        # 'w14:prstDash' यह सुनिश्चित करता है कि आउटलाइन टूटी हुई न हो (Solid line)
        dash_tag = cls.create_element('w14:prstDash')
        cls.create_attribute(dash_tag, 'w14:val', 'solid')
        out_tag.append(dash_tag)

        # 'w14:round' जॉइंट्स को गोल (Smooth) बनाता है, जो अक्षरों पर बेहतर दिखता है
        round_tag = cls.create_element('w14:round')
        out_tag.append(round_tag)

        # 4. XML इंजेक्शन
        # सुनिश्चित करें कि R_PR_ORDER में 'w14:textOutline' सही क्रम में हो
        cls.upsert_child(rPr, out_tag, cls.R_PR_ORDER)  
           
     
    @classmethod
    def _set_reflection_xml(cls, rPr, reflection):
        """
        [ULTIMATE VERSION] - Matches exact Word 2010 Manual XML structure.
        Uses stA, endA, and fadeDir attributes.
        """
        ref_tag = cls.create_element('w14:reflection')
        
        # 1. Geometry & Distortion
        # dist, blurRad 'unit_converter' के ज़रिए EMUs में होने चाहिए
        cls.create_attribute(ref_tag, 'w14:blurRad', str(reflection.get('blur', 6350)))
        cls.create_attribute(ref_tag, 'w14:dist', str(reflection.get('dist', 29997)))
        
        # 2. Reflection Physics (Angles & Scales)
        cls.create_attribute(ref_tag, 'w14:dir', '5400000')      # 90 degrees (Straight Down)
        cls.create_attribute(ref_tag, 'w14:fadeDir', '5400000') # Fade direction downward
        cls.create_attribute(ref_tag, 'w14:sx', '100000')       # X-Scale 100%
        cls.create_attribute(ref_tag, 'w14:sy', '-100000')      # Y-Scale -100% (Vertical Flip)
        cls.create_attribute(ref_tag, 'w14:kx', '0')
        cls.create_attribute(ref_tag, 'w14:ky', '0')
        cls.create_attribute(ref_tag, 'w14:algn', 'bl')         # Bottom-Left Alignment (MATCHED)

        # 3. Alpha & Fading (Alpha is measured in 1/1000 percent)
        # stA (Start Alpha): 100% = 100000
        start_alpha = str(reflection.get('alpha', 60000))       # Default 60% as per your XML
        
        cls.create_attribute(ref_tag, 'w14:stA', start_alpha)
        cls.create_attribute(ref_tag, 'w14:stPos', '0')         # Fading starts at 0%
        cls.create_attribute(ref_tag, 'w14:endA', '900')         # Ends almost invisible (900/100000)
        cls.create_attribute(ref_tag, 'w14:endPos', '60000')     # Fading finishes at 60% height

        # Final Injection
        cls.upsert_child(rPr, ref_tag, cls.R_PR_ORDER)  
        
        res = cls.upsert_child(rPr, ref_tag, cls.R_PR_ORDER)

        if getattr(AppConfig, 'DEBUG_TEXT_LAYOUT', False):
             logger.debug(f"   ✅ [TextXml] Reflection Injected into XML Order: {res}")
   
        
    @classmethod
    def _set_gradient_xml(cls, rPr, gradient):
        """
        [ULTIMATE VERSION] Matches Manual Word XML: 
        w14:textFill -> w14:gradFill -> w14:gsLst -> w14:gs
        """
        # 1. सबसे बाहरी कंटेनर
        text_fill = cls.create_element('w14:textFill')
        
        # 2. ग्रेडिएंट मुख्य टैग
        grad_fill = cls.create_element('w14:gradFill')
        
        # 3. ग्रेडिएंट स्टॉप लिस्ट (वैल्यूज़ w14 नेम्सपेस में)
        gs_lst = cls.create_element('w14:gsLst')
        
        colors = gradient.get('colors', [])
        count = len(colors)
        
        for i, hex_col in enumerate(colors):
            # स्थिति गणना (0, 50000, 100000)
            pos = str(int((i / (count - 1)) * 100000)) if count > 1 else "0"
            
            gs = cls.create_element('w14:gs')
            cls.create_attribute(gs, 'w14:pos', pos)
            
            # रंग (w14:srgbClr)
            srgb = cls.create_element('w14:srgbClr')
            cls.create_attribute(srgb, 'w14:val', hex_col.replace('#', ''))
            
            # [Optional]: यदि आप मैन्युअल XML की तरह हल्का टिंट जोड़ना चाहें तो यहाँ जोड़ सकते हैं
            # अभी के लिए हम सॉलिड हेक्स इस्तेमाल कर रहे हैं।
            
            gs.append(srgb)
            gs_lst.append(gs)

        # 4. एंगल निर्धारण (Linear Angle)
        # आपके मैनुअल XML में '10800000' (180 degree) था। 
        # नीचे से ऊपर के लिए: 5400000 (90 degree)।
        lin = cls.create_element('w14:lin')
        cls.create_attribute(lin, 'w14:ang', str(gradient.get('angle', 5400000)))
        cls.create_attribute(lin, 'w14:scaled', '0')

        # असेंबली (अंदर से बाहर)
        grad_fill.append(gs_lst)
        grad_fill.append(lin)
        text_fill.append(grad_fill)

        # अंतिम इंजेक्शन rPr में
        cls.upsert_child(rPr, text_fill, cls.R_PR_ORDER)  
    
    @classmethod
    def set_run_scaling(cls, run, scale_val):
        """
        Sets Horizontal Scaling (Character Width).
        scale_val: Integer (100 = normal, 150 = expanded)
        """
        rPr = cls._get_or_create_rPr(run._element)
        
        # <w:w> का मतलब है Width Scale
        w_tag = cls.create_element('w:w')
        cls.create_attribute(w_tag, 'w:val', str(scale_val))
        
        # 'w' आर्डर में spacing और kern के बीच में होता है
        cls.upsert_child(rPr, w_tag, cls.R_PR_ORDER)
    
    @classmethod
    def set_run_position(cls, run, pos_val):
        """
        Raises or Lowers text from baseline.
        pos_val: Integer in half-points (Positive for Up, Negative for Down)
        """
        rPr = cls._get_or_create_rPr(run._element)
        
        # <w:position> टैग बनाना
        pos_tag = cls.create_element('w:position')
        cls.create_attribute(pos_tag, 'w:val', str(pos_val))
        
        # XML ट्री में इंजेक्ट करना
        cls.upsert_child(rPr, pos_tag, cls.R_PR_ORDER)
          
          
    @classmethod
    def _set_shading_advanced_xml(cls, rPr, data):
        """
        Safe version for Advanced Shading Patterns.
        Handles None values to prevent .replace() errors.
        """
        shd = cls.create_element('w:shd')
        
        # 1. पैटर्न का प्रकार
        cls.create_attribute(shd, 'w:val', data.get('val', 'solid'))
        
        # 2. फोरग्राउंड कलर (पैटर्न कलर) - सुरक्षा जाँच के साथ
        color = data.get('color')
        if color and isinstance(color, str):
            clean_color = color.replace('#', '')
            cls.create_attribute(shd, 'w:color', clean_color)
        else:
            # अगर रंग नहीं है, तो 'auto' सेट करें
            cls.create_attribute(shd, 'w:color', 'auto')
        
        # 3. फिल कलर (बैकग्राउंड) - सुरक्षा जाँच के साथ
        fill = data.get('fill')
        if fill and isinstance(fill, str) and fill != 'transparent':
            clean_fill = fill.replace('#', '')
            cls.create_attribute(shd, 'w:fill', clean_fill)
        else:
            # अगर कोई फिल नहीं है तो एट्रीब्यूट न लगायें या पारदर्शी रखें
            pass

        # R_PR_ORDER में जोड़ें
        cls.upsert_child(rPr, shd, cls.R_PR_ORDER)
         
    @classmethod
    def set_run_shading_advanced(cls, run, shading_data):
        """
        असली काम यहाँ हो रहा है। 'cls' के जरिए यह '_get_or_create_rPr' को 
        अपनी ही क्लास में ढूंढ लेगा।
        """
        # 1. 'rPr' बनाओ (यह औजार TextXml क्लास में मौजूद है)
        rPr = cls._get_or_create_rPr(run._element)
        
        # 2. हेल्पर को बुलाओ जो XML टैग बनाएगा
        cls._set_shading_advanced_xml(rPr, shading_data)
     
                        
    # =========================================================================
    # 2. 🧱 PARAGRAPH PROPERTIES (pPr) - Block Level
    # =========================================================================

    @staticmethod
    def _get_or_create_pPr(paragraph):
        return paragraph._element.get_or_add_pPr()

    @classmethod
    def set_paragraph_shading(cls, paragraph, hex_color):
        """Block Background Color (entire paragraph width)."""
        pPr = cls._get_or_create_pPr(paragraph)
        
        shd = cls.create_element('w:shd')
        cls.create_attribute(shd, 'w:val', 'clear')
        cls.create_attribute(shd, 'w:fill', hex_color)
        
        cls.upsert_child(pPr, shd, cls.P_PR_ORDER)

    @classmethod
    def set_paragraph_border(cls, paragraph, side='bottom', size=6, color='auto', style='single'):
        """
        [NEW] Adds paragraph borders (e.g. underline for Headings, box for quotes).
        Sides: 'top', 'bottom', 'left', 'right', 'bar'.
        """
        pPr = cls._get_or_create_pPr(paragraph)
        
        # pBdr container creation
        pBdr = pPr.find(qn('w:pBdr'))
        if pBdr is None:
            pBdr = cls.create_element('w:pBdr')
            # Warning: pBdr has internal order too, but python-docx doesn't crash on this usually.
            # Ideally: Insert logic. For simplicity, we create wrapper and manage sides inside.
        
        side_tag = cls.create_element(f"w:{side}")
        cls.create_attribute(side_tag, 'w:val', style)
        cls.create_attribute(side_tag, 'w:sz', str(size))
        cls.create_attribute(side_tag, 'w:space', '1') # Space between text and line
        cls.create_attribute(side_tag, 'w:color', color)
        
        # Remove old side if exists
        cls.upsert_child(pBdr, side_tag, None) # Borders inside pBdr aren't strict sorted, but good practice
        
        # Update Main Properties
        cls.upsert_child(pPr, pBdr, cls.P_PR_ORDER)

    @classmethod
    def set_indent(cls, paragraph, left=0, right=0, first_line=0, hanging=0):
        """Sets strict indentation."""
        pPr = cls._get_or_create_pPr(paragraph)
        
        ind = cls.create_element('w:ind')
        
        # Only set non-zero or specific logic attributes
        if left: cls.create_attribute(ind, 'w:left', str(left))
        if right: cls.create_attribute(ind, 'w:right', str(right))
        
        # Mutual exclusive: FirstLine vs Hanging
        if hanging:
            cls.create_attribute(ind, 'w:hanging', str(hanging))
        elif first_line:
            cls.create_attribute(ind, 'w:firstLine', str(first_line))
            
        cls.upsert_child(pPr, ind, cls.P_PR_ORDER)

    @classmethod
    def set_outline_level(cls, paragraph, level):
        """
        Sets Heading Outline Level.
        XML: <w:outlineLvl w:val="0"/> (0=Heading 1)
        """
        if level is None: return
        
        pPr = cls._get_or_create_pPr(paragraph)
        
        # पुराना हटाएं
        existing = pPr.find(qn('w:outlineLvl'))
        if existing is not None:
            pPr.remove(existing)
            
        # नया जोड़ें
        outLvl = cls.create_element('w:outlineLvl')
        cls.create_attribute(outLvl, 'w:val', str(level))
        
        # P_PR_ORDER में यह शामिल है, सो सॉर्टिंग काम करेगी
        cls.upsert_child(pPr, outLvl, cls.P_PR_ORDER)


    @classmethod
    def set_spacing(cls, paragraph, before=0, after=0, line=240, line_rule='auto'):
        """
        Controls spacing between paragraphs and lines.
        Line Rule: 'auto' (1.15x), 'exact' (fixed pts).
        """
        pPr = cls._get_or_create_pPr(paragraph)
        
        spacing = cls.create_element('w:spacing')
        cls.create_attribute(spacing, 'w:before', str(before))
        cls.create_attribute(spacing, 'w:after', str(after))
        cls.create_attribute(spacing, 'w:line', str(line))
        cls.create_attribute(spacing, 'w:lineRule', line_rule)
        
        cls.upsert_child(pPr, spacing, cls.P_PR_ORDER)

    @classmethod
    def set_numbering(cls, paragraph, num_id, level_id):
        """
        Associates paragraph with a List ID.
        Ref: <w:numPr> -> <w:numId> + <w:ilvl>
        """
        pPr = cls._get_or_create_pPr(paragraph)
        
        # [STEP 2 FIX]: Indentation Cleanup Logic
        # लिस्ट स्टाइल लगाते समय, पुराना मैनुअल इंडेंट (<w:ind>) हटाना अनिवार्य है।
        # यदि यह नहीं हटाया गया, तो Word "List Style Indent" और "Direct Indent" 
        # के बीच कंफ्यूज हो जाता है, जिससे बुलेट्स गायब (Hidden) हो जाते हैं।
        # (नोट: सही इंडेंट बाद में ListController द्वारा दोबारा लगाया जाएगा)
        existing_ind = pPr.find(qn('w:ind'))
        if existing_ind is not None:
            pPr.remove(existing_ind)

        numPr = cls.create_element('w:numPr')
        
        # Level must come BEFORE ID in XML Schema (Standard)
        # However, numPr children sorting is local.
        
        ilvl = cls.create_element('w:ilvl')
        cls.create_attribute(ilvl, 'w:val', str(level_id))
        numPr.append(ilvl)
        
        nid = cls.create_element('w:numId')
        cls.create_attribute(nid, 'w:val', str(num_id))
        numPr.append(nid)
        
        # Main insert
        cls.upsert_child(pPr, numPr, cls.P_PR_ORDER)