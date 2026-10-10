---
title: Braşov or Brașov? 41 LLMs spell my city right, until you spell it wrong first
published: true
tags: devchallenge, kagglechallenge, ai, machinelearning
cover_image: https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/cover.png
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

Look at these two words:

> **Braşov**   **Brașov**

One of them is the name of the city I live in. The other is a 1990s encoding workaround that never went away. You probably can't tell which is which. Language models can. Type the wrong one, though, and about a third of their answers hand it back.

**TL;DR**

- **41 models: 99 % clean answers when I typed Brașov, 68 % when I typed Braşov.** They spot the wrong letter when asked, then copy it anyway: 91 % of the wrong words came straight from my input. Typed with no diacritics at all, the same text comes back fixed (96 %).
- **Upgrades can make it worse.** On the same prompts, Claude Opus 4.8 kept 95 % of its answers clean and Opus 5 56 %; Sonnet 4.6 95 % and Sonnet 5 58 %. Gemini Flash got slowly better.
- **One sentence in the system prompt gets it to 94 %, and breaks Turkish**, where ş is the right letter: with "never write ş", 5 of 5 models got Turkish replies wrong, most often by switching to Romanian.
- **Outside Romanian, my prediction failed.** English text with Cyrillic look-alike letters came back clean; mojibake didn't. The cedilla seems to be special because the web is full of it.
- **What changed for me:** I stopped expecting the model to clean up my input. I normalize before and after.

![They spot the cedilla and still copy it](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-gap.png)

## What I Benchmarked

Romanian has two letters with a mark underneath, **ș** and **ț**, and the mark is a comma (U+0219, U+021B). The encodings Romanian computers used in the 1990s, ISO 8859-2 and Windows-1250, didn't have them, so we typed the Turkish **ş** and a **ţ** with a cedilla instead (U+015F, U+0163). Unicode added the right letters in 1999.

I assumed that was history, so I counted. On 30 September I fetched the front pages of 35 Romanian sites: national and Brașov news, the government, the National Bank, my city hall, the rail operator, four shops and Wikipedia. **29 of them still had cedilla letters in Romanian words**, and on 12 more than one in ten ș/ț letters was the wrong one. The government publishes an "INFORMAŢIE DE PRESĂ"; one financial daily is 93 % cedilla.

To a computer these are different characters. `"Brașov" == "Braşov"` is `false`, and `grep`, a SQL query with a binary collation, most site search boxes, deduplication and URL slugs all treat them as two words. It's also the text models are trained on, and the text retrieval systems feed them.

So my question was: **do language models write the right letter, and what do they do when the text they read has the wrong one?**

- **Every input comes in pairs** that are identical except for the code points of ș and ț.
- **No LLM judge.** Scores come from Unicode code points after NFC normalization; I checked the answer keys as a native speaker.
- **The scorer was tested first**, against nine fake models with known behaviour: a model that copies its input scores 0 % on the main task, one that normalizes everything 100 %.
- **Predictions first.** For the second round I wrote my predictions into each task's description on Kaggle before running it. Two of them failed.

Here is one of the 22 prompts, typed four ways, and Claude Opus 5.5's four answers. The question was where the festival took place and when next year's tickets go on sale:

| My text was typed | Claude Opus 5.5 answered |
| --- | --- |
| correctly (ș ț) | Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie. |
| with cedillas (ş ţ) | Festivalul a avut loc la **Sighişoara**, iar biletele pentru **ediţia** de anul viitor se vor pune în vânzare în decembrie. |
| without diacritics | Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie. |
| with cedillas, plus one rule | Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie. |

Four answers you can't tell apart, one of them wrong. The bold words are the ones with the cedilla.

{% details The twelve tasks %}

| # | Task | What it asks |
| --- | --- | --- |
| 1 | Write | English prompt, ASCII names: does the Romanian answer use ș/ț? |
| 2 | Echo | Reply, summarize or answer from text typed correctly or with cedillas |
| 3 | Fix | "Proofread this" vs "correct the diacritics" vs an explicit instruction |
| 4 | See | Same characters? Any cedilla here? Which code point? |
| 5 | Restore | Diacritics where only context decides (*peste* / *pește*) |
| 6 | Code | Write `fix_romanian(text)`; 14 hidden tests |
| 7 | Echo + rule | Echo's cedilla inputs plus one system-prompt sentence |
| 8 | Echo, four inputs | Correct, cedilla, no diacritics, cedilla + rule; every model |
| 9 | Contagion | Four documents; some of the others typed with cedillas |
| 10 | Turkish guests | Turkish, where ş is correct, under three rules |
| 11 | Other look-alikes | English with Cyrillic look-alikes or mojibake |
| 12 | Turns | Does a cedilla first text infect the second summary? |

