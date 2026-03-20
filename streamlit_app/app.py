import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import pycountry
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Negativity Instinct vs Child Survival",
    page_icon="🌍",
    layout="wide",
)

# -----------------------------
# helpers
# -----------------------------
@st.cache_data
def load_perception():
    df = pd.read_csv("streamlit_app/world_getting_worse_extracted.csv")

    if "country_iso3" not in df.columns:
        if "country" not in df.columns:
            raise ValueError("world_getting_worse_extracted.csv must contain 'country' or 'country_iso3'.")
        iso_list = []
        for c in df["country"]:
            try:
                iso_list.append(pycountry.countries.lookup(c).alpha_3)
            except Exception:
                iso_list.append(None)
        df["country_iso3"] = iso_list

    if "country" not in df.columns:
        names = []
        for iso in df["country_iso3"]:
            try:
                names.append(pycountry.countries.get(alpha_3=iso).name)
            except Exception:
                names.append(iso)
        df["country"] = names

    if "pct_answered_world_getting_worse" not in df.columns:
        raise ValueError("world_getting_worse_extracted.csv must contain 'pct_answered_world_getting_worse'.")

    df = df.dropna(subset=["country_iso3"]).copy()
    return df


@st.cache_data
def load_u5mr():
    df = pd.read_csv("streamlit_app/u5mr_country_year_all_countries.csv")

    df = df.rename(columns={
        "country_iso": "country_iso3",
        "country_name": "country",
        "u5mr_estimate": "u5mr",
        "standard_error_of_estimates": "standard_error",
    })

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["u5mr"] = pd.to_numeric(df["u5mr"], errors="coerce")
    df["standard_error"] = pd.to_numeric(df["standard_error"], errors="coerce")

    if "is_interpolated" in df.columns:
        df["is_interpolated"] = df["is_interpolated"].astype(str).str.upper().eq("TRUE")
    else:
        df["is_interpolated"] = False

    df["95% CI Lower"] = df["u5mr"] - 1.96 * df["standard_error"]
    df["95% CI Upper"] = df["u5mr"] + 1.96 * df["standard_error"]

    return df


@st.cache_data
def load_world_geojson():
    url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


def get_country_name(df, iso3):
    row = df[df["country_iso3"] == iso3]
    if row.empty:
        return iso3
    return row["country"].iloc[0]


# -----------------------------
# load data
# -----------------------------
perception_df = load_perception()
u5mr_df = load_u5mr()
world_geojson = load_world_geojson()

iso_choices = sorted(
    set(perception_df["country_iso3"].dropna()) &
    set(u5mr_df["country_iso3"].dropna())
)

if not iso_choices:
    st.error("No overlapping country_iso3 values found between perception and U5MR data.")
    st.stop()

default_iso = "JPN" if "JPN" in iso_choices else iso_choices[0]

if "selected_iso" not in st.session_state:
    st.session_state.selected_iso = default_iso

map_df = perception_df[perception_df["country_iso3"].isin(iso_choices)].copy()

