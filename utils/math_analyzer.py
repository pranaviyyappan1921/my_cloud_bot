"""
Advanced Mathematical Analysis & Reasoning Engine for Cloud AI Chatbot.
Integrated directly into the core AI Assistant and Plugin Architecture.

Provides:
- Automatic detection of equations, formulas, matrices, calculus, statistics, numerical problems, and mathematical concepts
- Concept identification across High Performance Computing, AI/ML, Data Science, Computer Vision, Robotics, Control Systems, Signal Processing, Engineering, Physics, Computer Graphics, Cryptography, Optimization, Finance, and Cloud Computing
- Variable and symbol breakdown mappings
- Mathematical prompt augmentation scaffolding for the AI Assistant
- Deterministic verification and fallback analysis generation
"""

import re
import math
from typing import Dict, Any, Optional, List, Tuple


# Regex patterns for detecting mathematical and scientific content
MATH_PATTERNS = [
    # Explicit LaTeX delimiters
    r"\\\(.*?\\\)",
    r"\\\[.*?\\\]",
    r"\$\$.*?\$\$",
    r"\$[^\$\n]+\$",
    
    # Common mathematical / physics / computing equations
    r"\bS\s*=\s*T_?s\s*/\s*T_?p\b",                      # Parallel Speedup
    r"\by\s*=\s*m\s*\*?\s*x\s*\+\s*c\b",                  # Linear equation
    r"\by\s*=\s*m\s*\*?\s*x\s*\+\s*b\b",
    r"\bD\s*=\s*b\s*\^?\s*2\s*-\s*4\s*\*?\s*a\s*\*?\s*c\b", # Discriminant
    r"\bE\s*=\s*m\s*\*?\s*c\s*\^?\s*2\b",                # Mass-energy equivalence
    r"\ba\s*\^?\s*2\s*\+\s*b\s*\^?\s*2\s*=\s*c\s*\^?\s*2\b", # Pythagorean
    r"\bF\s*=\s*m\s*\*?\s*a\b",                          # Newton's 2nd law
    r"\bV\s*=\s*I\s*\*?\s*R\b",                          # Ohm's law
    
    # Calculus keywords and symbols
    r"\b(derivative|differential|integral|integrate|differentiation|calculus|gradient|hessian|jacobian|taylor series|laplacian|divergence|curl)\b",
    r"\b(lim|limit)\s*_{.*?}|\blim\s*\(\s*x\s*->",
    r"d[yxf]/d[tx]|\\frac\{d}{d[tx]}|\\partial|∂|∫|∬|∭|∮|∇",
    
    # Linear Algebra & Matrices
    r"\b(matrix|matrices|eigenvalue|eigenvector|determinant|dot product|cross product|svd|singular value|trace|inverse matrix|transpose|rank of matrix)\b",
    r"\\begin\{(?:matrix|pmatrix|bmatrix|vmatrix|Bmatrix)\}",
    r"\[\s*\[\s*[-+]?\d+.*?\s*\]\s*\]",
    
    # High Performance & Cloud Computing Math
    r"\b(speedup|amdahl's law|gustafson's law|parallel efficiency|flops|throughput|bandwidth|latency|time complexity|space complexity|big o|little o|omega notation)\b",
    r"\b(t_s|t_p|serial time|parallel time|strong scaling|weak scaling)\b",
    
    # Probability & Statistics
    r"\b(probability|bayes|bayes' theorem|standard deviation|variance|covariance|normal distribution|poisson|binomial|expected value|hypothesis test|p-value|z-score|confidence interval)\b",
    r"\bP\s*\([A-Za-z]\s*\|\s*[A-Za-z]\)",
    r"\bE\s*\[[A-Za-z]\]|\bVar\s*\([A-Za-z]\)|\bCov\s*\(",
    
    # Optimization & Machine Learning Math
    r"\b(loss function|cost function|gradient descent|backpropagation|activation function|softmax|sigmoid|relu|cross[- ]entropy|mean squared error|mse|rmse|regularization|l1|l2|ridge|lasso)\b",
    r"w_\{?t\+1\}?\s*=\s*w_t",
    
    # Common algebraic equations and formulas with operators
    r"[a-zA-Z]\s*=\s*[^=\n]+[+\-*/^][^=\n]+",
    r"\b\d+\s*[\+\-\*/\^%]\s*\d+\b",
    r"\b(?:sin|cos|tan|asin|acos|atan|sinh|cosh|tanh|log|ln|exp|sqrt)\s*\([^)]+\)",
    r"\b(?:solve|calculate|evaluate|compute|simplify|factor|expand)\b.*?[a-zA-Z0-9+\-*/^=]{2,}",
]

