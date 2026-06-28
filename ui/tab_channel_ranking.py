import time
import streamlit as st
import config
from modules.channel_ranker import fetch_trending_channels


COUNTRIES = {
    "Argentina": "AR", "Australia": "AU", "Austria": "AT", "Belgium": "BE",
    "Bolivia": "BO", "Brazil": "BR", "Canada": "CA", "Chile": "CL",
    "Colombia": "CO", "Croatia": "HR", "Czech Republic": "CZ", "Denmark": "DK",
    "Ecuador": "EC", "Egypt": "EG", "Finland": "FI", "France": "FR",
    "Germany": "DE", "Ghana": "GH", "Greece": "GR", "Hungary": "HU",
    "India": "IN", "Indonesia": "ID", "Ireland": "IE", "Israel": "IL",
    "Italy": "IT", "Japan": "JP", "Kenya": "KE", "Malaysia": "MY",
    "Mexico": "MX", "Morocco": "MA", "Netherlands": "NL", "New Zealand": "NZ",
    "Nigeria": "NG", "Norway": "NO", "Pakistan": "PK", "Panama": "PA",
    "Paraguay": "PY", "Peru": "PE", "Philippines": "PH", "Poland": "PL",
    "Portugal": "PT", "Romania": "RO", "Russia": "RU", "Saudi Arabia": "SA",
    "Singapore": "SG", "South Africa": "ZA", "South Korea": "KR", "Spain": "ES",
    "Sweden": "SE", "Switzerland": "CH", "Taiwan": "TW", "Thailand": "TH",
    "Turkey": "TR", "Ukraine": "UA", "United Arab Emirates": "AE",
    "United Kingdom": "GB", "United States": "US", "Uruguay": "UY",
    "Venezuela": "VE", "Vietnam": "VN", "Zimbabwe": "ZW",
}

CACHE_TTL = 3600  # 1 hour


def _fmt_number(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def render_channel_ranking():
    st.header("Channel Rankings")
    st.caption("Top channels dominating YouTube trending right now, by country.")

    if not config.YOUTUBE_API_KEY:
        st.error("Add your YOUTUBE_API_KEY to config.py")
        return

    col1, col2 = st.columns([2, 2])
    with col1:
        sorted_countries = sorted(COUNTRIES.keys())
        default_idx = sorted_countries.index("United States")
        country_name = st.selectbox("Country", options=sorted_countries, index=default_idx)
    with col2:
        metric = st.radio("Rank by", ["🔥 Trending Videos", "👁 Trending Views"], horizontal=True)

    country_code = COUNTRIES[country_name]
    cache_key = f"ranking_{country_code}"
    cache_ts_key = f"ranking_{country_code}_ts"

    now = time.time()
    cached_ts = st.session_state.get(cache_ts_key, 0)
    is_fresh = (now - cached_ts) < CACHE_TTL

    if is_fresh and cache_key in st.session_state:
        age_min = int((now - cached_ts) / 60)
        st.caption(f"Last updated {age_min} min ago · click Load Rankings to refresh")

    if st.button("Load Rankings", type="primary"):
        with st.spinner(f"Fetching trending data for {country_name}..."):
            try:
                results = fetch_trending_channels(country_code, config.YOUTUBE_API_KEY)
                st.session_state[cache_key] = results
                st.session_state[cache_ts_key] = time.time()
            except Exception as e:
                msg = str(e)
                if "invalid" in msg.lower() or "400" in msg:
                    st.error("Invalid YouTube API key. Check YOUTUBE_API_KEY in config.py.")
                elif "quota" in msg.lower() or "403" in msg:
                    st.error("YouTube API quota exceeded. Try again tomorrow.")
                else:
                    st.error(str(e))
                return

    if cache_key not in st.session_state:
        return
    results = st.session_state[cache_key]
    if not results:
        st.info("No trending data available for this country. Try another.")
        return

    sort_key = "trending_count" if "Videos" in metric else "trending_views"
    sorted_results = sorted(results, key=lambda x: x[sort_key], reverse=True)

    st.divider()
    for rank, ch in enumerate(sorted_results, start=1):
        col_rank, col_thumb, col_info = st.columns([0.5, 1, 8])
        with col_rank:
            st.markdown(f"**#{rank}**")
        with col_thumb:
            if ch["thumbnail"]:
                st.image(ch["thumbnail"], width=40)
        with col_info:
            yt_url = f"https://www.youtube.com/channel/{ch['channel_id']}"
            st.markdown(
                f'<a href="{yt_url}" target="_blank" style="color:#e2e8f0;font-weight:600;text-decoration:none;">{ch["name"]}</a>'
                f'&nbsp;&nbsp;·&nbsp;&nbsp;👥 {_fmt_number(ch["subscribers"])} subs'
                f'&nbsp;&nbsp;·&nbsp;&nbsp;🔥 {_fmt_number(ch["trending_count"])} trending'
                f'&nbsp;&nbsp;·&nbsp;&nbsp;👁 {_fmt_number(ch["trending_views"])} views',
                unsafe_allow_html=True,
            )
