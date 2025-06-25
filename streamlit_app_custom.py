import streamlit as st
import pandas as pd
import plotly.express as px

def highlight_second_max(s, color='yellow'):
    if s.dtype in ['int64', 'float64']:
        second_max = s.nlargest(2).iloc[-1]
        return ['background-color: %s' % color if v == second_max else '' for v in s]
    return [''] * len(s)

def calculate_costs_custom(inputs, env):
    costs = {}

    # Solo para Producción, añadir los valores fijos (ANUALES)
    if env == "Producción":
        costs['GitLab'] = 73350
        costs['CheckMarx'] = 26265.5
        costs['Sonarqube'] = 32643.78  # Valor actualizado

    # CodePipeline (mensual)
    v1_pipelines = inputs['codepipeline_v1']
    v2_minutes = inputs['codepipeline_v2']
    costs['CodePipeline'] = max(v1_pipelines - 1, 0)*1.00 + max(v2_minutes - 100, 0)*0.002

    # CodeBuild (mensual)
    builds = inputs['codebuild_builds']
    duration = inputs['codebuild_duration']
    duration_sec = duration * 60
    costs['CodeBuild'] = builds * duration_sec * 0.00002

    # CodeArtifact (mensual)
    storage = inputs['codeartifact_storage']
    requests = inputs['codeartifact_requests']
    intra = inputs['codeartifact_intra']
    outbound = inputs['codeartifact_outbound']

    storage_cost = max(storage - 2, 0) * 0.05
    requests_cost = max(requests - 100000, 0) * 0.000005
    intra_cost = intra * 0.02
    outbound_cost = outbound * 0.09

    costs['CodeArtifact'] = storage_cost + requests_cost + intra_cost + outbound_cost + 0.60

    return costs

# --- CONFIGURACIÓN DE PÁGINA Y ENCABEZADO VISUAL ---
st.set_page_config(page_title="AWS Cost Calculator (Custom)", layout="wide")
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image("https://a0.awsstatic.com/libra-css/images/logos/aws_logo_smile_1200x630.png", width=80)
with col_title:
    st.title("Calculadora de Costos AWS (Custom) 📊")

st.markdown("""
<div style='font-size:18px; color:#444;'>
Esta herramienta te permite comparar los costos estimados de diferentes entornos de AWS.<br>
<b>¿Cómo usarla?</b>
</div>
""", unsafe_allow_html=True)

# --- GUÍA RÁPIDA EN EXPANDER ---
with st.expander("🛈 Guía rápida de uso"):
    st.markdown("""
    1. **Selecciona los entornos** que deseas comparar (Producción, Desarrollo, Pruebas, QA).
    2. **Ajusta los parámetros** de cada entorno en la barra lateral (puedes dejar los valores por defecto o personalizarlos).
    3. Si lo prefieres, haz clic en **"Cargar ejemplo rápido"** para ver un caso de ejemplo.
    4. Observa los resultados, visualizaciones y recomendaciones automáticas.
    """)

st.markdown("---")

# --- BOTÓN DE EJEMPLO DESTACADO ---
col_btn, col_spacer = st.columns([2, 8])
with col_btn:
    if st.button("✨ Cargar ejemplo rápido"):
        st.session_state.update({
            "Producción_codepipeline_v1": 5,
            "Producción_codepipeline_v2": 25000,
            "Producción_codebuild_builds": 25000,
            "Producción_codebuild_duration": 5,
            "Producción_codeartifact_storage": 100,
            "Producción_codeartifact_requests": 25000,
            "Producción_codeartifact_intra": 0.0,
            "Producción_codeartifact_outbound": 100.0,
            "Desarrollo (DEV)_codepipeline_v1": 2,
            "Desarrollo (DEV)_codepipeline_v2": 100000,
            "Desarrollo (DEV)_codebuild_builds": 100000,
            "Desarrollo (DEV)_codebuild_duration": 5,
            "Desarrollo (DEV)_codeartifact_storage": 100,
            "Desarrollo (DEV)_codeartifact_requests": 100000,
            "Desarrollo (DEV)_codeartifact_intra": 0.0,
            "Desarrollo (DEV)_codeartifact_outbound": 100.0,
            "Pruebas (UAT)_codepipeline_v1": 1,
            "Pruebas (UAT)_codepipeline_v2": 25000,
            "Pruebas (UAT)_codebuild_builds": 25000,
            "Pruebas (UAT)_codebuild_duration": 5,
            "Pruebas (UAT)_codeartifact_storage": 100,
            "Pruebas (UAT)_codeartifact_requests": 25000,
            "Pruebas (UAT)_codeartifact_intra": 0.0,
            "Pruebas (UAT)_codeartifact_outbound": 100.0,
            "QA_codepipeline_v1": 1,
            "QA_codepipeline_v2": 50000,
            "QA_codebuild_builds": 50000,
            "QA_codebuild_duration": 5,
            "QA_codeartifact_storage": 100,
            "QA_codeartifact_requests": 50000,
            "QA_codeartifact_intra": 0.0,
            "QA_codeartifact_outbound": 100.0,
        })
        st.experimental_rerun()

