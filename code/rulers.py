#!/usr/bin/env python3
"""Five ways to measure the same 246 tasks.

    python3 rulers.py /path/to/data_complete.csv [results.json]

Data: METR, "Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer
Productivity" (arXiv 2507.09089), anonymized release at
https://github.com/METR/Measuring-Early-2025-AI-on-Exp-OSS-Devs (data_complete.csv).

Everything is expressed as the change in completion time caused by (or attributed to)
AI: -0.24 means "24% less time", +0.19 means "19% more time".
"""
import json
import sys

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

SEED = 20261006


def load(path):
    d = pd.read_csv(path)
    # METR's imputation: missing post-review time = mean of the task's own arm (regression.py)
    m = {t: d[(d.ai_treatment == t) & d.post_review_implementation_time.notna()].post_review_implementation_time.mean()
         for t in (0, 1)}
    d["post"] = d.post_review_implementation_time.fillna(d.ai_treatment.map(m))
    d["total"] = d.initial_implementation_time + d["post"]
    d["log_time"] = np.log(d.total)
    d["log_est"] = np.log(d.predicted_time_no_ai)
    d["gain"] = d.predicted_time_ai_allowed / d.predicted_time_no_ai - 1     # forecast change, per issue
    return d


def effect(d, formula="log_time ~ ai_treatment + log_est"):
    """Change in completion time and its 95% CI, from a log-linear regression (METR's specification)."""
    r = smf.ols(formula, d).fit()
    lo, hi = r.conf_int().loc["ai_treatment"]
    return {"estimate": float(np.exp(r.params.ai_treatment) - 1), "lo": float(np.exp(lo) - 1), "hi": float(np.exp(hi) - 1),
            "p": float(r.pvalues.ai_treatment), "resid_sd": float(np.sqrt(r.scale)), "r2": float(r.rsquared), "n": int(r.nobs)}


def naive(d):
    """What a dashboard shows: mean minutes per task, AI tasks against the rest. No adjustment."""
    a, b = d[d.ai_treatment == 1].total, d[d.ai_treatment == 0].total
    return {"change": float(a.mean() / b.mean() - 1), "mean_ai": float(a.mean()), "mean_no_ai": float(b.mean()),
            "n_ai": int(len(a)), "n_no_ai": int(len(b))}


def self_selected(d, rule):
    """Turn the randomized data into what you would observe if developers picked where to use AI.

    From the AI arm keep only tasks the rule says a developer WOULD have used AI on; from the
    no-AI arm keep only the tasks the rule says they would NOT. Every row is still a real task
    with its real time; only the mix of tasks on each side changes.
    """
    short = d.predicted_time_no_ai <= d.predicted_time_no_ai.median()        # ties go to "short"
    use_ai = {"largest_expected_gain": d.gain <= d.gain.median(),            # gain is negative: lower = bigger cut
              "short_tasks": short, "long_tasks": ~short}[rule]
    obs = d[((d.ai_treatment == 1) & use_ai) | ((d.ai_treatment == 0) & ~use_ai)]
    return {"rule": rule, **naive(obs), "tasks_used": int(len(obs)), "adjusted": effect(obs)["estimate"]}


def pilots(d, sizes=(20, 30, 40, 60, 80, 120, 160, 246), reps=4000):
    """Resample pilots of n tasks (with replacement) and ask what each would have concluded."""
    rng = np.random.default_rng(SEED)
    X = np.column_stack([np.ones(len(d)), d.ai_treatment.to_numpy(), d.log_est.to_numpy()])
    y = d.log_time.to_numpy()
    out = []
    for n in sizes:
        est, sig = [], []
        while len(est) < reps:
            i = rng.integers(0, len(d), n)
            Xi, yi = X[i], y[i]
            if Xi[:, 1].min() == Xi[:, 1].max():
                continue                                   # a pilot with a single arm estimates nothing
            beta, res, rank, _ = np.linalg.lstsq(Xi, yi, rcond=None)
            if rank < 3:
                continue
            resid = yi - Xi @ beta
            cov = (resid @ resid / (n - 3)) * np.linalg.inv(Xi.T @ Xi)
            t = beta[1] / np.sqrt(cov[1, 1])
            est.append(np.exp(beta[1]) - 1)
            sig.append(abs(t) > stats.t.ppf(0.975, n - 3))
        est, sig = np.array(est), np.array(sig)
        out.append({"n": n, "says_ai_is_faster": float((est < 0).mean()),
                    "significant_slower": float(((est > 0) & sig).mean()), "significant_faster": float(((est < 0) & sig).mean()),
                    "inconclusive": float((~sig).mean()),
                    "p10": float(np.quantile(est, 0.10)), "median": float(np.median(est)), "p90": float(np.quantile(est, 0.90))})
    return out


def tasks_needed(resid_sd, change, power=0.80, alpha=0.05):
    """Tasks per arm for a two-sided test to detect `change` in completion time."""
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return int(np.ceil(2 * z ** 2 * resid_sd ** 2 / np.log(1 + change) ** 2))


