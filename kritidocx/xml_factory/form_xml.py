"""
from kritidocx.utils.logger import logger
FORM XML FACTORY (The Interaction Architect)
--------------------------------------------
Responsibility:
Generates Structured Document Tags (SDT) for interactive elements.
- Checkboxes (Clickable toggles).
- Dropdown Lists (Selectable options).
- Text Fields (Input areas with placeholders).
- Date Pickers.

Technical Details:
Word uses 'w:sdt' (Structured Document Tag) to define these regions.
Every SDT must have a unique ID and separate Content/Pr tags.
"""

import random
from docx.oxml.ns import qn, nsmap

from kritidocx.utils import logger
from .base import XmlBase
from kritidocx.config.settings import AppConfig

# Ensure Word 2010 namespaces are mapped for advanced controls
if 'w14' not in nsmap:
    nsmap['w14'] = 'http://schemas.microsoft.com/office/word/2010/wordml'

class FormXml(XmlBase):
    
    # [OFFICIAL FIX]: Atomic Counter initialization
    # Start from a safe high number range reserved for user/custom parts
    # (Microsoft internally uses lower IDs usually, sticking to 500M+ prevents clash)
    _atomic_id_counter = 500000000

    @classmethod
    def _generate_unique_id(cls):
        """
        [PRO-LEVEL FIX]: Generates a deterministic unique ID sequentially.
        This mathematically guarantees NO collision ever happens within a document.
        """
        # Increment counter atomically
        cls._atomic_id_counter += 1
        
        # Return string
        return str(cls._atomic_id_counter)

    @staticmethod
    def _create_sdt_wrapper(tag_name="MyControl"):
        """
        Creates the skeletal structure for any Form Control.
        Structure:
        <w:sdt>
          <w:sdtPr>
             <w:id .../>
             <w:tag .../>
          </w:sdtPr>
          <w:sdtContent>
             ...
          </w:sdtContent>
        </w:sdt>
        """
        # 1. Main Container
        sdt = XmlBase.create_element('w:sdt')
        
        # 2. Properties Container
        sdtPr = XmlBase.create_element('w:sdtPr')
        
        # ID (Required) -> Calls our new sequential generator
        id_tag = XmlBase.create_element('w:id')
        
        # [CALL]: यहाँ अब नया unique id फंक्शन कॉल होगा
        unique_val = FormXml._generate_unique_id()
        XmlBase.create_attribute(id_tag, 'w:val', unique_val)
        
        sdtPr.append(id_tag)
        
        # Tag/Alias
        if tag_name:
            tag_tag = XmlBase.create_element('w:tag')
            XmlBase.create_attribute(tag_tag, 'w:val', tag_name)
            sdtPr.append(tag_tag)
            
        sdt.append(sdtPr)
        
        # 3. Content Container
        sdtContent = XmlBase.create_element('w:sdtContent')
        sdt.append(sdtContent)
        
        return sdt, sdtPr, sdtContent

    # =========================================================================
    # 1. ☑ CHECKBOX BUILDER (Complex Script & Visuals)
    # =========================================================================
    @classmethod
    def create_checkbox(cls, parent_paragraph, checked=False, symbol_char=u"\u2612", 
                        font_name="MS Gothic", hex_color=None, font_size=24):
        
        # [DEBUG LOG]
        try:
            from kritidocx.config.settings import AppConfig
            if getattr(AppConfig, 'DEBUG_FORMS', False):
                logger.debug(f"   🛠️ [XML FACTORY] Creating Checkbox | Val: {symbol_char} | Color: {hex_color} | Sz: {font_size}")
        except: pass

        # Wrapper create
        sdt, sdtPr, sdtContent = cls._create_sdt_wrapper("checkbox_control")
        
        run = cls.create_element('w:r')
        rPr = cls.create_element('w:rPr')
        
        # --- [1. FONTS INJECTION via Upsert] ---
        # हम manual append नहीं करेंगे, ताकि ऑर्डर बना रहे
        fonts = cls.create_element('w:rFonts')
        cls.create_attribute(fonts, 'w:ascii', font_name)
        cls.create_attribute(fonts, 'w:hAnsi', font_name)
        cls.create_attribute(fonts, 'w:eastAsia', font_name)
        cls.create_attribute(fonts, 'w:hint', 'eastAsia') 
        # यह R_PR_ORDER के हिसाब से अपनी जगह लेगा
        cls.upsert_child(rPr, fonts, cls.R_PR_ORDER) 

        # --- [2. COLOR INJECTION] ---
        if hex_color and hex_color.lower() not in ['auto', 'none']:
            clean_hex = hex_color.replace('#', '').upper()
            color_tag = cls.create_element('w:color')
            cls.create_attribute(color_tag, 'w:val', clean_hex)
            cls.upsert_child(rPr, color_tag, cls.R_PR_ORDER) # ऑटो सॉर्टिंग

        # --- [3. SIZE INJECTION] ---
        if font_size:
            sz = cls.create_element('w:sz')
            cls.create_attribute(sz, 'w:val', str(font_size))
            cls.upsert_child(rPr, sz, cls.R_PR_ORDER)
            
            sz_cs = cls.create_element('w:szCs')
            cls.create_attribute(sz_cs, 'w:val', str(font_size))
            cls.upsert_child(rPr, sz_cs, cls.R_PR_ORDER)

        run.append(rPr)
        
        # Text Symbol
        t = cls.create_element('w:t')
        t.text = symbol_char
        run.append(t)
        
        sdtContent.append(run)
        
        # Parent में जोड़ें
        parent_paragraph._element.append(sdt)

    # =========================================================================
    # 2. 📋 DROPDOWN LIST (Combo Box)
    # =========================================================================
    @classmethod
    def create_dropdown(cls, parent_paragraph, items, default_text="Choose item"):
        """
        Creates a Dropdown list.
        items: List of tuples -> [("Display", "Value"), ...]
        """
        sdt, sdtPr, sdtContent = cls._create_sdt_wrapper("dropdown_list")
        
        # --- A. Properties (Define List Items) ---
        dd_list = cls.create_element('w:dropDownList')
        
        # Create Options
        for display, value in items:
            item = cls.create_element('w:listItem')
            cls.create_attribute(item, 'w:displayText', str(display))
            cls.create_attribute(item, 'w:value', str(value))
            dd_list.append(item)
            
        sdtPr.append(dd_list)
        
        # --- B. Content (Current Selection) ---
        # Usually shows the first item or a default text
        run = cls.create_element('w:r')
        t = cls.create_element('w:t')
        t.text = default_text
        run.append(t)
        sdtContent.append(run)
        
        parent_paragraph._element.append(sdt)

    # =========================================================================
    # 3. 📝 TEXT INPUT FIELD (With Placeholder)
    # =========================================================================
    @classmethod
    def create_text_input(cls, parent_paragraph, initial_text="", is_placeholder=False, multiline=True):
        """
        Creates a Text Input. 
        [UPDATED]: Supports multiLine flag and correct newline mapping.
        """
        sdt, sdtPr, sdtContent = cls._create_sdt_wrapper("text_input")
        
        # 1. Properties - Set multiline support
        text_type = cls.create_element('w:text')
        if multiline:
            cls.create_attribute(text_type, 'w:multiLine', '1') # 🔥 Word को आदेश: न्यू लाइन मानो
        sdtPr.append(text_type)
        
        if is_placeholder:
            sdtPr.append(cls.create_element('w:showingPlcHdr'))
            
        # 2. Content Injection
        run = cls.create_element('w:r')
        if is_placeholder:
            rPr = cls.create_element('w:rPr')
            color = cls.create_element('w:color'); cls.create_attribute(color, 'w:val', '888888')
            rPr.append(color); run.append(rPr)

        # 🔥 CRITICAL: \n को वर्ड ब्रेक्स में बदलें
        content = initial_text if initial_text else ""
        lines = content.split('\n')
        
        for i, line_text in enumerate(lines):
            t = cls.create_element('w:t')
            # खाली लाइन में भी space बचाएं
            if not line_text.strip() and len(lines) > 1:
                cls.create_attribute(t, 'xml:space', 'preserve')
            t.text = line_text
            run.append(t)
            
            # अगर यह आख़िरी लाइन नहीं है, तो Line Break डालें
            if i < len(lines) - 1:
                run.append(cls.create_element('w:br'))
        
        sdtContent.append(run)
        parent_paragraph._element.append(sdt)
        
        
    # =========================================================================
    # 4. 📅 DATE PICKER (Calendar)
    # =========================================================================
    @classmethod
    def create_date_picker(cls, parent_paragraph, date_iso_fmt=None):
        """
        Creates a Date Picker Control.
        date_iso_fmt: YYYY-MM-DD (Default current if displayed)
        """
        sdt, sdtPr, sdtContent = cls._create_sdt_wrapper("date_picker")
        
        # --- A. Properties ---
        # w14 namespace अक्सर जरुरी होता है (अगर error आये तो 'w:date' वापस कर देना)
        date_tag = cls.create_element('w:date')
        
        # Date Format को स्टैंडर्ड करें (d MMMM yyyy = 26 January 2026)
        date_fmt = cls.create_element('w:dateFormat')
        # user-friendly format
        cls.create_attribute(date_fmt, 'w:val', "d/M/yyyy") 
        date_tag.append(date_fmt)
        
        lid = cls.create_element('w:lid')
        cls.create_attribute(lid, 'w:val', 'en-US') # Hindi 'hi-IN' भी कर सकते हैं
        date_tag.append(lid)
        
        sdtPr.append(date_tag)
        
        # --- B. Content (Display) ---
        run = cls.create_element('w:r')
        
        # 1pt स्पेस के लिए एक नया 't' (text) नोड जोड़ें जो केवल खाली जगह हो
        t_gap = cls.create_element('w:t')
        cls.create_attribute(t_gap, 'xml:space', 'preserve')
        t_gap.text = " " # यहाँ एक स्पेस दें
        run.append(t_gap)

        
        # [Visual Update]: प्लेसहोल्डर स्टाइल
        rPr = cls.create_element('w:rPr')
        color = cls.create_element('w:color')
        cls.create_attribute(color, 'w:val', '888888') # ग्रे कलर ताकि लगे कि भरना है
        rPr.append(color)
        run.append(rPr)

        t = cls.create_element('w:t')
        t.text = "DD/MM/YYYY"  # [Select Date] की जगह यह बेहतर दिखेगा
        run.append(t)
        
        sdtContent.append(run)
        
        parent_paragraph._element.append(sdt)


    # =========================================================================
    # 5. ⚡ FIELD CODES (Variables)
    # =========================================================================
    @classmethod
    def create_field_code(cls, parent_paragraph, command_text, display_result="0"):
        """
        [MAJOR UPDATE]: फ़ील्ड्स को अब SDT (Box) में रैप किया जाता है।
        यह उसे 'Simple Text' से 'Interactive Control' बनाता है।
        """
        
        # 1. SDT Wrapper (यही वह 'Box' बनाता है जो Date जैसा दिखता है)
        # हमने tag_name को None रखा है ताकि यह एक 'Rich Text Box' बने
        sdt, sdtPr, sdtContent = cls._create_sdt_wrapper(None)
        
        # (Optional) लॉक हटाएं ताकि वैल्यू अपडेट हो सके
        # SDT properties में जाके सुनिश्चित करें कि लॉकिंग न हो
        # (wrapper डिफॉल्ट रूप से अनलॉक होता है)

        # -------------------------------------------------
        # फील्ड कंस्ट्रक्शन (Field Construction)
        # अब हम parent_paragraph के बजाय 'sdtContent' में append करेंगे
        # -------------------------------------------------

        # A. BEGIN Char (w:dirty="true" ताकि खुलते ही रीफ्रेश हो)
        r1 = cls.create_element('w:r')
        fldChar1 = cls.create_element('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        fldChar1.set(qn('w:dirty'), 'true') 
        r1.append(fldChar1)
        sdtContent.append(r1)  # <-- Changed: p -> sdtContent

        # B. Field Command ( Instruction )
        r2 = cls.create_element('w:r')
        instr = cls.create_element('w:instrText')
        instr.set(qn('xml:space'), 'preserve')
        instr.text = f" {command_text.strip()} " # e.g. " NUMPAGES "
        r2.append(instr)
        sdtContent.append(r2)

        # C. SEPARATE Char
        r3 = cls.create_element('w:r')
        fldChar2 = cls.create_element('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'separate')
        r3.append(fldChar2)
        sdtContent.append(r3)

        # D. RESULT Holder (Initial Value)
        r4 = cls.create_element('w:r')
        
        # ✅ [NEW FEATURE]: Run Properties जोड़ें
        rPr = cls.create_element('w:rPr')
        
        # 1. No Proofing (ताकि इस नंबर के नीचे लाल लाइन कभी न आए)
        noProof = cls.create_element('w:noProof')
        rPr.append(noProof)
        
        # 2. (Optional) Highlight/Visual adjustment 
        # (यह 'Date' जैसा इंटरएक्शन तो नहीं देगा, लेकिन इसे साफ दिखाएगा)
        
        r4.append(rPr)  # प्रॉपर्टीज को रन में जोड़ें

        t = cls.create_element('w:t')
        t.text = str(display_result) # "0" या Placeholder
        r4.append(t)
        sdtContent.append(r4)


        # E. END Char
        r5 = cls.create_element('w:r')
        fldChar3 = cls.create_element('w:fldChar')
        fldChar3.set(qn('w:fldCharType'), 'end')
        r5.append(fldChar3)
        sdtContent.append(r5)

        # -------------------------------------------------
        # Final Injection
        # बॉक्स (SDT) को अब असली पैराग्राफ में जोड़ें
        # -------------------------------------------------
        parent_paragraph._element.append(sdt)