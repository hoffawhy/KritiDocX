# 🧬 The Hybrid Injection Mode

Welcome to the **"Killer Feature"** of the KritiDocX Engine.

In standard workflows, formatting reports dynamically is a nightmare. Do you write Python code to loop over styles? Do you try to merge complex data structures directly inside raw MS Word XML templates? Both approaches are extremely slow and fragile.

**The Hybrid Mode** introduces a "Separation of Concerns":
1. **Design Layer (`.html`):** The beautiful company letterhead, borders, global typography, headers, and footers.
2. **Data Layer (`.md`):** The raw reports, tables, calculations, and mathematical data pulled from your Database or API.

KritiDocX intelligently *injects* the Data Layer straight into the Design Layer while perfectly honoring CSS inheritance boundaries.

---

## 🛠️ How It Works (The Blueprint)

### Step 1: The Design (HTML Layout)
Create an HTML file that contains your company’s aesthetic layout. **Crucially, give an `id="content"` to the div where you want your text to flow.**

```html title="corporate_layout.html"
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Calibri'; color: #333; }
        
        /* Awesome Flexible Header */
        header {
            display: flex;
            justify-content: space-between;
            background-color: #1F2937;
            color: #F59E0B;
            padding: 15px;
            margin-bottom: 20px;
        }

        /* Beautiful styling that the Markdown Data will inherit! */
        #content h2 { 
            color: #2E74B5; 
            border-bottom: 2px dashed #BFBFBF; 
        }
        #content table {
            width: 100%; border: 1px solid black; 
        }
        #content th { background-color: #4472C4; color: white; }
    </style>
</head>
<body>

    <!-- Structure -> The Flexbox Grid Logic Engine handles this perfectly -->
    <header>
        <div>ACME Analytics Division</div>
        <div>Report Status: VERIFIED</div>
    </header>

    <!-- The Target Injection Pocket 🎯 -->
    <main id="content">
        <!-- ALL DYNAMIC DATA WILL MAGICALLY APPEAR HERE -->
    </main>

    <!-- Global Page Footers also work here! -->
</body>
</html>
```

### Step 2: The Data (Markdown Payload)
Generate your data however you want (from a Database, an AI Model, or an API string) and save it as standard Markdown.

```markdown title="q1_sales.md"
## Quarter 1 Growth Metrics

The server metrics are operating well within our projected SLA logic gates:

| Parameter     | Region | Metric (%) |
| ------------- | :----: | ---------: |
| Latency Ratio | EU-West| 99.8 %     |
| Packet Loss   | Asia   | 0.05 %     |

As Einstein noted:
$$ E=mc^2 $$

> *Notice: Proceed with kernel patching on Asia server nodes by tomorrow.*
```

### Step 3: The Engine Call (Magic Time)
Instead of feeding just one file, you provide **both parameters** to the engine via `convert_document()`.

```python title="hybrid_runner.py"
from kritidocx import convert_document

success = convert_document(
    input_file="corporate_layout.html", # Pass the Layout here
    data_source="q1_sales.md",          # Pass the Markdown payload here!
    output_file="Auto_Generated_Report.docx"
)

if success:
    print("Report compiled. The payload was injected flawlessly.")
```

---

## 🎯 Smart Injection Targeting Logic

You don't *strictly* have to use `<div id="content">`. KritiDocX's parser has a **Fall-down Semantic Scanner**. When running in Hybrid Mode, the engine searches your HTML layout in this exact order to find where to put the Markdown data:

1. **`id="content"`:** (Top Priority) The absolute standard for safety.
2. **`<main>`:** Uses standard HTML5 semantic elements if the ID is missing.
3. **`class="content"` or `class="container"`:** Scans standard CSS-defined bodies.
4. **End of `<body>`:** (Ultimate Fallback). If you supply a completely flat HTML document with no structure, it safely appends the markdown right at the end of the body to prevent breaking CSS headers.

!!! tip "Inheritance Power (Context Sync)"
    The Hybrid Injection doesn't just "concatenate text files together." It executes full DOM rendering.
    If you set your `<main>` div's font to `"Arial"` in the HTML Template CSS, all the raw markdown that gets pushed inside will automatically inherit that font-family within the resulting Word XML Document. 
    
    **It calculates style specificity precisely as Google Chrome would!**

---

Now that you can orchestrate Design and Content separately, explore how KritiDocX transforms one of the most frustrating aspects of automation—drawing perfect lines in Word via our **[Advanced Tables & Matrix Engine ➔](tables-matrix.md)**.