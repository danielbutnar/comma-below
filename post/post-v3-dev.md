---
title: Braşov or Brașov? 43 LLMs copy my wrong letter into a third of their answers
published: true
tags: devchallenge, kagglechallenge, ai, machinelearning
cover_image: https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/cover-v2.png
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

- **The keyboard echo: a third of the answers keep my wrong letter.** I gave 43 models the same 22 Romanian prompts, typed four ways. Typed correctly or without any diacritics, 96 to 99 % of the answers came back clean. Typed with the cedilla letters, 68 %. When an answer copies all of my cedillas, the model's own new words get them too.
- **Newer can be worse.** Claude Opus 4.8 kept 95 % of its answers clean, Opus 5 55 %, run after run.
- **One sentence in the system prompt fixes most of it, and breaks Turkish**, where the cedilla letter is right. A short function that leaves Turkish sentences alone fixed every broken answer.

![Typed with the cedilla, a third of the answers keep it. 43 models, the same 22 prompts typed four ways: 99 % of answers clean when typed correctly, 96 % without diacritics, 68 % with the cedilla, 95 % with the cedilla and one sentence in the system prompt](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-hero.png)

## What I Benchmarked

If you couldn't tell which answer was wrong, neither could the 10 Romanians I asked to compare twelve word pairs like these on their own screens: they got 50 % right, what guessing gets. Even I, knowing what to look for, got 9 of 12. The models caught 89 of the 90 real differences. You can [take the two-minute test](https://danielbutnar.github.io/comma-below/human/test.html?from=dev) yourself.

Romanian has two letters with a comma underneath, **ș** and **ț** (U+0219, U+021B). The encodings Romanian computers used in the 1990s didn't have them, so people typed the Turkish **ş** and a **ţ** with a cedilla (U+015F, U+0163) instead. Unicode added the right letters in 1999. When I fetched the front pages of 35 Romanian sites on 30 September, 29 still had cedilla letters in Romanian words, the government's press releases among them.

To a computer they are different characters: `"Brașov" == "Braşov"` is `false`. The cedilla spelling is also all over the text that models learn from and that retrieval systems hand them. So I asked two things. Do models write the right letter? And what do they do when the text they read has the wrong one?

Every prompt comes in versions that differ only in how the letters are typed. A script, not an LLM, scores each answer by its Unicode code points after NFC normalization. I tested it first on fake models (one that copies its input scores 0 %, one that fixes everything 100 %) and checked the answer keys as a native speaker. For round two I wrote my predictions into each task's description on Kaggle before running it. 4 of the 20 failed.

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

**44 models.** Round one (30 September – 1 October) ran 15 models on the first seven tasks. Round two (8–11 October) ran the four-way test on every model Kaggle would serve and the follow-up tests on 10 to 28 of them. GPT-6 Astra's runs of the four-way test failed, so that test has 43 models. I picked the lineup for two comparisons: versions of the same model on identical prompts (Claude Opus 4.5 to 5.5, Gemini Flash 2.5 to 3.8, GPT-5.4 to GPT-6.1), and the same model with reasoning on and off (Grok 4.20, Qwen 3 Next). Everything ran on Kaggle's model proxy with default settings and an 8,192-token cap, for $30.19 of the free quota. Qwen 3 Next Thinking mostly ran out of tokens before answering.

{% details Full model list %}

**Anthropic:** Claude Haiku 4.5, Claude Opus 4.5, Claude Opus 4.6, Claude Opus 4.7, Claude Opus 4.8, Claude Opus 5.5, Claude Opus 5, Claude Sonnet 4.5, Claude Sonnet 4.6, Claude Sonnet 5.5, Claude Sonnet 5. **Google:** Gemini 2.5 Flash, Gemini 2.5 Pro, Gemini 3 Flash, Gemini 3.1 Flash-Lite, Gemini 3.1 Pro, Gemini 3.5 Flash, Gemini 3.5 Flash-Lite, Gemini 3.6 Flash, Gemini 3.7 Flash, Gemini 3.8 Flash, Gemma 4 26B A4B, Gemma 4 31B. **OpenAI:** GPT-5.4, GPT-5.4 mini, GPT-5.4 nano, GPT-5.5, GPT-5.6 Luna, GPT-5.6 Sol, GPT-5.6 Terra, GPT-6 Astra, GPT-6 Luna, GPT-6 Sol, GPT-6.1 Sol, gpt-oss-120b, gpt-oss-20b. **xAI:** Grok 4.20 Non-Reasoning, Grok 4.20 Reasoning. **DeepSeek:** DeepSeek-R1. **Alibaba:** Qwen 3 235B, Qwen 3 Coder 480B, Qwen 3 Next 80B Instruct, Qwen 3 Next 80B Thinking. **Zhipu:** GLM-5.

{% enddetails %}

## Findings

### 1. Models restore missing diacritics but keep wrong ones

