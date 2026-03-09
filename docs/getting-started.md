# ⚙️ Getting Started

In this guide, you will learn how to install **KritiDocX**, set up your environment, and write your very first script to generate a beautifully styled Microsoft Word Document.

---

## 🛠️ 1. Installation

KritiDocX requires **Python 3.8 or higher**. We highly recommend using a Virtual Environment.

*(Currently, you can install the library locally or from source. The PyPI `pip install kritidocx` command will be available soon.)*

### Install from Requirements
If you have cloned the repository, simply navigate to the project folder and run:

```bash
pip install -r requirements.txt
```

!!! success "Library Core Dependencies"
    The engine relies on battle-tested libraries like `python-docx` for low-level XML wrapping, `beautifulsoup4` and `lxml` for deep DOM parsing, `Pillow` for smart image analysis, and `latex2mathml` for formula preprocessing.

---

## 🚀 2. Your First Document (Simple Mode)

Let's convert a basic HTML string into a Word file. 
Create a file named `generate.py` in your working directory and paste the following code:

```python title="generate.py"
import os
from kritidocx import convert_document

# 1. Create a simple dummy HTML file with Inline CSS
html_content = """
<!DOCTYPE html>
<html>
<body>
    <h1 style="color: #2E74B5; border-bottom: 2px solid orange;">
        Welcome to KritiDocX
    </h1>
    <p>
        This text demonstrates how <b>inline tags</b> and 
        <span style="background-color: yellow;">highlighted spans</span> 
        are translated into <i>Native Word Runs</i> perfectly.
    </p>
</body>
</html>
"""

with open("my_test.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# 2. Run the Engine!
print("Starting Engine...")

success = convert_document(
    input_file="my_test.html",
    output_file="My_First_Output.docx"
)

if success:
    print("✅ Success! Open 'My_First_Output.docx' to see the magic.")
else:
    print("❌ Failed. Check the terminal logs.")
```

**Run the script:**
```bash
python generate.py
```

Open the newly generated `.docx` file, and you will notice that the header color and the yellow highlight are exactly how they would look in a web browser!

---

## 📝 3. Converting Markdown

Prefer writing in Markdown? KritiDocX has a highly capable Markdown pre-processor. It protects your Math formulas and Tables while parsing standard markdown syntax into HTML.

```python title="md_convert.py"
from kritidocx import convert_document

# Note: You only need to pass a .md file. 
# The engine auto-detects the extension and switches the parsing logic.

convert_document(
    input_file="science_paper.md", 
    output_file="Science_Paper.docx"
)
```

!!! tip "Image Paths in HTML/Markdown"
    You can use absolute paths (`C:/images/logo.png`), relative paths (`logo.png`), or Web URLs (`https://example.com/logo.png`) in your source files. KritiDocX's `ImageLoader` will handle the network and caching automatically without crashing the process.

---

## 🛑 4. Safe Error Handling

Because KritiDocX is designed for **production enterprise environments**, it is programmed never to use aggressive `sys.exit()` calls that kill your backend server.

Instead, if a major failure occurs, it raises standard Python Exceptions that you can catch gracefully.

```python title="safe_execution.py"
from kritidocx import convert_document
from kritidocx.exceptions import KritiDocXError, InputNotFoundError

try:
    convert_document("does_not_exist.html", "out.docx")

except InputNotFoundError as e:
    # Captures file missing errors specifically
    print(f"File missing: {e}")

except KritiDocXError as e:
    # Catches all other library-specific failures 
    # (e.g., Template structural logic failures)
    print(f"KritiDocX Internal Failure: {e}")
```

---

## 🎯 Next Steps

Now that you have successfully generated a basic document, it's time to unlock the real power of the Engine. 

Learn how to merge design layouts with dynamic data seamlessly in our most powerful feature: **[The Hybrid Injection System ➔](hybrid-mode.md)**.