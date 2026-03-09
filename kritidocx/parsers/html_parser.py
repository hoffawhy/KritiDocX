"""
HTML PARSER MODULE (The Content Ingestor)
-----------------------------------------
Responsibility:
Reads HTML/XML content, cleans it, processes styles, and dispatches nodes to the Core Router.

Advanced capabilities:
1. CSS Inlining: Moves global <style> rules into inline 'style' attributes.
2. Structure Cleanup: Unwraps html/body/head tags properly.
3. Whitespace Handling: Distinguishes between layout whitespace and text whitespace.
4. Normalization: Standardizes aliases (b -> strong, i -> em).

Integration:
Calls 'InputSanitizer' for cleanup.
Calls 'Router.process_node' to handover control to Logic Layer.
"""

import re
import os
import logging
from kritidocx.exceptions import InputNotFoundError
from bs4 import BeautifulSoup, NavigableString, Comment, Tag

from .sanitizer import InputSanitizer
from kritidocx.config.theme import ThemeConfig
from kritidocx.basics.css_parser import CssParser

logger = logging.getLogger("MyDocX_Parser")

class HtmlParser:
    """
    Main Logic Engine for parsing DOM structures.
    """

    def __init__(self, router_instance):
        """
        :param router_instance: The instantiated Router from kritidocx.core.router
        """
        self.router = router_instance
        
        # Tags that preserve whitespace
        self.PRESERVE_WS_TAGS = ['pre', 'code', 'textarea']

    # =========================================================================
    # 🚀 PUBLIC API
    # =========================================================================

    def parse_file(self, file_path):
        """Reads file securely with encoding handling."""
        if not os.path.exists(file_path):
            # कस्टम एरर ताकि यूजर try-except में पकड़ सके
            raise InputNotFoundError(f"Input file not found at: {file_path}")

        try:
            logger.info(f"📂 Parsing File: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.parse_string(content)
            
        except UnicodeDecodeError:
            # Fallback for older systems using cp1252/latin-1
            logger.warning("UTF-8 Decode failed, trying latin-1...")
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            self.parse_string(content)

    def parse_string(self, html_string):
        """
        Core pipeline: String -> Soup -> Clean Soup -> Flatten Styles -> Dispatch.
        """
        if not html_string.strip(): return

        # 1. Hygiene Check
        clean_html = InputSanitizer.clean_html(html_string, remove_styles=False)

        # 2. Build DOM Tree
        # 'html.parser' is faster, 'lxml' is more lenient. Using built-in for zero-dep strictness
        # (Though we require lxml in project, html.parser handles broken tags decently via bs4)
        soup = BeautifulSoup(clean_html, 'html.parser')

        # 3. Flatten Internal CSS (<style> to inline style)
        self._inline_css_styles(soup)

        # 4. Extract Document Metadata
        self._extract_metadata(soup)

        # 5. Determine Root Entry Point
        # Use body if present, else use full soup
        body_node = soup.find('body')
        entry_node = body_node if body_node else soup

        logger.info("🚀 Starting Traversal Phase...")

        # 6. Begin Traversal
        # We iterate over immediate children. The Router handles recursion.
        for child in entry_node.children:
            self._dispatch(child)
            
        logger.info("✅ Traversal Complete.")

    # -------------------------------------------------------------------------
    # [STEP 2]: SMART INJECTION ENGINE (Hybrid-Mode)
    # -------------------------------------------------------------------------
    def parse_with_template(self, template_path, injected_content_html, target_id='content'):
        """
        Reads HTML Template -> Finds container ID -> Injects content -> Processes full tree.
        Ensures template CSS applies to the new content.
        
        Args:
            template_path (str): Path to layout HTML file.
            injected_content_html (str): The body content (converted from MD).
            target_id (str): ID of the div to replace (default: "content").
        """
        if not os.path.exists(template_path):
            logger.error(f"❌ Template file missing: {template_path}")
            return

        # 1. Load Template
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_html = f.read()
        except UnicodeDecodeError:
            with open(template_path, 'r', encoding='latin-1') as f:
                template_html = f.read()

        # 2. Create Base Soup (Template)
        # Note: Do not remove styles, we need them for the new content!
        clean_tpl = InputSanitizer.clean_html(template_html, remove_styles=False)
        soup = BeautifulSoup(clean_tpl, 'html.parser')

        # 3. Create Content Fragment (Data)
        # content को भी soup ऑब्जेक्ट बनाएं ताकि append किया जा सके
        content_fragment = BeautifulSoup(injected_content_html, 'html.parser')

        # 4. 💉 SURGERY: Robust Injection Mechanism (Step 5 Update)
        
        # Priority 1: User requested ID (e.g. #content)
        target_container = soup.find(id=target_id)
        match_source = f"ID '#{target_id}'"

        # Priority 2: Semantic HTML Standard (<main>)
        if not target_container:
            target_container = soup.find('main')
            match_source = "<main> tag"

        # Priority 3: Common Layout Conventions (.content or .container)
        if not target_container:
            target_container = soup.find(class_='content') or soup.find(class_='container')
            match_source = "CSS Class .content/.container"

        # EXECUTION OF INJECTION
        if target_container:
            logger.info(f"   💉 Smart Injection: Found container via {match_source}")
            
            # सफाई: यदि टेम्पलेट में "Placeholder Text" लिखा था, तो उसे हटाएं
            target_container.clear() 
            
            # नया डाटा डालें
            target_container.append(content_fragment)
            
        else:
            # Priority 4: Ultimate Fallback (Append to Body end)
            logger.warning(f"   ⚠️ No suitable container found for injection. Appending to BODY end.")
            body_node = soup.find('body')
            
            if body_node:
                # बॉडी के अंत में चिपका दें (ताकि हैडर के ऊपर न चढ़ जाए)
                body_node.append(content_fragment)
            else:
                # यदि बॉडी टैग भी नहीं है (Invalid HTML), तो Root में चिपका दें
                soup.append(content_fragment)
                
        # -------------------------------------------------------
        # 5. EXECUTION: This sequence is CRITICAL for Style Inheritance
        # -------------------------------------------------------
        
        # A. Apply CSS (Inlining)
        # चूंकि इंजेक्शन पहले हुआ है, टेम्पलेट की CSS अब MD कंटेंट पर भी लागू होगी!
        self._inline_css_styles(soup)

        # B. Metadata
        self._extract_metadata(soup)

        # C. Determine Entry Point
        entry_node = soup.find('body') or soup

        # D. Start Engine
        logger.info("🚀 Starting Hybrid Traversal Phase...")
        for child in entry_node.children:
            self._dispatch(child)
            
        logger.info("✅ Hybrid Generation Complete.")

    # =========================================================================
    # 🕵️ DISPATCHER (Traffic Control)
    # =========================================================================

    def _dispatch(self, node):
        """
        Analyzes a single node and decides action.
        """
        # A. Comment Stripping
        if isinstance(node, Comment):
            return

        # B. Text Node Logic
        if isinstance(node, NavigableString):
            text = str(node)
            # Only process text if it's meaningful content
            # BUT: Check context (handled inside router text processing),
            # At Root/Body level, whitespace is usually formatting (ignore).
            if text.strip():
                # Router handles raw text -> paragraph logic
                self.router.process_node(node, container=None)
            return

        # C. Element Tag Logic
        if isinstance(node, Tag):
            # Normalize Tag Names
            self._normalize_tag(node)
            
            # Metadata tags removal
            if node.name in ['head', 'script', 'style', 'meta', 'link', 'title']:
                return

            # 🔥 THE BRIDGE: Pass control to Core Router
            # Container=None means "Add to Document Body"
            self.router.process_node(node, container=None)

    # =========================================================================
    # 🎨 STYLE PROCESSOR (The Inliner)
    # =========================================================================

    def _inline_css_styles(self, soup):
        """
        Extracts rules from <style> blocks and applies them to matching elements.
        Reason: Word objects usually only look at 'style="..."' attributes.
        """
        styles = soup.find_all('style')
        
        # Simple CSS Parser for Tag/Class selectors
        # Does NOT support complex specificity rules, but covers 90% report cases
        for style_tag in reversed(styles):
            if not style_tag.string: continue
            
            css_text = style_tag.string
            # Regex to grab "selector { body }"
            # Non-greedy match for content inside brackets
            rules = re.findall(r'([^{]+)\{(.*?)\}', css_text, re.DOTALL)
            
            for selector, body in reversed(rules):
                selector = selector.strip()
                clean_style = body.replace('\n', ' ').strip()
                if not clean_style: continue
                
                try:
                    # Apply to matches
                    # Only supporting basic selectors to avoid crash
                    matches = soup.select(selector)
                    for match in matches:
                        existing = match.get('style', '')
                        # Append new style. CSS Cascade: Latest wins.
                        # Put existing at end to preserve inline override priority
                        new_style_str = f"{clean_style}; {existing}"
                        match['style'] = new_style_str
                        
                except Exception:
                    # Ignore complex pseudo-selectors that bs4 doesn't support
                    pass
            
            # Remove <style> tag after processing to clean DOM
            style_tag.decompose()

    # =========================================================================
    # 🛠️ UTILITIES
    # =========================================================================

    def _extract_metadata(self, soup):
        """Sets Word Core Properties (Title, Author) if available."""
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            title_text = title_tag.string.strip()
            self.router.driver.doc.core_properties.title = title_text
            
        # Optional: Meta Author
        # author_tag = soup.find('meta', attrs={'name': 'author'}) ...
        pass

    def _normalize_tag(self, node):
        """Converts deprecated tags to semantic equivalents."""
        original = node.name.lower()
        
        # Remove namespace prefixes (e.g. o:p -> p)
        if ':' in original:
            node.name = original.split(':')[-1]
            return
        
        mapping = {
            'b': 'strong',
            'i': 'em',
            'strike': 's',
            'center': 'div', # We'll check 'center' alignment logic later
            'article': 'div',
            'section': 'div',
            'main': 'div',
            'figure': 'div'
        }
        
        if original in mapping:
            # For 'center', inject alignment style too
            if original == 'center':
                current_style = node.get('style', '')
                node['style'] = f"text-align: center; {current_style}"
            
            node.name = mapping[original]