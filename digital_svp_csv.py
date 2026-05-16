from html import escape

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Digitálny ŠVP", page_icon=":ledger:")
st.warning("Slúži iba na kontrolu dát. Neoficiálna verzia!")
sheet_id = st.secrets.get("sheet_id")

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# -----------------------------
# Konštanty
# -----------------------------

VZDELAVACIE_OBLASTI = {
    "Jazyk a komunikácia": [
        "Slovenský jazyk a literatúra",
        "Jazyky národnostných menšín",
        "Slovenský jazyk ako druhý jazyk",
        "Cudzí jazyk",
    ],
    "Matematika a informatika": ["Matematika", "Informatika"],
    "Človek a príroda": [],
    "Človek a spoločnosť": ["Človek a spoločnosť", "Náboženstvo"],
    "Človek a svet práce": [],
    "Umenie a kultúra": ["Hudobná výchova", "Výtvarná výchova"],
    "Zdravie a pohyb": [],
}

JAZYKY_NARODNOSTNE = [
    "Maďarský jazyk a literatúra",
    "Nemecký jazyk a literatúra",
    "Rómsky jazyk a literatúra",
    "Rusínsky jazyk a literatúra",
    "Ruský jazyk a literatúra",
    "Ukrajinský jazyk a literatúra",
]

CUDZIE_JAZYKY = [
    "Anglický jazyk",
    "Francúzsky jazyk",
    "Nemecký jazyk",
    "Ruský jazyk",
    "Španielsky jazyk",
    "Taliansky jazyk",
]

SLOVENCINA_AKO_DRUHY_JAZYK = [
    "Slovenský jazyk ako druhý jazyk",
    "Slovenský jazyk a slovenská literatúra",
]

NABOZENSTVA = [
    "Náboženstvo Cirkvi bratskej",
    "Náboženstvo Gréckokatolíckej cirkvi",
    "Náboženstvo Pravoslávnej cirkvi",
    "Náboženstvo Reformovanej kresťanskej cirkvi",
    "Náboženstvo Rímskokatolíckej cirkvi",
    "Náboženstvo Evanjelickej cirkvi a. v.",
]

PREDMETY_KODY = {
    "Slovenský jazyk a literatúra": "sk",
    "Maďarský jazyk a literatúra": "hu",
    "Nemecký jazyk a literatúra": "de",
    "Rómsky jazyk a literatúra": "ry",
    "Rusínsky jazyk a literatúra": "ri",
    "Ruský jazyk a literatúra": "ru",
    "Ukrajinský jazyk a literatúra": "uk",
    "Slovenský jazyk a slovenská literatúra": "sj",
    "Slovenský jazyk ako druhý jazyk": "dj",
    "Cudzí jazyk": "cj",
    "Matematika": "mt",
    "Informatika": "if",
    "Človek a spoločnosť": "cs",
    "Človek a príroda": "cp",
    "Človek a svet práce": "sp",
    "Hudobná výchova": "hv",
    "Výtvarná výchova": "vv",
    "Zdravie a pohyb": "zp",
    "Náboženstvo Cirkvi bratskej": "br",
    "Náboženstvo Gréckokatolíckej cirkvi": "gr",
    "Náboženstvo Pravoslávnej cirkvi": "pr",
    "Náboženstvo Reformovanej kresťanskej cirkvi": "rf",
    "Náboženstvo Rímskokatolíckej cirkvi": "rk",
    "Náboženstvo Evanjelickej cirkvi a. v.": "ev",
}

PREDMETY_VYKONY_POD_CIELMI = {"Človek a príroda", "Človek a spoločnosť"}

PREDMETY_BEZ_DELENIA_OBSAH_STANDARDOV = {
    "Hudobná výchova",
    "Výtvarná výchova",
    "Zdravie a pohyb",
    "Informatika",
    "Matematika",
    *NABOZENSTVA,
}

DEFAULT_TABS_CYKLY = {
    "1. cyklus (r. 1-3)": 1,
    "2. cyklus (r. 4-5)": 2,
    "3. cyklus (r. 6-9)": 3,
}

