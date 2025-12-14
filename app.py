import streamlit as st
import feedparser
import requests
import re
import html
import urllib3
from datetime import datetime, timedelta
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Pauta Fácil TV",
    layout="wide",
    page_icon="📺",
    initial_sidebar_state="collapsed"
)

# Ignora erro de SSL (Cadeado de segurança)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- MEMÓRIA PERMANENTE ---
if 'cache_noticias' not in st.session_state:
    st.session_state.cache_noticias = {}

# --- FUNÇÕES ÚTEIS ---
def hora_brasilia():
    # Pega hora atual UTC-3
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
    # Remove HTML
    clean = re.compile('<.*?>')
    t = re.sub(clean, '', texto)
    # Remove caracteres estranhos
    return html.escape(t).replace('\n', ' ').strip()

def detectar_local(texto):
    locais = ["Ceilândia", "Taguatinga", "Samambaia", "Gama", "Santa Maria", "Planaltina", "Recanto das Emas", "São Sebastião", "Brazlândia", "Sol Nascente", "Pôr do Sol", "Paranoá", "Núcleo Bandeirante", "Guará", "Sobradinho", "Jardim Botânico", "Lago Norte", "Lago Sul", "Águas Claras", "Riacho Fundo", "Candangolândia", "Vicente Pires", "Varjão", "Fercal", "Itapoã", "Sia", "Cruzeiro", "Sudoeste", "Octogonal", "Luziânia", "Valparaíso", "Águas Lindas", "Novo Gama", "Cidade Ocidental", "Formosa", "Santo Antônio", "Padre Bernardo", "Alexânia", "Planaltina de Goiás", "Esplanada", "Buriti", "Câmara Legislativa"]
    for l in locais:
        if re.search(r'\b' + re.escape(l) + r'\b', texto, re.IGNORECASE):
            return l
    return None

# --- MOTOR DE BUSCA (COM DISFARCE E MEMÓRIA) ---
def buscar_feed(chave, url):
    # Cabeçalhos para enganar bloqueios
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    
    dados = None
    try:
        # 1. Tenta baixar
        r = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        if r.status_code == 200:
            feed = feedparser.parse(r.content)
            if feed.entries:
                entry = feed.entries[0]
                
                # 2. Processa dados
                dados = {
                    "titulo": limpar_texto(entry.title),
                    "link": entry.link,
                    "resumo": limpar_texto(entry.get('summary', entry.get('description', ''))),
                    "hora": formatar_data(entry),
                    "local": None,
                    "status": "🟢 Online"
                }
                
                # 3. Detecta local
                texto_full = f"{dados['titulo']} {dados['resumo']}"
                dados['local'] = detectar_local(texto_full)
                
                # 4. Salva na memória
                st.session_state.cache_noticias[chave] = dados

    except Exception as e:
        # print(f"Erro {chave}: {e}")
        pass

    # RETORNO INTELIGENTE:
    # Se baixou novo, retorna novo.
    # Se falhou, mas tem memória, retorna memória com aviso.
    if dados:
        return dados
    elif chave in st.session_state.cache_noticias:
        memoria = st.session_state.cache_noticias[chave]
        memoria['status'] = "⚠️ Offline (Memória)"
        return memoria
    else:
        return None

# --- RENDERIZAÇÃO VISUAL (SEM INDENTAÇÃO PARA NÃO QUEBRAR) ---
def render_card(chave, nome, url, cor, icone):
    d = buscar_feed(chave, url)
    
    # Se não tem nada (nem novo, nem memória)
    if not d:
        st.markdown(f"""
<div style="background:#eee; padding:15px; border-radius:10px; border-left:5px solid #999; margin-bottom:15px; opacity:0.6;">
    <strong style="color:#555">{icone} {nome}</strong><br>
    <span style="font-size:12px">Conectando...</span>
</div>""", unsafe_allow_html=True)
        return

    # Monta tags
    tag_local = ""
    if d['local']:
        tag_local = f"<span style='background:#e3f2fd; color:#1565c0; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:800; margin-left:5px;'>📍 {d['local']}</span>"

    # HTML CRÍTICO - NÃO ADICIONE ESPAÇOS NO INÍCIO DAS LINHAS ABAIXO
    html_card = f"""
<div style="background:white; padding:15px; border-radius:12px; box-shadow:0 3px 8px rgba(0,0,0,0.08); margin-bottom:15px; border-left:5px solid {cor}; border:1px solid #eee;">
<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
<div><span style="font-weight:900; color:{cor}; font-size:12px;">{icone} {nome}</span>{tag_local}</div>
<div style="text-align:right;"><div style="font-size:11px; font-weight:bold; color:#555;">{d['hora']}</div><div style="font-size:9px; color:#999;">{d['status']}</div></div>
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
    if st.button("🔄 ATUALIZAR"): st.rerun()

st.caption(f"Última verificação: {hora_brasilia()}")

st.markdown("#### 🚨 Policial & Segurança")
c1, c2, c3 = st.columns(3)
with c1: render_card("pcdf", "PCDF", "https://www.pcdf.df.gov.br/noticias?format=feed&type=rss", "#2c3e50", "🕵️‍♂️")
with c2: render_card("metro", "METRÓPOLES", "https://www.metropoles.com/distrito-federal/feed", "#007bff", "📱")
with c3: render_card("pcgo", "PCGO", "https://policiacivil.go.gov.br/feed", "#c0392b", "🔫")

st.markdown("---")
st.markdown("#### 🏛️ Poder & Serviços")
c4, c5, c6, c7 = st.columns(4)
with c4: render_card("gdf", "GDF", "https://www.agenciabrasilia.df.gov.br/feed/", "#009688", "📢")
with c5: render_card("mp", "MPDFT", "https://www.mpdft.mp.br/portal/index.php/comunicacao-menu/noticias?format=feed&type=rss", "#b71c1c", "⚖️")
with c6: render_card("senado", "SENADO", "https://www12.senado.leg.br/noticias/feed/metadados/agencia", "#673ab7", "🏛️")
with c7: render_card("cbm", "BOMBEIROS", "https://www.cbm.df.gov.br/feed/", "#f39c12", "🔥")
