import streamlit as st
import feedparser
import requests
import re
import html
import urllib3
from datetime import datetime, timedelta
import time
import concurrent.futures

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Pauta Fácil TV",
    layout="wide",
    page_icon="📺",
    initial_sidebar_state="collapsed"
)

# Ignora erro de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- AUTO-REFRESH (5 Minutos) ---
from streamlit.runtime.scriptrunner import RerunData, RerunException
def auto_atualizar(segundos=300):
    if 'ultimo_update' not in st.session_state:
        st.session_state.ultimo_update = time.time()
    if time.time() - st.session_state.ultimo_update > segundos:
        st.session_state.ultimo_update = time.time()
        st.rerun()
auto_atualizar(300)

# --- MEMÓRIA ---
if 'cache_noticias' not in st.session_state:
    st.session_state.cache_noticias = {}

# --- LISTA DE FONTES (CONFIGURAÇÃO) ---
FONTES = {
    "pcdf": {"nome": "PCDF", "url": "https://www.pcdf.df.gov.br/noticias?format=feed&type=rss", "cor": "#2c3e50", "icone": "🕵️‍♂️"},
    "metro": {"nome": "METRÓPOLES", "url": "https://www.metropoles.com/distrito-federal/feed", "cor": "#007bff", "icone": "📱"},
    "pcgo": {"nome": "PCGO", "url": "https://policiacivil.go.gov.br/feed", "cor": "#c0392b", "icone": "🔫"},
    "gdf": {"nome": "GDF", "url": "https://www.agenciabrasilia.df.gov.br/feed/", "cor": "#009688", "icone": "📢"},
    "mp": {"nome": "MPDFT", "url": "https://www.mpdft.mp.br/portal/index.php/comunicacao-menu/noticias?format=feed&type=rss", "cor": "#b71c1c", "icone": "⚖️"},
    "senado": {"nome": "SENADO", "url": "https://www12.senado.leg.br/noticias/feed/metadados/agencia", "cor": "#673ab7", "icone": "🏛️"},
    "cbm": {"nome": "BOMBEIROS", "url": "https://www.cbm.df.gov.br/feed/", "cor": "#f39c12", "icone": "🔥"}
}

# --- FUNÇÕES ÚTEIS ---
def hora_brasilia():
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%H:%M')

def formatar_data(entry):
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            dt = dt - timedelta(hours=3)
            return dt.strftime('%d/%m %H:%M')
    except: pass
    return "Recente"

def limpar_texto(texto):
    if not texto: return ""
    clean = re.compile('<.*?>')
    t = re.sub(clean, '', texto)
    return html.escape(t).replace('\n', ' ').strip()

def detectar_local(texto):
    locais = ["Ceilândia", "Taguatinga", "Samambaia", "Gama", "Santa Maria", "Planaltina", "Recanto das Emas", "São Sebastião", "Brazlândia", "Sol Nascente", "Pôr do Sol", "Paranoá", "Núcleo Bandeirante", "Guará", "Sobradinho", "Jardim Botânico", "Lago Norte", "Lago Sul", "Águas Claras", "Riacho Fundo", "Candangolândia", "Vicente Pires", "Varjão", "Fercal", "Itapoã", "Sia", "Cruzeiro", "Sudoeste", "Octogonal", "Luziânia", "Valparaíso", "Águas Lindas", "Novo Gama", "Cidade Ocidental", "Formosa", "Santo Antônio", "Padre Bernardo", "Alexânia", "Planaltina de Goiás", "Esplanada", "Buriti", "Câmara Legislativa"]
    for l in locais:
        if re.search(r'\b' + re.escape(l) + r'\b', texto, re.IGNORECASE):
            return l
    return None

# --- MOTOR DE BUSCA INDIVIDUAL (EXECUTADO EM PARALELO) ---
def baixar_url(chave, url):
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    try:
        # Timeout reduzido para 6s. Se PCDF não responder em 6s, desiste para não travar o resto.
        r = requests.get(url, headers=HEADERS, verify=False, timeout=6)
        if r.status_code == 200:
            feed = feedparser.parse(r.content)
            if feed.entries:
                entry = feed.entries[0]
                dados = {
                    "titulo": limpar_texto(entry.title),
                    "link": entry.link,
                    "resumo": limpar_texto(entry.get('summary', entry.get('description', ''))),
                    "hora": formatar_data(entry),
                    "local": detectar_local(f"{entry.title} {entry.get('summary', '')}"),
                    "status": "🟢 Online"
                }
                return chave, dados
    except:
        pass
    return chave, None

