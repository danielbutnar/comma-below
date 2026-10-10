---
title: Braşov or Brașov? {{N_MODELS}} LLMs copy my wrong letter into a third of their answers
published: true
tags: devchallenge, kagglechallenge, ai, machinelearning
cover_image: COVER_URL
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

**Braşov** or **Brașov**? The second one is right. Brașov, the city I live in, is spelled with an s with a comma below. The first one has an s with a cedilla, a stand-in from the 1990s, when Romanian computers didn't have the right letter. Language models know the difference. They don't always act on it. Give them text typed with the old letter and a third of their answers copy it, most of them all the way, down to words I never wrote. I call it the **keyboard echo**. To a search box or a database, Braşov and Brașov are two different words.

I asked Claude Opus 5.5 the same question four times, about the same Romanian news paragraph, typed four different ways. Three answers are spelled right. Which one isn't?

> **A.** Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie.
>
> **B.** Festivalul a avut loc la Sighişoara, iar biletele pentru ediţia de anul viitor se vor pune în vânzare în decembrie.
>
> **C.** Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie.
>
> **D.** Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie.

{% details The answer %}

**B.** *Sighişoara* and *ediţia* carry the cedilla, because the paragraph I gave it did.

| Answer | My paragraph was typed |
| --- | --- |
| A | correctly (ș ț) |
| B | with the old cedilla letters (ş ţ) |
| C | without any diacritics |
| D | with the cedilla letters, plus one sentence in the system prompt |

{% enddetails %}

**TL;DR**

- **The keyboard echo: a third of the answers keep my wrong letter.** I gave {{N_MODELS}} models the same 22 Romanian prompts, typed four ways. Typed correctly or without any diacritics, {{E4_ASCII}} to {{E4_CLEAN}} % of the answers came back clean. Typed with the cedilla letters, {{E4_CED}} %. When an answer copies all of my cedillas, the model's own new words get them too.
- **Newer can be worse.** Claude Opus 4.8 kept {{V_OPUS_48}} % of its answers clean, Opus 5 {{V_OPUS_5}} %, run after run.
- **One sentence in the system prompt fixes most of it, and breaks Turkish**, where the cedilla letter is right. A short function that leaves Turkish sentences alone fixed every broken answer.

![Typed with the cedilla, a third of the answers keep it. {{N_MODELS}} models, the same 22 prompts typed four ways: {{E4_CLEAN}} % of answers clean when typed correctly, {{E4_ASCII}} % without diacritics, {{E4_CED}} % with the cedilla, {{E4_RULE}} % with the cedilla and one sentence in the system prompt](CHART_HERO_URL)

## What I Benchmarked

If you couldn't tell which answer was wrong, neither could the {{HUMAN_N}} Romanians I asked to compare twelve word pairs like these on their own screens: they got {{HUMAN_SD}} % right, what guessing gets. Even I, knowing what to look for, got {{HUMAN_AUTHOR_SD}} of 12. The models caught {{SEE_DIFF_K}} of the {{SEE_DIFF_N}} real differences. You can [take the two-minute test](https://danielbutnar.github.io/comma-below/human/test.html?from=dev) yourself.

Romanian has two letters with a comma underneath, **ș** and **ț** (U+0219, U+021B). The encodings Romanian computers used in the 1990s didn't have them, so people typed the Turkish **ş** and a **ţ** with a cedilla (U+015F, U+0163) instead. Unicode added the right letters in 1999. When I fetched the front pages of 35 Romanian sites on 30 September, {{CENSUS_WITH}} still had cedilla letters in Romanian words, the government's press releases among them.

To a computer they are different characters: `"Brașov" == "Braşov"` is `false`. The cedilla spelling is also all over the text that models learn from and that retrieval systems hand them. So I asked two things. Do models write the right letter? And what do they do when the text they read has the wrong one?

Every prompt comes in versions that differ only in how the letters are typed. A script, not an LLM, scores each answer by its Unicode code points after NFC normalization. I tested it first on fake models (one that copies its input scores 0 %, one that fixes everything 100 %) and checked the answer keys as a native speaker. For round two I wrote my predictions into each task's description on Kaggle before running it. {{PRED_FAILED}} of the {{PRED_TOTAL}} failed.