TABS_CYKLY_CUDZI_JAZYK = {
    "1. cyklus (r.1-3)": 1,
    "2. cyklus (r.4-5)": 2,
    "3. cyklus - prvý jazyk (r.6-9)": 3,
    "3. cyklus - druhý jazyk (r.6-9)": 4,
}


# -----------------------------
# Pomocné funkcie
# -----------------------------

@st.cache_data(show_spinner="Načítavam štandardy...")
def load_standardy() -> pd.DataFrame:
    """Načíta ŠVP v štruktúrovanej podobe."""
    if not sheet_id:
        st.error("Chýba `sheet_id` v Streamlit secrets.")
        st.stop()

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

    df = pd.read_csv(csv_url)
    df = df.rename(
        columns={
            "typ štandardu": "typ_standardu",
            "tematický celok": "tema",
        }
    )

    required_columns = {"id", "definicia", "predmet", "cyklus", "typ_standardu", "tema", "komponent"}
    missing = required_columns - set(df.columns)
    if missing:
        st.error(f"V dátach chýbajú stĺpce: {', '.join(sorted(missing))}")
        st.stop()

    df = df[df["definicia"].notna()].copy()
    df["id"] = df["id"].astype(str)
    df["definicia"] = df["definicia"].astype(str)

    # zvyrazni zmenu
    i_zmena = df["zmena"] == "doplnit"

    df.loc[i_zmena, "definicia"] = df.loc[i_zmena, "definicia"] + ' <span>🆕</span>'

    # df.loc[i_zmena, "definicia"] = '<mark>' + df.loc[i_zmena, "definicia"] + '</mark>'

    # pridaj tooltip
    df["tooltip_html"] = df.apply(
        lambda r: f'<span class="tooltip">{r["tooltip"]}<span class="tooltiptext">{r["tooltip_text"]}</span></span>',
        axis=1
    )

    df["definicia"] = df.apply(
        lambda row: row["definicia"].replace(row["tooltip"], row["tooltip_html"])
        if pd.notna(row["tooltip"]) and pd.notna(row["tooltip_html"])
        else row["definicia"],
        axis=1
    )

    return df


def render_standardy_as_items(standardy: pd.Series) -> None:
    """Zobrazí štandardy vždy ako bullet pointy."""
    standardy = standardy.dropna().astype(str)

    if standardy.empty:
        return

    items = []

    standardy = standardy.str.strip().str.lstrip("-").str.strip()
    items = "- " + standardy

    st.markdown("\n".join(items), unsafe_allow_html=True)


def render_by_typ_standardu(df: pd.DataFrame, ziak_vie: bool = False) -> None:
    """Zobrazí štandardy rozdelené podľa typu štandardu."""
    if df.empty:
        return

    # df = add_id_tooltips(df)
    typy_standardov = df["typ_standardu"].dropna().unique().tolist()

    if typy_standardov:
        for typ_standardu in typy_standardov:
            if typ_standardu not in {"Úvod", "none"}:
                st.markdown(
                    f'<p style="color: #004280;"><b>{typ_standardu}</b></p>',
                    unsafe_allow_html=True,
                )
                if ziak_vie:
                    st.markdown("<b>Žiak vie/dokáže:</b>", unsafe_allow_html=True)

            render_standardy_as_items(
                df.loc[df["typ_standardu"] == typ_standardu, "definicia"]
            )
            st.markdown("\n")
    else:
        if ziak_vie:
            st.markdown("<b>Žiak vie/dokáže:</b>", unsafe_allow_html=True)

        render_standardy_as_items(df["definicia"])


def vyber_podla_predmetu_cap(df: pd.DataFrame, options: list[str]) -> pd.DataFrame:
    """Vyberie štandardy pre Fyziku, Chémiu alebo Biológiu v oblasti Človek a príroda."""

    subject_codes = {
        "Chémia": r"\bCH\b",
        "Fyzika": r"\bF\b",
        "Biológia": r"\bB\b",
    }

    selected_mask = pd.Series(False, index=df.index)

    for predmet, regex in subject_codes.items():
        if predmet in options:
            selected_mask |= df["definicia"].astype(str).str.contains(regex, na=False, regex=True)

    return df[selected_mask | df["is_v"]].copy()


