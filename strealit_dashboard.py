import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Data Quality Guard - Accidents 2024",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLE CSS CUSTOM ---
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: bold; color: #1E3A8A; margin-bottom: 5px; }
    .subtitle { font-size: 1.1rem; color: #4B5563; margin-bottom: 25px; }
    .metric-card { background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 5px solid #3B82F6; }
    </style>
""", unsafe_allow_html=True)

# --- DONNÉES DE SÉCURITÉ (PROFILAGE DU NOTEBOOK) ---
NOTEBOOK_STATS = {
    'caract-2024.csv': {
        'rows': 54402, 'cols': 15, 'dup_total': 0, 'dup_keys': 0, 'key_cols': ['Num_Acc'],
        'missing': {'col': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6, 2310, 0, 0], 'pct': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.01, 4.25, 0.0, 0.0], 'cols': ['Num_Acc', 'jour', 'mois', 'an', 'hrmn', 'lum', 'dep', 'com', 'agg', 'int', 'atm', 'col', 'adr', 'lat', 'long']}
    },
    'lieux-2024.csv': {
        'rows': 70248, 'cols': 18, 'dup_total': 2, 'dup_keys': 1831, 'key_cols': ['Num_Acc', 'voie'],
        'missing': {'col': [0, 0, 13331, 16272, 64332, 4354, 4178, 3832, 50, 27364, 27432, 40, 70215, 48646, 38, 812, 38, 3630], 'pct': [0.0, 0.0, 18.98, 23.16, 91.58, 6.2, 5.95, 5.45, 0.07, 38.95, 39.05, 0.06, 99.95, 69.25, 0.05, 1.16, 0.05, 5.17], 'cols': ['Num_Acc', 'catr', 'voie', 'v1', 'v2', 'circ', 'nbv', 'vosp', 'prof', 'pr', 'pr1', 'plan', 'lartpc', 'larrout', 'surf', 'infra', 'situ', 'vma']}
    },
    'usagers-2024.csv': {
        'rows': 125187, 'cols': 16, 'dup_total': 0, 'dup_keys': 0, 'key_cols': ['Num_Acc', 'id_usager'],
        'missing': {'col': [0, 0, 0, 0, 3, 0, 0, 2395, 2579, 2626, 2103, 53813, 113133, 61771, 61726, 114932], 'pct': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.91, 2.06, 2.1, 1.68, 42.99, 90.37, 49.34, 49.31, 91.81], 'cols': ['Num_Acc', 'id_usager', 'id_vehicule', 'num_veh', 'place', 'catu', 'grav', 'sexe', 'an_nais', 'trajet', 'secu1', 'secu2', 'secu3', 'locp', 'actp', 'etatp']}
    },
    'vehicules-2024.csv': {
        'rows': 92678, 'cols': 11, 'dup_total': 0, 'dup_keys': 0, 'key_cols': ['Num_Acc', 'id_vehicule'],
        'missing': {'col': [0, 0, 0, 68, 1, 27, 30, 44, 27, 192, 91729], 'pct': [0.0, 0.0, 0.0, 0.07, 0.0, 0.03, 0.03, 0.05, 0.03, 0.21, 98.98], 'cols': ['Num_Acc', 'id_vehicule', 'num_veh', 'senc', 'catv', 'obs', 'obsm', 'choc', 'manv', 'motor', 'occutc']}
    }
}

# --- CHARGEMENT INTELLIGENT DES DONNÉES ---
@st.cache_data
def load_dataset(filename):
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename, sep=';', quotechar='"', encoding='utf-8', dtype=str)
            df = df.replace({'': pd.NA, 'N/A': pd.NA, ' -1': pd.NA, ' -1 ': pd.NA})
            return df, True
        except Exception:
            return None, False
    return None, False


def detect_numeric_columns(df):
    numeric = []
    id_columns = {'num_acc', 'id_usager', 'id_vehicule', 'num_veh'}
    for col in df.columns:
        if col.lower() in id_columns:
            continue
        non_null = df[col].dropna().astype(str).str.replace(',', '.', regex=False).str.strip()
        if len(non_null) == 0:
            continue
        coerced = pd.to_numeric(non_null, errors='coerce')
        if coerced.notna().all():
            numeric.append(col)
    return numeric


def detect_categorical_columns(df, max_unique=15):
    categorical = []
    for col in df.columns:
        non_null = df[col].dropna().astype(str)
        unique_count = non_null.nunique()
        if 1 < unique_count <= max_unique:
            categorical.append(col)
    return categorical

# --- INTERFACE PRINCIPALE ---
st.markdown('<div class="main-title">Data Quality Summary</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Analyse de l\'intégrité des datasets d\'accidents routiers 2024</div>', unsafe_allow_html=True)

# Configuration Sidebar
st.sidebar.header("Configuration des sources")
selected_file = st.sidebar.selectbox("Sélectionner le fichier à auditer :", list(NOTEBOOK_STATS.keys()))

df, is_live = load_dataset(selected_file)
stats = NOTEBOOK_STATS[selected_file]

if is_live:
    st.sidebar.success("Mode dynamique : données réelles chargées")
    row_count, col_count = df.shape[0], df.shape[1]
else:
    st.sidebar.info("Mode rapport : utilisation des métriques pré-calculées")
    row_count, col_count = stats['rows'], stats['cols']

# --- KPI BLOCKS ---
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    st.metric("Nombre de Lignes", f"{row_count:,}")
with col_kpi2:
    st.metric("Nombre de Colonnes", col_count)
with col_kpi3:
    st.metric("Doublons Totaux", stats['dup_total'])
with col_kpi4:
    st.metric("Doublons Clés Logiques", stats['dup_keys'])

st.markdown("---")

# --- ONGLETS DE PROFILAGE ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Clés", 
    "Doublons", 
    "Valeurs manquantes", 
    "Graphes", 
    "Imputation"
])

# --- TAB 1 : CLÉS ---
with tab1:
    st.subheader("Vérification de la clé primaire")
    st.write(f"Clé de jointure attendue : `{' + '.join(stats['key_cols'])}`")
    
    if stats['dup_keys'] == 0:
        st.success("Intégrité de la clé primaire validée. Aucune collision de clé détectée.")
    else:
        st.error(f"Violation d'unicité : {stats['dup_keys']} occurrence(s) sur la clé.")
        st.warning("Action recommandée : nettoyer les entrées conflictuelles avant toute jointure.")

# --- TAB 2 : DOUBLONS ---
with tab2:
    st.subheader("Gestion des doublons")
    
    col_dup1, col_dup2 = st.columns([1, 2])
    with col_dup1:
        st.markdown(f"""
        **Diagnostic :**
        * Doublons strictes (lignes identiques) : `{stats['dup_total']}`
        * Doublons sur clés logiques : `{stats['dup_keys']}`
        """)
    with col_dup2:
        st.info("""
        Règles recommandées :
        1. Supprimer les doublons totaux avec `.drop_duplicates()`.
        2. Pour les doublons de clés, vérifier s'il s'agit de plusieurs voies ou véhicules pour un même accident.
        """)

# --- TAB 3 : VALEURS MANQUANTES ---
with tab3:
    st.subheader("Gestion des Valeurs Nulles & Manquantes")
    
    # Construction du DataFrame des valeurs manquantes
    if is_live:
        missing_series = df.isna().sum()
        pct_series = (missing_series / len(df) * 100).round(2)
        df_miss_plot = pd.DataFrame({'Colonnes': missing_series.index, 'Manquants': missing_series.values, 'Pourcentage (%)': pct_series.values})
    else:
        df_miss_plot = pd.DataFrame({'Colonnes': stats['missing']['cols'], 'Manquants': stats['missing']['col'], 'Pourcentage (%)': stats['missing']['pct']})
    
    df_miss_plot = df_miss_plot.sort_values(by='Pourcentage (%)', ascending=False)
    
    # Graphique Plotly réclamé
    fig = px.bar(
        df_miss_plot, 
        x='Pourcentage (%)', 
        y='Colonnes', 
        orientation='h',
        title=f"Taux de complétude par variable ({selected_file})",
        color='Pourcentage (%)',
        color_continuous_scale='Reds',
        text='Pourcentage (%)'
    )
    fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # Alertes spécifiques basées sur le fichier choisi
    st.markdown("**Points à vérifier :**")
    if selected_file == 'caract-2024.csv':
        st.markdown("- `adr` est partiel : privilégier `lat`/`long` pour les analyses géographiques.")
    elif selected_file == 'lieux-2024.csv':
        st.markdown("- Colonnes techniques très incomplètes (`lartpc`, `larrout`) : privilégier `vma`, `catr`, `circ`.")
    elif selected_file == 'usagers-2024.csv':
        st.markdown("- `etatp` est peu fiable : utiliser `grav` et `catu` pour l'analyse des victimes.")
    elif selected_file == 'vehicules-2024.csv':
        st.markdown("- `occutc` est presque vide : croiser avec `usagers` pour obtenir le nombre d'occupants.")

# --- TAB 4 : GRAPHIQUES ---
with tab4:
    st.subheader("Graphes de profilage")
    
    if is_live:
        numeric_cols = detect_numeric_columns(df)
        categorical_cols = detect_categorical_columns(df)

        if numeric_cols:
            col = numeric_cols[0]
            fig_num = px.histogram(
                df,
                x=col,
                nbins=30,
                title=f"Distribution de {col}",
                labels={col: col}
            )
            st.plotly_chart(fig_num, use_container_width=True)
        else:
            st.info("Aucune colonne numérique identifiable pour ce dataset.")

        if categorical_cols:
            col = categorical_cols[0]
            counts = df[col].fillna("(manquant)").value_counts().reset_index()
            counts.columns = [col, 'count']
            counts = counts.head(10)
            fig_cat = px.bar(
                counts,
                x='count',
                y=col,
                orientation='h',
                title=f"Top 10 des valeurs de {col}",
                labels={'count': 'Nombre', col: col}
            )
            fig_cat.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Aucune variable catégorielle simple détectée pour ce dataset.")
    else:
        st.info("Chargez le fichier pour afficher les graphiques de profilage.")

# --- TAB 5 : IMPUTATION ---
with tab5:
    st.subheader("Stratégie d'imputation")
    
    st.markdown("""
    L'imputation doit être adaptée aux variables numériques continues et à la nature des données.
    """)
    
    if selected_file == 'usagers-2024.csv':
        st.markdown("Cas d'usage : `an_nais` (Année de naissance - 2.06% de manquants)")
        st.markdown("""
        * Option moyenne : peut introduire une année irréaliste.
        * Option recommandée : imputation par la médiane ou par le mode selon `catu`.
        """)
    elif selected_file == 'lieux-2024.csv':
        st.markdown("Cas d'usage : `vma` (Vitesse maximale autorisée - 5.17% de manquants)")
        st.markdown("""
        * Attention : des valeurs non numériques peuvent exister.
        * Option recommandée : remplacer les manquants par la médiane groupée par `catr`.
        """)
    else:
        st.info("Aucune variable numérique majeure ne nécessite d'imputation immédiate.")