{% details The 13 tasks %}

| # | Task | What it asks |
| --- | --- | --- |
| 1 | Write | English prompt, plain ASCII names: does the Romanian answer use ș/ț? |
| 2 | Echo | Reply, summarize or answer from text typed correctly or with cedillas |
| 3 | Fix | "Proofread this" vs "correct the diacritics" vs an explicit instruction |
| 4 | See | Same characters? Any cedilla here? Which code point? |
| 5 | Restore | Diacritics where only context decides (*peste* / *pește*) |
| 6 | Code | Write `fix_romanian(text)`; 14 hidden tests |
| 7 | Echo + rule | Echo's cedilla inputs plus one system-prompt sentence |
| 8 | Echo, four inputs | Correct, cedilla, no diacritics, cedilla + rule; every model |
| 9 | Contagion | Four documents; some of the other three typed with cedillas |
| 10 | Turkish guests | Turkish, where ş is correct, under three rules |
| 11 | Other look-alikes | English with Cyrillic look-alikes or mojibake |
| 12 | Turns | Does a cedilla first text change the second summary? |
| 13 | Other wrong letters | Task 8's summaries with a dot below (ṣ) or old mojibake (º) instead of the cedilla |

{% enddetails %}

## Models Tested

**{{N_MODELS_ALL}} models.** Round one (30 September – 1 October) ran 15 models on the first seven tasks. Round two (8–11 October) ran the four-way test on every model Kaggle would serve and the follow-up tests on {{N_R2_MIN}} to {{N_T13}} of them.{{E4_MISSING_NOTE}} I picked the lineup for two comparisons: versions of the same model on identical prompts (Claude Opus 4.5 to 5.5, Gemini Flash 2.5 to 3.8, GPT-5.4 to GPT-6.1), and the same model with reasoning on and off (Grok 4.20, Qwen 3 Next). Everything ran on Kaggle's model proxy with default settings and an 8,192-token cap, for ${{COST}} of the free quota. Qwen 3 Next Thinking mostly ran out of tokens before answering.

{% details Full model list %}

{{MODELS_LINE}}

{% enddetails %}

## Findings

### 1. Models restore missing diacritics but keep wrong ones

Many Romanians type without diacritics at all ("Brasov"). Given the 22 prompts that way, the models put the letters back: {{E4_ASCII}} % of answers came back clean. Given the same prompts with cedillas, {{E4_CED}} % did.

They can tell. The same 15 first-round models wrote ș and ț correctly from English prompts ({{R1_WRITE}} %), spotted the cedilla in every sentence typed with it, and fixed {{R1_FIX_L2}} % of answers when told to correct the diacritics. If anything they see differences that aren't there: shown two identical words with the letter, they called them different a third of the time. They just don't fix it unless asked, and they never mention it: not one of the {{N_CED_ALL}} answers to text typed with cedillas did.

DeepSeek-R1 shows its reasoning, so I could check whether it even notices. Without the rule, it mentioned the letters in {{DS_NR_TALK}} of {{DS_NR_N}} answers. With the rule, in {{DS_RU_TALK}} of {{DS_RU_N}}, and {{DS_RU_TALK_COPIED}} of those still came out with cedillas. In one, it planned "proper Romanian orthography with ș/ț commas below, not cedillas" and then answered: "Autorităţile recomandă turiştilor să verifice starea drumului înainte de plecare." Both letters carry the cedilla. Reasoning didn't help Grok 4.20 either: {{V_GROK_R}} % clean with it, {{V_GROK_NR}} % without.

### 2. The keyboard echo: the model's own words get my cedilla too

![When an answer kept all of my cedillas, {{OWN_ALL_PCT}} % of the new ș/ț words the model chose itself had the cedilla too; when it kept only some, {{OWN_SOME_PCT}} %](CHART_KEYBOARD_URL)

Summaries and answers from a document reuse my words, so they copy the most: answers from a document came back clean only {{E4_RAG}} % of the time, guest replies {{E4_REPLY}} %. And it's mostly all or nothing: {{ALLNONE_PCT}} % of the answers that kept one of my cedillas kept all of them.

