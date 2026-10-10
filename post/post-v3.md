---
title: Braşov or Brașov? I typed my wrong letter to {{N_MODELS}} LLMs, and a third of the answers kept it
published: true
ai_disclosure_level: some_ai
tags: devchallenge, kagglechallenge, ai, machinelearning
description: "Typed with the old cedilla letters, {{N_MODELS}} LLMs kept them in a third of their answers, even in words they chose themselves. A Kaggle benchmark with 13 tasks and no LLM judge."
cover_image: COVER_URL
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

Brașov, the city I live in, is spelled with ș, an s with a comma below. The 1990s stand-in, ş, has a cedilla instead, and to a spell-checker or an exact-match lookup, Brașov and Braşov are different words. I asked Claude Opus 5.5 the same question about one Romanian news paragraph, sent four different ways. Three answers are spelled right. Which one isn't?

> **A.** Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie.
>
> **B.** Festivalul a avut loc la Sighişoara, iar biletele pentru ediţia de anul viitor se vor pune în vânzare în decembrie.
>
> **C.** Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie.
>
> **D.** Festivalul a avut loc la Sighișoara, iar biletele pentru ediția de anul viitor se vor pune în vânzare în decembrie.

{% details The answer %}

**B.** *Sighişoara* and *ediţia* carry the cedilla, because the paragraph I gave it did. A, C and D are the same characters. The question was "Where did the festival take place, and when do next year's tickets go on sale?" (In Sighișoara; in December.)

| Answer | My paragraph was typed |
| --- | --- |
| A | correctly (ș ț) |
| B | with the old cedilla letters (ş ţ) |
| C | without any diacritics |
| D | with the cedilla letters, plus one sentence in the system prompt |

{% enddetails %}

Models know the right letter. Hand them text typed with the old one and a third of their answers keep it. Most of those keep every one, and when they add a word of their own, it gets the cedilla too, as if they had switched to my keyboard. I call it the **keyboard echo**.

**TL;DR**

- **A third of the answers keep my wrong letter.** Same 22 prompts, {{N_MODELS}} models: typed correctly, {{E4_CLEAN}}% came back clean; without diacritics, {{E4_ASCII}}%; with the cedilla letters, {{E4_CED}}%. Every model did it at least once.
- **The model's own words get it too**, but only the cedilla does this: a dot below and old mojibake get repaired.
- **Newer can be worse.** The three cleanest models were each followed by a version that kept {{OLDER3_NEXT}} clean.
- **One sentence in the system prompt fixes most of it, and breaks Turkish**, where the cedilla is right. A few lines of code fixed every Romanian answer and changed {{FIX_TR_ALTERED}} of {{FIX_TR_N}} Turkish replies.

![Typed with the cedilla, a third of the answers keep it. {{N_MODELS}} models, the same 22 Romanian prompts. Share of clean answers (with ș or ț, and no cedilla or look-alike letter): typed correctly {{E4_CLEAN}}%, without diacritics {{E4_ASCII}}%, with the cedilla letters {{E4_CED}}%, with the cedilla letters plus one system-prompt sentence {{E4_RULE}}%. Typed correctly, gpt-oss-120b and gpt-oss-20b kept 82% clean; typed with the cedilla, the best were {{TOP_NAMES}} at {{E4_MAX}}%, the lowest gpt-oss-120b at 32%.](CHART_HERO_URL)

## What I Benchmarked

Romanian has two letters with a comma underneath, **ș** and **ț** (U+0219, U+021B). The 1990s encodings didn't have them, so people typed the Turkish **ş** and a **ţ** with a cedilla (U+015F, U+0163). Unicode added the right letters in 1999, yet {{CENSUS_WITH}} of the {{CENSUS_OK}} Romanian front pages I fetched on 30 September still had cedilla letters, the government's site among them. On a page marked as Romanian, fonts like Roboto and Segoe UI even draw ş with a comma, so the people who publish the wrong letter may never see it.

`"Brașov" == "Braşov"` is `false`, and the cedilla spelling is all over the text models learn from and that retrieval hands them. So I asked: do models write the right letter, and what do they do when the text they read has the wrong one?

