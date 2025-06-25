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

st.set_page_config(page_title="AWS Cost Calculator (Custom)", layout="wide")
st.title("Calculadora de Costos AWS (Custom) 📊")
st.markdown("---")

# --- Selección de entornos para comparar ---
st.header("🔍 Comparación de Entornos")
environments = ["Producción", "Desarrollo (DEV)", "Pruebas (UAT)", "QA"]
selected_environments = st.multiselect(
    "Seleccionar Entornos a Comparar",
    environments,
    default=environments,
    help="Selecciona los entornos que deseas comparar"
)
st.markdown("---")

# Sidebar para configuraciones de entornos
with st.sidebar:
    st.header("⚙️ Configuración de Entornos")
    environment_inputs = {}
    for env in environments:
        with st.expander(f"Configuración {env}"):
            environment_inputs[env] = {
                'codepipeline_v1': st.number_input(
                    f"{env} - CodePipeline V1 - Pipelines activos", 0, 50000, 0,
                    help="Primer pipeline gratuito", key=f"{env}_codepipeline_v1"),
                'codepipeline_v2': st.number_input(
                    f"{env} - CodePipeline V2 - Minutos ejecución", 0, 100000,
                    25000 if env == "Producción" else (
                    100000 if env == "Desarrollo (DEV)" else (
                    25000 if env == "Pruebas (UAT)" else 50000)),
                    help="Primeros 100 minutos gratuitos", key=f"{env}_codepipeline_v2"),
                'codebuild_builds': st.number_input(
                    f"{env} - CodeBuild - Builds/mes", 0, 10000000,
                    25000 if env == "Producción" else (
                    100000 if env == "Desarrollo (DEV)" else (
                    25000 if env == "Pruebas (UAT)" else 50000)),
                    help="Número total de builds mensuales", key=f"{env}_codebuild_builds"),
                'codebuild_duration': st.number_input(
                    f"{env} - CodeBuild - Duración (min)", 0, 600, 5,
                    help="Duración promedio por build", key=f"{env}_codebuild_duration"),
                'codeartifact_storage': st.number_input(
                    f"{env} - CodeArtifact - Almacenamiento (GB)", 0, 1000, 100,
                    help="Primeros 2 GB gratuitos", key=f"{env}_codeartifact_storage"),
                'codeartifact_requests': st.number_input(
                    f"{env} - CodeArtifact - Solicitudes/mes", 0, 10000000,
                    25000 if env == "Producción" else (
                    100000 if env == "Desarrollo (DEV)" else (
                    25000 if env == "Pruebas (UAT)" else 50000)),
                    help="Primeras 100,000 solicitudes gratuitas", key=f"{env}_codeartifact_requests"),
                'codeartifact_intra': st.number_input(
                    f"{env} - Transferencia Intra (GB)", 0.0, 10000.0, 0.0,
                    help="0.01 USD/GB entrada + 0.01 USD/GB salida", key=f"{env}_codeartifact_intra"),
                'codeartifact_outbound': st.number_input(
                    f"{env} - Transferencia Saliente (GB)", 0.0, 10000.0, 100.0,
                    help="0.09 USD/GB a Internet", key=f"{env}_codeartifact_outbound"),
            }

# Calcular costos para cada entorno
environment_costs = {}
for env, inputs in environment_inputs.items():
    environment_costs[env] = calculate_costs_custom(inputs, env)

if selected_environments:
    st.header("Comparativa de Costos Seleccionados")

    # --- Métricas Clave ---
    st.subheader("Métricas Clave Comparativas")
    metrics_data = {}
    total_sum_annual = 0.0  # Para la suma total de todos los ambientes
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

    # Añadir fila de sumatoria total anual
    metrics_df = pd.DataFrame(metrics_data).T
    metrics_df.loc["TOTAL"] = [
        "",  # No aplica mensual para el total
        f"${total_sum_annual:,.2f} USD"
    ]
    st.dataframe(metrics_df)
    st.markdown("---")

    # --- Desglose Detallado con Totales ---
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
    # Agregar fila de totales (mensual + anual correctamente)
    for env in selected_environments:
        annual_services = ['GitLab', 'CheckMarx', 'Sonarqube']
        annual_cost = sum(environment_costs[env][s] for s in annual_services if s in environment_costs[env])
        monthly_cost = sum(v for k, v in environment_costs[env].items() if k not in annual_services)
        totals[env] = annual_cost + (monthly_cost * 12)
    # Añadir columna de sumatoria total anual
    detailed_data['Total'] = {env: f"${totals[env]:,.2f}" for env in selected_environments}
    detailed_data['Total']["TOTAL"] = f"${sum(totals.values()):,.2f}"
    detailed_df = pd.DataFrame(detailed_data).T
    st.dataframe(detailed_df)
    st.markdown("---")

    # --- Visualizaciones ---
    st.subheader("Visualizaciones Comparativas")
    cols = st.columns(len(selected_environments))
    for i, env in enumerate(selected_environments):
        with cols[i]:
            st.subheader(env)
            df_viz = pd.DataFrame(list(environment_costs[env].items()), columns=['Servicio', 'Costo'])
            fig_bar = px.bar(df_viz, x='Servicio', y='Costo', color='Servicio',
                            title="Distribución de Costos", text_auto='.2s')
            st.plotly_chart(fig_bar, use_container_width=True, key=f"{env}_bar")
            fig_pie = px.pie(df_viz, names='Servicio', values='Costo',
                            title="Distribución Porcentual", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True, key=f"{env}_pie")
    st.markdown("---")
else:
    st.info("Por favor, selecciona al menos un entorno para comparar.")

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

st.markdown("---")
st.markdown("_* Los precios están basados en la región US East (N. Virginia)_")