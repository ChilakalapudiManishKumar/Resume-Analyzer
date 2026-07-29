"""
Consolidated evaluation report: pulls together both training runs'
comparison CSVs and prints feature importances for the winning models,
so you can explain WHY each model predicts what it predicts — not just
that it does.

Run this AFTER both train_role_classifier.py and train_salary_regressor.py.
"""
from pathlib import Path

import joblib
import pandas as pd

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


import numpy as np


def top_feature_importances(model, feature_names: list[str], top_n: int = 12) -> pd.DataFrame:
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        # Multi-class Logistic Regression has one coefficient row per class;
        # average the absolute coefficient across classes as an overall
        # "how much does this feature move the decision" measure.
        importances = np.abs(model.coef_).mean(axis=0)
    else:
        return pd.DataFrame({"note": ["Model exposes neither feature_importances_ nor coef_."]})

    df = pd.DataFrame({"feature": feature_names, "importance": importances})
    return df.sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)


def main():
    print("=" * 60)
    print("ROLE CLASSIFICATION — model comparison")
    print("=" * 60)
    role_results = pd.read_csv(ARTIFACTS_DIR / "role_model_comparison.csv")
    print(role_results.sort_values("macro_f1", ascending=False).to_string(index=False))

    role_model = joblib.load(ARTIFACTS_DIR / "role_classifier.joblib")
    role_features = joblib.load(ARTIFACTS_DIR / "role_feature_columns.joblib")
    print("\nTop features driving role prediction:")
    print(top_feature_importances(role_model, role_features).to_string(index=False))

    print("\n" + "=" * 60)
    print("SALARY REGRESSION — model comparison")
    print("=" * 60)
    salary_results = pd.read_csv(ARTIFACTS_DIR / "salary_model_comparison.csv")
    print(salary_results.sort_values("r2", ascending=False).to_string(index=False))

    salary_model = joblib.load(ARTIFACTS_DIR / "salary_regressor.joblib")
    salary_features = joblib.load(ARTIFACTS_DIR / "salary_feature_columns.joblib")
    print("\nTop features driving salary prediction:")
    print(top_feature_importances(salary_model, salary_features).to_string(index=False))


if __name__ == "__main__":
    main()
