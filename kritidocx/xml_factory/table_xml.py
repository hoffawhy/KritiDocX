"""
TABLE XML FACTORY (The Grid Architect)
--------------------------------------
Responsibility:
Generates XML for Table Cell Properties (tcPr) and Table Properties (tblPr).

Ensures correct schema sequence:
1. Widths -> 2. Merging -> 3. Borders -> 4. Shading -> 5. Margins -> 6. Alignment.

Features:
- Nested Border definitions.
- Rowspan (vMerge) & Colspan (gridSpan) logic.
- Text Rotation logic.
- Table Alignment & Layout Fixed/Auto.
"""

from docx.oxml.ns import qn
from docx.shared import Emu
from .base import XmlBase

class TableXml(XmlBase):
    
    # Border Order inside <w:tcBorders> specifically
    BORDER_ORDER = ['top', 'left', 'bottom', 'right', 'insideH', 'insideV', 'tl2br', 'tr2bl']

    # =========================================================================
    # 1. 🟥 CELL PROPERTIES (tcPr)
    # =========================================================================

    @staticmethod
    def _get_or_create_tcPr(cell):
        """Helper to fetch tcPr element."""
        return cell._tc.get_or_add_tcPr()

    @classmethod
    def set_cell_width(cls, cell, width_value, width_type='dxa'):
        """
        Sets explicit cell width.
        Type: 'dxa' (Twips), 'pct' (Percentage), or 'nil' (Auto).
        """
        tcPr = cls._get_or_create_tcPr(cell)
        
        tcW = cls.create_element('w:tcW')
        cls.create_attribute(tcW, 'w:w', str(width_value))
        
        # अगर टाइप 'nil' है, तो type attribute न सेट करें, या 'auto' भेजें। 
        # Word XML में w:type="auto" अक्सर 'auto' या 'nil' स्ट्रिंग लेता है।
        cls.create_attribute(tcW, 'w:type', width_type)
        
        cls.upsert_child(tcPr, tcW, cls.TC_PR_ORDER)

    @classmethod
    def set_cell_shading(cls, cell, hex_color):
        """Sets Background Color."""
        tcPr = cls._get_or_create_tcPr(cell)
        
        # XML Tag: <w:shd w:val="clear" w:color="auto" w:fill="FF0000"/>
        shd = cls.create_element('w:shd')
        cls.create_attribute(shd, 'w:val', 'clear')
        cls.create_attribute(shd, 'w:color', 'auto')
        cls.create_attribute(shd, 'w:fill', hex_color.replace('#', '').upper())
        
        cls.upsert_child(tcPr, shd, cls.TC_PR_ORDER)

    @classmethod
    def set_cell_borders(cls, cell, borders_dict):
        """
        [ADVANCED] Creates Nested Border Definition.
        borders_dict example:
        {
            'top': {'sz': 4, 'val': 'single', 'color': 'FF0000'},
            'bottom': ...
        }
        """
        if not borders_dict: return

        tcPr = cls._get_or_create_tcPr(cell)
        
        # 1. tcBorders container
        tcBorders = tcPr.find(qn('w:tcBorders'))
        if tcBorders is None:
            tcBorders = cls.create_element('w:tcBorders')
            # Warning: We will insert it later via upsert to ensure main order
        else:
            # If creating fresh borders, prefer clearing old container logic via update
            # But here we just modify content.
            pass

        # 2. Iterate directions
        for side, props in borders_dict.items():
            if not props: continue
            
            # Tag: <w:top ... />
            tag_name = f"w:{side}"
            
            border_tag = cls.create_element(tag_name)
            
            # Special Case: 'nil' means no border
            val_type = props.get('val', 'single')
            if val_type == 'nil':
                cls.create_attribute(border_tag, 'w:val', 'nil')
            else:
                cls.create_attribute(border_tag, 'w:val', val_type)
                cls.create_attribute(border_tag, 'w:sz', str(props.get('sz', 4)))
                
                # [Collision Fix] Space
                # '0' space महत्वपूर्ण है ताकि Cell Border बिल्कुल ग्रिड लाइन पर बैठे
                # और Table Border (नीचे) को ढक सके।
                cls.create_attribute(border_tag, 'w:space', '0')
                
                # Color Handling
                color_val = props.get('color', 'auto')
                if val_type != 'nil':
                     cls.create_attribute(border_tag, 'w:color', color_val)

            # Safe Insert inside tcBorders using specific border sort order
            cls.upsert_child(tcBorders, border_tag, cls.BORDER_ORDER)

        # 3. Insert container back into tcPr
        cls.upsert_child(tcPr, tcBorders, cls.TC_PR_ORDER)

    @classmethod
    def set_v_merge(cls, cell, val):
        """
        Sets Rowspan.
        val: 'restart' (start of merge) or 'continue' (merged area).
        """
        tcPr = cls._get_or_create_tcPr(cell)
        
        vMerge = cls.create_element('w:vMerge')
        if val == 'restart':
            cls.create_attribute(vMerge, 'w:val', 'restart')
        # if val == 'continue', tag exists without val attribute implies continue
        
        cls.upsert_child(tcPr, vMerge, cls.TC_PR_ORDER)

    @classmethod
    def set_grid_span(cls, cell, span_count):
        """Sets Colspan (Horizontal Merge)."""
        if span_count <= 1: return
        
        tcPr = cls._get_or_create_tcPr(cell)
        
        gridSpan = cls.create_element('w:gridSpan')
        cls.create_attribute(gridSpan, 'w:val', str(span_count))
        
        cls.upsert_child(tcPr, gridSpan, cls.TC_PR_ORDER)

    @classmethod
    def set_cell_margins(cls, cell, margins_dict):
        """
        Sets Padding (Cell Margins).
        margins_dict: {'top': 100, 'left': 200 ...} (in Twips)
        """
        if not margins_dict: return
        tcPr = cls._get_or_create_tcPr(cell)
        
        tcMar = cls.create_element('w:tcMar')
        # Note: Internal order for margins: top, left, bottom, right
        
        # Since tcMar child order matters (Top -> Left -> Bottom -> Right)
        # We handle manual append sequence
        margin_order = ['top', 'left', 'bottom', 'right']
        
        for side in margin_order:
            val = margins_dict.get(side)
            if val is not None:
                tag = cls.create_element(f"w:{side}")
                cls.create_attribute(tag, 'w:w', str(val))
                cls.create_attribute(tag, 'w:type', 'dxa') # Always Twips here
                tcMar.append(tag)
        
        # Use simple replace if old exists to avoid mix-up
        cls.upsert_child(tcPr, tcMar, cls.TC_PR_ORDER)

    @classmethod
    def set_vertical_alignment(cls, cell, align):
        """Values: top, center, bottom"""
        tcPr = cls._get_or_create_tcPr(cell)
        
        # Word XML map
        map_val = {'middle': 'center', 'center': 'center', 'bottom': 'bottom', 'top': 'top'}
        final_val = map_val.get(align, 'top')
        
        vAlign = cls.create_element('w:vAlign')
        cls.create_attribute(vAlign, 'w:val', final_val)
        
        cls.upsert_child(tcPr, vAlign, cls.TC_PR_ORDER)

    @classmethod
    def set_text_direction(cls, cell, direction='tbRl'):
        """Sets text rotation (e.g. Vertical Text)."""
        tcPr = cls._get_or_create_tcPr(cell)
        
        textDirection = cls.create_element('w:textDirection')
        cls.create_attribute(textDirection, 'w:val', direction)
        
        cls.upsert_child(tcPr, textDirection, cls.TC_PR_ORDER)

    # =========================================================================
    # 2. 🟩 TABLE PROPERTIES (tblPr) - Global Level
    # =========================================================================

    @classmethod
    def set_table_width(cls, table, width_val, type_val='pct'):
        """
        Global Table Width. 
        type='pct' (5000=100%) or 'dxa' (Twips).
        """
        tblPr = table._element.tblPr
        
        tblW = cls.create_element('w:tblW')
        cls.create_attribute(tblW, 'w:w', str(width_val))
        cls.create_attribute(tblW, 'w:type', type_val)
        
        cls.upsert_child(tblPr, tblW, cls.TBL_PR_ORDER)

    @classmethod
    def set_table_alignment(cls, table, align_str):
        """Table Alignment: left, center, right"""
        tblPr = table._element.tblPr
        
        jc = cls.create_element('w:jc')
        cls.create_attribute(jc, 'w:val', align_str)
        
        cls.upsert_child(tblPr, jc, cls.TBL_PR_ORDER)

    @classmethod
    def set_table_indent(cls, table, indent_twips):
        """Sets Left Indentation (Margin-left behavior)."""
        tblPr = table._element.tblPr
        
        tblInd = cls.create_element('w:tblInd')
        cls.create_attribute(tblInd, 'w:w', str(indent_twips))
        cls.create_attribute(tblInd, 'w:type', 'dxa')
        
        cls.upsert_child(tblPr, tblInd, cls.TBL_PR_ORDER)

    @classmethod
    def set_table_layout(cls, table, layout_type='fixed'):
        """
        Layout Algorithm:
        - fixed: Respects specific column widths (Good for grids).
        - autofit: Resizes based on content (Good for simple data).
        """
        tblPr = table._element.tblPr
        
        tblLayout = cls.create_element('w:tblLayout')
        cls.create_attribute(tblLayout, 'w:type', layout_type)
        
        cls.upsert_child(tblPr, tblLayout, cls.TBL_PR_ORDER)

    @classmethod
    def set_table_look(cls, table, val_hex="04A0"):
        """Controls visual styles (firstRow, lastRow, banding). Default 04A0."""
        tblPr = table._element.tblPr
        
        tblLook = cls.create_element('w:tblLook')
        cls.create_attribute(tblLook, 'w:val', val_hex)
        
        cls.upsert_child(tblPr, tblLook, cls.TBL_PR_ORDER)
        
        
    @classmethod
    def set_table_layout_preset(cls, table, layout_type='fixed'):
        """टेबल के लेआउट को फिक्स या ऑटो करने के लिए सुरक्षित मेथड।"""
        tblPr = table._element.tblPr
        tblLayout = cls.create_element('w:tblLayout')
        cls.create_attribute(tblLayout, 'w:type', layout_type)
        cls.upsert_child(tblPr, tblLayout, cls.TBL_PR_ORDER)

    @classmethod
    def set_table_borders_to_none(cls, table):
        """टेबल की सभी 6 बॉर्डर साइड्स को 'nil' (अदृश्य) सेट करता है।"""
        tblPr = table._element.tblPr
        tblBorders = cls.create_element('w:tblBorders')
        
        # सभी जरूरी साइड्स जो लेआउट में बाधा डालती हैं
        sides = ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']
        for side in sides:
            bdr = cls.create_element(f'w:{side}')
            cls.create_attribute(bdr, 'w:val', 'nil')
            cls.create_attribute(bdr, 'w:sz', '0')
            cls.create_attribute(bdr, 'w:space', '0')
            tblBorders.append(bdr)
            
        cls.upsert_child(tblPr, tblBorders, cls.TBL_PR_ORDER)   
        
    # -------------------------------------------------------------
    # ADD NEW METHOD inside Class TableXml
    # -------------------------------------------------------------

    @classmethod
    def set_table_borders_sides(cls, table, borders_dict):
        """
        Applies Borders to the Table Properties (tblPr).
        Argument: borders_dict = {'top': {'val': 'single', 'sz': 12, 'color': 'FF0000'}, ...}
        """
        if not borders_dict: return

        # tblPr निकालें
        tblPr = table._element.tblPr
        
        # tblBorders टैग बनाएँ या ढूँढें
        # (चूँकि हमें ऑर्डर फॉलो करना है, हम इसे नया बनाकर इन्सर्ट करेंगे)
        tblBorders = cls.create_element('w:tblBorders')
        
        # Word के लिए बॉर्डर का सही क्रम: top, left, bottom, right, insideH, insideV
        order_sides = ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']
        
        for side in order_sides:
            props = borders_dict.get(side)
            if props:
                tag = cls.create_element(f"w:{side}")
                # Attributes सेट करें
                cls.create_attribute(tag, 'w:val', props.get('val', 'single'))
                cls.create_attribute(tag, 'w:sz', str(props.get('sz', 4)))
                cls.create_attribute(tag, 'w:space', '0')
                # w:color (HEX कोड RRGGBB)
                color = props.get('color')
                # अगर 'auto' है, तो उसे 'auto' रहने दें, वर्ना Hex इस्तेमाल करें
                cls.create_attribute(tag, 'w:color', color if color else 'auto')

                tblBorders.append(tag)
        
        # tblPr में सही क्रम पर लगायें (TBL_PR_ORDER का उपयोग करते हुए)
        # Note: 'tblBorders' हमारे TBL_PR_ORDER लिस्ट में पहले से होना चाहिए (base.py)
        cls.upsert_child(tblPr, tblBorders, cls.TBL_PR_ORDER)
        
        
        
    # -------------------------------------------------------------
    # 🆕 NEW METHOD FOR COLGROUP SUPPORT
    # -------------------------------------------------------------
    @classmethod
    def define_table_grid(cls, table, widths_list_twips):
        """
        Creates <w:tblGrid> structure based on <col> tags.
        Sequence in XML: <w:tblPr> ... <w:tblGrid> ... <w:tr>
        """
        if not widths_list_twips: return

        # 1. Main Table Element (<w:tbl>)
        tbl_element = table._element
        
        # 2. Create the Grid Container
        tblGrid = cls.create_element('w:tblGrid')
        
        # 3. Add Columns
        for w in widths_list_twips:
            gridCol = cls.create_element('w:gridCol')
            cls.create_attribute(gridCol, 'w:w', str(w))
            tblGrid.append(gridCol)
            
        # 4. Safe Insertion Strategy
        # <tblGrid> को <tblPr> के तुरंत बाद आना चाहिए, लेकिन <tr/> से पहले।
        
        # A. Remove existing grid if any
        old_grid = tbl_element.find(qn('w:tblGrid'))
        if old_grid is not None:
            tbl_element.remove(old_grid)
            
        # B. Find Insertion Point
        # सबसे आसान तरीका: tblPr के बाद डालें।
        tblPr = tbl_element.find(qn('w:tblPr'))
        if tblPr is not None:
            # lxml logic to insert 'after' specific node
            index = tbl_element.index(tblPr) + 1
            tbl_element.insert(index, tblGrid)
        else:
            # अगर tblPr नहीं है (Rare), तो सबसे ऊपर डालें
            tbl_element.insert(0, tblGrid)   
            
    @classmethod
    def set_cell_no_wrap(cls, cell, no_wrap=True):
        """
        Maps CSS 'white-space: nowrap'.
        Prevents text from breaking into multiple lines, expanding the cell instead.
        """
        tcPr = cls._get_or_create_tcPr(cell)
        
        # Tag: <w:noWrap w:val="on"/>
        # If False, we should remove the tag, but usually we just set it if True.
        if no_wrap:
            tag = cls.create_element('w:noWrap')
            cls.create_attribute(tag, 'w:val', 'on')
            cls.upsert_child(tcPr, tag, cls.TC_PR_ORDER)

    @classmethod
    def set_cell_fit_text(cls, cell, fit_text=True):
        """
        Maps specific 'word-break' logic or compression.
        """
        tcPr = cls._get_or_create_tcPr(cell)
        if fit_text:
            tag = cls.create_element('w:tcFitText')
            cls.create_attribute(tag, 'w:val', 'on')
            cls.upsert_child(tcPr, tag, cls.TC_PR_ORDER)        