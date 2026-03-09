"""
XML BASE FACTORY (The Schema Enforcer)
--------------------------------------
जिम्मेदारी: 
1. Low-level XML Elements बनाना (python-docx OxmlElement wrapper)।
2. MS Word ECMA-376 मानकों के अनुसार टैग्स को सख्ती से सॉर्ट (Sort) करना।

यह क्लास सुनिश्चित करती है कि 'File Corrupt' एरर कभी न आए।
"""

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re
from docx.oxml.ns import nsmap
# नए वर्ड्स इफेक्ट्स के लिए इन दो को जोड़ना जरूरी है:
nsmap['w14'] = 'http://schemas.microsoft.com/office/word/2010/wordml'
nsmap['a'] = 'http://schemas.openxmlformats.org/drawingml/2006/main'
nsmap['mc'] = 'http://schemas.openxmlformats.org/markup-compatibility/2006'


class XmlBase:
    """
    Base utility class for all XML writers.
    Contains strictly ordered lists defining Valid OOXML Schema sequence.
    """

    # =========================================================================
    # 📜 SACRED SCHEMA ORDERS (Word की नियमावली)
    # इन सूचियों का क्रम न बदलें, यह Microsoft द्वारा निर्धारित है।
    # =========================================================================

    # 1. Run Properties (rPr) - Character Styles
    # Ref: CT_RPr
    R_PR_ORDER = [
        'rStyle', 'rFonts', 'b', 'bCs', 'i', 'iCs', 'caps', 'smallCaps', 'strike', 
        'dstrike', 'outline', 'shadow', 'emboss', 'imprint', 'noProof', 'snapToGrid', 
        'vanish', 'webHidden', 'color', 'w14:gradFill', 'spacing', 'w', 'kern', 'position', 'sz', 
        'szCs', 'highlight', 'u', 'effect', 'bdr', 'shd', 'fitText', 'vertAlign', 
        'rtl', 'cs', 'em', 'lang', 'eastAsianLayout', 'specVanish', 'oMath', 'w14:textFill','w14:glow', 'w14:shadow', 'w14:reflection', 'w14:textOutline'
    ]

    # 2. Paragraph Properties (pPr) - Block Styles
    # Ref: CT_PPr
    P_PR_ORDER = [
        'pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl',
        'numPr', 'suppressLineNumbers', 'pBdr', 'shd', 'tabs', 'suppressAutoHyphens',
        'kinsoku', 'wordWrap', 'overflowPunct', 'topLinePunct', 'autoSpaceDE',
        'autoSpaceDN', 'bidi', 'adjustRightInd', 'snapToGrid', 'spacing', 'ind',
        'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc', 'textDirection',
        'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 
        'rPr', 'sectPr', 'pPrChange'
    ]

    # 3. Table Cell Properties (tcPr)
    # Ref: CT_TcPr
    TC_PR_ORDER = [
        'tcW', 'gridSpan', 'hMerge', 'vMerge', 'tcBorders', 'shd', 
        'noWrap', 'tcMar', 'textDirection', 'tcFitText', 'vAlign', 'hideMark', 
        'headers', 'cellDel', 'cellMerge'
    ]

    # 4. Table Properties (tblPr) - Table Global Settings
    # Ref: CT_TblPr
    TBL_PR_ORDER = [
        'tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual', 'tblStyleRowBandSize', 
        'tblStyleColBandSize', 'tblW', 'jc', 'tblCellSpacing', 'tblInd', 
        'tblBorders', 'shd', 'tblLayout', 'tblCellMar', 'tblLook', 
        'tblCaption', 'tblDescription'
    ]

    # 5. Section Properties (sectPr) - Page Setup
    # Ref: CT_SectPr
    SECT_PR_ORDER = [
        'headerReference', 'footerReference', 'footnotePr', 'endnotePr', 'type', 
        'pgSz', 'pgMar', 'paperSrc', 'pgBorders', 'lnNumType', 'pgNumType', 
        'cols', 'formProt', 'vAlign', 'noEndnote', 'titlePg', 'textDirection', 
        'bidi', 'rtlGutter', 'docGrid', 'printerSettings', 'sectPrChange'
    ]

    # 6. Floating Object Anchor (wp:anchor)
    # Ref: CT_Anchor (DrawingML)
    ANCHOR_ORDER = [
        'simplePos', 'positionH', 'positionV', 'extent', 'effectExtent', 
        'wrapNone', 'wrapSquare', 'wrapTight', 'wrapThrough', 'wrapTopAndBottom', 
        'docPr', 'cNvGraphicFramePr', 'graphic', 'relativeHeight'
    ]

    # =========================================================================
    # 🛠️ HELPER METHODS (XML जनरेटर)
    # =========================================================================

    @staticmethod
    def create_element(name):
        """Standard wrapper to create an XML element (Node)."""
        return OxmlElement(name)

    @staticmethod
    def create_attribute(element, name, value):
        """
        Safely sets an XML attribute.
        Uses `qn()` if namespace prefix is present (e.g. w:val).
        """
        if value is None: return # Don't set empty attributes
        
        if ':' in name:
            element.set(qn(name), str(value))
        else:
            element.set(str(name), str(value))

    # =========================================================================
    # 🧹 SORTING LOGIC (The Stabilizer)
    # =========================================================================

    @staticmethod
    def sort_element_children(parent_element, order_list):
        """
        [THE MAGIC FUNCTION]
        पैरेंट नोड के बच्चों को हटाकर उन्हें सही क्रम में वापस लगाता है।
        यह 'Namespace Pollution' को हैंडल करता है।
        """
        # 1. मौजूदा बच्चों की लिस्ट बनाएं और पैरेंट को खाली करें
        children = [child for child in parent_element]
        for child in children: 
            parent_element.remove(child)
        
        # 2. सॉर्ट कुंजी (Sort Key) लॉजिक
        def sort_key(child):
            # lxml tags: {http://schemas...}color
            # हम prefix हटाकर सिर्फ localname ('color') लेंगे
            full_tag = child.tag
            local_name = full_tag.split('}')[-1] # Remove Namespace
            
            try:
                return order_list.index(local_name)
            except ValueError:
                # अगर लिस्ट में नहीं है (Unknown tag), तो इसे सबसे अंत में रखें
                return 999 
        
        # 3. सॉर्ट करें
        children.sort(key=sort_key)
        
        # 4. वापस जोड़ें
        for child in children: 
            parent_element.append(child)

    @classmethod
    def upsert_child(cls, parent_element, new_child, order_list=None):
        """
        [NEW FEATURE: Smart Insert]
        Updates (Replaces) a child if it exists, otherwise inserts it.
        Then sorts the parent automatically if order_list provided.
        """
        if parent_element is None or new_child is None: return

        # 1. पुराने डुप्लीकेट टैग को ढूंढें और हटाएं
        child_tag = new_child.tag
        existing = parent_element.find(child_tag)
        
        if existing is not None:
            parent_element.remove(existing)
            
        # 2. नया टैग जोड़ें
        parent_element.append(new_child)
        
        # 3. यदि ऑर्डर लिस्ट है, तो सॉर्ट करें
        if order_list:
            cls.sort_element_children(parent_element, order_list)