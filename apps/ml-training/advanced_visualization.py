"""
Advanced visualizations: Feature importance, metrics, and performance comparisons.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from ml_model import load_model, train_and_evaluate
from ml_data import load_data

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 300
plt.rcParams["font.size"] = 11
plt.rcParams["figure.facecolor"] = "white"

OUTPUT_DIR = Path("poster_graphics")
OUTPUT_DIR.mkdir(exist_ok=True)


def plot_metrics_card(sample_df, output_file="metrics_card.png"):
    """Create a clean metrics summary card for the poster."""
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

    # Calculate metrics
    mse_energy = mean_squared_error(
        sample_df["actual_gpu_energy_j"], sample_df["pred_gpu_energy_j"]
    )
    rmse_energy = np.sqrt(mse_energy)
    r2_energy = r2_score(
        sample_df["actual_gpu_energy_j"], sample_df["pred_gpu_energy_j"]
    )
    mae_energy = mean_absolute_error(
        sample_df["actual_gpu_energy_j"], sample_df["pred_gpu_energy_j"]
    )

    mse_tokens = mean_squared_error(
        sample_df["actual_output_tokens"], sample_df["pred_output_tokens"]
    )
    rmse_tokens = np.sqrt(mse_tokens)
    r2_tokens = r2_score(
        sample_df["actual_output_tokens"], sample_df["pred_output_tokens"]
    )
    mae_tokens = mean_absolute_error(
        sample_df["actual_output_tokens"], sample_df["pred_output_tokens"]
    )

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis("off")

    # Title
    title_y = 0.95
    ax.text(
        0.5,
        title_y,
        "Model Performance Metrics",
        fontsize=18,
        fontweight="bold",
        ha="center",
        transform=ax.transAxes,
    )

    # GPU Energy Card
    card_y = 0.75
    from matplotlib.patches import FancyBboxPatch

    # Energy card background
    rect = FancyBboxPatch(
        (0.05, card_y - 0.25),
        0.4,
        0.25,
        boxstyle="round,pad=0.02",
        facecolor="#FFE5E5",
        edgecolor="#FF6B6B",
        linewidth=3,
        transform=ax.transAxes,
    )
    ax.add_patch(rect)

    ax.text(
        0.25,
        card_y - 0.02,
        "GPU Energy Predictions",
        fontsize=13,
        fontweight="bold",
        ha="center",
        transform=ax.transAxes,
    )
    ax.text(
        0.07,
        card_y - 0.08,
        f"R² Score: {r2_energy:.4f}",
        fontsize=11,
        transform=ax.transAxes,
        family="monospace",
        fontweight="bold",
    )
    ax.text(
        0.07,
        card_y - 0.13,
        f"RMSE: {rmse_energy:.4f} J",
        fontsize=11,
        transform=ax.transAxes,
        family="monospace",
        fontweight="bold",
    )
    ax.text(
        0.07,
        card_y - 0.18,
        f"MAE: {mae_energy:.4f} J",
        fontsize=11,
        transform=ax.transAxes,
        family="monospace",
        fontweight="bold",
    )
    ax.text(
        0.07,
        card_y - 0.23,
        f"n_samples: {len(sample_df)}",
        fontsize=10,
        transform=ax.transAxes,
        family="monospace",
        style="italic",
    )

    # Tokens card background
    rect = FancyBboxPatch(
        (0.55, card_y - 0.25),
        0.4,
        0.25,
        boxstyle="round,pad=0.02",
        facecolor="#E5F5E5",
        edgecolor="#4ECDC4",
        linewidth=3,
        transform=ax.transAxes,
    )
    ax.add_patch(rect)

    ax.text(
        0.75,
        card_y - 0.02,
        "Output Token Predictions",
        fontsize=13,
        fontweight="bold",
        ha="center",
        transform=ax.transAxes,
    )
    ax.text(
        0.57,
        card_y - 0.08,
        f"R² Score: {r2_tokens:.4f}",
        fontsize=11,
        transform=ax.transAxes,
        family="monospace",
        fontweight="bold",
    )
    ax.text(
        0.57,
        card_y - 0.13,
        f"RMSE: {rmse_tokens:.4f}",
        fontsize=11,
        transform=ax.transAxes,
        family="monospace",
        fontweight="bold",
    )
    ax.text(
        0.57,
        card_y - 0.18,
        f"MAE: {mae_tokens:.4f}",
        fontsize=11,
        transform=ax.transAxes,
        family="monospace",
        fontweight="bold",
    )
    ax.text(
        0.57,
        card_y - 0.23,
        f"n_samples: {len(sample_df)}",
        fontsize=10,
        transform=ax.transAxes,
        family="monospace",
        style="italic",
    )

    # Model Info
    info_y = 0.35
    rect = FancyBboxPatch(
        (0.05, info_y - 0.2),
        0.9,
        0.2,
        boxstyle="round,pad=0.02",
        facecolor="#F0F0F0",
        edgecolor="black",
        linewidth=2,
        transform=ax.transAxes,
    )
    ax.add_patch(rect)

    ax.text(
        0.5,
        info_y - 0.02,
        "Model Configuration",
        fontsize=12,
        fontweight="bold",
        ha="center",
        transform=ax.transAxes,
    )
    ax.text(
        0.08,
        info_y - 0.08,
        "Algorithm: MultiOutputRegressor (Ridge)",
        fontsize=10,
        transform=ax.transAxes,
        family="monospace",
    )
    ax.text(
        0.08,
        info_y - 0.13,
        "Text Features: TF-IDF (2000 features, 1-2 grams)",
        fontsize=10,
        transform=ax.transAxes,
        family="monospace",
    )
    ax.text(
        0.08,
        info_y - 0.18,
        "Numerical Features: Standardized input tokens",
        fontsize=10,
        transform=ax.transAxes,
        family="monospace",
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


def plot_prediction_accuracy_heatmap(sample_df, output_file="accuracy_heatmap.png"):
    """Create binned heatmap showing prediction accuracy across ranges."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # GPU Energy: Bin actual values and show average error
    ax = axes[0]
    energy_bins = pd.cut(sample_df["actual_gpu_energy_j"], bins=10)
    token_bins = pd.cut(sample_df["input_tokens"], bins=10)

    energy_errors = np.abs(
        sample_df["actual_gpu_energy_j"] - sample_df["pred_gpu_energy_j"]
    )
    heatmap_data_energy = (
        sample_df.groupby([energy_bins, token_bins])
        .apply(lambda x: energy_errors[x.index].mean())
        .unstack()
    )

    sns.heatmap(
        heatmap_data_energy,
        cmap="RdYlGn_r",
        ax=ax,
        cbar_kws={"label": "Mean Absolute Error (J)"},
    )
    ax.set_xlabel("Input Tokens (binned)", fontweight="bold")
    ax.set_ylabel("GPU Energy (binned)", fontweight="bold")
    ax.set_title(
        "GPU Energy - Prediction Error Heatmap", fontweight="bold", fontsize=13
    )

    # Output Tokens: Similar analysis
    ax = axes[1]
    token_errors = np.abs(
        sample_df["actual_output_tokens"] - sample_df["pred_output_tokens"]
    )
    energy_bins2 = pd.cut(sample_df["actual_gpu_energy_j"], bins=10)
    heatmap_data_tokens = (
        sample_df.groupby([energy_bins2, token_bins])
        .apply(lambda x: token_errors[x.index].mean())
        .unstack()
    )

    sns.heatmap(
        heatmap_data_tokens,
        cmap="RdYlGn_r",
        ax=ax,
        cbar_kws={"label": "Mean Absolute Error (tokens)"},
    )
    ax.set_xlabel("Input Tokens (binned)", fontweight="bold")
    ax.set_ylabel("GPU Energy (binned)", fontweight="bold")
    ax.set_title(
        "Output Tokens - Prediction Error Heatmap", fontweight="bold", fontsize=13
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


def plot_top_features(output_file="top_features.png"):
    """Extract and visualize top TF-IDF features."""
    df = load_data("assets/merged.parquet")
    cols = ["input_text", "input_tokens", "output_tokens", "gpu_energy_j"]
    df = df[cols].dropna()

    # Fit TF-IDF to get feature names
    tfidf = TfidfVectorizer(max_features=2000, ngram_range=(1, 2), stop_words="english")
    X_tfidf = tfidf.fit_transform(df["input_text"])

    # Get feature names
    feature_names = tfidf.get_feature_names_out()

    # Calculate mean TF-IDF scores for each feature
    mean_tfidf = np.asarray(X_tfidf.mean(axis=0)).ravel()

    # Get top 15 features
    top_indices = np.argsort(mean_tfidf)[-15:][::-1]
    top_features = feature_names[top_indices]
    top_scores = mean_tfidf[top_indices]

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.viridis(np.linspace(0, 1, len(top_features)))
    bars = ax.barh(
        range(len(top_features)),
        top_scores,
        color=colors,
        edgecolor="black",
        linewidth=1.5,
    )

    ax.set_yticks(range(len(top_features)))
    ax.set_yticklabels(top_features, fontsize=11, fontweight="bold")
    ax.set_xlabel("Mean TF-IDF Score", fontweight="bold", fontsize=12)
    ax.set_title("Top 15 Most Important Text Features", fontweight="bold", fontsize=14)
    ax.grid(alpha=0.3, axis="x")

    # Add value labels
    for i, (bar, score) in enumerate(zip(bars, top_scores)):
        ax.text(
            score + 0.001,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.4f}",
            va="center",
            fontsize=9,
            fontweight="bold",
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


def plot_correlation_with_energy(sample_df, output_file="correlation_energy.png"):
    """Show correlation between various input features and GPU energy."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create correlation features
    sample_df["error_energy"] = np.abs(
        sample_df["actual_gpu_energy_j"] - sample_df["pred_gpu_energy_j"]
    )
    sample_df["error_tokens"] = np.abs(
        sample_df["actual_output_tokens"] - sample_df["pred_output_tokens"]
    )
    sample_df["pred_accuracy_energy"] = 1 - (
        sample_df["error_energy"] / sample_df["actual_gpu_energy_j"].max()
    )

    # Correlation analysis
    corr_data = {
        "Input Tokens": sample_df["input_tokens"].corr(
            sample_df["actual_gpu_energy_j"]
        ),
        "Predicted Energy": sample_df["pred_gpu_energy_j"].corr(
            sample_df["actual_gpu_energy_j"]
        ),
        "Output Tokens": sample_df["actual_output_tokens"].corr(
            sample_df["actual_gpu_energy_j"]
        ),
    }

    features = list(corr_data.keys())
    correlations = list(corr_data.values())
    colors_corr = ["#FF6B6B" if x < 0.5 else "#4ECDC4" for x in correlations]

    bars = ax.bar(
        features,
        correlations,
        color=colors_corr,
        edgecolor="black",
        linewidth=2,
        width=0.6,
    )
    ax.set_ylabel("Correlation with GPU Energy", fontweight="bold", fontsize=12)
    ax.set_title(
        "Feature Correlations with Energy Consumption", fontweight="bold", fontsize=14
    )
    ax.set_ylim([0, 1])
    ax.grid(alpha=0.3, axis="y")

    # Add value labels
    for bar, corr in zip(bars, correlations):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.02,
            f"{corr:.3f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
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
    print("🎨 Generating advanced graphics...\n")

    # Load data
    print("Loading data...")
    df = load_data("assets/merged.parquet")
    pipe, sample_df = train_and_evaluate(df, test_size=0.2, random_state=0)

    print("\n📊 Creating advanced visualizations...")
    # Generate visualizations
    plot_metrics_card(sample_df)
    plot_prediction_accuracy_heatmap(sample_df)
    plot_top_features()
    plot_correlation_with_energy(sample_df)

    print(f"\n✨ Advanced graphics saved to {OUTPUT_DIR}/")