The main test has 22 prompts: 6 guest messages to a Brașov guesthouse's booking assistant, 6 news paragraphs to summarize, and 10 questions about those texts (the quiz is one). Each went out four ways, like the quiz: correct, without diacritics, with cedillas, and with cedillas plus a one-sentence rule in the system prompt. An answer is **clean** when it has at least one ș or ț and no cedilla or look-alike letter. A script, not an LLM, checks that by code point; I tested it on fake models first and checked the answer keys as a native speaker. Twelve more tasks on [Kaggle Benchmarks](https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below) probe the edges, and for tasks 8 to 13 I wrote my predictions into each notebook before its first run.

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
| 8 | Echo, four inputs | The main test: correct, cedilla, no diacritics, cedilla + rule; every model |
| 9 | Contagion | Four documents and a question about one; the target clean or typed with cedillas, and 0, 1 or 3 of the others typed with cedillas |
| 10 | Turkish guests | Turkish, where ş is correct: no rule, the full rule, the rule scoped to Romanian |
| 11 | Other look-alikes | English with Cyrillic look-alikes or mojibake |
| 12 | Turns | Does a cedilla first text change the second summary? |
| 13 | Other wrong letters | Task 8's summaries and document questions with a dot below (ṣ) or old mojibake (º) instead of the cedilla |

{% enddetails %}

## Models Tested