# --- GERENCIADOR DE CARREGAMENTO PARALELO ---
def atualizar_tudo():
    # Cria uma barra de progresso
    bar = st.progress(0, text="Iniciando Turbo Download...")
    
    # Lista de tarefas
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Dispara todos os downloads ao mesmo tempo
        futuros = {executor.submit(baixar_url, k, v["url"]): k for k, v in FONTES.items()}
        
        completos = 0
        total = len(FONTES)
        
        for future in concurrent.futures.as_completed(futuros):
            chave, dados = future.result()
            if dados:
                st.session_state.cache_noticias[chave] = dados
            
            # Atualiza barra
            completos += 1
            bar.progress(completos / total, text=f"Carregando fontes... {completos}/{total}")
            
    time.sleep(0.5)
    bar.empty() # Remove a barra quando terminar

# --- RENDERIZAÇÃO ---
def render_card(chave):
    conf = FONTES[chave]
    
    # Pega da memória (que foi atualizada pelo Turbo)
    d = st.session_state.cache_noticias.get(chave)
    
    # Se não tiver nada na memória (nunca carregou)
    if not d:
        st.markdown(f"""
<div style="background:#f4f4f4; padding:15px; border-radius:10px; border-left:5px solid #ccc; margin-bottom:15px; opacity:0.6;">
    <strong style="color:#555">{conf['icone']} {conf['nome']}</strong><br>
    <span style="font-size:11px">Aguardando...</span>
</div>""", unsafe_allow_html=True)
        return

    # Se tiver na memória, verifica se é atualização recente ou velha
    status_label = d.get('status', '⚠️ Memória')

    tag_local = ""
    if d['local']:
        tag_local = f"<span style='background:#e3f2fd; color:#1565c0; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:800; margin-left:5px;'>📍 {d['local']}</span>"

    html_card = f"""
<div style="background:white; padding:15px; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.05); margin-bottom:15px; border-left:5px solid {conf['cor']}; border:1px solid #eee;">
<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
<div><span style="font-weight:900; color:{conf['cor']}; font-size:12px;">{conf['icone']} {conf['nome']}</span>{tag_local}</div>
<div style="text-align:right;"><div style="font-size:11px; font-weight:bold; color:#555;">{d['hora']}</div><div style="font-size:9px; color:#999;">{status_label}</div></div>
</div>
<div style="font-size:15px; font-weight:800; color:#222; margin-bottom:8px; line-height:1.3;">{d['titulo']}</div>
<div style="font-size:13px; color:#555; margin-bottom:12px; line-height:1.4; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;">{d['resumo'][:160]}...</div>
<div style="text-align:right;"><a href="{d['link']}" target="_blank" style="text-decoration:none; color:#333; font-weight:800; font-size:11px; background:#f0f2f6; padding:8px 14px; border-radius:6px;">LER MATÉRIA ➜</a></div>
</div>
"""
    st.markdown(html_card, unsafe_allow_html=True)

# --- LAYOUT PRINCIPAL ---
c_topo1, c_topo2 = st.columns([4, 1])
with c_topo1: st.markdown("### 📺 Pauta Fácil TV")
with c_topo2: 
    if st.button("🚀 TURBO UPDATE", type="primary"):
        atualizar_tudo()
        st.rerun()

# Se for a primeira vez que abre, já roda o turbo
if not st.session_state.cache_noticias:
    atualizar_tudo()

st.caption(f"Última verificação: {hora_brasilia()}")

st.markdown("#### 🚨 Policial & Segurança")
c1, c2, c3 = st.columns(3)
with c1: render_card("pcdf")
with c2: render_card("metro")
with c3: render_card("pcgo")

st.markdown("---")
st.markdown("#### 🏛️ Poder & Serviços")
c4, c5, c6, c7 = st.columns(4)
with c4: render_card("gdf")
with c5: render_card("mp")
with c6: render_card("senado")
with c7: render_card("cbm")
