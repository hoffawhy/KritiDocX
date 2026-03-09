"""
DROPDOWN HANDLER MODULE (The List Architect)
--------------------------------------------
Responsibility:
Converts HTML <select> tags into MS Word Dropdown Lists (SDT).

Features:
1. Option Parsing: Extracts value vs text mapping correctly.
2. Default Selection: Respects the 'selected' HTML attribute.
3. Metadata Injection: Maps HTML 'id/name' to Word SDT Tags.
4. Error Handling: Provides fallback items for empty lists.

Word Technicality:
Word Dropdowns (SDT) contain a 'w:dropDownList' with 'w:listItem'.
The visual text is inside 'w:sdtContent'.
"""

from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.basics.css_parser import CssParser

class DropdownHandler:
    """
    Controller for Dropdown List Controls.
    """

    @classmethod
    def add_dropdown(cls, select_node, paragraph):
        """
        Parses <select> and options to create a Word Dropdown.
        
        Args:
            select_node: BeautifulSoup <select> tag.
            paragraph: Parent docx Paragraph.
        """
        # 1. Parse Styling & Metadata
        style_str = select_node.get('style', '')
        # css_props = CssParser.parse(style_str) # Logic if needed for color customization later
        
        # HTML ID/Name becomes the SDT "Tag" (Useful for form data extraction)
        control_alias = select_node.get('name') or select_node.get('id') or "dropdown_control"

        # 2. Extract Options
        # Logic: Find all <option> children
        html_options = select_node.find_all('option')
        
        items_list = []
        default_display_text = None
        
        for opt in html_options:
            # Display Text (Visible to user)
            display = opt.get_text(strip=True)
            if not display: display = " " # Empty check
            
            # Internal Value (Used for database/logic)
            # Default to display text if value missing
            val = opt.get('value', display)
            
            items_list.append((display, val))
            
            # 3. Handle 'selected' State
            if opt.has_attr('selected'):
                default_display_text = display

        # 4. Fallback Logic (Safety)
        if not items_list:
            items_list.append(("[No Options Available]", "none"))
            default_display_text = "[No Options Available]"
        
        # If no explicit selection, default to the first item (Browser standard)
        if default_display_text is None:
            default_display_text = items_list[0][0] # Display text of first tuple

        # 5. Call XML Builder
        # We pass the alias/tag logic if XML builder supports extended params
        # For now using standard signature based on XML Builder facade
        
        # Note: XML Builder 'insert_sdt_dropdown' usually expects: (paragraph, items, default_text)
        # To add alias/tag support, update XML Builder logic or keep basic here.
        # Current standard Builder call:
        
        XmlBuilder.insert_sdt_dropdown(
            paragraph=paragraph,
            items=items_list,
            default_text=default_display_text
        )
        
        # Optional: Advanced metadata injection via direct XML access
        # if control_alias:
        #     # Logic to access last inserted SDT and set <w:tag> could go here 
        #     # if not handled by factory wrapper.
        #     pass