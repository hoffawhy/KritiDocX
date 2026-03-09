"""
COLUMN MANAGER MODULE (The Newspaper Layout Engine)
---------------------------------------------------
Responsibility:
Manages multi-column layouts (Text splitting into vertical strips).
Operates directly on Section Properties.

Key Capabilities:
1. Column Creation: Sets Num, Space, and Equal Width logic.
2. Visual Separators: Toggle vertical lines between columns.
3. Content Width Logic: Calculates available width per column (Vital for resizing images/tables in columns).

XML Target: <w:cols>
"""

from docx.shared import Twips
from kritidocx.config.constants import DocConstants
from kritidocx.basics.unit_converter import UnitConverter
from kritidocx.xml_factory.xml_builder import XmlBuilder

class ColumnManager:
    """
    Advanced Layout Controller for Page Columns.
    """

    # Default gap between columns (0.5 inch is standard academic/legal)
    DEFAULT_SPACING_INCH = 0.5

    @staticmethod
    def apply_columns(section, num_columns=1, spacing=None, separator=False):
        """
        Master method to configure columns on a section.
        
        Args:
            section: Target python-docx Section object.
            num_columns (int): 1, 2, 3... (Max usually 4-5 depending on width).
            spacing (str/int): Gap '0.5in', '20px'. Default ~720 twips.
            separator (bool): Draw vertical line between columns.
        """
        # 1. Validation & normalization
        if not num_columns or int(num_columns) < 1:
            num = 1
        else:
            num = int(num_columns)

        # 2. Calculate Spacing (Gap)
        # 1 column has 0 spacing technically, but we keep default variable clean
        space_twips = 0
        if num > 1:
            if spacing:
                space_twips = UnitConverter.to_twips(spacing)
            else:
                # Default 0.5 inch (720 twips)
                space_twips = int(ColumnManager.DEFAULT_SPACING_INCH * DocConstants.TWIPS_PER_INCH)

        # 3. Apply via XML Factory
        XmlBuilder.set_section_columns(section, num, space_twips)
        
        # 4. Apply Separator (Visual Line) - Special Logic
        # (Using a separate XML manipulator if separator logic isn't fully inside builder or just needs attribute update)
        if separator:
            # We access the section element we just updated
            # FIX: Use curly braces for namespace definition {url}tagname
            cols = section._sectPr.find(f"{{{DocConstants.NS['w']}}}cols")
            
            # Assuming set_section_columns created the tag
            if cols is not None:
                # Direct injection for separator logic
                XmlBuilder.create_attribute(cols, 'w:sep', '1')
    # =========================================================================
    # 📐 WIDTH CALCULATOR (The "Physics" Helper)
    # =========================================================================
    # यह सबसे महत्वपूर्ण फंक्शन है। यह बताता है कि एक कॉलम के अंदर
    # लिखने के लिए वास्तव में कितनी जगह बची है।
    
    @staticmethod
    def get_column_content_width(section):
        """
        Calculates the writable width of a single column in Twips.
        Formula: (PageWidth - Margins - TotalGapSpace) / NumCols
        
        Returns:
            int (Twips)
        """
        try:
            sectPr = section._sectPr
            
            # 1. Get Page Width & Margins
            # (Requires getting properties manually or via python-docx object if loaded)
            page_w = section.page_width
            left_mar = section.left_margin or 0
            right_mar = section.right_margin or 0
            gutter = section.gutter or 0
            
            # Available Space on Page
            total_printable = page_w - left_mar - right_mar - gutter
            
            # 2. Get Column Config from XML
            # Default values if no XML tag exists
            num_cols = 1
            col_space = 0
            
            # Using Namespace to find w:cols
            # FIX: Construct {http://...}cols syntax
            cols_tag = sectPr.find(f"{{{DocConstants.NS['w']}}}cols")
            
            if cols_tag is not None:
                # Parse num
                # FIX: Construct {http://...}num syntax for attributes too
                num_attr = cols_tag.get(f"{{{DocConstants.NS['w']}}}num")
                if num_attr: num_cols = int(num_attr)
                
                # Parse space
                space_attr = cols_tag.get(f"{{{DocConstants.NS['w']}}}space")
                if space_attr: col_space = int(space_attr)

            if num_cols <= 1:
                return total_printable

            # 3. Calculate Gap Loss
            # Gaps exist between columns. (N cols = N-1 gaps)
            total_gap_loss = (num_cols - 1) * col_space
            
            # 4. Final Width per Column
            column_width = (total_printable - total_gap_loss) / num_cols
            
            return int(column_width)

        except Exception as e:
            # Safe Fallback to a generally safe width (approx 3 inches for columns)
            # Or 6.5 inch for full page.
            return 4320 # ~3 inches