{% enddetails %}

## Models Tested

**41 models in two rounds.** Round one (30 September – 1 October): 15 models, tasks 1–7. Round two (8–11 October): task 8 on every model Kaggle would serve, and tasks 9–12 on 5 of them. Kaggle also lists Grok 4.5 and Grok 4.6, but every call to them came back "model not found".

I picked the lineup to answer two questions. Is this getting better? Six versions of Claude Opus, six of Gemini Flash and five generations of GPT, on identical prompts. Does thinking help? Grok 4.20 and Qwen 3 Next both come with and without reasoning.

{% details Full model list %}

**Anthropic:** Claude Haiku 4.5, Claude Opus 4.5, Claude Opus 4.6, Claude Opus 4.7, Claude Opus 4.8, Claude Opus 5.5, Claude Opus 5, Claude Sonnet 4.5, Claude Sonnet 4.6, Claude Sonnet 5.5, Claude Sonnet 5. **Google:** Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 3 Flash, Gemini 3.1 Flash-Lite, Gemini 3.5 Flash, Gemini 3.5 Flash-Lite, Gemini 3.6 Flash, Gemini 3.7 Flash, Gemma 4 26B A4B, Gemma 4 31B. **OpenAI:** GPT-5.4, GPT-5.4 mini, GPT-5.4 nano, GPT-5.5, GPT-5.6 Luna, GPT-5.6 Sol, GPT-5.6 Terra, GPT-6 Luna, GPT-6 Sol, GPT-6.1 Sol, gpt-oss-120b, gpt-oss-20b. **xAI:** Grok 4.20 Non-Reasoning, Grok 4.20 Reasoning. **DeepSeek:** DeepSeek-R1. **Alibaba:** Qwen 3 235B, Qwen 3 Coder 480B, Qwen 3 Next 80B Instruct, Qwen 3 Next 80B Thinking. **Zhipu:** GLM-5.

{% enddetails %}

Everything ran on Kaggle's model proxy with its defaults, output capped at 8,192 tokens. Most models run at their provider's default temperature there, so I repeated runs where I could; every interval in this post resamples the prompts. The whole thing cost $21.16 of Kaggle's free quota.

## Findings

### 1. They spot the cedilla and still copy it

The chart at the top puts four first-round tasks side by side for the same 15 models. From an English prompt, they write ș and ț correctly (98 % of answers). Shown a sentence typed with cedillas and asked whether it has any, every model says yes, and it says no to clean sentences 97 % of the time. Told to "correct the spelling and the diacritics", 99 % of answers repair every letter. Then, given text typed with cedillas to reply to, summarize or answer questions from, only 64 % come out right.

Grok 4.20 is the clearest case: 100 %, 100 % and 100 % on the first three, 44 % on the fourth.

Two numbers complicate the picture. Asked only to "proofread this", 79 % of answers repaired every letter (71 of 90). And shown two identical strings containing ș or ş, the models called them the same only 66 % of the time (59 of 90), against 93 % for plain pairs like "Sibiu" and "Sibiu": the letter alone makes some models answer "different". If I had only tested pairs that really differ, I'd have concluded that they see perfectly. They do notice the letter. Unless asked, they leave it, and they never mention it: not one of the 1066 second-round answers to cedilla input said a word about the letters, neither the 726 that fixed them nor the 340 that copied them. How well a model spots the cedilla also tells you nothing about how often it copies it (rank correlation 0.06 across the 15 first-round models).

### 2. 41 models, the same 22 prompts

![Clean in, clean out. Cedilla in, cedilla out.](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-echo44.png)

Typed correctly, the 22 prompts came back right in 99 % of answers. Typed with cedillas, 68 %, and every model slipped at least once. Claude Opus 4.8, Claude Sonnet 4.6, GPT-5.6 Sol kept 95 % clean; Grok 4.20 Reasoning, 43 %. With 22 prompts per run the intervals are wide, so read the middle of the chart as a crowd, not a ranking.

The task mattered about as much as the model. Replying to a guest, models write their own sentences and keep the letters right (96 % with cedilla input). Summarizing a news paragraph (67 %) and answering a question from a document (52 %), they reuse the source's words, and its bytes with them. Of the 1099 cedilla words in all answers, **91 % were copied verbatim from the input**, 3 % were inflected forms of input words, and 6 % were words the model chose itself, like *îndrumaţi* ("directed") in this first-round summary from Claude Opus 5:

