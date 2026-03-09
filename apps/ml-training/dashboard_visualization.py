"""
Comprehensive dashboard visualization combining multiple metrics in one poster-friendly image.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from ml_model import train_and_evaluate
from ml_data import load_data

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 300
plt.rcParams["font.size"] = 9
plt.rcParams["figure.facecolor"] = "white"

OUTPUT_DIR = Path("poster_graphics")
OUTPUT_DIR.mkdir(exist_ok=True)


def create_comprehensive_dashboard(sample_df, output_file="dashboard.png"):
    """Create a comprehensive dashboard with all key metrics and plots."""

    # Create figure with custom layout
    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.3)

    # ===== ROW 1: TITLE AND KEY METRICS =====
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis("off")
    ax_title.text(
        0.5,
        0.8,
        "GPU Energy & Token Prediction Model",
        fontsize=20,
        fontweight="bold",
        ha="center",
        transform=ax_title.transAxes,
    )
    ax_title.text(
        0.5,
        0.3,
        "Multi-output regression predicting GPU energy consumption and output tokens from input text and token count",
        fontsize=11,
        ha="center",
        transform=ax_title.transAxes,
        style="italic",
        color="gray",
    )

    # ===== ROW 2: PREDICTIONS & ERRORS =====
    # Predictions plot - GPU Energy
    ax1 = fig.add_subplot(gs[1, 0])
    ax1.scatter(
        sample_df["actual_gpu_energy_j"],
        sample_df["pred_gpu_energy_j"],
        alpha=0.5,
        s=30,
        color="#FF6B6B",
        edgecolors="darkred",
        linewidth=0.3,
    )
    min_v = sample_df["actual_gpu_energy_j"].min()
    max_v = sample_df["actual_gpu_energy_j"].max()
    ax1.plot([min_v, max_v], [min_v, max_v], "k--", lw=1.5, alpha=0.6)
    ax1.set_xlabel("Actual (J)", fontweight="bold", fontsize=10)
    ax1.set_ylabel("Predicted (J)", fontweight="bold", fontsize=10)
    ax1.set_title("GPU Energy Predictions", fontweight="bold")
    ax1.grid(alpha=0.2)

    # Predictions plot - Tokens
    ax2 = fig.add_subplot(gs[1, 1])
    ax2.scatter(
        sample_df["actual_output_tokens"],
        sample_df["pred_output_tokens"],
        alpha=0.5,
        s=30,
        color="#4ECDC4",
        edgecolors="darkgreen",
        linewidth=0.3,
    )
    min_v = sample_df["actual_output_tokens"].min()
    max_v = sample_df["actual_output_tokens"].max()
    ax2.plot([min_v, max_v], [min_v, max_v], "k--", lw=1.5, alpha=0.6)
    ax2.set_xlabel("Actual", fontweight="bold", fontsize=10)
    ax2.set_ylabel("Predicted", fontweight="bold", fontsize=10)
    ax2.set_title("Output Token Predictions", fontweight="bold")
    ax2.grid(alpha=0.2)

    # Metrics summary box
    ax3 = fig.add_subplot(gs[1, 2])
    ax3.axis("off")

    r2_energy = r2_score(
        sample_df["actual_gpu_energy_j"], sample_df["pred_gpu_energy_j"]
    )
    r2_tokens = r2_score(
        sample_df["actual_output_tokens"], sample_df["pred_output_tokens"]
    )
    rmse_energy = np.sqrt(
        mean_squared_error(
            sample_df["actual_gpu_energy_j"], sample_df["pred_gpu_energy_j"]
        )
    )
    rmse_tokens = np.sqrt(
        mean_squared_error(
            sample_df["actual_output_tokens"], sample_df["pred_output_tokens"]
        )
    )

    metrics_text = f"""
    ╔═══════════════════════════╗
    ║   MODEL PERFORMANCE       ║
    ╠═══════════════════════════╣
    ║  GPU ENERGY               ║
    ║  R² = {r2_energy:.4f}          ║
    ║  RMSE = {rmse_energy:.4f} J        ║
    ║                           ║
    ║  OUTPUT TOKENS            ║
    ║  R² = {r2_tokens:.4f}          ║
    ║  RMSE = {rmse_tokens:.4f}          ║
    ║                           ║
    ║  Test Set: {len(sample_df)} samples   ║
    ╚═══════════════════════════╝
    """
    ax3.text(
        0.05,
        0.5,
        metrics_text,
        fontsize=9,
        family="monospace",
        transform=ax3.transAxes,
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8, pad=0.8),
    )

    # ===== ROW 3: DISTRIBUTIONS & CORRELATIONS =====
    # Error distribution - Energy
    ax4 = fig.add_subplot(gs[2, 0])
    errors_e = np.abs(sample_df["actual_gpu_energy_j"] - sample_df["pred_gpu_energy_j"])
    ax4.hist(
        errors_e,
        bins=25,
        color="#FF6B6B",
        alpha=0.7,
        edgecolor="darkred",
        linewidth=0.5,
    )
    ax4.axvline(
        errors_e.mean(),
        color="red",
        linestyle="--",
        lw=2,
        label=f"μ={errors_e.mean():.2f}",
    )
    ax4.set_xlabel("Absolute Error (J)", fontweight="bold", fontsize=10)
    ax4.set_ylabel("Frequency", fontweight="bold", fontsize=10)
    ax4.set_title("Energy Error Distribution", fontweight="bold")
    ax4.legend(fontsize=8)
    ax4.grid(alpha=0.2, axis="y")

    # Error distribution - Tokens
    ax5 = fig.add_subplot(gs[2, 1])
    errors_t = np.abs(
        sample_df["actual_output_tokens"] - sample_df["pred_output_tokens"]
    )
    ax5.hist(
        errors_t,
        bins=25,
        color="#4ECDC4",
        alpha=0.7,
        edgecolor="darkgreen",
        linewidth=0.5,
    )
    ax5.axvline(
        errors_t.mean(),
        color="teal",
        linestyle="--",
        lw=2,
        label=f"μ={errors_t.mean():.2f}",
    )
    ax5.set_xlabel("Absolute Error (tokens)", fontweight="bold", fontsize=10)
    ax5.set_ylabel("Frequency", fontweight="bold", fontsize=10)
    ax5.set_title("Token Error Distribution", fontweight="bold")
    ax5.legend(fontsize=8)
    ax5.grid(alpha=0.2, axis="y")

    # Input-Output relationship
    ax6 = fig.add_subplot(gs[2, 2])
    scatter = ax6.scatter(
        sample_df["input_tokens"],
        sample_df["actual_gpu_energy_j"],
        c=sample_df["actual_output_tokens"],
        s=50,
        cmap="plasma",
        alpha=0.6,
        edgecolors="black",
        linewidth=0.3,
    )
    ax6.set_xlabel("Input Tokens", fontweight="bold", fontsize=10)
    ax6.set_ylabel("GPU Energy (J)", fontweight="bold", fontsize=10)
    ax6.set_title("Tokens vs Energy", fontweight="bold")
    ax6.grid(alpha=0.2)
    cbar = plt.colorbar(scatter, ax=ax6, label="Output Tokens")
    cbar.ax.tick_params(labelsize=8)

    plt.savefig(
        OUTPUT_DIR / output_file,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    print(f"✓ Saved {output_file}")
    plt.close()


def create_summary_infographic(sample_df, output_file="summary_infographic.png"):
    """Create a visually striking summary infographic."""
    fig, ax = plt.subplots(figsize=(12, 10), facecolor="white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Calculate metrics
    r2_energy = r2_score(
        sample_df["actual_gpu_energy_j"], sample_df["pred_gpu_energy_j"]
    )
    mae_energy = mean_absolute_error(
        sample_df["actual_gpu_energy_j"], sample_df["pred_gpu_energy_j"]
    )

    # Title
    ax.text(
        5, 9.3, "Sustainability ML Model", fontsize=24, fontweight="bold", ha="center"
    )
    ax.text(
        5,
        8.9,
        "Predicting GPU Energy Consumption & LLM Output",
        fontsize=12,
        ha="center",
        style="italic",
        color="gray",
    )

    # Key metrics in boxes
    from matplotlib.patches import FancyBboxPatch, Circle

    box_y = 7.8
    box_height = 1.2
    box_width = 2.8

    # Box 1: Dataset
    rect = FancyBboxPatch(
        (0.5, box_y - box_height),
        box_width,
        box_height,
        boxstyle="round,pad=0.1",
        facecolor="#E3F2FD",
        edgecolor="#1976D2",
        linewidth=2.5,
    )
    ax.add_patch(rect)
    ax.text(
        0.5 + box_width / 2,
        box_y - 0.3,
        "📊 Dataset",
        fontsize=12,
        fontweight="bold",
        ha="center",
    )
    ax.text(
        0.5 + box_width / 2,
        box_y - 0.65,
        f"{len(sample_df)} samples",
        fontsize=11,
        ha="center",
        fontweight="bold",
    )
    ax.text(
        0.5 + box_width / 2,
        box_y - 0.95,
        "80/20 split",
        fontsize=10,
        ha="center",
        style="italic",
    )

    # Box 2: Model Accuracy
    rect = FancyBboxPatch(
        (3.6, box_y - box_height),
        box_width,
        box_height,
        boxstyle="round,pad=0.1",
        facecolor="#F3E5F5",
        edgecolor="#7B1FA2",
        linewidth=2.5,
    )
    ax.add_patch(rect)
    ax.text(
        3.6 + box_width / 2,
        box_y - 0.3,
        "🎯 Accuracy",
        fontsize=12,
        fontweight="bold",
        ha="center",
    )
    ax.text(
        3.6 + box_width / 2,
        box_y - 0.65,
        f"R² = {r2_energy:.3f}",
        fontsize=11,
        ha="center",
        fontweight="bold",
    )
    ax.text(
        3.6 + box_width / 2,
        box_y - 0.95,
        f"MAE = {mae_energy:.2f}J",
        fontsize=10,
        ha="center",
        style="italic",
    )

    # Box 3: Features
    rect = FancyBboxPatch(
        (6.7, box_y - box_height),
        box_width,
        box_height,
        boxstyle="round,pad=0.1",
        facecolor="#E8F5E9",
        edgecolor="#388E3C",
        linewidth=2.5,
    )
    ax.add_patch(rect)
    ax.text(
        6.7 + box_width / 2,
        box_y - 0.3,
        "⚙️ Features",
        fontsize=12,
        fontweight="bold",
        ha="center",
    )
    ax.text(
        6.7 + box_width / 2,
        box_y - 0.65,
        "2000 TF-IDF",
        fontsize=10,
        ha="center",
        fontweight="bold",
    )
    ax.text(
        6.7 + box_width / 2,
        box_y - 0.95,
        "+ token count",
        fontsize=10,
        ha="center",
        style="italic",
    )

    # Model pipeline explanation
    y_line = 6.8
    ax.text(5, y_line, "Model Pipeline", fontsize=14, fontweight="bold", ha="center")

    # Pipeline steps
    steps = [
        ("Input\nText + Tokens", 1.2, "#FFF9C4"),
        ("Feature\nExtraction", 3.2, "#C8E6C9"),
        ("Ridge\nRegression", 5.2, "#BBDEFB"),
        ("Multi-Output\nPrediction", 7.2, "#F8BBD0"),
    ]

    for text, x, color in steps:
        circle = Circle(
            (x, y_line - 1.2), 0.35, color=color, ec="black", linewidth=2, zorder=2
        )
        ax.add_patch(circle)
        ax.text(
            x,
            y_line - 1.2,
            text,
            fontsize=8,
            ha="center",
            va="center",
            fontweight="bold",
            zorder=3,
        )

        # Draw arrow between circles
        if x < 7.2:
            ax.annotate(
                "",
                xy=(x + 0.6, y_line - 1.2),
                xytext=(x + 0.35, y_line - 1.2),
                arrowprops=dict(arrowstyle="->", lw=2, color="black"),
            )

    # Output targets
    y_output = 3.5
    ax.text(
        5, y_output, "Prediction Targets", fontsize=14, fontweight="bold", ha="center"
    )

    output_items = [
        ("💾 GPU Energy (J)", 2, "#FFE5E5"),
        ("🔤 Output Tokens", 5, "#E5F5E5"),
        ("⚡ Inference Cost", 8, "#E5E5FF"),
    ]

    for text, x, color in output_items:
        rect = FancyBboxPatch(
            (x - 0.9, y_output - 1.3),
            1.8,
            0.7,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor="black",
            linewidth=1.5,
        )
        ax.add_patch(rect)
        ax.text(x, y_output - 0.95, text, fontsize=10, ha="center", fontweight="bold")

    # Footer
    ax.text(
        5,
        0.5,
        "🌱 Reducing AI Carbon Footprint Through Predictive Energy Modeling 🌱",
        fontsize=11,
        ha="center",
        fontweight="bold",
        bbox=dict(boxstyle="round", facecolor="#C8E6C9", alpha=0.7, pad=0.5),
    )

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / output_file,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        edgecolor="none",
    )
    print(f"✓ Saved {output_file}")
    plt.close()


if __name__ == "__main__":
    print("🎨 Generating dashboard & infographic...\n")

    # Load data
    print("Loading data...")
    df = load_data("assets/merged.parquet")
    pipe, sample_df = train_and_evaluate(df, test_size=0.2, random_state=0)

    print("\n📊 Creating comprehensive visualizations...")
    create_comprehensive_dashboard(sample_df)
    create_summary_infographic(sample_df)

    print(f"\n✨ Dashboard graphics saved to {OUTPUT_DIR}/")
