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
        costs['GitLab'] = 73750  # $9,000
        costs['CheckMarx'] = 26265.5
        costs['Sonarqube'] = 32643.78
        costs['CodeArtifact'] = 950 * 12  # $9,000 anual fijo SOLO en Producción

    # CodePipeline v2 (mensual)
    pipelines = inputs['codepipeline_pipelines']
    executions_per_day = inputs['codepipeline_executions_per_day']
    minutes_per_execution = inputs['codepipeline_minutes_per_execution']
    transitions_per_execution = inputs['codepipeline_transitions_per_execution']

    total_executions = pipelines * executions_per_day * 30
    total_transitions = total_executions * transitions_per_execution
    total_minutes = total_executions * minutes_per_execution

    cost_transitions = total_transitions * 0.002
    cost_minutes = max(total_minutes - 100, 0) * 0.002  # 100 mins gratis
    codepipeline_v2_monthly = cost_transitions + cost_minutes
    costs['CodePipeline'] = codepipeline_v2_monthly

    # CodeBuild (mensual)
    builds = inputs['codebuild_builds']
    duration = inputs['codebuild_duration']
    duration_sec = duration * 60
    codebuild_monthly = builds * duration_sec * 0.00002
    costs['CodeBuild'] = codebuild_monthly

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
with st.expander("🛈 Guía rápida de uso..."):
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
            "Producción_codepipeline_pipelines": 300,
            "Producción_codepipeline_executions_per_day": 10,
            "Producción_codepipeline_minutes_per_execution": 5,
            "Producción_codepipeline_transitions_per_execution": 2,
            "Producción_codebuild_builds": 25000,
            "Producción_codebuild_duration": 5,
            "Producción_codeartifact_storage": 100,
            "Producción_codeartifact_requests": 25000,
            "Producción_codeartifact_intra": 0.0,
            "Producción_codeartifact_outbound": 100.0,
            "Desarrollo (DEV)_codepipeline_pipelines": 300,
            "Desarrollo (DEV)_codepipeline_executions_per_day": 10,
            "Desarrollo (DEV)_codepipeline_minutes_per_execution": 5,
            "Desarrollo (DEV)_codepipeline_transitions_per_execution": 2,
            "Desarrollo (DEV)_codebuild_builds": 100000,
            "Desarrollo (DEV)_codebuild_duration": 5,
            "Desarrollo (DEV)_codeartifact_storage": 100,
            "Desarrollo (DEV)_codeartifact_requests": 100000,
            "Desarrollo (DEV)_codeartifact_intra": 0.0,
            "Desarrollo (DEV)_codeartifact_outbound": 100.0,
            "Pruebas (UAT)_codepipeline_pipelines": 300,
            "Pruebas (UAT)_codepipeline_executions_per_day": 10,
            "Pruebas (UAT)_codepipeline_minutes_per_execution": 5,
            "Pruebas (UAT)_codepipeline_transitions_per_execution": 2,
            "Pruebas (UAT)_codebuild_builds": 25000,
            "Pruebas (UAT)_codebuild_duration": 5,
            "Pruebas (UAT)_codeartifact_storage": 100,
            "Pruebas (UAT)_codeartifact_requests": 25000,
            "Pruebas (UAT)_codeartifact_intra": 0.0,
            "Pruebas (UAT)_codeartifact_outbound": 100.0,
            "QA_codepipeline_pipelines": 300,
            "QA_codepipeline_executions_per_day": 10,
            "QA_codepipeline_minutes_per_execution": 5,
            "QA_codepipeline_transitions_per_execution": 2,
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
            tab1, tab2, tab3 = st.tabs(["CodePipeline v2", "CodeBuild", "CodeArtifact"])
            with tab1:
                st.subheader("CodePipeline v2")
                pipelines = st.number_input(
                    f"{env} - Pipelines activos", 1, 1000, 300,
                    help="Cantidad de pipelines activos en CodePipeline v2.",
                    key=f"{env}_codepipeline_pipelines")
                executions_per_day = st.number_input(
                    f"{env} - Ejecuciones por día (por pipeline)", 1, 1000, 10,
                    help="Ejecuciones diarias por pipeline.",
                    key=f"{env}_codepipeline_executions_per_day")
                minutes_per_execution = st.number_input(
                    f"{env} - Minutos por ejecución", 1, 60, 5,
                    help="Duración promedio de cada ejecución.",
                    key=f"{env}_codepipeline_minutes_per_execution")
                transitions_per_execution = st.number_input(
                    f"{env} - Transiciones por ejecución", 1, 10, 2,
                    help="Transiciones por ejecución (Source → Deploy).",
                    key=f"{env}_codepipeline_transitions_per_execution")
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
                'codepipeline_pipelines': pipelines,
                'codepipeline_executions_per_day': executions_per_day,
                'codepipeline_minutes_per_execution': minutes_per_execution,
                'codepipeline_transitions_per_execution': transitions_per_execution,
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
            annual_services = ['GitLab', 'CheckMarx', 'Sonarqube', 'CodeArtifact']
            annual_cost = sum(environment_costs[env][s] for s in annual_services if s in environment_costs[env])
            monthly_cost = sum(v for k, v in environment_costs[env].items() if k not in annual_services)
            total_cost_annual = annual_cost + (monthly_cost * 12)
            # Solo Producción: mostrar solo el anual y el valor fijo solicitado
            if env == "Producción":
                metrics_data[env] = {
                    "Costo Total Anual":  "$160,976.88 USD"
                }
                total_sum_annual += 160976.88
            else:
                metrics_data[env] = {
                    "Costo Total Mensual": f"${monthly_cost:,.2f} USD",
                    "Costo Total Anual":  f"${total_cost_annual:,.2f} USD"
                }
                total_sum_annual += total_cost_annual

    # Ajustar columnas según si Producción está seleccionada
    if "Producción" in metrics_data:
        metrics_df = pd.DataFrame(metrics_data).T
        # Si Producción es la única seleccionada, solo muestra el anual
        if len(metrics_df.columns) == 1:
            metrics_df = metrics_df[["Costo Total Anual"]]
    else:
        metrics_df = pd.DataFrame(metrics_data).T

    # Ajustar la fila TOTAL para que coincida con el número de columnas
    total_row = []
    for col in metrics_df.columns:
        if col == "Costo Total Anual":
            total_row.append(f"${total_sum_annual:,.2f} USD")
        else:
            total_row.append("")

    metrics_df.loc["TOTAL"] = total_row

    st.dataframe(metrics_df, height=220)
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
            # Mostrar CodeArtifact solo en Producción
            if service == "CodeArtifact" and env != "Producción":
                detailed_data[service][env] = "-"
            else:
                cost = environment_costs[env].get(service, None)
                detailed_data[service][env] = f"${cost:,.2f}" if cost is not None else "-"
    for env in selected_environments:
        annual_services = ['GitLab', 'CheckMarx', 'Sonarqube', 'CodeArtifact']
        annual_cost = sum(environment_costs[env][s] for s in annual_services if s in environment_costs[env])
        monthly_cost = sum(v for k, v in environment_costs[env].items() if k not in annual_services)
        # Producción: mostrar el total anual, los demás ambientes mostrar solo la suma mensual
        if env == "Producción":
            totals[env] = annual_cost + (monthly_cost * 12)
        else:
            totals[env] = annual_cost + monthly_cost
    detailed_data['Total'] = {env: f"${totals[env]:,.2f}" for env in selected_environments}
    detailed_df = pd.DataFrame(detailed_data).T

    # Agregar fila de sumatoria de ambientes debajo del total
    sum_row = {env: "" for env in selected_environments}
    sum_row["TOTAL"] = f"Sumatoria Ambientes: ${sum(totals.values()):,.2f} USD"
    detailed_df.loc[""] = sum_row

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
    
    Costo anual fijo:  = **$73,750 USD**

    **CheckMarx:**  
    Valor fijo anual para Producción: 26265.5

    **Sonarqube:**  
    Valor fijo anual para Producción: 32643.78

    **CodePipeline v2:**  
    - **Ejecuciones por mes:** Pipelines × Ejecuciones/día × 30  
    - **Transiciones por mes:** Ejecuciones × Transiciones/ejecución  
    - **Minutos por mes:** Ejecuciones × Minutos/ejecución  
    - **Costo transiciones:** Transiciones × $0.002 USD  
    - **Costo minutos:** max(Minutos - 100, 0) × $0.002 USD  
    - **Total mensual:** Costo transiciones + Costo minutos  
    - **Total anual:** Total mensual × 12

    **CodeBuild:**  
    Costo = Builds × Duración × 0.00002 USD

    **CodeArtifact:**  
    Costo mensual: $750 USD  
    Costo anual: $950 × 12 = **$11,400 USD**  
    _(Nota: Para efectos de este cálculo, CodeArtifact se considera un costo fijo anual de $11,400 USD)_
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