# --- Selección de entornos para comparar ---
st.header("🔍 Comparación de Entornos")
environments = ["Producción", "Desarrollo (DEV)", "Pruebas (UAT)", "QA"]
selected_environments = st.multiselect(
    "Seleccionar Entornos a Comparar",
    environments,
    default=["Producción", "Desarrollo (DEV)"],
    help="Selecciona los entornos que deseas comparar"
)
st.markdown("---")

# --- SIDEBAR: INPUTS AGRUPADOS POR SERVICIO ---
with st.sidebar:
    st.header("⚙️ Configuración de Entornos")
    environment_inputs = {}
    for env in environments:
        with st.expander(f"Configuración {env}"):
            st.markdown("Ajusta los parámetros de cada servicio para este entorno.")
            tab1, tab2, tab3 = st.tabs(["CodePipeline", "CodeBuild", "CodeArtifact"])
            with tab1:
                st.subheader("CodePipeline")
                codepipeline_v1 = st.number_input(
                    f"{env} - V1 - Pipelines activos", 0, 50000, 0,
                    help="Cantidad de pipelines activos en CodePipeline versión 1. El primero es gratuito.",
                    key=f"{env}_codepipeline_v1")
                codepipeline_v2 = st.number_input(
                    f"{env} - V2 - Minutos ejecución", 0, 100000,
                    25000 if env == "Producción" else (
                    100000 if env == "Desarrollo (DEV)" else (
                    25000 if env == "Pruebas (UAT)" else 50000)),
                    help="Primeros 100 minutos gratuitos", key=f"{env}_codepipeline_v2")
            with tab2:
                st.subheader("CodeBuild")
                codebuild_builds = st.number_input(
                    f"{env} - Builds/mes", 0, 10000000,
                    25000 if env == "Producción" else (
                    100000 if env == "Desarrollo (DEV)" else (
                    25000 if env == "Pruebas (UAT)" else 50000)),
                    help="Número total de builds mensuales", key=f"{env}_codebuild_builds")
                codebuild_duration = st.number_input(
                    f"{env} - Duración (min)", 0, 600, 5,
                    help="Duración promedio por build", key=f"{env}_codebuild_duration")
            with tab3:
                st.subheader("CodeArtifact")
                codeartifact_storage = st.number_input(
                    f"{env} - Almacenamiento (GB)", 0, 1000, 100,
                    help="Primeros 2 GB gratuitos", key=f"{env}_codeartifact_storage")
                codeartifact_requests = st.number_input(
                    f"{env} - Solicitudes/mes", 0, 10000000,
                    25000 if env == "Producción" else (
                    100000 if env == "Desarrollo (DEV)" else (
                    25000 if env == "Pruebas (UAT)" else 50000)),
                    help="Primeras 100,000 solicitudes gratuitas", key=f"{env}_codeartifact_requests")
                codeartifact_intra = st.number_input(
                    f"{env} - Transferencia Intra (GB)", 0.0, 10000.0, 0.0,
                    help="0.01 USD/GB entrada + 0.01 USD/GB salida", key=f"{env}_codeartifact_intra")
                codeartifact_outbound = st.number_input(
                    f"{env} - Transferencia Saliente (GB)", 0.0, 10000.0, 100.0,
                    help="0.09 USD/GB a Internet", key=f"{env}_codeartifact_outbound")
            environment_inputs[env] = {
                'codepipeline_v1': codepipeline_v1,
                'codepipeline_v2': codepipeline_v2,
                'codebuild_builds': codebuild_builds,
                'codebuild_duration': codebuild_duration,
                'codeartifact_storage': codeartifact_storage,
                'codeartifact_requests': codeartifact_requests,
                'codeartifact_intra': codeartifact_intra,
                'codeartifact_outbound': codeartifact_outbound,
            }

# --- CÁLCULO DE COSTOS ---
environment_costs = {}
for env, inputs in environment_inputs.items():
    environment_costs[env] = calculate_costs_custom(inputs, env)

