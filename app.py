import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA (WIDE E ÍCONE) ---
st.set_page_config(
    page_title="Radar News DF",
    layout="wide",
    page_icon="📡",
    initial_sidebar_state="expanded"
)

# Desabilitar avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}

# --- ESTILOS CSS PROFISSIONAIS ---
st.markdown("""
    <style>
    /* Fundo geral e fontes */
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; }
    
    /* Card de Notícia */
    .news-card {
        background-color: white;
        border-radius: 12px;
        padding: 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        margin-bottom: 20px;
        border: 1px solid #eee;
        overflow: hidden;
    }
    .news-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    /* Cabeçalho do Card (Colorido) */
    .card-header {
        padding: 10px 15px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Corpo do Card */
    .card-body { padding: 15px; }
    .news-title {
        font-size: 16px;
        font-weight: 700;
        color: #2c3e50;
        line-height: 1.4;
        margin-bottom: 12px;
        min-height: 45px; /* Alinha altura */
    }
    
    /* Tags */
    .tags-container { margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 5px; }
    .tag {
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
    }
    .tag-local { background-color: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb; }
    .tag-video { background-color: #fce4ec; color: #c2185b; border: 1px solid #f8bbd0; }
    .tag-foto { background-color: #f3e5f5; color: #7b1fa2; border: 1px solid #e1bee7; }
    
    /* Botão Link */
    .card-footer {
        padding: 10px 15px;
        background-color: #f8f9fa;
        border-top: 1px solid #eee;
        text-align: right;
    }
    .read-btn {
        text-decoration: none;
        color: #333;
        font-size: 12px;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 5px;
    }
    .read-btn:hover { color: #007bff; }
    
    /* Ajustes Dark Mode (Streamlit nativo cuida do resto, mas ajustamos cards) */
    @media (prefers-color-scheme: dark) {
        .news-card { background-color: #262730; border-color: #333; }
        .card-footer { background-color: #1e1e1e; border-color: #333; }
        .news-title { color: #e0e0e0; }
        .read-btn { color: #ccc; }
    }
    </style>
""", unsafe_allow_html=True)

# --- LOCAIS E FUNÇÕES (MANTIDOS DA VERSÃO ANTERIOR) ---
LOCAIS_ALVO = [
    "Ceilândia", "Taguatinga", "Samambaia", "Gama", "Santa Maria", "Planaltina", "Recanto das Emas",
    "São Sebastião", "Brazlândia", "Sol Nascente", "Pôr do Sol", "Paranoá", "Núcleo Bandeirante",
    "Guará", "Sobradinho", "Jardim Botânico", "Lago Norte", "Lago Sul", "Águas Claras", "Riacho Fundo",
    "Candangolândia", "Vicente Pires", "Varjão", "Fercal", "Itapoã", "Sia", "Cruzeiro", "Sudoeste", "Octogonal",
    "Luziânia", "Valparaíso", "Águas Lindas", "Novo Gama", "Cidade Ocidental", "Formosa", "Santo Antônio do Descoberto",
    "Padre Bernardo", "Alexânia", "Planaltina de Goiás", "Esplanada", "Buriti", "Câmara Legislativa"
]