What surprised me were the words the model added itself. They can't be copied, so their spelling shows which keyboard the model is typing on. In answers that kept all of my cedillas, {{OWN_ALL_PCT}} % of the new ș/ț words had the cedilla too; in answers that kept only some, {{OWN_SOME_PCT}} %. The gap holds inside each of the {{WITHIN_N}} with enough words of both kinds to check, and in a fresh run on {{T13_MODELS}} models, where I had written it down as a prediction: {{T13_OWN_ALL_K}} of {{T13_OWN_ALL_N}} new words against {{T13_OWN_SOME_K}} of {{T13_OWN_SOME_N}}.

That is the keyboard echo: the model picks up my keyboard and types the whole answer on it. Claude Opus 5 rewrote a city-hall notice that said *rugați* ("asked") as *îndrumaţi* ("directed"), a word my text didn't have, cedilla included. Opus 4.6 and GPT-5.6 Luna made the same move.

The text the model answers from sets the keyboard; the documents around it turn the echo up or down. I put each question's document among three others and typed 0, 1 or 3 of the others with cedillas. Around a clean document, the neighbours hardly mattered: at least {{K9_CLEAN_MIN}} % of answers stayed clean at every level, and only {{K9_CLEAN_MOVERS}} slipped at all. Around a cedilla document, they did: {{K9_CED0}} % of answers came back clean with three clean neighbours, {{K9_CED3}} % with three cedilla ones, and {{K9_LOWER}} of the {{N_K9}} models moved that way, none the other. In a chat, a cedilla first message rarely changed the next answer.

### 3. Only the cedilla echoes: a dot below and mojibake get repaired

![Of three wrong spellings, only the cedilla survives: {{T13_CED_KEPT}} % of s and t letters came back with the cedilla, {{T13_DOT_KEPT}} % with a dot below, {{T13_LEG_KEPT}} % as mojibake](CHART_WRONG_URL)

Why the cedilla? Before a fresh run, I wrote down a test that could fail. I typed the same summaries and document questions two more ways: with s and t with a dot below (Braṣov), letters that look almost exactly like the right ones and exist in Yoruba and in transliteration but not in Romanian, and as the mojibake that old Romanian pages and subtitles often showed (Braºov), which looks broken.

On {{T13_MODELS}} models, the cedilla came back in {{T13_CED_KEPT}} % of the s and t letters. The dot below came back in {{T13_DOT_KEPT}} % and the mojibake in {{T13_LEG_KEPT}} %. {{T13_MODELS_LOWER}} of the {{T13_MODELS}} models kept the dot less often than the cedilla, and none kept it more.

So my guess was wrong: the dot below looks just as right, and the models fixed it. Of the three wrong spellings they keep only the cedilla, the one real Romanian text is full of, and the right letter in Turkish. This test can't tell which of those two makes it stick.

### 4. An upgrade can make it worse: Claude Opus 5 kept {{V_OPUS_5}} % clean, Opus 4.8 kept {{V_OPUS_48}} %

![Of {{N_STEPS}} upgrades on the same prompts, the biggest drops were Claude Opus 4.8 to 5 ({{V_OPUS_48}} to {{V_OPUS_5}} % clean) and Sonnet 4.6 to 5 ({{V_SONNET_46}} to {{V_SONNET_5}} %)](CHART_UPGRADES_URL)

Kaggle serves several versions of the same models, so I could compare them on identical prompts. Opus 4.8 kept {{V_OPUS_48}} % of its answers clean and Opus 5 {{V_OPUS_5}} %; Sonnet 4.6 {{V_SONNET_46}} % and Sonnet 5 {{V_SONNET_5}} %. Both drops survive a correction for the {{N_STEPS}} upgrades I compared. GPT Luna went the other way, from {{V_LUNA_56}} % to {{V_LUNA_6}} %.

These aren't one-run flukes. Opus 5 scored {{OPUS5_RUNS}}, from 30 September to 9 October, and the fresh run put both pairs of versions in the same order. Single answers do flip between identical runs ({{FLIP_R1}} % of model-and-prompt pairs in round one), but a model's overall rate barely moves: a median of {{RUN_SPREAD_MED}} points. So test every upgrade, and run it more than once.

### 5. One sentence stops the echo, and breaks Turkish

