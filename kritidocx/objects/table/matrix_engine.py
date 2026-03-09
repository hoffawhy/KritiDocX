"""
MATRIX ENGINE MODULE (The Table Mathematician)
----------------------------------------------
Responsibility:
Converts a messy HTML table structure into a strict 2D Matrix (Grid).
Handles the complex logic of Rowspans, Colspans, and Cell collisions.

Why is this needed?
- HTML tables are 'flow-based' (cells pushed to next available spot).
- Word tables are 'grid-based' (N Rows x M Cols).
- This module bridges that gap by calculating exact X/Y coordinates for every cell.

Algorithm:
1. "Ray-Tracing" for spans: Looks ahead to mark future cells as occupied.
2. Dynamic Resize: Expands grid if row contents exceed initial width estimate.
3. Padding: Fills missing cells to ensure rectangular geometry.
"""

class MatrixEngine:
    """
    Core calculation logic for Table layouts.
    State-less processing (pure inputs -> pure outputs).
    """

    @staticmethod
    def normalize_structure(table_node):
        """
        [UPDATED LOGIC] Analyzes HTML <table> and returns a solved 2D Matrix.
        Fixes: Rowspan/Colspan collisions and Dynamic Width Expansion.
        """
        # 1. Flatten HTML (Merge thead, tbody, tfoot into linear rows)
        rows_list = MatrixEngine._extract_linear_rows(table_node)
        total_rows = len(rows_list)
        
        if total_rows == 0:
            return [], 0

        # 2. Initial Width Guess (Maximum cells in a single tr)
        max_cols = 0
        for r in rows_list:
            cells = r.find_all(['td', 'th'], recursive=False)
            current_w = 0
            for c in cells:
                # Parse colspan safely
                try:
                    span_val = c.get('colspan', '1').strip()
                    colspan = int(span_val) if span_val.isdigit() else 1
                except ValueError: 
                    colspan = 1
                current_w += colspan
            max_cols = max(max_cols, current_w)
            
        if max_cols == 0: max_cols = 1 # Minimum safety

        # 3. Initialize Empty 2D Matrix
        # [Rows][Cols] = None
        matrix = [[None for _ in range(max_cols)] for _ in range(total_rows)]

        # 4. The Solver Loop (MyDocX_Engine Logic)
        for r_idx, row in enumerate(rows_list):
            html_cells = row.find_all(['td', 'th'], recursive=False)
            
            c_idx = 0        # Matrix Pointer (Logical Column)
            html_ptr = 0     # HTML List Pointer (Physical Tag)
            
            # Continue until we run out of HTML cells OR we fill the row
            while html_ptr < len(html_cells) or c_idx < max_cols:
                
                # --- A. DYNAMIC EXPANSION (Critical Fix) ---
                # अगर वर्तमान कॉलम मैट्रिक्स की सीमा पार कर रहा है, तो मैट्रिक्स को बड़ा करें
                if c_idx >= max_cols:
                    new_width = c_idx + 1
                    expand_by = new_width - max_cols
                    for r in matrix:
                        r.extend([None] * expand_by)
                    max_cols = new_width

                # --- B. COLLISION DETECTION ---
                # चेक करें कि क्या ऊपर से कोई Rowspan आ रहा है?
                if matrix[r_idx][c_idx] is not None:
                    # Slot taken by a previous vertical merge. Skip it.
                    c_idx += 1
                    continue

                # --- C. PROCESS REAL CELL ---
                if html_ptr < len(html_cells):
                    cell = html_cells[html_ptr]
                    
                    # Parse Attributes
                    try:
                        rs_raw = cell.get('rowspan', '1').strip()
                        cs_raw = cell.get('colspan', '1').strip()
                        rs = int(rs_raw) if rs_raw.isdigit() else 1
                        cs = int(cs_raw) if cs_raw.isdigit() else 1
                    except:
                        rs, cs = 1, 1
                    
                    # Clamp: Logic ensures we don't merge beyond document length
                    rs = min(rs, total_rows - r_idx)
                    
                    cell_data = {
                        'type': 'real',
                        'tag': cell,
                        'rowspan': rs,
                        'colspan': cs,
                        'v_merge': 'restart' if rs > 1 else None, 
                        'grid_span': cs if cs > 1 else None
                    }
                    
                    # Check expansion again for Wide Colspan
                    required_width = c_idx + cs
                    if required_width > max_cols:
                        expand_by = required_width - max_cols
                        for r in matrix:
                            r.extend([None] * expand_by)
                        max_cols = required_width

                    # --- D. MARK THE GRID (Ray Tracing) ---
                    # Loop covers the area this cell occupies [Rows x Cols]
                    for r_offset in range(rs):
                        for c_offset in range(cs):
                            target_r = r_idx + r_offset
                            target_c = c_idx + c_offset
                            
                            # Boundary Safety
                            if target_r < total_rows:
                                if r_offset == 0 and c_offset == 0:
                                    # The Head (Actual content)
                                    matrix[target_r][target_c] = cell_data
                                else:
                                    # The Ghost (Placeholders)
                                    matrix[target_r][target_c] = {
                                        'type': 'merged_placeholder',
                                        'master': cell_data, # Reference to parent
                                        'v_merge': 'continue' if r_offset > 0 else None,
                                        'is_h_merged': (c_offset > 0) # Used to skip rendering
                                    }
                    
                    # Move Pointers
                    html_ptr += 1
                    c_idx += cs
                    
                else:
                    # E. Fill Gaps (Pad cells for rectangularity)
                    # If HTML row is shorter than table width, fill with empty cells
                    matrix[r_idx][c_idx] = {'type': 'pad', 'tag': None}
                    c_idx += 1

        return matrix, max_cols
    
    
    @staticmethod
    def _extract_linear_rows(table_node):
        """
        Unpacks rows from table ensuring Order: THEAD -> TBODY/TR -> TFOOT.
        [FIXED]: Now scans TFOOT even if direct TRs exist.
        """
        all_rows = []
        
        # 1. THEAD (हमेशा सबसे ऊपर)
        thead = table_node.find('thead', recursive=False)
        if thead:
            all_rows.extend(thead.find_all('tr', recursive=False))
            
        # 2. BODY CONTENT (TBODY + Direct TRs)
        # कभी-कभी HTML मिक्स्ड होता है (कुछ रो Tbody में, कुछ बाहर)
        # हम दोनों को जोड़ेंगे।
        
        # A. Explicit TBODY tags
        tbodys = table_node.find_all('tbody', recursive=False)
        for tb in tbodys:
            all_rows.extend(tb.find_all('tr', recursive=False))
            
        # B. Direct TR Children (Implicit Body)
        # जो सीधे <table> के अंदर हैं (बिना किसी thead/tbody/tfoot के)
        direct_rows = table_node.find_all('tr', recursive=False)
        if direct_rows:
            all_rows.extend(direct_rows)

        # 3. TFOOT (हमेशा सबसे नीचे)
        # [CRITICAL FIX]: यह हिस्सा अब हमेशा चलेगा, स्किप नहीं होगा।
        tfoot = table_node.find('tfoot', recursive=False)
        if tfoot:
            all_rows.extend(tfoot.find_all('tr', recursive=False))
            
        return all_rows