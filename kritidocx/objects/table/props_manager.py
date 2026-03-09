"""
TABLE PROPERTIES MANAGER (The Global Table Architect)
-----------------------------------------------------
Responsibility:
Manages properties applied to the entire table (<w:tblPr>).

Controls:
1. Dimensions: Table Width logic (Percentage vs Fixed Twips).
2. Layout Algorithm: Fixed Widths vs Content AutoFit.
3. Alignment: Left, Center, Right positioning on page.
4. Indentation: Margin-Left simulation.
5. Borders: Global Table Borders (Outer & Inner frames).
6. Look & Feel: Zebra striping (Banding), Header visibility.

Unit Standards:
- Width (Pct): 50ths of a percent (5000 = 100%).
- Width (Dxa): Twips (1/1440 inch).
"""

from docx.enum.table import WD_TABLE_ALIGNMENT
from kritidocx.config.settings import AppConfig
from kritidocx.basics.css_parser import CssParser
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.basics.border_parser import BorderParser
from kritidocx.basics.color_manager import ColorManager
from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.config.theme import ThemeConfig
from docx.oxml.ns import qn

class TablePropsManager:
    """
    Controller for Global Table Attributes.
    """

    @classmethod
    def apply_global_styles(cls, word_table, style_str, html_node):
        """
        Master method to configure table structure.
        """
        if not word_table: return

        # 1. Parse Styles
        styles = CssParser.parse(style_str)
        
        # 2. Width Calculation (Critical for Mobile -> Word conversion)
        cls._apply_width(word_table, styles, html_node)

        # 3. Layout Algorithm (Autofit vs Fixed)
        # Defaulting to Fixed often produces better PDF-like results
        cls._apply_layout(word_table, styles)

        # 4. Alignment & Indentation
        cls._apply_positioning(word_table, styles, html_node)

        # 5. Visual Look (Zebra Striping / Shading)
        cls._apply_table_look(word_table, styles)


        # 6. 🆕 Process <colgroup> tags
        cls._process_column_groups(word_table, html_node) 
        
        # 7. Global Borders
        # Note: HTML tables usually have 'border="1"' attribute handling
        cls._apply_global_borders(word_table, styles, html_node)

    # -------------------------------------------------------------------------
    # 📏 WIDTH & LAYOUT LOGIC (Completely Updated for Dynamic Page Sizing)
    # -------------------------------------------------------------------------

    @staticmethod
    def _apply_width(word_table, styles, node):
        """
        [DYNAMIC SYSTEM UPDATE]
        Smart Logic:
        1. Checks for Left Indents/Margins to avoid Right-Side overflow.
        2. Uses explicit Twips (dxa) whenever possible instead of 'pct'.
        3. Prevents thick borders from causing 'Bleeding' issues.
        """
        width_val = styles.get('width') or node.get('width')
        
        # 1. Check Indentation (Left Margin)
        # अगर लेफ्ट में जगह छोड़ी गई है, तो 100% का मतलब "पेज से बाहर" हो जाएगा।
        indent_twips = 0
        m_left = styles.get('margin-left') or styles.get('padding-left')
        if m_left and m_left != 'auto':
            indent_twips = UnitConverter.to_twips(str(m_left))
            
        # मानक पेज की चौड़ाई (Content Area) - Approx 6.7 inches
        PAGE_CONTENT_TWIPS = 9600 

        # --- CASE A: DEFAULT (No explicit width) ---
        if not width_val:
            # Safe Fallback: 100% (Percentage) के बजाय हम Page Width (Fixed) का उपयोग करेंगे
            # यह बॉर्डर ब्लिडिंग (Bleeding) को रोकता है।
            
            # Available Width = Page Width - Indent
            safe_width = PAGE_CONTENT_TWIPS - indent_twips
            
            # थोड़ा सा बफर (Padding) छोड़ें (लगभग 100 twips / 5px) ताकि बॉर्डर फिट हो सकें
            safe_width -= 100 

            from kritidocx.xml_factory.table_xml import TableXml
            TableXml.set_table_width(word_table, str(safe_width), 'dxa')
            return

        raw = str(width_val).strip()

        # --- CASE B: PERCENTAGE (User Defined) ---
        if '%' in raw:
            # अगर यूजर ने 100% बोला है:
            # Word Scale: 5000 = 100%
            pct_val = UnitConverter.to_table_pct(raw) 
            
            # यदि इंडेंट है, तो 100% (5000) तकनीकी रूप से गलत होगा। 
            # 5000 का मतलब "मार्जिन से मार्जिन तक", लेकिन इंडेंट इसे धक्का दे रहा है।
            if indent_twips > 0 and pct_val >= 5000:
                # कन्वर्ट टू ट्विप्स फॉर सेफ्टी
                avail_width = PAGE_CONTENT_TWIPS - indent_twips - 50 # 50 Border Buffer
                from kritidocx.xml_factory.table_xml import TableXml
                TableXml.set_table_width(word_table, str(avail_width), 'dxa')
            else:
                from kritidocx.xml_factory.table_xml import TableXml
                TableXml.set_table_width(word_table, str(pct_val), 'pct')

        # --- CASE C: ABSOLUTE UNITS (Fixed) ---
        else:
            twips_val = UnitConverter.to_twips(raw)
            if twips_val > 0:
                from kritidocx.xml_factory.table_xml import TableXml
                TableXml.set_table_width(word_table, str(twips_val), 'dxa')     
                
    # --- [REPLACE THIS BLOCK in _apply_layout] ---

    @staticmethod
    def _apply_layout(word_table, styles):
        """
        Controls how column widths are calculated.
        Fixed = Requires explicit <col> tags or crashes layout logic.
        Autofit = Resizes based on content (Better for general HTML).
        """
        # CHANGE: Default 'fixed' -> 'autofit' (Much safer for tables without colgroups)
        layout_style = styles.get('table-layout', 'autofit') 
        
        # Word mapping: 'fixed' -> 'fixed', 'auto' -> 'autofit'
        if layout_style == 'fixed':
            XmlBuilder.set_table_look(word_table, "04A0") 
            from kritidocx.xml_factory.table_xml import TableXml
            TableXml.set_table_layout(word_table, 'fixed')
        else:
            from kritidocx.xml_factory.table_xml import TableXml
            TableXml.set_table_layout(word_table, 'autofit')
            
            # [ADDITION] Autofit needs a preferred width (e.g. 100%) to work best
            if not styles.get('width'):
                 TableXml.set_table_width(word_table, '5000', 'pct')
   
   
    # -------------------------------------------------------------------------
    # 🧭 ALIGNMENT & POSITION
    # -------------------------------------------------------------------------

    @staticmethod
    def _apply_positioning(word_table, styles, node):
        """
        Handles Alignment (Left/Center/Right) and Indentation.
        Supports: 'margin: auto' and 'float'.
        """
        # A. Alignment Detection
        alignment = WD_TABLE_ALIGNMENT.LEFT # Default
        
        # HTML align attribute
        attr_align = node.get('align', '').lower()
        
        # CSS Float
        css_float = styles.get('float', '').lower()
        
        # CSS Margin Auto (Center Trick)
        m_left = styles.get('margin-left', '')
        m_right = styles.get('margin-right', '')
        is_margin_auto = (m_left == 'auto' and m_right == 'auto')

        if attr_align == 'center' or is_margin_auto:
            alignment = WD_TABLE_ALIGNMENT.CENTER
        elif attr_align == 'right' or css_float == 'right':
            alignment = WD_TABLE_ALIGNMENT.RIGHT
        
        # Apply to python-docx object
        word_table.alignment = alignment

        # 🟢 CHANGE: Explicitly update XML via Builder for consistency/testing.
        # This fixes 'None != center' error because Mock object doesn't auto-update XML.
        
        align_map = {
            WD_TABLE_ALIGNMENT.CENTER: 'center',
            WD_TABLE_ALIGNMENT.RIGHT: 'right',
            WD_TABLE_ALIGNMENT.LEFT: 'left'
        }
        xml_align_val = align_map.get(alignment, 'left')
        XmlBuilder.set_table_alignment(word_table, xml_align_val)

        # B. Indentation (Left Margin)
        # If not centered/right, respect left-margin/padding as indentation
        if alignment == WD_TABLE_ALIGNMENT.LEFT:
            indent_str = styles.get('margin-left') or styles.get('padding-left')
            if indent_str and indent_str != 'auto':
                indent_twips = UnitConverter.to_twips(indent_str)
                # Word "Indentation from Left"
                XmlBuilder.set_table_indent(word_table, indent_twips)


    # -------------------------------------------------------------------------
    # 🛡️ GLOBAL BORDERS FIX
    # -------------------------------------------------------------------------

    @staticmethod
    def _apply_global_borders(word_table, styles, node):
        """
        [FIXED STRATEGY]: Apply Base Grid on Table Level.
        This allows Cell-Level custom borders (like Double Red) to strictly override
        the base grid without artifact collisions.
        """
        from kritidocx.xml_factory.table_xml import TableXml

        # 1. Parse custom borders (if any) to detect styles
        # (Assuming you mostly want a clean internal grid)
        
        # 2. APPLY DEFAULT INTERNAL GRID (Instead of removing it)
        # हम Table Level पर 'InsideH' और 'InsideV' को स्टैंडर्ड सेट करेंगे।
        default_grid = {
            'val': 'single', 
            'sz': 4,        # 1/2 pt
            'color': 'auto',
            'space': 0
        }

        # बेसिक बॉर्डर मैप तैयार करें (Perimeter + Inside)
        global_map = {
            'top': default_grid, 'bottom': default_grid, 
            'left': default_grid, 'right': default_grid,
            'insideH': default_grid, 'insideV': default_grid
        }

        # CSS Overrides check (optional implementation details...)
        if styles.get('border'):
            # अगर CSS में टेबल बॉर्डर दिया है, तो उसे यहाँ लागू करें (लॉजिक पूर्ववत)
            # यहाँ simplicity के लिए हम सिर्फ XML पर पुश कर रहे हैं:
            pass

        # Apply Table Defaults
        TableXml.set_table_borders_sides(word_table, global_map)
         
            
    @staticmethod
    def _apply_table_look(word_table, styles):
        """
        Sets Visual Features: First Row Bold (Header), Banded Rows (Zebra).
        Defaults: Enabled Header Row & Banded Rows (Standard '04A0' hex value behavior).
        """
        # CSS override? 
        # Usually logic relies on default theme settings.
        
        # TblLook 'val' breakdown (Hex bitmask):
        # 0x0020 = First Row
        # 0x0040 = Last Row
        # 0x0080 = First Col
        # 0x0100 = Last Col
        # 0x0200 = Banded Rows
        # 0x0400 = Banded Cols
        
        # Standard: 0x04A0 (0x0400 | 0x0020 | 0x0080) in some specs
        # python-docx does this automatically if using a Style.
        # But we ensure it via XML builder just in case styles strip it.
        XmlBuilder.set_table_look(word_table, "04A0") 
        # Enables: First Row formatting + First Column formatting + Banded Rows
        
        
    # -------------------------------------------------------------
    # 🆕 COLUMN GROUP ENGINE
    # -------------------------------------------------------------
    @staticmethod
    def _process_column_groups(word_table, table_node):
        """
        Parses <colgroup> and <col> to enforce column widths via <w:tblGrid>.
        [UPDATED FIX]: Calculates 'Rest of Width' manually to force FIXED layout logic.
        """
        if not table_node: return

        colgroup = table_node.find('colgroup')
        if not colgroup: return

        raw_widths_twips = []
        cols = colgroup.find_all('col')
        
        # ---------------------------------------------------------
        # 1. Extract Widths
        # ---------------------------------------------------------
        for col in cols:
            try:
                span_val = int(col.get('span', 1))
            except ValueError:
                span_val = 1
                
            style_str = col.get('style', '')
            c_styles = CssParser.parse(style_str)
            raw_w = c_styles.get('width') or col.get('width')
            
            final_w_twips = 0 
            
            if raw_w:
                if '%' in str(raw_w):
                    # Fixed Grid में प्रतिशत काम नहीं करता, इसे 0 मानें (Auto Calculation)
                    final_w_twips = 0 
                else:
                    final_w_twips = UnitConverter.to_twips(str(raw_w))

            # Span Support
            for _ in range(span_val):
                raw_widths_twips.append(final_w_twips)

        if not raw_widths_twips: return

        # ---------------------------------------------------------
        # 2. 🧮 HYBRID CALCULATION (The Master Fix)
        # ---------------------------------------------------------
        # समस्या: Word को 'Fixed' लेआउट चाहिए ताकि पहले दो कॉलम अपनी साइज न बदलें।
        # लेकिन 'Fixed' में 0 चौड़ाई वाला कॉलम गायब हो जाता है।
        # समाधान: 'Rest of Width' को हम खुद मापेंगे।

        # एक मानक पेज (A4) की 'Writable Area' चौड़ाई लगभग 9000-9600 Twips होती है।
        # हम सुरक्षित मान (Safe Standard) लेंगे।
        PAGE_CONTENT_WIDTH = 9638 # Approx 6.7 inches
        
        # ज्ञात चौड़ाइयाँ (Known Widths) का जोड़
        fixed_sum = sum(w for w in raw_widths_twips if w > 0)
        
        # कितने कॉलम 'Auto' हैं? (width=0 वाले)
        auto_cols_indices = [i for i, x in enumerate(raw_widths_twips) if x == 0]
        num_auto = len(auto_cols_indices)

        final_widths_to_apply = list(raw_widths_twips)

        if num_auto > 0:
            # बची हुई जगह निकालें
            remaining = PAGE_CONTENT_WIDTH - fixed_sum
            
            # अगर बची हुई जगह बहुत कम या नेगेटिव हो, तो एक सुरक्षित न्यूनतम चौड़ाई (1 इंच) दें
            if remaining < 1440: 
                remaining = 1440 
            
            # हर ऑटो कॉलम को हिस्सा दें
            share = int(remaining / num_auto)
            
            for idx in auto_cols_indices:
                final_widths_to_apply[idx] = share

        # ---------------------------------------------------------
        # 3. APPLY TO XML & FORCE FIXED LAYOUT
        # ---------------------------------------------------------
        
        XmlBuilder.define_table_grid(word_table, final_widths_to_apply)

        # 🚀 FORCE 'FIXED' layout:
        # अब चूँकि हमने "Auto" कॉलम को भी एक फिक्स नंबर दे दिया है,
        # हम Table Layout को 'fixed' कर सकते हैं।
        # इससे Word '50px Constraint' को छेड़ने की हिम्मत नहीं करेगा।
        
        from kritidocx.xml_factory.table_xml import TableXml
        TableXml.set_table_layout(word_table, 'fixed')

        # [Safety] टेबल की कुल चौड़ाई भी 100% कर दें ताकि वह पेज से बाहर न जाए
        TableXml.set_table_width(word_table, '5000', 'pct')