# ▦ Tables & The Matrix Engine

HTML tables are flexible and liquid (`<td>` cells push others dynamically). MS Word tables, however, are strictly geometric grid objects. Trying to force fluid HTML directly into rigid XML is why 90% of open-source Word converters produce broken, bleeding, and crashed table outputs.

KritiDocX handles this by inserting a **Calculated Matrix Engine** strictly before the render begins. 

---

## 🧮 How The 2D Matrix Engine Works

Before any Word element is generated, our internal algorithm analyzes your entire HTML table (across `<head>`, `<body>`, `<tfoot>`) and builds an explicit `[Rows] x [Cols]` mathematical map.

It fires **"Ray Tracing" Algorithms** (Logical Plotting):
1. **Ahead Scans:** If a cell uses `rowspan="3"`, it plots mathematical ghosts in the columns exactly underneath. 
2. **Width Guarantees:** Ensures your matrix does not collapse vertically. When scanning physical child row data over matrix dimensions, it safely extends trailing missing `pad_blocks`.
3. **Translates `w:gridSpan`:** Handles Colspans natively parsing across your X dimensions so borders perfectly seal above trailing data structures.

!!! success "Complex Structures Enabled"
    You can safely paste heavy Corporate KPI Grids that use deep arrays of nested `Rowspans` inside `<tr class="flex_mode_data">`—our resolver maps it directly onto proper standard Grid Arrays with perfect internal cell boundary retention. No `NotImplemented` or overlapping boundary crash codes!

---

## 🚀 Resolving The "Zebra Styling" & Border Conflicts

In web browsers, CSS logic works like this: "If the row is green and the cell has a red line, figure it out." In Word, conflicting Cell `<w:tcBorders>` and Table Grid (`w:tblPr`) definitions corrupt document render behaviors natively resulting in fat bold lines (Border Collision).

**The KritiDocX Conflict Resolver Algorithm ensures logic stability:**
If user demands specific inline CSS boundaries onto target matrices, The Render Layer executes **Style Deflection (Target Safe Suppression):**

```html
<!-- Table Background Inheritance Handled! -->
<table style="width: 100%; border: 1px solid black;">
    <!-- Head retains specialized 'Corporate Design Theme Base Colors' unless forced inline -->
    <tr>
        <th>Primary Key</th>
        <th style="border-right: 5px double red;">Overwritten Custom Logic</th>
    </tr>
    <!-- Zebra Color inheritances process successfully into the Matrix XML cell-shading parameters directly -->
    <tr style="background-color: #f1f1f1">
        <td rowspan="2" style="background-color: yellow">Spanned Inheritance Retained!</td>
        <td>Flows Grey seamlessly!</td>
    </tr>
    <tr>
         <!-- Ghost Row safely carries Yellow Background without text injection bugs! -->
         <td>Grey Data Flow...</td>
    </tr>
</table>
```
KritiDocX isolates Fallback properties away from active `<w:tcPr>`. A cell explicitly receiving CSS `.borders` intercepts and blocks "Grid Double Scaling".

---

## 📐 AutoFit & Dynamic Constraints (ColGroups)

Word usually snaps wide columns aggressively causing overlapping blocks in Mobile outputs. The Native **Width & Calculation Parser**:

### 1. Safeties over Padding Bounds (`Twips/1440Inch`)
```css
/* KritidocX recalculates absolute percentage bounds handling left/right Indents actively 
to avoid text bleeding across raw XML Document Right Margins! */
margin-left: 20px; width: 100%; /* It recalculates Page Limits to ~95% dynamically safely */
```

### 2. Column Controls 
Include classic `<colgroup>` structure logic? Our Engine supports precise forced Fixed grid limits over traditional autofit models.
```html
<!-- Creates explicitly managed width scaling bypassing general table calculations -->
<colgroup>
    <col span="1" style="width: 15%;">
    <col span="1" style="width: 85%;">
</colgroup>
```
If fixed width columns define exactly `< 100%`, **KritiDocX hybrid processing** allocates a specific Auto distribution function resolving all trailing values seamlessly within page size properties.

---

## ⚖️ Cell Layout Specifics & Directionals 

Table cells possess an insane amount of layout settings beyond typography natively supported here:

*   **Paddings/Mar:** Standard conversions convert raw `margin` strings mapped dynamically. (Default `Rotated cells = Center alignment force parameters` mapped inside engine physics constraints automatically).
*   **Rotation Arrays (tb-Rl):** 
```html
<td style="writing-mode: vertical-rl;">This spins perfectly 90 degrees native.</td>
```
*   **Flex-box Split Simulator (`justify-content`):** KritiDocX intercepts top level Flex wrappers around headers transforming complex alignment into discrete matrix mapping.

Next, see the pinnacle of what an Advanced Transformer is by stepping outside general visual HTML constraints, diving directly into native formula capabilities inside the **[Scientific Core ➔](scientific-math.md)**.