> Primăria **Braşov** **anunţă** închiderea **Pieţei** Sfatului pentru traficul auto în weekend, între orele 8 **şi** 20, din cauza târgului de toamnă. **Şoferii** sunt **îndrumaţi** să parcheze pe strada **Mureşenilor** sau lângă Gara **Braşov**.
>
> (Bold: a word with a cedilla letter. The source had "Piaţa", not "Pieţei", and no "îndrumaţi" at all.)

So it isn't only copying: once an answer goes cedilla, the model's own words usually follow. In 32 of 41 models, most failing answers are cedilla from the first word to the last. In the second round, Claude Opus 4.6 and GPT-5.6 Luna made exactly the same move as Opus 5: they rephrased the notice's "rugați" ("asked") as "îndrumaţi", cedilla included.

And some models don't need a bad input at all: the two gpt-oss models put a cedilla into 10 of 59 answers to correctly typed text.

### 3. A missing letter gets fixed. A wrong one gets copied.

![What gets repaired and what gets copied](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-lookright.png)

Most Romanians type without diacritics at all ("Brasov"), so I gave the models the same 22 prompts that way too. A model that simply mirrored my style would answer without diacritics. They don't: 96 % of answers came back fully corrected, and only 3.0 % of the source's ș/ț words stayed bare. With cedillas, 28 % of those words kept the wrong letter. My guess: to a model, a bare s looks like a typo, and a cedilla looks like a real letter.

One model shows its reasoning, and it agrees. DeepSeek-R1 writes out its thinking before it answers. In 88 answers to cedilla input it mentioned the letters only 3 times, and one of those was a final check that protected the wrong one:

> Final check: county name spelled "Timiş" with ş, not "Timis". Must preserve diacritics in response.

With the rule in the prompt, its reasoning named the problem in 43 of 44 answers, and 6 of those still came out with cedillas. In one, it planned to write "proper Romanian orthography with ș/ț commas below, not cedillas", then answered: "Autorităţile recomandă turiştilor să verifice starea drumului înainte de plecare."

I expected the same to hold outside Romanian, and wrote it down: in English text, letters that only look Latin (Cyrillic а, е, о inside "Zürich") would be copied, and mojibake ("ZÃ¼rich"), which looks broken, would be repaired. I was wrong. Across 5 models, Cyrillic look-alikes came back in only 5 % of answers, whether they filled every word or sat only in the names. Mojibake was repaired in 100 % of summaries but copied into 37 % of the answers that quoted the document. Gemini 3.7 Flash, asked who owns the café: "CafÃ© MÃ¼ller in KÃ¶ln is closing, and it is owned by JosÃ© FernÃ¡ndez."

What the cedilla and mojibake have in common is that both are all over the real web; Cyrillic letters inside Latin words are not. So my best guess now is that models keep a spelling they have seen used for real and repair one they rarely see. That's a hypothesis for a next round, not a result of this one.

### 4. [pending: F4_HEAD]

![Does the cedilla spread to text that was typed correctly?](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-spread.png)

[pending: FINDING4]

### 5. Upgrades can make it worse

![Claude dropped at version 5. Gemini Flash crept up.](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-lines.png)

Kaggle serves several versions of the same models, so I could check whether newer means better. Before running anything, I wrote down that it wouldn't: newer versions would copy at least as often as older ones.

It's messier than that. Gemini Flash improved slowly, from 55 % clean answers (2.5) to 76 % (3.7). Claude improved through the 4.x versions and then fell back: Sonnet 4.6 kept 95 % clean, Sonnet 5 58 %; Opus 4.8 95 %, Opus 5 56 %. GPT-5.6 Sol kept 95 %, GPT-6 Sol 64 %, GPT-6.1 Sol 55 %. GPT Luna went the other way, from 64 % to 89 %.

How much of that is noise? Rerunning the same model on the same prompts moved its score by up to 18 points (median 5). Of 17 upgrades, 4 moved more than chance would at p < 0.05, 3 for the worse and 1 for the better; Claude Opus 4.8 → Opus 5 (-40 points) and Claude Sonnet 4.6 → Sonnet 5 (-38 points) survive a correction for 17 tests. Reasoning didn't help: Grok 4.20 kept 43 % with it and 45 % without. In another entry, [Precedent vs Spec](https://dev.to/finn_mead_feb2e66f91b0c9d/the-header-says-10-the-table-says-8-most-frontier-models-quietly-went-with-the-table-bdn), the same Grok switch flipped the result; here it changed nothing, which makes copying the encoding look like a habit rather than a decision. (Qwen 3 Next's Thinking model mostly ran out of tokens before answering, so its numbers rest on 11 prompts.)

