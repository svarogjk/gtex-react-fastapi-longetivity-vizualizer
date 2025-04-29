# GTEx Gene Expression Survival Analysis

This module extends the GTEx gene expression visualization platform with survival analysis capabilities, enabling researchers to study relationships between gene expression levels and longevity outcomes.

## Overview

The survival analysis functionality integrates GTEx gene expression data with sample metadata (age, sex, cause of death) to identify gene expression patterns associated with survival outcomes. This approach is particularly valuable for longevity research as it connects molecular mechanisms with phenotypic outcomes.

### Key Features

- **Optimal Cutpoint Analysis**: Automatically identifies the gene expression threshold that maximizes survival differences between groups
- **Kaplan-Meier Survival Curves**: Visualizes survival probabilities for high vs. low expression groups
- **Cox Proportional Hazards Models**: Quantifies association between gene expression and survival with adjustment for covariates
- **Multi-gene Analysis**: Identifies significant longevity-related genes across sets of candidates

## Technical Implementation

The implementation creates an integrated dataset using:

1. **GTEx Gene Expression Data**: TPM values for genes across tissue samples
2. **GTEx Sample Metadata**: Age brackets, sex, and hardy scale (cause of death)
3. **Statistical Analysis**: Optimal cutpoint detection, Kaplan-Meier estimation, and Cox proportional hazards modeling

### Age Representation

Since GTEx only provides age brackets rather than exact ages, the system uses the median age of each bracket (e.g., "60-69" → 65 years).

### Caveats and Limitations

- **All samples are from deceased donors**: This means the analysis focuses on "time-to-death" rather than true longevity
- **Limited covariates**: The available metadata includes only basic demographic information
- **Cause of death confounding**: The analysis should adjust for hardy scale (cause of death) as it influences survival curves

## API Endpoints

### 1. Individual Gene Survival Analysis

```
GET /genes/{gene}/survival/{tissue}
```

Analyzes the relationship between a gene's expression and survival outcomes in a specific tissue.

#### Parameters:
- `gene` (path): Gene symbol (e.g., "FOXO3")
- `tissue` (path): Tissue type from GTEx (e.g., "Brain_Cortex")

#### Response:
```json
{
  "status": "success",
  "message": "Survival analysis completed for gene FOXO3 in Brain_Cortex",
  "data": {
    "metadata": {
      "gene": "FOXO3",
      "tissue": "Brain_Cortex",
      "sample_count": 96,
      "high_expr_count": 43,
      "low_expr_count": 53,
      "median_expression": 5.23,
      "cutpoint": {
        "value": 4.87,
        "type": "optimal",
        "high_expression_definition": "> 4.8700 TPM",
        "low_expression_definition": "≤ 4.8700 TPM",
        "percent_high": 44.8,
        "percent_low": 55.2
      }
    },
    "high_expression": {
      "survival_curve": [...],
      "median_survival": 68.5
    },
    "low_expression": {
      "survival_curve": [...],
      "median_survival": 62.3
    },
    "statistical_analysis": {
      "logrank_test": {
        "p_value": 0.032,
        "test_statistic": 4.58,
        "is_significant": true
      },
      "cox_models": {
        "continuous_expression": {
          "gene_expression_coef": -0.342,
          "gene_expression_p_value": 0.028,
          "gene_expression_hazard_ratio": 0.71,
          "gene_expression_is_significant": true,
          "covariates": {
            "sex_male": {
              "coef": 0.213,
              "p_value": 0.187,
              "hazard_ratio": 1.24
            },
            "hardy_numeric": {
              "coef": 0.548,
              "p_value": 0.003,
              "hazard_ratio": 1.73
            }
          },
          "model_quality": {
            "concordance": 0.68,
            "log_likelihood": -324.5,
            "aic": 655.0
          }
        },
        "binary_expression_group": {
          "high_expression_group_coef": -0.462,
          "high_expression_group_p_value": 0.023,
          "high_expression_group_hazard_ratio": 0.63,
          "high_expression_group_is_significant": true,
          "covariates": {...},
          "model_quality": {...}
        }
      }
    },
    "interpretation": "Higher expression of FOXO3 is significantly associated with improved survival outcomes."
  }
}
```

### 2. Gene Set Survival Analysis

```
GET /genes/survival/{tissue}
```

Analyzes multiple genes' expression and their relationships with survival outcomes in a specific tissue.

