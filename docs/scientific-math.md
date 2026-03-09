# 🧮 Scientific Math & OMML Engine

Most text-converters process Mathematical Formulas by sending equations to web servers, turning them into PNG Images, and pasting them back onto the Word file. 

This causes: **A)** Blur / Loss of Quality, **B)** Increased File Weight, and **C)** Lack of ability for anyone to open the Document later to "edit the `2` into a `3`."

KritiDocX avoids images entirely by incorporating a fully native **Latex -> MathML -> OMML** compilation flow based on internal Microsoft Schema transformations using core Extensible Stylesheet Definitions.

---

## ⚡ Inserting Equations: Dual Architecture Supported 

KritiDocX gracefully listens for both conventional HTML web markers or straight text syntax flows natively mapping data. 

### 1. LaTeX String Definitions 
Type exact physics and formula parameters using standard Block or Inline symbols defined by the community across data flows natively mapped!

*   **Block Output (`$$`):** Wraps Math variables, centering strings safely across new paragraph limits structurally generating proper `<m:oMath>` alignments correctly parsing document variables.
*   **Inline (`$`):** Drops the formulas properly side by side within actual text bounds processing normal sentence flows without document line break failures!

```markdown
We calculate option pricing standard vectors: 

$$ C(S, t) = N(d_1)S - N(d_2)Ke^{-r(T-t)} $$

If $X < 4$, calculations require structural modification to align the limit of variance securely:
$$ A = \frac{X+2}{\sigma^2} $$
```

### 2. MathML Block Wrappers (`<math>`)
Exporting natively formatted reports directly from libraries retaining native semantic outputs processes without issue utilizing `<math xmlns="...">` HTML structures securely!

```html
<p>
  Einstein Formula Generated Semantic Engine Direct:
  <math display="block"><mrow><mi>E</mi><mo>=</mo><mi>m</mi><msup><mi>c</mi><mn>2</mn></mn></msup></mrow></math>
</p>
```

---

## 🛡️ Matrix Sanitation (Fencing The Fringes) 

Raw mathematical parameters compiled inside Office Engines naturally struggle resizing "hard borders" generated during arrays parsing causing lines bounding Matrix Data to crash graphically locking parameters tightly cutting digits randomly in Word instances dynamically! 

Our Pre-Sanitizer parses core bounds detecting specific structures mapping custom boundaries into true `OMML Delimiter Brackets` scaling visually around numbers dynamically without layout corruption bounds failing! 

Supported dynamically expanding brackets native over LaTeX mappings replacing flat outputs:
- **Parentheses Matrices:** `\begin{pmatrix}`
- **Bracket Matrices:** `\begin{bmatrix}`
- **Curly Arrays:** `\begin{Bmatrix}`
- **Vector Columns:** `\begin{vmatrix}`

```markdown
$$
A = \begin{bmatrix}
   \alpha & \beta & \gamma \\
   1 & 0 & 0 \\
   0 & 1 & 0 
\end{bmatrix} \times \begin{pmatrix} x \\ y \\ z \end{pmatrix}
$$
```

*(KritiDocX auto-wraps this inside scalable fences guaranteeing beautiful output boundaries.)*

---

## 🌈 Coloring Variables / Complex Visual Alignments 

Applying strict Theme Colors mapped upon equation objects fails fundamentally standardizing across engine environments natively. KritiDocX injects dynamic schema boundaries rewriting standard run mappings across entire arrays: `Integrals`, `Summation Headers`, `Variable parameters`, applying Hex modifications without corrupting string flow syntax layouts safely natively overriding OMML overrides structurally mapped automatically applying base styles automatically across equations cleanly:

```html
<div style="color: blue;">
    Text will be blue and formulas magically sync to design scopes overriding system base mappings without conflict checks required parsing!
    $$ x^2 + y^2 = z^2 $$
</div>

<!-- Applying Wave underline + colors dynamically through explicit classes locally across formulas overrides! -->
<p style="text-decoration: underline wavy green">
  $$\sigma = 5$$
</p>
```

## 🐞 Handling Broken Data Inputs: Graceful Fail-Over Engine  
Should complex strings corrupt conversion XML capabilities due to catastrophic external variables passed to LaTeX parameters internally structurally misdefined mathematically rendering equations to collapse the engine safely generates clean String Fallback Variables displaying parameters explicitly identifying failure parameters without application exit triggers failing system automation workflows handling multiple large scale pipelines locally!

**Error Rendering Example Output:**
*[Formula: $ Broken \backslash Matrix \$ Error _ _ Data$]* 


Push further! See how the engine replaces input syntax definitions entirely swapping them to functioning UI objects in the  **[Interactive Forms (SDT) Framework ➔](interactive-forms.md)**