import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("ROV Mission Intelligence Platform (RMIP)")
st.subheader("ROV Operational Intelligence Dashboard")

st.markdown("""
Analyze ROV mission telemetry data, detect anomalies, and visualize subsea operations in real time.
""")

st.info("Upload a CSV file with columns like: timestamp, depth, latitude, longitude, signal_quality")
uploaded_file = st.file_uploader("Upload Mission Log CSV", type=["csv"])

# 🔥 CACHE
@st.cache_data
def load_data(file):
    df = pd.read_csv(file, sep=None, engine="python")
    if len(df.columns) == 1:
        file.seek(0)
        df = pd.read_csv(file, sep=";")
    return df

if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)

        # Normaliza colunas
        df.columns = df.columns.str.strip().str.lower()

        # Corrige timestamp
        for col in df.columns:
            if 'time' in col:
                df.rename(columns={col: 'timestamp'}, inplace=True)

        # Corrige depth
        for col in df.columns:
            if 'depth' in col or 'profundidade' in col or col == 'z':
                df.rename(columns={col: 'depth'}, inplace=True)

        # Corrige latitude/longitude
        for col in df.columns:
            if 'lat' in col:
                df.rename(columns={col: 'latitude'}, inplace=True)
            if 'lon' in col:
                df.rename(columns={col: 'longitude'}, inplace=True)

    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    st.write("Colunas detectadas:", list(df.columns))

    # Validação
    required_columns = ['timestamp', 'depth']
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # Converte timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    # Remove linhas inválidas
    df = df.dropna(subset=['timestamp'])

    # Preview
    st.subheader("Mission Data Preview")
    st.dataframe(df)

    # 🔥 FILTRO DE TEMPO SEGURO
    st.subheader("Time Filter")

    min_date = df['timestamp'].min()
    max_date = df['timestamp'].max()

    start_date = st.date_input("Start Date", min_date)
    end_date = st.date_input("End Date", max_date)

    if start_date and end_date:
        df = df[
            (df['timestamp'] >= pd.to_datetime(start_date)) &
            (df['timestamp'] <= pd.to_datetime(end_date))
        ]

    # 🔥 PROTEÇÃO CONTRA DATAFRAME VAZIO
    if df.empty:
        st.warning("No data available for selected date range")
        st.stop()

    # Gráfico
    fig = px.line(df, x='timestamp', y='depth', title='Depth Over Time')
    st.plotly_chart(fig, use_container_width=True)

    # KPIs
    max_depth = df['depth'].max()
    mean_depth = df['depth'].mean()

    if 'signal_quality' in df.columns:
        signal_loss = (df['signal_quality'] < 50).sum() / len(df) * 100
    else:
        signal_loss = None

    col1, col2, col3 = st.columns(3)
    col1.metric("Max Depth (m)", round(max_depth, 2))
    col2.metric("Mean Depth (m)", round(mean_depth, 2))
    if signal_loss is not None:
        col3.metric("Signal Loss (%)", round(signal_loss, 2))

    # Alerts
    st.subheader("Operational Alerts")
    if signal_loss is not None and signal_loss > 10:
        st.warning(f"High signal loss detected: {signal_loss:.2f}%")
    if max_depth > 200:
        st.error("Depth exceeded safe operational limit!")

    # 3D
    if all(col in df.columns for col in ['latitude', 'longitude', 'depth']):
        st.subheader("3D Mission Visualization")
        fig_3d = go.Figure(data=[go.Scatter3d(
            x=df['longitude'],
            y=df['latitude'],
            z=df['depth'],
            mode='lines+markers',
            marker=dict(size=3),
            line=dict(width=4)
        )])
        fig_3d.update_layout(
            scene=dict(
                zaxis=dict(autorange="reversed"),
                xaxis_title='Longitude',
                yaxis_title='Latitude',
                zaxis_title='Depth'
            )
        )
        st.plotly_chart(fig_3d, use_container_width=True)

    # 🌍 MAPA
    if all(col in df.columns for col in ['latitude', 'longitude']):
        st.subheader("ROV Mission Map")

        fig_map = px.line_mapbox(
            df,
            lat="latitude",
            lon="longitude",
            hover_data=["depth"] if "depth" in df.columns else None,
            zoom=10,
            height=500
        )

        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0}
        )

        st.plotly_chart(fig_map, use_container_width=True)

    # Coverage
    if all(col in df.columns for col in ['latitude', 'longitude']):
        st.subheader("Mission Coverage Analysis")

        lat_bins = pd.cut(df['latitude'], bins=10)
        lon_bins = pd.cut(df['longitude'], bins=10)

        coverage = df.groupby([lat_bins, lon_bins]).size().reset_index(name='count')
        coverage_percent = (len(coverage) / (10 * 10)) * 100

        st.metric("Coverage (%)", round(coverage_percent, 2))
