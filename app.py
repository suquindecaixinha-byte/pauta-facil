import streamlit as st
import feedparser
import requests
import re
import urllib3
from datetime import datetime
import pytz

# --- CONFIGURAÇÃO ---
st.set_page_config(
    page_title="Pauta Fácil RSS",
    layout="wide",
    page_icon="📡",
    initial_sidebar_state="expanded"
)

# Desabilitar avisos de segurança (Necessário para PCDF)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# HEADERS (Disfarce de Navegador)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/'
}

# --- FUNÇÃO DE CARREGAMENTO BLINDADA ---
@st.cache_data(ttl=300) # Atualiza a cada 5 min
def carregar_rss(url):
    try:
        # O Requests baixa o conteúdo "na força bruta", ignorando SSL e bloqueios
        resp = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if resp.status_code == 200:
            # O feedparser apenas lê o que o requests baixou
            return feedparser.parse(resp.content)
    except:
        pass
    # Retorna vazio se der erro
    return feedparser.FeedParserDict(entries=[])

# --- UTILITÁRIOS ---
def hora_atual():
    return datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%H:%M')

def limpar_html(texto):
    """Remove tags HTML do resumo"""
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
    
    # Se estiver vazio
    if not feed.entries:
        st.markdown(f"""
        <div style="background:white; padding:15px; border-radius:10px; border-left:5px solid #ccc; opacity:0.7; margin-bottom:15px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
            <strong>{icone} {nome_fonte}</strong><br>
            <span style="font-size:12px; color:#666">Sem novidades ou conexão instável.</span>
        </div>
        """, unsafe_allow_html=True)
        return

    # Pega a notícia mais recente
    post = feed.entries[0]
    titulo = post.title
    link = post.link
    
    # Tenta pegar resumo
    resumo = ""
    if 'summary' in post: resumo = post.summary
    elif 'description' in post: resumo = post.description
    
    resumo_limpo = limpar_html(resumo)[:160] # Limita caracteres
    if len(resumo_limpo) > 150: resumo_limpo += "..."
    
    local = detectar_local(titulo + " " + resumo_limpo)
    
    tags_html = ""
    if local: tags_html = f"<span style='background:#e3f2fd; color:#1565c0; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:bold;'>📍 {local}</span>"
    
    st.markdown(f"""
    <div style="background:white; padding:15px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.08); margin-bottom:15px; border-left:5px solid {cor_borda}; transition: transform 0.2s;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-weight:bold; color:{cor_borda}; font-size:12px; text-transform:uppercase; font-family:sans-serif;">{icone} {nome_fonte}</span>
            {tags_html}
        </div>
        <div style="font-size:15px; font-weight:700; margin-bottom:8px; line-height:1.3; color:#222; font-family:sans-serif;">{titulo}</div>
        <div style="font-size:12px; color:#555; margin-bottom:12px; line-height:1.4; font-family:sans-serif;">{resumo_limpo}</div>
        <div style="text-align:right;">
            <a href="{link}" target="_blank" style="text-decoration:none; color:#333; font-weight:800; font-size:11px; background:#f5f5f5; padding:6px 12px; border-radius:4px;">LER MATÉRIA ➜</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("📡 Pauta Fácil")
    st.caption("Monitoramento RSS Híbrido")
    if st.button("🔄 ATUALIZAR AGORA", type="primary", use_container_width=True): 
        st.cache_data.clear()
        st.rerun()
    st.write("---")
    st.markdown(f"**Brasília: {hora_atual()}**")

# --- LAYOUT PRINCIPAL ---
st.markdown("### 🚨 Plantão Policial")
c1, c2, c3 = st.columns(3)

with c1:
    processar_feed("PCDF", "https://www.pcdf.df.gov.br/noticias?format=feed&type=rss", "#000", "🕵️‍♂️")
with c2:
    # Metrópoles DF (Cobre PMDF/Bombeiros)
    processar_feed("METRÓPOLES", "https://www.metropoles.com/distrito-federal/feed", "#007bff", "📱")
with c3:
    # Jornal Opção (Entorno) ou PCGO
    processar_feed("PCGO", "https://policiacivil.go.gov.br/feed", "#1565c0", "🔫")

st.markdown("---")
st.markdown("### 🏛️ Poder & Serviços")
c4, c5, c6, c7 = st.columns(4)

with c4:
    processar_feed("GDF", "https://www.agenciabrasilia.df.gov.br/feed/", "#009688", "📢")
with c5:
    processar_feed("MPDFT", "https://www.mpdft.mp.br/portal/index.php/comunicacao-menu/noticias?format=feed&type=rss", "#b71c1c", "⚖️")
with c6:
    processar_feed("SENADO", "https://www12.senado.leg.br/noticias/feed/metadados/agencia", "#673ab7", "🏛️")
with c7:
    processar_feed("BOMBEIROS", "https://www.cbm.df.gov.br/feed/", "#fbc02d", "🔥")
