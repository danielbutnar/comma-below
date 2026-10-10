---
title: Braşov or Brașov? Give {{N_MODELS}} LLMs the wrong letter, and a third of their answers keep it
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

Couldn't spot it? In my first human test, {{HUMAN_N}} Romanians did no better than a coin flip, partly because my page drew the two letters alike on some screens. [Try the fixed two-minute test](https://danielbutnar.github.io/comma-below/human/test.html?from=dev).

| Answer | My paragraph was typed |
| --- | --- |
| A | correctly (ș ț) |
| B | with the old cedilla letters (ş ţ) |
| C | without any diacritics |
| D | with the cedilla letters, plus one sentence in the system prompt |

{% enddetails %}

Models know the right letter. Hand them text typed with the old one and a third of their answers keep it. Most of those keep every one, and when they add a word of their own, it gets the cedilla too, as if they had switched to my keyboard. I call it the **keyboard echo**. It's one Romanian letter, but I suspect the lesson isn't Romanian: the text you hand a model, retrieval chunks included, is also a style sample, and familiar errors in it can come back in the answer.

**TL;DR**

- **A third of the answers keep my wrong letter.** Typed correctly, {{E4_CLEAN}}% of answers came back clean; without diacritics, {{E4_ASCII}}%; with the cedilla letters, {{E4_CED}}%. Every one of the {{N_MODELS}} models did it at least once.
- **The model's own words get it too**, but only the cedilla does this: a dot below and old mojibake (text garbled by the wrong encoding) get repaired.
- **Newer can be worse.** Claude Opus 4.8 → 5 went from {{V_OPUS_48}}% to {{V_OPUS_5}}% clean and Sonnet 4.6 → 5 from {{V_SONNET_46}}% to {{V_SONNET_5}}%, and the drops repeated in a fresh run. Other upgrades got better, so test each one.
- **One sentence in the system prompt fixes most of it, and breaks Turkish**, where the cedilla is right. A few lines of code fixed every Romanian answer and changed {{FIX_TR_ALTERED}} of {{FIX_TR_N}} Turkish replies.

![Typed with the cedilla, a third of the answers keep it. {{N_MODELS}} models, the same 22 Romanian prompts. Share of clean answers (with ș or ț, and no cedilla or look-alike letter): typed correctly {{E4_CLEAN}}%, without diacritics {{E4_ASCII}}%, with the cedilla letters {{E4_CED}}%, with the cedilla letters plus one system-prompt sentence {{E4_RULE}}%. Typed correctly, gpt-oss-120b and gpt-oss-20b kept 82% clean; typed with the cedilla, the best were {{TOP_NAMES}} at {{E4_MAX}}%, the lowest gpt-oss-120b at 32%.](CHART_HERO_URL)

## What I Benchmarked

Romanian has two letters with a comma underneath, **ș** and **ț** (U+0219, U+021B). The 1990s encodings didn't have them, so people typed the Turkish **ş** and a **ţ** with a cedilla (U+015F, U+0163). Unicode added the right letters in 1999, yet {{CENSUS_WITH}} of the {{CENSUS_OK}} Romanian front pages I fetched on 30 September still had cedilla letters, the government's site among them. On a page marked as Romanian, fonts like Roboto and Segoe UI even draw ş with a comma, so the people who publish the wrong letter may never see it.

`"Brașov" == "Braşov"` is `false`, and the cedilla spelling is all over the text models learn from and that retrieval hands them. So I asked: do models write the right letter, and what do they do when the text they read has the wrong one?

The main test has 22 prompts: 6 guest messages to a Brașov guesthouse's booking assistant, 6 news paragraphs to summarize, and 10 questions about those texts (the quiz is one). Each went out four ways, like the quiz: correct, without diacritics, with cedillas, and with cedillas plus a one-sentence rule in the system prompt. An answer is **clean** when it has at least one ș or ț and no cedilla or look-alike letter. A script, not an LLM, checks that by code point. Twelve more tasks on [Kaggle Benchmarks](https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below) probe the edges; for tasks 8 to 13 I wrote my predictions into each notebook before its first run (see [task 13](https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-13-other-wrong-letters)).

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

Mainly gpt-oss-120b, gpt-oss-20b and Claude Haiku 4.5 add cedillas to text that had none ("Șoferii sunt **rugaţi**…", from gpt-oss); for the rest, the cedilla almost always comes from my text.