def resolve_predmet_a_cykly(predmet: str) -> tuple[str, dict[str, int], str | None]:
    """Vyrieši špecifické výbery predmetov v sidebare."""
    tabs_cykly = DEFAULT_TABS_CYKLY.copy()
    jazyk = None

    if predmet == "Slovenský jazyk ako druhý jazyk":
        predmet = st.sidebar.selectbox(
            "Slovenský jazyk ako druhý jazyk",
            SLOVENCINA_AKO_DRUHY_JAZYK,
            label_visibility="collapsed",
        )
        if predmet == "Slovenský jazyk ako druhý jazyk":
            tabs_cykly = {
                "Komunikačná úroveň 1 (základná)": 1,
                "Komunikačná úroveň 2 (rozširujúca)": 2,
            }

    elif predmet == "Cudzí jazyk":
        tabs_cykly = TABS_CYKLY_CUDZI_JAZYK.copy()
        jazyk = st.sidebar.selectbox("Jazyk", CUDZIE_JAZYKY)

    elif predmet == "Náboženstvo":
        predmet = st.sidebar.selectbox(
            "Náboženstvo",
            NABOZENSTVA,
            label_visibility="collapsed",
        )

    elif predmet == "Jazyky národnostných menšín":
        predmet = st.sidebar.selectbox(
            "Jazyky národnostných menšín",
            JAZYKY_NARODNOSTNE,
            label_visibility="collapsed",
        )

    return predmet, tabs_cykly, jazyk


def filter_data(df: pd.DataFrame, predmet: str, cyklus: int, jazyk: str | None) -> pd.DataFrame:
    """Vyfiltruje dáta podľa predmetu, cyklu a prípadne cudzieho jazyka."""
    filtered = df[
        (df["predmet"].astype(str) == predmet)
        & (df["cyklus"] == cyklus)
    ].copy()

    if predmet == "Cudzí jazyk" and jazyk:
        ine_jazyky = [j for j in CUDZIE_JAZYKY if j != jazyk]
        filtered = filtered[~filtered["typ_standardu"].isin(ine_jazyky)].copy()

    return filtered


# -----------------------------
# Načítanie dát
# -----------------------------

if st.sidebar.button("Clear cache"):
    st.cache_data.clear()
    st.rerun()

df = load_standardy()


# -----------------------------
# Sidebar
# -----------------------------

vzdelavacia_oblast = st.sidebar.selectbox(
    "Vzdelávacia oblasť",
    list(VZDELAVACIE_OBLASTI.keys()),
)

predmety = VZDELAVACIE_OBLASTI[vzdelavacia_oblast]

if predmety:
    predmet = st.sidebar.selectbox("Predmet", predmety)
else:
    predmet = vzdelavacia_oblast

predmet, tabs_cykly, jazyk = resolve_predmet_a_cykly(predmet)

cyklus_vyber = st.sidebar.selectbox("Cyklus", list(tabs_cykly.keys()))
cyklus = tabs_cykly[cyklus_vyber]

df = filter_data(df, predmet, cyklus, jazyk)

df["is_v"] = df["id"].str.contains("-v-", na=False)
df["is_o"] = df["id"].str.contains("-o-", na=False)
df["is_c"] = df["id"].str.contains("-c-", na=False)
df["is_hc"] = df["id"].str.contains("-hc-", na=False)

only_new = st.sidebar.checkbox("Zobraziť len zmeny0")

if only_new:
    df = df[df["zmena"] == "doplnit"]

# -----------------------------
# Main panel
# -----------------------------

st.markdown(f"### {predmet} - {cyklus_vyber}")

if predmet in PREDMETY_VYKONY_POD_CIELMI:
    st.markdown("#### Ciele a výkonové štandardy")
else:
    st.markdown("#### Ciele")


