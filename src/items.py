"""Source of truth for every benchmark item.

All Romanian text here is written in correct orthography (comma-below ș ț).
Cedilla variants and diacritic-free variants are *generated* from it by
`to_cedilla()` and `strip_diacritics()`, never typed by hand, so the gold and
the corrupted inputs cannot drift apart. `check_items()` asserts this file
contains no cedilla letters at all.
"""

from __future__ import annotations

import unicodedata

COMMA_TO_CEDILLA = str.maketrans({"ș": "ş", "Ș": "Ş", "ț": "ţ", "Ț": "Ţ"})
STRIP = str.maketrans(
    {"ă": "a", "Ă": "A", "â": "a", "Â": "A", "î": "i", "Î": "I",
     "ș": "s", "Ș": "S", "ț": "t", "Ț": "T"}
)


def to_cedilla(text: str) -> str:
    """Replace comma-below ș ț with the legacy cedilla ş ţ (the error)."""
    return text.translate(COMMA_TO_CEDILLA)


def strip_diacritics(text: str) -> str:
    """Romanian text as typed on a keyboard without diacritics."""
    return text.translate(STRIP)


# ---------------------------------------------------------------------------
# Task 1 · WRITE — English prompt, ASCII place names, Romanian answer.
# `required`: substrings that must appear (case-insensitive, code-point exact).
# Empty list: the answer must contain at least one ș/ț.
# ---------------------------------------------------------------------------

TR = "Translate into Romanian. Reply with the translation only.\n\n"

WRITE = [
    ("W01", "translate", TR + "The train from Timisoara to Iasi stops in Brasov for ten minutes.",
     ["Timișoara", "Iași", "Brașov"]),
    ("W02", "translate", TR + "We spent the weekend in Sighisoara and then drove to Targu Mures.",
     ["Sighișoara", "Mureș"]),
    ("W03", "translate", TR + "The Black Church is the best-known building in Brasov.",
     ["Brașov"]),
    ("W04", "translate", TR + "My grandmother was born in Constanta and later moved to Pitesti.",
     ["Constanța", "Pitești"]),
    ("W05", "translate", TR + "Stefan cel Mare ruled Moldavia for forty-seven years.",
     ["Ștefan"]),
    ("W06", "translate", TR + "The Transfagarasan road is closed every winter.",
     ["Transfăgărășan"]),
    ("W07", "translate", TR + "Let's meet in Piata Sfatului at eight o'clock.",
     ["Piața Sfatului"]),
    ("W08", "translate", TR + "The Cismigiu gardens are in the centre of Bucharest.",
     ["Cișmigiu", "București"]),
    ("W09", "translate", TR + "The Rasnov fortress is a short drive from Brasov.",
     ["Râșnov", "Brașov"]),
    ("W10", "translate", TR + "Arges county is famous for the Poenari fortress.",
     ["Argeș"]),
    ("W11", "word", "What is the Romanian word for 'school'? Reply with the word only.",
     ["școal"]),
    ("W12", "word", "Write the Romanian numbers from one to ten in words, separated by commas.",
     ["șase", "șapte"]),
    ("W13", "word", "List the seven days of the week in Romanian, separated by commas.",
     ["marți"]),
    ("W14", "translate", TR + "I don't know, but I will find out.",
     ["știu"]),
    ("W15", "translate", TR + "Thank you very much!",
     ["mulțum"]),
    ("W16", "word", "What is the Romanian word for 'country' (as in 'my country')? Reply with the word only.",
     ["țar"]),
    ("W17", "caps", "Write the Romanian word for 'school' in capital letters only. Reply with the word only.",
     ["ȘCOAL"]),
    ("W18", "json", "Return a JSON object that maps each of these English city names to its correct "
     "Romanian spelling: Brasov, Timisoara, Iasi, Constanta, Pitesti. Return only the JSON.",
     ["Brașov", "Timișoara", "Iași", "Constanța", "Pitești"]),
    ("W19", "code", "Write a JavaScript constant array named DAYS with the Romanian names of the days "
     "of the week, starting with Monday. Reply with the code only.",
     ["marți"]),
    ("W20", "html", "Write the HTML <title> element for the homepage of a small guesthouse in Brasov. "
     "The title must be in Romanian. Reply with the element only.",
     ["Brașov"]),
    ("W21", "long", "Write a description of Brasov in Romanian for a tourism website, about 120 words.",
     ["Brașov"]),
    ("W22", "long", "Write a short email in Romanian (about 80 words) confirming a hotel booking in "
     "Timisoara for two nights.",
     ["Timișoara"]),
    ("W23", "long", "Explain in Romanian, in about 100 words, how to make sarmale.",
     []),
    ("W24", "long", "Write two sentences in Romanian about the Carpathian mountains in winter.",
     []),
]

