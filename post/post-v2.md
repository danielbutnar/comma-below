---
title: Braşov or Brașov? {{N_MODELS}} LLMs spell my city right, until you spell it wrong first
published: true
tags: devchallenge, kagglechallenge, ai, machinelearning
cover_image: COVER_URL
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

Look at these two words:

> **Braşov**   **Brașov**

One of them is the name of the city I live in. The other is a 1990s encoding workaround that never went away. You probably can't tell which is which. Language models can. Type the wrong one, though, and about a third of their answers hand it back.

**TL;DR**

- **{{N_MODELS}} models: {{E4_CLEAN}} % clean answers when I typed Brașov, {{E4_CED}} % when I typed Braşov.** They spot the wrong letter when asked, then copy it anyway: {{E4_COPY_EXACT}} % of the wrong words came straight from my input. Typed with no diacritics at all, the same text comes back fixed ({{E4_ASCII}} %).
- **Upgrades can make it worse.** On the same prompts, Claude Opus 4.8 kept {{V_OPUS_48}} % of its answers clean and Opus 5 {{V_OPUS_5}} %; Sonnet 4.6 {{V_SONNET_46}} % and Sonnet 5 {{V_SONNET_5}} %. Gemini Flash got slowly better.
- **One sentence in the system prompt gets it to {{E4_RULE}} %, and breaks Turkish**, where ş is the right letter: with "never write ş", {{N_TR_BROKE}} of {{N_TR_MODELS}} models got Turkish replies wrong, most often by switching to Romanian.
- **Outside Romanian, my prediction failed.** English text with Cyrillic look-alike letters came back clean; mojibake didn't. The cedilla seems to be special because the web is full of it.
- **What changed for me:** I stopped expecting the model to clean up my input. I normalize before and after.

![They spot the cedilla and still copy it](CHART_GAP_URL)

## What I Benchmarked

Romanian has two letters with a mark underneath, **ș** and **ț**, and the mark is a comma (U+0219, U+021B). The encodings Romanian computers used in the 1990s, ISO 8859-2 and Windows-1250, didn't have them, so we typed the Turkish **ş** and a **ţ** with a cedilla instead (U+015F, U+0163). Unicode added the right letters in 1999.

I assumed that was history, so I counted. On 30 September I fetched the front pages of 35 Romanian sites: national and Brașov news, the government, the National Bank, my city hall, the rail operator, four shops and Wikipedia. **{{CENSUS_WITH}} of them still had cedilla letters in Romanian words**, and on {{CENSUS_10}} more than one in ten ș/ț letters was the wrong one. The government publishes an "INFORMAŢIE DE PRESĂ"; one financial daily is {{CENSUS_MAX}} % cedilla.

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

**{{N_MODELS}} models in two rounds.** Round one (30 September – 1 October): 15 models, tasks 1–7. Round two (8–11 October): task 8 on every model Kaggle would serve, and tasks 9–12 on {{N_R2_SMALL}} of them. Kaggle also lists Grok 4.5 and Grok 4.6, but every call to them came back "model not found".

I picked the lineup to answer two questions. Is this getting better? Six versions of Claude Opus, six of Gemini Flash and five generations of GPT, on identical prompts. Does thinking help? Grok 4.20 and Qwen 3 Next both come with and without reasoning.

{% details Full model list %}

{{MODELS_LINE}}

{% enddetails %}

Everything ran on Kaggle's model proxy with its defaults, output capped at 8,192 tokens. Most models run at their provider's default temperature there, so I repeated runs where I could; every interval in this post resamples the prompts. The whole thing cost ${{COST}} of Kaggle's free quota.

## Findings

### 1. They spot the cedilla and still copy it

The chart at the top puts four first-round tasks side by side for the same 15 models. From an English prompt, they write ș and ț correctly ({{R1_WRITE}} % of answers). Shown a sentence typed with cedillas and asked whether it has any, every model says yes, and it says no to clean sentences {{R1_SEE_CLEAN}} % of the time. Told to "correct the spelling and the diacritics", {{R1_FIX_L2}} % of answers repair every letter. Then, given text typed with cedillas to reply to, summarize or answer questions from, only {{R1_ECHO_CED}} % come out right.

Grok 4.20 is the clearest case: {{GROK_W}} %, {{GROK_SEE}} % and {{GROK_FIX}} % on the first three, {{GROK_ECHO}} % on the fourth.

Two numbers complicate the picture. Asked only to "proofread this", {{R1_PROOF}} % of answers repaired every letter ({{R1_PROOF_K}} of {{R1_PROOF_N}}). And shown two identical strings containing ș or ş, the models called them the same only {{R1_IDENT_PCT}} % of the time ({{R1_IDENT_SAME}} of {{R1_IDENT_N}}), against {{R1_ASCII_PCT}} % for plain pairs like "Sibiu" and "Sibiu": the letter alone makes some models answer "different". If I had only tested pairs that really differ, I'd have concluded that they see perfectly. They do notice the letter. Unless asked, they leave it, and they never mention it: not one of the {{N_CED_ANSWERS}} second-round answers to cedilla input said a word about the letters, neither the {{N_CED_FIXED}} that fixed them nor the {{N_CED_COPIED}} that copied them. How well a model spots the cedilla also tells you nothing about how often it copies it (rank correlation {{SPOT_COPY_RHO}} across the 15 first-round models).