#### Parameters:
- `genes` (query): Comma-separated list of gene symbols
- `tissue` (path): Tissue type from GTEx

#### Response:
```json
{
  "status": "success",
  "message": "Survival analysis completed for 5 genes in Brain_Cortex",
  "data": {
    "gene_results": {
      "FOXO3": {...},
      "SIRT1": {...},
      "SIRT6": {...},
      "CDKN2A": {...},
      "TERT": {...}
    },
    "summary": {
      "total_genes_analyzed": 5,
      "successful_analyses": 5,
      "significant_genes": {
        "continuous_model": ["FOXO3", "SIRT1"],
        "continuous_count": 2,
        "binary_model": ["FOXO3", "SIRT1", "SIRT6"],
        "binary_count": 3
      },
      "functional_groups": {
        "protective_genes": ["FOXO3", "SIRT1"],
        "risk_genes": ["SIRT6"]
      },
      "cutpoints": {
        "FOXO3": {"value": 4.87, "type": "optimal"},
        "SIRT1": {"value": 5.23, "type": "optimal"},
        "SIRT6": {"value": 3.56, "type": "median"},
        "CDKN2A": {"value": 1.82, "type": "median"},
        "TERT": {"value": 0.95, "type": "median"}
      },
      "tissue": "Brain_Cortex"
    }
  }
}
```

## Understanding the Results

### Survival Curves

The Kaplan-Meier survival curves visualize the probability of survival over time for high vs. low expression groups. The key interpretation is:

- **Curve Separation**: Greater separation indicates stronger gene expression effect
- **Direction of Effect**: If high expression group shows better survival, the gene may be protective

### Cox Proportional Hazards Models

The Cox models quantify the relationship between gene expression and survival risk while adjusting for covariates:

- **Hazard Ratio (HR)**: 
  - HR < 1: Higher expression associated with DECREASED risk (better survival)
  - HR > 1: Higher expression associated with INCREASED risk (worse survival)

- **Coefficient (coef)**:
  - Negative coefficient: Protective effect
  - Positive coefficient: Risk effect

- **P-value**: Statistical significance of the effect (significant if < 0.05)

### Optimal Cutpoint vs. Median

The analysis first attempts to find an optimal cutpoint for stratifying patients by gene expression, rather than simply using the median. This is important because:

1. The biological effect may not occur at the median
2. The optimal cutpoint maximizes the statistical power to detect gene-survival associations
3. It may reveal threshold effects that are clinically meaningful

If no statistically significant optimal cutpoint is found, the system falls back to using the median value.

## Integration with the GTEx React Longevity Visualizer

This survival analysis functionality integrates with the existing GTEx React Longevity Visualizer, allowing researchers to:

1. Explore gene expression patterns across tissues
2. Identify longevity-related genes
3. Analyze survival outcomes associated with expression patterns
4. Visualize results through interactive charts

## Implementation Notes

### Handling GTEx Data Limitations

GTEx data comes with inherent limitations for survival analysis:

1. **No exact age information**: Only age brackets are available
2. **All donors are deceased**: No true censoring in the typical survival analysis sense
3. **Limited follow-up time**: No longitudinal data available

The implementation addresses these by:

- Using age brackets as a proxy for survival time
- Adjusting for cause of death via the hardy scale
- Focusing on relative comparisons rather than absolute survival times

### Statistical Considerations

The optimal cutpoint methodology requires careful interpretation:

1. **Multiple testing**: Looking for the optimal cutpoint involves testing multiple thresholds, which can increase Type I error
2. **Sample size**: Smaller tissues have limited sample sizes, reducing statistical power
3. **Validation**: Findings should ideally be validated in independent datasets

## Example Use Cases

1. **Identify tissue-specific longevity genes**: Compare survival effects of known longevity genes across tissues
2. **Screen candidate genes**: Test sets of candidate genes to prioritize for further research
3. **Understand gene-environment interactions**: Explore how tissue context modifies gene-survival associations
4. **Connect genotype to phenotype**: Bridge genetic longevity pathways with survival outcomes

## References

1. Fan J, et al. (2011). "Evaluation of methods for finding optimal gene expression thresholds in survival analysis." *BMC Medical Research Methodology*
2. Dinse GE, et al. (2000). "Improving long-term survival comparisons by minimizing variability in the beginning of follow-up." *Statistics in Medicine*
3. Liu X, et al. (2018). "Optimal cut-points for biomarkers: methods based on timing of events and the Cox model." *PLOS ONE*