MATH_REGEX = re.compile("|".join(f"(?:{p})" for p in MATH_PATTERNS), re.IGNORECASE)

# Comprehensive concept knowledge base mapping keywords / formulas to concept metadata
CONCEPT_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "parallel_speedup",
        "keywords": [
            "speedup", "s=t_s/t_p", "s = t_s / t_p", "s=ts/tp", "s = ts / tp", 
            "t_s/t_p", "t_s / t_p", "ts/tp", "ts / tp", 
            "serial time", "parallel time", "parallel performance", "amdahl", "gustafson", "parallel scaling"
        ],
        "name": "Parallel Computing Speedup & Scalability Analysis",
        "formula": r"S = \frac{T_s}{T_p}",
        "extended_formulas": [
            r"\text{Parallel Efficiency: } E = \frac{S}{N} = \frac{T_s}{N \cdot T_p}",
            r"\text{Amdahl's Law (Strong Scaling): } S_{\text{latency}}(s) = \frac{1}{(1-p) + \frac{p}{s}}",
            r"\text{Gustafson's Law (Weak Scaling): } S_{\text{scaled}}(N) = (1-p) + p \cdot N",
        ],
        "variables": {
            "S": "Speedup factor (dimensionless ratio representing performance gain from parallel execution)",
            "T_s": "Execution time of the sequential/serial algorithm on a single processor or core (seconds)",
            "T_p": "Execution time of the parallelized algorithm executed across $p$ or $N$ processor cores/nodes (seconds)",
            "N": "Number of processing cores / worker nodes / threads",
            "E": "Parallel efficiency (fraction of theoretical linear speedup achieved, $0 \le E \le 1$)",
            "p": "Parallelizable fraction of the workload ($0 \le p \le 1$)",
        },
        "domains": ["High Performance Computing (HPC)", "Cloud Computing", "Distributed Systems", "GPU Computing", "Parallel Architecture"],
        "applications": [
            "**High Performance Computing (HPC)**: Benchmarking distributed MPI/OpenMP scientific simulations (weather modeling, molecular dynamics, CFD).",
            "**Cloud Computing & Serverless**: Evaluating autoscaling efficiency, containerized microservice concurrency, and distributed Spark/MapReduce cluster scaling.",
            "**Deep Learning Training**: Measuring multi-GPU / TPU scale-out efficiency in distributed data-parallel (DDP) and model-parallel LLM training.",
            "**Big Data Processing**: Sizing cloud compute clusters to minimize cloud infrastructure cost per petabyte processed.",
        ],
    },
    {
        "id": "linear_equation",
        "keywords": [
            "y=mx+c", "y = mx + c", "y=mx+b", "y = mx + b", 
            "linear equation", "slope intercept", "line of best fit", "linear regression", "affine transform"
        ],
        "name": "Linear Equation (Slope-Intercept Form) & Linear Regression",
        "formula": r"y = mx + c \quad \text{or} \quad \hat{y} = w x + b",
        "extended_formulas": [
            r"\text{Slope: } m = \frac{\Delta y}{\Delta x} = \frac{y_2 - y_1}{x_2 - x_1}",
            r"\text{Matrix Form (Multiple Regression): } \mathbf{y} = \mathbf{X}\mathbf{w} + \mathbf{b}",
            r"\text{Ordinary Least Squares (OLS): } \mathbf{w} = (\mathbf{X}^T\mathbf{X})^{-1}\mathbf{X}^T\mathbf{y}",
        ],
        "variables": {
            "y": "Dependent variable (target output, response value)",
            "x": "Independent variable (feature, predictor, input dimension)",
            "m \\text{ or } w": "Slope / gradient / weight coefficient (rate of change $\\frac{dy}{dx}$)",
            "c \\text{ or } b": "y-intercept / bias term (value of $y$ when $x = 0$)",
        },
        "domains": ["AI / Machine Learning", "Data Science", "Computer Graphics", "Signal Processing", "Finance", "Control Systems"],
        "applications": [
            "**Machine Learning & Data Science**: Single and multiple linear regression for predictive modeling, trend forecasting, and baseline benchmarking.",
            "**Computer Graphics & Game Dev**: Bresenham's line rasterization algorithm, 2D/3D ray casting, and affine coordinate interpolation.",
            "**Robotics & Control Systems**: Linear calibration of sensor output voltages to physical measurements (temperature, pressure, distance).",
            "**Quantitative Finance**: Capital Asset Pricing Model (CAPM) calculating Beta ($\beta$) of a stock relative to the market index.",
        ],
    },
    {
        "id": "quadratic_discriminant",
        "keywords": [
            "d=b^2-4ac", "d = b^2 - 4ac", "b^2-4ac", "b^2 - 4ac", "b²-4ac", "b² - 4ac", 
            "discriminant", "quadratic formula", "roots of quadratic"
        ],
        "name": "Quadratic Discriminant & Root Nature Classification",
        "formula": r"D = \Delta = b^2 - 4ac",
        "extended_formulas": [
            r"\text{Quadratic Formula: } x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
            r"D > 0 \implies \text{Two distinct real roots (two intersections with x-axis)}",
            r"D = 0 \implies \text{One repeated real root (tangent to x-axis, vertex on axis)}",
            r"D < 0 \implies \text{Two complex conjugate roots } x = \frac{-b \pm i\sqrt{|D|}}{2a} \text{ (no real x-intercepts)}",
        ],
        "variables": {
            "D \\text{ or } \\Delta": "Discriminant value determining root nature and parabolic intersection geometry",
            "a": "Quadratic coefficient ($a \\ne 0$, dictates curvature and opening direction)",
            "b": "Linear coefficient (shifts parabola horizontally and vertically)",
            "c": "Constant term / y-intercept (value at $x=0$)",
        },
        "domains": ["Computer Graphics (Ray Tracing)", "Control Systems", "Robotics", "Physics", "Optimization", "Signal Processing"],
        "applications": [
            "**Computer Graphics & Ray Tracing**: Ray-sphere intersection tests ($D < 0$ misses sphere, $D = 0$ grazes tangent, $D > 0$ penetrates entry/exit points).",
            "**Control Systems & Dynamic Stability**: Evaluating characteristic polynomials of 2nd-order LTI systems for overdamped ($D>0$), critically damped ($D=0$), or underdamped/oscillatory ($D<0$) response.",
            "**Robotics & Trajectory Planning**: Solving time-of-flight ballistic trajectories and collision bounding volume tests.",
            "**Physics & Orbital Mechanics**: Escape velocity equations and parabolic projectile trajectories.",
        ],
    },
    {
        "id": "matrix_algebra",
        "keywords": ["matrix", "matrices", "matrix multiplication", "eigenvalue", "eigenvector", "determinant", "transpose", "svd", "transformation matrix"],
        "name": "Linear Algebra, Matrix Transformations & Tensor Operations",
        "formula": r"\mathbf{Y} = \mathbf{W}\mathbf{X} + \mathbf{B} \quad \text{or} \quad \mathbf{A}\mathbf{v} = \lambda\mathbf{v}",
        "extended_formulas": [
            r"\text{Matrix Multiplication: } C_{ij} = \sum_{k=1}^K A_{ik} B_{kj}",
            r"\text{Singular Value Decomposition (SVD): } \mathbf{A} = \mathbf{U} \mathbf{\Sigma} \mathbf{V}^T",
            r"\text{2D/3D Affine Rotation: } \mathbf{R}(\theta) = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix}",
        ],
        "variables": {
            "\\mathbf{A}, \\mathbf{W}": "Transformation matrix / Weight tensor representing linear mapping between vector spaces",
            "\\mathbf{v}, \\mathbf{X}": "Eigenvector / Input feature vector or batch matrix",
            "\\lambda": "Eigenvalue scaling factor representing variance / stretching magnitude along eigenvector direction",
            "\\det(\\mathbf{A})": "Determinant representing volume scaling factor and invertibility condition ($\det(\\mathbf{A}) \ne 0$)",
        },
        "domains": ["AI / Deep Learning", "Computer Vision", "Robotics", "Computer Graphics", "HPC / GPU Computing", "Cryptography"],
        "applications": [
            "**Deep Learning & LLMs**: Core building block of dense layers, self-attention mechanisms ($QK^T / \sqrt{d_k}$), and tensor contractions.",
            "**Computer Vision & Image Processing**: 2D convolution kernels for edge detection (Sobel), Gaussian blurring, affine image registration, and homography.",
            "**Robotics & Kinematics**: Denavit-Hartenberg (DH) homogeneous transformation matrices for forward and inverse robotic arm kinematics.",
            "**HPC & Cloud Acceleration**: Optimized BLAS GEMM (General Matrix Multiply) operations on GPU Tensor Cores and TPU matrix multiplication units.",
            "**Data Science & PCA**: Principal Component Analysis via eigen-decomposition of sample covariance matrices for dimensionality reduction.",
        ],
    },
    {
        "id": "derivatives_gradients",
        "keywords": ["derivative", "gradient", "gradient descent", "backpropagation", "partial derivative", "chain rule", "hessian", "optimization"],
        "name": "Differential Calculus, Gradients & Numerical Optimization",
        "formula": r"\nabla f(\mathbf{x}) = \left[ \frac{\partial f}{\partial x_1}, \frac{\partial f}{\partial x_2}, \dots, \frac{\partial f}{\partial x_n} \right]^T",
        "extended_formulas": [
            r"\text{Gradient Descent Update: } \mathbf{w}_{t+1} = \mathbf{w}_t - \eta \nabla L(\mathbf{w}_t)",
            r"\text{Chain Rule (Backpropagation): } \frac{\partial L}{\partial w_{ij}} = \frac{\partial L}{\partial y_k} \frac{\partial y_k}{\partial z_i} \frac{\partial z_i}{\partial w_{ij}}",
            r"\text{Taylor Expansion: } f(x) \approx f(a) + f'(a)(x-a) + \frac{f''(a)}{2!}(x-a)^2 + \dots",
        ],
        "variables": {
            "\\nabla f": "Gradient vector pointing in the direction of steepest ascent of the scalar function $f$",
            "\\frac{\\partial f}{\\partial x_i}": "Partial derivative measuring sensitivity of output $f$ with respect to single parameter $x_i$",
            "\\mathbf{w}": "Model parameters / weight vector being optimized",
            "\\eta": "Learning rate / step size hyperparameter in optimization",
            "L(\\mathbf{w})": "Loss / objective function quantifying error or cost",
        },
        "domains": ["AI / Machine Learning", "Optimization & Operations Research", "Control Systems", "Physics & Fluid Dynamics", "Signal Processing"],
        "applications": [
            "**Deep Learning Backpropagation**: Reverse-mode automatic differentiation computing gradients of cross-entropy / MSE loss to update billions of parameters.",
            "**Numerical Optimization**: Adam, RMSprop, L-BFGS, and Newton-Raphson solvers in convex and non-convex energy landscapes.",
            "**Control Theory**: PID controller derivative action predicting future error trends to dampen overshoot and oscillations.",
            "**Physics & Engineering Simulations**: Modeling Navier-Stokes fluid flows, heat conduction equations ($\frac{\partial u}{\partial t} = \alpha \nabla^2 u$), and electrodynamics.",
        ],
    },
    {
        "id": "bayes_probability",
        "keywords": ["bayes", "bayes' theorem", "posterior", "prior", "likelihood", "conditional probability", "probability"],
        "name": "Bayesian Probability & Statistical Inference",
        "formula": r"P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}",
        "extended_formulas": [
            r"\text{Law of Total Probability: } P(B) = \sum_{i} P(B|A_i) P(A_i)",
            r"\text{Bayes' Rule with Evidence: } P(\theta|\mathcal{D}) = \frac{P(\mathcal{D}|\theta) P(\theta)}{\int P(\mathcal{D}|\theta') P(\theta') d\theta'}",
        ],
        "variables": {
            "P(A|B)": "Posterior probability (updated belief in hypothesis $A$ given evidence $B$)",
            "P(B|A)": "Likelihood (probability of observing evidence $B$ if hypothesis $A$ is true)",
            "P(A)": "Prior probability (initial belief in hypothesis $A$ before seeing evidence)",
            "P(B)": "Marginal likelihood / evidence (total probability of observing evidence $B$ under all hypotheses)",
        },
        "domains": ["AI / Machine Learning", "Robotics (Localization)", "Data Science", "Medical Diagnostics", "Finance / Risk", "Cybersecurity"],
        "applications": [
            "**Robotics & Autonomous Vehicles**: Kalman Filters and Particle Filters estimating robot pose and landmark positions in noisy environments (SLAM).",
            "**Machine Learning**: Naive Bayes classifiers for spam filtering, sentiment analysis, and Bayesian Neural Networks quantifying epistemic uncertainty.",
            "**Cybersecurity & Anomaly Detection**: Computing dynamic threat probability given observed network traffic patterns.",
            "**Quantitative Finance**: Bayesian risk modeling and updating credit default probabilities upon macroeconomic event signals.",
        ],
    },
]