### 2. {{N_MODELS}} models, the same 22 prompts

![Clean in, clean out. Cedilla in, cedilla out.](CHART_ECHO44_URL)

Typed correctly, the 22 prompts came back right in {{E4_CLEAN}} % of answers. Typed with cedillas, {{E4_CED}} %, and every model slipped at least once. {{TOP_NAMES}} kept {{TOP_SCORE}} % clean; {{E4_MIN_NAME}}, {{E4_MIN}} %. With 22 prompts per run the intervals are wide, so read the middle of the chart as a crowd, not a ranking.

The task mattered about as much as the model. Replying to a guest, models write their own sentences and keep the letters right ({{E4_REPLY}} % with cedilla input). Summarizing a news paragraph ({{E4_SUMMARY}} %) and answering a question from a document ({{E4_RAG}} %), they reuse the source's words, and its bytes with them. Of the {{E4_CED_WORDS}} cedilla words in all answers, **{{E4_COPY_EXACT}} % were copied verbatim from the input**, {{E4_COPY_INFL}} % were inflected forms of input words, and {{E4_COPY_NEW}} % were words the model chose itself, like *îndrumaţi* ("directed") in this first-round summary from Claude Opus 5:

> Primăria **Braşov** **anunţă** închiderea **Pieţei** Sfatului pentru traficul auto în weekend, între orele 8 **şi** 20, din cauza târgului de toamnă. **Şoferii** sunt **îndrumaţi** să parcheze pe strada **Mureşenilor** sau lângă Gara **Braşov**.
>
> (Bold: a word with a cedilla letter. The source had "Piaţa", not "Pieţei", and no "îndrumaţi" at all.)

So it isn't only copying: once an answer goes cedilla, the model's own words usually follow. In {{N_WHOLE}} of {{N_MODELS}} models, most failing answers are cedilla from the first word to the last. In the second round, Claude Opus 4.6 and GPT-5.6 Luna made exactly the same move as Opus 5: they rephrased the notice's "rugați" ("asked") as "îndrumaţi", cedilla included.

And some models don't need a bad input at all: the two gpt-oss models put a cedilla into {{OSS_CLEAN_K}} of {{OSS_CLEAN_N}} answers to correctly typed text.

### 3. A missing letter gets fixed. A wrong one gets copied.

![What gets repaired and what gets copied](CHART_LOOKRIGHT_URL)

Most Romanians type without diacritics at all ("Brasov"), so I gave the models the same 22 prompts that way too. A model that simply mirrored my style would answer without diacritics. They don't: {{E4_ASCII}} % of answers came back fully corrected, and only {{E4_WORD_ASCII}} % of the source's ș/ț words stayed bare. With cedillas, {{E4_WORD_CED}} % of those words kept the wrong letter. My guess: to a model, a bare s looks like a typo, and a cedilla looks like a real letter.

One model shows its reasoning, and it agrees. DeepSeek-R1 writes out its thinking before it answers. In {{DS_NR_N}} answers to cedilla input it mentioned the letters only {{DS_NR_TALK}} times, and one of those was a final check that protected the wrong one:

> Final check: county name spelled "Timiş" with ş, not "Timis". Must preserve diacritics in response.

With the rule in the prompt, its reasoning named the problem in {{DS_RU_TALK}} of {{DS_RU_N}} answers, and {{DS_RU_TALK_COPIED}} of those still came out with cedillas. In one, it planned to write "proper Romanian orthography with ș/ț commas below, not cedillas", then answered: "Autorităţile recomandă turiştilor să verifice starea drumului înainte de plecare."

I expected the same to hold outside Romanian, and wrote it down: in English text, letters that only look Latin (Cyrillic а, е, о inside "Zürich") would be copied, and mojibake ("ZÃ¼rich"), which looks broken, would be repaired. I was wrong. Across {{N_LK_MODELS}} models, Cyrillic look-alikes came back in only {{LK_CYR_COPIED}} % of answers, whether they filled every word or sat only in the names. Mojibake was repaired in {{LK_MOJI_SUM}} % of summaries but copied into {{LK_MOJI_COPIED_RAG}} % of the answers that quoted the document. Gemini 3.7 Flash, asked who owns the café: "CafÃ© MÃ¼ller in KÃ¶ln is closing, and it is owned by JosÃ© FernÃ¡ndez."

What the cedilla and mojibake have in common is that both are all over the real web; Cyrillic letters inside Latin words are not. So my best guess now is that models keep a spelling they have seen used for real and repair one they rarely see. That's a hypothesis for a next round, not a result of this one.

### 4. {{F4_HEAD}}

![Does the cedilla spread to text that was typed correctly?](CHART_SPREAD_URL)

{{FINDING4}}

### 5. Upgrades can make it worse

