import html
import streamlit as st
import spacy

st.set_page_config(page_title="American to Canadian English Converter", page_icon="🍁")

@st.cache_resource
def load_nlp():
    return spacy.load("en_core_web_sm")

nlp = load_nlp()

BASE_REPLACEMENTS = {
    "color": "colour",
    "honor": "honour",
    "labor": "labour",
    "favor": "favour",
    "neighbor": "neighbour",
    "behavior": "behaviour",
    "center": "centre",
    "theater": "theatre",
    "catalog": "catalogue",
    "dialog": "dialogue",
    "defense": "defence",
    "offense": "offence",
}

SAFE_REPLACEMENTS = {
    "color": "colour",
    "colors": "colours",
    "colored": "coloured",
    "coloring": "colouring",
    "colorful": "colourful",
    "honor": "honour",
    "honors": "honours",
    "honored": "honoured",
    "honoring": "honouring",
    "labor": "labour",
    "labors": "labours",
    "labored": "laboured",
    "laboring": "labouring",
    "favor": "favour",
    "favorite": "favourite",
    "favorites": "favourites",
    "neighbor": "neighbour",
    "neighbors": "neighbours",
    "neighborly": "neighbourly",
    "behavior": "behaviour",
    "behaviors": "behaviours",
    "center": "centre",
    "centers": "centres",
    "centered": "centred",
    "centering": "centring",
    "theater": "theatre",
    "theaters": "theatres",
    "liter": "litre",
    "liters": "litres",
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
    "catalog": "catalogue",
    "catalogs": "catalogues",
    "dialog": "dialogue",
    "dialogs": "dialogues",
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


def replace_by_base(word: str) -> str | None:
    lower = word.lower()

    for base, replacement in sorted(BASE_REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True):
        if lower.startswith(base) and lower != base:
            suffix = lower[len(base):]
            new_word = replacement + suffix
            return preserve_case(word, new_word)

    return None


def convert_token(token) -> tuple[str, bool]:
    lower = token.text.lower()

    if lower in SAFE_REPLACEMENTS:
        new_text = preserve_case(token.text, SAFE_REPLACEMENTS[lower])
        return new_text, True

    ambiguous = convert_ambiguous(token)
    if ambiguous is not None:
        new_text = preserve_case(token.text, ambiguous)
        changed = new_text != token.text
        return new_text, changed

    base_match = replace_by_base(token.text)
    if base_match is not None:
        return base_match, base_match != token.text

    return token.text, False


def american_to_canadian_highlighted(text: str) -> str:
    doc = nlp(text)
    parts = []

    for token in doc:
        new_text, changed = convert_token(token)
        escaped_text = html.escape(new_text)
        escaped_ws = html.escape(token.whitespace_)

        if changed:
            parts.append(
                f'<mark style="background-color:#fff3a3; padding:0.1em 0.2em; border-radius:0.2em;">{escaped_text}</mark>{escaped_ws}'
            )
        else:
            parts.append(f"{escaped_text}{escaped_ws}")

    return "".join(parts)


st.title("🍁 American to Canadian English Converter")
st.write("Paste text below to convert common American English spellings to Canadian English.")

input_text = st.text_area(
    "Input text",
    height=220,
    placeholder="Enter American English text here..."
)

if st.button("Convert"):
    if input_text.strip():
        highlighted_html = american_to_canadian_highlighted(input_text)

        st.subheader("Highlighted changes")
        st.markdown(
            f"""
            <div style="
                padding: 1rem;
                border: 1px solid #ddd;
                border-radius: 0.5rem;
                background-color: white;
                color: black;
                line-height: 1.6;
                white-space: pre-wrap;
            ">
                {highlighted_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Please enter some text first.")
