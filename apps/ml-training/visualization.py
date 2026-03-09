"""
Generate publication-quality graphics for ML model presentation.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from ml_model import load_model, train_and_evaluate
from ml_data import load_data

# Set style for poster-quality graphics
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 300
plt.rcParams["font.size"] = 11
plt.rcParams["axes.labelsize"] = 12
plt.rcParams["axes.titlesize"] = 13
plt.rcParams["xtick.labelsize"] = 10
plt.rcParams["ytick.labelsize"] = 10
plt.rcParams["legend.fontsize"] = 10
plt.rcParams["figure.facecolor"] = "white"

OUTPUT_DIR = Path("poster_graphics")
OUTPUT_DIR.mkdir(exist_ok=True)


def plot_predictions_vs_actual(sample_df, output_file="predictions_vs_actual.png"):
    """Create side-by-side scatter plots for model predictions."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # GPU Energy predictions
    ax = axes[0]
    ax.scatter(
        sample_df["actual_gpu_energy_j"],
        sample_df["pred_gpu_energy_j"],
        alpha=0.6,
        s=50,
        color="#FF6B6B",
        edgecolors="black",
        linewidth=0.5,
    )

    # Perfect prediction line
    min_val = sample_df["actual_gpu_energy_j"].min()
    max_val = sample_df["actual_gpu_energy_j"].max()
    ax.plot(
        [min_val, max_val],
        [min_val, max_val],
        "k--",
        lw=2,
        alpha=0.7,
        label="Perfect prediction",
    )
    ax.set_xlabel("Actual GPU Energy (Joules)", fontweight="bold")
    ax.set_ylabel("Predicted GPU Energy (Joules)", fontweight="bold")
    ax.set_title("GPU Energy Consumption Predictions", fontweight="bold", fontsize=13)
    ax.legend()
    ax.grid(alpha=0.3)

    # Output tokens predictions
    ax = axes[1]
    ax.scatter(
        sample_df["actual_output_tokens"],
        sample_df["pred_output_tokens"],
        alpha=0.6,
        s=50,
        color="#4ECDC4",
        edgecolors="black",
        linewidth=0.5,
    )

    min_val = sample_df["actual_output_tokens"].min()
    max_val = sample_df["actual_output_tokens"].max()
    ax.plot(
        [min_val, max_val],
        [min_val, max_val],
        "k--",
        lw=2,
        alpha=0.7,
        label="Perfect prediction",
    )
    ax.set_xlabel("Actual Output Tokens", fontweight="bold")
    ax.set_ylabel("Predicted Output Tokens", fontweight="bold")
    ax.set_title("Output Token Predictions", fontweight="bold", fontsize=13)
    ax.legend()
    ax.grid(alpha=0.3)

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


def plot_residuals(sample_df, output_file="residuals.png"):
    """Create residual plots to show prediction errors."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # GPU Energy residuals
    ax = axes[0]
    residuals_energy = sample_df["actual_gpu_energy_j"] - sample_df["pred_gpu_energy_j"]
    ax.scatter(
        sample_df["pred_gpu_energy_j"],
        residuals_energy,
        alpha=0.6,
        s=50,
        color="#FF6B6B",
        edgecolors="black",
        linewidth=0.5,
    )
    ax.axhline(y=0, color="k", linestyle="--", lw=2)
    ax.set_xlabel("Predicted GPU Energy (Joules)", fontweight="bold")
    ax.set_ylabel("Residuals", fontweight="bold")
    ax.set_title("GPU Energy - Residual Plot", fontweight="bold", fontsize=13)
    ax.grid(alpha=0.3)

    # Output tokens residuals
    ax = axes[1]
    residuals_tokens = (
        sample_df["actual_output_tokens"] - sample_df["pred_output_tokens"]
    )
    ax.scatter(
        sample_df["pred_output_tokens"],
        residuals_tokens,
        alpha=0.6,
        s=50,
        color="#4ECDC4",
        edgecolors="black",
        linewidth=0.5,
    )
    ax.axhline(y=0, color="k", linestyle="--", lw=2)
    ax.set_xlabel("Predicted Output Tokens", fontweight="bold")
    ax.set_ylabel("Residuals", fontweight="bold")
    ax.set_title("Output Tokens - Residual Plot", fontweight="bold", fontsize=13)
    ax.grid(alpha=0.3)

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


def plot_energy_vs_tokens(sample_df, output_file="energy_vs_tokens.png"):
    """Show relationship between input tokens and GPU energy."""
    fig, ax = plt.subplots(figsize=(10, 7))

    # Create scatter plot
    scatter = ax.scatter(
        sample_df["input_tokens"],
        sample_df["actual_gpu_energy_j"],
        c=sample_df["pred_gpu_energy_j"],
        s=100,
        cmap="viridis",
        alpha=0.7,
        edgecolors="black",
        linewidth=0.5,
    )

    ax.set_xlabel("Input Tokens", fontweight="bold", fontsize=12)
    ax.set_ylabel("GPU Energy Consumption (Joules)", fontweight="bold", fontsize=12)
    ax.set_title(
        "Inference Cost: Input Tokens vs Energy", fontweight="bold", fontsize=14
    )
    ax.grid(alpha=0.3)

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Predicted Energy (J)", fontweight="bold")

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


def plot_error_distribution(sample_df, output_file="error_distribution.png"):
    """Show distribution of prediction errors."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # GPU Energy errors
    ax = axes[0]
    errors_energy = np.abs(
        sample_df["actual_gpu_energy_j"] - sample_df["pred_gpu_energy_j"]
    )
    ax.hist(errors_energy, bins=30, color="#FF6B6B", alpha=0.7, edgecolor="black")
    ax.set_xlabel("Absolute Error (Joules)", fontweight="bold")
    ax.set_ylabel("Frequency", fontweight="bold")
    ax.set_title("GPU Energy - Error Distribution", fontweight="bold", fontsize=13)
    ax.axvline(
        errors_energy.mean(),
        color="red",
        linestyle="--",
        lw=2,
        label=f"Mean: {errors_energy.mean():.2f}",
    )
    ax.legend()
    ax.grid(alpha=0.3, axis="y")

    # Output tokens errors
    ax = axes[1]
    errors_tokens = np.abs(
        sample_df["actual_output_tokens"] - sample_df["pred_output_tokens"]
    )
    ax.hist(errors_tokens, bins=30, color="#4ECDC4", alpha=0.7, edgecolor="black")
    ax.set_xlabel("Absolute Error (tokens)", fontweight="bold")
    ax.set_ylabel("Frequency", fontweight="bold")
    ax.set_title("Output Tokens - Error Distribution", fontweight="bold", fontsize=13)
    ax.axvline(
        errors_tokens.mean(),
        color="teal",
        linestyle="--",
        lw=2,
        label=f"Mean: {errors_tokens.mean():.2f}",
    )
    ax.legend()
    ax.grid(alpha=0.3, axis="y")

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