![Claude dropped at version 5. Gemini Flash crept up.](CHART_LINES_URL)

Kaggle serves several versions of the same models, so I could check whether newer means better. Before running anything, I wrote down that it wouldn't: newer versions would copy at least as often as older ones.

It's messier than that. Gemini Flash improved slowly, from {{V_FLASH_25}} % clean answers (2.5) to {{V_FLASH_37}} % (3.7). Claude improved through the 4.x versions and then fell back: Sonnet 4.6 kept {{V_SONNET_46}} % clean, Sonnet 5 {{V_SONNET_5}} %; Opus 4.8 {{V_OPUS_48}} %, Opus 5 {{V_OPUS_5}} %. GPT-5.6 Sol kept {{V_SOL_56}} %, GPT-6 Sol {{V_SOL_6}} %, GPT-6.1 Sol {{V_SOL_61}} %. GPT Luna went the other way, from {{V_LUNA_56}} % to {{V_LUNA_6}} %.

How much of that is noise? Rerunning the same model on the same prompts moved its score by up to {{RUN_SPREAD_MAX}} points (median {{RUN_SPREAD_MED}}). Of {{N_STEPS}} upgrades, {{N_STEPS_SIG}} moved more than chance would at p < 0.05, {{N_STEPS_DOWN}} for the worse and {{N_STEPS_UP}} for the better; {{STEPS_HOLM}} survive a correction for {{N_STEPS}} tests. Reasoning didn't help: Grok 4.20 kept {{V_GROK_R}} % with it and {{V_GROK_NR}} % without. In another entry, [Precedent vs Spec](https://dev.to/finn_mead_feb2e66f91b0c9d/the-header-says-10-the-table-says-8-most-frontier-models-quietly-went-with-the-table-bdn), the same Grok switch flipped the result; here it changed nothing, which makes copying the encoding look like a habit rather than a decision. (Qwen 3 Next's Thinking model mostly ran out of tokens before answering, so its numbers rest on {{QWEN_T_N}} prompts.)

If you depend on a behaviour like this, rerun your test on every upgrade.

### 6. The fix, and the fix for the fix

![One sentence fixes Romanian. Scoped, it spares most of the Turkish.](CHART_FIX_URL)

One sentence in the system prompt, *"Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them."*, lifts clean answers on cedilla input from {{E4_CED}} % to {{E4_RULE}} %. Not every model listens equally: {{RULE_LOW}} stayed below 80 % even with the rule.

Then I remembered where the cedilla came from. It's the Turkish letter, and in Turkish it's correct. A guesthouse bot in Brașov gets Turkish guests too, so I sent the same system prompt eight messages in Turkish ({{N_TR_MODELS}} models). Without the rule, {{TR_NONE}} % of replies were correct Turkish. With "never write ş", {{TR_RULE}} % were, and the rest went wrong in three different ways:

- **{{TR_RULE_RO}} % slipped into Romanian.** The rule mentions Romanian, so some models started answering the Turkish guest in Romanian.
- **{{TR_RULE_NOS}} % avoided the letter**, rephrasing around every word that needs it.
- **{{TR_RULE_COMMA}} % spelled Turkish with the Romanian letter.** Gemini 3.7 Flash, offering a honeymoon room: "balayınız için **muhteșem** dağ manzaralı … **Șarap** tadımı için…".

{{N_TR_BROKE}} of the {{N_TR_MODELS}} models broke at least one Turkish reply. Scoping the rule ("this applies to Romanian only; other languages keep their own letters") brought correct Turkish back to {{TR_SCOPED}} % and kept Romanian at {{RO_SCOPED}} %, but {{N_TR_SCOPED_BROKE}} models still slipped. (I scored these by the language of each sentence and checked every flagged word by hand; Romanian place names like Brașov don't count against a Turkish reply.)

The same thing happens in code. Asked for `fix_romanian(text)`, almost every model wrote the obvious translation table, which would break every ş in a Turkish name, and which misses decomposed letters (an `s` followed by a combining cedilla, as some PDFs and macOS file names produce): {{CODE_DECOMP_FAIL}} of 30 programs failed that test. When my prompt named the four wrong letters, {{CODE_C1_FULL}} of 15 programs passed everything; when it only described the goal, {{CODE_C2_FULL}} of 15 did. That's one program per model and prompt (McNemar p = {{CODE_P}}), so it's a hint, not a result: the more precisely I described the bug, the narrower the fix.

### My predictions, scored

I wrote these into the task descriptions on Kaggle before running Round 2.

{{PREDICTIONS}}

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

{{TABLE}}

{% enddetails %}

## My Benchmark

**Romanian Comma Below on Kaggle:** [kaggle.com/benchmarks/danielbutnar/romanian-comma-below](https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below)

Twelve tasks, all public, with every model answer in the run outputs. The code that builds the tasks, the fake models that test the scorer, the census, the analysis with its intervals, the charts, and a script that re-checks every number in this post against the raw results are on GitHub: [github.com/danielbutnar/comma-below](https://github.com/danielbutnar/comma-below).
