import streamlit as st
import feedparser
import re
from datetime import datetime
import pytz

# --- CONFIGURAÇÃO ---
st.set_page_config(
    page_title="Pauta Fácil RSS",
    layout="wide",
    page_icon="📡",
    initial_sidebar_state="expanded"
)

# Cache para não recarregar o RSS toda hora (performance)
@st.cache_data(ttl=300) # Atualiza a cada 5 min
def carregar_rss(url):
    return feedparser.parse(url)

# --- UTILITÁRIOS ---
def hora_atual():
    return datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M')

def limpar_html(texto):
    """Remove tags HTML do resumo do RSS para ficar limpo"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', texto)

# --- DETECTOR DE LOCAL ---
LOCAIS_ALVO = ["Ceilândia", "Taguatinga", "Samambaia", "Gama", "Santa Maria", "Planaltina", "Recanto das Emas", "São Sebastião", "Brazlândia", "Sol Nascente", "Pôr do Sol", "Paranoá", "Núcleo Bandeirante", "Guará", "Sobradinho", "Jardim Botânico", "Lago Norte", "Lago Sul", "Águas Claras", "Riacho Fundo", "Candangolândia", "Vicente Pires", "Varjão", "Fercal", "Itapoã", "Sia", "Cruzeiro", "Sudoeste", "Octogonal", "Luziânia", "Valparaíso", "Águas Lindas", "Novo Gama", "Cidade Ocidental", "Formosa", "Santo Antônio", "Padre Bernardo", "Alexânia", "Planaltina de Goiás", "Esplanada", "Buriti", "Câmara Legislativa"]

def detectar_local(texto):
    for l in LOCAIS_ALVO:
        if re.search(r'\b' + re.escape(l) + r'\b', texto, re.IGNORECASE):
            return l
    return None

# --- PROCESSADOR DE FEED ---
def processar_feed(nome_fonte, url_rss, cor_borda, icone):
    feed = carregar_rss(url_rss)
    
    # Se o feed estiver vazio ou der erro (Bozo no bloqueio)
    if not feed.entries:
        st.markdown(f"""
        <div style="background:#eee; padding:15px; border-radius:10px; border-left:5px solid {cor_borda}; opacity:0.6; margin-bottom:15px;">
            <strong>{icone} {nome_fonte}</strong><br>
            <span style="font-size:12px">Sem conexão ou bloqueado.</span>
        </div>
        """, unsafe_allow_html=True)
        return

    # Pega a notícia mais recente (a primeira da lista)
    post = feed.entries[0]
    titulo = post.title
    link = post.link
    
    # Tenta pegar o resumo (description ou summary)
    resumo = ""
    if 'summary' in post: resumo = post.summary
    elif 'description' in post: resumo = post.description
    
    # Limpeza
    resumo_limpo = limpar_html(resumo)[:150] + "..." # Pega só os primeiros caracteres
    local = detectar_local(titulo + " " + resumo_limpo)
    
    # Monta o HTML
    tags_html = ""
    if local: tags_html = f"<span style='background:#e3f2fd; color:#1565c0; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;'>📍 {local}</span>"
    
    st.markdown(f"""
    <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1); margin-bottom:15px; border-left:5px solid {cor_borda}; transition: transform 0.2s;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:bold; color:{cor_borda}; font-size:12px; text-transform:uppercase;">{icone} {nome_fonte}</span>
            {tags_html}
        </div>
        <div style="font-size:15px; font-weight:bold; margin:10px 0; line-height:1.4; color:#333;">{titulo}</div>
        <div style="font-size:12px; color:#666; margin-bottom:10px;">{resumo_limpo}</div>
        <div style="text-align:right;">
            <a href="{link}" target="_blank" style="text-decoration:none; color:#007bff; font-weight:bold; font-size:11px;">LER MATÉRIA ➜</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("📡 Pauta Fácil RSS")
    st.markdown("Monitoramento via Feeds")
    if st.button("🔄 ATUALIZAR", type="primary"): 
        st.cache_data.clear()
        st.rerun()
    st.info(f"Brasília: {hora_atual()}")

# --- LAYOUT PRINCIPAL ---
st.markdown("### 🚨 Plantão Policial")
c1, c2, c3 = st.columns(3)

with c1:
    # PCDF (Joomla RSS)
    processar_feed("PCDF", "https://www.pcdf.df.gov.br/noticias?format=feed&type=rss", "#000", "🕵️‍♂️")

with c2:
    # Metrópoles DF (WordPress RSS) - Usamos no lugar da PMDF que não tem RSS bom
    processar_feed("METRÓPOLES", "https://www.metropoles.com/distrito-federal/feed", "#007bff", "📱")

with c3:
    # PCGO (WordPress RSS)
    processar_feed("PCGO", "https://policiacivil.go.gov.br/feed", "#1565c0", "🔫")

st.markdown("---")
st.markdown("### 🏛️ Poder & Serviços")
c4, c5, c6, c7 = st.columns(4)

with c4:
    # Agência Brasília (RSS)
    processar_feed("GDF", "https://www.agenciabrasilia.df.gov.br/feed/", "#009688", "📢")

with c5:
    # MPDFT (RSS)
    processar_feed("MPDFT", "https://www.mpdft.mp.br/portal/index.php/comunicacao-menu/noticias?format=feed&type=rss", "#b71c1c", "⚖️")

with c6:
    # Senado/Câmara (Exemplo - CLDF não tem RSS fácil, usando Senado como teste)
    processar_feed("SENADO", "https://www12.senado.leg.br/noticias/feed/metadados/agencia", "#673ab7", "🏛️")

with c7:
    # Bombeiros (CBMDF - WordPress RSS)
    processar_feed("BOMBEIROS", "https://www.cbm.df.gov.br/feed/", "#fbc02d", "🔥")
