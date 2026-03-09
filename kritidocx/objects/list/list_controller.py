"""
from kritidocx.utils.logger import logger
LIST CONTROLLER MODULE (The Hierarchy Manager)
----------------------------------------------
Responsibility:
Manages the State (Level, ID) of lists during traversal.
Calculates nesting logic and acts as a bridge between HTML structure 
and Word's Flat Paragraph structure.

Logic Flow:
1. Detect List Start (<ul>/<ol>).
2. Check existing context (Are we already inside a list?).
3. Request NumID from NumberingManager.
4. Prepare Context dictionary.
5. Recursively pass context to Router for <li> processing.
"""

from kritidocx.config.settings import AppConfig
from kritidocx.objects.list.numbering_manager import NumberingManager
from kritidocx.objects.list.indent_math import IndentMath
from kritidocx.utils import logger
from kritidocx.xml_factory.xml_builder import XmlBuilder
from kritidocx.config.theme import ThemeConfig

class ListController:
    """
    Manages recursion state for Bulleted and Numbered lists.
    """

    def __init__(self, doc_driver):
        self.doc = doc_driver.doc
        # Connect to the Database Admin (Numbering Manager)
        self.num_manager = NumberingManager(doc_driver.doc)

    def process_list(self, list_node, container, parent_context, router_instance):
        """
        Main entry point called by Router when encountering <ul> or <ol>.
        
        Args:
            list_node: BS4 Tag (<ul> or <ol>)
            container: Word Doc/Cell/Div
            parent_context: Dict inherited from above (contains color/font etc.)
            router_instance: The central router to continue traversing children.
        """
        tag_name = list_node.name.lower()
        
        # 1. ANALYZE CURRENT STATE (Recursion Depth)
        # Check if we inherited list data from parent
        current_depth = parent_context.get('list_depth', -1)
        inherited_num_id = parent_context.get('num_id')
        
        # =========================================================================
        # [FIXED LOGIC START]: Detect Style from HTML Class + Logging Switch
        # =========================================================================
        from kritidocx.config.settings import AppConfig
        
        # HTML से क्लासेस निकालें (BS4 list या string दे सकता है)
        node_classes = list_node.get('class', [])
        if isinstance(node_classes, str): node_classes = [node_classes]
        
        # स्टाइल तय करें
        if tag_name == 'ol':
            # यदि वर्तमान टैग में 'legal' क्लास है OR पैरेंट लिस्ट पहले से 'legal' थी
            if 'legal' in node_classes or parent_context.get('list_type') == 'legal':
                style_type = 'legal'
            else:
                style_type = 'decimal'
        else:
            style_type = 'bullet'

            
        # Logging Switch (config/settings.py के DEBUG_LISTS से नियंत्रित)
        if getattr(AppConfig, 'DEBUG_LISTS', False):
            logger.debug(f"   🔍 [DEBUG LIST]: Tag=<{tag_name}> | Classes Found={node_classes} | Chosen Style={style_type}")
  
        # Override for Checkboxes logic if needed
        # (Assuming CSS class or type check could switch this later)
        
        # 2. DECIDE: NEW LIST OR CONTINUATION?
        final_num_id = None
        
        # पिछले लिस्ट का प्रकार चेक करें (ताकि OL और UL मिक्स न हों)
        previous_type = parent_context.get('list_type')
        
        # [STEP 6 FIX]: Smart Nesting Logic
        # Case A: Same Type Nesting (OL > OL or UL > UL)
        # हम ID को 'Reuse' करेंगे ताकि 1. के बाद 1.1 आए (Hierarchy बनी रहे)।
        if inherited_num_id is not None and previous_type == style_type:
            final_num_id = inherited_num_id
            new_depth = current_depth + 1
            
        # Case B: Mixed Type Switching (OL > UL) or Root List
        else:
            final_num_id = self.num_manager.create_list_instance(style_type)
            
            # [FIX]: Depth Logic for Mixed Lists
            # अगर हम किसी लिस्ट के अंदर हैं (inherited_num_id मौजूद है), तो 
            # लेवल को 0 पर रीसेट करने के बजाय 'बढ़ाना' चाहिए, 
            # ताकि टेक्स्ट सही इंडेंटेशन (Indentation) पर दिखे।
            if inherited_num_id is not None:
                new_depth = current_depth + 1
            else:
                # यह सचमुच एक नई रूट लिस्ट है
                new_depth = 0
            
        # Word Limit Safety (Max 9 levels: 0-8)
        if new_depth > 8: new_depth = 8
        

        # 3. PREPARE NEW CONTEXT
        # Create a new context specifically for the children (<li>) of THIS list
        list_context = parent_context.copy()
        
        list_context.update({
            'num_id': final_num_id,
            'list_depth': new_depth,
            'list_type': style_type,
            
            # Reset Layout Params: Lists shouldn't inherit Flex/Grid logic internally
            'layout_mode': None,
            'width_pct': None 
        })

        # [DEBUG LOG]
        if getattr(AppConfig, 'DEBUG_LISTS', False):
            logger.debug(f"   🌲 [ListController] Recursion Step | Depth: {new_depth} | Active ID: {final_num_id} | Tag: {tag_name}")

        # =========================================================================
        # [NEW UPDATE]: CREATE WRAPPER BOX (To Fix missing container)
        # यदि <ul> में बॉर्डर/बैकग्राउंड है, तो हमें उसे रखने के लिए एक बॉक्स बनाना होगा।
        # अन्यथा, हम डॉक्यूमेंट बॉडी का ही उपयोग करेंगे।
        # =========================================================================
        
        target_container = container if container is not None else self.doc
        
        # चेक करें कि क्या बॉक्स बनाने की आवश्यकता है?
        visual_styles_present = any(k in parent_context for k in ['border', 'background-color', 'background', 'block_bg'])
        
        if visual_styles_present and router_instance:
            # 1. ड्राइवर से टेबल कंट्रोलर का उपयोग करके बॉक्स बनाएँ
            # (यह 'TableController.create_box_container' लॉजिक का उपयोग करता है)
            box_cell = router_instance.driver.table_ctrl.create_box_container(parent_context, target_container)
            
            # 2. अब हमारा target बदल गया है (Doc -> Box Cell)
            target_container = box_cell

        # 4. 🟢 INSERTION & PROCESSING LOOP (CORE FIX)
   
        if list_node:
            # केवल सीधे 'li' बच्चे निकालें (नेस्टेड 'ul/ol' अपने आप राउटर से प्रोसेस होंगे)
            # note: find_all('li', recursive=False) bs4 का स्टैंडर्ड तरीका है
            import bs4
            items = []
            if isinstance(list_node, bs4.element.Tag):
                items = list_node.find_all('li', recursive=False)

            for li in items:
                # -------------------------------------------------------------
                # 🛠️ [RAW XML FIX START]: Handle Containers without helpers
                # -------------------------------------------------------------
                li_paragraph = None
                
                # Case A: Standard Document/Cell (Has helpers)
                if hasattr(target_container, 'add_paragraph'):
                    li_paragraph = target_container.add_paragraph()
                
                # Case B: Raw XML Element (Textbox/Shape Content)
                elif hasattr(target_container, 'append'):
                    # 1. Manual XML Creation
                    from kritidocx.xml_factory.xml_builder import XmlBuilder
                    from docx.text.paragraph import Paragraph
                    
                    p_node = XmlBuilder.create_element('w:p')
                    target_container.append(p_node)
                    
                    # 2. Wrapper (Doc Context passed via self.doc)
                    li_paragraph = Paragraph(p_node, self.doc)
                
                else:
                    # Fallback if unhandled type
                    continue
                # -------------------------------------------------------------


                # B. पैराग्राफ पर 'List Style' (Bullet/Number) लागू करें
                from kritidocx.objects.text.paragraph_manager import ParagraphManager
                ParagraphManager.apply_formatting(li_paragraph, list_context)

                # C. [CRITICAL FIX]: Recurse Children INTO THIS PARAGRAPH
                # 'router_instance' का उपयोग करके li के बच्चों (span, text, u) को प्रोसेस करें।
                # हम 'container=li_paragraph' भेज रहे हैं, ताकि राउटर को पता चले कि
                # नया पैराग्राफ नहीं बनाना है, इसी में टेक्स्ट जोड़ना है।
                
                # नोट: style_data (CSS) भी पास करें
                if router_instance:
                    # 'li' का खुद का CSS निकालें (जैसे color: red) और context में मिलाएं
                    from kritidocx.basics.css_parser import CssParser
                    li_css = CssParser.parse(li.get('style', ''))
                    child_context = list_context.copy()
                    child_context.update(li_css) # Merge li styles

                    for child in li.children:
                        # 1. नेस्टेड लिस्ट (ul/ol) के लिए विशेष चेक
                        # नेस्टेड लिस्ट को पैराग्राफ के 'अंदर' नहीं डाल सकते।
                        # वे अपने आप में ब्लॉक एलीमेंट हैं।
                        if child.name in ['ul', 'ol']:
                            # नेस्टेड लिस्ट के लिए पैराग्राफ को बंद करें (container=None भेजें या target_container)
                            router_instance.process_node(child, target_container, child_context)
                        
                        else:
                            # 2. इनलाइन सामग्री (span, text, b, img)
                            # इन्हें 'li_paragraph' के अंदर डालें
                            router_instance.process_node(child, li_paragraph, child_context)


    # =========================================================================
    # 🔌 TEXT ENGINE HOOK (Called by Text/ParagraphManager)
    # =========================================================================
    
    @staticmethod
    def apply_formatting(paragraph, style_data):
        """
        Used by `ParagraphManager` to apply XML tags when it detects list properties.
        This isolates the Logic from the Rendering.
        """
        num_id = style_data.get('num_id')
        depth = style_data.get('list_depth')

        # Validity Check
        if num_id is not None and depth is not None and depth >= 0:
            
            # 1. XML Injection: Connect Paragraph to the List ID
            # (<w:numPr> -> <w:numId val="X">, <w:ilvl val="Y">)
            from kritidocx.xml_factory.xml_builder import XmlBuilder
            XmlBuilder.set_paragraph_numbering(paragraph, depth, num_id)
            
            # 2. इंडेंट कैलकुलेट करें (1.25in वाली वैल्यू यहाँ आएगी)
            from .indent_math import IndentMath
            left_twips, hang_twips = IndentMath.calculate(
                depth, 
                style_overrides=style_data
            )
            
            # Explicitly force indentation settings
            # (Word defaults are often bad, we override them with calculation)
            XmlBuilder.set_paragraph_indent(
                paragraph, 
                left=left_twips, 
                hanging=hang_twips
            )
            
            # 3. Visual Cleanup (Spacing)
            # Lists look bad with extra space between items. 
            # We override 'Space After' to 0 unless CSS says otherwise.
            if 'margin-bottom' not in style_data:
                from docx.shared import Pt
                paragraph.paragraph_format.space_after = Pt(0)