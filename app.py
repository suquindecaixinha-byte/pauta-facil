import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime
import pytz # Biblioteca para fuso horário

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Pauta Fácil",
    layout="wide",
    page_icon="📝",
    initial_sidebar_state="expanded"
)

# --- CONFIGURAÇÃO DE ESTADO (MEMÓRIA) ---
# Isso permite saber se a notícia é nova ou se já estava lá
if 'historico' not in st.session_state:
    st.session_state.historico = {}

# Desabilitar avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}

# --- FUSO HORÁRIO DE BRASÍLIA ---
def hora_brasilia():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime('%H:%M:%S')

# --- ESTILOS CSS (VISUAL TV) ---
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    h1, h2, h3 { font-family: 'Roboto', sans-serif; }
    
    /* Assinatura do Criador */
    .criador {
        font-size: 12px;
        color: #666;
        margin-top: -15px;
        margin-bottom: 20px;
        font-style: italic;
    }

    /* Card de Notícia */
    .news-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e1e4e8;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* Cabeçalho do Card */
    .card-header {
        padding: 8px 15px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Status da Notícia (Nova vs Antiga) */
    .status-badge {
        background: rgba(0,0,0,0.3);
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 10px;
    }
    
    .card-body { padding: 15px; }
    .news-title {
        font-size: 15px;
        font-weight: 700;
        color: #1a1a1a;
        line-height: 1.4;
        margin-bottom: 12px;
        min-height: 42px;
    }
    
    /* Tags */
    .tags-container { margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 5px; }
    .tag { font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 700; text-transform: uppercase; }
    .tag-local { background: #e3f2fd; color: #1565c0; }
    .tag-video { background: #fce4ec; color: #c2185b; }
    .tag-foto { background: #f3e5f5; color: #7b1fa2; }
    
    /* Botão */
    .card-footer {
        padding: 8px 15px;
        background-color: #f8f9fa;
        border-top: 1px solid #eee;
        text-align: right;
    }
    .read-btn {
        text-decoration: none;
        color: #333;
        font-size: 11px;
        font-weight: 700;
    }
    .read-btn:hover { color: #007bff; }
    
    </style>
""", unsafe_allow_html=True)

# --- INTELIGÊNCIA DE LOCAL ---
LOCAIS_ALVO = [
    "Ceilândia", "Taguatinga", "Samambaia", "Gama", "Santa Maria", "Planaltina", "Recanto das Emas",
    "São Sebastião", "Brazlândia", "Sol Nascente", "Pôr do Sol", "Paranoá", "Núcleo Bandeirante",
    "Guará", "Sobradinho", "Jardim Botânico", "Lago Norte", "Lago Sul", "Águas Claras", "Riacho Fundo",
    "Candangolândia", "Vicente Pires", "Varjão", "Fercal", "Itapoã", "Sia", "Cruzeiro", "Sudoeste", "Octogonal",
    "Luziânia", "Valparaíso", "Águas Lindas", "Novo Gama", "Cidade Ocidental", "Formosa", "Santo Antônio",
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

# --- SCRAPER MESTRE ---
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

def pmdf_v2():
    try:
        url = "https://portal.pm.df.gov.br/ocorrencias/"
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            headers = soup.find_all(['h3', 'h2', 'h4'])
            for h in headers:
                link = h.find('a')
                if link:
                    texto = link.get_text().strip()
                    url_final = link['href']
                    if len(texto) < 15 or "leia mais" in texto.lower(): continue
                    if not url_final.startswith('http'): url_final = "https://portal.pm.df.gov.br" + url_final
                    local, foto, video = investigar_detalhes(url_final)
                    return texto, url_final, local, foto, video
    except: pass
    return None, None, None, None, None

# --- DEFINIÇÕES DE FONTES ---
def pcdf(): return buscar_generico("https://www.pcdf.df.gov.br/noticias", "a", regex_link=r'/noticias/\d+')
def pcgo(): return buscar_generico("https://policiacivil.go.gov.br/noticias", "h2", "entry-title")
def metropoles(): return buscar_generico("https://www.metropoles.com/distrito-federal", "h3")
def agencia(): return buscar_generico("https://www.agenciabrasilia.df.gov.br/", "h3")
def mpdft(): return buscar_generico("https://www.mpdft.mp.br/portal/index.php/comunicacao-menu/noticias", "h2")
def tjdft(): return buscar_generico("https://www.tjdft.jus.br/institucional/imprensa/noticias", "article", "entry")
def cldf(): return buscar_generico("https://www.cl.df.gov.br/web/guest/noticias", "h3")

# --- SIDEBAR ---
with st.sidebar:
    st.title("📝 Pauta Fácil")
    st.markdown("<div class='criador'>Criado por Deivlin Vale</div>", unsafe_allow_html=True)
    
    if st.button("🔄 ATUALIZAR AGORA", type="primary", use_container_width=True):
        st.rerun()
        
    st.write("---")
    st.info(f"🕒 Horário de Brasília:\n**{hora_brasilia()}**")
    st.write("---")
    st.caption("Fontes Monitoradas: 8")

# --- LAYOUT PRINCIPAL ---

# Título Principal (Opcional, já está na sidebar, mas bom para mobile)
# st.title("Pauta Fácil") 

# Função de Renderização Inteligente
def render_card(id_fonte, nome_fonte, cor_fundo, icone, dados):
    titulo, link, local, foto, video = dados
    
    # Lógica de Estado (Novo vs Velho)
    status_label = "📌 ÚLTIMA"
    cor_status = "rgba(255,255,255,0.2)" # Transparente
    
    if titulo:
        ultimo_titulo = st.session_state.historico.get(id_fonte)
        
        if ultimo_titulo:
            if ultimo_titulo == titulo:
                status_label = "⏳ ANTIGA"
                cor_status = "rgba(0,0,0,0.4)" # Cinza escuro
            else:
                status_label = "🔥 NOVA!"
                cor_status = "#00c853" # Verde vibrante
        
        # Atualiza histórico
        st.session_state.historico[id_fonte] = titulo
    else:
        status_label = "OFFLINE"

    if not titulo:
        st.markdown(f"""
        <div class="news-card" style="opacity: 0.6;">
            <div class="card-header" style="background-color: #999;">{nome_fonte}</div>
            <div class="card-body"><div class="news-title" style="color:#777; font-size:13px;">Sem dados recentes.</div></div>
        </div>
        """, unsafe_allow_html=True)
        return

    tags_html = '<div class="tags-container">'
    if local: tags_html += f'<span class="tag tag-local">📍 {local}</span>'
    if video: tags_html += '<span class="tag tag-video">🎥 VÍDEO</span>'
    if foto: tags_html += '<span class="tag tag-foto">📸 FOTO</span>'
    tags_html += '</div>'

    st.markdown(f"""
    <div class="news-card">
        <div class="card-header" style="background: {cor_fundo};">
            <span>{icone} {nome_fonte}</span>
            <span class="status-badge" style="background:{cor_status}">{status_label}</span>
        </div>
        <div class="card-body">
            {tags_html}
            <div class="news-title">{titulo}</div>
        </div>
        <div class="card-footer">
            <a href="{link}" target="_blank" class="read-btn">ACESSAR PAUTA ➜</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- ABAS ---
tab_policia, tab_poder, tab_concorrencia = st.tabs(["🚨 POLICIAL", "🏛️ PODER", "📰 PORTAIS"])

with tab_policia:
    c1, c2, c3 = st.columns(3)
    with c1: render_card("pcdf", "PCDF", "linear-gradient(45deg, #2c3e50, #000000)", "🕵️‍♂️", pcdf())
    with c2: render_card("pmdf", "PMDF", "linear-gradient(45deg, #c0392b, #8e44ad)", "🚓", pmdf_v2())
    with c3: render_card("pcgo", "PCGO ENTORNO", "linear-gradient(45deg, #2980b9, #2c3e50)", "🔫", pcgo())

with tab_poder:
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_card("ag", "AGÊNCIA BSB", "#009688", "📢", agencia())
    with c2: render_card("mp", "MPDFT", "#c0392b", "⚖️", mpdft())
    with c3: render_card("tj", "TJDFT", "#7f8c8d", "🔨", tjdft())
    with c4: render_card("cl", "CÂMARA (CLDF)", "#8e44ad", "🏛️", cldf())

with tab_concorrencia:
    col_main, col_spacer = st.columns([1, 2])
    with col_main:
        render_card("metro", "METRÓPOLES DF", "linear-gradient(45deg, #039be5, #00acc1)", "📱", metropoles())
    with col_spacer:
        st.info(f"Última verificação às {hora_brasilia()}")