**{{N_MODELS_ALL}} models.** Round one (30 September – 1 October) ran 15 models on tasks 1–7. Round two (8–10 October) ran the main test on the {{N_MODELS}} models Kaggle served that answered (GPT-6 Astra's runs failed), and tasks 9–13 on {{N_R2_MIN}} to {{N_T13}} models each. The lineup lets me compare versions of one model on identical prompts, and reasoning on and off. Everything ran on Kaggle's model proxy with default settings and an 8,192-token cap, for ${{COST}} of the free quota.

{% details Full model list %}

{{MODELS_LINE}}

{% enddetails %}

## Findings

### 1. Models restore missing diacritics but keep wrong ones

Many Romanians type without diacritics ("Brasov"), and the models put them back ({{E4_ASCII}}% clean, against {{E4_CED}}% for cedilla input).

They can tell. The 15 first-round models wrote ș and ț correctly from English prompts ({{R1_WRITE}}%), spotted the cedilla in every sentence typed entirely with it, and fixed {{R1_FIX_L2}}% of texts when told to correct the diacritics. They just don't fix it unprompted, or mention it: none of the {{N_CED_ALL}} answers to cedilla text did (my prompts asked for short answers).

Three models bring the old letter themselves. gpt-oss-120b and gpt-oss-20b put a cedilla into {{OSS_CLEAN_IN}}% of their answers to correctly typed text, sometimes next to the right letter: "{{OSS_EXAMPLE}}" Claude Haiku 4.5 does it when it puts missing diacritics back ({{HAIKU_ASCII_CED}} of {{HAIKU_ASCII_N}} answers to text without any). Other models almost never write it unless my text has it.

DeepSeek-R1 shows its reasoning, so I could check whether it notices. Without the rule, its reasoning mentioned the letters in {{DS_NR_TALK}} of {{DS_NR_N}} answers; with it, in {{DS_RU_TALK}} of {{DS_RU_N}}, mostly repeating the rule, and {{DS_RU_TALK_COPIED}} of those still came out with cedillas. In one, it planned for "proper Romanian orthography with ș/ț commas below, not cedillas" and answered "Autorităţile recomandă turiştilor să verifice starea drumului înainte de plecare." Reasoning didn't help Grok 4.20 either ({{V8_GROK_R}}% clean with it, {{V_GROK_NR}}% without), and Qwen 3 Next Thinking ran out of tokens too often to tell.

### 2. The keyboard echo: the model's own words get my cedilla too

Answers from a document copy the most, because they reuse my words: {{E4_RAG}}% came back clean, summaries {{KIND_SUM}}%, guest replies {{E4_REPLY}}%. And it's mostly all or nothing: {{ALLNONE_PCT}}% of the answers that kept any of my cedillas kept all of them.

What surprised me were the model's own words. They can't be copied, so their spelling shows which keyboard the model is typing on. Claude Opus 5 summarized a city-hall notice that asked drivers (*rugați*, "asked") to park elsewhere:

> Şoferii sunt **îndrumaţi** să parcheze pe strada Mureşenilor sau lângă Gara Braşov.

*Îndrumaţi* ("directed") isn't in my text. The model chose it, and typed it on my keyboard. {{N_INDRUMATI_WORD}} other models made the same move. Across tasks 2 and 8, when an answer kept all my cedillas, {{OWN_ALL_PCT}}% of the ș/ț words it added had the cedilla; when it kept some, {{OWN_SOME_PCT}}%.

![When an answer kept all my cedillas, {{OWN_ALL_PCT}}% of the new ș/ț words it added had the cedilla too ({{OWN_ALL_K}} of {{OWN_ALL_N}}); when it kept some of them, {{OWN_SOME_PCT}}% ({{OWN_SOME_K}} of {{OWN_SOME_N}}); when it kept none, {{OWN_NONE_PCT}}%. A new word is one not in my text and not an inflection of a word in it. Tasks 2 and 8.](CHART_KEYBOARD_URL)

The gap holds inside the {{WITHIN_N}} with enough new words to test it ({{OWN_WITHIN_NAMES}}), and in a fresh run on {{T13_MODELS}} models (task 13), where I had predicted it: {{T13_OWN_ALL_K}} of {{T13_OWN_ALL_N}} new words against {{T13_OWN_SOME_K}} of {{T13_OWN_SOME_N}}. A quote of my document might keep my spelling, but a quote doesn't explain the cedilla on a word the model chose itself. And even counting every place name an answer kept as a fair quote, only {{E4_CED_NAMES_OK}}% of answers would be clean.

The document the model answers from sets the keyboard; the others around it turn the echo up or down. I put each question's document among three others, 0, 1 or 3 of them typed with cedillas (0 or 3 around a cedilla document). Around a clean document, at least {{K9_CLEAN_MIN}}% of answers stayed clean. Around a cedilla document, {{K9_CED0}}% came back clean with three clean neighbors and {{K9_CED3}}% with three cedilla ones; {{K9_LOWER}} of the {{N_K9}} models moved that way, none the other.

In a chat, a cedilla first message hardly mattered: only {{T12_INF_N}} of {{T12_INF_TOTAL}} clean second summaries picked up a cedilla, both from {{T12_MODEL}}, which writes cedillas even in chats that have none.

### 3. Only the cedilla sticks: a dot below and mojibake get repaired


Why the cedilla? If any near-twin of the right letter got through, a dot below would too; if it's the familiar wrong spelling, a rare one wouldn't. Before a fresh run on {{T13_MODELS}} models (task 13), I wrote down a test between the two and predicted the second: the same summaries and questions typed with a dot below (Braṣov), a near-twin no Romanian text uses, and with the mojibake old Romanian pages showed (Braºov), which looks broken.

![Of three wrong spellings, only the cedilla survives. {{T13_MODELS}} models, the same 16 summaries and document questions. Of the ș and ț letters in words the answers reused from my text, {{T13_CED_KEPT}}% came back with the cedilla (Braşov), {{T13_DOT_KEPT}}% with a dot below (Braṣov) and {{T13_LEG_KEPT}}% as old mojibake (Braºov).](CHART_WRONG_URL)

{{T13_MODELS_LOWER}} of the {{T13_MODELS}} models kept the dot less often than the cedilla, and none kept it more. So it isn't just a near-twin slipping through.

Familiarity fits: the cedilla fills real Romanian text, and ş is a real Turkish letter. It also fits a prediction of mine that failed: in English I expected Cyrillic look-alikes to be copied more than mojibake, but from an English document the mojibake common on the web (ZÃ¼rich) came back in {{LK_MOJI_COPIED_RAG}}% of answers, Cyrillic look-alikes in the same names in {{LK_CYR_NAMES_COPIED_RAG}}%. I didn't measure how common each spelling is, so this is a hypothesis.

### 4. Newer can be worse: Opus 4.8 kept {{V_OPUS_48}}% clean, Opus 5 {{V_OPUS_5}}%

![Of {{N_STEPS}} upgrades on the same prompts, {{N_STEPS_HOLM}} copied my cedillas far more often, and none far less: Claude Opus 4.8 {{V_OPUS_48}}% to Opus 5 {{V_OPUS_5}}%, Claude Sonnet 4.6 {{V_SONNET_46}}% to Sonnet 5 {{V_SONNET_5}}%. The other changes, among them GPT Sol 5.6 to 6 ({{V_SOL_56}}% to {{V_SOL_6}}%) and GPT Luna 5.6 to 6 ({{V_LUNA_56}}% to {{V_LUNA_6}}%), don't survive a correction for all {{N_STEPS}} comparisons.](CHART_UPGRADES_URL)

I compared {{N_STEPS}} upgrades on identical prompts. The three cleanest models, {{TOP_NAMES}}, are each the older half of a pair: Opus 5, Sonnet 5 and GPT-6 Sol kept {{OLDER3_NEXT}}. Only the two Claude drops survive a correction for making {{N_STEPS}} comparisons; GPT Sol's doesn't, and neither does GPT Luna's rise ({{V_LUNA_56}}% to {{V_LUNA_6}}%).

Picking the three cleanest of {{N_MODELS}} invites some fall back by chance, so I checked the fresh run of 16 of these prompts (task 13): all three pairs came out in the same order again (Opus {{T13_OPUS48}}% vs {{T13_OPUS5}}%, Sonnet {{T13_SONNET46}}% vs {{T13_SONNET5}}%, GPT Sol {{T13_SOL56}}% vs {{T13_SOL6}}%). Single answers do flip between identical runs, but a model's rate moved a median of {{RUN_SPREAD_R1_MED}} points between them, against drops of almost 40. So test every upgrade, and run it more than once.

### 5. One sentence stops the echo, and breaks Turkish

![A Romanian-only swap in code cleans every Romanian answer and changes {{FIX_TR_ALTERED}} of {{FIX_TR_N}} Turkish replies. Romanian answers clean and Turkish replies still correct: no fix {{T13_CED_CLEAN}}% and {{TR_NONE}}%; one sentence in the system prompt {{T13_FULL}}% and {{TR_RULE}}%; the same sentence for Romanian only {{T13_SCOPED}}% and {{TR_SCOPED}}%; swapping every ş for ș in code 100% and 0%; swapping only outside Turkish-looking sentences 100% and 96%.](CHART_FIXES_URL)

In the main test, one sentence in the system prompt lifted clean answers on cedilla input from {{E4_CED}}% to {{E4_RULE}}%: *"Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them."* The chart uses task 13, which has no guest replies: {{T13_CED_CLEAN}}% to {{T13_FULL}}%.

But in Turkish, ş is correct. Brașov gets Turkish guests too, so I sent the booking assistant eight messages in Turkish. Without the rule, every reply was correct; with it, {{TR_RULE}}%. Some spelled Turkish with the Romanian ș, some switched to Romanian, some avoided ş altogether. Gemini 3.7 Flash offered a honeymoon couple a "**muhteșem** dağ manzaralı" room (a magnificent mountain view) and a "**Șarap** tadımı" (wine tasting). Adding "this applies to Romanian only" brought Turkish back to {{TR_SCOPED}}%. (A script sorted the replies by language and I checked every flagged word; no Turkish speaker did.)

Code does better. The usual fix, swapping every ş for ș, broke {{FIX_NAIVE_PHRASE}} correct Turkish replies. Swapping only in sentences without ı, ğ, ç, ö or ü fixed all {{FIX_RO_N}} broken Romanian answers and changed {{FIX_TR_ALTERED}} of the {{FIX_TR_N}} Turkish replies, {{FIX_TR_HOS}} of them greetings like "Hoş geldiniz" that have none of those letters.

## What I got wrong

- **My predictions.** {{PRED_FAILED}} of the {{PRED_TOTAL}} failed and {{PRED_UNCLEAR}} more were too close to call. I wrote most of them as directions and set the thresholds when scoring; the dot-below and mojibake test had its thresholds written first, and {{T13_PRED_PHRASE}}. The full table is in the block below.
- **My sample.** Everything rests on short paragraphs I wrote about one city, and {{N_SINGLE_RUN}} of the {{N_MODELS}} models ran the main test once, so one model's rate carries an interval about {{CI_WIDTH_MED}} points wide. Trust the patterns more than any one rank. "A third" also depends on my mix of prompts: answers from a document kept the cedilla nearly half the time.
- **My human test.** {{HUMAN_N}} Romanians tried to tell twelve word pairs apart on their own screens and did no better than a coin flip. Part of that was my page: marked as Romanian, it drew the two letters the same on some screens. The page is fixed: [take the two-minute test](https://danielbutnar.github.io/comma-below/human/test.html?from=dev).

{% details Two smaller mistakes, and every prediction scored %}

**My upload.** The Kaggle CLI reads task files with the system encoding, cp1250 on my laptop, so my first task file would have uploaded "Brașov" as "BraČ™ov". The task files are now pure ASCII and check a hash of their data before running.

**My first fix.** The `fix_romanian()` in the first version of this post broke Turkish, the same way the one-sentence rule does.

{{PRED_NOTE}}

{{PREDICTIONS}}

{% enddetails %}

## What changed in how I think about these models

I went in expecting a knowledge test, and the models passed it. What I hadn't thought about: the text I hand a model is also a style sample, encoding included. The model answers in that style, most closely when it summarizes or answers from my text, which is what retrieval does all day.

So I fix it in code, before the text reaches the model and again after, and only where the text is Romanian:

```python
import re
import unicodedata

CEDILLA_TO_COMMA = str.maketrans("şŞţŢ", "șȘțȚ")
T_ONLY = str.maketrans("ţŢ", "țȚ")  # Turkish has no ţ, so it is always wrong
NOT_ROMANIAN = set("ıİğĞçÇöÖüÜ")  # letters Turkish uses and Romanian words don't

def fix_romanian(text: str) -> str:
    text = unicodedata.normalize("NFC", text)  # "s" + combining cedilla -> "ş"
    return re.sub(r"[^.!?\n]+", lambda m: m.group(0).translate(
        T_ONLY if set(m.group(0)) & NOT_ROMANIAN else CEDILLA_TO_COMMA), text)
```

Besides "Hoş geldiniz", its blind spot: it would leave the ş in a Romanian sentence quoting a name like Zürich.

Does your model do it? Send it the prompt in step 1 below and paste its answer: every cedilla letter turns red. (No box? [Open the checker on its own page](https://danielbutnar.github.io/comma-below/post/checker.html).)

{{CHECKER_TAG}}

## What I'd Measure Next

Whether the echo survives a real retrieval pipeline, which cleans and chunks documents first, and whether other languages with a look-alike letter from an old encoding echo it too. Does yours have a pair like ş and ș? Tell me in the comments.

## My Benchmark

{% cta https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below %} Romanian Comma Below on Kaggle {% endcta %}

Thirteen tasks, with every model answer in the run outputs. This post's numbers come from the runs up to 10 October; later runs on the leaderboard aren't in them. Read task 8's leaderboard rather than the overall score, which averages different tasks for different models. It uses each model's latest run and counts an empty answer as a failure, which is why Qwen 3 Next Thinking shows {{QWEN_T_KAGGLE}}% and Grok 4.5 and 4.6 (every call errored) 0%.

{% details All the numbers (the 15 first-round models) %}

Task scores in %. Echo with cedilla is the mean of every run on the same prompts (tasks 2 and 8); Echo + rule pools tasks 7 and 8. See counts the first true/false or code point in each answer, as Kaggle does: DeepSeek-R1 listed every letter's code point before giving the right one, so on its final answers it scores {{SEE_DS_FINAL}} (Gemini 3.5 Flash-Lite {{SEE_FL_FINAL}}).

{{TABLE}}

{% enddetails %}

The task builder, the fake models that test the scorer, the analysis and a script that re-checks this post's numbers against the raw answers are on [GitHub](https://github.com/danielbutnar/comma-below). Every input is generated from correctly spelled text in `src/items.py`, so testing another letter pair or language is a small change. Built with [kaggle-benchmarks](https://pypi.org/project/kaggle-benchmarks/); the checker runs on [LiveCodes](https://livecodes.io). I used Claude as a coding and editing assistant.