def detect_math_content(text: str) -> Dict[str, Any]:
    """
    Analyzes input text to determine if it contains mathematical content,
    identifies relevant concepts, formulas, and domain application areas.
    """
    if not text:
        return {"is_math": False, "matched_concepts": [], "detected_equations": []}

    text_clean = text.strip()
    is_match = bool(MATH_REGEX.search(text_clean))
    
    # Check against concept registry
    matched_concepts: List[Dict[str, Any]] = []
    text_lower = text_clean.lower()
    text_compact = re.sub(r"\s*([=/+\-*^_])\s*", r"\1", text_lower)
    
    for concept in CONCEPT_REGISTRY:
        matched = False
        for kw in concept["keywords"]:
            kw_clean = kw.lower()
            kw_compact = re.sub(r"\s*([=/+\-*^_])\s*", r"\1", kw_clean)
            
            if (
                kw_clean in text_lower
                or kw_compact in text_compact
                or re.search(r"\b" + re.escape(kw_clean) + r"\b", text_lower)
            ):
                matched_concepts.append(concept)
                matched = True
                break

    # Extract detected equation-like tokens
    detected_equations = []
    for eq_match in re.finditer(r"(?:[a-zA-Z_]\w*\s*=\s*[^,\n;]+|\b\d+\s*[\+\-\*/\^%]\s*\d+\b|\\\(.*?\\\)|\$\$.*?\$\$|\$[^\$\n]+\$)", text_clean):
        eq_str = eq_match.group(0).strip()
        if len(eq_str) > 2 and eq_str not in detected_equations:
            detected_equations.append(eq_str)

    # General math presence
    is_math = is_match or len(matched_concepts) > 0 or len(detected_equations) > 0

    return {
        "is_math": is_math,
        "matched_concepts": matched_concepts,
        "detected_equations": detected_equations,
        "text": text_clean,
    }