Many Romanians type without diacritics at all ("Brasov"). Given the 22 prompts that way, the models put the letters back: 96 % of answers came back clean. Given the same prompts with cedillas, 68 % did.

They can tell. The same 15 first-round models wrote ș and ț correctly from English prompts (98 %), spotted the cedilla in every sentence typed with it, and fixed 99 % of answers when told to correct the diacritics. If anything they see differences that aren't there: shown two identical words with the letter, they called them different a third of the time. They just don't fix it unless asked, and they never mention it: not one of the 3,160 answers to text typed with cedillas did.

DeepSeek-R1 shows its reasoning, so I could check whether it even notices. Without the rule, it mentioned the letters in 3 of 88 answers. With the rule, in 43 of 44, and 6 of those still came out with cedillas. In one, it planned "proper Romanian orthography with ș/ț commas below, not cedillas" and then answered: "Autorităţile recomandă turiştilor să verifice starea drumului înainte de plecare." Both letters carry the cedilla. Reasoning didn't help Grok 4.20 either: 41 % clean with it, 45 % without.

### 2. The keyboard echo: the model's own words get my cedilla too

![When an answer kept all of my cedillas, 95 % of the new ș/ț words the model chose itself had the cedilla too; when it kept only some, 10 %](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-keyboard.png)

Summaries and answers from a document reuse my words, so they copy the most: answers from a document came back clean only 52 % of the time, guest replies 96 %. And it's mostly all or nothing: 75 % of the answers that kept one of my cedillas kept all of them.

What surprised me were the words the model added itself. They can't be copied, so their spelling shows which keyboard the model is typing on. In answers that kept all of my cedillas, 95 % of the new ș/ț words had the cedilla too; in answers that kept only some, 10 %. The gap holds inside each of the two models with enough words of both kinds to check, and in a fresh run on 28 models, where I had written it down as a prediction: 13 of 15 new words against 1 of 18.

That is the keyboard echo: the model picks up my keyboard and types the whole answer on it. Claude Opus 5 rewrote a city-hall notice that said *rugați* ("asked") as *îndrumaţi* ("directed"), a word my text didn't have, cedilla included. Opus 4.6 and GPT-5.6 Luna made the same move.

The text the model answers from sets the keyboard; the documents around it turn the echo up or down. I put each question's document among three others and typed 0, 1 or 3 of the others with cedillas. Around a clean document, the neighbours hardly mattered: at least 95 % of answers stayed clean at every level, and only Claude Opus 5 and Claude Sonnet 5 slipped at all. Around a cedilla document, they did: 78 % of answers came back clean with three clean neighbours, 36 % with three cedilla ones, and 14 of the 15 models moved that way, none the other. In a chat, a cedilla first message rarely changed the next answer.

### 3. Only the cedilla echoes: a dot below and mojibake get repaired

![Of three wrong spellings, only the cedilla survives: 38 % of s and t letters came back with the cedilla, 0.9 % with a dot below, 1.4 % as mojibake](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-wrong.png)

Why the cedilla? Before a fresh run, I wrote down a test that could fail. I typed the same summaries and document questions two more ways: with s and t with a dot below (Braṣov), letters that look almost exactly like the right ones and exist in Yoruba and in transliteration but not in Romanian, and as the mojibake that old Romanian pages and subtitles often showed (Braºov), which looks broken.

On 28 models, the cedilla came back in 38 % of the s and t letters. The dot below came back in 0.9 % and the mojibake in 1.4 %. 27 of the 28 models kept the dot less often than the cedilla, and none kept it more.

So my guess was wrong: the dot below looks just as right, and the models fixed it. Of the three wrong spellings they keep only the cedilla, the one real Romanian text is full of, and the right letter in Turkish. This test can't tell which of those two makes it stick.

### 4. An upgrade can make it worse: Claude Opus 5 kept 55 % clean, Opus 4.8 kept 95 %

![Of 19 upgrades on the same prompts, the biggest drops were Claude Opus 4.8 to 5 (95 to 55 % clean) and Sonnet 4.6 to 5 (95 to 59 %)](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-upgrades.png)

Kaggle serves several versions of the same models, so I could compare them on identical prompts. Opus 4.8 kept 95 % of its answers clean and Opus 5 55 %; Sonnet 4.6 95 % and Sonnet 5 59 %. Both drops survive a correction for the 19 upgrades I compared. GPT Luna went the other way, from 64 % to 89 %.

These aren't one-run flukes. Opus 5 scored between 50 and 59 % in all four of its runs, from 30 September to 9 October, and the fresh run put both pairs of versions in the same order. Single answers do flip between identical runs (26 % of model-and-prompt pairs in round one), but a model's overall rate barely moves: a median of 5 points. So test every upgrade, and run it more than once.

### 5. One sentence stops the echo, and breaks Turkish

