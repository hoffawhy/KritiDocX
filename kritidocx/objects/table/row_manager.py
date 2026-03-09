"""
ROW MANAGER MODULE (The Horizontal Architect)
---------------------------------------------
Responsibility:
Manages properties of Table Rows (<w:tr>).

Key Features:
1. Row Height: Calculations using Twips/Points. 
   Supports 'atLeast' (auto-expand) vs 'exact' (fixed height) modes.
2. Pagination Control: 'Can Split' logic (keep row on one page).
3. Header Logic: 'Repeat Header Rows' for multi-page tables.
4. Alignment: Center row in page (rare but supported via styling context).

Dependency:
- Uses `UnitConverter` for dimensional math.
- Direct XML manipulation via OXML for features missing in python-docx wrapper.
"""

from docx.shared import Twips
from docx.oxml.ns import qn
from docx.enum.table import WD_ROW_HEIGHT_RULE

from kritidocx.basics.css_parser import CssParser
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.xml_factory.xml_builder import XmlBuilder

class RowManager:
    """
    Controller for single table row styling and behavior.
    """

    @classmethod
    def apply_row_props(cls, word_row, html_tr_node):
        """
        Master method to apply row-level settings.
        [UPDATED]: Added 'TH' tag detection to auto-fix missing repeating headers.
        """
        if not html_tr_node: return

        # 1. Parse CSS
        style_str = html_tr_node.get('style', '')
        styles = CssParser.parse(style_str)

        # 2. Row Height
        cls._apply_height(word_row, styles, html_tr_node)

        # -------------------------------------------------------------
        # 3. 🛡️ HEADER REPETITION INTELLIGENCE (Upgraded)
        # -------------------------------------------------------------
        
        # Criteria A: Structural (<thead ...>)
        parent_tag = html_tr_node.parent.name if html_tr_node.parent else ""
        is_thead = (parent_tag == 'thead')

        # Criteria B: CSS Style (display: table-header-group)
        css_display = styles.get('display', '').lower()
        is_css_header = (css_display == 'table-header-group')

        # Criteria C: Explicit Class (repeat-header)
        classes = html_tr_node.get('class', [])
        is_class_header = 'repeat-header' in classes

        # 🚀 Criteria D: Heuristic Detection (Does it contain <th>?)
        # यदि HTML में <thead> नहीं है, तो भी <th> का होना बताता है कि यह हेडर रो है।
        has_th_cells = bool(html_tr_node.find('th', recursive=False))

        # Check: अगर यह 'Row 1' है (वैकल्पिक रूप से), लेकिन <th> सबसे मजबूत संकेत है।
        
        if is_thead or is_css_header or is_class_header or has_th_cells:
            cls._set_as_header_row(word_row)

        # -------------------------------------------------------------
        # 4. PAGINATION LOGIC (Row Splitting)
        # -------------------------------------------------------------
        cls._apply_pagination(word_row, styles)




    # -------------------------------------------------------------
    # 📏 INTERNAL LOGIC HANDLERS
    # -------------------------------------------------------------

    @staticmethod
    def _apply_height(word_row, styles, node):
        """
        Sets the row height based on CSS or Attribute.
        Logic Update: Scans child cells if row height is missing.
        """
        # 1. Direct TR Height (Priority 1)
        raw_height = styles.get('height') or node.get('height')

        # 2. If TR has no height, Scan Cells (Priority 2)
        # HTML अक्सर CSS classes के जरिए TD पर height लगाता है (.grid td {height: 150px})
        if not raw_height:
            max_h_twips = 0
            
            # पंक्ति के सभी डायरेक्ट सेल्स (td/th) को ढूंढें
            cells = node.find_all(['td', 'th'], recursive=False)
            
            for cell in cells:
                # इनलाइन स्टाइल पार्स करें
                c_style_str = cell.get('style', '')
                # ध्यान दें: पूरी स्टाइल पार्स करने की जगह हम सिर्फ height ढूंढ सकते हैं 
                # (Optimized for speed) या CssParser यूज करें
                from kritidocx.basics.css_parser import CssParser
                c_styles = CssParser.parse(c_style_str)
                
                # Check style 'height' then attr 'height'
                h_val = c_styles.get('height') or cell.get('height')
                
                if h_val:
                    # वैल्यू को ट्विप्स में बदलें और तुलना करें
                    # (ताकि 'px' और '%' की तुलना सही हो सके, हम ट्विप्स को मानक मानते हैं)
                    tw = UnitConverter.to_twips(str(h_val))
                    if tw > max_h_twips:
                        max_h_twips = tw
            
            # अगर किसी सेल में वैलिड ऊंचाई मिली, तो उसे उपयोग करें
            if max_h_twips > 0:
                word_row.height = Twips(max_h_twips)
                
                # -------------------------------------------------------------
                # 🚀 RULE UPDATE: AT_LEAST vs EXACTLY
                # -------------------------------------------------------------
                # AT_LEAST: कंटेंट ज्यादा हुआ तो हाइट बढ़ जाएगी (Safe for Text)
                # EXACTLY: कंटेंट कटेगा, लेकिन डिजाइन फिक्स रहेगा (Safe for Layout)
                
                # हम 'AT_LEAST' ही रखेंगे क्योंकि यह डाटा कटने नहीं देता,
                # और 150px जैसी बड़ी वैल्यू पर यह विज़ुअली 'EXACTLY' जैसा ही दिखता है।
                word_row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
                return

        # 3. Apply found TR Height (अगर ऊपर स्कैन की जरूरत नहीं पड़ी)
        if raw_height:
            height_twips = UnitConverter.to_twips(str(raw_height))
            if height_twips > 0:
                word_row.height = Twips(height_twips)
                word_row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST


    @classmethod
    def _set_as_header_row(cls, word_row):
        """
        Marks row to repeat at the top of each page if table splits.
        Tag: <w:trPr><w:tblHeader/></w:trPr>
        """
        # 1. python-docx Standard Property
        # यह Python ऑब्जेक्ट में flag सेट करता है ताकि docx इसे पहचान ले
        word_row.table_header = True
        
        # 2. XML Reinforcement (Safety)
        # कभी-कभी styles के कारण यह प्रॉपर्टी उड़ जाती है, इसलिए हम इसे XML में ठोक देंगे
        tr = word_row._tr
        trPr = tr.get_or_add_trPr()
        
        # 'w:tblHeader' टैग को जोड़ना सुनिश्चित करता है कि Word इसे हेडर माने
        # इसमें 'val' attribute की जरूरत नहीं होती, बस टैग काफी है
        # लेकिन सुरक्षित रहने के लिए हम existing method का प्रयोग करेंगे
        cls._upsert_bool_tag(trPr, 'w:tblHeader', None) # Value None implies tag presence only

        # [PRO TIP]: Headers should never break inside. 
        # आधा हेडर इस पेज पर और आधा उस पेज पर अजीब दिखता है।
        cls._upsert_bool_tag(trPr, 'w:cantSplit', '1')



    @classmethod
    def _apply_pagination(cls, word_row, styles):
        """
        Handles Row Breaking logic.
        Supported CSS: 
          - page-break-inside: avoid;
          - break-inside: avoid;
        """
        # Check Modern Syntax first (break-inside)
        break_val = styles.get('break-inside', '').lower()
        
        # Check Legacy Syntax (page-break-inside)
        if not break_val:
            break_val = styles.get('page-break-inside', '').lower()
        
        # Also check explicit HTML attribute data-split="false"
        should_prevent_split = (break_val in ['avoid', 'avoid-page'])
        
        if should_prevent_split:
            tr = word_row._tr
            trPr = tr.get_or_add_trPr()
            
            # <w:cantSplit w:val="on"/> tells Word: 
            # "Do not let this row get cut in half at the end of a page"
            # It pushes the WHOLE row to the next page if it doesn't fit.
            cls._upsert_bool_tag(trPr, 'w:cantSplit', 'on')


    @staticmethod
    def _upsert_bool_tag(parent_xml, tag_name, val):
        """
        Helper for raw XML flag toggling.
        """
        tag = parent_xml.find(qn(tag_name))
        if tag is None:
            tag = XmlBuilder.create_element(tag_name)
            parent_xml.append(tag)
        
        # Set value if tag expects attribute (usually boolean tags handle presence as true, but some need val)
        if val:
            XmlBuilder.create_attribute(tag, 'w:val', val)