If you depend on a behaviour like this, rerun your test on every upgrade.

### 6. The fix, and the fix for the fix

![One sentence fixes Romanian. Scoped, it spares most of the Turkish.](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-fix.png)

One sentence in the system prompt, *"Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them."*, lifts clean answers on cedilla input from 68 % to 94 %. Not every model listens equally: gpt-oss-20b (53 %), gpt-oss-120b (59 %), Qwen 3 Next 80B Instruct (61 %) and Grok 4.20 Non-Reasoning (73 %) stayed below 80 % even with the rule.

Then I remembered where the cedilla came from. It's the Turkish letter, and in Turkish it's correct. A guesthouse bot in Brașov gets Turkish guests too, so I sent the same system prompt eight messages in Turkish (5 models). Without the rule, 100 % of replies were correct Turkish. With "never write ş", 65 % were, and the rest went wrong in three different ways:

- **18 % slipped into Romanian.** The rule mentions Romanian, so some models started answering the Turkish guest in Romanian.
- **10 % avoided the letter**, rephrasing around every word that needs it.
- **8 % spelled Turkish with the Romanian letter.** Gemini 3.7 Flash, offering a honeymoon room: "balayınız için **muhteșem** dağ manzaralı … **Șarap** tadımı için…".

5 of the 5 models broke at least one Turkish reply. Scoping the rule ("this applies to Romanian only; other languages keep their own letters") brought correct Turkish back to 88 % and kept Romanian at 97 %, but 3 models still slipped. (I scored these by the language of each sentence and checked every flagged word by hand; Romanian place names like Brașov don't count against a Turkish reply.)

The same thing happens in code. Asked for `fix_romanian(text)`, almost every model wrote the obvious translation table, which would break every ş in a Turkish name, and which misses decomposed letters (an `s` followed by a combining cedilla, as some PDFs and macOS file names produce): 23 of 30 programs failed that test. When my prompt named the four wrong letters, 1 of 15 programs passed everything; when it only described the goal, 6 of 15 did. That's one program per model and prompt (McNemar p = 0.06), so it's a hint, not a result: the more precisely I described the bug, the narrower the fix.

### My predictions, scored

I wrote these into the task descriptions on Kaggle before running Round 2.

| Task | Prediction | Result | |
| --- | --- | --- | --- |
| 8 | Correct input stays near 100 % for every model. | lowest: gpt-oss-120b, 82 % | **failed** |
| 8 | Cedilla input fails far more often than input without diacritics. | 96 % vs 68 % clean answers | held |
| 8 | Newer versions in a family copy the cedilla at least as often as older ones. | no overall trend (rank correlation -0.18, p = 0.55); of 17 upgrades, 3 got worse and 1 better (p < 0.05) | held |
| 8 | The one-sentence rule lifts cedilla input to at least 90 % for most models. | 34 of 41 models at 90 % or more | held |
| 10 | Without a rule, Turkish replies keep ş. | 100 % kept it | held |
| 10 | Task 7's rule makes some models write Turkish with the Romanian comma letter. | 4 of 5 models did | held |
| 10 | The scoped rule keeps Turkish intact and still fixes Romanian. | Turkish 85 %, Romanian 97 % | **failed** |
| 11 | Correct English input stays near 100 %. | 100 % | held |
| 11 | Cyrillic look-alikes are copied far more often than mojibake. | clean answers: 93 % with look-alikes in the names, 82 % with mojibake | **failed** |
| 11 | The models that copy the Romanian cedilla most also copy the look-alikes most. | rank correlation +0.11 over 5 models | **failed** |
| 12 | A cedilla first text infects some clean second summaries, mostly after a cedilla first summary. | 7 % infected; 22 % when the first summary was itself in cedilla | held |
| 12 | A clean first text does not protect a cedilla second text much. | 77 % clean after a clean first text, 63 % on its own (task 8 summaries) | held |

### What went wrong

- **My upload.** The Kaggle CLI reads task files with the system encoding, which on my Windows laptop is cp1250, so my first task file would have uploaded "Brașov" as "BraČ™ov". The task files are now pure ASCII and check a SHA-256 of their data before running.
- **My census.** Romanian Wikipedia's front page had exactly one "cedilla" letter, in *Tolışi*, the Talysh language's name for itself, where ş is correct. I've taken it out of the count.
- **My first fix.** The `fix_romanian()` in the first version of this post breaks Turkish, the same way the one-sentence rule does.
- **A model that thought too long.** Qwen 3 Next Thinking hit the 8,192-token cap on most prompts and returned nothing visible; those prompts are left out, not counted as failures.

### What changed in how I think about these models

I went in expecting a knowledge test, and the models passed it. What I hadn't thought about is that the text I hand a model is also a style sample, encoding included, and the model follows that sample most closely when it summarizes or answers from my text, which is what retrieval does all day. Another entry in this challenge, [Asked in Dutch, sent to an English menu](https://dev.to/dsiacci/asked-in-dutch-sent-to-an-english-menu-48m4), found the same habit one level up: answers named the menu label of whatever page the model was given, not the reader's. And the behaviour isn't stable: it moved by 20 to 40 points between versions of the same model, in both directions.

So I fix it in code, before the text reaches the model and again after, and only for Romanian text. To see whether your own content has the problem, `grep -rn '[şŞţŢ]' .` is enough. To fix it:

```python
import unicodedata

CEDILLA_TO_COMMA = str.maketrans("şŞţŢ", "șȘțȚ")

def fix_romanian(text: str) -> str:
    # Romanian text only: in Turkish, Azerbaijani or Talysh, ş is the right letter.
    # NFC first, so "s" + combining cedilla becomes "ş" and then "ș".
    return unicodedata.normalize("NFC", text).translate(CEDILLA_TO_COMMA)
```

### What I'd measure next

- **Where the habit comes from.** In OpenAI's o200k tokenizer both letters are single tokens (ş is token 981, ș is 3591), so it isn't the cedilla breaking into bytes. With open-weight models I could check whether copying follows how often each spelling appeared in training.
- **People.** I said you probably can't tell the two apart. I'd like to measure that the same way the models were measured.

{% details All the numbers (the 15 first-round models) %}

Echo with cedilla is the mean of every run on the same prompts (tasks 2 and 8). Fix and See are task totals, so they include the harder probes left out of the chart at the top.

| Model | Write | Echo: cedilla | Echo: no diacritics | Echo + rule | Fix | See | Restore | Code |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 3 235B | 92 | 85 | 100 | 93 | 89 | 89 | 90 | 61 |
| Gemini 3.1 Pro | 100 | 82 | – | 100 | 100 | 97 | 100 | 86 |
| Gemini 3.7 Flash | 100 | 76 | 100 | 100 | 100 | 97 | 100 | 86 |
| Gemini 3.8 Flash | 100 | 71 | – | 100 | 100 | 81 | 100 | 93 |
| DeepSeek-R1 | 96 | 69 | 95 | 86 | 83 | 83 | 93 | 86 |
| Gemini 3.5 Flash-Lite | 100 | 67 | 91 | 100 | 89 | 83 | 90 | 93 |
| GPT-5.5 | 100 | 66 | 100 | 100 | 100 | 100 | 100 | 93 |
| Gemma 4 31B | 100 | 65 | 95 | 100 | 89 | 89 | 90 | 64 |
| Claude Sonnet 5 | 100 | 58 | 91 | 95 | 72 | 83 | 100 | 86 |
| GPT-5.4 nano | 96 | 58 | 100 | 82 | 83 | 83 | 90 | 93 |
| Claude Opus 5 | 100 | 56 | 100 | 100 | 100 | 81 | 100 | 100 |
| GPT-6 Astra | 100 | 55 | – | 100 | 100 | 100 | 100 | 93 |
| GLM-5 | 100 | 52 | 82 | 100 | 94 | 94 | 100 | 86 |
| Claude Haiku 4.5 | 92 | 47 | 73 | 91 | 89 | 72 | 93 | 86 |
| Grok 4.20 Reasoning | 100 | 43 | 82 | 100 | 83 | 97 | 87 | 86 |

{% enddetails %}

## My Benchmark

**Romanian Comma Below on Kaggle:** [kaggle.com/benchmarks/danielbutnar/romanian-comma-below](https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below)

Twelve tasks, all public, with every model answer in the run outputs. The code that builds the tasks, the fake models that test the scorer, the census, the analysis with its intervals, the charts, and a script that re-checks every number in this post against the raw results are on GitHub: [github.com/danielbutnar/comma-below](https://github.com/danielbutnar/comma-below).