![Romanian answers clean and Turkish replies intact under each fix: a Romanian-only swap in code cleans every Romanian answer and changes 5 of 112 Turkish replies](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-fixes.png)

One sentence in the system prompt, *"Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them."*, lifted clean answers on cedilla input from 68 % to 95 % (on the harder summaries and document questions in the chart, from 53 % to 93 %).

Then I remembered where the cedilla came from. It's the Turkish letter, and in Turkish it's correct. A guesthouse bot in Brașov gets Turkish guests too, so I sent the same bot eight messages in Turkish. Without the rule, 100 % of the replies were correct. With it, 69 % were: some switched to Romanian, some avoided the letter, some spelled Turkish with the Romanian one. Gemini 3.7 Flash offered a honeymoon couple a "**muhteșem** dağ manzaralı" room and a "**Șarap** tadımı". Adding "this applies to Romanian only" brought Turkish back to 94 %. (A script sorted the replies by language; I checked every flagged word by hand. No native speaker checked the Turkish.)

A few lines of code do better. The usual fix, swapping every ş for ș, broke all 112 correct Turkish replies. Doing the same swap only in sentences without ı, ğ, ç, ö or ü changed 5 of them and still fixed every Romanian answer.

## What I got wrong

- **My predictions.** 4 of the 20 failed and 2 more were mixed or too close to call. Most were directions, with thresholds I set when scoring; the look-alike test had its thresholds written down first, and all 5 of its predictions held. The full table is below.
- **My upload.** The Kaggle CLI reads task files with the system encoding, cp1250 on my laptop, so my first task file would have uploaded "Brașov" as "BraČ™ov". The task files are now pure ASCII and check a hash of their data before running.
- **My first fix.** The `fix_romanian()` in the first version of this post broke Turkish, the same way the one-sentence rule does.

{% details All the predictions, scored %}

| Task | Prediction | Result | |
| --- | --- | --- | --- |
| 8 | Correct input stays near 100 % for every model. | lowest: gpt-oss-120b and gpt-oss-20b, 82 % | **failed** |
| 8 | Cedilla input fails far more often than input without diacritics. | 96 % vs 68 % clean answers | held |
| 8 | Newer versions in a family copy the cedilla at least as often as older ones. | of 19 upgrades, 3 copied more and 1 copied less (p < 0.05); no overall trend (rank correlation -0.29) | mixed |
| 8 | The one-sentence rule lifts cedilla input to at least 90 % for most models. | 36 of 43 models at 90 % or more | held |
| 9 | With a clean target, answers stay clean for most models even when the other three documents are cedilla. | 13 of 15 models at 90 % or more | held |
| 9 | The models that rewrite whole answers in cedilla are the ones whose clean-target answers get infected. | rank correlation +0.27 over 14 models | **failed** |
| 9 | A cedilla target is copied less when the other documents are clean. | 78 % vs 36 % clean answers | held |
| 10 | Without a rule, Turkish replies keep ş. | 100 % correct | held |
| 10 | Task 7's rule makes some models write Turkish with the Romanian comma letter. | 6 of 14 models, 16 replies | held |
| 10 | The scoped rule keeps Turkish intact and still fixes Romanian. | Turkish 94 % correct (no rule: 100 %, full rule: 69 %), Romanian 99 % | **failed** |
| 11 | Correct English input stays near 100 %. | 100 % | held |
| 11 | Cyrillic look-alikes are copied far more often than mojibake. | clean answers: 95 % with look-alikes in the names, 80 % with mojibake | **failed** |
| 11 | The models that copy the Romanian cedilla most also copy the look-alikes most. | rank correlation +0.55 over 10 models | held |
| 12 | A cedilla first text infects some clean second summaries, mostly after a cedilla first summary. | 3 % infected (2 of 60 conversations); 11 % when the first summary was itself in cedilla | held |
| 12 | A clean first text does not protect a cedilla second text much. | 83 % clean after a clean first text, 69 % on its own (task 8 summaries) | inconclusive |
| 13 | The dot below is kept in a smaller share of s/t letters than the cedilla (paired, 95 % interval below zero). | 0.9 % vs 38.1 % of letters kept (-37 points, -45 to -29) | held |
| 13 | The old mojibake is also kept less often than the cedilla. | 1.4 % vs 38.1 % (-37 points, -44 to -29) | held |
| 13 | Repaired dot-below and mojibake letters become comma-below letters in at least 90 % of cases. | 98 % comma, 1.6 % cedilla | held |
| 13 | Both rules give at least 90 % clean answers, and the scoped rule is within 5 points of the full rule. | scoped 94 %, full 93 % | held |
| 13 | In cedilla answers that keep every cedilla, at least 80 % of the model's own new s/t words have the cedilla; when they keep only some, at most 30 %. | 13 of 15 vs 1 of 18 new words | held |

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

It would skip a Romanian sentence that quotes a name like Zürich. In my 352 broken answers it never missed a letter.