def investigar_detalhes(url):
    local_encontrado = None
    tem_foto = False
    tem_video = False
    try:
        r = requests.get(url, headers=HEADERS, timeout=8, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            texto = soup.get_text()
            for local in LOCAIS_ALVO:
                if re.search(r'\b' + re.escape(local) + r'\b', texto, re.IGNORECASE):
                    local_encontrado = local
                    break
            if soup.find('iframe') or soup.find('video') or "youtube.com" in str(soup): tem_video = True
            if len(soup.find_all('img')) > 2: tem_foto = True
    except: pass
    return local_encontrado, tem_foto, tem_video

def buscar_generico(url, seletor_tag, seletor_classe=None, regex_link=None):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            alvo = soup.find('a', href=re.compile(regex_link)) if regex_link else soup.find(seletor_tag, class_=seletor_classe) if seletor_classe else soup.find(seletor_tag)
            
            if alvo:
                link_tag = alvo if alvo.name == 'a' else alvo.find('a')
                if link_tag:
                    titulo = link_tag.get_text().strip()
                    url_final = link_tag['href']
                    if not url_final.startswith('http'):
                        base = "/".join(url.split('/')[:3])
                        if not url_final.startswith('/'): url_final = '/' + url_final
                        url_final = base + url_final
                    
                    if len(titulo) > 10:
                        local, foto, video = investigar_detalhes(url_final)
                        return titulo, url_final, local, foto, video
    except: pass
    return None, None, None, None, None

# --- DEFINIÇÕES DE FONTES ---
# (Mesmas funções de antes, simplificadas aqui para economizar espaço visual no código)
def pcdf(): return buscar_generico("https://www.pcdf.df.gov.br/noticias", "a", regex_link=r'/noticias/\d+')
def pmdf(): return buscar_generico("https://portal.pm.df.gov.br/ocorrencias/", "h3") 
def cbmdf(): return buscar_generico("https://www.cbm.df.gov.br/category/noticias/", "h2", "entry-title")
def pcgo(): return buscar_generico("https://policiacivil.go.gov.br/noticias", "h2", "entry-title")
def metropoles(): return buscar_generico("https://www.metropoles.com/distrito-federal", "h3")
def agencia(): return buscar_generico("https://www.agenciabrasilia.df.gov.br/", "h3")
def mpdft(): return buscar_generico("https://www.mpdft.mp.br/portal/index.php/comunicacao-menu/noticias", "h2")
def tjdft(): return buscar_generico("https://www.tjdft.jus.br/institucional/imprensa/noticias", "article", "entry")
def cldf(): return buscar_generico("https://www.cl.df.gov.br/web/guest/noticias", "h3")

# --- SIDEBAR (CONTROLES) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2537/2537853.png", width=50)
    st.title("Radar News DF")
    st.markdown("Central de Monitoramento")
    
    st.write("---")
    
    if st.button("🔄 ATUALIZAR AGORA", type="primary", use_container_width=True):
        st.rerun()
        
    st.write("---")
    st.caption("Fontes Monitoradas:")
    st.markdown("- 🚓 Polícias (Civil/Militar)\n- 🔥 Bombeiros\n- 🏛️ GDF/Justiça\n- 📰 Imprensa Local")
    st.write("---")
    st.caption(f"Versão 7.0 | {datetime.now().strftime('%d/%m/%Y')}")

# --- DASHBOARD PRINCIPAL ---

# Métricas de Topo
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Fontes Ativas", "9 Portais", delta="Online")
col_m2.metric("Regiões Alvo", f"{len(LOCAIS_ALVO)} Locais", delta="DF + Entorno")
col_m3.metric("Última Varredura", datetime.now().strftime('%H:%M:%S'), delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# Função para desenhar o Card Bonito
def render_card(titulo_fonte, cor_fundo, icone, dados):
    titulo, link, local, foto, video = dados
    
    if not titulo:
        # Card vazio/erro
        st.markdown(f"""
        <div class="news-card" style="opacity: 0.6;">
            <div class="card-header" style="background-color: #ccc;">{titulo_fonte} <span style="font-size:10px">OFFLINE/SEM DADOS</span></div>
            <div class="card-body">
                <div class="news-title" style="color:#999; font-style:italic; font-size:14px;">Nenhuma novidade recente detectada na varredura.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Tags HTML
    tags_html = '<div class="tags-container">'
    if local: tags_html += f'<span class="tag tag-local">📍 {local}</span>'
    if video: tags_html += '<span class="tag tag-video">🎥 VÍDEO</span>'
    if foto: tags_html += '<span class="tag tag-foto">📸 FOTOS</span>'
    tags_html += '</div>'

    # Renderiza Card Completo
    st.markdown(f"""
    <div class="news-card">
        <div class="card-header" style="background: {cor_fundo};">
            <span>{icone} {titulo_fonte}</span>
            <span style="background:rgba(255,255,255,0.2); padding:2px 6px; border-radius:4px;">AGORA</span>
        </div>
        <div class="card-body">
            {tags_html}
            <div class="news-title">{titulo}</div>
        </div>
        <div class="card-footer">
            <a href="{link}" target="_blank" class="read-btn">LER MATÉRIA COMPLETA ➜</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- ORGANIZAÇÃO DAS ABAS ---
tab_policia, tab_poder, tab_concorrencia = st.tabs(["🚨 PLANTÃO POLICIAL", "🏛️ PODER & SERVIÇOS", "📰 DESTAQUES PORTAIS"])

with tab_policia:
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_card("PCDF", "linear-gradient(45deg, #000000, #434343)", "🕵️‍♂️", pcdf())
    with c2: render_card("PMDF", "linear-gradient(45deg, #d32f2f, #b71c1c)", "🚓", pmdf())
    with c3: render_card("BOMBEIROS", "linear-gradient(45deg, #fbc02d, #f57f17)", "🔥", cbmdf())
    with c4: render_card("PCGO (Entorno)", "linear-gradient(45deg, #1565c0, #0d47a1)", "🔫", pcgo())

with tab_poder:
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_card("AGÊNCIA BSB", "#009688", "📢", agencia())
    with c2: render_card("MPDFT", "#b71c1c", "⚖️", mpdft())
    with c3: render_card("TJDFT", "#607d8b", "🔨", tjdft())
    with c4: render_card("CÂMARA (CLDF)", "#673ab7", "🏛️", cldf())

with tab_poder: # Adicionando espaço ou reorganizando se quiser
    pass

with tab_concorrencia:
    col_main, col_spacer = st.columns([1, 2])
    with col_main:
        render_card("METRÓPOLES DF", "linear-gradient(45deg, #0288d1, #26c6da)", "📱", metropoles())
    with col_spacer:
        st.info("💡 Dica: O Metrópoles costuma atualizar muito rápido. Se aparecer aqui, confirme na PCDF/PMDF antes de rodar.")
