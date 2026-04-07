import streamlit as st
import spacy

st.set_page_config(page_title="American to Canadian English Converter", page_icon="🍁")

@st.cache_resource
def load_nlp():
    return spacy.load("en_core_web_sm")


nlp = load_nlp()

SAFE_REPLACEMENTS = {
    # -or -> -our
    "color": "colour",
    "colors": "colours",
    "colored": "coloured",
    "coloring": "colouring",
    "honor": "honour",
    "honors": "honours",
    "honored": "honoured",
    "honoring": "honouring",
    "labor": "labour",
    "labors": "labours",
    "labored": "laboured",
    "laboring": "labouring",
    "favorite": "favourite",
    "favorites": "favourites",
    "neighbor": "neighbour",
    "neighbors": "neighbours",
    "neighborly": "neighbourly",
    "behavior": "behaviour",
    "behaviors": "behaviours",

    # -er -> -re
    "center": "centre",
    "centers": "centres",
    "centered": "centred",
    "centering": "centring",
    "theater": "theatre",
    "theaters": "theatres",
    "liter": "litre",
    "liters": "litres",

    # -ize / -yze
    "realize": "realise",
    "realizes": "realises",
    "realized": "realised",
    "realizing": "realising",
    "analyze": "analyse",
    "analyzed": "analysed",
    "analyzing": "analysing",
    "paralyze": "paralyse",
    "paralyzed": "paralysed",
    "paralyzing": "paralysing",

    # -og -> -ogue
    "catalog": "catalogue",
    "catalogs": "catalogues",
    "dialog": "dialogue",
    "dialogs": "dialogues",

    # doubled consonants
    "traveled": "travelled",
    "traveling": "travelling",
    "traveler": "traveller",
    "travelers": "travellers",
    "canceled": "cancelled",
    "canceling": "cancelling",
    "modeled": "modelled",
    "modeling": "modelling",
    "modeler": "modeller",
    "modelers": "modellers",
    "labeled": "labelled",
    "labeling": "labelling",

    # -ce / -se
    "defense": "defence",
    "defenses": "defences",
    "offense": "offence",
    "offenses": "offences",
}


def preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original.istitle():
        return replacement.title()
    return replacement


def is_banking_check(token) -> bool:
    if token.text.lower() not in {"check", "checks"}:
        return False

    context_words = {
        "bank", "deposit", "deposited", "payment", "payments", "pay", "paid",
        "mail", "mailed", "cash", "cashed", "write", "wrote", "written",
        "account", "accounts", "invoice", "invoices", "refund", "refunds",
        "vendor", "vendors", "customer", "customers", "signed", "sign",
        "issue", "issued", "issuing"
    }

    start = max(0, token.i - 4)
    end = min(len(token.doc), token.i + 5)
    window = list(token.doc[start:end])
    nearby = {t.text.lower() for t in window} | {t.lemma_.lower() for t in window}

    if nearby & context_words:
        return True

    for t in window:
        if t.like_num or "$" in t.text:
            return True

    return False


def is_measurement_meter(token) -> bool:
    if token.text.lower() not in {"meter", "meters"}:
        return False

    unit_context = {
        "long", "length", "distance", "distances", "wide", "width",
        "tall", "height", "deep", "depth", "square", "cubic", "per",
        "km", "cm", "mm", "m", "foot", "feet", "yard", "yards",
        "mile", "miles", "away"
    }

    device_context = {
        "parking", "gas", "water", "electric", "electricity",
        "power", "utility", "utilities", "voltage", "speed", "smart", "flow"
    }

    start = max(0, token.i - 4)
    end = min(len(token.doc), token.i + 5)
    window = list(token.doc[start:end])
    nearby = {t.text.lower() for t in window} | {t.lemma_.lower() for t in window}

    if nearby & device_context:
        return False
    if nearby & unit_context:
        return True

    for t in window:
        if t.like_num:
            return True

    return False


def convert_license(token) -> str | None:
    text = token.text.lower()

    if text not in {"license", "licenses", "licensed", "licensing"}:
        return None

    if token.pos_ == "VERB":
        return text

    if text in {"licensed", "licensing"}:
        return text

    if text == "license":
        return "licence"
    if text == "licenses":
        return "licences"

    return None


def convert_ambiguous(token) -> str | None:
    text = token.text.lower()

    if text in {"check", "checks"} and is_banking_check(token):
        return "cheque" if text == "check" else "cheques"

    if text in {"meter", "meters"} and is_measurement_meter(token):
        return "metre" if text == "meter" else "metres"

    if text in {"license", "licenses", "licensed", "licensing"}:
        return convert_license(token)

    return None


def american_to_canadian(text: str) -> str:
    doc = nlp(text)
    output = []

    for token in doc:
        lower = token.text.lower()

        if lower in SAFE_REPLACEMENTS:
            new_text = preserve_case(token.text, SAFE_REPLACEMENTS[lower])
            output.append(new_text + token.whitespace_)
            continue

        ambiguous = convert_ambiguous(token)
        if ambiguous is not None:
            new_text = preserve_case(token.text, ambiguous)
            output.append(new_text + token.whitespace_)
            continue

        output.append(token.text_with_ws)

    return "".join(output)


st.title("🍁 American to Canadian English Converter")
st.write("Paste text below to convert common American English spellings to Canadian English.")

input_text = st.text_area(
    "Input text",
    height=220,
    placeholder="Enter American English text here..."
)

if st.button("Convert"):
    if input_text.strip():
        converted_text = american_to_canadian(input_text)
        st.subheader("Converted text")
        st.text_area("Result", converted_text, height=220)
    else:
        st.warning("Please enter some text first.")