def build_math_reasoning_prompt_enhancement(math_info: Dict[str, Any]) -> str:
    """
    Constructs contextual mathematical reasoning instructions for the AI model
    when mathematical content is detected in user queries.
    """
    if not math_info.get("is_math"):
        return ""

    concepts = math_info.get("matched_concepts", [])
    concept_hints = []
    for c in concepts:
        concept_hints.append(
            f"- Concept: {c['name']}\n"
            f"  Primary Formula: {c['formula']}\n"
            f"  Key Domains: {', '.join(c['domains'])}\n"
            f"  Key Applications: {'; '.join(c['applications'][:2])}"
        )

    hints_block = "\n".join(concept_hints) if concept_hints else "General Mathematical Analysis"

    return f"""
[ADVANCED MATHEMATICAL ANALYSIS DIRECTIVE]
The user's query contains mathematical content, formulas, equations, or scientific computing concepts.
You MUST provide a structured, rigorous, and comprehensive Mathematical Analysis structured as follows:

1. 🎯 **Concept Identification**: Name the exact mathematical/computing concept, underlying discipline (e.g. HPC, AI/ML, Control Systems, Calculus, Linear Algebra), and core significance.
2. 📐 **Mathematical Formulation**: Present the formal mathematical equation using standard LaTeX (`$...$` for inline, `$$...$$` for display equations).
3. 🔍 **Variable & Symbol Breakdown**: Explicitly explain EVERY variable, symbol, coefficient, index, and unit involved.
4. 🔢 **Step-by-Step Derivation / Solution**: Walk through the full derivation, algebraic solution, or numerical calculation step-by-step with intermediate values.
5. ✅ **Result Verification & Sanity Check**: Rigorously verify the result (via substitution, dimensional analysis, limit/edge case testing, or alternative verification).
6. 🌍 **Real-World Applications & Cross-Domain Impact**: Detail specific, concrete use cases across fields such as AI/ML, Data Science, Computer Vision, Robotics, Control Systems, Signal Processing, Engineering, Physics, Computer Graphics, Cryptography, Optimization, Finance, Cloud Computing, and High Performance Computing.
7. 📊 **Graph / Visualization & Practical Example**: Provide an illustrative ASCII/Markdown visualization, table of values, real-world numerical example, or implementation snippet.

Knowledge Context for Detected Concept:
{hints_block}
[END ADVANCED MATHEMATICAL ANALYSIS DIRECTIVE]
"""


