# 🚀 Welcome to KritiDocX

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()
[![Built With](https://img.shields.io/badge/Built%20With-Google%20AI%20Studio-orange.svg)](https://aistudio.google.com/)

**KritiDocX** is a revolutionary, industrial-grade **Document Compiler**. It takes standard HTML, complex CSS, and pure Markdown, and completely rebuilds them into high-fidelity, native Microsoft Word (`.docx`) files.

Stop relying on tools that just "paste text" onto a blank canvas. KritiDocX understands Word's internal geometry and builds a perfect document, pixel by pixel, object by object.

---

!!! info "✨ The Zero-Code Miracle: Built in 30 Days"
    This engine has an inspiring origin story. It was conceptually architected, debugged, and deployed by a creator from a **non-coding background** entirely through collaboration with **Google AI Studio**. Every Matrix engine, every XML Factory, and every rendering logic is proof of what human vision combined with advanced AI can build.

---

## 🌟 Why Choose KritiDocX?

Most HTML-to-Word converters fail at three things: Complex Tables (`colspan`/`rowspan`), Advanced Math, and overlapping CSS margins. KritiDocX solves them all.

### 🧩 1. The 2D Matrix Engine (Flawless Tables)
We don't just dump HTML tags into Word. Our engine plots your HTML table on a virtual 2D Matrix before rendering. This means nested rows, colspans, overlapping grid-borders, and auto-fitting column widths render *flawlessly*—just like they do in the browser.

### 📐 2. The "Hybrid" Injection System
Keep your Design and Data separate. 
You can use a beautifully styled **HTML file** as a Template (e.g., your Company Letterhead) and inject raw **Markdown files** containing data straight into a target container (like `<main>`). KritiDocX handles the inheritance seamlessly.

### 🧮 3. Scientific-Grade OMML Math
KritiDocX is a researcher's best friend. Type pure LaTeX like `$$ E = mc^2 $$`. Instead of generating a blurry image, the engine uses XSLT to convert it into **Native Word Editable Equations** (Office Math Markup Language). It even features intelligent scalable fencing for large Matrices.

### 🎛️ 4. Native Word Forms (SDT)
Are you building dynamic forms? Converting an `<input type="checkbox" checked>` won't just output a static symbol. KritiDocX creates **Interactive Structured Document Tags**. Your checkboxes will be clickable, and your drop-downs will work *inside* MS Word.

### 🎨 5. Print-Ready Typographics & Visuals
*   **Fonts & Scripts:** Intelligent language processing handles English alongside Hindi (`Mangal`), complex symbols, and Asian layouts without getting "Boxed-Tofu" (`[]`) characters.
*   **Box Model & Effects:** Absolute positioning, Text Shadows, Z-Index stacking, Glowing borders, and CSS rotations translated strictly to DrawingML limits.

---

## ⚡ A Taste of the API

It is powered by a powerful Facade pattern. The entire complexity of the Engine is hidden behind **one single, elegant function call**.

```python
from kritidocx import convert_document

# Generating a masterpiece in 1 step:
success = convert_document(
    input_file="templates/report_layout.html", 
    data_source="data/q1_metrics.md",          
    output_file="out/Corporate_Q1_Report.docx"
)

if success:
    print("Document successfully generated!")
```

---

## 🧭 Where to go next?

Ready to start building beautiful reports? Jump into the guides:

*   **[⚙️ Installation & Getting Started](getting-started.md)**: Setup your environment in 2 minutes.
*   **[🧬 The Hybrid Mode](hybrid-mode.md)**: Learn how to inject Markdown into HTML templates.
*   **[📊 Mastering Tables](tables-matrix.md)**: Understand the power of our Grid engine.
*   **[🧪 Developer Lab / API](configuration-api.md)**: Explore the settings and deep debugging modes.

---
*Created with ❤️ by the KritiDocX Team & Google AI Studio.*
