import streamlit as st
import feedparser
import requests
import re
import html
import urllib3
from datetime import datetime, timedelta
import time

# --- CONFIGURAÇÃO ---
st.set_page_config(
    page_title="Pauta Fácil TV",
    layout="wide",
    page_icon="📺",
    initial_sidebar_state="collapsed" # Esconde a sidebar para dar mais espaço na TV
)

# Ignorar avisos de SSL (Para PCDF)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- INICIALIZAÇÃO DA MEMÓRIA ---
# Isso garante que a última notícia fique salva mesmo se o site cair
if 'cache_noticias' not in st.session_state:
    st.session_state.cache_noticias = {}

# --- UTILITÁRIOS ---
def hora_atual_brasilia():
    # Ajuste simples para UTC-3 (Brasília)
    return (datetime.utcnow() - timedelta(hours=3)).strftime('%H:%M')

def formatar_data_rss(entry):
    """ Tenta extrair e formatar a hora da publicação do RSS """
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            # Converte a tupla de tempo do RSS para datetime
            dt = datetime.fromtimestamp(time.mktime(entry.published_parsed))
            # Ajusta fuso (RSS geralmente é UTC ou local, vamos assumir -3h para simplificar visualização)
            dt = dt - timedelta(hours=3)
            return dt.strftime('%d/%m %H:%M')
    except:
        pass
    return "Recente"

def limpar_texto(texto):
    """ Limpa HTML e caracteres que quebram o layout """
    if not texto: return ""
    # Remove tags HTML
    clean = re.compile('<.*?>')
    texto_sem_html = re.sub(clean, '', texto)
    # Escapa caracteres especiais (resolve o bug do </div> aparecendo)
    return html.escape(texto_sem_html)

# --- DETECTOR DE LOCAL ---
LOCAIS_ALVO = ["Ceilândia", "Taguatinga", "Samambaia", "Gama", "Santa Maria", "Planaltina", "Recanto das Emas", "São Sebastião", "Brazlândia", "Sol Nascente", "Pôr do Sol", "Paranoá", "Núcleo Bandeirante", "Guará", "Sobradinho", "Jardim Botânico", "Lago Norte", "Lago Sul", "Águas Claras", "Riacho Fundo", "Candangolândia", "Vicente Pires", "Varjão", "Fercal", "Itapoã", "Sia", "Cruzeiro", "Sudoeste", "Octogonal", "Luziânia", "Valparaíso", "Águas Lindas", "Novo Gama", "Cidade Ocidental", "Formosa", "Santo Antônio", "Padre Bernardo", "Alexânia", "Planaltina de Goiás", "Esplanada", "Buriti", "Câmara Legislativa"]

def detectar_local(texto):
    for l in LOCAIS_ALVO:
        if re.search(r'\b' + re.escape(l) + r'\b', texto, re.IGNORECASE):
            return l
    return None

# --- MOTOR DE BUSCA (COM MEMÓRIA) ---
def buscar_feed(chave, url_rss):
    """ 
    Tenta baixar. 
    Se conseguir -> Atualiza memória e retorna.
    Se falhar -> Retorna o que tem na memória.
    """
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*'
    }
    
    sucesso = False
    dados_novos = None

    try:
        # Tenta baixar com Requests (mais robusto que feedparser direto)
        resp = requests.get(url_rss, headers=HEADERS, verify=False, timeout=10)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            if feed.entries:
                entry = feed.entries[0]
                
                # Prepara os dados limpos
                dados_novos = {
                    "titulo": limpar_texto(entry.title),
                    "link": entry.link,
                    "resumo": limpar_texto(entry.get('summary', entry.get('description', ''))),
                    "hora": formatar_data_rss(entry),
                    "status": "🟢 Online"
                }
                
                # Detecta local
                texto_completo = f"{dados_novos['titulo']} {dados_novos['resumo']}"
                dados_novos['local'] = detectar_local(texto_completo)
                
                # Salva na memória
                st.session_state.cache_noticias[chave] = dados_novos
                sucesso = True
    except Exception as e:
        # print(f"Erro ao buscar {chave}: {e}") # Debug
        pass

    # Retorno: Dados novos OU Dados da memória OU None
    if sucesso:
        return dados_novos
    elif chave in st.session_state.cache_noticias:
        # Recupera da memória e avisa que é cache
        dados_antigos = st.session_state.cache_noticias[chave]
        dados_antigos['status'] = "⚠️ Memória" 
        return dados_antigos
    else:
        return None

