import pandas as pd
import streamlit as st
from rapidfuzz import fuzz
from io import BytesIO

st.set_page_config(
    page_title="Digitálny ŠVP",
    page_icon=":ledger:",
    initial_sidebar_state="expanded"
)

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

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=661840704"

    df = pd.read_csv(csv_url)
    df = df.rename(
        columns={
            "typ štandardu": "typ_standardu",
            "tematický celok": "tema",
        }
    )

    df["id"] = df["id"].astype(str)
    df["definicia"] = df["definicia"].astype(str)

    # zvyrazni zmenu
    i_zmena = df["zmena"] == "doplnit"

    # zvyrazni zmenu - nové štandardy sú modre, zmenené sú zelene
    i_zmena = df["zmena"] == "doplnit"
    df.loc[i_zmena, "definicia"] = "<span class='mark_new'>" + df.loc[i_zmena, "definicia"] + '</span>  🆕'

    i_zmena = df["zmena"] == "doplnit_cast"
    df.loc[i_zmena, "definicia"] = "<span class='mark_update'>" + df.loc[i_zmena, "definicia"] + '</span>  ✏️'

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


@st.cache_data(show_spinner="Načítavam štandardy...")
def load_standardy_old() -> pd.DataFrame:
    """Načíta ŠVP v štruktúrovanej podobe."""
    # df = pd.read_csv("standardy_old.csv", sep='\t')

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=1762149550"
    df = pd.read_csv(csv_url)
    df = df.rename(
        columns={
            "typ štandardu": "typ_standardu",
            "tematický celok": "tema",
        }
    )

    i_zmena = df["zmena"] == "update"
    df.loc[i_zmena, "definicia"] = "<span class='mark_update'>" + df.loc[i_zmena, "definicia"] + '</span> ✏️'

    i_zmena = df["zmena"] == "delete"
    df.loc[i_zmena, "definicia"] = "<span class='mark_delete'>" + df.loc[i_zmena, "definicia"] + '</span> 🗑️'

    df["id"] = df["id"].astype(str)
    df["definicia"] = df["definicia"].astype(str)
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


def show_search_results(df):
    """
    Zobrazenie výsledkov vyhľadávania.

    definicia = 'Kriticky posudzovať využitie výsledkov (vedeckého) výskumu pre človeka a spoločnosť.'
    zaradenie = 'Výtvarná výchova | 3. cyklus | Obsahový štandard | Osobnosť | vv3-o-033'
    """
    for id, row in df.iterrows():
        definicia = row.definicia.strip()
        st.markdown(f"<b><span title='{id}'>{definicia}</span></b>",
                    unsafe_allow_html=True)
        zaradenie = f"{row.predmet} | {row.cyklus}. cyklus | {row.typ} | {row.komponent} | {row.tema} | {row.typ_standardu} | {id}"
        zaradenie = zaradenie.replace("none", "")
        zaradenie = zaradenie.replace("|  |  |","|").replace("|  |","|")
        st.markdown(zaradenie, unsafe_allow_html=True)
        st.markdown('---')

def export_to_excel(df):
    """Úprava excel tabuľky na export."""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.close()
    processed_data = output.getvalue()
    return processed_data


# @st.cache_data()
def tranform_to_export(df):
    """Vyčistí definície pre účely exportu."""
    df = df[(df.typ_standardu != 'Úvod')]
    df = df[(df.tema != 'Úvod')]
    df = df[~df["id"].str.contains('-hc-')]
    df = df.rename(columns={'typ_standardu': 'druh', 'tema':'tematicky celok', 'definicia': 'vzdelavaci standard'})

    # vyber stlpcov
    cols_to_xlsx = ['id', 'typ', 'komponent', 'tematicky celok', 'druh', 'vzdelavaci standard']
    df = export_to_excel(df.reset_index()[cols_to_xlsx])
    return df


# -----------------------------
# Načítanie dát
# -----------------------------

if st.sidebar.button("Clear cache"):
    st.cache_data.clear()

# -----------------------------
# Sidebar
# -----------------------------

