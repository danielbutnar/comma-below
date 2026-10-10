---
title: Braşov or Brașov? Give 43 LLMs the wrong letter, and a third of their answers keep it
published: true
ai_disclosure_level: some_ai
tags: devchallenge, kagglechallenge, ai, machinelearning
description: "Typed with the old cedilla letters, 43 LLMs kept them in a third of their answers, even in words they chose themselves. A Kaggle benchmark with 13 tasks and no LLM judge."
cover_image: https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/cover-v3.png
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

- **A third of the answers keep my wrong letter.** Same 22 prompts, 43 models: typed correctly, 99% came back clean (with ș or ț and no cedilla); without diacritics, 96%; with the cedilla letters, 68%. Every model did it at least once.
- **The model's own words get it too**, but only the cedilla does this: a dot below and old mojibake (text garbled by the wrong encoding) get repaired.
- **Newer can be worse.** Claude Opus 4.8 → 5 went from 95% to 56% clean and Sonnet 4.6 → 5 from 95% to 58%, again in a fresh run. Other upgrades got better, so test each one.
- **One sentence in the system prompt fixes most of it, and breaks Turkish**, where the cedilla is right. A few lines of code fixed every Romanian answer and changed 5 of 112 Turkish replies.

![Typed with the cedilla, a third of the answers keep it. 43 models, the same 22 Romanian prompts. Share of clean answers (with ș or ț, and no cedilla or look-alike letter): typed correctly 99%, without diacritics 96%, with the cedilla letters 68%, with the cedilla letters plus one system-prompt sentence 95%. Typed correctly, gpt-oss-120b and gpt-oss-20b kept 82% clean; typed with the cedilla, the best were Claude Opus 4.8, Claude Sonnet 4.6 and GPT-5.6 Sol at 95%, the lowest gpt-oss-120b at 32%.](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-hero-v2.png)

## What I Benchmarked

Romanian has two letters with a comma underneath, **ș** and **ț** (U+0219, U+021B). The 1990s encodings didn't have them, so people typed the Turkish **ş** and a **ţ** with a cedilla (U+015F, U+0163). Unicode added the right letters in 1999, yet 29 of the 35 Romanian front pages I fetched on 30 September still had cedilla letters, the government's site among them. On a page marked as Romanian, fonts like Roboto and Segoe UI even draw ş with a comma, so the people who publish the wrong letter may never see it.

`"Brașov" == "Braşov"` is `false`, and the cedilla spelling is all over the text models learn from and that retrieval hands them. So I asked: do models write the right letter, and what do they do when the text they read has the wrong one?

The main test has 22 prompts: 6 guest messages to a Brașov guesthouse's booking assistant, 6 news paragraphs to summarize, and 10 questions about those texts (the quiz is one). Each went out four ways, like the quiz: correct, without diacritics, with cedillas, and with cedillas plus a one-sentence rule in the system prompt. An answer is **clean** when it has at least one ș or ț and no cedilla or look-alike letter. A script, not an LLM, checks that by code point; I tested it on fake models first and checked the answer keys as a native speaker. Twelve more tasks on [Kaggle Benchmarks](https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below) probe the edges, and for tasks 8 to 13 I wrote my predictions into each notebook before its first run (see [task 13](https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-13-other-wrong-letters)).

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