![Romanian answers clean and Turkish replies intact under each fix: a Romanian-only swap in code cleans every Romanian answer and changes {{FIX_TR_ALTERED}} of {{FIX_TR_N}} Turkish replies](CHART_FIXES_URL)

One sentence in the system prompt, *"Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them."*, lifted clean answers on cedilla input from {{E4_CED}} % to {{E4_RULE}} % (on the harder summaries and document questions in the chart, from {{T13_CED_CLEAN}} % to {{T13_FULL}} %).

Then I remembered where the cedilla came from. It's the Turkish letter, and in Turkish it's correct. A guesthouse bot in Brașov gets Turkish guests too, so I sent the same bot eight messages in Turkish. Without the rule, {{TR_NONE}} % of the replies were correct. With it, {{TR_RULE}} % were: some switched to Romanian, some avoided the letter, some spelled Turkish with the Romanian one. Gemini 3.7 Flash offered a honeymoon couple a "**muhteșem** dağ manzaralı" room and a "**Șarap** tadımı". Adding "this applies to Romanian only" brought Turkish back to {{TR_SCOPED}} %. (A script sorted the replies by language; I checked every flagged word by hand. No native speaker checked the Turkish.)

A few lines of code do better. The usual fix, swapping every ş for ș, broke {{FIX_NAIVE_PHRASE}} correct Turkish replies. Doing the same swap only in sentences without ı, ğ, ç, ö or ü changed {{FIX_TR_ALTERED}} of them and still fixed every Romanian answer.

## What I got wrong

- **My predictions.** {{PRED_FAILED}} of the {{PRED_TOTAL}} failed and {{PRED_UNCLEAR}} more were mixed or too close to call. Most were directions, with thresholds I set when scoring; the look-alike test had its thresholds written down first, and {{T13_PRED_PHRASE}}. The full table is below.
- **My upload.** The Kaggle CLI reads task files with the system encoding, cp1250 on my laptop, so my first task file would have uploaded "Brașov" as "BraČ™ov". The task files are now pure ASCII and check a hash of their data before running.
- **My first fix.** The `fix_romanian()` in the first version of this post broke Turkish, the same way the one-sentence rule does.

{% details All the predictions, scored %}

{{PREDICTIONS}}

{% enddetails %}

## What changed in how I think about these models

I went in expecting a knowledge test, and the models passed it. What I hadn't thought about is that the text I hand a model is also a style sample, encoding included, and the model answers in it: the keyboard echo. The model follows that sample most closely when it summarizes or answers from my text, which is what retrieval does all day. And it moves between versions, in both directions.

So I fix it in code, before the text reaches the model and again after, and only where the text is Romanian:

```python
import re
import unicodedata

CEDILLA_TO_COMMA = str.maketrans("şŞţŢ", "șȘțȚ")
NOT_ROMANIAN = set("ıİğĞçÇöÖüÜ")  # letters Turkish uses and Romanian words don't

def fix_romanian(text: str) -> str:
    text = unicodedata.normalize("NFC", text)  # "s" + combining cedilla -> "ş"
    return re.sub(r"[^.!?\n]+", lambda m: m.group(0) if set(m.group(0)) & NOT_ROMANIAN
                  else m.group(0).translate(CEDILLA_TO_COMMA), text)
```

It would skip a Romanian sentence that quotes a name like Zürich. In my {{FIX_RO_N}} broken answers it never missed a letter.

Want to know whether your model does it? Paste one of its answers below. Every cedilla letter turns red.

{{CHECKER_TAG}}

Does your language have a pair like ş and ș? Tell me in the comments. I'd like to test it next.

{% details All the numbers (the 15 first-round models) %}

Echo with cedilla is the mean of every run on the same prompts (tasks 2 and 8).

{{TABLE}}

{% enddetails %}

## My Benchmark

{% cta https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below %} Romanian Comma Below on Kaggle {% endcta %}

Thirteen tasks with every model answer in the run outputs. The four-way test's own leaderboard ranks the models on the keyboard echo. The code that builds the tasks, the fake models that test the scorer, the census, the analysis and a script that re-checks the post's numbers against the raw results are on GitHub: [github.com/danielbutnar/comma-below](https://github.com/danielbutnar/comma-below). Every input is generated from correctly spelled text in one file, `src/items.py`, so testing another letter pair or another language is a small change.
