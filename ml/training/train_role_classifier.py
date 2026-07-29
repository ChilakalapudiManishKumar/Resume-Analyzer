"""
Train + compare job-role classifiers.

Models compared: Logistic Regression (linear baseline), Random Forest,
XGBoost. We pick the best by macro-F1 (not accuracy) because we have 14
balanced classes but some roles are intentionally harder to separate
(e.g. Data Scientist vs Data Analyst) — macro-F1 penalizes a model that
does well on "easy" roles but silently fails on the hard ones, which
plain accuracy would hide.

Run: python train_role_classifier.py
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from feature_engineering import ARTIFACTS_DIR, fit_encoders, save_encoders, transform_features

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "career_dataset_synthetic.csv"
RANDOM_SEED = 42


def load_and_split():
    df = pd.read_csv(DATASET_PATH)
    train_df, test_df = train_test_split(
        df, test_size=0.2, random_state=RANDOM_SEED, stratify=df["role"]
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def main():
    train_df, test_df = load_and_split()

    # Fit encoders on TRAIN ONLY — fitting on the full dataset (including
    # test rows) would leak test-set information into the encoding, which
    # would make the evaluation numbers optimistic and wrong.
    encoders = fit_encoders(train_df)
    X_train = transform_features(train_df, encoders)
    X_test = transform_features(test_df, encoders)

    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(train_df["role"])
    y_test = label_encoder.transform(test_df["role"])

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=2000, random_state=RANDOM_SEED),
        "RandomForest": RandomForestClassifier(n_estimators=300, max_depth=12, random_state=RANDOM_SEED),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            eval_metric="mlogloss", random_state=RANDOM_SEED,
        ),
    }

    results = []
    best_name, best_model, best_f1 = None, None, -1.0

    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        macro_f1 = f1_score(y_test, preds, average="macro")
        results.append({"model": name, "accuracy": round(acc, 4), "macro_f1": round(macro_f1, 4)})
        print(f"\n=== {name} ===")
        print(f"Accuracy: {acc:.4f}  |  Macro F1: {macro_f1:.4f}")

        if macro_f1 > best_f1:
            best_name, best_model, best_f1 = name, model, macro_f1

    print("\n" + "=" * 50)
    print("MODEL COMPARISON")
    print(pd.DataFrame(results).sort_values("macro_f1", ascending=False).to_string(index=False))
    print(f"\nBest model: {best_name} (macro F1 = {best_f1:.4f})")

    print(f"\nDetailed classification report for best model ({best_name}):")
    best_preds = best_model.predict(X_test)
    print(classification_report(y_test, best_preds, target_names=label_encoder.classes_))

    # Persist everything needed to reproduce predictions at inference time.
    save_encoders(encoders)
    joblib.dump(label_encoder, ARTIFACTS_DIR / "role_label_encoder.joblib")
    joblib.dump(best_model, ARTIFACTS_DIR / "role_classifier.joblib")
    joblib.dump(list(X_train.columns), ARTIFACTS_DIR / "role_feature_columns.joblib")
    pd.DataFrame(results).to_csv(ARTIFACTS_DIR / "role_model_comparison.csv", index=False)
    print(f"\nSaved best model + encoders to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