def plot_model_architecture(output_file="model_architecture.png"):
    """Create a visual flowchart of the model architecture."""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # Define colors
    input_color = "#E8F4F8"
    process_color = "#FFE5E5"
    output_color = "#E5F5E5"

    # Helper function to draw boxes
    def draw_box(ax, x, y, width, height, text, color, fontsize=11, fontweight="bold"):
        from matplotlib.patches import FancyBboxPatch

        box = FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.1",
            edgecolor="black",
            facecolor=color,
            linewidth=2,
        )
        ax.add_patch(box)
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight=fontweight,
            wrap=True,
        )

    def draw_arrow(ax, x1, y1, x2, y2, text=""):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", lw=2.5, color="black"),
        )
        if text:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(
                mid_x + 0.3,
                mid_y,
                text,
                fontsize=9,
                style="italic",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.9),
            )

    # Input Features
    draw_box(ax, 2, 8.5, 2.5, 0.8, "Input Features", input_color, fontsize=12)
    draw_box(ax, 0.8, 7.2, 1.8, 0.7, "input_text", input_color, fontsize=10)
    draw_box(ax, 3.2, 7.2, 1.8, 0.7, "input_tokens", input_color, fontsize=10)

    # Preprocessing
    draw_arrow(ax, 0.8, 6.8, 0.8, 6)
    draw_arrow(ax, 3.2, 6.8, 3.2, 6)
    draw_box(
        ax,
        0.8,
        5.3,
        2,
        0.8,
        "TF-IDF Vectorizer\n(2000 features)",
        process_color,
        fontsize=10,
    )
    draw_box(ax, 3.2, 5.3, 2, 0.8, "StandardScaler", process_color, fontsize=10)

    # Feature Combination
    draw_arrow(ax, 0.8, 4.9, 2, 4.3)
    draw_arrow(ax, 3.2, 4.9, 2, 4.3)
    draw_box(ax, 2, 3.8, 2, 0.8, "Feature Space", process_color, fontsize=11)

    # Model
    draw_arrow(ax, 2, 3.4, 2, 2.6)
    draw_box(
        ax, 2, 2.1, 3, 0.8, "MultiOutputRegressor (Ridge)", process_color, fontsize=11
    )

    # Outputs
    draw_arrow(ax, 1.2, 1.7, 0.8, 1.1)
    draw_arrow(ax, 2.8, 1.7, 3.2, 1.1)
    draw_box(ax, 0.8, 0.4, 1.8, 0.7, "Output Tokens", output_color, fontsize=10)
    draw_box(ax, 3.2, 0.4, 1.8, 0.7, "GPU Energy (J)", output_color, fontsize=10)

    # Title
    ax.text(5.5, 8.8, "Model Pipeline Architecture", fontsize=16, fontweight="bold")

    # Legend
    ax.text(
        6.5,
        7.5,
        "📊 Multi-output Regression",
        fontsize=10,
        bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8),
    )
    ax.text(6.5, 6.9, "• Predicts energy & tokens", fontsize=9)
    ax.text(6.5, 6.5, "• Ridge regression (α=1.0)", fontsize=9)
    ax.text(6.5, 6.1, "• 80/20 train/test split", fontsize=9)

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
    print("🎨 Generating poster graphics...\n")

    # Load data and train model
    print("Loading data and training model...")
    df = load_data("assets/merged.parquet")
    pipe, sample_df = train_and_evaluate(df, test_size=0.2, random_state=0)

    print("\n📈 Creating visualizations...")
    # Generate all visualizations
    plot_predictions_vs_actual(sample_df)
    plot_residuals(sample_df)
    plot_energy_vs_tokens(sample_df)
    plot_error_distribution(sample_df)
    plot_model_architecture()

    print(f"\n✨ Graphics saved to {OUTPUT_DIR}/")
    print("Ready for your poster! 🎨")
