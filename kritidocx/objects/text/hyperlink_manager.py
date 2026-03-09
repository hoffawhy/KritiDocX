"""
HYPERLINK MANAGER MODULE (The Connectivity Engine)
--------------------------------------------------
Responsibility:
Creates clickable links inside text paragraphs.

Types Managed:
1. External: Web URLs (https://...), Mailto (mailto:), File paths (file://).
2. Internal: Bookmarks/Anchors (#introduction).

Features:
- Auto Relationship Mapping (rId generation).
- Tooltips (Hover Text).
- Visited/Unvisited Logic flag.
- Custom Styling override (Not just default blue).
"""

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
import docx

from kritidocx.basics.color_manager import ColorManager
from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.config.theme import ThemeConfig
# Circular import avoidance: We need RunManager logic, but let's keep dependency clean.
# We will duplicate a tiny run creation or inject style manually via XmlBuilder.

class HyperlinkManager:
    """
    Advanced controller for Document Links.
    """

    @classmethod
    def add_hyperlink(cls, paragraph, url, text_content, style_data=None, tooltip=None):
        """
        Master method to inject a hyperlink.
        
        Args:
            paragraph: Target paragraph object.
            url (str): Target address (http://... or #anchor).
            text_content (str): The visible text.
            style_data (dict): Styling overrides (Bold, Color).
            tooltip (str): Text shown on mouse hover.
        """
        if not url or not text_content:
            # Fallback to plain text if invalid data
            if text_content: paragraph.add_run(text_content)
            return

        # 1. Initialize XML Structure
        hyperlink = OxmlElement('w:hyperlink')
        
        # 2. Determine Type (Internal vs External)
        is_internal = url.startswith('#')
        
        if is_internal:
            # Anchor Link Logic
            anchor_name = url.lstrip('#')
            # Word Anchors usually don't support spaces easily, handle mapping if needed
            # For now assume clean anchor
            cls._set_attribute(hyperlink, 'w:anchor', anchor_name)
        else:
            # External Web/File Link Logic
            # Needs valid rId from relationship manager
            r_id = cls._get_or_create_relationship(paragraph.part, url)
            cls._set_attribute(hyperlink, 'r:id', r_id)

        # 3. Configure Behavior flags
        # history=1 prevents the link from looking "Visited" (Purple) immediately
        cls._set_attribute(hyperlink, 'w:history', '1')
        
        # Add Tooltip if provided
        if tooltip:
            cls._set_attribute(hyperlink, 'w:tooltip', str(tooltip))

        # 4. Create Inner Run (The Visible Part)
        # Hyperlinks contains Runs, just like Paragraphs.
        new_run = OxmlElement('w:r')
        
        # 5. Apply Visual Styles (Crucial Phase)
        # Link Style Logic: User Override > Default Theme > Native Word Default
        
        final_style = style_data.copy() if style_data else {}
        
        # If user did NOT specify color, force Theme Hyperlink Color
        # (Otherwise links might look like normal black text)
        if not final_style.get('color'):
            theme_color = ThemeConfig.THEME_COLORS.get('hyperlink', '0563C1') # Standard Blue
            final_style['color'] = theme_color
            
        # If user did NOT specify underline status, force Underline
        if 'underline' not in final_style and 'text-decoration' not in final_style:
            final_style['underline'] = True
        
        # 6. Apply formatting using XML Builder Logic
        # We assume the caller might want bold/italic from styles
        cls._style_hyperlink_run(new_run, final_style, text_content)

        # 7. Append Structure
        hyperlink.append(new_run)
        paragraph._p.append(hyperlink)

        return hyperlink

    # =========================================================================
    # 🔗 INTERNAL UTILITIES
    # =========================================================================

    @staticmethod
    def _set_attribute(element, attr_name, value):
        """Safe attribute setter with Namespace support."""
        if ':' in attr_name:
            element.set(qn(attr_name), str(value))
        else:
            element.set(attr_name, str(value))

    @staticmethod
    def _get_or_create_relationship(part, url):
        """
        Manages the .rels file integration.
        Uses existing Relationship ID if URL exists, else creates new.
        """
        return part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    @staticmethod
    def _style_hyperlink_run(run_element, style_data, text_content):
        """
        Manually builds the Run XML since we can't easily use RunManager 
        on a raw XML node disconnected from python-docx Wrapper initially.
        """
        # A. Create Properties
        rPr = OxmlElement('w:rPr')
        
        # B. Native Hyperlink Style
        # This tells Word "Use the Blue color logic from styles.xml"
        # However, manual override (below) is stronger.
        rStyle = OxmlElement('w:rStyle')
        HyperlinkManager._set_attribute(rStyle, 'w:val', 'Hyperlink')
        rPr.append(rStyle)

        # C. Manual Overrides (via XML Builder directly for speed/import safety)
        
        # Color
        if style_data.get('color'):
            c_val = ColorManager.get_hex(style_data['color'])
            if c_val:
                # [FIXED] Direct XML injection. 
                # We are building raw XML manually here, so avoiding Builder dependencies is safer and faster.
                color = OxmlElement('w:color')
                HyperlinkManager._set_attribute(color, 'w:val', c_val)
                rPr.append(color)

        # Underline
        if style_data.get('underline') or style_data.get('text_decoration') == 'underline':
            u = OxmlElement('w:u')
            HyperlinkManager._set_attribute(u, 'w:val', 'single')
            rPr.append(u)
            
        # Bold/Italic
        if style_data.get('bold'): rPr.append(OxmlElement('w:b'))
        if style_data.get('italic'): rPr.append(OxmlElement('w:i'))

        # Add Properties to Run
        run_element.append(rPr)
        
        # D. Add Text Content
        t = OxmlElement('w:t')
        # Preserve whitespace is important for links in sentences
        HyperlinkManager._set_attribute(t, 'xml:space', 'preserve')
        t.text = str(text_content)
        run_element.append(t)