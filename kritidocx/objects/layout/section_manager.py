"""
SECTION MANAGER MODULE (The Document Divider)
---------------------------------------------
Responsibility:
Manages Word Sections (Breaks, Layout Rules, Visual Properties).

What is a Section in Word?
It's a container for Page Setup. To change Margins, Orientation, or Columns
in the middle of a document, you MUST create a new Section.

Features:
- Break Types: Next Page, Continuous, Odd/Even Page.
- Line Numbering: Critical for Legal documents.
- Page Borders: Art/Line borders around the page.
- Vertical Alignment: Center text on Title Pages.
"""

from docx.enum.section import WD_SECTION
from kritidocx.xml_factory.xml_builder import XmlBuilder

class SectionManager:
    """
    Control logic for Document Sections.
    Operates on python-docx Section objects.
    """

    # Enum Mapping for readable API inputs
    BREAK_TYPES = {
        'next_page': WD_SECTION.NEW_PAGE,
        'continuous': WD_SECTION.CONTINUOUS,
        'even_page': WD_SECTION.EVEN_PAGE,
        'odd_page': WD_SECTION.ODD_PAGE,
        'column': WD_SECTION.NEW_COLUMN 
    }

    def __init__(self, doc):
        """
        :param doc: python-docx Document instance.
        """
        self.doc = doc

    # =========================================================================
    # 1. 🏗️ SECTION CREATION (Breaks)
    # =========================================================================

    def add_section_break(self, break_type='next_page'):
        """
        Inserts a new section break.
        Returns the NEW Section object.
        """
        # 1. Resolve Enum type
        wd_type = self.BREAK_TYPES.get(break_type.lower(), WD_SECTION.NEW_PAGE)
        
        # 2. Add Section
        # This appends a paragraph implicitly usually, creating logic gap in Word
        new_section = self.doc.add_section(wd_type)
        
        # 3. Inheritance Linkage (Optional Safety)
        # Note: python-docx usually inherits header/footer/page-size from previous.
        # But specifically checking 'start_type' logic ensures cleanliness.
        new_section.start_type = wd_type
        
        return new_section

    def get_last_section(self):
        """Returns the current active section (last one)."""
        if self.doc.sections:
            return self.doc.sections[-1]
        return None

    def get_section_by_index(self, index):
        """Safe access to arbitrary sections."""
        try:
            return self.doc.sections[index]
        except IndexError:
            return None

    # =========================================================================
    # 2. ⚖️ LEGAL LINE NUMBERING (Advanced Layout)
    # =========================================================================

    def apply_line_numbering(self, section=None, start_at=1, restart_mode='new_section', count_by=1):
        """
        Enables line numbering in the left margin.
        
        Args:
            section: Target section (defaults to last).
            start_at: Number to start from (e.g., 1).
            restart_mode: 'new_section', 'new_page', or 'continuous'.
            count_by: Increment (Display every nth number).
        """
        target = section if section else self.get_last_section()
        if not target: return

        # Map 'new_section' -> 'newSection' XML Value
        restart_map = {
            'new_section': 'newSection',
            'new_page': 'newPage',
            'continuous': 'continuous'
        }
        xml_restart = restart_map.get(restart_mode, 'newSection')

        # Call XML Builder
        XmlBuilder.set_section_line_numbering(target, start_at, xml_restart, count_by=count_by)

    # =========================================================================
    # 3. 📐 VERTICAL ALIGNMENT (For Cover Pages)
    # =========================================================================

    def set_vertical_alignment(self, align_type='top', section=None):
        """
        Controls vertical text flow.
        Usage: Set 'center' for Cover Pages to center titles perfectly.
        Values: 'top', 'center', 'bottom', 'both' (justified).
        """
        target = section if section else self.get_last_section()
        if not target: return

        # Valid XML values: top, center, bottom, both
        safe_val = align_type.lower()
        if safe_val == 'middle': safe_val = 'center' # Alias
        
        XmlBuilder.set_section_valign(target, safe_val)

    # =========================================================================
    # 4. 🎨 PAGE BORDERS (Art & Frames)
    # =========================================================================

    def apply_page_borders(self, style_dict, section=None):
        """
        Apply global borders to the page.
        Supports both: Single Style Dict OR Full Config Dict.
        """
        target = section if section else self.get_last_section()
        if not target or not style_dict: return

        # [UPDATED] Check if input is ALREADY a full configuration (Used by advanced tests)
        if 'borders' in style_dict and isinstance(style_dict['borders'], dict):
            # Pass through the manual config directly
            XmlBuilder.set_section_borders(target, style_dict)
            return        
        border_config = {
            'display': 'allPages',  # Default logic
            'offset_from': 'text',  # Or 'page' edge
            'z_order': 'front',
            'borders': {
                'top': style_dict,
                'bottom': style_dict,
                'left': style_dict,
                'right': style_dict
            }
        }
        
        # Check special flag for First Page Only
        # (Useful if users say "Cover Border only")
        if style_dict.get('first_page_only'):
            border_config['display'] = 'firstPage'

        XmlBuilder.set_section_borders(target, border_config)

    # =========================================================================
    # 5. 🛠️ CLEANUP UTILS
    # =========================================================================

    def remove_last_break(self):
        """
        Use case: Orientation switch creates an unavoidable break.
        If the last paragraph is empty, clean it before section start.
        """
        if len(self.doc.paragraphs) == 0: return
        
        last_p = self.doc.paragraphs[-1]
        if not last_p.text.strip() and not last_p.runs:
            # Delete element using lxml parent logic
            p_element = last_p._element
            p_element.getparent().remove(p_element)
            # Remove from python-docx list cache manually? 
            # Not needed as it reads from element tree, but good to be aware.