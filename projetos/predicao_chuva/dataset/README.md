# Rain Narrowcasting Benchmark Dataset

## Overview

Satellite communication links experience signal degradation due to rainfall, atmospheric absorption, and other propagation effects. This dataset is designed as a benchmark for **rain narrowcasting**: the task of estimating instantaneous rainfall intensity directly from satellite communication telemetry.

The dataset is generated using **RainCast**, a physics-based satellite communication simulator that combines realistic orbital propagation with ITU-R atmospheric propagation models. It provides an ML-ready benchmark where all features have already been extracted and organized, allowing researchers to focus on model development rather than data preparation. (RainCast: https://github.com/Satyanshgaur/RainCast.git )

Unlike the general-purpose **Satellite Link Performance Time Series Dataset**, this benchmark is specifically designed for supervised machine learning and reproducible evaluation.

---

# Machine Learning Tasks

The benchmark supports two complementary prediction tasks.

## 1. Rain Detection (Binary Classification)

Determine whether rainfall is occurring.

**Target**

```text
rain_event
```

Classes:

- `0` → No Rain
- `1` → Rain

This provides a straightforward benchmark for rain event detection before tackling rainfall estimation.

---

## 2. Rain Rate Estimation (Regression)

Estimate the instantaneous rainfall intensity.

**Target**

```text
rain_rate_mm_per_hr
```

Units:

- **mm/h**

This is the primary benchmark task.

---

# Dataset Split

The dataset is pre-divided into training, validation, and testing subsets.

Temporal ordering is preserved to prevent data leakage and better represent real-world deployment scenarios.

| File | Purpose |
|------|---------|
| `train.parquet` | Training set (70%) |
| `validation.parquet` | Hyperparameter tuning (15%) |
| `test.parquet` | Final evaluation (15%) |

Each split contains the complete feature set described in `column_dictionary.csv`.

---

# Feature Design

The benchmark is intended to approximate the information available to a real satellite communication operator.

Included features include:

- Received SNR
- Carrier frequency
- Elevation angle
- Slant range
- Excess attenuation
- Effective propagation path length
- Rolling statistical features
- Frequency-aware propagation coefficients
- Station metadata

These features enable models to learn the relationship between observed link degradation and underlying rainfall.

---

# Operational Feature Set

To ensure realistic evaluation, the benchmark intentionally excludes simulator internal state variables that would reveal the target directly.

For example, variables such as:

- Ground-truth rain attenuation
- Standalone scintillation loss
- Other internal propagation components unavailable to an operational receiver

are **not provided as model inputs**.

Instead, models must infer rainfall from realistic signal observables, mirroring the constraints faced in operational satellite communication systems.

---

# Folder Structure

```text
rain-narrowcasting-dataset/
│
├── README.md
├── LICENSE
├── metadata.json
├── column_dictionary.csv
│
├── train.parquet
├── validation.parquet
├── test.parquet
│
├── feature_description.csv
├── baseline_metrics.json
│
└── sample_plots/
    ├── rain_distribution.png
    ├── feature_importance.png
    ├── attenuation_vs_rain.png
    ├── train_test_split.png
    └── stageB_vs_stageC.png
```

---

# Included Files

### train.parquet

Training dataset used for model development.

---

### validation.parquet

Validation dataset intended for hyperparameter tuning and model selection.

---

### test.parquet

Held-out evaluation dataset used to benchmark model performance.

---

### feature_description.csv

Detailed description of every feature, including:

- data type
- units
- physical meaning
- benchmark stage

---

### column_dictionary.csv

Complete schema of every column contained in the dataset.

---

### metadata.json

Machine-readable metadata describing:

- simulation parameters
- dataset version
- satellite catalog
- station information
- generation settings
- benchmark configuration

---

### baseline_metrics.json

Reference performance obtained using the baseline models supplied with the project.

---

### sample_plots/

Example visualizations illustrating the benchmark data distribution and characteristics.

---

# Baseline Models

The benchmark includes machine-readable baseline results for three reference approaches.

| Model | Task |
|--------|------|
| Analytical Inverse | Rain Rate Regression |
| XGBoost Classifier | Rain Detection |
| XGBoost Regressor | Rain Rate Estimation |

Complete evaluation metrics are provided in `baseline_metrics.json`.

---

# Evaluation Protocol

Researchers are encouraged to evaluate new models using the provided train/validation/test split.

The primary evaluation metrics are:

- RMSE
- MAE
- R² Score
- F1 Score (Rain Detection)

Using the provided split ensures that published results remain directly comparable across different models.

---

# Applications

The dataset is suitable for:

- Rain narrowcasting
- Satellite communication research
- Machine learning benchmarking
- Time-series regression
- Signal processing
- RF propagation analysis
- Feature engineering research
- Physics-informed machine learning
- Educational demonstrations

---

# Citation

If you use this dataset in academic work, please cite the **RainCast** project and this dataset release. (RainCast: https://github.com/Satyanshgaur/RainCast.git )

The benchmark is intended to serve as an open resource for reproducible research in satellite communications, atmospheric propagation, and machine learning.

---

# License

This dataset is distributed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

You are free to share, modify, and build upon the dataset, provided appropriate attribution is given.

For the complete license text, see the included `LICENSE` file or visit:

https://creativecommons.org/licenses/by/4.0/