# Revízia ŠVP
with st.sidebar:
    link = "https://www.minedu.sk/data/files/11808_statny-vzdelavaci-program-pre-zakladne-vzdelavanie-cely.pdf"

    st.markdown(
        f'# <a href="{link}" style="text-decoration:none; color:#004280;">'
        'Digitálna verzia štátneho vzdelávacieho programu 2023 pre ZŠ'
        '</a>',
        unsafe_allow_html=True
    )

    # Vyhľadávanie v štandardoch
    query = st.text_input('Vyhľadávanie v ŠVP', '', key=1,
                          placeholder='🔍 Vyhľadaj štandard, tému alebo kľúčové slovo ...')

    st.markdown('---')

    svp = st.selectbox("Verzia ŠVP", ["2023", "2023 - doplnok č.5"], index=1)

    vzdelavacia_oblast = st.selectbox(
        "Vzdelávacia oblasť",
        list(VZDELAVACIE_OBLASTI.keys()),
    )

    predmety = VZDELAVACIE_OBLASTI[vzdelavacia_oblast]

    if predmety:
        predmet = st.selectbox("Predmet", predmety)
    else:
        predmet = vzdelavacia_oblast

    predmet, tabs_cykly, jazyk = resolve_predmet_a_cykly(predmet)

    cyklus_vyber = st.selectbox("Cyklus", list(tabs_cykly.keys()))
    cyklus = tabs_cykly[cyklus_vyber]

    st.markdown('---')

    if svp == '2023 - doplnok č.5':
        st.markdown("### Zmeny voči dodatku č.5")
        zmeny_only = st.checkbox("Zobraziť len zmeny",
                                 help='Zobrazujú sa iba zmeny zavedené dodatkom č.5 oproti verzii 2023.0.')
        st.markdown("""
                    🟦 🆕 nový\\
                    🟩 ✏️ zmenený
                    """)

    if svp == "2023":
        st.markdown("### Zmeny v doplnku č.5")
        zmeny_only = st.checkbox("Zobraziť len zmeny",
                         help='Zobrazujú sa iba zmeny zavedené dodatkom č.5 oproti verzii 2023.0.')
        st.markdown("""
            🟩 ✏️ zmenený \\
            🟥 🗑️ odstránený
            """)

        st.markdown("""
        ### Prierezové gramotností

        - 📖 🖼️ **Čitateľská a vizuálna gramotnosť**
        - 💻 🌐 **Digitálna gramotnosť**
        - € 📊 **Finančná gramotnosť**
        - 🏛️ 📱 🌍 **Občianska gramotnosť**  
          *(občianska, mediálna, interkultúrna)*
        - 🌱 **Environmentálna gramotnosť**
        - 🧑‍🤝‍🧑 ❤️ **Sociálna a emocionálna gramotnosť**
        """)


# -----------------------------
# Main panel
# -----------------------------

if svp == '2023':
    df = load_standardy_old()

    PREDMETY_VYKONY_POD_CIELMI = {"Človek a príroda", "Človek a spoločnosť", "Informatika", "Matematika"}

    PREDMETY_BEZ_DELENIA_OBSAH_STANDARDOV = {
        "Hudobná výchova",
        "Výtvarná výchova",
        "Zdravie a pohyb",
        *NABOZENSTVA,
    }

if svp == "2023 - doplnok č.5":
    df = load_standardy()

    PREDMETY_VYKONY_POD_CIELMI = {"Človek a príroda", "Človek a spoločnosť"}

    PREDMETY_BEZ_DELENIA_OBSAH_STANDARDOV = {
        "Hudobná výchova",
        "Výtvarná výchova",
        "Zdravie a pohyb",
        "Informatika",
        "Matematika",
        *NABOZENSTVA,
    }

