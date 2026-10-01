---
title: Braşov or Brașov? 15 LLMs spell my city right, until you spell it wrong first
published: false
tags: devchallenge, kagglechallenge, ai, machinelearning
cover_image: https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/cover.png
---

*This is a submission for the [Kaggle Benchmarking Challenge](https://dev.to/challenges/kaggle-2026-09-23)*

Look at these two words:

> **Braşov**   **Brașov**

One of them is the name of the city I live in. The other one is a 1990s encoding workaround that never went away. Most people can't tell which is which, and it turns out the question is just as interesting for language models: they can write the right one, but they can't resist copying the wrong one.

## What I Benchmarked

Romanian has two letters with a little mark underneath: **ș** and **ț**. The mark is a comma (U+0219 and U+021B). In the 1990s, the encodings everyone used, ISO 8859-2 and Windows-1250, simply didn't have those letters. They had the Turkish **ş** and a **ţ** that almost no living language uses, both with a cedilla (U+015F and U+0163), and Romanian computing quietly adopted those. Unicode added the correct letters in 1999. Windows XP needed a font update in 2007 to show them.

That's history, I thought. So before writing a single prompt, I counted. I fetched the front pages of 35 Romanian sites on 30 September 2026 and counted both kinds of letter.

![30 of 35 Romanian front pages contain cedilla letters](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-web-census.png)

**30 of 35 still contain the wrong letters.** The government's site has an "INFORMAŢIE DE PRESĂ". The National Bank lists "Elemente de siguranţă". My own city hall quotes an "Ordonanţa de Urgenţă". The national rail operator shows a "Preţul integral". One financial daily is 93 % cedilla. Many pages mix both kinds, sometimes in the same paragraph.

Why should a developer care about a letter you can barely see? Because to a computer they are different characters. `"Brașov" == "Braşov"` is `false`. Ctrl+F for one doesn't find the other. Your search index, your deduplication, your URL slugs, your sort order and your screen reader all treat them as two different words. And the text with the wrong letters is exactly what models are trained on, and exactly what a retrieval system feeds them.

So my itch turned into one question: **do language models write the right letter, and what do they do when the text they read has the wrong one?**

I split it into six tasks. Every score is computed from Unicode code points; there is no LLM judge anywhere, and I checked every answer key as a native speaker.

| # | Task | What it asks |
| --- | --- | --- |
| 1 | **Write** | English prompt with ASCII names ("Timisoara", "Brasov"). Does the Romanian answer use ș/ț? |
| 2 | **Echo** | The same guest messages and news paragraphs arrive twice: typed correctly, and typed with cedillas. The model replies, summarizes, or answers a question from the text. Does it copy the wrong letters? |
| 3 | **Fix** | Cedilla text with one ordinary typo: "proofread this" vs "correct the spelling and the diacritics" vs an explicit description of the problem. |
| 4 | **See** | "Are these two strings the same sequence of Unicode characters?" Half the pairs differ only by comma vs cedilla; half are byte-identical. |
| 5 | **Restore** | Put the diacritics back where only context decides: *peste* (over) vs *pește* (fish), *fata* (the girl) vs *fața* (the face). |
| 6 | **Code** | Write `fix_romanian(text)`. 14 hidden tests: uppercase, decomposed letters (s + U+0327), already-correct text, French ç that must survive. |

## Models Tested

15 models, picked to cover each big lab's flagship, mid-size and small model, plus the open-weight models people actually self-host:

- **Anthropic:** Claude Opus 5, Claude Sonnet 5, Claude Haiku 4.5
- **Google:** Gemini 3.1 Pro, Gemini 3.8 Flash, Gemini 3.7 Flash, Gemini 3.5 Flash-Lite, Gemma 4 31B (open)
- **OpenAI:** GPT-6 Astra, GPT-5.5, GPT-5.4 nano
- **Others:** Grok 4.20 Reasoning, DeepSeek-R1, Qwen 3 235B, GLM-5

If the problem lives in the training data, size and lab should matter. If it lives somewhere else, they shouldn't. That was the point of the spread.

Everything ran on Kaggle's model proxy with Kaggle's defaults, with output capped at 8,192 tokens. Most models run at their provider's default temperature there, so I ran the key task, Echo, three times per model. I dropped gpt-oss-120b, whose provider answered most of my calls with "heavy load", and Grok 4.6, which Kaggle lists but can't serve. The whole thing, including pilots and repeats, cost $11.53 of Kaggle's free inference quota.

## Findings

### 1. Writing is (almost) solved

Given an English prompt and ASCII names, 11 of the 15 models wrote every Romanian word correctly. The exceptions are small and specific: Claude Haiku 4.5 wrote "Nu ştiu" and "Răşnov" with cedillas on its own, GPT-5.4 nano wrote "Cişmigiu" and "Bucureştiului", and Qwen 3 and DeepSeek-R1 dropped diacritics from a few names ("Cismigiu", "Brasov"). Restoring diacritics from context was strong too: eight models got all 30 sentences right.

So if the models know the right letter, where does the wrong one come from?

### 2. Clean in, clean out. Cedilla in, cedilla out.

This is the main result.

![Echo results: every model scores 100 % on clean input, 44–85 % on the same text typed with cedillas, and 77–100 % once one sentence is added to the system prompt](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-echo.png)

When the guest message or news paragraph was typed correctly, **every model kept every letter correct, in all 45 runs.** When the *same text* was typed with cedillas, the share of clean answers fell to **between 44 % (Grok 4.20) and 85 % (Qwen 3)**. Model size bought nothing: Claude Opus 5 (56 %) and GPT-6 Astra (55 %) sit next to GPT-5.4 nano (61 %), well below Qwen 3.

What the model was doing mattered more than which model it was:

| Answer type (cedilla input, all models, 3 runs) | Clean answers |
| --- | --- |
| Reply to a guest's message | 97 % |
| Summary of a news paragraph | 62 % |
| Answer a question using only the text (retrieval style) | 45 % |

Replying, the models write their own sentences. Summarizing and answering from a document, they reuse the document's words, and with them its bytes: **93 % of the wrong words in all answers were copied verbatim from the input** (1,105 of 1,186). The most copied: *şi* ("and"), *Braşov*, *Sighişoara*, *Mureşenilor*.

The surprise came from the other 7 %. Some models wrote cedilla letters into words that weren't in the input at all. Claude Opus 5, summarizing a cedilla-typed notice about a closed square, wrote:

> Primăria Braşov anunţă închiderea Pieţei Sfatului pentru traficul auto în weekend, între orele 8 şi 20, din cauza târgului de toamnă. Şoferii sunt **îndrumaţi** să parcheze pe strada Mureşenilor sau lângă Gara Braşov.

*Îndrumaţi* ("directed") isn't in the source. Opus wrote it, and wrote it with a cedilla, because the whole text was in cedilla. Every single failing answer from Opus 5, GPT-6 Astra and Gemini 3.8 Flash was cedilla from start to finish. Smaller models fail differently: Qwen 3 and GPT-5.4 nano mostly *mix* the two letters inside one sentence, like this answer from Gemini 3.5 Flash-Lite:

> **Ș**oferii sunt ruga**ț**i să folosească parcările de pe strada Mure**ş**enilor **ş**i de lângă Gara Bra**ş**ov.

Its own words came out right; the borrowed ones came out the way they were typed. I counted 71 sentences like that.

So the stronger the model, the more consistently it treats the encoding of your text as a *style* to match, the same way it would match your tone or your formality. That's usually a feature. Here it means the error is contagious.

### 3. "Proofread this" is not enough

Given cedilla text with one ordinary typo:

- **"Proofread the following text":** 79 % of answers repaired the letters.
- **"Correct the spelling and the diacritics":** 99 %.
- **Explicit description of the cedilla problem:** 97 %.

In 19 of the 90 plain proofreads the model fixed the typo and kept the cedilla letters. Claude Sonnet 5 did that in 5 of 6 texts. The knowledge is clearly there (one word, "diacritics", is enough to switch it on), but it isn't part of what the models consider proofreading.

### 4. "Can you see the difference?" was the wrong question

I expected the models to fail at telling ş from ș. Instead, everyone scored nearly 100 % on pairs that really differ. Then I looked at the control pairs.

![Some models call every ș/ş pair different, even identical ones](https://raw.githubusercontent.com/danielbutnar/comma-below/main/post/chart-see.png)

Asked whether two **byte-identical** strings like "Brașov" and "Brașov" are the same sequence of characters, Claude Opus 5, Claude Sonnet 5, Claude Haiku 4.5 and Gemini 3.8 Flash answered "false" every time. The question is obviously a trick, so they assume the answer is "different". Their perfect score on the real differences says nothing about perception. Eight other models, including GPT-5.5, GPT-6 Astra, DeepSeek-R1, Grok 4.20 and Qwen 3, got every identical pair right.

If I'd only tested pairs that differ, I would have written the opposite conclusion. Every "spot the difference" benchmark needs pairs with no difference.

### 5. Code: the more precisely I described the bug, the narrower the fix

Asked for `fix_romanian(text)`, almost every model wrote a clean translation table, `str.maketrans("şŞţŢ", "șȘțȚ")`. That passes most tests, but **23 of 30 programs failed on decomposed letters**: an `s` followed by a combining cedilla (U+0327), which is what you get from some PDFs and macOS file names. When my prompt named the four wrong letters, **only 1 of 15 programs handled the decomposed ones** (Claude Opus 5's). When I only described the goal, "normalize the Romanian diacritics", 6 of 15 did. Naming the letters made the models write exactly that four-letter replacement and nothing more. Opus 5 was the only model with all 14 tests passing on both prompts.

### 6. The bug that almost ate my benchmark

The first version of my task file contained the word "Brașov". On my laptop, the Kaggle CLI reads task files with `open(file)` and no encoding argument, so Windows decoded my UTF-8 as cp1250, the Central European code page, and would have uploaded **"BraČ™ov"**. A benchmark about one wrong character, broken by one wrong character on the way in. My task files are now pure ASCII (every Romanian letter is a `\u` escape) and check a SHA-256 of their data before running.

### All the numbers

Percent of items passed; Echo is the mean of three runs on cedilla input (on clean input every model scored 100). Rows are sorted by Echo.

| Model | Write | Echo: cedilla input | Echo + rule | Fix | See | Restore | Code |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen 3 235B | 92 | 85 | 91 | 89 | 89 | 90 | 61 |
| Gemini 3.1 Pro | 100 | 82 | 100 | 100 | 97 | 100 | 86 |
| Gemini 3.7 Flash | 100 | 76 | 100 | 100 | 97 | 100 | 86 |
| Gemini 3.8 Flash | 100 | 71 | 100 | 100 | 81 | 100 | 93 |
| DeepSeek-R1 | 96 | 70 | 91 | 83 | 83 | 93 | 86 |
| Gemini 3.5 Flash-Lite | 100 | 68 | 100 | 89 | 83 | 90 | 93 |
| Gemma 4 31B | 100 | 68 | 100 | 89 | 89 | 90 | 64 |
| GPT-5.5 | 100 | 65 | 100 | 100 | 100 | 100 | 93 |
| GPT-5.4 nano | 96 | 61 | 77 | 83 | 83 | 90 | 93 |
| Claude Sonnet 5 | 100 | 58 | 91 | 72 | 83 | 100 | 86 |
| Claude Opus 5 | 100 | 56 | 100 | 100 | 81 | 100 | 100 |
| GPT-6 Astra | 100 | 55 | 100 | 100 | 100 | 100 | 93 |
| GLM-5 | 100 | 53 | 100 | 94 | 94 | 100 | 86 |
| Claude Haiku 4.5 | 92 | 45 | 86 | 89 | 72 | 93 | 86 |
| Grok 4.20 Reasoning | 100 | 44 | 100 | 83 | 97 | 87 | 86 |

### What changed in how I think about these models

I started out thinking of this as a knowledge problem: maybe the models never learned the right letter. They did. They write it correctly when nobody shows them the wrong one. The failure is **inheritance**: whatever encoding is in the context comes back out, and the better the model, the more faithfully it comes back.

That moves the fix from the model to the pipeline. If you build anything in Romanian on top of an LLM, and especially anything retrieval-based on top of the Romanian web, normalize the text before it reaches the model and again after:

```python
import unicodedata

CEDILLA_TO_COMMA = str.maketrans("şŞţŢ", "șȘțȚ")

def fix_romanian(text: str) -> str:
    # NFC first, so "s" + combining cedilla becomes "ş" and then "ș"
    return unicodedata.normalize("NFC", text).translate(CEDILLA_TO_COMMA)
```

And the obvious fix, simply telling the model? I tested that as a follow-up task, [Echo With a Rule](https://www.kaggle.com/benchmarks/tasks/danielbutnar/romanian-comma-below-7-echo-with-a-rule): the same 22 cedilla inputs, plus one sentence in the system prompt:

> *Use correct Romanian orthography: write ș and ț with a comma below, never ş or ţ with a cedilla, even if the input uses them.*

Clean answers went from **64 % to 96 %** across all models. Ten of the fifteen were perfect, including Claude Opus 5 (56 % → 100 %), GPT-6 Astra (55 % → 100 %) and Grok 4.20 (44 % → 100 %). The holdouts were the smaller models: GPT-5.4 nano still copied the wrong letters in 5 of its 22 answers.

So the models know the rule. They just don't apply it unless you ask, because matching your text is what they're built to do. Ask, and normalize anyway.

### What I'd measure next

- **Other look-alike pairs:** Turkish dotless ı and İ, the Hawaiian ʻokina vs the apostrophe, the Catalan l·l. Same experiment, different alphabet.
- **Longer contexts:** does one cedilla paragraph among ten clean ones still flip the answer?
- **Where the switch happens:** the tokenizer sees different bytes for ş and ș; at what point does the model "decide" which encoding it's writing in?

## My Benchmark

**Romanian Comma Below on Kaggle:** [kaggle.com/benchmarks/danielbutnar/romanian-comma-below](https://www.kaggle.com/benchmarks/danielbutnar/romanian-comma-below)

All task notebooks are public, every model answer is in the run outputs, and the code that generates the tasks, the census of Romanian sites and the charts is on GitHub: [github.com/danielbutnar/comma-below](https://github.com/danielbutnar/comma-below).

{% embed https://github.com/danielbutnar/comma-below %}
