# Five rulers on the same 246 tasks

Code and results for the article on measuring productivity with AI. The dataset is not
included; it is METR's public release.

## Data

METR, "Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity"
(arXiv 2507.09089). Anonymized task-level data:
https://github.com/METR/Measuring-Early-2025-AI-on-Exp-OSS-Devs (`data_complete.csv`,
commit 7ff2d76 used here).

## Run

```bash
pip install pandas numpy scipy statsmodels matplotlib graphviz playwright
git clone https://github.com/METR/Measuring-Early-2025-AI-on-Exp-OSS-Devs
python3 code/rulers.py Measuring-Early-2025-AI-on-Exp-OSS-Devs/data_complete.csv results/rulers.json
python3 code/figs.py en      # or pt; needs the Graphviz binary
python3 code/tables.py en    # needs a Chromium for Playwright
```

`rulers.py` takes about five seconds. Everything is expressed as the change in completion
time attributed to AI: −0.24 is 24% less time, +0.19 is 19% more.

## What it computes

| Key in `results/rulers.json` | What it is |
| --- | --- |
| `forecast` | what the developers predicted before the coin flip, per task |
| `calibration` | actual time over forecast time, with and without AI |
| `self_selected` | the dashboard comparison when a rule, not a coin, decides where AI goes |
| `randomized_without_estimate`, `randomized_with_estimate` | the two regressions; the second is METR's specification |
| `per_developer` | one regression per developer with at least 8 tasks in both arms |
| `pilots` | 4,000 resampled pilots per size and what each would have concluded |
| `tasks_needed_per_arm` | sample size for 80% power at several effect sizes |
| `rework` | post-review time by arm, with a bootstrap interval |

To use your own data, the core regression needs four columns: who did the work, the
estimate written down beforehand, whether the coin flip allowed AI, and how long it took.
