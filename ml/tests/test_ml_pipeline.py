"""
Tests for the ML pipeline itself — Phases 3-5 tested the trained models'
API endpoints extensively, but never the generation/feature-engineering
code that produces them. Worth covering since a broken generator would
silently produce a bad dataset that still "trains" without erroring.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))

from generate_dataset import N_PER_ROLE, ROLES, compute_salary, generate_dataset, sample_skills  # noqa: E402
from feature_engineering import fit_encoders, transform_features  # noqa: E402


def test_generate_dataset_has_expected_shape():
    df = generate_dataset()
    assert len(df) == N_PER_ROLE * len(ROLES)
    assert set(df["role"].unique()) == set(ROLES)
    assert df["role"].value_counts().nunique() == 1  # perfectly balanced


def test_generate_dataset_is_deterministic():
    # Same RANDOM_SEED should produce identical output on repeated runs —
    # important for reproducibility (anyone re-running this should get the
    # same dataset, same trained model, same reported metrics).
    df1 = generate_dataset()
    df2 = generate_dataset()
    assert df1.equals(df2)


def test_generate_dataset_salary_is_positive_and_bounded():
    df = generate_dataset()
    assert (df["salary_lpa"] > 0).all()
    assert df["salary_lpa"].max() < 100  # sanity bound — no runaway noise


def test_sample_skills_always_returns_at_least_three():
    for role in ROLES:
        for _ in range(20):  # sampling is random, check multiple draws
            skills = sample_skills(role)
            assert len(skills) >= 3


def test_compute_salary_higher_experience_increases_salary_on_average():
    # Not a strict monotonic guarantee per-record (there's noise), but the
    # average over many draws should clearly favor more experience.
    low_exp = [
        compute_salary("Data Scientist", 0, "Bachelors", 2, 0, "Tier-2", "Startup")
        for _ in range(200)
    ]
    high_exp = [
        compute_salary("Data Scientist", 10, "Bachelors", 2, 0, "Tier-2", "Startup")
        for _ in range(200)
    ]
    assert sum(high_exp) / len(high_exp) > sum(low_exp) / len(low_exp)


def test_feature_engineering_handles_unseen_category_gracefully():
    # transform_features must not crash on a category value the encoder
    # never saw during fit (handle_unknown="ignore" in the OneHotEncoder) —
    # this matters because real user input at inference time isn't
    # guaranteed to match the training data's exact category values.
    import pandas as pd

    train_df = pd.DataFrame([
        {"skills": "python|sql", "experience_years": 2, "education": "Bachelors",
         "num_projects": 3, "certifications": 1, "location_tier": "Tier-1", "company_type": "Startup"},
    ])
    encoders = fit_encoders(train_df)

    unseen_df = pd.DataFrame([
        {"skills": "python|sql|some_never_seen_skill", "experience_years": 2, "education": "Bachelors",
         "num_projects": 3, "certifications": 1, "location_tier": "Tier-3", "company_type": "Enterprise"},
    ])
    result = transform_features(unseen_df, encoders)
    assert len(result) == 1  # doesn't raise, produces a row
