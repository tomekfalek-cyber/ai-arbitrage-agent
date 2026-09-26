"""
AI Arbitrage Agent – Streamlit Cloud ready
- Monitor boxów: Olimibox, Returnstore, Amazon
- Skaner OLX (okazje)
- Ewidencja sprzedaży (działalność nierejestrowana 2026)
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from modules.boxes import get_all_boxes
from modules.ewidencja import render_tab as render_ewidencja
from modules.olx import search_olx
from modules.utils import format_pln, today_str

st.set_page_config(
    page_title="AI Arbitrage Agent",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----- Minimal clean theme -----
st.markdown(
    """
<style>
html, body, [class*="css"] { font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; }
.stApp { background: #0F1115; color: #E4E7EC; }
header[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem !important; max-width: 1100px; }
h1 { font-size: 1.65rem !important; font-weight: 700 !important; color: #F5F6F8 !important; }
h2, h3 { color: #F5F6F8 !important; }
section[data-testid="stSidebar"] { background: #14171D !important; border-right: 1px solid #23262E; }
div[data-testid="stMetric"] {
    background: #171A21; border: 1px solid #23262E; border-radius: 10px; padding: 12px 16px;
}
.offer-card {
    background: #171A21; border: 1px solid #23262E; border-radius: 10px;
    padding: 14px 16px; margin-bottom: 10px;
}
.source-pill {
    display: inline-block; background: #23262E; color: #A0A8B4;
    font-size: 0.72rem; padding: 2px 8px; border-radius: 999px; margin-right: 6px;
}
.price-tag { color: #34D399; font-weight: 700; font-size: 1.05rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ----- Sidebar -----
with st.sidebar:
    st.markdown("### Ustawienia")
    max_buy = st.number_input("Maks. cena zakupu OLX (zł)", min_value=50.0, max_value=10000.0, value=800.0, step=50.0)
    min_margin = st.slider("Min. marża szacunkowa %", 10, 100, 30, 5)
    st.caption("Marża szacunkowa = (sugerowana sprzedaż − zakup) / zakup. Boxy nie mają automatycznej mediany.")
    st.markdown("---")
    st.markdown("**Klucze API (opcjonalne)**")
    st.text_input("Allegro Client ID", type="password", key="allegro_id")
    st.text_input("Allegro Client Secret", type="password", key="allegro_secret")
    st.text_input("Amazon Access Key", type="password", key="amazon_key")
    st.caption("Bez kluczy: OLX + boxy (Olimibox/Returnstore) działają. Amazon = linki wyszukiwania.")
    st.markdown("---")
    st.caption("Limit działalności nierejestrowanej 2026: **10 813,50 zł / kwartał**")

# ----- Header -----
st.title("AI Arbitrage Agent")
st.caption("Boxy zwrotów · okazje OLX · ewidencja sprzedaży (PL 2026)")

tab_boxes, tab_olx, tab_ewid, tab_about = st.tabs(
    ["📦 Boxy (Olimibox / Returnstore / Amazon)", "🔍 Skaner OLX", "📒 Ewidencja sprzedaży", "ℹ️ O aplikacji"]
)

# ========== TAB 1: BOXY ==========
with tab_boxes:
    st.subheader("Aktualne oferty boxów i palet")
    st.caption(
        "Śledzone produkty: Box Mix A (Olimibox) oraz ElectroBox zwroty (Returnstore). "
        "Dodatkowo skan listingów + linki Amazon.pl."
    )

    col_a, col_b = st.columns([1, 3])
    with col_a:
        run_boxes = st.button("Odśwież boxy", type="primary", use_container_width=True)
    with col_b:
        include_listings = st.checkbox("Pobierz też listingi kategorii", value=True)

    if run_boxes or "boxes_cache" not in st.session_state:
        with st.spinner("Pobieram oferty z Olimibox, Returnstore i przygotowuję linki Amazon..."):
            try:
                boxes = get_all_boxes(include_listings=include_listings)
                st.session_state.boxes_cache = boxes
            except Exception as e:
                st.error(f"Błąd pobierania: {e}")
                st.session_state.boxes_cache = []

    boxes = st.session_state.get("boxes_cache", [])
    if not boxes:
        st.info("Kliknij **Odśwież boxy**, aby pobrać aktualne oferty.")
    else:
        featured = [b for b in boxes if b.get("type") == "featured"]
        listings = [b for b in boxes if b.get("type") == "listing"]
        amazon = [b for b in boxes if b.get("type") == "amazon_search"]

        if featured:
            st.markdown("#### Śledzone produkty (Twoje URL)")
            for b in featured:
                price_txt = format_pln(b["price"]) if b.get("price") else "sprawdź na stronie"
                retail = f" · sugerowana detal ~{format_pln(b['retail_hint'])}" if b.get("retail_hint") else ""
                st.markdown(
                    f"""
                    <div class="offer-card">
                        <span class="source-pill">{b.get('source')}</span>
                        <span class="source-pill">{b.get('category')}</span>
                        <div style="margin-top:6px;font-weight:600;color:#F5F6F8;">{b.get('title')}</div>
                        <div style="margin-top:8px;">
                            <span class="price-tag">{price_txt}</span>
                            <span style="color:#8A93A3;font-size:0.85rem;">{retail}</span>
                            <span style="color:#8A93A3;font-size:0.85rem;"> · {b.get('available')}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if b.get("url"):
                    st.link_button("Otwórz ofertę", b["url"], use_container_width=False)

        if listings:
            st.markdown("#### Inne boxy / palety z listingów")
            rows = []
            for b in listings:
                rows.append(
                    {
                        "Źródło": b.get("source"),
                        "Tytuł": (b.get("title") or "")[:80],
                        "Cena": b.get("price") or None,
                        "URL": b.get("url"),
                    }
                )
            df = pd.DataFrame(rows)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("Link"),
                    "Cena": st.column_config.NumberColumn("Cena (zł)", format="%.0f"),
                },
            )

        if amazon:
            st.markdown("#### Amazon.pl – szybkie linki")
            st.caption("Amazon nie udostępnia darmowego feedu cen bez Product Advertising API. Poniżej gotowe wyszukiwania.")
            for b in amazon:
                st.markdown(f"**{b.get('title')}**")
                st.link_button("Otwórz na Amazon.pl", b["url"])

        # CSV export
        flat = [
            {
                "source": b.get("source"),
                "title": b.get("title"),
                "price": b.get("price"),
                "url": b.get("url"),
                "type": b.get("type"),
            }
            for b in boxes
        ]
        st.download_button(
            "Pobierz listę boxów (CSV)",
            data=pd.DataFrame(flat).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"boxy_{today_str()}.csv",
            mime="text/csv",
        )

# ========== TAB 2: OLX ==========
with tab_olx:
    st.subheader("Skaner okazji OLX")
    query = st.text_input("Fraza produktowa", value="słuchawki bluetooth", placeholder="np. iPhone 13, robot Xiaomi...")
    run_olx = st.button("Szukaj na OLX", type="primary")

    if run_olx and query.strip():
        with st.spinner("Szukam na OLX..."):
            offers = search_olx(query.strip(), max_price=max_buy, limit=20)
        if not offers:
            st.warning("Brak wyników lub strona OLX zablokowała zapytanie. Spróbuj inną frazę lub później.")
        else:
            st.success(f"Znaleziono {len(offers)} ofert do {format_pln(max_buy)}")
            for o in offers:
                est_sell = o["price"] * (1 + min_margin / 100)
                profit = est_sell - o["price"]
                st.markdown(
                    f"""
                    <div class="offer-card">
                        <span class="source-pill">OLX</span>
                        <div style="margin-top:6px;font-weight:600;">{o['title']}</div>
                        <div style="margin-top:8px;font-size:0.9rem;">
                            Kup: <b>{format_pln(o['price'])}</b>
                            · Szac. sprzedaż (@{min_margin}%): <b>{format_pln(est_sell)}</b>
                            · Zysk ~ <span class="price-tag">{format_pln(profit)}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if o.get("url"):
                    st.link_button("Otwórz na OLX", o["url"])
            df = pd.DataFrame(offers)
            st.download_button(
                "Pobierz wyniki OLX (CSV)",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"olx_{today_str()}.csv",
                mime="text/csv",
            )
    else:
        st.info("Wpisz frazę i kliknij **Szukaj na OLX**.")

# ========== TAB 3: EWIDENCJA ==========
with tab_ewid:
    render_ewidencja()

# ========== TAB 4: ABOUT ==========
with tab_about:
    st.markdown(
        """
### Co robi aplikacja
1. **Boxy** – pobiera aktualne ceny i dostępność z Olimibox.pl oraz Returnstore.pl  
   (w tym Twoje konkretne URL: Box Mix A i ElectroBox zwroty).  
   Amazon.pl: gotowe linki wyszukiwania (pełne ceny wymagają PA-API).
2. **Skaner OLX** – szuka tanich ofert pod odsprzedaż.
3. **Ewidencja sprzedaży** – zgodna z wymogami działalności nierejestrowanej 2026  
   (limit **10 813,50 zł przychodu należnego na kwartał**).

### Deploy na Streamlit Cloud
1. Wrzuć to repo na GitHub (cały folder).
2. [share.streamlit.io](https://share.streamlit.io) → New app → Main file: `app.py`.
3. Gotowe. Dane ewidencji są w sesji przeglądarki – **pobieraj CSV** regularnie.

### Uwagi prawne / regulaminy
- Scraping w rozsądnych limitach, tylko do użytku prywatnego.
- Respektuj regulaminy Olimibox, Returnstore, OLX, Amazon, Allegro.
- Regularny handel zwrotami = działalność gospodarcza; ewidencja nie zwalnia z limitu.

### Limit działalności nierejestrowanej (2026)
- **10 813,50 zł** przychodu należnego na kwartał  
- Po przekroczeniu: 7 dni na CEIDG  
- Dochód w PIT-36 (skala podatkowa)
"""
    )

st.markdown("---")
st.caption(f"AI Arbitrage Agent · {today_str()} · używaj odpowiedzialnie")