# ---------------------------------------------------------------------------
# Task 2 · ECHO — the user's Romanian text arrives either clean or typed with
# cedilla. Same text, same instruction; only the bytes of ș/ț differ.
# ---------------------------------------------------------------------------

ECHO_SYSTEM = (
    "You are the booking assistant of a small guesthouse in Brasov, Romania. "
    "Reply to the guest in Romanian, in 2 to 4 sentences."
)
ECHO_SUMMARY = "Summarize the following Romanian news paragraph in Romanian, in at most two sentences.\n\n"

ECHO = [
    ("E01", "reply", "Bună ziua! Aș dori să rezerv o cameră dublă în Brașov pentru două nopți, de vineri "
     "până duminică. Aveți parcare și mic dejun inclus? Mulțumesc!"),
    ("E02", "reply", "Salut, ajungem în Brașov sâmbătă seara, pe la ora nouă. Se poate face check-in și "
     "după ora zece? Suntem patru persoane și avem un câine mic."),
    ("E03", "reply", "Bună seara. Vreau să anulez rezervarea de săptămâna viitoare, pentru că mi s-a "
     "îmbolnăvit fiica. Îmi returnați avansul? Mulțumesc frumos."),
    ("E04", "reply", "Bună! Câți kilometri sunt de la pensiune până la Cetatea Râșnov și la Castelul Bran? "
     "Există autobuz sau e mai bine cu mașina?"),
    ("E05", "reply", "Bună ziua, am stat la dumneavoastră weekendul trecut și cred că mi-am uitat "
     "încărcătorul de telefon în cameră. Puteți verifica, vă rog?"),
    ("E06", "reply", "Salutare! Organizăm o întâlnire de familie de treizeci de persoane în octombrie. "
     "Aveți o sală și un meniu cu mâncare tradițională?"),
    ("E07", "summary", "Primăria Brașov anunță că Piața Sfatului va fi închisă traficului auto în weekend, "
     "între orele opt și douăzeci, din cauza târgului de toamnă. Șoferii sunt rugați să folosească "
     "parcările de pe strada Mureșenilor și de lângă Gara Brașov."),
    ("E08", "summary", "Drumul Transfăgărășan se închide în fiecare an la sfârșitul lunii octombrie, iar "
     "redeschiderea are loc, de obicei, la începutul lui iulie. Autoritățile recomandă turiștilor să "
     "verifice starea drumului înainte de plecare, deoarece ninsorile pot apărea și în septembrie."),
    ("E09", "summary", "Școlile din județul Timiș își vor începe cursurile cu o săptămână mai târziu, după "
     "ce mai multe clădiri au necesitat lucrări de reparații. Părinții vor fi anunțați prin mesaj de "
     "fiecare unitate de învățământ."),
    ("E10", "summary", "Festivalul de muzică de la Sighișoara a adunat peste cincisprezece mii de spectatori "
     "în trei zile. Organizatorii spun că biletele pentru ediția de anul viitor se vor pune în vânzare "
     "în decembrie, cu reducere pentru studenți."),
    ("E11", "summary", "Trenul de noapte dintre București și Iași va circula din nou începând cu luna "
     "viitoare, după o pauză de doi ani. Călătoria va dura aproximativ șapte ore, iar vagoanele de "
     "dormit au fost modernizate."),
    ("E12", "summary", "Ursul văzut în cartierul Răcădău din Brașov a fost relocat de jandarmi în cursul "
     "nopții. Locuitorii sunt sfătuiți să nu lase resturi de mâncare lângă blocuri și să anunțe prin "
     "112 orice apariție a animalelor sălbatice."),
]

# Retrieval-style questions over some of the news paragraphs above: the model
# answers from the text, which invites it to reuse the text's own words.
ECHO_RAG_PROMPT = ("Answer the question using only the text below. Answer in Romanian, in one sentence.\n\n"
                   "Text:\n{text}\n\nQuestion: {question}")
ECHO_RAG = [
    ("E07", "Where are drivers asked to park during the weekend?"),
    ("E08", "When does the road usually close, and when does it reopen?"),
    ("E10", "Where did the festival take place, and when do next year's tickets go on sale?"),
    ("E11", "Between which two cities does the night train run, and how long is the journey?"),
    ("E07", "Which square will be closed to cars, and why?"),
    ("E08", "What do the authorities recommend to tourists?"),
    ("E09", "Which county's schools will start later, and why?"),
    ("E12", "Where was the bear seen, and what should residents do?"),
    ("E01", "What does the guest want to book, and what do they ask about?"),
    ("E04", "Which two places does the guest ask about?"),
]

