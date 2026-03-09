"""
NUMBERING XML FACTORY (The List Architect)
------------------------------------------
Responsibility:
Generates XML structures for 'numbering.xml'.

Structures:
1. AbstractNum (<w:abstractNum>): Defines the "Style" (Look & Feel).
   - Contains 9 <w:lvl> elements (Level 0-8).
2. Num (<w:num>): Defines the "Instance" (Usage in document).
   - Links back to AbstractNum via ID.

Key Features:
- Supports rich text properties for bullets (Color, Fonts).
- Manages strict Indentation XML (hanging/left).
- Ensures Hex NSID generation for list uniqueness.
"""

from docx.oxml.ns import qn
from .base import XmlBase
import random

class NumberingXml(XmlBase):
    
    # Schema Order for Level Properties (<w:lvl>)
    # Word is very strict about this order!
    LVL_ORDER = [
        'start', 'numFmt', 'lvlRestart', 'pStyle', 'isLgl', 'suff', 
        'lvlText', 'lvlPicBulletId', 'legacy', 'lvlJc', 'pPr', 'rPr'
    ]

    @staticmethod
    def _generate_hex_nsid():
        """Generates 8-char HEX ID (FFFFFFFF max) to identify unique lists."""
        val = random.randint(0, 0xFFFFFFFF)
        return "{:08X}".format(val)

    # =========================================================================
    # 1. 🏗️ ABSTRACT DEFINITION (Style Rule)
    # =========================================================================

    @classmethod
    def create_abstract_num(cls, abstract_id, multi_level_type="multilevel", template_name=None):
        """
        Creates the wrapper <w:abstractNum>.
        Levels (<w:lvl>) should be appended to this element later.
        """
        abs_num = cls.create_element('w:abstractNum')
        cls.create_attribute(abs_num, 'w:abstractNumId', str(abstract_id))
        
        # 1. NSID (Hex ID) - Random signature
        nsid = cls.create_element('w:nsid')
        cls.create_attribute(nsid, 'w:val', cls._generate_hex_nsid())
        abs_num.append(nsid)
        
        # 2. MultiLevel Type
        multi = cls.create_element('w:multiLevelType')
        cls.create_attribute(multi, 'w:val', multi_level_type)
        abs_num.append(multi)
        
        # 3. Template Name (Optional, good for debugging XML)
        if template_name:
            tmpl = cls.create_element('w:tmpl')
            cls.create_attribute(tmpl, 'w:val', str(template_name))
            abs_num.append(tmpl)
            
        return abs_num

    @classmethod
    def create_level(cls, level_idx, fmt_type, lvl_text, 
                     indent=720, hanging=360, 
                     font_data=None, align='left', start=1):
        """
        Creates one <w:lvl> element (e.g., Level 0: 1. , Level 1: a. ).
        
        Args:
            level_idx: 0 to 8
            fmt_type: 'decimal', 'bullet', 'lowerLetter', etc.
            lvl_text: '%1.' or '●'
            indent: Total indent from left (Twips)
            hanging: Gap between bullet and text (Twips)
            font_data: Dict {'name': 'Symbol', 'color': 'FF0000'}
        """
        lvl = cls.create_element('w:lvl')
        cls.create_attribute(lvl, 'w:ilvl', str(level_idx))
        
        # A. Start Index
        start_tag = cls.create_element('w:start')
        cls.create_attribute(start_tag, 'w:val', str(start))
        cls.upsert_child(lvl, start_tag, cls.LVL_ORDER)
        
        # B. Number Format
        numFmt = cls.create_element('w:numFmt')
        cls.create_attribute(numFmt, 'w:val', fmt_type)
        cls.upsert_child(lvl, numFmt, cls.LVL_ORDER)
        
        # [FIX]: Insert isLgl BEFORE lvlText to follow LVL_ORDER strictly
        # =========================================================================
        if font_data and font_data.get('is_legal'):
            isLgl = cls.create_element('w:isLgl')
            # Note: upsert_child will handle the sorting based on LVL_ORDER
            cls.upsert_child(lvl, isLgl, cls.LVL_ORDER)

        
        
        # C. Level Text
        # Note: XML escapes special chars automatically in lxml, but we rely on string input
        txt = cls.create_element('w:lvlText')
        cls.create_attribute(txt, 'w:val', lvl_text)
        cls.upsert_child(lvl, txt, cls.LVL_ORDER)
        
        # D. Alignment (Justification)
        jc = cls.create_element('w:lvlJc')
        cls.create_attribute(jc, 'w:val', align)
        cls.upsert_child(lvl, jc, cls.LVL_ORDER)
        
        # : LEGAL NUMBERING ENFORCEMENT
        # यदि 'is_legal' फ्लैग मौजूद है, तो <w:isLgl/> टैग जोड़ें।
        # यही वह टैग है जो 1.1, 1.1.1 फॉर्मेट को एक्टिवेट करता है।
        # =========================================================================
        if font_data and font_data.get('is_legal'):
            isLgl = cls.create_element('w:isLgl')
            cls.create_attribute(isLgl, 'w:val', '1')
            cls.upsert_child(lvl, isLgl, cls.LVL_ORDER)
         
        
        # E. 📏 INDENTATION (<w:pPr>)
        # Critical for list alignment visuals
        pPr = cls.create_element('w:pPr')
        ind = cls.create_element('w:ind')
        cls.create_attribute(ind, 'w:left', str(indent))
        cls.create_attribute(ind, 'w:hanging', str(hanging))
        pPr.append(ind)
        cls.upsert_child(lvl, pPr, cls.LVL_ORDER)
        
        # F. 🎨 FONT & COLOR (<w:rPr>) - For the Bullet/Number only
        # [STEP 1 FIX]: Font Safety & Schema Compliance
        if font_data:
            rPr = cls.create_element('w:rPr')
            
            # 1. Font Family Logic
            if font_data.get('name'):
                f_name = font_data['name']
                
                # [CRITICAL FIX]: Symbol Font Replacement
                # 'Symbol' फॉन्ट अक्सर Unicode बुलेट्स (●, ➤) को रेंडर नहीं कर पाता और □ दिखाता है।
                # हम मानक (Safe) फॉन्ट को फोर्स करेंगे, जब तक कि वह Wingdings न हो।
                if f_name == 'Symbol': 
                    f_name = 'Calibri'
                
                fonts = cls.create_element('w:rFonts')
                # बुलेट सही दिखने के लिए ascii और hAnsi दोनों सेट करना जरुरी है
                cls.create_attribute(fonts, 'w:ascii', f_name)
                cls.create_attribute(fonts, 'w:hAnsi', f_name)
                # hint='default' Word को सही ग्लाइफ़ चुनने में मदद करता है
                cls.create_attribute(fonts, 'w:hint', 'default')
                rPr.append(fonts)
                
            # 2. Font Color
            if font_data.get('color'):
                color = cls.create_element('w:color')
                cls.create_attribute(color, 'w:val', font_data['color'])
                rPr.append(color)
            
            # 3. Font Size
            if font_data.get('size'):
                sz = cls.create_element('w:sz')
                cls.create_attribute(sz, 'w:val', str(font_data['size']))
                rPr.append(sz)

            # Insert rPr (Run Properties) using Strict Schema Order
            # (यह सुनिश्चित करता है कि XML Corrupt न हो)
            cls.upsert_child(lvl, rPr, cls.LVL_ORDER)

        return lvl

    # =========================================================================
    # 2. 🔗 LIST INSTANCE (Linker)
    # =========================================================================

    @classmethod
    def create_num_instance(cls, num_id, abstract_id):
        """
        Creates the usage instance <w:num>.
        Links `numId` (Used in paragraphs) to `abstractNumId` (The style definition).
        [FIXED]: Force Restart at 1 using lvlOverride.
        """
        num = cls.create_element('w:num')
        cls.create_attribute(num, 'w:numId', str(num_id))
        
        abs_ref = cls.create_element('w:abstractNumId')
        cls.create_attribute(abs_ref, 'w:val', str(abstract_id))
        num.append(abs_ref)

        # [RESTART FIX]: Force Level 0 to Start at 1
        # जब भी हम एक नई लिस्ट (numInstance) बनाते हैं, तो हमें Word को स्पष्ट 
        # रूप से बताना होता है कि Level 0 की गिनती 1 से शुरू होनी चाहिए।
        # अन्यथा Word पिछली लिस्ट की गिनती जारी रख सकता है (e.g. 1,2.. -> 3,4)।
        
        lvlOverride = cls.create_element('w:lvlOverride')
        cls.create_attribute(lvlOverride, 'w:ilvl', '0')
        
        startOverride = cls.create_element('w:startOverride')
        cls.create_attribute(startOverride, 'w:val', '1')
        
        lvlOverride.append(startOverride)
        num.append(lvlOverride)
        
        return num
    # =========================================================================
    # 3. 🛡️ INJECTION HELPERS
    # =========================================================================

    @classmethod
    def register_abstract_list(cls, numbering_part, abstract_id, levels_config):
        """
        Constructs and injects the complete <w:abstractNum> tree.
        """
        if numbering_part is None: return

        # 1. Container Create
        abstract_element = cls.create_abstract_num(
            abstract_id, 
            multi_level_type="multilevel"
        )
        
        # 2. Loop & Append Levels
        # levels_config = List of dicts (from StyleFactory)
        for cfg in levels_config:
            lvl_node = cls.create_level(
                level_idx=cfg['level'],
                fmt_type=cfg['format'],
                lvl_text=cfg['text'],
                indent=cfg.get('left', 720),     # Default logic handled by obj/math if missing
                hanging=cfg.get('hanging', 360),
                font_data=cfg.get('font'),       # {name: 'Symbol'}
                align=cfg.get('align', 'left')
            )
            abstract_element.append(lvl_node)
            
        # 3. Inject into XML (ORDER MATTERS)
        # abstractNum MUST appear before num
        root = numbering_part.numbering_definitions._numbering
        
        # Find position: End of existing abstracts, Before first <w:num>
        first_num_index = -1
        for i, child in enumerate(root):
            if child.tag.endswith('num'):
                first_num_index = i
                break
        
        if first_num_index != -1:
            root.insert(first_num_index, abstract_element)
        else:
            root.append(abstract_element)

    @classmethod
    def register_list_instance(cls, numbering_part, num_id, abstract_id):
        """
        Injects <w:num>. This can safely go at the end of the file.
        """
        if numbering_part is None: return
        
        root = numbering_part.numbering_definitions._numbering
        num_element = cls.create_num_instance(num_id, abstract_id)
        
        # Always append num instances at the bottom
        root.append(num_element)