def main(path):
    d = load(path)
    core, raw = effect(d), effect(d, "log_time ~ ai_treatment")
    R = {"tasks": len(d), "developers": int(d.dev_id.nunique()), "tasks_ai": int(d.ai_treatment.sum()),
         "randomized_with_estimate": core, "randomized_without_estimate": raw, "dashboard_on_randomized_data": naive(d)}

    # Ruler 1: ask people. The forecast both times was given BEFORE the coin flip, for every issue.
    R["forecast"] = {
        "change_ratio_of_sums": float(d.predicted_time_ai_allowed.sum() / d.predicted_time_no_ai.sum() - 1),
        "change_geometric": float(np.exp(np.log(1 + d.gain).mean()) - 1),
        "issues_forecast_faster": float((d.gain < 0).mean()), "issues_forecast_equal": float((d.gain == 0).mean()),
        "issues_forecast_slower": float((d.gain > 0).mean()),
        "per_developer": sorted(float(g.predicted_time_ai_allowed.sum() / g.predicted_time_no_ai.sum() - 1) for _, g in d.groupby("dev_id")),
    }
    # How good are the same people at forecasting their own time?
    R["calibration"] = {}
    for arm, col in ((0, "predicted_time_no_ai"), (1, "predicted_time_ai_allowed")):
        s = d[d.ai_treatment == arm]
        R["calibration"]["ai" if arm else "no_ai"] = {
            "actual_over_forecast": float(s.total.sum() / s[col].sum()),
            "corr_log": float(np.corrcoef(np.log(s.total), np.log(s[col]))[0, 1]), "n": int(len(s))}

    # Ruler 2: the dashboard, with developers choosing where AI goes.
    R["self_selected"] = [self_selected(d, r) for r in ("largest_expected_gain", "short_tasks", "long_tasks")]
    med = d.predicted_time_no_ai.median()
    R["ties"] = {"median_forecast_minutes": float(med), "tasks_at_the_median": int((d.predicted_time_no_ai == med).sum()),
                 "median_gain": float(d.gain.median()), "tasks_at_the_median_gain": int((d.gain == d.gain.median()).sum())}
    # the same two rules with the tied tasks sent to the other side: how much do the numbers move?
    strict = d.predicted_time_no_ai < med
    alt = {}
    for name, use_ai in (("short_tasks", strict), ("long_tasks", ~strict)):
        alt[name] = naive(d[((d.ai_treatment == 1) & use_ai) | ((d.ai_treatment == 0) & ~use_ai)])["change"]
    R["ties"]["with_ties_on_the_long_side"] = alt

    # Rework: time spent after review, only where it was recorded.
    s = d[d.post_review_implementation_time.notna()]
    a, b = s[s.ai_treatment == 1].post_review_implementation_time, s[s.ai_treatment == 0].post_review_implementation_time
    rng = np.random.default_rng(SEED)
    boot = [rng.choice(a, len(a)).mean() / rng.choice(b, len(b)).mean() - 1 for _ in range(10000)]
    R["rework"] = {"mean_ai": float(a.mean()), "mean_no_ai": float(b.mean()), "change": float(a.mean() / b.mean() - 1),
                   "boot_lo": float(np.quantile(boot, 0.025)), "boot_hi": float(np.quantile(boot, 0.975)),
                   "median_ai": float(a.median()), "median_no_ai": float(b.median()),
                   "any_ai": float((a > 0).mean()), "any_no_ai": float((b > 0).mean()),
                   "mannwhitney_p": float(stats.mannwhitneyu(a, b).pvalue), "n_ai": int(len(a)), "n_no_ai": int(len(b)),
                   "share_of_total_ai": float(d[d.ai_treatment == 1].post.sum() / d[d.ai_treatment == 1].total.sum()),
                   "share_of_total_no_ai": float(d[d.ai_treatment == 0].post.sum() / d[d.ai_treatment == 0].total.sum())}

    # One person at a time.
    per = []
    for dev, g in d.groupby("dev_id"):
        if g.ai_treatment.nunique() == 2 and len(g) >= 8:
            e = effect(g)
            per.append({"n": int(len(g)), "estimate": e["estimate"], "lo": e["lo"], "hi": e["hi"],
                        "forecast": float(g.predicted_time_ai_allowed.sum() / g.predicted_time_no_ai.sum() - 1)})
    per.sort(key=lambda r: r["estimate"])
    R["per_developer"] = {"rows": per, "developers": len(per), "slower": sum(r["estimate"] > 0 for r in per),
                          "ci_excludes_zero": sum(r["lo"] > 0 or r["hi"] < 0 for r in per),
                          "min_tasks": min(r["n"] for r in per), "max_tasks": max(r["n"] for r in per)}

    R["pilots"] = pilots(d)
    R["tasks_needed_per_arm"] = {
        f"{int(c * 100)}%": {"with_estimate": tasks_needed(core["resid_sd"], c), "without_estimate": tasks_needed(raw["resid_sd"], c)}
        for c in (0.05, 0.10, 0.20, 0.30)}
    R["variance_removed_by_estimate"] = 1 - (core["resid_sd"] / raw["resid_sd"]) ** 2
    R["hours"] = {"total": float(d.total.sum() / 60), "mean_task_minutes": float(d.total.mean()), "median_task_minutes": float(d.total.median())}
    return R


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    R = main(sys.argv[1])
    if len(sys.argv) > 2:
        json.dump(R, open(sys.argv[2], "w"), indent=1)
    print(json.dumps({k: v for k, v in R.items() if k != "per_developer"}, indent=1))
    print(json.dumps({k: v for k, v in R["per_developer"].items() if k != "rows"}))