# Hlavný cieľ
hlavny_ciel = df.loc[df["is_hc"], "definicia"]

if not hlavny_ciel.empty:
    st.info(hlavny_ciel.iloc[0])


# Ciele vzdelávania
ciele = df.loc[df["is_c"], "definicia"]

with st.expander("Ciele vzdelávania"):
    render_standardy_as_items(ciele)


# Vzdelávacie štandardy
if predmet in PREDMETY_VYKONY_POD_CIELMI:
    with st.expander("Výkonové štandardy"):
        render_by_typ_standardu(df.loc[df["is_v"]], ziak_vie=True)

    st.markdown("\n")
    st.markdown("#### Obsahové štandardy pre komponenty")

    if predmet == "Človek a príroda":
        uvod_mask = (
            (df["typ_standardu"] == "Úvod")
            & df["is_o"]
        )
        uvod_obsahoveho_standardu = df.loc[uvod_mask, "definicia"]

        if not uvod_obsahoveho_standardu.empty:
            st.markdown(uvod_obsahoveho_standardu.iloc[0], unsafe_allow_html=True)

else:
    st.markdown("#### Vzdelávacie štandardy pre komponenty")


# Rozdelenie podľa vnorených predmetov v Človek a príroda
if predmet == "Človek a príroda" and cyklus == 3:
    predmety_cap = ["Fyzika", "Chémia", "Biológia"]
    vybrane_predmety = st.multiselect(
        "Ktoré predmety vás zaujímajú?",
        predmety_cap,
        default=predmety_cap,
    )
    df = vyber_podla_predmetu_cap(df, vybrane_predmety)


# Výnimka pre cudzí jazyk - druhý jazyk
if cyklus_vyber == "3. cyklus - druhý jazyk (r.6-9)":
    st.tabs(["Komunikačné jazykové činnosti (recepcia, produkcia, interakcia)"])

    druhy_jazyk_info = df.loc[
        df["typ"] == "Výkonový a obsahový štandard",
        "definicia",
    ]

    if not druhy_jazyk_info.empty:
        st.info(druhy_jazyk_info.iloc[0])
    else:
        st.warning("Pre tento výber sa nenašiel výkonový a obsahový štandard.")

    st.stop()


# Komponenty
komponenty = (
    df["komponent"]
    .dropna()
    .unique()
    .tolist()
)

if not komponenty:
    st.error("Pre výber sa nenašli komponenty.")
    st.stop()

tabs_komponenty = st.tabs(komponenty)

for komponent, tab_komponent in zip(komponenty, tabs_komponenty):
    with tab_komponent:
        if predmet not in PREDMETY_VYKONY_POD_CIELMI:
            with st.expander("Výkonové štandardy"):
                df_vykonove = df[
                    (df["komponent"] == komponent)
                    & df["is_v"]
                ].copy()

                # Tematický celok sa používa ako typ štandardu.
                if not df_vykonove.empty:
                    df_vykonove["typ_standardu"] = df_vykonove["tema"].copy()
                else:
                    df_vykonove = df[df["is_v"]].copy()

                render_by_typ_standardu(df_vykonove, ziak_vie=True)

            if predmet not in PREDMETY_BEZ_DELENIA_OBSAH_STANDARDOV:
                st.markdown(
                    "<h5 style='text-align: center;'>Obsahové štandardy</h5>",
                    unsafe_allow_html=True,
                )

        # Obsahové štandardy
        df_obsahove = df[(df["komponent"] == komponent) & df["is_o"]].copy()

        temy = df_obsahove["tema"].dropna().unique().tolist()

        if temy:
            for tema in temy:
                with st.expander(str(tema)):
                    dfl = df_obsahove[df_obsahove["tema"] == tema].copy()
                    render_by_typ_standardu(dfl)
        else:
            if predmet not in PREDMETY_VYKONY_POD_CIELMI:
                with st.expander("Obsahový štandard"):
                    render_by_typ_standardu(df_obsahove)
            else:
                render_by_typ_standardu(df_obsahove)
