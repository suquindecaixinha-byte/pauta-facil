import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime
import pytz

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Pauta Fácil",
    layout="wide",
    page_icon="📝",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE MEMÓRIA (CACHE) ---
if 'db_noticias' not in st.session_state:
    st.session_state.db_noticias = {}

# Desabilitar avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# HEADERS REFORÇADOS (Para parecer um PC real e não ser bloqueado)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}

# --- FUNÇÕES DE TEMPO ---
def hora_atual():
    fuso = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso).strftime('%H:%M')

def extrair_horario_texto(soup):
    try:
        texto = soup.get_text()
        match = re.search(r'(\d{2}[:h]\d{2})', texto)
        if match: return match.group(1).replace('h', ':')
    except: pass
    return None

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Oswald:wght@500&display=swap');
    .main { background-color: #f0f2f5; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .criador { font-size: 11px; color: #888; margin-top: -15px; margin-bottom: 20px; border-bottom: 1px solid #ddd; padding-bottom: 10px;}
    
    .news-card {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        border: 1px solid #ffffff;
        overflow: hidden;
        transition: transform 0.2s;
    }
    .news-card:hover { transform: translateY(-2px); border-color: #b0bec5; }
    
    .card-header {
        padding: 10px 18px;
        font-family: 'Oswald', sans-serif;
        font-size: 14px;
        text-transform: uppercase;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .time-badge { background: rgba(0,0,0,0.4); padding: 3px 8px; border-radius: 6px; font-size: 11px; font-family: 'Inter', sans-serif; font-weight: 600; }
    .card-body { padding: 18px; }
    .news-title { font-size: 16px; font-weight: 700; color: #111; line-height: 1.5; margin-bottom: 15px; min-height: 50px; }
    
    .tags-container { margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 6px; }
    .tag { font-size: 10px; padding: 4px 8px; border-radius: 6px; font-weight: 700; text-transform: uppercase; }
    .tag-local { background: #e8f0fe; color: #1967d2; border: 1px solid #d2e3fc; }
    .tag-video { background: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }
    .tag-foto { background: #f3e8fd; color: #8430ce; border: 1px solid #e8d2fa; }
    
    .card-footer { padding: 12px 18px; background-color: #f8f9fa; border-top: 1px solid #f1f3f4; text-align: right; }
    .read-btn { text-decoration: none; color: #333; font-size: 11px; font-weight: 800; }
    .read-btn:hover { color: #1a73e8; }
    </style>
""", unsafe_allow_html=True)

LOCAIS_ALVO = ["Ceilândia", "Taguatinga", "Samambaia", "Gama", "Santa Maria", "Planaltina", "Recanto das Emas", "São Sebastião", "Brazlândia", "Sol Nascente", "Pôr do Sol", "Paranoá", "Núcleo Bandeirante", "Guará", "Sobradinho", "Jardim Botânico", "Lago Norte", "Lago Sul", "Águas Claras", "Riacho Fundo", "Candangolândia", "Vicente Pires", "Varjão", "Fercal", "Itapoã", "Sia", "Cruzeiro", "Sudoeste", "Octogonal", "Luziânia", "Valparaíso", "Águas Lindas", "Novo Gama", "Cidade Ocidental", "Formosa", "Santo Antônio", "Padre Bernardo", "Alexânia", "Planaltina de Goiás", "Esplanada", "Buriti", "Câmara Legislativa"]

def investigar_detalhes(url):
    local_encontrado, tem_foto, tem_video, hora_publicacao = None, False, False, None
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
            hora_publicacao = extrair_horario_texto(soup)
    except: pass
    return local_encontrado, tem_foto, tem_video, hora_publicacao

# --- FUNÇÕES DE BUSCA CORRIGIDAS (V10) ---

def pcdf_corrigida():
    """ Busca na PCDF sem regex estrito, pega o primeiro link de notícia real """
    try:
        # A PCDF as vezes muda a URL base, vamos garantir
        url = "https://www.pcdf.df.gov.br/noticias"
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # Pega TODOS os links da página
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                texto = link.get_text().strip()
                
                # Filtro: Link tem que ter 'noticias' E o texto tem que ser grande (> 25 chars)
                # Isso evita pegar botões de menu como "Mais notícias"
                if '/noticias/' in href and len(texto) > 25:
                    url_final = href
                    if not url_final.startswith('http'): url_final = "https://www.pcdf.df.gov.br" + url_final
                    
                    local, foto, video, hora = investigar_detalhes(url_final)
                    return texto, url_final, local, foto, video, hora
    except Exception as e:
        # print(f"Erro PCDF: {e}") # Debug
        pass
    return None, None, None, None, None, None

def pcgo_corrigida():
    """ Busca na PCGO modo 'Trator' (Force Brute) """
    try:
        url = "https://policiacivil.go.gov.br/noticias"
        r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            
            # PCGO é WordPress. Vamos pegar todos os titulos H2 e H3
            titulos = soup.find_all(['h2', 'h3'])
            
            for t in titulos:
                link_tag = t.find('a')
                if link_tag:
                    texto = link_tag.get_text().strip()
                    href = link_tag['href']
                    
                    # Filtro: Texto longo o suficiente para ser uma manchete
                    if len(texto) > 20:
                        local, foto, video, hora = investigar_detalhes(href)
                        return texto, href, local, foto, video, hora
    except: pass
    return None, None, None, None, None, None

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
                    local, foto, video, hora = investigar_detalhes(url_final)
                    return texto, url_final, local, foto, video, hora
    except: pass
    return None, None, None, None, None, None

# Genérico para os outros
def buscar_generico(url, seletor_tag, seletor_classe=None):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            alvo = soup.find(seletor_tag, class_=seletor_classe) if seletor_classe else soup.find(seletor_tag)
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
                        local, foto, video, hora = investigar_detalhes(url_final)
                        return titulo, url_final, local, foto, video, hora
    except: pass
    return None, None, None, None, None, None

# --- SIDEBAR ---
with st.sidebar:
    st.title("📝 Pauta Fácil")
    st.markdown("<div class='criador'>Criado por Deivlin Vale</div>", unsafe_allow_html=True)
    if st.button("🔄 ATUALIZAR SISTEMA", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.write("---")
    st.caption(f"Brasília, {datetime.now().strftime('%d/%m/%Y')}")
    st.markdown(f"**{hora_atual()}**")

# --- RENDERIZAÇÃO ---
def render_card(chave_id, nome_fonte, cor_fundo, icone, func_busca):
    dados = func_busca()
    titulo, link, local, foto, video, hora = dados
    status_msg = ""
    
    if titulo:
        st.session_state.db_noticias[chave_id] = {
            "titulo": titulo, "link": link, "local": local, 
            "foto": foto, "video": video, "hora": hora, "timestamp": hora_atual()
        }
        status_msg = "⏱ " + (hora if hora else "Recente")
    else:
        memoria = st.session_state.db_noticias.get(chave_id)
        if memoria:
            titulo, link, local, foto, video, hora = memoria["titulo"], memoria["link"], memoria["local"], memoria["foto"], memoria["video"], memoria["hora"]
            status_msg = "⚠️ CACHED"
        else:
            st.markdown(f"""<div class="news-card" style="opacity: 0.5;"><div class="card-header" style="background-color: #999;">{nome_fonte}</div><div class="card-body"><div class="news-title" style="color:#777; font-size:13px;">Verificando fonte... (Offline ou Sem Novidades)</div></div></div>""", unsafe_allow_html=True)
            return

    tags_html = '<div class="tags-container">'
    if local: tags_html += f'<span class="tag tag-local">📍 {local}</span>'
    if video: tags_html += '<span class="tag tag-video">🎥 VÍDEO</span>'
    if foto: tags_html += '<span class="tag tag-foto">📸 FOTO</span>'
    tags_html += '</div>'

    st.markdown(f"""
    <div class="news-card">
        <div class="card-header" style="background: {cor_fundo};"><span>{icone} {nome_fonte}</span><div class="time-badge">{status_msg}</div></div>
        <div class="card-body">{tags_html}<div class="news-title">{titulo}</div></div>
        <div class="card-footer"><a href="{link}" target="_blank" class="read-btn">LER MATÉRIA ➜</a></div>
    </div>
    """, unsafe_allow_html=True)

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["🚨 POLICIAL", "🏛️ PODER", "📰 PORTAIS"])

# Funções Lambda (Apelidos)
f_ag = lambda: buscar_generico("https://www.agenciabrasilia.df.gov.br/", "h3")
f_mp = lambda: buscar_generico("https://www.mpdft.mp.br/portal/index.php/comunicacao-menu/noticias", "h2")
f_tj = lambda: buscar_generico("https://www.tjdft.jus.br/institucional/imprensa/noticias", "article", "entry")
f_cl = lambda: buscar_generico("https://www.cl.df.gov.br/web/guest/noticias", "h3")
f_metro = lambda: buscar_generico("https://www.metropoles.com/distrito-federal", "h3")

with tab1:
    c1, c2, c3 = st.columns(3)
    # Usando as funções corrigidas aqui:
    with c1: render_card("pcdf", "PCDF", "linear-gradient(135deg, #232526, #414345)", "🕵️‍♂️", pcdf_corrigida)
    with c2: render_card("pmdf", "PMDF", "linear-gradient(135deg, #cb2d3e, #ef473a)", "🚓", pmdf_v2)
    with c3: render_card("pcgo", "PCGO", "linear-gradient(135deg, #1A2980, #26D0CE)", "🔫", pcgo_corrigida)

with tab2:
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_card("ag", "GDF", "#009688", "📢", f_ag)
    with c2: render_card("mp", "MPDFT", "#b71c1c", "⚖️", f_mp)
    with c3: render_card("tj", "TJDFT", "#607d8b", "🔨", f_tj)
    with c4: render_card("cl", "CLDF", "#673ab7", "🏛️", f_cl)

with tab3:
    c1, c2 = st.columns([1, 2])
    with c1: render_card("mt", "METRÓPOLES", "linear-gradient(135deg, #00B4DB, #0083B0)", "📱", f_metro)
    with c2: st.info(f"Monitoramento de concorrência ativo.")
