"""
FORM CONTROLLER MODULE (The Interaction Dispatcher)
---------------------------------------------------
Responsibility:
Central entry point for all Form Controls.
Delegates HTML nodes to specific Handlers based on Tag Name and Type attribute.

Mapping Logic:
1. <input type="checkbox">  -> CheckboxHandler
2. <select>                 -> DropdownHandler
3. <input type="text">      -> TextInputHandler
4. <input type="date">      -> Internal Date Logic
5. <textarea>               -> TextInputHandler (Multiline mode)

Integration:
- Works with Router.process_node().
- Ensures valid paragraph context before insertion.
"""

from .checkbox_handler import CheckboxHandler
from .dropdown_handler import DropdownHandler
from .text_input_handler import TextInputHandler
from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.config.theme import ThemeConfig
from kritidocx.xml_factory.form_xml import FormXml

from kritidocx.utils.logger import logger
from kritidocx.config.settings import AppConfig

class FormController:
    """
    Orchestrates form element conversion logic.
    """

    @classmethod
    def process_node(cls, node, paragraph, context=None):
        """
        Main API called by Router.
        
        Args:
            node: BeautifulSoup Node (<input>, <select>, <textarea>).
            paragraph: Target docx Paragraph.
        """
        if not node: return

        # 1. Container Safety Check
        # Forms need to live inside a paragraph run. If Router passed a Cell/Doc,
        # we must grab/create the active paragraph.
        target_para = cls._ensure_paragraph(paragraph)

        # 2. Identify Element Type
        tag_name = node.name.lower()
        
        # =========================================================
        # CASE A: INPUT TAGS
        # =========================================================
        if tag_name == 'input':
            input_type = node.get('type', 'text').lower()

            # --- Checkbox ---
            if input_type == 'checkbox':
                CheckboxHandler.add_checkbox(node, target_para, context)

            # --- Radio Button (Simulated) ---
            # Word handles radios poorly. We map them to Round Checkboxes logic.
            elif input_type == 'radio':
                # Reusing checkbox handler but forcing logic could happen here
                # or implemented directly.
                cls._handle_radio(node, target_para, context)

            # --- Date Picker ---
            elif input_type in ['date', 'datetime-local', 'month']:
                cls._handle_date(node, target_para)

            # --- Text Fields (Text, Email, Password, etc) ---
            else:
                TextInputHandler.add_text_field(node, target_para)

        # =========================================================
        # CASE B: SELECT (DROPDOWN)
        # =========================================================
        elif tag_name == 'select':
            DropdownHandler.add_dropdown(node, target_para)

        # =========================================================
        # CASE C: TEXTAREA
        # =========================================================
        elif tag_name == 'textarea':
            # 1. [FIX]: Force new paragraph for textareas (Heading से अलग करने के लिए)
            if hasattr(paragraph, '_parent') and hasattr(paragraph._parent, 'add_paragraph'):
                 target_para = paragraph._parent.add_paragraph()
            else:
                 target_para = paragraph

            # 2. Get content correctly
            content = node.get_text() # Tags के बीच का सारा टेक्स्ट लें
            
            # 3. Call Builder with multiline enabled
            from kritidocx.xml_factory.xml_builder import XmlBuilder
            XmlBuilder.insert_sdt_text(
                paragraph=target_para,
                initial_text=content.strip(),
                is_placeholder=False # क्योंकि यहाँ content मौजूद है
                # note: XmlBuilder.insert_sdt_text के signature में 'multiline=True' pass करें 
                # यदि आपने builder अपडेट किया है।
            )

    # -------------------------------------------------------------------------
    # 🕵️ SPECIALIZED INTERNAL HANDLERS
    # -------------------------------------------------------------------------

    @classmethod
    def _handle_date(cls, node, paragraph):
        """
        Invokes XML Date Picker control.
        """
        # New direct usage of factory method if available or Builder alias
        FormXml.create_date_picker(paragraph)



    @classmethod
    def _handle_radio(cls, node, paragraph, context=None):
        """
        Calibrated Radio Button Handling: Resolves the "Different Sizes" problem.
        """
        is_checked = node.has_attr('checked')
        
        # --- 1. सबसे संतुलित सिम्बल पेयर (Segoe UI Symbol/MS Gothic के लिए) ---
        # Selected: U+25C9 (◉) | Unselected: U+25CB (○)
        # नोट: U+25EF (◯) बहुत बड़ा है, उसे कभी इस्तेमाल न करें।
        symbol = "\u25C9" if is_checked else "\u25CB"
        
        # --- 2. Micro-Size Calibration (The Pro Secret) ---
        # आंखों के धोखे (Optical Illusion) को खत्म करने के लिए 
        # Selected (भरा हुआ) बिंदु 2 यूनिट बड़ा होना चाहिए।
        if is_checked:
            calibrated_size = 28  # Selected (Thick dot)
        else:
            calibrated_size = 15  # Unselected (Thin outline)

        # --- 3. Robust Color Logic ---
        from kritidocx.basics.css_parser import CssParser
        from kritidocx.basics.color_manager import ColorManager
        
        # Style Fetching
        styles = CssParser.parse(node.get('style', ''))
        raw_color = styles.get('color') or (context.get('color') if context else None)
        
        # Image Match Fallback (यदि कही से कलर नहीं मिला)
        if not raw_color:
            raw_color = '#2E74B5' # वही नीला जो आपकी इमेज में है
            
        target_hex = ColorManager.get_hex(raw_color)

        # DEBUG Trace
        if getattr(AppConfig, 'DEBUG_FORMS', False):
            logger.debug(f"🔘 [RADIO CALIBRATION] State: {is_checked} | Size: {calibrated_size} | Color: {target_hex}")

        # 4. Execute Builder call
        XmlBuilder.insert_sdt_checkbox(
            paragraph=paragraph,
            checked=is_checked,
            symbol_char=symbol,
            font_name=ThemeConfig.FONTS_COMPLEX.get('symbol', 'Segoe UI Symbol'), 
            hex_color=target_hex, 
            font_size=calibrated_size # यहाँ कैलिव्रेटेड वैल्यू जा रही है
        )
        
    # -------------------------------------------------------------------------
    # 🛡️ UTILITIES
    # -------------------------------------------------------------------------

    @staticmethod
    def _ensure_paragraph(container):
        """Validates that we have a Paragraph object, not Doc/Cell."""
        if hasattr(container, 'add_run'):
            return container
        
        # If it's a wrapper (Doc/Cell), get/create P
        if hasattr(container, 'paragraphs'):
            if len(container.paragraphs) > 0:
                return container.paragraphs[-1]
            return container.add_paragraph()
            
        return container # Fail-safe, might crash if raw element, but usually covered
    
    @classmethod
    def process_field_patterns(cls, text_node, paragraph):
        """
        टेक्स्ट में मौजूद { FIELD } पैटर्न को असली वर्ड फील्ड में बदलता है।
        """
        import re
        content = str(text_node)
        # Regex to find anything inside curly braces: { DATE }, { PAGE }
        parts = re.split(r'(\{.*?\})', content)
        
        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                # निकालें क्या कमांड है: { PAGE } -> PAGE
                command = part.strip('{} ').upper()
                from kritidocx.xml_factory.xml_builder import XmlBuilder
                # असली वर्ड फील्ड इंजेक्ट करें
                XmlBuilder.insert_field_code(paragraph, command)
            elif part.strip():
                # बचा हुआ सादा टेक्स्ट
                paragraph.add_run(part)