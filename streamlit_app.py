import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("ROV Mission Intelligence Platform (RMIP)")
st.subheader("Telemetry Dashboard")

# Upload do arquivo CSV
uploaded_file = st.file_uploader("Upload Mission Log CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # 🔥 Leitura robusta (resolve seu problema)
        df = pd.read_csv(uploaded_file, sep=None, engine="python")

        # 🔥 Normalização das colunas
        df.columns = df.columns.str.strip().str.lower()

    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    # Debug (pode remover depois)
    st.write("Colunas detectadas:", df.columns)

    # Validação de colunas obrigatórias
    required_columns = ['timestamp', 'depth']
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # Preview dos dados
    st.subheader("Mission Data Preview")
    st.dataframe(df)

    # Gráfico de profundidade ao longo do tempo
    fig = px.line(df, x='timestamp', y='depth', title='Depth Over Time')
    st.plotly_chart(fig, use_container_width=True)

    # Métricas básicas
    max_depth = df['depth'].max()
    mean_depth = df['depth'].mean()

    # Cálculo de Signal Loss (%)
    if 'signal_quality' in df.columns:
        signal_loss = (df['signal_quality'] < 50).sum() / len(df) * 100
    else:
        signal_loss = None

    # KPIs
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

    # 3D Mission Visualization
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

    # Mission Coverage Analysis
    if all(col in df.columns for col in ['latitude', 'longitude']):
        st.subheader("Mission Coverage Analysis")
        lat_bins = pd.cut(df['latitude'], bins=10)
        lon_bins = pd.cut(df['longitude'], bins=10)
        coverage = df.groupby([lat_bins, lon_bins]).size().reset_index(name='count')
        coverage_percent = (len(coverage) / (10 * 10)) * 100
        st.metric("Coverage (%)", round(coverage_percent, 2))