Want to know whether your model does it? Paste one of its answers below. Every cedilla letter turns red.

{% livecodes https://livecodes.io/?mode=result&title=Cedilla%20checker&html=%3C%21doctype%20html%3E%0A%3Chtml%20lang%3D%22en%22%3E%0A%3Chead%3E%0A%3Cmeta%20charset%3D%22utf-8%22%3E%0A%3Cmeta%20name%3D%22viewport%22%20content%3D%22width%3Ddevice-width%2C%20initial-scale%3D1%22%3E%0A%3Ctitle%3ECedilla%20checker%3C%2Ftitle%3E%0A%3Cstyle%3E%0A%3Aroot%7B--bg%3A%23fcfcfb%3B--ink%3A%231c1a17%3B--muted%3A%235f5a52%3B--line%3A%23d9d4ca%3B--bad%3A%23b2452f%3B--badbg%3A%23fbe3dc%3B--ok%3A%231f6b58%3B--btn%3A%231c1a17%3B--btnink%3A%23fff%3B--box%3A%23fff%7D%0A%40media%20%28prefers-color-scheme%3Adark%29%7B%3Aroot%7B--bg%3A%23171615%3B--ink%3A%23eeebe5%3B--muted%3A%23aaa49a%3B--line%3A%233a3733%3B--bad%3A%23ff8d74%3B--badbg%3A%234a2219%3B--ok%3A%236fd1b3%3B--btn%3A%23eeebe5%3B--btnink%3A%23171615%3B--box%3A%23201f1d%7D%7D%0A%2A%7Bbox-sizing%3Aborder-box%3Bmargin%3A0%7D%0A%5Bhidden%5D%7Bdisplay%3Anone%21important%7D%0Abody%7Bbackground%3Avar%28--bg%29%3Bcolor%3Avar%28--ink%29%3Bfont%3A15px%2F1.5%20system-ui%2C-apple-system%2C%22Segoe%20UI%22%2CRoboto%2Csans-serif%3Bpadding%3A14px%2016px%7D%0Ah1%7Bfont-size%3A17px%3Bfont-weight%3A650%7D%0Ap.sub%7Bcolor%3Avar%28--muted%29%3Bfont-size%3A13.5px%3Bmargin%3A2px%200%2012px%7D%0A.step%7Bfont-size%3A13px%3Bfont-weight%3A650%3Bletter-spacing%3A.04em%3Btext-transform%3Auppercase%3Bcolor%3Avar%28--muted%29%3Bmargin%3A10px%200%204px%7D%0Apre%2Ctextarea%2C.out%7Bwidth%3A100%25%3Bborder%3A1px%20solid%20var%28--line%29%3Bborder-radius%3A8px%3Bbackground%3Avar%28--box%29%3Bcolor%3Avar%28--ink%29%3Bfont%3A14px%2F1.5%20system-ui%2C-apple-system%2C%22Segoe%20UI%22%2CRoboto%2Csans-serif%3Bpadding%3A8px%2010px%7D%0Apre%7Bwhite-space%3Apre-wrap%3Bmax-height%3A96px%3Boverflow%3Aauto%7D%0Atextarea%7Bmin-height%3A76px%3Bresize%3Avertical%7D%0A.row%7Bdisplay%3Aflex%3Bflex-wrap%3Awrap%3Bgap%3A8px%3Bmargin-top%3A6px%3Balign-items%3Acenter%7D%0Abutton%7Bfont%3A600%2013.5px%2F1%20system-ui%2C-apple-system%2C%22Segoe%20UI%22%2Csans-serif%3Bpadding%3A8px%2012px%3Bborder-radius%3A7px%3Bborder%3A1px%20solid%20var%28--btn%29%3Bbackground%3Avar%28--btn%29%3Bcolor%3Avar%28--btnink%29%3Bcursor%3Apointer%7D%0Abutton.ghost%7Bbackground%3Atransparent%3Bcolor%3Avar%28--ink%29%7D%0Abutton%3Afocus-visible%2Ctextarea%3Afocus-visible%7Boutline%3A3px%20solid%20%232a78d6%3Boutline-offset%3A2px%7D%0A.verdict%7Bfont-weight%3A650%3Bmargin-top%3A8px%7D%0A.verdict.bad%7Bcolor%3Avar%28--bad%29%7D%20.verdict.ok%7Bcolor%3Avar%28--ok%29%7D%0A.out%7Bmargin-top%3A6px%3Bmin-height%3A40px%7D%0Amark%7Bbackground%3Avar%28--badbg%29%3Bcolor%3Avar%28--bad%29%3Bfont-weight%3A700%3Bborder-bottom%3A2px%20solid%20var%28--bad%29%3Bborder-radius%3A2px%3Bpadding%3A0%201px%7D%0A.okl%7Bborder-bottom%3A2px%20dotted%20var%28--ok%29%7D%0A.tr%7Bborder-bottom%3A2px%20dotted%20var%28--muted%29%7D%0A.note%7Bcolor%3Avar%28--muted%29%3Bfont-size%3A12.5px%3Bmargin-top%3A4px%7D%0A.hint%7Bcolor%3Avar%28--muted%29%3Bfont-size%3A12.5px%7D%0A%3C%2Fstyle%3E%0A%3C%2Fhead%3E%0A%3Cbody%3E%0A%3Ch1%3EDoes%20your%20model%20copy%20the%20cedilla%3F%3C%2Fh1%3E%0A%3Cp%20class%3D%22sub%22%3ETwo%20steps.%20The%20check%20runs%20in%20your%20browser%2C%20the%20same%20way%20my%20scorer%20does%3A%20NFC%20first%2C%20then%20each%20letter%20by%20its%20code%20point.%3C%2Fp%3E%0A%3Cdiv%20class%3D%22step%22%3E1%20%26%23xB7%3B%20Send%20this%20to%20your%20chatbot%3C%2Fdiv%3E%0A%3Cpre%20id%3D%22prompt%22%3E%3C%2Fpre%3E%0A%3Cdiv%20class%3D%22row%22%3E%3Cbutton%20id%3D%22copyPrompt%22%3ECopy%20the%20prompt%3C%2Fbutton%3E%3Cspan%20class%3D%22hint%22%20id%3D%22copyMsg%22%20aria-live%3D%22polite%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%0A%3Cdiv%20class%3D%22step%22%3E2%20%26%23xB7%3B%20Paste%20its%20answer%20here%3C%2Fdiv%3E%0A%3Clabel%20for%3D%22t%22%20class%3D%22note%22%20style%3D%22display%3Ablock%3Bmargin%3A0%200%204px%22%3EOr%20any%20Romanian%20text%3A%20a%20web%20page%2C%20a%20database%20export%2C%20a%20translation.%3C%2Flabel%3E%0A%3Ctextarea%20id%3D%22t%22%20spellcheck%3D%22false%22%20placeholder%3D%22Paste%20here%22%3E%3C%2Ftextarea%3E%0A%3Cdiv%20class%3D%22row%22%3E%3Cbutton%20class%3D%22ghost%22%20id%3D%22sample%22%3EShow%20me%20an%20example%20answer%3C%2Fbutton%3E%3Cbutton%20class%3D%22ghost%22%20id%3D%22clear%22%3EClear%3C%2Fbutton%3E%3C%2Fdiv%3E%0A%3Cdiv%20class%3D%22verdict%22%20id%3D%22verdict%22%20aria-live%3D%22polite%22%3E%3C%2Fdiv%3E%0A%3Cdiv%20class%3D%22out%22%20id%3D%22out%22%20hidden%3E%3C%2Fdiv%3E%0A%3Cdiv%20class%3D%22row%22%20id%3D%22fixRow%22%20hidden%3E%3Cbutton%20id%3D%22fix%22%3EFix%20it%20%28Romanian%20only%29%3C%2Fbutton%3E%3Cspan%20class%3D%22hint%22%20id%3D%22fixMsg%22%20aria-live%3D%22polite%22%3E%3C%2Fspan%3E%3C%2Fdiv%3E%0A%3Cp%20class%3D%22note%22%20id%3D%22fixNote%22%20hidden%3EThe%20fix%20swaps%20%26%23x15F%3B%20%26%23x163%3B%20for%20%26%23x219%3B%20%26%23x21B%3B%20sentence%20by%20sentence%20and%20skips%20sentences%20with%20%26%23x131%3B%2C%20%26%23x11F%3B%2C%20%26%23xE7%3B%2C%20%26%23xF6%3B%20or%20%26%23xFC%3B%2C%20so%20Turkish%20keeps%20its%20%26%23x15F%3B.%20It%27s%20the%20%3Ccode%3Efix_romanian%28%29%3C%2Fcode%3E%20from%20the%20post.%3C%2Fp%3E%0A%3Cscript%3E%0A%2F%2F%20Letters%2C%20by%20code%20point%2C%20so%20nothing%20depends%20on%20how%20this%20file%20was%20saved.%0Avar%20CED%20%3D%20%7B%22%5Cu015F%22%3A%22U%2B015F%20s%20with%20cedilla%22%2C%22%5Cu015E%22%3A%22U%2B015E%20S%20with%20cedilla%22%2C%22%5Cu0163%22%3A%22U%2B0163%20t%20with%20cedilla%22%2C%22%5Cu0162%22%3A%22U%2B0162%20T%20with%20cedilla%22%7D%3B%0Avar%20COM%20%3D%20%7B%22%5Cu0219%22%3A%22U%2B0219%20s%20with%20comma%20below%22%2C%22%5Cu0218%22%3A%22U%2B0218%20S%20with%20comma%20below%22%2C%22%5Cu021B%22%3A%22U%2B021B%20t%20with%20comma%20below%22%2C%22%5Cu021A%22%3A%22U%2B021A%20T%20with%20comma%20below%22%7D%3B%0Avar%20FIX%20%3D%20%7B%22%5Cu015F%22%3A%22%5Cu0219%22%2C%22%5Cu015E%22%3A%22%5Cu0218%22%2C%22%5Cu0163%22%3A%22%5Cu021B%22%2C%22%5Cu0162%22%3A%22%5Cu021A%22%7D%3B%0Avar%20NOT_ROMANIAN%20%3D%20%2F%5B%5Cu0131%5Cu0130%5Cu011F%5Cu011E%5Cu00E7%5Cu00C7%5Cu00F6%5Cu00D6%5Cu00FC%5Cu00DC%5D%2F%3B%20%20%2F%2F%20letters%20Turkish%20uses%20and%20Romanian%20never%20does%0Afunction%20fixRomanian%28text%29%7B%0Areturn%20text.normalize%28%22NFC%22%29.replace%28%2F%5B%5E.%21%3F%5Cn%5D%2B%2Fg%2C%20function%28sentence%29%7B%0Areturn%20NOT_ROMANIAN.test%28sentence%29%20%3F%20sentence%20%3A%20sentence.replace%28%2F%5B%5Cu015F%5Cu015E%5Cu0163%5Cu0162%5D%2Fg%2C%20function%28c%29%7Breturn%20FIX%5Bc%5D%3B%7D%29%3B%0A%7D%29%3B%0A%7D%0Afunction%20toCedilla%28s%29%7Breturn%20s.replace%28%2F%5Cu0219%2Fg%2C%22%5Cu015F%22%29.replace%28%2F%5Cu0218%2Fg%2C%22%5Cu015E%22%29.replace%28%2F%5Cu021B%2Fg%2C%22%5Cu0163%22%29.replace%28%2F%5Cu021A%2Fg%2C%22%5Cu0162%22%29%3B%7D%0A%2F%2F%20Task%208%2C%20prompt%20Q02%20of%20the%20benchmark%2C%20typed%20with%20cedillas.%0Avar%20TEXT%20%3D%20%22Drumul%20Transf%5Cu0103g%5Cu0103r%5Cu0103%5Cu0219an%20se%20%5Cu00EEnchide%20%5Cu00EEn%20fiecare%20an%20la%20sf%5Cu00E2r%5Cu0219itul%20lunii%20octombrie%2C%20iar%20redeschiderea%20are%20loc%2C%20de%20obicei%2C%20la%20%5Cu00EEnceputul%20lui%20iulie.%20Autorit%5Cu0103%5Cu021Bile%20recomand%5Cu0103%20turi%5Cu0219tilor%20s%5Cu0103%20verifice%20starea%20drumului%20%5Cu00EEnainte%20de%20plecare%2C%20deoarece%20ninsorile%20pot%20ap%5Cu0103rea%20%5Cu0219i%20%5Cu00EEn%20septembrie.%22%3B%0Avar%20PROMPT%20%3D%20%22Answer%20the%20question%20using%20only%20the%20text%20below.%20Answer%20in%20Romanian%2C%20in%20one%20sentence.%5Cn%5CnText%3A%5Cn%22%20%2B%20toCedilla%28TEXT%29%20%2B%20%22%5Cn%5CnQuestion%3A%20When%20does%20the%20road%20usually%20close%2C%20and%20when%20does%20it%20reopen%3F%22%3B%0A%2F%2F%20A%20real%20answer%20to%20the%20same%20kind%20of%20input%20%28Claude%20Opus%205%2C%20first%20round%29.%0Avar%20SAMPLE%20%3D%20toCedilla%28%22Prim%5Cu0103ria%20Bra%5Cu0219ov%20anun%5Cu021B%5Cu0103%20%5Cu00EEnchiderea%20Pie%5Cu021Bei%20Sfatului%20pentru%20traficul%20auto%20%5Cu00EEn%20weekend%2C%20%5Cu00EEntre%20orele%208%20%5Cu0219i%2020%2C%20din%20cauza%20t%5Cu00E2rgului%20de%20toamn%5Cu0103.%20%5Cu0218oferii%20sunt%20%5Cu00EEndruma%5Cu021Bi%20s%5Cu0103%20parcheze%20pe%20strada%20Mure%5Cu0219enilor%20sau%20l%5Cu00E2ng%5Cu0103%20Gara%20Bra%5Cu0219ov.%22%29%3B%0Avar%20%24%20%3D%20function%28id%29%7Breturn%20document.getElementById%28id%29%3B%7D%3B%0A%24%28%22prompt%22%29.textContent%20%3D%20PROMPT%3B%0Afunction%20copyText%28text%2C%20msgEl%2C%20fallbackEl%29%7B%0Afunction%20ok%28%29%7BmsgEl.textContent%20%3D%20%22Copied.%22%3B%7D%0Afunction%20manual%28%29%7B%0Aif%20%28fallbackEl%29%7BfallbackEl.focus%28%29%3B%20if%20%28fallbackEl.select%29%20fallbackEl.select%28%29%3B%20else%20%7Bvar%20r%3Ddocument.createRange%28%29%3B%20r.selectNodeContents%28fallbackEl%29%3B%20var%20s%3DgetSelection%28%29%3B%20s.removeAllRanges%28%29%3B%20s.addRange%28r%29%3B%7D%7D%0AmsgEl.textContent%20%3D%20%22Selected.%20Press%20Ctrl%2BC%20%28%5Cu2318C%20on%20a%20Mac%29.%22%3B%0A%7D%0Aif%20%28navigator.clipboard%20%26%26%20navigator.clipboard.writeText%29%7Bnavigator.clipboard.writeText%28text%29.then%28ok%2C%20manual%29%3B%7D%20else%20manual%28%29%3B%0A%7D%0A%24%28%22copyPrompt%22%29.onclick%20%3D%20function%28%29%7BcopyText%28PROMPT%2C%20%24%28%22copyMsg%22%29%2C%20%24%28%22prompt%22%29%29%3B%7D%3B%0Afunction%20check%28%29%7B%0Avar%20raw%20%3D%20%24%28%22t%22%29.value%2C%20s%20%3D%20raw.normalize%28%22NFC%22%29%3B%0Avar%20out%20%3D%20%24%28%22out%22%29%2C%20nCed%20%3D%200%2C%20nCom%20%3D%200%3B%0Aout.textContent%20%3D%20%22%22%3B%0Aif%20%28%21s.trim%28%29%29%7B%20%24%28%22verdict%22%29.textContent%20%3D%20%22%22%3B%20%24%28%22verdict%22%29.className%20%3D%20%22verdict%22%3B%20out.hidden%20%3D%20true%3B%20%24%28%22fixRow%22%29.hidden%20%3D%20true%3B%20%24%28%22fixNote%22%29.hidden%20%3D%20true%3B%20return%3B%20%7D%0Avar%20buf%20%3D%20%22%22%2C%20nTr%20%3D%200%3B%0Afunction%20flush%28%29%7B%20if%20%28buf%29%7B%20out.appendChild%28document.createTextNode%28buf%29%29%3B%20buf%20%3D%20%22%22%3B%20%7D%20%7D%0A%2F%2F%20sentence%20by%20sentence%2C%20like%20the%20fix%3A%20in%20a%20sentence%20with%20%5Cu0131%20%5Cu011F%20%5Cu00E7%20%5Cu00F6%20%5Cu00FC%20the%20cedilla%20is%20Turkish%20and%20right%0Avar%20parts%20%3D%20s.match%28%2F%5B%5E.%21%3F%5Cn%5D%2B%7C%5B.%21%3F%5Cn%5D%2B%2Fg%29%20%7C%7C%20%5B%5D%3B%0Afor%20%28var%20part%20of%20parts%29%7B%0Avar%20turkish%20%3D%20NOT_ROMANIAN.test%28part%29%3B%0Afor%20%28var%20ch%20of%20part%29%7B%0Aif%20%28CED%5Bch%5D%20%26%26%20%21turkish%29%7B%20flush%28%29%3B%20var%20m%20%3D%20document.createElement%28%22mark%22%29%3B%20m.textContent%20%3D%20ch%3B%20m.title%20%3D%20CED%5Bch%5D%20%2B%20%22%20%28wrong%20in%20Romanian%29%22%3B%20out.appendChild%28m%29%3B%20nCed%2B%2B%3B%20%7D%0Aelse%20if%20%28CED%5Bch%5D%29%7B%20flush%28%29%3B%20var%20t%20%3D%20document.createElement%28%22span%22%29%3B%20t.className%20%3D%20%22tr%22%3B%20t.textContent%20%3D%20ch%3B%20t.title%20%3D%20CED%5Bch%5D%20%2B%20%22%20%28Turkish%20sentence%3A%20right%20here%29%22%3B%20out.appendChild%28t%29%3B%20nTr%2B%2B%3B%20%7D%0Aelse%20if%20%28COM%5Bch%5D%29%7B%20flush%28%29%3B%20var%20o%20%3D%20document.createElement%28%22span%22%29%3B%20o.className%20%3D%20%22okl%22%3B%20o.textContent%20%3D%20ch%3B%20o.title%20%3D%20COM%5Bch%5D%3B%20out.appendChild%28o%29%3B%20nCom%2B%2B%3B%20%7D%0Aelse%20buf%20%2B%3D%20ch%3B%0A%7D%0A%7D%0Aflush%28%29%3B%0Aout.hidden%20%3D%20false%3B%0Avar%20v%20%3D%20%24%28%22verdict%22%29%3B%0Avar%20decomposed%20%3D%20raw%20%21%3D%3D%20s%20%3F%20%22%20Some%20letters%20were%20typed%20as%20two%20code%20points%3B%20shown%20here%20combined.%22%20%3A%20%22%22%3B%0Avar%20turkishNote%20%3D%20nTr%20%3F%20%22%20%22%20%2B%20nTr%20%2B%20%22%20%5Cu015F%2F%5Cu0163%20in%20Turkish%20sentences%20are%20right%20there%20and%20left%20alone.%22%20%3A%20%22%22%3B%0Aif%20%28nCed%29%7B%0Av.className%20%3D%20%22verdict%20bad%22%3B%0Av.textContent%20%3D%20nCed%20%2B%20%28nCed%20%3D%3D%3D%201%20%3F%20%22%20letter%20has%22%20%3A%20%22%20letters%20have%22%29%20%2B%20%22%20a%20cedilla%20%28%5Cu015F%20%5Cu0163%29%2C%20marked%20below.%20%22%20%2B%20nCom%20%2B%20%22%20use%20the%20comma%20below%20%28%5Cu0219%20%5Cu021B%29.%22%20%2B%20turkishNote%20%2B%20decomposed%3B%0A%24%28%22fixRow%22%29.hidden%20%3D%20false%3B%20%24%28%22fixNote%22%29.hidden%20%3D%20false%3B%0A%7D%20else%20%7B%0Av.className%20%3D%20%22verdict%20ok%22%3B%0Av.textContent%20%3D%20%28nCom%20%3F%20%22Clean%3A%20all%20%22%20%2B%20nCom%20%2B%20%22%20Romanian%20letters%20use%20the%20comma%20below%20%28%5Cu0219%20%5Cu021B%29.%22%20%3A%20%22No%20%5Cu0219%2C%20%5Cu021B%2C%20%5Cu015F%20or%20%5Cu0163%20in%20Romanian%20sentences%20here.%22%29%20%2B%20turkishNote%20%2B%20decomposed%3B%0A%24%28%22fixRow%22%29.hidden%20%3D%20true%3B%20%24%28%22fixNote%22%29.hidden%20%3D%20true%3B%0A%7D%0A%7D%0A%24%28%22t%22%29.addEventListener%28%22input%22%2C%20check%29%3B%0A%24%28%22sample%22%29.onclick%20%3D%20function%28%29%7B%20%24%28%22t%22%29.value%20%3D%20SAMPLE%3B%20check%28%29%3B%20%7D%3B%0A%24%28%22clear%22%29.onclick%20%3D%20function%28%29%7B%20%24%28%22t%22%29.value%20%3D%20%22%22%3B%20check%28%29%3B%20%24%28%22t%22%29.focus%28%29%3B%20%7D%3B%0A%24%28%22fix%22%29.onclick%20%3D%20function%28%29%7B%0Avar%20fixed%20%3D%20fixRomanian%28%24%28%22t%22%29.value%29%3B%0Avar%20msg%20%3D%20%24%28%22fixMsg%22%29%3B%0A%24%28%22t%22%29.value%20%3D%20fixed%3B%20check%28%29%3B%0Afunction%20selectIt%28%29%7B%20%24%28%22t%22%29.focus%28%29%3B%20%24%28%22t%22%29.select%28%29%3B%20msg.textContent%20%3D%20%22Fixed%20text%20is%20in%20the%20box%2C%20selected.%20Press%20Ctrl%2BC%20%28%5Cu2318C%20on%20a%20Mac%29.%22%3B%20%7D%0Aif%20%28navigator.clipboard%20%26%26%20navigator.clipboard.writeText%29%7B%20navigator.clipboard.writeText%28fixed%29.then%28function%28%29%7B%20msg.textContent%20%3D%20%22Fixed%20in%20the%20box%20and%20copied.%22%3B%20%7D%2C%20selectIt%29%3B%20%7D%20else%20selectIt%28%29%3B%0A%7D%3B%0A%3C%2Fscript%3E%0A%3C%2Fbody%3E%0A%3C%2Fhtml%3E%0A height=720 %}

Does your language have a pair like ş and ș? Tell me in the comments. I'd like to test it next.

{% details All the numbers (the 15 first-round models) %}

Echo with cedilla is the mean of every run on the same prompts (tasks 2 and 8).

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

## My Benchmark

{% cta https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below %} Romanian Comma Below on Kaggle {% endcta %}

Thirteen tasks with every model answer in the run outputs. The four-way test's own leaderboard ranks the models on the keyboard echo. The code that builds the tasks, the fake models that test the scorer, the census, the analysis and a script that re-checks the post's numbers against the raw results are on GitHub: [github.com/danielbutnar/comma-below](https://github.com/danielbutnar/comma-below). Every input is generated from correctly spelled text in one file, `src/items.py`, so testing another letter pair or another language is a small change.