# --- RENDERIZAÇÃO DO CARD ---
def render_card(chave, nome, url, cor, icone):
    dados = buscar_feed(chave, url)
    
    if not dados:
        # Caso nunca tenha carregado nada
        st.markdown(f"""
        <div style="background:#f0f2f6; padding:15px; border-radius:10px; border-left:5px solid #ccc; margin-bottom:15px; opacity:0.6;">
            <strong style="color:#555">{icone} {nome}</strong><br>
            <span style="font-size:12px; color:#777">Aguardando primeira conexão...</span>
        </div>
        """, unsafe_allow_html=True)
        return

    # Monta as Tags
    html_tags = ""
    if dados['local']:
        html_tags += f"<span style='background:#e3f2fd; color:#1565c0; padding:2px 6px; border-radius:4px; font-size:10px; font-weight:800; margin-left:5px;'>📍 {dados['local']}</span>"

    # HTML Seguro (Sem f-strings complexas que quebram o layout)
    card_html = f"""
    <div style="background:white; padding:15px; border-radius:12px; box-shadow:0 3px 10px rgba(0,0,0,0.08); margin-bottom:15px; border-left:5px solid {cor}; border-top:1px solid #eee; border-right:1px solid #eee; border-bottom:1px solid #eee;">
        
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
            <div>
                <span style="font-weight:900; color:{cor}; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">{icone} {nome}</span>
                {html_tags}
            </div>
            <div style="text-align:right;">
                <div style="font-size:11px; font-weight:bold; color:#555;">{dados['hora']}</div>
                <div style="font-size:9px; color:#999;">{dados['status']}</div>
            </div>
        </div>

        <div style="font-size:15px; font-weight:800; color:#222; margin-bottom:8px; line-height:1.4;">
            {dados['titulo']}
        </div>

        <div style="font-size:13px; color:#555; margin-bottom:12px; line-height:1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
            {dados['resumo'][:180]}...
        </div>

        <div style="text-align:right;">
            <a href="{dados['link']}" target="_blank" style="display:inline-block; text-decoration:none; color:#333; font-weight:800; font-size:11px; background:#f0f2f6; padding:8px 14px; border-radius:6px; transition:0.2s;">LER MATÉRIA ➜</a>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

# --- CABEÇALHO ---
c_head1, c_head2 = st.columns([3, 1])
with c_head1:
    st.markdown("### 📺 Pauta Fácil TV")
with c_head2:
    if st.button("🔄 ATUALIZAR", type="primary", use_container_width=True):
        st.rerun()

st.markdown(f"<div style='text-align:right; font-size:12px; color:#666; margin-top:-10px; margin-bottom:20px;'>Última verificação: <b>{hora_atual_brasilia()}</b></div>", unsafe_allow_html=True)

# --- COLUNAS DE NOTÍCIAS ---
st.markdown("#### 🚨 Policial & Segurança")
col1, col2, col3 = st.columns(3)

with col1:
    render_card("pcdf", "PCDF", "https://www.pcdf.df.gov.br/noticias?format=feed&type=rss", "#2c3e50", "🕵️‍♂️")

with col2:
    # Metrópoles (Distrito Federal)
    render_card("metro", "METRÓPOLES", "https://www.metropoles.com/distrito-federal/feed", "#007bff", "📱")

with col3:
    # PCGO
    render_card("pcgo", "PCGO", "https://policiacivil.go.gov.br/feed", "#c0392b", "🔫")

st.markdown("---")
st.markdown("#### 🏛️ Poder & Serviços")
col4, col5, col6, col7 = st.columns(4)

with col4:
    render_card("gdf", "GDF", "https://www.agenciabrasilia.df.gov.br/feed/", "#009688", "📢")

with col5:
    render_card("mp", "MPDFT", "https://www.mpdft.mp.br/portal/index.php/comunicacao-menu/noticias?format=feed&type=rss", "#b71c1c", "⚖️")

with col6:
    render_card("senado", "SENADO", "https://www12.senado.leg.br/noticias/feed/metadados/agencia", "#673ab7", "🏛️")

with col7:
    render_card("cbm", "BOMBEIROS", "https://www.cbm.df.gov.br/feed/", "#f39c12", "🔥")
