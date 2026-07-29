"""
Reusable Plotly chart builders — kept separate from page files so the
same chart can be reused across Dashboard / Salary Insights pages without
duplicating styling code.
"""
import plotly.graph_objects as go


def role_probability_bar(role_probabilities: dict[str, float], top_n: int = 6) -> go.Figure:
    items = list(role_probabilities.items())[:top_n]
    labels = [k for k, _ in items]
    values = [v * 100 for _, v in items]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=values, colorscale="Tealgrn"),
        text=[f"{v:.1f}%" for v in values], textposition="outside",
    ))
    fig.update_layout(
        title="Role Probability",
        xaxis_title="Probability (%)",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
        template="plotly_dark",
    )
    return fig


def salary_range_chart(salary_min: float, salary_avg: float, salary_max: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Min", "Average", "Max"], y=[salary_min, salary_avg, salary_max],
        marker_color=["#4C9F70", "#2E86AB", "#F24236"],
        text=[f"{v:.1f} LPA" for v in [salary_min, salary_avg, salary_max]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Predicted Salary Range (LPA)",
        yaxis_title="Lakhs Per Annum",
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
        template="plotly_dark",
    )
    return fig


def skill_gap_donut(matching_count: int, missing_count: int) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=["Matching Skills", "Missing Skills"],
        values=[matching_count, missing_count],
        hole=0.55,
        marker=dict(colors=["#2E86AB", "#F24236"]),
    ))
    fig.update_layout(
        title="Skill Readiness",
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
        template="plotly_dark",
    )
    return fig


def ats_category_bar(category_scores: dict[str, int], max_scores: dict[str, int]) -> go.Figure:
    labels = list(category_scores.keys())
    values = [category_scores[k] for k in labels]
    maxes = [max_scores[k] for k in labels]
    pct = [round((v / m) * 100) if m else 0 for v, m in zip(values, maxes)]

    fig = go.Figure(go.Bar(
        x=[label.replace("_", " ").title() for label in labels], y=pct,
        marker_color="#2E86AB",
        text=[f"{v}/{m}" for v, m in zip(values, maxes)], textposition="outside",
    ))
    fig.update_layout(
        title="ATS Category Breakdown",
        yaxis_title="Score (%)", yaxis_range=[0, 110],
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
        template="plotly_dark",
    )
    return fig
