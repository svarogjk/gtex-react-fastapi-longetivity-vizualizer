import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from lifelines import KaplanMeierFitter
import numpy as np
import json

# Configuration
API_BASE_URL = "http://localhost:8000"  # Adjust to match your FastAPI server
LONGEVITY_GENES = ["FOXO3", "SIRT1", "SIRT6", "CDKN2A", "KLOTHO", "TERT"]
TARGET_TISSUES = ["Brain_Cortex", "Heart_Left_Ventricle", "Liver", "Muscle_Skeletal"]


def fetch_gene_survival_analysis(gene, tissue):
    """Fetch survival analysis for a specific gene in a specific tissue"""
    url = f"{API_BASE_URL}/genes/{gene}/survival/{tissue}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching data for {gene} in {tissue}: {response.status_code}")
        print(response.text)
        return None


def fetch_gene_set_survival_analysis(genes, tissue):
    """Fetch survival analysis for multiple genes in a specific tissue"""
    url = f"{API_BASE_URL}/genes/survival/{tissue}"
    response = requests.get(url, params={"genes": ",".join(genes)})

    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching data for genes in {tissue}: {response.status_code}")
        print(response.text)
        return None


def plot_survival_curves(survival_data, gene, tissue, save_path=None):
    """Plot Kaplan-Meier survival curves from the API response"""
    # Create a new figure
    plt.figure(figsize=(10, 6))

    # Extract data for high and low expression groups
    high_expr_data = pd.DataFrame(survival_data["high_expression"]["survival_curve"])
    low_expr_data = pd.DataFrame(survival_data["low_expression"]["survival_curve"])

    # Create KM plot
    kmf = KaplanMeierFitter()

    # Plot high expression group
    kmf.fit(high_expr_data["time"], [1] * len(high_expr_data), label="High Expression")
    kmf.survival_function_ = high_expr_data.set_index("time")[["survival_probability"]]
    ax = kmf.plot(color="blue", ci_show=False)

    # Plot low expression group
    kmf.fit(low_expr_data["time"], [1] * len(low_expr_data), label="Low Expression")
    kmf.survival_function_ = low_expr_data.set_index("time")[["survival_probability"]]
    kmf.plot(ax=ax, color="red", ci_show=False)

    # Add statistical information
    p_value = survival_data["statistical_analysis"]["logrank_test"]["p_value"]
    hazard_ratio = survival_data["statistical_analysis"]["cox_models"][
        "continuous_expression"
    ]["gene_expression_hazard_ratio"]

    # Add cutpoint information
    cutpoint = survival_data["metadata"]["cutpoint"]["value"]
    cutpoint_type = survival_data["metadata"]["cutpoint"]["type"]

    # Annotate the plot
    plt.title(f"Survival Analysis of {gene} in {tissue.replace('_', ' ')}")
    plt.xlabel("Age (years)")
    plt.ylabel("Survival Probability")

    # Add a text box with statistical information
    textbox = (
        f"p-value: {p_value:.3f}\n"
        f"Hazard Ratio: {hazard_ratio:.2f}\n"
        f"Cutpoint: {cutpoint:.2f} ({cutpoint_type})\n"
        f"n={survival_data['metadata']['sample_count']} samples"
    )
    props = dict(boxstyle="round", facecolor="white", alpha=0.7)
    plt.text(
        0.05,
        0.05,
        textbox,
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment="bottom",
        bbox=props,
    )

    # Improve appearance
    plt.grid(alpha=0.3)
    plt.tight_layout()

    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Figure saved to {save_path}")

    plt.show()


def create_gene_tissue_heatmap(genes, tissues, save_path=None):
    """Create a heatmap of survival effects across genes and tissues"""
    # Initialize data structure
    data = {
        "gene": [],
        "tissue": [],
        "hazard_ratio": [],
        "p_value": [],
        "is_significant": [],
        "cutpoint_type": [],
    }

    # Fetch data for each gene-tissue combination
    for tissue in tissues:
        # Fetch all genes at once for this tissue
        result = fetch_gene_set_survival_analysis(genes, tissue)

        if result:
            # Process each gene's result
            for gene in genes:
                if (
                    gene in result["gene_results"]
                    and "error" not in result["gene_results"][gene]
                ):
                    gene_result = result["gene_results"][gene]

                    # Extract Cox model results
                    if (
                        "statistical_analysis" in gene_result
                        and "cox_models" in gene_result["statistical_analysis"]
                        and "continuous_expression"
                        in gene_result["statistical_analysis"]["cox_models"]
                    ):

                        cox_model = gene_result["statistical_analysis"]["cox_models"][
                            "continuous_expression"
                        ]

                        # Add to data
                        data["gene"].append(gene)
                        data["tissue"].append(tissue.replace("_", " "))
                        data["hazard_ratio"].append(
                            cox_model["gene_expression_hazard_ratio"]
                        )
                        data["p_value"].append(cox_model["gene_expression_p_value"])
                        data["is_significant"].append(
                            cox_model["gene_expression_is_significant"]
                        )
                        data["cutpoint_type"].append(
                            gene_result["metadata"]["cutpoint"]["type"]
                        )

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Transform for heatmap
    heatmap_data = df.pivot_table(index="gene", columns="tissue", values="hazard_ratio")

    # Create a mask for non-significant results
    sig_mask = df.pivot_table(index="gene", columns="tissue", values="is_significant")

    # Create the heatmap plot
    plt.figure(figsize=(12, 8))

    # Use a diverging colormap centered at 1.0 (neutral hazard ratio)
    cmap = sns.diverging_palette(220, 20, as_cmap=True)

    # Plot the heatmap
    ax = sns.heatmap(
        heatmap_data,
        annot=True,
        cmap=cmap,
        center=1.0,
        vmin=0.5,
        vmax=2.0,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"label": "Hazard Ratio (HR)"},
    )

    # Add markers for significance
    for i, gene in enumerate(heatmap_data.index):
        for j, tissue in enumerate(heatmap_data.columns):
            if sig_mask.loc[gene, tissue]:
                ax.add_patch(
                    plt.Rectangle((j, i), 1, 1, fill=False, edgecolor="black", lw=2)
                )

    # Add legend for significance
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="none", edgecolor="black", label="p < 0.05", linewidth=2)
    ]
    plt.legend(handles=legend_elements, loc="upper right", framealpha=0.7)

    plt.title("Gene Expression Hazard Ratios Across Tissues")
    plt.tight_layout()

    # Interpretation guide
    plt.figtext(
        0.5,
        0.01,
        "HR < 1: Higher expression associated with better survival (protective)\n"
        "HR > 1: Higher expression associated with worse survival (risk factor)",
        ha="center",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.7, "pad": 5},
    )

    # Save if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Heatmap saved to {save_path}")

    plt.show()

    return df


