"""
Train + compare salary regressors.

Models compared: Linear Regression (baseline), Random Forest Regressor,
XGBoost Regressor. Picked by R² (variance explained) plus RMSE/MAE shown
for interpretability — RMSE is in the same units as salary (LPA), so it's
directly readable as "the model is typically off by about X lakhs".

Run: python train_salary_regressor.py
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from feature_engineering import ARTIFACTS_DIR, fit_encoders, save_encoders, transform_features

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "career_dataset_synthetic.csv"
RANDOM_SEED = 42


def load_and_split():
    df = pd.read_csv(DATASET_PATH)
    return train_test_split(df, test_size=0.2, random_state=RANDOM_SEED)


def main():
    train_df, test_df = load_and_split()
    train_df = train_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    encoders = fit_encoders(train_df)
    X_train = transform_features(train_df, encoders)
    X_test = transform_features(test_df, encoders)
    y_train = train_df["salary_lpa"].values
    y_test = test_df["salary_lpa"].values

    candidates = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=300, max_depth=12, random_state=RANDOM_SEED),
        "XGBoost": XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1, random_state=RANDOM_SEED),
    }

    results = []
    best_name, best_model, best_r2 = None, None, -np.inf

    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))
        results.append({"model": name, "rmse_lpa": round(rmse, 3), "mae_lpa": round(mae, 3), "r2": round(r2, 4)})
        print(f"\n=== {name} ===")
        print(f"RMSE: {rmse:.3f} LPA  |  MAE: {mae:.3f} LPA  |  R2: {r2:.4f}")

        if r2 > best_r2:
            best_name, best_model, best_r2 = name, model, r2

    print("\n" + "=" * 50)
    print("MODEL COMPARISON")
    print(pd.DataFrame(results).sort_values("r2", ascending=False).to_string(index=False))
    print(f"\nBest model: {best_name} (R2 = {best_r2:.4f})")

    save_encoders(encoders, filename="salary_feature_encoders.joblib")
    joblib.dump(best_model, ARTIFACTS_DIR / "salary_regressor.joblib")
    joblib.dump(list(X_train.columns), ARTIFACTS_DIR / "salary_feature_columns.joblib")
    pd.DataFrame(results).to_csv(ARTIFACTS_DIR / "salary_model_comparison.csv", index=False)
    print(f"\nSaved best model + encoders to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
