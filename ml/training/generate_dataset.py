"""
Synthetic career dataset generator.

Generates candidate records for 14 job roles with:
- Skills sampled from each role's core + overlap pool (creates realistic
  ambiguity between adjacent roles — e.g. Data Scientist vs Data Analyst)
- Experience/education/projects/certifications
- Location tier + company type
- A salary computed from an explicit, explainable formula + noise

Run: python generate_dataset.py
Output: ../datasets/career_dataset_synthetic.csv
"""
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 42
N_PER_ROLE = 2000

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "datasets" / "career_dataset_synthetic.csv"

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

with open(DATA_DIR / "role_skill_map.json", encoding="utf-8") as f:
    ROLE_SKILL_MAP = json.load(f)["roles"]

ROLES = list(ROLE_SKILL_MAP.keys())

EDUCATION_LEVELS = ["Bachelors", "Masters", "PhD"]
EDUCATION_WEIGHTS = [0.65, 0.30, 0.05]
EDUCATION_SALARY_BONUS = {"Bachelors": 0.0, "Masters": 1.2, "PhD": 2.5}  # LPA bonus

LOCATION_TIERS = ["Tier-1", "Tier-2", "Tier-3"]
LOCATION_WEIGHTS = [0.50, 0.35, 0.15]
LOCATION_MULTIPLIER = {"Tier-1": 1.15, "Tier-2": 1.0, "Tier-3": 0.85}

COMPANY_TYPES = ["Startup", "Product-based", "Service-based", "Enterprise"]
COMPANY_WEIGHTS = [0.25, 0.30, 0.30, 0.15]
COMPANY_MULTIPLIER = {"Startup": 1.05, "Product-based": 1.20, "Service-based": 0.90, "Enterprise": 1.05}

# Base salary (LPA) at ~0 years experience, and per-year growth rate, per role.
# These are deliberately rough approximations of real Indian tech-market
# ranges, not scraped figures — good enough to make the regression problem
# realistic without claiming false precision.
ROLE_SALARY_PARAMS = {
    "Data Scientist":          {"base": 7.0,  "growth": 1.6},
    "Machine Learning Engineer": {"base": 8.0,  "growth": 1.8},
    "Data Analyst":            {"base": 5.0,  "growth": 1.0},
    "AI Engineer":             {"base": 9.0,  "growth": 1.9},
    "Software Engineer":       {"base": 6.0,  "growth": 1.2},
    "Backend Developer":       {"base": 6.0,  "growth": 1.2},
    "Frontend Developer":      {"base": 5.5,  "growth": 1.1},
    "Full Stack Developer":    {"base": 6.0,  "growth": 1.25},
    "Cloud Engineer":          {"base": 7.0,  "growth": 1.5},
    "Cybersecurity Analyst":   {"base": 6.0,  "growth": 1.4},
    "Business Analyst":        {"base": 5.0,  "growth": 1.0},
    "Product Manager":         {"base": 9.5,  "growth": 2.0},
    "UI/UX Designer":          {"base": 5.0,  "growth": 1.0},
    "DevOps Engineer":         {"base": 7.0,  "growth": 1.5},
}


def sample_skills(role: str) -> list[str]:
    core = ROLE_SKILL_MAP[role]["core_skills"]
    overlap = ROLE_SKILL_MAP[role]["overlap_pool"]

    # Each core skill appears with high probability (a real candidate in
    # this role usually — but not always — lists most of the core skills).
    chosen = [s for s in core if random.random() < 0.75]
    if len(chosen) < 3:  # guarantee a minimally plausible resume
        chosen = random.sample(core, k=min(3, len(core)))

    # A handful of overlap skills sneak in too — this is what makes roles
    # genuinely hard to distinguish sometimes, same as in real resumes.
    n_overlap = random.randint(0, min(3, len(overlap)))
    chosen += random.sample(overlap, k=n_overlap)

    return sorted(set(chosen))


def sample_experience_years() -> float:
    # Skewed toward junior candidates (0-5 yrs), long tail to 15.
    return float(round(np.clip(np.random.exponential(scale=3.0), 0, 15), 1))


def compute_salary(role: str, experience: float, education: str, num_projects: int,
                    certifications: int, location_tier: str, company_type: str) -> float:
    params = ROLE_SALARY_PARAMS[role]
    salary = params["base"] + params["growth"] * experience
    salary += EDUCATION_SALARY_BONUS[education]
    salary += 0.15 * num_projects
    salary += 0.25 * certifications
    salary *= LOCATION_MULTIPLIER[location_tier]
    salary *= COMPANY_MULTIPLIER[company_type]
    salary *= np.random.normal(loc=1.0, scale=0.08)  # +/- realistic market noise
    return round(max(salary, 2.5), 2)  # floor so noise can't produce a negative/absurd salary


def generate_record(role: str) -> dict:
    experience = sample_experience_years()
    education = random.choices(EDUCATION_LEVELS, weights=EDUCATION_WEIGHTS, k=1)[0]
    num_projects = int(np.random.poisson(lam=3) + 1)
    certifications = int(np.random.poisson(lam=1))
    location_tier = random.choices(LOCATION_TIERS, weights=LOCATION_WEIGHTS, k=1)[0]
    company_type = random.choices(COMPANY_TYPES, weights=COMPANY_WEIGHTS, k=1)[0]
    skills = sample_skills(role)

    salary = compute_salary(role, experience, education, num_projects, certifications,
                             location_tier, company_type)

    return {
        "role": role,
        "experience_years": experience,
        "education": education,
        "num_projects": num_projects,
        "certifications": certifications,
        "location_tier": location_tier,
        "company_type": company_type,
        "skills": "|".join(skills),
        "salary_lpa": salary,
    }


def generate_dataset() -> pd.DataFrame:
    # Reseed HERE, not just once at module import — otherwise a second call
    # to this function within the same process continues from wherever the
    # RNG state was left, silently breaking the "same seed -> same dataset"
    # reproducibility guarantee. Found by a test that called this twice.
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    records = [generate_record(role) for role in ROLES for _ in range(N_PER_ROLE)]
    df = pd.DataFrame(records)
    return df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)  # shuffle rows


if __name__ == "__main__":
    df = generate_dataset()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Generated {len(df)} records -> {OUTPUT_PATH}")
    print(df["role"].value_counts())
    print(df[["experience_years", "salary_lpa"]].describe())
