# Publishing checklist

The deadline is 11 October 2026, 23:59 PDT (12 October, 09:59 in Romania). About 30 minutes in all.

## 1. Merge into main (5 minutes)

The write-up loads its images from `main`, and GitHub Pages serves the human test and the checker from `main`,
so this comes first.

1. Open https://github.com/danielbutnar/comma-below.
2. If a yellow banner says the branch "had recent pushes", click **Compare & pull request**. Otherwise click
   **Pull requests**, then **New pull request**, set **base: main** and **compare:** the branch with these changes.
3. Click **Create pull request**, then **Merge pull request**, then **Confirm merge**.
4. Open the **Actions** tab and wait until the newest **pages build and deployment** run has a green check
   (one or two minutes).
5. Check that these load:
   - https://danielbutnar.github.io/comma-below/human/test.html
   - https://danielbutnar.github.io/comma-below/post/checker.html
   - https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-hero-v2.png

## 2. DEV: edit the existing post (10 minutes)

**Never create a new post.** One submission per participant, and the reactions on the existing post break
ties. The address keeps its old "15-llms" slug after the edit; that is fine.

1. Open https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/post-v3-dev.md, press Ctrl+A,
   then Ctrl+C.
2. Open https://dev.to/danielbutnar/brasov-or-brasov-15-llms-spell-my-city-right-until-you-spell-it-wrong-first-75a/edit
3. Click into the editor, press Ctrl+A, then Ctrl+V. The text starts with the `---` front matter (title, tags,
   cover); keep it. (If the editor shows separate title, tag and cover fields instead, fill them from the front
   matter and paste only the text below its second `---`.)
4. Click **Preview** and check:
   - the cedilla checker renders (a box titled "Does your model copy the cedilla?");
   - every image loads: the cover and each chart;
   - the five collapsed sections (details) open.
5. Click **Save changes**.
6. Open the post in a private window: the new title and cover show, and the tags still include
   `kagglechallenge`.

## 3. Kaggle: descriptions (15 minutes)

1. Benchmark: open https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below, edit the description,
   and paste all of
   https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/kaggle-description-v2.md
2. Tasks: open https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/kaggle-task-descriptions.md.
   For each of the 13 tasks, open the link under its heading, edit the task's Description, and paste its block
   from "Part of **Comma Below**" down to the "Code:" line.
3. If you have two minutes: open the version history of tasks 10 and 11 and check that version 1 shows the
   same predictions as version 2. Their notes say the predictions are unchanged.
4. In a private window, open the benchmark and two or three tasks: they must be public and show the new text.

## Don't

- **Don't create a new DEV post** (see step 2).
- **Don't push or run tasks on Kaggle** (`kaggle b t push`, `kaggle b t run`). A new version changes the code
  under the leaderboard and the dated text that holds the predictions, and `tasks/*.py` here must keep matching
  what produced the leaderboard. The fixes wait in `docs/next-version.md`.
- **Don't run `analysis/check_claims.py --values` from a clone without the run traces** (`results/raw/**/*.run.json`,
  only on the laptop). DeepSeek-R1's reasoning numbers and the cost need them. The script now keeps the
  committed values when the traces are missing, but nothing needs recomputing to publish: the committed
  `results/post_values.json` is what the post was checked against. If you do run it, `git diff
  results/post_values.json` must show no change before you commit.
- **Don't delete or move the images in `post/`.** DEV and the cover load them from `main`.