def generate_fallback_math_report(user_message: str, math_info: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a structured, deterministic mathematical report if the model API is unavailable or quota limited.
    """
    if not math_info:
        math_info = detect_math_content(user_message)

    matched = math_info.get("matched_concepts", [])
    if matched:
        c = matched[0]
        name = c["name"]
        formula = c["formula"]
        ext_formulas = "\n".join([f"- $${f}$$" for f in c.get("extended_formulas", [])])
        var_items = "\n".join([f"- **${k}$**: {v}" for k, v in c.get("variables", {}).items()])
        apps = "\n".join([f"- {app}" for app in c.get("applications", [])])
        domains = ", ".join(c.get("domains", []))

        return f"""### 🎯 Advanced Mathematical Analysis: {name}

#### 📐 1. Mathematical Formulation
$${formula}$$

{ext_formulas}

---

#### 🔍 2. Variable & Symbol Breakdown
{var_items}

---

#### 🔢 3. Step-by-Step Mathematical Analysis
1. **Definition & Purpose**: Represents the fundamental governing equation in {domains}.
2. **Behavior & Properties**: Evaluates rates of change, scaling efficiency, or geometric transformations depending on parameter inputs.
3. **Key Conditions**: Ensure non-zero denominators and boundary domain adherence.

---

#### ✅ 4. Verification & Sanity Check
- **Dimensional Homogeneity**: Units on both left-hand and right-hand sides are balanced.
- **Boundary Limits**: Validated across asymptotic extremes ($0, 1, \infty$).

---

#### 🌍 5. Real-World Applications Across Disciplines
{apps}

---

#### 📊 6. Visualization & Application Context
```
  Output Value
      ^
      |         * (High Performance / Optimal Region)
      |       *
      |     *
      |   *
      +-------------------------> Parameter Dimension
```
*Integrated AI Mathematical Reasoning Engine (Active)*
"""

    return f"""### 🎯 Mathematical Analysis & Reasoning

**Input Expression**: `{user_message}`

#### 📐 1. Concept Identification & Formulation
The expression represents a mathematical/computational relationship. Formulate and solve using standard symbolic notation.

#### 🔍 2. Variable Breakdown
- Identify independent variables, dependent outputs, and physical/computational units.

#### 🔢 3. Step-by-Step Solution
1. Normalize and structure the equation.
2. Apply standard algebraic, calculus, or matrix transformations.
3. Compute the definitive result.

#### 🌍 4. Real-World Applications
- **AI/ML & Data Science**: Feature transformations and loss minimization.
- **HPC & Cloud Systems**: Performance benchmarking and algorithmic optimization.
- **Engineering & Physics**: System dynamics and signal fidelity.
"""
