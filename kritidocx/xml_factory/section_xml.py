"""
SECTION XML FACTORY (The Page Architect)
----------------------------------------
Responsibility:
Generates XML for Section Properties (sectPr).
This controls:
1. Page Geometry (Size, Orientation).
2. Margins (Gutter, Headers dist).
3. Layout (Columns, Line Numbering).
4. References (Headers/Footers).
5. Visuals (Page Borders, Vertical Alignment).

Strict Schema:
Respects 'SECT_PR_ORDER' to prevent corrupt files.
"""

from kritidocx.utils.logger import logger
from docx.oxml.ns import qn
from .base import XmlBase

class SectionXml(XmlBase):
    
    # Border Sides for Page Borders
    BORDER_SIDES = ['top', 'left', 'bottom', 'right']

    @staticmethod
    def _get_sectPr(section):
        """Helper to get raw XML element from a Section object."""
        return section._sectPr

    # =========================================================================
    # 1. 📄 PAGE GEOMETRY (Size & Margins)
    # =========================================================================

    @classmethod
    def set_page_size(cls, section, width, height, orientation='portrait'):
        """
        Sets A4/Letter size and Orientation.
        XML: <w:pgSz w:w="..." w:h="..." w:orient="..."/>
        Units: Twips.
        """
        sectPr = cls._get_sectPr(section)
        
        pgSz = cls.create_element('w:pgSz')
        
        # DEBUG: Final Attribute Writer
        logger.debug(f"      📝 [SectionXml] Creating Tag: <w:pgSz w={width} h={height} ... />")
 
        cls.create_attribute(pgSz, 'w:w', width)
        cls.create_attribute(pgSz, 'w:h', height)
        if orientation:
            logger.debug(f"      ✅ [SectionXml] Wrote Attribute: w:orient='{orientation}'")
            cls.create_attribute(pgSz, 'w:orient', str(orientation))
        else:
            logger.debug(f"      ❌ [SectionXml] 'orientation' argument was None or False!")
      
        cls.upsert_child(sectPr, pgSz, cls.SECT_PR_ORDER)

    @classmethod
    def set_page_margins(cls, section, margins_dict):
        """
        Sets margins.
        XML: <w:pgMar w:top="..." w:bottom="..." .../>
        keys: top, bottom, left, right, header, footer, gutter.
        Units: Twips.
        """
        sectPr = cls._get_sectPr(section)
        pgMar = cls.create_element('w:pgMar')
        
        # Default keys mapping to attributes
        for key in ['top', 'bottom', 'left', 'right', 'header', 'footer', 'gutter']:
            val = margins_dict.get(key)
            if val is not None:
                cls.create_attribute(pgMar, f"w:{key}", str(val))
                
        cls.upsert_child(sectPr, pgMar, cls.SECT_PR_ORDER)

    # =========================================================================
    # 2. 📰 COLUMNS & NUMBERING (Layout)
    # =========================================================================

    @classmethod
    def set_columns(cls, section, num=1, space=720, equal_width=True, separator=False):
        """
        Multi-column setup.
        XML: <w:cols w:num="2" w:space="720" w:sep="1"/>
        space: Gap between columns (Twips). 720 = 0.5 inch.
        """
        sectPr = cls._get_sectPr(section)
        cols = cls.create_element('w:cols')
        
        cls.create_attribute(cols, 'w:num', str(num))
        cls.create_attribute(cols, 'w:space', str(space))
        cls.create_attribute(cols, 'w:equalWidth', '1' if equal_width else '0')
        
        if separator:
            cls.create_attribute(cols, 'w:sep', '1') # Vertical line between cols
            
        cls.upsert_child(sectPr, cols, cls.SECT_PR_ORDER)

    @classmethod
    def set_line_numbering(cls, section, start=1, count_by=1, restart='newSection', distance=0):
        """
        Legal Line Numbering.
        XML: <w:lnNumType .../>
        restart: newPage, newSection, continuous.
        """
        sectPr = cls._get_sectPr(section)
        ln = cls.create_element('w:lnNumType')
        
        cls.create_attribute(ln, 'w:countBy', str(count_by))
        cls.create_attribute(ln, 'w:start', str(start))
        cls.create_attribute(ln, 'w:restart', restart)
        if distance > 0:
            cls.create_attribute(ln, 'w:distance', str(distance))
            
        cls.upsert_child(sectPr, ln, cls.SECT_PR_ORDER)

    @classmethod
    def set_doc_grid(cls, section, type_val='lines', line_pitch=None):
        """
        Sets Document Grid (lines per page).
        Critical for exact layout replication from government docs.
        """
        sectPr = cls._get_sectPr(section)
        grid = cls.create_element('w:docGrid')
        
        cls.create_attribute(grid, 'w:type', type_val)
        if line_pitch:
            cls.create_attribute(grid, 'w:linePitch', str(line_pitch))
            
        cls.upsert_child(sectPr, grid, cls.SECT_PR_ORDER)

    # =========================================================================
    # 3. 🎩 HEADERS & FOOTERS LINKING
    # =========================================================================

    @classmethod
    def set_reference(cls, section, ref_type, r_id, type_attr='default'):
        """
        Links a Header/Footer part to this section.
        ref_type: 'headerReference' or 'footerReference'
        type_attr: 'default', 'first', 'even'
        """
        sectPr = cls._get_sectPr(section)
        
        # 1. Clean collision: 
        # A section can have 3 headerRefs. We must remove only the one matching type='type_attr'
        tag_name = qn(f'w:{ref_type}')
        existing = sectPr.findall(tag_name)
        
        for node in existing:
            if node.get(qn('w:type')) == type_attr:
                sectPr.remove(node)
                
        # 2. Create New Reference
        ref = cls.create_element(f'w:{ref_type}')
        cls.create_attribute(ref, 'w:type', type_attr)
        cls.create_attribute(ref, 'r:id', r_id)
        
        # 3. Smart Insert (No strict simple-sort because duplication logic handled manually above)
        # Note: Ideally all references are grouped. We'll append then sort standard list.
        sectPr.append(ref)
        
        # Force Full Re-Sort (Safest method)
        cls.sort_element_children(sectPr, cls.SECT_PR_ORDER)

    @classmethod
    def set_title_page_flag(cls, section, is_active=True):
        """Sets <w:titlePg/>. Needed for 'Different First Page'."""
        sectPr = cls._get_sectPr(section)
        if is_active:
            # Add flag if True
            tag = cls.create_element('w:titlePg')
            cls.upsert_child(sectPr, tag, cls.SECT_PR_ORDER)
        else:
            # Remove flag if False
            existing = sectPr.find(qn('w:titlePg'))
            if existing is not None:
                sectPr.remove(existing)

    # =========================================================================
    # 4. 📐 VERTICAL ALIGNMENT & BORDERS
    # =========================================================================

    @classmethod
    def set_vertical_alignment(cls, section, val='top'):
        """
        Centers text vertically on the page (Good for Covers).
        val: 'top', 'center', 'both' (justified), 'bottom'.
        XML: <w:vAlign w:val="center"/>
        """
        sectPr = cls._get_sectPr(section)
        vAlign = cls.create_element('w:vAlign')
        cls.create_attribute(vAlign, 'w:val', val)
        cls.upsert_child(sectPr, vAlign, cls.SECT_PR_ORDER)

    @classmethod
    def set_page_borders(cls, section, border_config):
        """
        Sets Page Borders.
        border_config = {
            'display': 'all_pages' (default) | 'not_first_page' | 'first_page',
            'offset_from': 'text' | 'page',
            'z_order': 'front' | 'back',
            'borders': {'top': {'val': 'single', ...}, ...}
        }
        XML: <w:pgBorders w:offsetFrom="page"> <w:top .../> </w:pgBorders>
        """
        if not border_config or not border_config.get('borders'): return

        sectPr = cls._get_sectPr(section)
        
        pgBorders = cls.create_element('w:pgBorders')
        
        # Properties
        cls.create_attribute(pgBorders, 'w:offsetFrom', border_config.get('offset_from', 'text'))
        cls.create_attribute(pgBorders, 'w:zOrder', border_config.get('z_order', 'front'))
        cls.create_attribute(pgBorders, 'w:display', border_config.get('display', 'allPages'))
        
        # Border Sides
        borders = border_config.get('borders', {})
        for side in cls.BORDER_SIDES:
            props = borders.get(side)
            if props:
                tag = cls.create_element(f'w:{side}')
                cls.create_attribute(tag, 'w:val', props.get('val', 'single'))
                cls.create_attribute(tag, 'w:sz', str(props.get('sz', 24))) # default 3pt
                cls.create_attribute(tag, 'w:space', str(props.get('space', 24)))
                cls.create_attribute(tag, 'w:color', props.get('color', 'auto'))
                if props.get('shadow'):
                    cls.create_attribute(tag, 'w:shadow', '1')
                pgBorders.append(tag)
        
        cls.upsert_child(sectPr, pgBorders, cls.SECT_PR_ORDER)