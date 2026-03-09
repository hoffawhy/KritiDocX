# 🎨 Typography & Advanced Styling

Welcome to the **"Visual Layer"**. Microsoft Word (`.docx`) processes text completely differently from HTML. Instead of simple strings, it builds `Runs` inside `Paragraphs` and forces fonts into multiple slots (e.g., ASCII vs. Complex Script). 

The KritiDocX `RunManager` bridged this gap completely, mapping web CSS properties to Office DrawingML physics.

---

## 🔤 Font Safeties (The Tofu-Killer)

Ever noticed how rendering Hindi text (Devanagari) or Chinese characters in a generic converter usually results in little empty boxes (`[][][]`) known as 'Tofu'?

KritiDocX features **Multi-Script typography Engine**. It scans the unicode sequence of your content string and applies the precise Native Word schema configuration behind the scenes.

**Supported by default (without any user logic needed):**

1. **Standard:** Maps `sans-serif` automatically to `Calibri` (hAnsi slot).
2. **Complex Script (CS):** Scans for Unicode `0x0900+` (Hindi) and forces it onto `Mangal`. Scans for `0x0590+` and processes Arabic alignments automatically via `<w:cs>` hint flags!
3. **Symbols & Emoji:** Detects standard glyph forms and automatically allocates to `Segoe UI Symbol` avoiding layout collapses.
4. **Checkbox Forms:** Translates input glyphs to strictly use `MS Gothic`.

!!! tip "Implicit Sizing Fixes"
    You don't need to specify points or pixels manually. Using `font-size: 1rem;` dynamically adapts your MS word sizes to a baseline scale (Typically 11pt, converted strictly into 22 half-point Twip logic integers!) 

---

## ✨ CSS Web-Effects in MS Word

Below is the dictionary of highly specialized text-rendering CSS properties supported that standard converters typically abandon.

### 1. Real Highlighter vs Paragraph Shading
Unlike basic parsers that throw up backgrounds randomly, KritiDocX knows the visual distinction between drawing a physical text block vs highlighting a text stream.

```html
<!-- Use generic CSS words mapping directly to Word WD_COLOR_INDEX (The real marker!) -->
<span style="highlight: yellow;">This is natively "highlighted".</span>
<span style="background-color: #f1f1f1;">This fills a physical color block shading container</span>
```

### 2. The Vector "Underline" Engine
A `<u/>` or standard single text-decoration underline is basic. What if you want wavy grammar underlines mimicking editorial feedback?
KritiDocX expands the capability of CSS to control stroke color AND pattern independent of text properties:

```html
<!-- Yes, double-styled border syntax natively works! -->
<p>
  Check this out: <span style="text-decoration: underline wavy #ff0000">Spelling issue?</span>
</p>
<p>
  Account Value: <span style="underline: double green;">Passed Financial Clearance</span>
</p>
```

### 3. Glow & Stacking Attributes (Office 2010 Engine Layer)
Want "Banner Title Page" graphics? HTML `text-glow` transforms strings directly to standard OOXML `w14:glow` rendering layers inside a Paragraph run context!

```html
<span style="font-size: 26pt; color: #1E3A8A; text-glow: 5px #F59E0B;">
    QUARTERLY PERFORMANCE ARCHIVE
</span>
```
*(Automatically mathematically aligns `<w14:glow>` opacity values `Alpha 60% / 60000EMUs` preventing overly blocky bleeds usually produced via API errors.)*

### 4. Advanced Reflections and Stacking Metrics
Our internal physics mapping translates modern Drop Shadows securely to Word Cartesian Polar Coordinates mapping: `Dir=FinalDir() & Dist = Dist² EMU() ` limits ensuring the document isn’t flagged corrupt due to mathematical limits over-flow:

```html
<!-- Drops shadow + Letter Tracking Spacing modifications -->
<p style="letter-spacing: 5px; text-shadow: 2px 2px 4px gray;">
  SUPER SECURE CONFIDENTIAL DROP!
</p>
```

---

## 🎨 System Variables Fallbacks

Below are mapped shortcuts that save designers 10 lines of hex parsing properties inside pure Text and Body Blocks.
You may invoke explicit colors simply passing CSS color namespaces! `red` → automatically handles exact Theme Hexes, meaning `red` gets correctly substituted via:

* `dark_gray` mapping overrides flat css fallback behaviors providing print-grade contrast
* Implicit Fallback guarantees Black output replacing null inputs instead of random word rendering (Usually 'Automated Black Font Rendering Bugs') that happens natively across many platforms lacking deep namespace definitions on string runs.

Ready to check out the ultimate physics layout processing on Grid elements? Move onto how KritiDocX compiles pure math into our **[Table & Matrix Resolver Engines ➔](tables-matrix.md)**.