DeepSeek-R1 shows its reasoning, so I could check whether it notices. Without the rule, its reasoning mentioned the letters in {{DS_NR_TALK}} of {{DS_NR_N}} answers; with it, in {{DS_RU_TALK}} of {{DS_RU_N}}, mostly repeating the rule, and {{DS_RU_TALK_COPIED}} of those still came out with cedillas. In one, it planned for "proper Romanian orthography with ș/ț commas below, not cedillas" and answered "**Autorităţile** recomandă **turiştilor** să verifice starea drumului înainte de plecare." Both words carry the cedilla.

### 2. The keyboard echo: the model's own words get my cedilla too

Answers to questions about a document came back clean {{E4_RAG}}% of the time, summaries {{KIND_SUM}}%, guest replies {{E4_REPLY}}%: the more of my words an answer reuses, the more cedillas it keeps. And it's mostly all or nothing: {{ALLNONE_PCT}}% of the answers that kept any of my cedillas kept all of them.

What surprised me were the model's own words. They can't be copied, so their spelling shows which keyboard the model is typing on. Claude Opus 5 summarized a city-hall notice that asked drivers (*rugați*, "asked") to park elsewhere:

> Şoferii sunt **îndrumaţi** să parcheze pe strada Mureşenilor sau lângă Gara Braşov.

*Îndrumaţi* ("directed") isn't in my text. The model chose it, and typed it on my keyboard. {{N_INDRUMATI_WORD}} other models chose the same word, cedilla and all. Across all the echo answers, when an answer kept all my cedillas, {{OWN_ALL_PCT}}% of the ș/ț words it added had the cedilla; when it kept some, {{OWN_SOME_PCT}}%. Those partial answers tended to keep the cedilla in place names like Braşov and Sighişoara, the way you'd quote a name, and wrote their own words with the comma. So there are two behaviors: quoting names, and switching keyboards.

![When an answer kept all my cedillas, {{OWN_ALL_PCT}}% of the new ș/ț words it added had the cedilla too ({{OWN_ALL_K}} of {{OWN_ALL_N}}); when it kept some of them, {{OWN_SOME_PCT}}% ({{OWN_SOME_K}} of {{OWN_SOME_N}}); when it kept none, {{OWN_NONE_PCT}}%. A new word is one not in my text and not an inflection of a word in it. Tasks 2 and 8.](CHART_KEYBOARD_URL)

The gap holds inside the {{WITHIN_N}} with enough new words to test it ({{OWN_WITHIN_NAMES}}), and in a fresh run on {{T13_MODELS}} models, where I had predicted it: {{T13_OWN_ALL_K}} of {{T13_OWN_ALL_N}} new words against {{T13_OWN_SOME_K}} of {{T13_OWN_SOME_N}}.

Could keeping my spelling just be faithful quoting? Not for a word the model chose itself, and the same models silently turn Brasov into Brașov. Even if I excuse every place name copied from my text as a quotation, only {{E4_CED_NAMES_OK}}% of answers are clean.

### 3. The documents around it turn the echo up or down

I hid each question's document among three others and typed 0, 1 or 3 of them with cedillas. Around a clean document, the neighbors hardly mattered: at least {{K9_CLEAN_MIN}}% of answers stayed clean. Around a cedilla document, three clean neighbors pulled answers up to **{{K9_CED0}}% clean** and three cedilla ones down to **{{K9_CED3}}%**; {{K9_LOWER}} of the {{N_K9}} models moved that way, none the other.

In a chat, a first message typed with cedillas hardly mattered: only {{T12_INF_N}} of {{T12_INF_TOTAL}} clean second summaries picked up one, both from {{T12_MODEL}}.

### 4. Only the cedilla sticks: a dot below and mojibake get repaired


Why the cedilla? Either any near-twin of the right letter slips through, or only the familiar wrong one does. A dot below (Braṣov) tells them apart: it looks just as close, but no Romanian text uses it. Before a fresh run on {{T13_MODELS}} models I wrote down that it would be repaired, along with mojibake (Braºov), which looks broken.

![Of three wrong spellings, only the cedilla survives. {{T13_MODELS}} models, the same 16 summaries and document questions. Of the ș and ț letters in words the answers reused from my text, {{T13_CED_KEPT}}% came back with the cedilla (Braşov), {{T13_DOT_KEPT}}% with a dot below (Braṣov) and {{T13_LEG_KEPT}}% as old mojibake (Braºov).](CHART_WRONG_URL)

