"""
PAGE SETUP MANAGER (The Geometry Engine)
----------------------------------------
जिम्मेदारी:
1. दस्तावेज़ के पेज का आकार (Page Size) सेट करना (A4, Letter, Custom).
2. ओरिएंटेशन (Portrait/Landscape) को संभालना और आयामों (Dimensions) को स्वैप करना।
3. यूनिट रूपांतरण और सीमाओं की जाँच (Validation).

Dependency:
- Uses 'basics.unit_converter' for unit math.
- Uses 'xml_factory.xml_builder' to write changes.
- Uses 'config.constants' for safety limits.
"""

from kritidocx.utils.logger import logger 
from docx.enum.section import WD_ORIENT
from kritidocx.config.constants import DocConstants
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.xml_factory.xml_builder import XmlBuilder

class PageSetup:
    """
    Manages Document Geometry (Paper Size & Orientation).
    Functions act on a specific 'Section' of the Word document.
    """

    # =========================================================================
    # 📏 STANDARD PAPER REGISTRY (In Twips)
    # 1 Inch = 1440 Twips. Defined here for fast lookup.
    # =========================================================================
    PAPER_SIZES = {
        'a3':        (16838, 23811),
        'a4':        (11906, 16838),  # Most Common (210mm x 297mm)
        'a5':        (8390, 11906),
        'b4':        (14570, 20636),
        'b5':        (10318, 14570),
        'letter':    (12240, 15840),  # US Standard (8.5" x 11")
        'legal':     (12240, 20160),  # (8.5" x 14")
        'tabloid':   (15840, 24480),  # (11" x 17")
        'executive': (10440, 15120),  # (7.25" x 10.5")
    }

    @classmethod
    def apply_settings(cls, section, size_name=None, width=None, height=None, orientation=None):
        """
        Master method to apply page setup configuration.
        """
        
        # DEBUG: Input check
        logger.debug(f"📐 [PageSetup] Request: Size='{size_name}', W={width}, H={height}, Orient='{orientation}'")

        
        # 1. Determine Base Dimensions (Width, Height) in Twips
        final_w = 0
        final_h = 0
        
        is_custom_dims = False  # नया फ्लैग जोड़ें

        # Case A: Custom explicit dimensions provided
        if width and height:
            final_w = UnitConverter.to_twips(width)
            final_h = UnitConverter.to_twips(height)
            is_custom_dims = True  # इसे True सेट करें
            
        # Case B: Named Size lookup
        else:
            # Clean string and lookup
            key = (size_name or 'a4').lower().strip()
            # Retrieve from map or fallback to A4
            dims = cls.PAPER_SIZES.get(key, cls.PAPER_SIZES['a4'])
            final_w, final_h = dims

        # 2. Determine Orientation
        # 'landscape' means the wider edge is horizontal
        target_orient = (orientation or 'portrait').lower()
        
        word_orient_enum = WD_ORIENT.PORTRAIT
        
        if target_orient == 'landscape':
            word_orient_enum = WD_ORIENT.LANDSCAPE
            # Swap logic: Ensure Width > Height for Landscape
            if final_h > final_w:
                final_w, final_h = final_h, final_w
                
        else:
            # Portrait: Ensure Height > Width
            # (Exceptions exist, but standard papers follow this)
            
            # [UPDATED LOGIC HERE] -----------------------------
            # यदि यूजर ने कस्टम साइज़ दिया है, तो उसे FORCE ROTATE न करें
            # यह 5in x 3in जैसे कस्टम कार्ड्स को सही रहने देगा
            if not is_custom_dims and final_w > final_h:
                final_w, final_h = final_h, final_w
            # --------------------------------------------------


        # 3. Validate Constraints (Safety Net)
        # Word limits page size to 22 inches (approx 31680 Twips)
        # Prevents "Margins outside printable area" errors.
        limit = DocConstants.MAX_PAGE_WIDTH_TWIPS
        if final_w > limit: final_w = limit
        if final_h > limit: final_h = limit

        # 4. Apply via XML Factory
        # We pass integers (Twips) directly to the factory
        # We also set the orientation Enum which python-docx understands,
        # or handle raw attribute setting via builder if needed.
        
        # Method A: Use python-docx properties (Safe wrapper)
        section.orientation = word_orient_enum
        from docx.shared import Twips
        section.page_width = Twips(final_w)
        section.page_height = Twips(final_h)
        
        # Method B: Low-level XML Enforcement
        orient_str = 'landscape' if target_orient == 'landscape' else 'portrait'
        
        # Check if values are swapped correctly for landscape
        logger.debug(f"   -> Calculated: W={final_w}, H={final_h}, OrientMode='{orient_str}'")

        
        
        # Use python-docx properties mainly to trigger internal updates
        try:
            section.orientation = WD_ORIENT.LANDSCAPE if orient_str == 'landscape' else WD_ORIENT.PORTRAIT
            section.page_width = Twips(final_w)
            section.page_height = Twips(final_h)
        except:
            pass # Fail safe if library hiccups

        # 🟢 FINAL XML OVERRIDE (Authority)
        XmlBuilder.set_page_size_xml(
            section, 
            str(final_w), 
            str(final_h), 
            orient_str # Must be 'landscape' or 'portrait'
        )

        
        # Note on set_page_size_xml usage:
        # In section_xml.py, we typically need to also set 'w:orient' attribute manually 
        # because <w:pgSz> tag holds the orientation key.
        # Ensure XmlBuilder delegates 'orientation' string if supported.
        
        # For simplicity in this architecture, python-docx setters above are reliable for pgSz.
        # But if you expanded `SectionXml.set_page_size` to handle orientation string:
        # XmlBuilder.set_page_size_xml(section, str(final_w), str(final_h), orient_str)

    @classmethod
    def set_custom_size_from_css(cls, section, css_dict):
        """
        Parses CSS `@page { size: A4 landscape; }` or `size: 210mm 297mm;`.
        """
        size_str = css_dict.get('size', '').lower().strip()
        if not size_str: return

        parts = size_str.split()
        
        w_str = None
        h_str = None
        orient = None
        named = None
        
        # Detect tokens
        for part in parts:
            if part in ['landscape', 'portrait']:
                orient = part
            elif part in cls.PAPER_SIZES:
                named = part
            elif part[0].isdigit():
                # Assign dimension (first is width, second is height)
                if not w_str: w_str = part
                else: h_str = part
        
        # Logic resolution
        if w_str and h_str:
            cls.apply_settings(section, width=w_str, height=h_str, orientation=orient)
        elif named:
            cls.apply_settings(section, size_name=named, orientation=orient)
        elif orient:
            # Just change orientation, keep current size?
            # Or assume default A4 if this is initial setup
            cls.apply_settings(section, orientation=orient) # Defaults to A4 + Orient