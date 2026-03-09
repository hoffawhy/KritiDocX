"""
MARKDOWN PARSER MODULE (The Syntax Translator)
----------------------------------------------
Responsibility:
Converts Markdown text into valid HTML5, preserving complex structures.
It serves as a Pre-processor for the HtmlParser.

Key Features:
1. Math Shield: Protects LaTeX ($$..$$) from being mangled by Markdown formatter.
2. Extension Pack: Supports Tables, Admonitions, Attribute Lists, and TOC.
3. Code Integrity: Ensures fenced code blocks (```python) render as structured HTML.
4. Auto-Formatting: Converts plain text links to HTML links.

Dependency:
- 'markdown' library (pip install markdown)
"""

import markdown
import re
import logging
from .html_parser import HtmlParser

# Logging
try:
    from kritidocx.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("MyDocX_Parser")

class MarkdownParser:
    """
    Advanced MD to HTML Converter with specialized pre-processing hooks.
    """

    def __init__(self, router_instance):
        """
        :param router_instance: Passed down to HtmlParser so it can dispatch nodes.
        """
        # We delegate the final node traversal to HtmlParser
        self.html_parser = HtmlParser(router_instance)
        
        # Configuration for the 'markdown' lib
        self.md_extensions = [
            'extra',          # Tables, Fenced Code, Footnotes, etc.
            'admonition',     # !!! note "Title" blocks
            'codehilite',     # Syntax highlighting support structure
            'meta',           # Metadata support (Frontmatter)
            'sane_lists',     # Better list logic
            'nl2br',          # Newline to <br>
            'attr_list',      # Allow custom CSS {: .myClass style="color:red"}
            'toc'             # Table of contents generator
        ]
        
        self.extension_configs = {
            'codehilite': {
                'css_class': 'highlight',
                'guess_lang': False,
                'use_pygments': False # Keeps HTML cleaner for Word
            }
        }

    # =========================================================================
    # 🚀 PUBLIC API
    # =========================================================================

    def parse_file(self, file_path):
        """Reads MD file and starts conversion chain."""
        logger.info(f"📄 Parsing Markdown File: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_text = f.read()
            self.parse_string(md_text)
        except Exception as e:
            logger.error(f"Failed to read MD file: {e}")


    # -------------------------------------------------------------
    # [NEW METHOD]: For Template Engine Integration (Step 1)
    # -------------------------------------------------------------
    def convert_to_html(self, md_text):
        """
        Pure conversion logic. Returns cleaned HTML string without triggering pipeline.
        Used when injecting Markdown content into an external HTML template.
        """
        if not md_text: return ""

        # 1. MATH GUARD
        safe_text, math_cache = self._protect_math_sequences(md_text)

        # 2. CORE CONVERSION (MD -> HTML)
        html_output = markdown.markdown(
            safe_text, 
            extensions=self.md_extensions,
            extension_configs=self.extension_configs
        )

        # 3. MATH RESTORE
        final_html = self._restore_math_sequences(html_output, math_cache)
        
        # 4. CUSTOM FIXES
        final_html = self._polish_html_structure(final_html)

        return final_html

    def parse_string(self, md_text):
        """
        Legacy Flow: Converts Markdown and immediately pushes to Router.
        """
        # Call the new logic helper
        final_html = self.convert_to_html(md_text)
        
        if not final_html: return

        # 5. Hand over to HTML Parser
        logger.debug("Markdown conversion successful. Handing off to HTML Parser.")
        self.html_parser.parse_string(final_html)

    # =========================================================================
    # 🛡️ MATH PROTECTION ENGINE
    # =========================================================================

    def _protect_math_sequences(self, text):
        """
        Finds $$...$$ and $...$ and replaces them with __MATH_TOKEN_X__.
        """
        cache = {}
        counter = 0
        
        # Helper callback
        def replacement(match):
            nonlocal counter
            
            # 🟢 UPDATE: Removed underscores to prevent Markdown 'Bold/Italic' interpretation
            # Used a random Alphanumeric Prefix/Suffix that Markdown won't parse
            token = f"MATHXGUARDX{counter}XTOKEN" 
            
            # The matched text (e.g. $$x^2$$)
            original = match.group(0)
            
            cache[token] = original
            counter += 1
            return token

        # 1. Block Math: $$ ... $$ (Multiline safe)
        # Pattern: Double Dollar, anything inside non-greedy
        block_pattern = r'(\$\$[\s\S]*?\$\$)'
        text = re.sub(block_pattern, replacement, text)

        # 2. Inline Math: $ ... $ (Single line safe)
        # Lookbehind logic prevents matching currency like $50.
        # Pattern ensures $ starts and ends cleanly
        # Note: We need to be careful not to match existing tokens
        inline_pattern = r'(?<!\\|\d|\w)\$(?! )(.+?)(?<! )\$'
        # Complex Regex Explanation:
        # (?<!\\) -> Not preceded by backslash
        # \$ ... \$ -> Dollar boundary
        # (.+?) -> Content
        text = re.sub(inline_pattern, replacement, text)

        return text, cache

    def _restore_math_sequences(self, html_text, cache):
        """
        Swaps tokens back to LaTeX.
        Includes a critical Fix:
        When math restores inside a <p>, ensure we wrap it so MathController 
        knows it is math (e.g., wrap in a <span data-type="math"> or similar logic 
        if we were using advanced parsing, but keeping it raw latex text ensures
        Regex detection in TextProcessor works).
        """
        if not cache: return html_text
        
        for token, math_content in cache.items():
            # Escape HTML issues? Usually Markdown generator doesn't touch custom tokens.
            # But math might contain < or > which markdown lib might encode if leaked.
            # Here we restore the RAW original math string (e.g., "$$ x < y $$")
            # The HTML Parser later has 'LatexParser' which handles < > entity decoding.
            
            html_text = html_text.replace(token, math_content)
            
        return html_text

    # =========================================================================
    # 🎨 HTML POLISHER
    # =========================================================================

    def _polish_html_structure(self, html_text):
        """
        Modifies specific patterns to be more Word-Friendly.
        """
        # Fix 1: Admonitions
        # Python-Markdown generates: <div class="admonition note"><p class="admonition-title">...</p>
        # We ensure they map to styles our CSS Parser recognizes.
        # We can inject inline styles directly here if we want absolute safety, 
        # but our Theme/CSS engine handles class mapping better.
        # So we leave the structure but ensure cleaning.
        
        # Fix 2: Checkboxes [ ] or [x] in Lists
        # 'sane_lists' usually handles it, but sometimes renders as text.
        # Force Unicode checkbox logic:
        html_text = html_text.replace('[ ]', '<input type="checkbox" disabled>')
        html_text = html_text.replace('[x]', '<input type="checkbox" checked disabled>')
        
        # Fix 3: Image Paths inside paragraphs
        # Sometimes markdown places <img> inside <p>. This is fine for our system 
        # as TextHandler delegates to Router for children.
        
        return html_text