{{T13_MODELS_LOWER}} of the {{T13_MODELS}} models kept the dot less often than the cedilla, and none kept it more. So it isn't just a near-twin slipping through.

Familiarity fits: the cedilla fills real Romanian web text, and ş is a real Turkish letter. It also fits, after the fact, a prediction of mine that failed in English: in answers to questions about an English document, rare Cyrillic look-alikes came back less often than the mojibake common on the web ({{LK_CYR_NAMES_COPIED_RAG}}% against {{LK_MOJI_COPIED_RAG}}%). I didn't measure how common each spelling is, so this is a hypothesis.

### 5. Newer can be worse: Opus 4.8 kept {{V_OPUS_48}}% clean, Opus 5 {{V_OPUS_5}}%

![Of {{N_STEPS}} upgrades on the same prompts, {{N_STEPS_HOLM}} copied my cedillas far more often, and none far less: Claude Opus 4.8 {{V_OPUS_48}}% to Opus 5 {{V_OPUS_5}}%, Claude Sonnet 4.6 {{V_SONNET_46}}% to Sonnet 5 {{V_SONNET_5}}%. The other changes, among them GPT Sol 5.6 to 6 ({{V_SOL_56}}% to {{V_SOL_6}}%) and GPT Luna 5.6 to 6 ({{V_LUNA_56}}% to {{V_LUNA_6}}%), don't survive a correction for all {{N_STEPS}} comparisons.](CHART_UPGRADES_URL)

I compared {{N_STEPS}} upgrades on identical prompts. The three cleanest models all got worse in their next version: Opus 4.8 → 5 ({{V_OPUS_48}}% → {{V_OPUS_5}}%), Sonnet 4.6 → 5 ({{V_SONNET_46}}% → {{V_SONNET_5}}%), GPT-5.6 Sol → 6 ({{V_SOL_56}}% → {{V_SOL_6}}%). Only the two Claude drops survive a correction for {{N_STEPS}} comparisons; they come from the same generation, so probably one cause (Opus 5.5 recovered part of it, Sonnet 5.5 didn't). Several upgrades improved by 13 to 25 points, all within noise.

When you pick the best three of {{N_MODELS}}, some will slip on a rerun by chance alone, so I checked the fresh run: all three drops came back, GPT Sol's included, each by 30 points or more, while a model's rate moved a median of {{RUN_SPREAD_R1_MED}} points between identical runs. So test every upgrade, and run it more than once.

### 6. One sentence stops the echo, and breaks Turkish

![A Romanian-only swap in code cleans every Romanian answer and changes {{FIX_TR_ALTERED}} of {{FIX_TR_N}} Turkish replies. Romanian answers clean and Turkish replies still correct: no fix {{T13_CED_CLEAN}}% and {{TR_NONE}}%; one sentence in the system prompt {{T13_FULL}}% and {{TR_RULE}}%; the same sentence for Romanian only {{T13_SCOPED}}% and {{TR_SCOPED}}%; swapping every ş for ș in code 100% and 0%; swapping only outside Turkish-looking sentences 100% and 96%.](CHART_FIXES_URL)

One sentence in the system prompt lifted clean answers on cedilla input from {{E4_CED}}% to {{E4_RULE}}% in the main test, and from {{T13_CED_CLEAN}}% to {{T13_FULL}}% on the fresh run's summaries and questions in the chart: *"Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them."*

But in Turkish, ş is correct. Brașov gets Turkish guests too, so I sent the booking assistant eight messages in Turkish. Without the rule, every reply was correct; with it, {{TR_RULE}}%. Some spelled Turkish with the Romanian ș, some switched to Romanian, some avoided ş altogether. Gemini 3.7 Flash offered a honeymoon couple a "**muhteșem** dağ manzaralı" room (a magnificent mountain view) and a "**Șarap** tadımı" (wine tasting). Adding "this applies to Romanian only" brought Turkish back to {{TR_SCOPED}}%. (A script sorted the replies by language and I checked every flagged word; no Turkish speaker did.)

Code does better. Swapping every ş for ș broke all {{FIX_TR_N}} correct Turkish replies. Swapping only in sentences without ı, ğ, ç, ö or ü fixed all {{FIX_RO_N}} broken Romanian answers and changed just {{FIX_TR_ALTERED}} Turkish replies, {{FIX_TR_HOS}} of them short greetings like "Hoş geldiniz". One caveat: I wrote that rule looking at these same replies, so expect it to do a little worse on new text.

## What I Got Wrong

- **My predictions.** {{PRED_FAILED}} of {{PRED_TOTAL}} failed and {{PRED_UNCLEAR}} were too close to call. Most had no threshold until I scored them; the one test with thresholds written first (dot below and mojibake) went 5 for 5. The table is in the block below.
- **My sample.** Everything rests on short paragraphs I wrote about one city, and {{N_SINGLE_RUN}} of the {{N_MODELS}} models ran the main test once, so one model's rate carries an interval about {{CI_WIDTH_MED}} points wide. Trust the patterns more than any one rank. "A third" also depends on my mix of prompts: answers from a document kept the cedilla nearly half the time.

{% details Two smaller mistakes, and every prediction scored %}

**My upload.** The Kaggle CLI reads task files with the system encoding, cp1250 on my laptop, so my first task file would have uploaded "Brașov" as "BraČ™ov". The task files are now pure ASCII and check a hash of their data before running.

**My first fix.** The `fix_romanian()` in the first version of this post broke Turkish, the same way the one-sentence rule does.

{{PRED_NOTE}}

{{PREDICTIONS}}

{% enddetails %}

## What Changed in How I Think About These Models

I went in expecting a knowledge test, and the models passed it. What I hadn't thought about: the text I hand a model is also a style sample, encoding included. The model answers in that style, most closely when it summarizes or answers from my text, which is what retrieval does all day. It isn't only Romanian: asked about an English document typed with the mojibake common on the web (ZÃ¼rich), {{LK_MOJI_COPIED_RAG}}% of the answers kept it (summaries repaired it).

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

It has two blind spots: a short Turkish sentence without ı, ğ, ç, ö or ü, like "Hoş geldiniz", and a Romanian sentence quoting a name like Zürich.

Does your model do it? Send it the prompt in step 1 below and paste its answer: every cedilla letter turns red. (No box? [Open the checker on its own page](https://danielbutnar.github.io/comma-below/post/checker.html).)

{{CHECKER_TAG}}

## What I'd Measure Next

Whether the echo survives a real retrieval pipeline, which cleans and chunks documents first; whether other languages with a look-alike letter from an old encoding echo it too; and whether it tracks how tokenizers split each letter (ş is common in Turkish text, ṣ is rare).

## My Benchmark

{% cta https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below %} Romanian Comma Below on Kaggle {% endcta %}

Thirteen tasks, with every model answer in the run outputs. Read [task 8's leaderboard](https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-8-echo-four-inputs); the overall score averages different tasks for different models.

{% details Reading the leaderboard %}

This post's numbers come from the runs up to 10 October; later runs on the leaderboard aren't in them. Task 8's leaderboard uses each model's latest run and counts an empty answer as a failure. That's why Qwen 3 Next Thinking shows {{QWEN_T_KAGGLE}}%, and why Grok 4.5 and 4.6, listed by Kaggle but with every call errored (they're not among my 44), show 0%.

{% enddetails %}

{% details All the numbers (the 15 first-round models) %}

Task scores in %. Echo with cedilla is the mean of every run on the same prompts (tasks 2 and 8); Echo + rule pools tasks 7 and 8. See counts the first true/false or code point in each answer, as Kaggle does: DeepSeek-R1 listed every letter's code point before giving the right one, so on its final answers it scores {{SEE_DS_FINAL}} (Gemini 3.5 Flash-Lite {{SEE_FL_FINAL}}).

{{TABLE}}

{% enddetails %}

The task builder, the fake models that test the scorer, the analysis and a script that re-checks this post's numbers against the raw answers are on [GitHub](https://github.com/danielbutnar/comma-below). Every input is generated from correctly spelled text in `src/items.py`, so testing another letter pair or language is a small change. Built with [kaggle-benchmarks](https://pypi.org/project/kaggle-benchmarks/); the checker runs on [LiveCodes](https://livecodes.io). I used Claude as a coding and editing assistant.

If your pipeline touches Romanian, paste one of your model's answers into the checker above, and run `fix_romanian()` on the way in and on the way out. And if your language has its own ş, tell me in the comments.
