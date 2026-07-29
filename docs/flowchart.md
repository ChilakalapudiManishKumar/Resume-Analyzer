# User Flowchart

```mermaid
flowchart TD
    START([User opens app]) --> AUTH{Logged in?}
    AUTH -->|No| REGLOGIN[Register or Log in]
    REGLOGIN --> AUTH
    AUTH -->|Yes| UPLOAD[Resume Upload page]

    UPLOAD --> PARSE[Backend parses PDF/DOCX/TXT<br/>extracts name, email, phone, skills]
    PARSE --> REVIEW[User reviews extracted fields]
    REVIEW --> MANUAL[User fills in: experience, education,<br/>projects, certifications, location, company type]
    MANUAL --> GENERATE[Generate Prediction + ATS Score]

    GENERATE --> ML[ML: role classifier + salary regressor]
    GENERATE --> ATS[Rule-based ATS scorer]

    ML --> DASHBOARD[Dashboard: ATS score, predicted role,<br/>salary range, charts]
    ATS --> DASHBOARD

    DASHBOARD --> SKILLGAP[Skill Gap page:<br/>pick a target role, see missing skills]
    SKILLGAP --> ROADMAP[Roadmap page:<br/>learning resources per missing skill]
    DASHBOARD --> SALARY[Salary Insights page:<br/>detailed range + explanation]
    DASHBOARD --> INTERVIEW[Interview Prep page:<br/>Q&A by category for predicted/chosen role]

    style START fill:#2E86AB,color:#fff
    style DASHBOARD fill:#4C9F70,color:#fff
```

## Notes
- Dashboard depends on having uploaded a resume and generated at least one prediction — the frontend's page ordering (`1_Resume_Upload` before `2_Dashboard`) reflects this dependency, adjusted from the Phase 1 plan's listed order for better UX.
- Skill Gap, Roadmap, and Interview Prep can each be revisited with a *different* target role than the one predicted — the prediction suggests a role, it doesn't lock the user into it.