**44 models.** Round one (30 September – 1 October) ran 15 models on tasks 1–7. Round two (8–10 October) ran the main test on the 43 models Kaggle served that answered (GPT-6 Astra's runs failed), and tasks 9–13 on 10 to 28 models each. The lineup lets me compare versions of one model on identical prompts, and reasoning on and off. Everything ran on Kaggle's model proxy with default settings and an 8,192-token cap, for $30.19 of the free quota.

{% details Full model list %}

**Anthropic:** Claude Haiku 4.5, Claude Opus 4.5, Claude Opus 4.6, Claude Opus 4.7, Claude Opus 4.8, Claude Opus 5, Claude Opus 5.5, Claude Sonnet 4.5, Claude Sonnet 4.6, Claude Sonnet 5, Claude Sonnet 5.5. **Google:** Gemini 2.5 Flash, Gemini 3 Flash, Gemini 3.5 Flash, Gemini 3.6 Flash, Gemini 3.7 Flash, Gemini 3.8 Flash, Gemini 3.1 Flash-Lite, Gemini 3.5 Flash-Lite, Gemini 2.5 Pro, Gemini 3.1 Pro, Gemma 4 26B A4B, Gemma 4 31B. **OpenAI:** GPT-5.4, GPT-5.5, GPT-6 Astra, GPT-5.6 Luna, GPT-6 Luna, GPT-5.6 Sol, GPT-6 Sol, GPT-6.1 Sol, GPT-5.6 Terra, GPT-5.4 nano, GPT-5.4 mini, gpt-oss-20b, gpt-oss-120b. **xAI:** Grok 4.20 Non-Reasoning, Grok 4.20 Reasoning. **DeepSeek:** DeepSeek-R1. **Alibaba:** Qwen 3 235B, Qwen 3 Coder 480B, Qwen 3 Next 80B Instruct, Qwen 3 Next 80B Thinking. **Zhipu:** GLM-5.

{% enddetails %}

## Findings

### 1. Models restore missing diacritics but keep wrong ones

Many Romanians type without diacritics ("Brasov"), and the models put them back (96% clean, against 68% for cedilla input).

They can tell. The 15 first-round models wrote ș and ț correctly from English prompts (98%), spotted the cedilla in every sentence typed entirely with it, and fixed 99% of texts when told to correct the diacritics. They just don't fix it unprompted, or mention it: none of the 3,160 answers to cedilla text did (my prompts asked for short answers).

Three models bring the old letter themselves. gpt-oss-120b and gpt-oss-20b put a cedilla into 18% of their answers to correctly typed text, sometimes next to the right letter: "Șoferii sunt **rugaţi** să parcheze pe strada Mureșenilor și lângă Gara Brașov." Claude Haiku 4.5 does it when it puts missing diacritics back (6 of 22 answers to text without any). Other models almost never write it unless my text has it.

DeepSeek-R1 shows its reasoning, so I could check whether it notices. Without the rule, its reasoning mentioned the letters in 3 of 88 answers; with it, in 43 of 44, mostly repeating the rule, and 6 of those still came out with cedillas. In one, it planned for "proper Romanian orthography with ș/ț commas below, not cedillas" and answered "**Autorităţile** recomandă **turiştilor** să verifice starea drumului înainte de plecare." Both words carry the cedilla. Reasoning didn't help Grok 4.20 either (41% clean with it, 45% without), and Qwen 3 Next Thinking ran out of tokens too often to tell.

### 2. The keyboard echo: the model's own words get my cedilla too

Answers from a document copy the most, because they reuse my words: 52% came back clean, summaries 68%, guest replies 96%. And it's mostly all or nothing: 75% of the answers that kept any of my cedillas kept all of them.

What surprised me were the model's own words. They can't be copied, so their spelling shows which keyboard the model is typing on. Claude Opus 5 summarized a city-hall notice that asked drivers (*rugați*, "asked") to park elsewhere:

> Şoferii sunt **îndrumaţi** să parcheze pe strada Mureşenilor sau lângă Gara Braşov.

*Îndrumaţi* ("directed") isn't in my text. The model chose it, and typed it on my keyboard. Seven other models made the same move. Across tasks 2 and 8, when an answer kept all my cedillas, 95% of the ș/ț words it added had the cedilla; when it kept some, 9.5%.

![When an answer kept all my cedillas, 95% of the new ș/ț words it added had the cedilla too (86 of 91); when it kept some of them, 9.5% (9 of 95); when it kept none, 0.5%. A new word is one not in my text and not an inflection of a word in it. Tasks 2 and 8.](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-keyboard-v2.png)

The gap holds inside the two models with enough new words to test it (Claude Haiku 4.5 and GPT-5.4 nano), and in a fresh run on 28 models (task 13), where I had predicted it: 13 of 15 new words against 1 of 18. Could keeping my spelling just be faithful quoting? Not for a word the model chose itself, and the same models silently turn Brasov into Brașov. Even if I excuse every place name copied from my text as a quotation, only 73% of answers are clean.

The document the model answers from sets the keyboard; the others around it turn the echo up or down. I hid each question's document among three others and typed 0, 1 or 3 of them with cedillas. Around a clean document, the neighbors hardly mattered: at least 95% of answers stayed clean. Around a cedilla document, three clean neighbors pulled answers up to 78% clean and three cedilla ones down to 36%; 14 of the 15 models moved that way, none the other.

In a chat, a cedilla first message hardly mattered: only 2 of 60 clean second summaries picked up a cedilla, both from Claude Haiku 4.5, which writes cedillas even in chats that have none.

### 3. Only the cedilla sticks: a dot below and mojibake get repaired


Why the cedilla? If any near-twin of the right letter got through, a dot below would too; if it's the familiar wrong spelling, a rare one wouldn't. Before a fresh run on 28 models (task 13), I wrote down a test between the two and predicted the second: the same summaries and questions typed with a dot below (Braṣov), a near-twin no Romanian text uses, and with the mojibake old Romanian pages showed (Braºov), which looks broken.

![Of three wrong spellings, only the cedilla survives. 28 models, the same 16 summaries and document questions. Of the ș and ț letters in words the answers reused from my text, 38% came back with the cedilla (Braşov), 0.9% with a dot below (Braṣov) and 1.4% as old mojibake (Braºov).](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-wrong-v2.png)

27 of the 28 models kept the dot less often than the cedilla, and none kept it more. So it isn't just a near-twin slipping through.

Familiarity fits: the cedilla fills real Romanian text, and ş is a real Turkish letter. It also fits, after the fact, a prediction of mine that failed: in English I expected Cyrillic look-alikes to be copied more than mojibake, but from an English document the mojibake common on the web (ZÃ¼rich) came back in 41% of answers, Cyrillic look-alikes in the same names in 9%. I didn't measure how common each spelling is, so this is a hypothesis.

### 4. Newer can be worse: Opus 4.8 kept 95% clean, Opus 5 56%

![Of 19 upgrades on the same prompts, 2 copied my cedillas far more often, and none far less: Claude Opus 4.8 95% to Opus 5 56%, Claude Sonnet 4.6 95% to Sonnet 5 58%. The other changes, among them GPT Sol 5.6 to 6 (95% to 64%) and GPT Luna 5.6 to 6 (64% to 89%), don't survive a correction for all 19 comparisons.](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-upgrades-v2.png)

I compared 19 upgrades on identical prompts. The three cleanest models, Claude Opus 4.8, Claude Sonnet 4.6 and GPT-5.6 Sol, are each the older half of a pair: Opus 5, Sonnet 5 and GPT-6 Sol kept 56, 58 and 64%. Only the two Claude drops survive a correction for making 19 comparisons. GPT Sol's drop doesn't, and several upgrades got 13 to 25 points better, GPT Luna's among them (64% to 89%), also within noise.

When you pick the best three of 43, some will slip on a rerun by chance alone, so I checked the fresh run (task 13): all three pairs came out in the same order again. A model's rate moved a median of 9 points between identical runs, against drops of almost 40. So test every upgrade, and run it more than once.

### 5. One sentence stops the echo, and breaks Turkish

![A Romanian-only swap in code cleans every Romanian answer and changes 5 of 112 Turkish replies. Romanian answers clean and Turkish replies still correct: no fix 53% and 100%; one sentence in the system prompt 93% and 71%; the same sentence for Romanian only 94% and 95%; swapping every ş for ș in code 100% and 0%; swapping only outside Turkish-looking sentences 100% and 96%.](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-fixes-v5.png)

One sentence in the system prompt lifted clean answers on cedilla input from 68% to 95% in the main test, and from 53% to 93% on the fresh run's summaries and questions in the chart: *"Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them."*

But in Turkish, ş is correct. Brașov gets Turkish guests too, so I sent the booking assistant eight messages in Turkish. Without the rule, every reply was correct; with it, 71%. Some spelled Turkish with the Romanian ș, some switched to Romanian, some avoided ş altogether. Gemini 3.7 Flash offered a honeymoon couple a "**muhteșem** dağ manzaralı" room (a magnificent mountain view) and a "**Șarap** tadımı" (wine tasting). Adding "this applies to Romanian only" brought Turkish back to 95%. (A script sorted the replies by language and I checked every flagged word; no Turkish speaker did.)

Code does better. The usual fix, swapping every ş for ș, broke all 112 correct Turkish replies. Swapping only in sentences without ı, ğ, ç, ö or ü fixed all 352 broken Romanian answers and changed 5 of the 112 Turkish replies, 4 of them greetings like "Hoş geldiniz" that have none of those letters.

## What I Got Wrong

- **My predictions.** 2 of the 20 failed and 6 more were too close to call. I wrote most of them as directions and set the thresholds when scoring; the dot-below and mojibake test had its thresholds written first, and all 5 of its predictions held. The full table is in the block below.
- **My sample.** Everything rests on short paragraphs I wrote about one city, and 35 of the 43 models ran the main test once, so one model's rate carries an interval about 36 points wide. Trust the patterns more than any one rank. "A third" also depends on my mix of prompts: answers from a document kept the cedilla nearly half the time.
- **My human test.** 10 Romanians tried to tell twelve word pairs apart on their own screens and did no better than a coin flip. Part of that was my page: marked as Romanian, it drew the two letters the same on some screens. The page is fixed: [take the two-minute test](https://danielbutnar.github.io/comma-below/human/test.html?from=dev).

{% details Two smaller mistakes, and every prediction scored %}

**My upload.** The Kaggle CLI reads task files with the system encoding, cp1250 on my laptop, so my first task file would have uploaded "Brașov" as "BraČ™ov". The task files are now pure ASCII and check a hash of their data before running.

**My first fix.** The `fix_romanian()` in the first version of this post broke Turkish, the same way the one-sentence rule does.

Four of the verdicts too close to call rest on evidence that could be chance: the rank correlations in tasks 9 and 11 (permutation p = 0.20 and 0.11), task 8's upgrades, which went both ways before the correction, and task 12's 2 of 60 chat conversations, both from Claude Haiku 4.5.

| Task | Prediction | Result | |
| --- | --- | --- | --- |
| 8 | Correct input stays near 100% for every model. | lowest: gpt-oss-120b and gpt-oss-20b, 82% | **failed** |
| 8 | Cedilla input fails far more often than input without diacritics. | 96% vs 68% clean answers | held |
| 8 | Newer versions in a family copy the cedilla at least as often as older ones. | of 19 upgrades, 2 copied more and none copied less after a correction for multiple tests (3 and 1 at p < 0.05 before it); no overall trend (rank correlation -0.29) | inconclusive |
| 8 | The one-sentence rule lifts cedilla input to at least 90% for most models. | 36 of 43 models at 90% or more | held |
| 9 | With a clean target, answers stay clean for most models even when the other three documents are cedilla. | 13 of 15 models at 90% or more | held |
| 9 | The models that rewrote whole answers in cedilla in task 2 are the ones whose clean-target answers get infected. | rank correlation +0.38 over 15 models; only Claude Opus 5 and Claude Sonnet 5 had infected answers | inconclusive |
| 9 | A cedilla target is copied less when the other documents are clean. | 78% vs 36% clean answers | held |
| 10 | Without a rule, Turkish replies keep ş. | 100% correct | held |
| 10 | Task 7's rule makes some models write Turkish with the Romanian comma letter. | 6 of 14 models, 15 replies | held |
| 10 | The scoped rule keeps Turkish intact and still fixes Romanian. | Turkish 94.6% correct (no rule: 100%, full rule: 71%), Romanian 99% | inconclusive |
| 11 | Correct English input stays near 100%. | 100% | held |
| 11 | Cyrillic look-alikes are copied far more often than mojibake. | clean answers: 95% with look-alikes in the names, 80% with mojibake | **failed** |
| 11 | The models that copy the Romanian cedilla most also copy the look-alikes most. | rank correlation +0.55 over 10 models, resting on the 6 of 120 answers that kept a look-alike (4 models) | inconclusive |
| 12 | A cedilla first text infects some clean second summaries, mostly after a cedilla first summary. | 3% infected (2 of 60 conversations, both Claude Haiku 4.5); 11% when the first summary was itself in cedilla; the chats with no cedilla at all had 1 of 60 too (Claude Haiku 4.5) | inconclusive |
| 12 | A clean first text does not protect a cedilla second text much. | 83% clean after a clean first text, 68% on its own (the same models' task 2 summaries) | inconclusive |
| 13 | The dot below is kept in a smaller share of s/t letters than the cedilla (paired, 95% interval below zero). | 0.9% vs 38.1% of letters kept (-37 points, -45 to -29) | held |
| 13 | The old mojibake is also kept less often than the cedilla. | 1.4% vs 38.1% (-37 points, -44 to -29) | held |
| 13 | Repaired dot-below and mojibake letters become comma-below letters in at least 90% of cases. | 98% comma, 1.6% cedilla | held |
| 13 | Both rules give at least 90% clean answers, and the scoped rule is within 5 points of the full rule. | scoped 94%, full 93% | held |
| 13 | In cedilla answers that keep every cedilla, at least 80% of the model's own new s/t words have the cedilla; when they keep only some, at most 30%. | 13 of 15 vs 1 of 18 new words | held |

{% enddetails %}

## What Changed in How I Think About These Models

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

{% livecodes https://livecodes.io/?mode=result&title=Cedilla%20checker&html=%3C%21doctype+html%3E%0A%3Chtml+lang%3D%22en%22%3E%0A%3Chead%3E%0A%3Cmeta+charset%3D%22utf-8%22%3E%0A%3Cmeta+name%3D%22viewport%22+content%3D%22width%3Ddevice-width%2C+initial-scale%3D1%22%3E%0A%3Ctitle%3ECedilla+checker%3C%2Ftitle%3E%0A%3Cstyle%3E%0A%3Aroot%7B--bg%3A%23fcfcfb%3B--ink%3A%231c1a17%3B--muted%3A%235f5a52%3B--line%3A%238f897e%3B--bad%3A%23b2452f%3B--badbg%3A%23fbe3dc%3B--ok%3A%231f6b58%3B--btn%3A%231c1a17%3B--btnink%3A%23fff%3B--box%3A%23fff%7D%0A%40media+%28prefers-color-scheme%3Adark%29%7B%3Aroot%7B--bg%3A%23171615%3B--ink%3A%23eeebe5%3B--muted%3A%23aaa49a%3B--line%3A%2377726a%3B--bad%3A%23ff8d74%3B--badbg%3A%234a2219%3B--ok%3A%236fd1b3%3B--btn%3A%23eeebe5%3B--btnink%3A%23171615%3B--box%3A%23201f1d%7D%7D%0A%2A%7Bbox-sizing%3Aborder-box%3Bmargin%3A0%7D%0A%5Bhidden%5D%7Bdisplay%3Anone%21important%7D%0Abody%7Bbackground%3Avar%28--bg%29%3Bcolor%3Avar%28--ink%29%3Bfont%3A15px%2F1.5+system-ui%2C-apple-system%2C%22Segoe+UI%22%2CRoboto%2Csans-serif%3Bpadding%3A14px+16px%7D%0Ah1%7Bfont-size%3A17px%3Bfont-weight%3A650%7D%0Ap.sub%7Bcolor%3Avar%28--muted%29%3Bfont-size%3A13.5px%3Bmargin%3A2px+0+12px%7D%0A.step%7Bfont-size%3A13px%3Bfont-weight%3A650%3Bletter-spacing%3A.04em%3Btext-transform%3Auppercase%3Bcolor%3Avar%28--muted%29%3Bmargin%3A10px+0+4px%7D%0Apre%2Ctextarea%2C.out%7Bwidth%3A100%25%3Bborder%3A1px+solid+var%28--line%29%3Bborder-radius%3A8px%3Bbackground%3Avar%28--box%29%3Bcolor%3Avar%28--ink%29%3Bfont%3A14px%2F1.5+system-ui%2C-apple-system%2C%22Segoe+UI%22%2CRoboto%2Csans-serif%3Bpadding%3A8px+10px%7D%0Apre%7Bwhite-space%3Apre-wrap%3Bmax-height%3A96px%3Boverflow%3Aauto%7D%0Atextarea%7Bmin-height%3A76px%3Bresize%3Avertical%7D%0A.row%7Bdisplay%3Aflex%3Bflex-wrap%3Awrap%3Bgap%3A8px%3Bmargin-top%3A6px%3Balign-items%3Acenter%7D%0Abutton%7Bfont%3A600+13.5px%2F1+system-ui%2C-apple-system%2C%22Segoe+UI%22%2Csans-serif%3Bpadding%3A8px+12px%3Bborder-radius%3A7px%3Bborder%3A1px+solid+var%28--btn%29%3Bbackground%3Avar%28--btn%29%3Bcolor%3Avar%28--btnink%29%3Bcursor%3Apointer%7D%0Abutton.ghost%7Bbackground%3Atransparent%3Bcolor%3Avar%28--ink%29%7D%0Abutton%3Afocus-visible%2Ctextarea%3Afocus-visible%2Cpre%3Afocus-visible%2C.out%3Afocus-visible%7Boutline%3A3px+solid+%232a78d6%3Boutline-offset%3A2px%7D%0A.verdict%7Bfont-weight%3A650%3Bmargin-top%3A8px%7D%0A.verdict.bad%7Bcolor%3Avar%28--bad%29%7D+.verdict.ok%7Bcolor%3Avar%28--ok%29%7D%0A.out%7Bmargin-top%3A6px%3Bmin-height%3A40px%3Bmax-height%3A150px%3Boverflow%3Aauto%7D%0Amark%7Bbackground%3Avar%28--badbg%29%3Bcolor%3Avar%28--bad%29%3Bfont-weight%3A700%3Bborder-bottom%3A2px+solid+var%28--bad%29%3Bborder-radius%3A2px%3Bpadding%3A0+1px%7D%0A.okl%7Bborder-bottom%3A2px+solid+var%28--ok%29%7D%0A.tr%7Bborder-bottom%3A2px+dotted+var%28--muted%29%7D%0A.note%7Bcolor%3Avar%28--muted%29%3Bfont-size%3A12.5px%3Bmargin-top%3A4px%7D%0A.hint%7Bcolor%3Avar%28--muted%29%3Bfont-size%3A12.5px%7D%0A.sr%7Bposition%3Aabsolute%3Bwidth%3A1px%3Bheight%3A1px%3Boverflow%3Ahidden%3Bclip%3Arect%280+0+0+0%29%3Bwhite-space%3Anowrap%7D%0A%40media+%28max-width%3A480px%29%7Bbody%7Bpadding%3A12px%7Dpre%7Bmax-height%3A72px%7D.out%7Bmax-height%3A120px%7Dbutton%7Bpadding%3A8px+9px%3Bfont-size%3A13px%7D%7D%0A%3C%2Fstyle%3E%0A%3C%2Fhead%3E%0A%3Cbody%3E%0A%3Ch1%3EDoes+your+model+copy+the+cedilla%3F%3C%2Fh1%3E%0A%3Cp+class%3D%22sub%22%3ETwo+steps.+The+check+runs+in+your+browser.+Like+my+scorer%2C+it+reads+each+letter+by+its+code+point+after+NFC.+Unlike+it%2C+it+looks+only+at+%26%23x15F%3B+%26%23x163%3B+%26%23x219%3B+%26%23x21B%3B%2C+and+it+skips+%26%23x15F%3B+in+sentences+that+look+Turkish.%3C%2Fp%3E%0A%3Ch2+class%3D%22step%22+id%3D%22s1%22%3E1+%26%23xB7%3B+Send+this+to+your+chatbot%3C%2Fh2%3E%0A%3Cpre+id%3D%22prompt%22+tabindex%3D%220%22+aria-labelledby%3D%22s1%22%3E%3C%2Fpre%3E%0A%3Cdiv+class%3D%22row%22%3E%3Cbutton+id%3D%22copyPrompt%22%3ECopy+the+prompt%3C%2Fbutton%3E%3Cspan+class%3D%22hint%22+id%3D%22copyMsg%22+aria-live%3D%22polite%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%0A%3Ch2+class%3D%22step%22+id%3D%22s2%22%3E2+%26%23xB7%3B+Paste+its+answer+here%3C%2Fh2%3E%0A%3Cp+class%3D%22note%22+id%3D%22tnote%22+style%3D%22margin%3A0+0+4px%22%3EOr+any+Romanian+text%3A+a+web+page%2C+a+database+export%2C+a+translation.%3C%2Fp%3E%0A%3Ctextarea+id%3D%22t%22+spellcheck%3D%22false%22+placeholder%3D%22Paste+here%22+aria-labelledby%3D%22s2%22+aria-describedby%3D%22tnote%22%3E%3C%2Ftextarea%3E%0A%3Cdiv+class%3D%22row%22%3E%3Cbutton+class%3D%22ghost%22+id%3D%22sample%22%3EShow+Claude+Opus+5.5%27s+real+answer%3C%2Fbutton%3E%3Cbutton+class%3D%22ghost%22+id%3D%22clear%22%3EClear%3C%2Fbutton%3E%3C%2Fdiv%3E%0A%3Cdiv+class%3D%22verdict%22+id%3D%22verdict%22%3E%3C%2Fdiv%3E%0A%3Cdiv+class%3D%22out%22+id%3D%22out%22+role%3D%22region%22+tabindex%3D%220%22+aria-label%3D%22Your+text%2C+with+the+s+and+t+letters+marked%22+hidden%3E%3C%2Fdiv%3E%0A%3Cp+class%3D%22note%22+id%3D%22legend%22+hidden%3E%3C%2Fp%3E%0A%3Cdiv+class%3D%22row%22+id%3D%22fixRow%22+hidden%3E%3Cbutton+id%3D%22fix%22%3EFix+and+copy+%28Romanian+only%29%3C%2Fbutton%3E%3Cbutton+class%3D%22ghost%22+id%3D%22undo%22+hidden%3EUndo%3C%2Fbutton%3E%3Cspan+class%3D%22hint%22+id%3D%22fixMsg%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%0A%3Cp+class%3D%22note%22+id%3D%22fixNote%22+hidden%3EThe+fix+swaps+%26%23x15F%3B+%26%23x163%3B+for+%26%23x219%3B+%26%23x21B%3B+sentence+by+sentence.+In+a+sentence+with+%26%23x131%3B%2C+%26%23x11F%3B%2C+%26%23xE7%3B%2C+%26%23xF6%3B+or+%26%23xFC%3B+it+leaves+%26%23x15F%3B+alone%2C+so+most+Turkish+keeps+its+%26%23x15F%3B%2C+but+a+short+Turkish+sentence+without+those+letters%2C+like+%22Ho%26%23x15F%3B+geldiniz%21%22%2C+still+gets+changed.+%26%23x163%3B+is+always+swapped%3A+Turkish+has+no+%26%23x163%3B.+It%27s+the+%3Ccode%3Efix_romanian%28%29%3C%2Fcode%3E+from+the+post.%3C%2Fp%3E%0A%3Cdiv+class%3D%22sr%22+id%3D%22live%22+aria-live%3D%22polite%22%3E%3C%2Fdiv%3E%0A%3Cscript%3E%0Avar+FIX+%3D+%7B%22%5Cu015F%22%3A%22%5Cu0219%22%2C%22%5Cu015E%22%3A%22%5Cu0218%22%2C%22%5Cu0163%22%3A%22%5Cu021B%22%2C%22%5Cu0162%22%3A%22%5Cu021A%22%7D%3B%0Avar+COMMA+%3D+%2F%5B%5Cu0219%5Cu0218%5Cu021B%5Cu021A%5D%2F%2C+S+%3D+%2F%5B%5Cu015F%5Cu015E%5Cu0219%5Cu0218%5D%2F%3B%0Avar+NOT_ROMANIAN+%3D+%2F%5B%5Cu0131%5Cu0130%5Cu011F%5Cu011E%5Cu00E7%5Cu00C7%5Cu00F6%5Cu00D6%5Cu00FC%5Cu00DC%5D%2F%3B%0Afunction+fixRomanian%28text%29%7B%0Areturn+text.normalize%28%22NFC%22%29.replace%28%2F%5B%5E.%21%3F%5Cn%5D%2B%2Fg%2C+function%28sentence%29%7B%0Areturn+sentence.replace%28NOT_ROMANIAN.test%28sentence%29+%3F+%2F%5B%5Cu0163%5Cu0162%5D%2Fg+%3A+%2F%5B%5Cu015F%5Cu015E%5Cu0163%5Cu0162%5D%2Fg%2C+function%28c%29%7Breturn+FIX%5Bc%5D%3B%7D%29%3B%0A%7D%29%3B%0A%7D%0Afunction+toCedilla%28s%29%7Breturn+s.replace%28%2F%5Cu0219%2Fg%2C%22%5Cu015F%22%29.replace%28%2F%5Cu0218%2Fg%2C%22%5Cu015E%22%29.replace%28%2F%5Cu021B%2Fg%2C%22%5Cu0163%22%29.replace%28%2F%5Cu021A%2Fg%2C%22%5Cu0162%22%29%3B%7D%0Afunction+cp%28c%29%7Breturn+%22U%2B0%22+%2B+c.charCodeAt%280%29.toString%2816%29.toUpperCase%28%29%3B%7D%0Avar+TEXT+%3D+%22Drumul+Transf%5Cu0103g%5Cu0103r%5Cu0103%5Cu0219an+se+%5Cu00EEnchide+%5Cu00EEn+fiecare+an+la+sf%5Cu00E2r%5Cu0219itul+lunii+octombrie%2C+iar+redeschiderea+are+loc%2C+de+obicei%2C+la+%5Cu00EEnceputul+lui+iulie.+Autorit%5Cu0103%5Cu021Bile+recomand%5Cu0103+turi%5Cu0219tilor+s%5Cu0103+verifice+starea+drumului+%5Cu00EEnainte+de+plecare%2C+deoarece+ninsorile+pot+ap%5Cu0103rea+%5Cu0219i+%5Cu00EEn+septembrie.%22%3B%0Avar+PROMPT+%3D+%22Answer+the+question+using+only+the+text+below.+Answer+in+Romanian%2C+in+one+sentence.%5Cn%5CnText%3A%5Cn%22+%2B+toCedilla%28TEXT%29+%2B+%22%5Cn%5CnQuestion%3A+When+does+the+road+usually+close%2C+and+when+does+it+reopen%3F%22%3B%0Avar+SAMPLE+%3D+%22Drumul+Transf%5Cu0103g%5Cu0103r%5Cu0103%5Cu015Fan+se+%5Cu00EEnchide+%5Cu00EEn+fiecare+an+la+sf%5Cu00E2r%5Cu015Fitul+lunii+octombrie+%5Cu015Fi+se+redeschide%2C+de+obicei%2C+la+%5Cu00EEnceputul+lunii+iulie.%22%3B%0Avar+%24+%3D+function%28id%29%7Breturn+document.getElementById%28id%29%3B%7D%3B%0A%24%28%22prompt%22%29.textContent+%3D+PROMPT%3B%0Avar+keys+%3D+matchMedia%28%22%28pointer%3Acoarse%29%22%29.matches+%3F+%22press+and+hold%2C+then+tap+Copy.%22+%3A+%22press+Ctrl%2BC+%28%5Cu2318C+on+a+Mac%29.%22%3B%0Avar+timer%3B%0Afunction+announce%28text%2C+now%29%7B+clearTimeout%28timer%29%3B+timer+%3D+setTimeout%28function%28%29%7B+%24%28%22live%22%29.textContent+%3D+text%3B+%7D%2C+now+%3F+0+%3A+700%29%3B+%7D%0Afunction+clip%28text%29%7B+return+new+Promise%28function%28done%29%7B+done%28navigator.clipboard.writeText%28text%29%29%3B+%7D%29%3B+%7D%0Afunction+copyText%28text%2C+msg%2C+box%29%7B%0Aclip%28text%29.then%28function%28%29%7B%0Amsg.textContent+%3D+%22Copied.%22%3B+clearTimeout%28msg.timer%29%3B+msg.timer+%3D+setTimeout%28function%28%29%7B+msg.textContent+%3D+%22%22%3B+%7D%2C+3000%29%3B%0A%7D%29.catch%28function%28%29%7B%0AclearTimeout%28msg.timer%29%3B%0Abox.focus%28%29%3B%0Aif+%28box.select%29+box.select%28%29%3B+else+getSelection%28%29.selectAllChildren%28box%29%3B%0Amsg.textContent+%3D+%22Selected%3A+%22+%2B+keys%3B%0A%7D%29%3B%0A%7D%0A%24%28%22copyPrompt%22%29.onclick+%3D+function%28%29%7B+copyText%28PROMPT%2C+%24%28%22copyMsg%22%29%2C+%24%28%22prompt%22%29%29%3B+%7D%3B%0Avar+before+%3D+null%3B%0Afunction+count%28k%2C+one%2C+many%29%7B+return+k+%2B+%28k+%3D%3D%3D+1+%3F+one+%3A+many%29%3B+%7D%0Afunction+check%28now%29%7B%0Avar+raw+%3D+%24%28%22t%22%29.value%2C+s+%3D+raw.normalize%28%22NFC%22%29%2C+out+%3D+%24%28%22out%22%29%2C+v+%3D+%24%28%22verdict%22%29%3B%0Avar+n+%3D+%7Bmark%3A+0%2C+okl%3A+0%2C+skip%3A+0%2C+tr%3A+0%7D%2C+sent+%3D+%7Bskip%3A+0%2C+tr%3A+0%7D%2C+seen+%3D+%7Bmark%3A+%7B%7D%2C+okl%3A+%7B%7D%2C+tr%3A+%7B%7D%7D%2C+buf+%3D+%22%22%3B%0Aout.textContent+%3D+%22%22%3B%0Av.className+%3D+%22verdict%22%3B%0Aif+%28%21s.trim%28%29%29%7B+v.textContent+%3D+%24%28%22legend%22%29.textContent+%3D+%22%22%3B+out.hidden+%3D+%24%28%22legend%22%29.hidden+%3D+true%3B+showFix%28false%29%3B+announce%28%22%22%2C+now%29%3B+return%3B+%7D%0Afor+%28var+part+of+s.match%28%2F%5B%5E.%21%3F%5Cn%5D%2B%7C%5B.%21%3F%5Cn%5D%2B%2Fg%29+%7C%7C+%5B%5D%29%7B%0Avar+turkish+%3D+NOT_ROMANIAN.test%28part%29%2C+had+%3D+%7Bskip%3A+n.skip%2C+tr%3A+n.tr%7D%3B%0Afor+%28var+ch+of+part%29%7B%0Avar+kind+%3D+%21FIX%5Bch%5D+%26%26+%21COMMA.test%28ch%29+%3F+%22%22+%3A+turkish+%26%26+S.test%28ch%29+%3F+%28FIX%5Bch%5D+%3F+%22skip%22+%3A+%22tr%22%29+%3A+FIX%5Bch%5D+%3F+%22mark%22+%3A+%22okl%22%3B%0Aif+%28%21kind%29%7B+buf+%2B%3D+ch%3B+continue%3B+%7D%0Aout.append%28buf%29%3B+buf+%3D+%22%22%3B%0Avar+e+%3D+document.createElement%28kind+%3D%3D%3D+%22mark%22+%3F+%22mark%22+%3A+%22span%22%29%3B%0Ae.className+%3D+kind+%3D%3D%3D+%22skip%22+%3F+%22tr%22+%3A+kind%3B%0Ae.textContent+%3D+ch%3B%0Ae.title+%3D+cp%28ch%29+%2B+%7Bmark%3A+%22%2C+a+cedilla%3A+wrong+in+Romanian%22%2C+okl%3A+%22%2C+the+comma+below%22%2C+skip%3A+%22%2C+a+cedilla%3A+skipped%2C+the+sentence+has+%5Cu0131+%5Cu011F+%5Cu00E7+%5Cu00F6+or+%5Cu00FC%22%2C+tr%3A+%22%2C+the+comma+below%2C+in+a+sentence+that+looks+Turkish%22%7D%5Bkind%5D%3B%0Aout.append%28e%29%3B%0An%5Bkind%5D%2B%2B%3B%0Aseen%5Be.className%5D%5Bch%5D+%3D+1%3B%0A%7D%0Aif+%28n.skip+%3E+had.skip%29+sent.skip%2B%2B%3B%0Aif+%28n.tr+%3E+had.tr%29+sent.tr%2B%2B%3B%0A%7D%0Aout.append%28buf%29%3B%0Aout.hidden+%3D+false%3B%0Avar+notes+%3D+%28n.skip+%3F+%22+Skipped+%22+%2B+n.skip+%2B+%22+%5Cu015F+in+%22+%2B+count%28sent.skip%2C+%22+sentence%22%2C+%22+sentences%22%29+%2B+%22+with+%5Cu0131+%5Cu011F+%5Cu00E7+%5Cu00F6+or+%5Cu00FC+%28Turkish%2C+or+a+name+like+Z%5Cu00FCrich+or+Erdo%5Cu011Fan%29%3A+check+by+eye.%22+%3A+%22%22%29+%2B%0A%28n.tr+%3F+%22+%22+%2B+count%28n.tr%2C+%22+%5Cu0219+is%22%2C+%22+%5Cu0219+are%22%29+%2B+%22+in+%22+%2B+%28sent.tr+%3D%3D%3D+1+%3F+%22a+sentence+that+looks%22+%3A+%22sentences+that+look%22%29+%2B+%22+Turkish%2C+and+Turkish+writes+%5Cu015F%3A+check+by+eye.%22+%3A+%22%22%29+%2B%0A%28raw+%21%3D%3D+s+%3F+%22+Some+letters+were+typed+as+two+code+points%3B+shown+here+combined.%22+%3A+%22%22%29%3B%0Avar+comma+%3D+n.okl+%3F+count%28n.okl%2C+%22+letter+has%22%2C+%22+letters+have%22%29+%2B+%22+the+comma+below+%28%5Cu0219+%5Cu021B%29.%22+%3A+%22None+has+the+comma+below+%28%5Cu0219+%5Cu021B%29.%22%3B%0Aif+%28n.mark%29%7B%0Av.className+%3D+%22verdict+bad%22%3B%0Av.textContent+%3D+count%28n.mark%2C+%22+letter+has%22%2C+%22+letters+have%22%29+%2B+%22+a+cedilla+%28%5Cu015F+%5Cu0163%29%2C+marked+red+below.+%22+%2B+comma+%2B+notes%3B%0A%7D+else+if+%28n.skip+%7C%7C+n.tr%29+v.textContent+%3D+%22Nothing+marked+red.%22+%2B+%28n.okl+%3F+%22+%22+%2B+comma+%3A+%22%22%29+%2B+notes%3B%0Aelse+if+%28n.okl%29%7B%0Av.className+%3D+%22verdict+ok%22%3B%0Av.textContent+%3D+%28n.okl+%3D%3D%3D+1+%3F+%22Clean%3A+the+one+s%2Ft+letter+has%22+%3A+%22Clean%3A+all+%22+%2B+n.okl+%2B+%22+s%2Ft+letters+have%22%29+%2B+%22+the+comma+below+%28%5Cu0219+%5Cu021B%29.%22+%2B+notes%3B%0A%7D+else+v.textContent+%3D+%22No+%5Cu0219%2C+%5Cu021B%2C+%5Cu015F+or+%5Cu0163+here.+My+scorer+fails+an+answer+with+no+%5Cu0219+or+%5Cu021B%3A+did+the+model+drop+the+diacritics%3F%22+%2B+notes%3B%0Afunction+list%28o%29%7B+return+Object.keys%28o%29.map%28function%28c%29%7B+return+c+%2B+%22+%22+%2B+cp%28c%29%3B+%7D%29.join%28%22%2C+%22%29%3B+%7D%0A%24%28%22legend%22%29.textContent+%3D+%28n.mark+%3F+%22Red%3A+a+cedilla%2C+%22+%2B+list%28seen.mark%29+%2B+%22.+%22+%3A+%22%22%29+%2B+%28n.okl+%3F+%22Green+line%3A+the+comma+below%2C+%22+%2B+list%28seen.okl%29+%2B+%22.+%22+%3A+%22%22%29+%2B%0A%28n.skip+%7C%7C+n.tr+%3F+%22Grey+dots%3A+in+a+sentence+that+looks+Turkish%2C+%22+%2B+list%28seen.tr%29+%2B+%22.%22+%3A+%22%22%29%3B%0A%24%28%22legend%22%29.hidden+%3D+%21%24%28%22legend%22%29.textContent%3B%0AshowFix%28n.mark+%3E+0%29%3B%0Aannounce%28v.textContent%2C+now%29%3B%0A%7D%0Afunction+showFix%28fixable%29%7B%0A%24%28%22fix%22%29.hidden+%3D+%21fixable%3B%0A%24%28%22undo%22%29.hidden+%3D+before+%3D%3D%3D+null%3B%0A%24%28%22fixRow%22%29.hidden+%3D+%24%28%22fixNote%22%29.hidden+%3D+%21fixable+%26%26+before+%3D%3D%3D+null%3B%0A%7D%0Afunction+reset%28text%29%7B+before+%3D+null%3B+%24%28%22fixMsg%22%29.textContent+%3D+%22%22%3B+if+%28text+%21%3D%3D+undefined%29+%24%28%22t%22%29.value+%3D+text%3B+%7D%0A%24%28%22t%22%29.oninput+%3D+function%28%29%7B+reset%28%29%3B+check%28false%29%3B+%7D%3B%0A%24%28%22sample%22%29.onclick+%3D+function%28%29%7B+reset%28SAMPLE%29%3B+check%28true%29%3B+%7D%3B%0A%24%28%22clear%22%29.onclick+%3D+function%28%29%7B+reset%28%22%22%29%3B+check%28true%29%3B+%24%28%22t%22%29.focus%28%29%3B+%7D%3B%0A%24%28%22fix%22%29.onclick+%3D+function%28%29%7B%0Avar+t+%3D+%24%28%22t%22%29%2C+fixed+%3D+fixRomanian%28t.value%29%3B%0Abefore+%3D+t.value%3B%0At.value+%3D+fixed%3B%0Acheck%28true%29%3B%0Afunction+say%28text%29%7B+%24%28%22fixMsg%22%29.textContent+%3D+text%3B+announce%28%24%28%22verdict%22%29.textContent+%2B+%22+%22+%2B+text%2C+true%29%3B+%7D%0Aclip%28fixed%29.then%28function%28%29%7B+say%28%22Fixed+and+copied.%22%29%3B+%24%28%22undo%22%29.focus%28%29%3B+%7D%29.catch%28function%28%29%7B%0At.focus%28%29%3B+t.select%28%29%3B+say%28%22Fixed.+The+text+in+the+box+is+selected%3A+%22+%2B+keys%29%3B%0A%7D%29%3B%0A%7D%3B%0A%24%28%22undo%22%29.onclick+%3D+function%28%29%7B+reset%28before%29%3B+check%28true%29%3B+%24%28%22t%22%29.focus%28%29%3B+%7D%3B%0A%3C%2Fscript%3E%0A%3C%2Fbody%3E%0A%3C%2Fhtml%3E%0A height=760 %}

## What I'd Measure Next

Whether the echo survives a real retrieval pipeline, which cleans and chunks documents first, and whether other languages with a look-alike letter from an old encoding echo it too. Does yours have a pair like ş and ș? Tell me in the comments.

## My Benchmark

{% cta https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below %} Romanian Comma Below on Kaggle {% endcta %}

Thirteen tasks, with every model answer in the run outputs. This post's numbers come from the runs up to 10 October; later runs on the leaderboard aren't in them. Read task 8's leaderboard rather than the overall score, which averages different tasks for different models. It uses each model's latest run and counts an empty answer as a failure, which is why Qwen 3 Next Thinking shows 45% and Grok 4.5 and 4.6 (listed by Kaggle, but every call errored, so they're not among my 44) 0%.

{% details All the numbers (the 15 first-round models) %}

Task scores in %. Echo with cedilla is the mean of every run on the same prompts (tasks 2 and 8); Echo + rule pools tasks 7 and 8. See counts the first true/false or code point in each answer, as Kaggle does: DeepSeek-R1 listed every letter's code point before giving the right one, so on its final answers it scores 100 (Gemini 3.5 Flash-Lite 89).

| Model | Write | Echo: cedilla | Echo: no diacritics | Echo + rule | Fix | See | Restore | Code |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 3 235B | 92 | 85 | 100 | 93 | 89 | 89 | 90 | 61 |
| Gemini 3.1 Pro | 100 | 81 | 95 | 100 | 100 | 97 | 100 | 86 |
| Gemini 3.7 Flash | 100 | 76 | 100 | 100 | 100 | 97 | 100 | 86 |
| Gemini 3.8 Flash | 100 | 70 | 100 | 100 | 100 | 81 | 100 | 93 |
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

The task builder, the fake models that test the scorer, the analysis and a script that re-checks this post's numbers against the raw answers are on [GitHub](https://github.com/danielbutnar/comma-below). Every input is generated from correctly spelled text in `src/items.py`, so testing another letter pair or language is a small change. Built with [kaggle-benchmarks](https://pypi.org/project/kaggle-benchmarks/); the checker runs on [LiveCodes](https://livecodes.io). I used Claude as a coding and editing assistant.

If your pipeline touches Romanian, run `fix_romanian()` on the way in and on the way out. And if your language has its own ş, tell me in the comments.