# ---------------------------------------------------------------------------
# Task 3 · FIX — cedilla text with one ordinary typo, three instruction levels.
# (id, gold, correct_word, typo_word): the input is to_cedilla(gold with the
# typo inserted); the gold is the clean text.
# ---------------------------------------------------------------------------

FIX_LEVELS = {
    "L1_proofread": "Proofread the following Romanian text. Return only the corrected text.\n\n",
    "L2_diacritics": "Correct the spelling and the diacritics in the following Romanian text. "
                     "Return only the corrected text.\n\n",
    "L3_explicit": "The following Romanian text was typed on an old keyboard layout that produces the "
                   "cedilla letters ş and ţ instead of the correct Romanian comma-below letters ș and ț. "
                   "Return the text with every diacritic corrected, and nothing else.\n\n",
}

FIX = [
    ("F01", "Pensiunea noastră se află la cinci minute de Piața Sfatului, în centrul istoric al "
     "Brașovului. Toate camerele au baie proprie, iar micul dejun este inclus în preț.",
     "este inclus", "estte inclus"),
    ("F02", "Vă mulțumim pentru rezervare! Check-in-ul se face între orele paisprezece și douăzeci și "
     "două. Dacă ajungeți mai târziu, vă rugăm să ne anunțați telefonic.",
     "rezervare", "rezervrae"),
    ("F03", "Cetatea Râșnov a fost construită de cavalerii teutoni și a fost restaurată în ultimii ani. "
     "De acolo se vede toată Țara Bârsei.",
     "restaurată", "restauartă"),
    ("F04", "Școala de vară pentru copii începe pe întâi iulie și durează două săptămâni. Înscrierile se "
     "fac până la sfârșitul lunii iunie.",
     "Înscrierile", "Înscrierle"),
    ("F05", "Știrile de astăzi: trenul spre Timișoara întârzie patruzeci de minute, iar autostrada spre "
     "Pitești este aglomerată.",
     "aglomerată", "aglomrată"),
    ("F06", "Mulțumesc pentru ajutor! Mâine vă trimit fișierele și factura pentru luna trecută.",
     "factura", "facutra"),
]

# ---------------------------------------------------------------------------
# Task 4 · SEE — perception. Generated in build from these words/sentences.
# ---------------------------------------------------------------------------

SEE_WORDS = ["Brașov", "Timișoara", "Iași", "mulțumesc", "Ștefan", "țară", "Constanța", "știri"]

SEE_SENTENCES = [
    "Ne vedem mâine în Piața Sfatului, la ora șapte.",
    "Trenul spre Timișoara pleacă din Gara Brașov la ora nouă.",
    "Mulțumesc pentru ajutor, ne-a fost de mare folos.",
    "Știrile de azi vorbesc despre ninsorile din Țara Bârsei.",
    "Castelul Bran și Cetatea Râșnov sunt aproape de oraș.",
    "Școala se închide vineri pentru două săptămâni.",
    "Am cumpărat pâine și brânză de la piața din Iași.",
    "Drumul spre Pitești este aglomerat în fiecare vineri.",
    "Ștefan și Constanța au plecat în vacanță la munte.",
    "Pensiunea are o terasă cu vedere spre Tâmpa.",
    "Rezervarea pentru două nopți a fost confirmată.",
    "Vă așteptăm cu drag și săptămâna viitoare.",
]

# (word, 1-based position of the ș/ț letter)
SEE_CODEPOINT = [("Brașov", 4), ("Iași", 3), ("mulțumesc", 4), ("Țară", 1)]

# ---------------------------------------------------------------------------
# Task 5 · RESTORE — gold sentences; the input is strip_diacritics(gold).
# Several pairs only differ by context (peste/pește, fata/fața, masa/masă).
# ---------------------------------------------------------------------------

RESTORE = [
    ("R01", "Mănânc pește la cină."),
    ("R02", "Am sărit peste gard."),
    ("R03", "Peștele din lac e proaspăt."),
    ("R04", "Trecem peste pod și mergem acasă."),
    ("R05", "Fata mea are șapte ani."),
    ("R06", "Spală-te pe față înainte de culcare."),
    ("R07", "În fața casei e un nuc bătrân."),
    ("R08", "Fata a venit acasă de la școală."),
    ("R09", "Am pus masa în bucătărie."),
    ("R10", "Sunt două cărți pe masă."),
    ("R11", "Mama pregătește o masă mare de Crăciun."),
    ("R12", "Țara noastră are munți frumoși."),
    ("R13", "Munții Făgăraș sunt cei mai înalți din țară."),
    ("R14", "Casa e la șase kilometri de oraș."),
    ("R15", "Să știi că nu știu."),
    ("R16", "Și el vine, și ea vine."),
    ("R17", "Școala începe luni, pe cincisprezece septembrie."),
    ("R18", "Pe drum spre Brașov am văzut un urs."),
    ("R19", "Mă doare gâtul de la frig."),
    ("R20", "Cărțile sunt pe raft."),
    ("R21", "Tatăl lui e pescar la Tulcea."),
    ("R22", "Am cumpărat pâine și lapte."),
    ("R23", "Să ne vedem mâine la ora șapte în Piața Sfatului."),
    ("R24", "Nu-mi place să aștept."),
    ("R25", "Iași e un oraș din Moldova."),
    ("R26", "Suntem în România de două săptămâni."),
    ("R27", "Reîntoarcerea acasă a fost lungă."),
    ("R28", "A rămas un gest neînțeles."),
    ("R29", "Sticla e pe jumătate goală."),
    ("R30", "Când ajungi la Timișoara, sună-mă."),
]