# -----------------------------
# style
# -----------------------------
st.markdown(
    """
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        color: #2b2d42;
        margin-bottom: 0.25rem;
    }
    .sub-title {
        color: #7a7f8c;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-title">Negativity Instinct vs Child Survival</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Factfulness-inspired interactive dashboard</div>', unsafe_allow_html=True)

left, right = st.columns([1.7, 1.0], gap="large")

# -----------------------------
# left
# -----------------------------
with left:
    st.markdown("#### Select country")

    chosen_from_dropdown = st.selectbox(
        "Country",
        iso_choices,
        index=iso_choices.index(st.session_state.selected_iso) if st.session_state.selected_iso in iso_choices else 0,
        format_func=lambda x: f"{x} - {get_country_name(perception_df, x)}",
        label_visibility="collapsed",
    )
    st.session_state.selected_iso = chosen_from_dropdown

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

    # GeoJSON に tooltip 用プロパティ追加
    value_map = dict(zip(map_df["country_iso3"], map_df["pct_answered_world_getting_worse"]))
    name_map = dict(zip(map_df["country_iso3"], map_df["country"]))

    for feature in world_geojson["features"]:
        iso3 = feature.get("id")
        if "properties" not in feature or feature["properties"] is None:
            feature["properties"] = {}
        feature["properties"]["country_iso3"] = iso3
        feature["properties"]["country_name"] = name_map.get(iso3, iso3)
        feature["properties"]["negativity_ratio"] = value_map.get(iso3, None)

    choropleth = folium.Choropleth(
        geo_data=world_geojson,
        data=map_df,
        columns=["country_iso3", "pct_answered_world_getting_worse"],
        key_on="feature.id",
        fill_color="YlOrRd",
        fill_opacity=0.85,
        line_opacity=0.5,
        line_color="gray",
        legend_name="% saying world is getting worse",
        nan_fill_color="#d9d9d9",
        highlight=True,
    )
    choropleth.add_to(m)

    tooltip = folium.features.GeoJsonTooltip(
        fields=["country_name", "country_iso3", "negativity_ratio"],
        aliases=["Country", "ISO3", "Negativity Instinct ratio"],
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 6px;
            box-shadow: 3px;
        """,
    )

    geojson_layer = folium.GeoJson(
        world_geojson,
        style_function=lambda x: {
            "fillColor": "transparent",
            "color": "transparent",
            "weight": 0.1,
            "fillOpacity": 0.0,
        },
        highlight_function=lambda x: {
            "fillColor": "#00000000",
            "color": "#222222",
            "weight": 2.5,
            "fillOpacity": 0.0,
        },
        tooltip=tooltip,
    )
    geojson_layer.add_to(m)

    map_state = st_folium(
        m,
        width=None,
        height=700,
        returned_objects=["last_active_drawing", "last_object_clicked_tooltip"],
        key="negativity_map",
    )

    clicked_tooltip = map_state.get("last_object_clicked_tooltip", None)
    if isinstance(clicked_tooltip, dict):
        clicked_iso = clicked_tooltip.get("country_iso3")
        if clicked_iso and clicked_iso in iso_choices and clicked_iso != st.session_state.selected_iso:
            st.session_state.selected_iso = clicked_iso
            st.rerun()

# -----------------------------
# right
# -----------------------------
with right:
    selected_iso = st.session_state.selected_iso
    p = perception_df[perception_df["country_iso3"] == selected_iso].copy()
    u = u5mr_df[u5mr_df["country_iso3"] == selected_iso].copy().sort_values("year")

    country_name = p["country"].iloc[0] if not p.empty else selected_iso
    negativity_ratio = p["pct_answered_world_getting_worse"].iloc[0] if not p.empty else None

    st.subheader(f"{country_name} ({selected_iso})")

    info_df = pd.DataFrame({
        "Item": ["Country", "ISO3", "Negativity Instinct ratio"],
        "Value": [
            country_name,
            selected_iso,
            "N/A" if pd.isna(negativity_ratio) else f"{negativity_ratio:.1f}%"
        ],
    })
    st.table(info_df)

    st.markdown("**Under-five mortality rate (U5MR): deaths per 1,000 live births**")

    if u.empty:
        st.warning("No U5MR data available for this country.")
    else:
        fig_line = go.Figure()

        ci = u.dropna(subset=["95% CI Lower", "95% CI Upper"]).copy()
        if not ci.empty:
            fig_line.add_trace(go.Scatter(
                x=ci["year"],
                y=ci["95% CI Upper"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            ))
            fig_line.add_trace(go.Scatter(
                x=ci["year"],
                y=ci["95% CI Lower"],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(198,40,40,0.16)",
                name="95% CI",
                hoverinfo="skip",
            ))

        fig_line.add_trace(go.Scatter(
            x=u["year"],
            y=u["u5mr"],
            mode="lines",
            name="U5MR",
            line=dict(color="#c62828", width=3),
        ))

        fig_line.update_layout(
            title=f"U5MR trend: {country_name}",
            height=380,
            margin=dict(l=0, r=0, t=45, b=0),
            xaxis_title="Year",
            yaxis_title="Deaths per 1,000 live births",
            legend_title="",
        )
        st.plotly_chart(fig_line, use_container_width=True)

        st.caption(
            "U5MR measures the number of children dying before age 5 per 1,000 live births. "
            "Shaded band shows the 95% confidence interval when standard errors are available."
        )

        interpolated_share = u["is_interpolated"].mean() * 100 if "is_interpolated" in u.columns else None

        st.markdown("**Data sources and missingness**")
        meta_df = pd.DataFrame({
            "Item": [
                "Perception data source",
                "U5MR data source",
                "U5MR interpolated share",
            ],
            "Value": [
                "Factfulness / Gapminder visualization based on YouGov and Ipsos MORI survey results",
                "UN Inter-agency Group for Child Mortality Estimation (UN IGME)",
                "N/A" if interpolated_share is None or pd.isna(interpolated_share) else f"{interpolated_share:.1f}%"
            ],
        })
        st.table(meta_df)