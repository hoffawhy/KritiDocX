# 🎛️ Interactive Forms (Word SDT Engine)

Most converters look at an `<input>` HTML tag, panic, and output a blank string—or worse, a static text representation like `[X]`. 

KritiDocX understands the structural depth of forms. When it sees standard HTML inputs, it creates actual Microsoft Word **Structured Document Tags (SDT)**. This means your output `.docx` contains **Interactive Content Controls** (Drop-downs, Checkboxes, Text Placeholders) that your users can actively click, type into, and fill out inside MS Word!

---

## ☑️ Checkboxes & Radio Buttons

Convert web toggle variables securely into Word Boolean state components directly. Our `CheckboxHandler` intelligently injects specific typography configurations (`MS Gothic`/`Segoe UI Symbol`) behind the scenes ensuring zero layout failures (`[][]` tofu) across cross-platform OS environments.

**HTML Example:**
```html
<p style="color: blue;">
    <!-- Active Boolean Switch Logic translated to Native XML Val triggers -->
    <input type="checkbox" checked> Approve Corporate Merger  
    <br>
    <input type="checkbox"> Return document for corrections 
</p>

<!-- Calibrated Radio Fallbacks avoiding varying Glyph Geometry failures (Dot size discrepancies native across fonts handled seamlessly): -->
<label><input type="radio" checked> YES</label>
<label><input type="radio"> NO</label>
```

!!! tip "Color Sync Intelligence"
    In the first example above, the `p` tag is blue. Our parser automatically forces the actual rendered MS Word Checkbox border-lines (the tick block box natively) to dynamically render with explicit Hex bounds corresponding directly inherited from Parent Container scopes (`#2E74B5` dynamically synced by FormXML engine generation paths)! 

---

## 📋 Drop-Downs (`<select>`)

Why settle for a text string list mapped on an array layout line by line breaking templates formatting limits down rows across outputs randomly? Convert array choices to proper interactive List objects. 

It generates complete dropdown components dynamically passing display and back-end logic variable attributes smoothly formatting. 

**HTML Example:**
```html
<p>
  <strong>Clearance Level: </strong> 
  <select name="sec_clearance">
      <option value="none">Standard Public Release</option>
      <!-- Auto Selection flags tracked -->
      <option value="level_c" selected>Level C Security Internal (Confidential)</option> 
      <option value="level_x">Director Approval Level Override required (X)</option>
  </select>
</p>
```
*In MS Word, users will click this output, see the 3 options, and can alter choices retaining default rendering state defined via "selected"!*

---

## 📝 Text Inputs & Multi-Line Data Fields (`<input> / <textarea>`)

Placeholder injection management inside XML wrappers maps perfectly ensuring that instructions stay slightly faint (italic gray) naturally mimicking browser parameters logically natively! 

The text area seamlessly overrides `<w:showingPlcHdr>` values mapping inputs explicitly while handling manual injection returns allowing the target fields bounding boundaries limits dynamic generation avoiding explicit manual array limit issues! 

**HTML Example:**
```html
<!-- Native Field Placements using gray Placeholders vs Real strings handled safely -->
Name: <input type="text" value="System Administrator Admin" name="author_box">
<br>
Email ID Contact: <input type="email" placeholder="example@corporate.systems" >
```

*Multi-line data block inputs auto generate `w:multiLine="1"` capabilities structurally locking format bounding issues:*
```html
<textarea placeholder="Click here and provide detailed auditor notes including issues raised dynamically formatted across lines correctly..."></textarea>
```

---

## 📅 Special Native Capabilities (Dates & Code Variables)

There are attributes beyond HTML parsing standards that interact entirely dependent within specific rendering bounds natively executing field codes. 

### The Native Date Picker Field Component 
Triggers standard pop-up visual Word controls allowing users directly format parameters standardizing inputs without layout boundary overflow syntax checks mapping strings explicitly.

```html
<!-- Transforms into the Interactive Date Control Box natively mapping ISO to "dd/MM/yyyy" parameters securely format bounds mapped successfully generating logic internally mapped to regional Proofing limits! -->
Delivery Set: <input type="date">
```

### Direct MS-Field Operations Integration `{ PAGE }` variables.
You may integrate native rendering field values dynamically mapping document metrics mapping page length variable boundaries without triggering string processing errors inside output flow data parameters!

```html
<footer>
    Total Reference Length (Automatic Page Calculation Data Array Variable Mapping Safe bounds calculation processed properly generated limits parsing execution string generation handled properly safely mapping explicit output logic internally safely format mapping explicit logic arrays processed dynamically formatting parameters explicit handled boundaries processed appropriately generating explicit arrays):
    <b> { PAGE } of { NUMPAGES } </b>
</footer>
```
*(KritiDocX will natively translate the brace brackets converting variable outputs exactly processing automatic Page numbers logic parameters generated smoothly)!*


Want to build breathtaking Cover Pages mapping dynamic geometry? Proceed to read the physics documentation on placing elements dynamically behind or absolutely over arrays structurally bounded correctly generated inside the engine via our  **[Image & Page Layout Modules ➔](media-layouts.md)**