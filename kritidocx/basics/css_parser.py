"""
CSS PARSER (The Bridge)
-----------------------
Proxies calls to the new 'Advanced CSS Engine'.
Do not delete this file; it maintains compatibility with existing Imports.
"""

from kritidocx.css_engine.main import CssEngine as NewEngine

class CssParser:
    @staticmethod
    def parse(style_str):
        # सीधा नए, शक्तिशाली इंजन को कॉल करें
        return NewEngine.parse(style_str)