# 🎨 Poster Graphics Generator

Professional, publication-quality visualizations of your GPU energy prediction model designed for poster presentations.

## 📊 Scripts Overview

### 1. **visualization.py** - Core Model Visualizations
Essential plots showing model predictions and performance:

- **Predictions vs Actual** - Side-by-side scatter plots comparing predicted vs actual values for both GPU energy and output tokens with perfect prediction diagonal lines
- **Residual Plots** - Shows prediction errors across the range of values to identify systematic biases
- **Energy vs Tokens** - Scatter plot with color gradient showing the relationship between input tokens and GPU energy consumption
- **Error Distribution** - Histograms of absolute prediction errors with mean markers
- **Model Architecture** - Visual flowchart of the complete pipeline from inputs through preprocessing to predictions

**Usage:**
```bash
python visualization.py
```

**Output:** 5 PNG files (300 DPI)

---

### 2. **advanced_visualization.py** - Metrics & Feature Analysis
In-depth analysis suitable for technical audiences:

- **Metrics Card** - Clean summary card with R² scores, RMSE, MAE, and model configuration
- **Accuracy Heatmap** - Binned heatmaps showing prediction accuracy (MAE) across different input ranges
- **Top Features** - Bar chart of the 15 most important TF-IDF text features with scores
- **Correlation Analysis** - Shows which features correlate most strongly with GPU energy

**Usage:**
```bash
python advanced_visualization.py
```

**Output:** 4 PNG files (300 DPI)

---

### 3. **dashboard_visualization.py** - Comprehensive Dashboard
Ready-for-poster visualizations:

- **Comprehensive Dashboard** - All-in-one figure with predictions, metrics, error distributions, and correlations in a professional layout
- **Summary Infographic** - Visually striking summary with dataset info, accuracy metrics, model pipeline explanation, and sustainability message

**Usage:**
```bash
python dashboard_visualization.py
```

**Output:** 2 PNG files (300 DPI)

---

## 🚀 Quick Start

### Generate All Graphics at Once
```bash
python run_all_visualizations.py
```

This will run all three visualization scripts and display a summary of generated files.

### Generate Individual Visualizations
```bash
# Just core plots
python visualization.py

# Just advanced metrics
python advanced_visualization.py

# Just dashboard/infographic
python dashboard_visualization.py
```

## 📁 Output

All graphics are saved to the `poster_graphics/` directory created automatically.

**File naming:**
- `predictions_vs_actual.png` - Primary prediction accuracy plot
- `residuals.png` - Residual analysis
- `energy_vs_tokens.png` - Feature correlation
- `error_distribution.png` - Error patterns
- `model_architecture.png` - Pipeline diagram
- `metrics_card.png` - Performance summary
- `accuracy_heatmap.png` - 2D accuracy analysis
- `top_features.png` - Feature importance
- `correlation_energy.png` - Feature correlations
- `dashboard.png` - Comprehensive dashboard
- `summary_infographic.png` - Visual summary

## 🎯 Recommended Poster Usage

### For Academic Posters:
1. Use `model_architecture.png` to explain the model
2. Use `dashboard.png` as main visualization
3. Include `top_features.png` for technical details
4. Add `metrics_card.png` for performance claims

### For General Audiences:
1. Display `summary_infographic.png` as the hero visual
2. Use `predictions_vs_actual.png` to show accuracy
3. Include `energy_vs_tokens.png` to show the real-world relationship

### For Technical Details:
1. Include `model_architecture.png`
2. Show `accuracy_heatmap.png` for performance breakdown
3. Add `residuals.png` to show systematic errors
4. Display `top_features.png` for interpretability

## 🔍 About the Model

**What it does:**
- Predicts GPU energy consumption (Joules) during LLM inference
- Predicts output token count from input text

**Input features:**
- Input text (converted to 2000 TF-IDF features with 1-2 grams)
- Input token count (standardized)

**Algorithm:**
- MultiOutputRegressor with Ridge regression (α=1.0)
- Linear model producing smooth predictions without artifacts

**Training data:**
- Inference records with GPU metrics (power, temperature, memory, utilization)
- Train/test split: 80/20

## 📝 Customization

All scripts use configurable parameters:

```python
# Modify in scripts:
plt.rcParams['figure.dpi'] = 300  # DPI (300 for printing)
plt.rcParams['font.size'] = 11     # Base font size
OUTPUT_DIR = Path("poster_graphics")  # Output directory
```

## 🌱 Context: Sustainability

This model is part of a sustainability framework focused on:
- Understanding GPU energy consumption patterns
- Predicting inference costs for LLM deployments
- Optimizing AI workloads for environmental impact
- Supporting carbon-aware computing decisions

---

**All graphics are saved in 300 DPI PNG format suitable for printing on large posters!**