if query:
    st.sidebar.warning(f'Pre návrat na ŠVP zmažte text vo vyhľadávaní.')
    if len(query) < 3:
        st.sidebar.warning('Hľadaný text musí mať aspoň 3 znaky')
    else:
        # vyhľadávanie 1:1
        res = df[df.definicia.str.contains(query)]
        st.sidebar.info(f'Našlo sa {len(res)} podobných záznamov')
        show_search_results(res.head(50).fillna(''))
        if len(res) > 50:
            st.warning("Výsledky vyhľadávania boli skrátené na 50 záznamov.")

        # fuzzy search - ak sa nájde priamou cestou viac ako 5 nájdení
        if len(res) < 5:
            df["res"] = [fuzz.token_set_ratio(t, query) for t in df["definicia"]]  # TODO use processes
            df = df.sort_values("res", ascending=False)
            res2 = df.loc[df.res > 50].fillna('')
            res2 = res2.drop(res.index, errors='ignore')  # odstráni už vyhľadané záznamy cez exact match
            if len(res2) > 0:
                st.info("Výsledky vyhľadávania na základe podobnosti")
                show_search_results(res2.head(30))
                if len(res2) > 30:
                    st.warning("Výsledky vyhľadávania boli skrátené na 30 záznamov.")
    st.stop()

df = filter_data(df, predmet, cyklus, jazyk)

df["is_v"] = df["id"].str.contains("-v-", na=False)
df["is_o"] = df["id"].str.contains("-o-", na=False)
df["is_c"] = df["id"].str.contains("-c-", na=False)
df["is_hc"] = df["id"].str.contains("-hc-", na=False)

if zmeny_only:
    df = df[df["zmena"].notna()]
    rozbal = True
else:
    rozbal = False

col1, col2 = st.columns([6, 1])
with col1:
    st.title(predmet + f" {cyklus}. cyklus")

if vzdelavacia_oblast == predmet:
    st.caption(f"ŠVP {svp} · {vzdelavacia_oblast} · {cyklus}. cyklus")
else:
    st.caption(f"ŠVP {svp} · {vzdelavacia_oblast}")

if zmeny_only:
    st.warning("Zobrazené sú iba zmeny oproti verzii z roku 2023.")


# Hlavný cieľ
hlavny_ciel = df.loc[df["is_hc"], "definicia"]

if not hlavny_ciel.empty:
    st.info(hlavny_ciel.iloc[0])


# Ciele vzdelávania
ciele = df.loc[df["is_c"], "definicia"]

if any(ciele):
    with st.expander("Ciele vzdelávania", expanded=rozbal):
        render_standardy_as_items(ciele)

# Vzdelávacie štandardy
if predmet in PREDMETY_VYKONY_POD_CIELMI:
    if any(df["is_v"]):
        with st.expander("Výkonové štandardy", expanded=rozbal):
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
    st.info("Pre daný filter sa nenašli žiadne štandardy.")
    st.stop()

tabs_komponenty = st.tabs(komponenty)


for komponent, tab_komponent in zip(komponenty, tabs_komponenty):
    with tab_komponent:
        i_komponent = df["komponent"] == komponent

        if predmet not in PREDMETY_VYKONY_POD_CIELMI:
            i_vykonove = i_komponent & df["is_v"]
            if any(i_vykonove):
                with st.expander("Výkonové štandardy", expanded=rozbal):

                    # Tematický celok sa používa ako typ štandardu.
                    if not df[i_vykonove].empty:  # TODO spravne zaradenie v tabulke
                        df.loc[i_vykonove, "typ_standardu"] = df.loc[i_vykonove, "tema"].copy()

                    render_by_typ_standardu(df[i_vykonove], ziak_vie=True)

            if predmet not in PREDMETY_BEZ_DELENIA_OBSAH_STANDARDOV:
                st.markdown(
                    "<h5 style='text-align: left;'>Obsahové štandardy</h5>",
                    unsafe_allow_html=True,
                )

        # Obsahové štandardy
        i_obsahove = i_komponent & df["is_o"]

        temy = df.loc[i_obsahove, "tema"].dropna().unique().tolist()

        if temy:
            for tema in temy:
                with st.expander(str(tema), expanded=rozbal):
                    render_by_typ_standardu(df.loc[i_obsahove & (df["tema"] == tema)])
        else:
            if predmet not in PREDMETY_VYKONY_POD_CIELMI:
                if any(i_obsahove):
                    with st.expander("Obsahový štandard", expanded=rozbal):
                        render_by_typ_standardu(df.loc[i_obsahove])
            else:
                render_by_typ_standardu(df.loc[i_obsahove])

with col2:
    st.download_button(label='📥 Stiahnuť (xlsx)',
                       data=tranform_to_export(df),
                       file_name=f'standardy_{predmet}_c{cyklus}.xlsx')