if selected_environments:
    st.header("Comparativa de Costos Seleccionados")

    # --- MÉTRICAS CLAVE ---
    st.subheader("Métricas Clave Comparativas")
    metrics_data = {}
    total_sum_annual = 0.0
    for env in selected_environments:
        if env in environment_costs:
            annual_services = ['GitLab', 'CheckMarx', 'Sonarqube']
            annual_cost = sum(environment_costs[env][s] for s in annual_services if s in environment_costs[env])
            monthly_cost = sum(v for k, v in environment_costs[env].items() if k not in annual_services)
            total_cost_month = monthly_cost
            total_cost_annual = annual_cost + (monthly_cost * 12)
            metrics_data[env] = {
                "Costo Total Mensual": f"${total_cost_month:,.2f} USD",
                "Costo Total Anual":  f"${total_cost_annual:,.2f} USD"
            }
            total_sum_annual += total_cost_annual

    metrics_df = pd.DataFrame(metrics_data).T
    metrics_df.loc["TOTAL"] = [
        "",  # No aplica mensual para el total
        f"${total_sum_annual:,.2f} USD"
    ]
    st.dataframe(metrics_df.style.highlight_max(axis=0, color='#FFD700'), height=200)
    st.markdown("---")

    # --- DESGLOSE DETALLADO ---
    st.subheader("Desglose Detallado Comparativo")
    detailed_data = {}
    totals = {env: 0.0 for env in selected_environments}
    all_services = set()
    for env in selected_environments:
        all_services.update(environment_costs[env].keys())
    for service in sorted(all_services):
        detailed_data[service] = {}
        for env in selected_environments:
            cost = environment_costs[env].get(service, None)
            detailed_data[service][env] = f"${cost:,.2f}" if cost is not None else "-"
    for env in selected_environments:
        annual_services = ['GitLab', 'CheckMarx', 'Sonarqube']
        annual_cost = sum(environment_costs[env][s] for s in annual_services if s in environment_costs[env])
        monthly_cost = sum(v for k, v in environment_costs[env].items() if k not in annual_services)
        totals[env] = annual_cost + (monthly_cost * 12)
    detailed_data['Total'] = {env: f"${totals[env]:,.2f}" for env in selected_environments}
    detailed_data['Total']["TOTAL"] = f"${sum(totals.values()):,.2f}"
    detailed_df = pd.DataFrame(detailed_data).T
    st.dataframe(detailed_df, height=350)
    st.markdown("---")

    # --- VISUALIZACIONES MEJORADAS ---
    st.subheader("Visualizaciones Comparativas")
    cols = st.columns(len(selected_environments))
    for i, env in enumerate(selected_environments):
        with cols[i]:
            st.markdown(f"#### {env}")
            df_viz = pd.DataFrame(list(environment_costs[env].items()), columns=['Servicio', 'Costo'])
            fig_bar = px.bar(
                df_viz, x='Servicio', y='Costo', color='Servicio',
                title="Distribución de Costos",
                text_auto='.2s',
                color_discrete_sequence=px.colors.qualitative.Pastel,
                hover_data={'Costo':':$.2f'}
            )
            st.plotly_chart(fig_bar, use_container_width=True, key=f"{env}_bar")
            fig_pie = px.pie(
                df_viz, names='Servicio', values='Costo',
                title="Distribución Porcentual", hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True, key=f"{env}_pie")
    st.markdown("---")

    # --- INSIGHTS Y RECOMENDACIONES ---
    max_env = max(totals, key=totals.get)
    st.success(f"💡 El entorno con mayor costo anual es **{max_env}** (${totals[max_env]:,.2f} USD).")
    # Recomendación automática simple
    mayor_servicio = None
    mayor_valor = 0
    for servicio in all_services:
        suma = sum(environment_costs[env].get(servicio, 0) for env in selected_environments)
        if suma > mayor_valor:
            mayor_valor = suma
            mayor_servicio = servicio
    st.info(f"🔎 El servicio con mayor impacto en el costo total es **{mayor_servicio}**. Considera optimizar su uso para reducir gastos.")

else:
    st.info("Por favor, selecciona al menos un entorno para comparar.")

# --- DETALLES DE CÁLCULO EN EXPANDER ---
with st.expander("🧮 Detalles de Cálculo"):
    st.markdown("""
    **GitLab:**  
    Valor fijo anual para Producción: 73350

    **CheckMarx:**  
    Valor fijo anual para Producción: 26265.5

    **Sonarqube:**  
    Valor fijo anual para Producción: 32643.78

    **CodePipeline:**  
    V1 Costo = max(Pipelines - 1, 0) × 1.00 USD  
    V2 Costo = max(Minutos - 100, 0) × 0.002 USD

    **CodeBuild:**  
    Costo = Builds × Duración × 0.00002 USD

    **CodeArtifact:**  
    Almacenamiento = max(GB - 2, 0) × 0.05 USD  
    Solicitudes = max(Requests - 100,000, 0) × 0.000005 USD  
    Transferencia = (Intra × 0.02 USD) + (Outbound × 0.09 USD)
    """)

# --- PIE DE PÁGINA PROFESIONAL ---
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:gray; font-size:14px;'>
Desarrollado por tu equipo | Última actualización: Junio 2025<br>
Contacto: <a href='mailto:soporte@tuempresa.com'>soporte@tuempresa.com</a><br>
_* Los precios están basados en la región US East (N. Virginia)_
</div>
""", unsafe_allow_html=True)