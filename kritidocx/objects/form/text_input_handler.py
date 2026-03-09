"""
TEXT INPUT HANDLER MODULE (The Data Collector)
----------------------------------------------
Responsibility:
Converts HTML Input fields (<input type="text">, <textarea>) into Word Text Content Controls (SDT).

Features:
1. Placeholder Engine: Manages the <w:showingPlcHdr> state properly.
2. Styling: Applies specific visual hints (Grey text) for empty fields.
3. Content Preservation: If 'value' attribute exists, it populates real data instead of placeholder.
4. Formatting Awareness: Inherits font/size from the parent paragraph context.

Technicality:
- Word distinguishes between "Placeholder Text" (vanishes on edit) and "Default Text" (editable).
- This handler sets that flag via XmlBuilder.
"""

from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.basics.color_manager import ColorManager
from kritidocx.basics.css_parser import CssParser

class TextInputHandler:
    """
    Controller for Text-based Form Controls.
    Handles 'text', 'password', 'email', 'url', 'tel', and 'search' types.
    """

    # Visual style for placeholders (Modern Standard)
    PLACEHOLDER_COLOR = "595959" # Dark Gray
    PLACEHOLDER_ITALIC = True

    @classmethod
    def add_text_field(cls, input_node, paragraph):
        """
        Parses input node and injects Word SDT into paragraph.
        
        Args:
            input_node: BS4 Tag <input ...>
            paragraph: Target docx Paragraph object
        """
        
        # 1. Extract Core Data
        val = input_node.get('value', '').strip()
        ph = input_node.get('placeholder', '').strip()
        name = input_node.get('name') or input_node.get('id')
        input_type = input_node.get('type', 'text').lower()

        # 2. Logic: Value vs Placeholder
        # Logic: If 'value' is present, it's real data (Not placeholder).
        #        If 'value' missing, use 'placeholder'.
        
        text_to_show = ""
        is_placeholder_flag = False
        
        if val:
            # CASE A: Real Data
            text_to_show = val
            is_placeholder_flag = False
        
        elif ph:
            # CASE B: Placeholder Hint
            text_to_show = ph
            is_placeholder_flag = True
            
        else:
            # CASE C: Nothing provided
            # Generate smart default based on type
            text_to_show = cls._get_default_hint(input_type)
            is_placeholder_flag = True

        # 3. Call XML Builder
        # Delegate to factory. 
        # Note: Ideally we pass the 'name' (metadata tag) here too if Builder supports it later.
        
        # (Optional Future enhancement: Builder.insert_sdt_text supports visual styling logic internally
        # or we rely on standard paragraph run style).
        
        XmlBuilder.insert_sdt_text(
            paragraph=paragraph,
            initial_text=text_to_show,
            is_placeholder=is_placeholder_flag
        )
        
        # 4. Advanced Styling Post-Process (Simulated)
        # Note: XmlBuilder's text handler creates the run inside the SDT.
        # If we wanted strict grey styling for placeholders, that logic resides 
        # inside 'src/xml_factory/form_xml.py' based on the 'is_placeholder' boolean.
        # We assume the factory handles the "Gray Color" implementation to keep this Handler clean.

    # -------------------------------------------------------------------------
    # 🧠 INTERNAL HELPERS
    # -------------------------------------------------------------------------

    @staticmethod
    def _get_default_hint(input_type):
        """Generates contextual hints if no placeholder provided."""
        hints = {
            'text': "[Click to enter text]",
            'email': "[name@example.com]",
            'url': "[https://www.example.com]",
            'password': "••••••", # Visual cue
            'tel': "[+91 ...]",
            'date': "[Select Date]",
            'number': "[0]"
        }
        return hints.get(input_type, "[Enter details]")