def summarize_longevity_genes(genes, tissues):
    """Summarize survival effects of longevity genes across tissues"""
    results = {}

    for tissue in tissues:
        tissue_result = fetch_gene_set_survival_analysis(genes, tissue)
        if tissue_result:
            results[tissue] = tissue_result

    # Extract protective and risk genes for each tissue
    tissue_summary = {}
    for tissue, result in results.items():
        if "summary" in result and "functional_groups" in result["summary"]:
            tissue_summary[tissue] = {
                "protective_genes": result["summary"]["functional_groups"][
                    "protective_genes"
                ],
                "risk_genes": result["summary"]["functional_groups"]["risk_genes"],
                "significant_count": len(
                    result["summary"]["significant_genes"]["continuous_model"]
                ),
            }

    # Count how many tissues each gene is significant in
    gene_counts = {gene: {"protective": 0, "risk": 0} for gene in genes}

    for tissue, summary in tissue_summary.items():
        for gene in summary["protective_genes"]:
            if gene in gene_counts:
                gene_counts[gene]["protective"] += 1

        for gene in summary["risk_genes"]:
            if gene in gene_counts:
                gene_counts[gene]["risk"] += 1

    # Print summary
    print("\n=== LONGEVITY GENE SURVIVAL ANALYSIS SUMMARY ===\n")
    print(f"Analyzed {len(genes)} genes across {len(tissues)} tissues\n")

    print("GENE EFFECTS BY TISSUE:")
    for tissue, summary in tissue_summary.items():
        print(f"\n{tissue.replace('_', ' ')}:")
        print(f"  Significant genes: {summary['significant_count']}")
        print(
            f"  Protective genes: {', '.join(summary['protective_genes']) if summary['protective_genes'] else 'None'}"
        )
        print(
            f"  Risk genes: {', '.join(summary['risk_genes']) if summary['risk_genes'] else 'None'}"
        )

    print("\nGENE CONSISTENCY ACROSS TISSUES:")
    for gene, counts in gene_counts.items():
        total = counts["protective"] + counts["risk"]
        if total > 0:
            consistency = max(counts["protective"], counts["risk"]) / total * 100
            effect = "protective" if counts["protective"] > counts["risk"] else "risk"
            print(
                f"  {gene}: Significant in {total}/{len(tissues)} tissues ({consistency:.0f}% consistent as {effect})"
            )
        else:
            print(f"  {gene}: Not significant in any tissue")

    return tissue_summary, gene_counts


# Main execution
if __name__ == "__main__":
    # Example 1: Analyze a single gene in a specific tissue
    print("Analyzing FOXO3 in Brain Cortex...")
    foxo3_brain = fetch_gene_survival_analysis("FOXO3", "Brain_Cortex")
    if foxo3_brain:
        plot_survival_curves(
            foxo3_brain, "FOXO3", "Brain_Cortex", "foxo3_brain_survival.png"
        )

        # Print interpretation
        print("\nInterpretation:")
        print(foxo3_brain["interpretation"])

        # Print cutpoint information
        cutpoint = foxo3_brain["metadata"]["cutpoint"]
        print(f"\nCutpoint: {cutpoint['value']:.2f} TPM ({cutpoint['type']})")
        print(f"High expression: {cutpoint['high_expression_definition']}")
        print(f"Low expression: {cutpoint['low_expression_definition']}")

    # Example 2: Create a heatmap of survival effects across genes and tissues
    print("\nCreating heatmap of survival effects...")
    survival_data = create_gene_tissue_heatmap(
        LONGEVITY_GENES, TARGET_TISSUES, "longevity_gene_heatmap.png"
    )

    # Example 3: Summarize longevity genes across tissues
    print("\nSummarizing longevity gene effects...")
    tissue_summary, gene_counts = summarize_longevity_genes(
        LONGEVITY_GENES, TARGET_TISSUES
    )