# ---------------------------------------------------------------------------
# Task 6 · CODE — two prompt phrasings, hidden tests in build.
# ---------------------------------------------------------------------------

CODE_PROMPTS = [
    ("C1_explicit",
     "Our Romanian website's content was typed on old keyboards and uses the cedilla letters ş, Ş, ţ, Ţ "
     "instead of the correct Romanian comma-below letters ș, Ș, ț, Ț. Write a Python function "
     "`fix_romanian(text: str) -> str` that repairs the text. Only change what needs changing. "
     "Reply with one Python code block containing the function (imports allowed, no tests, no explanation)."),
    ("C2_goal",
     "Write a Python function `fix_romanian(text: str) -> str` that normalizes the Romanian diacritics in a "
     "text so that it follows the standard Romanian orthography. For example, 'Braşov' must become "
     "'Brașov'. Only change what needs changing. Reply with one Python code block containing the function "
     "(imports allowed, no tests, no explanation)."),
]

# (name, input, expected) — compared after NFC normalization of both sides.
CODE_TESTS = [
    ("basic", "Braşov", "Brașov"),
    ("two_words", "Timişoara, Iaşi", "Timișoara, Iași"),
    ("upper_s", "ŞCOALA", "ȘCOALA"),
    ("upper_t", "Ţara Bârsei", "Țara Bârsei"),
    ("lower_t", "mulţumesc", "mulțumesc"),
    ("decomposed_s", "Braşov", "Brașov"),
    ("decomposed_T", "Ţara", "Țara"),
    ("already_correct", "Brașov și Timișoara", "Brașov și Timișoara"),
    ("other_letters", "Mănăstirea din Târgu Mureș", "Mănăstirea din Târgu Mureș"),
    ("french_c_cedilla", "Français, garçon, façade", "Français, garçon, façade"),
    ("decomposed_c_cedilla", "garçon", "garçon"),
    ("whitespace_emoji", "Braşov\n\t🙂 ok", "Brașov\n\t🙂 ok"),
    ("mixed_paragraph", "Ne vedem mâine în Piaţa Sfatului; ştiu că Ştefan vine şi el.",
     "Ne vedem mâine în Piața Sfatului; știu că Ștefan vine și el."),
]
# Plus an idempotence test added in build: f(f(x)) == f(x) on the paragraph.


def check_items() -> None:
    """Fail loudly if any hand-typed text contains a cedilla letter."""
    import inspect
    import sys

    src = inspect.getsource(sys.modules[__name__])
    # The only legal cedilla letters in this file are inside COMMA_TO_CEDILLA,
    # FIX_LEVELS L3, CODE_PROMPTS and CODE_TESTS inputs (intentional).
    bad = []
    for name in ("WRITE", "ECHO", "FIX", "SEE_WORDS", "SEE_SENTENCES", "SEE_CODEPOINT", "RESTORE"):
        blob = repr(globals()[name])
        for ch in "şŞţŢ":
            if ch in blob:
                bad.append((name, ch))
    assert not bad, f"cedilla letters typed into gold data: {bad}"
    for name in ("WRITE", "ECHO", "FIX", "SEE_WORDS", "SEE_SENTENCES", "RESTORE"):
        blob = repr(globals()[name])
        assert unicodedata.normalize("NFC", blob) == blob, f"{name} is not NFC"
    assert src  # keep inspect import meaningful


if __name__ == "__main__":
    check_items()
    import collections

    counts = collections.Counter()
    for name in ("WRITE", "ECHO", "FIX", "SEE_WORDS", "SEE_SENTENCES", "RESTORE"):
        for ch in repr(globals()[name]):
            if ch in "șȘțȚşŞţŢ":
                counts[f"U+{ord(ch):04X} {ch}"] += 1
    print("items ok", dict(counts))
    print({k: len(v) for k, v in {"WRITE": WRITE, "ECHO": ECHO, "FIX": FIX, "RESTORE": RESTORE}.items()})
