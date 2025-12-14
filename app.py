import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar News DF - Inteligência", layout="wide", page_icon="📡")

# Desabilitar avisos SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}

# --- CÉREBRO: BANCO DE DADOS DE LOCAIS (DF + ENTORNO) ---
# Adicione aqui todas as cidades/RAs que você quer monitorar
LOCAIS_ALVO = [
    "Ceilândia", "Taguatinga", "Samambaia", "Gama", "Santa Maria", "Planaltina", "Recanto das Emas",
    "São Sebastião", "Brazlândia", "Sol Nascente", "Pôr do Sol", "Paranoá", "Núcleo Bandeirante",
    "Guará", "Sobradinho", "Jardim Botânico", "Lago Norte", "Lago Sul", "Águas Claras", "Riacho Fundo",
    "Candangolândia", "Vicente Pires", "Varjão", "Fercal", "Itapoã", "Sia", "Cruzeiro", "Sudoeste", "Octogonal",
    "Luziânia", "Valparaíso", "Águas Lindas", "Novo Gama", "Cidade Ocidental", "Formosa", "Santo Antônio do Descoberto",
    "Padre Bernardo", "Alexânia", "Planaltina de Goiás"
]

# --- FUNÇÃO INVESTIGADORA (ENTRA NO LINK) ---
def investigar_detalhes(url, site_tipo):
    """
    Entra no link, procura onde foi e se tem mídia.
    Retorna: (Local, Tem_Foto, Tem_Video)
    """
    local_encontrado = "Local não citado"
    tem_foto = False
    tem_video = False

    try:
        r = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            texto_completo = soup.get_text()

            # 1. Caça ao Local (Procura no texto da matéria)
            # Prioridade: Tenta achar o nome da RA ou Cidade no texto
            for local in LOCAIS_ALVO:
                # Procura o local no texto (ignorando maiúsculas/minúsculas)
                if re.search(r'\b' + re.escape(local) + r'\b', texto_completo, re.IGNORECASE):
                    local_encontrado = local
                    break # Achou o primeiro, para (geralmente o mais relevante aparece antes)

            # 2. Caça a Vídeos
            # Procura iframes (Youtube) ou tags video
            if soup.find('iframe') or soup.find('video') or "youtube.com" in str(soup):
                tem_video = True
            
            # 3. Caça a Fotos
            # Conta quantas imagens tem na área de conteúdo
            # Heurística simples: se tiver mais de 2 imagens grandes, provavelmente tem foto da ocorrência
            imgs = soup.find_all('img')
            if len(imgs) > 2: 
                tem_foto = True
                
    except:
        pass # Se der erro ao entrar, retorna o padrão

    return local_encontrado, tem_foto, tem_video

# --- SCRAPERS PRINCIPAIS ---

def buscar_pcdf():
    try:
        url = "https://www.pcdf.df.gov.br/noticias"
        r = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            link = soup.find('a', href=re.compile(r'/noticias/\d+'))
            if link:
                url_final = link['href']
                if not url_final.startswith('http'): url_final = "https://www.pcdf.df.gov.br" + url_final
                titulo = link.get_text().strip()
                
                # INVESTIGAÇÃO PROFUNDA
                local, foto, video = investigar_detalhes(url_final, "pcdf")
                return titulo, url_final, local, foto, video
    except: pass
    return None, None, None, None, None

def buscar_pmdf():
    try:
        url = "https://portal.pm.df.gov.br/ocorrencias/"
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            headers = soup.find_all(['h3', 'h2', 'h4'])
            for h in headers:
                l = h.find('a')
                if l and len(l.get_text()) > 15:
                    url_final = l['href']
                    titulo = l.get_text().strip()
                    
                    # INVESTIGAÇÃO PROFUNDA
                    local, foto, video = investigar_detalhes(url_final, "pmdf")
                    return titulo, url_final, local, foto, video
    except: pass
    return None, None, None, None, None

def buscar_cbmdf():
    try:
        url = "https://www.cbm.df.gov.br/category/noticias/"
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            artigo = soup.find('h2', class_='entry-title')
            if artigo and artigo.find('a'):
                l = artigo.find('a')
                url_final = l['href']
                titulo = l.get_text().strip()
                
                # INVESTIGAÇÃO PROFUNDA
                local, foto, video = investigar_detalhes(url_final, "cbmdf")
                return titulo, url_final, local, foto, video
    except: pass
    return None, None, None, None, None

def buscar_pcgo():
    try:
        url = "https://policiacivil.go.gov.br/noticias"
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html.parser')
            manchete = soup.find('h2', class_='entry-title') or soup.find('h3', class_='entry-title')
            if manchete and manchete.find('a'):
                l = manchete.find('a')
                url_final = l['href']
                titulo = l.get_text().strip()
                
                # INVESTIGAÇÃO PROFUNDA
                local, foto, video = investigar_detalhes(url_final, "pcgo")
                return titulo, url_final, local, foto, video
    except: pass
    return None, None, None, None, None

# --- FRONT-END (VISUAL) ---

st.markdown("""
    <style>
    .card { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .titulo { font-size: 18px; font-weight: 700; color: #2c3e50; line-height: 1.4; margin-bottom: 10px; }
    .tag-local { background-color: #e1f5fe; color: #0277bd; padding: 4px 8px; border-radius: 4px; font-size: 13px; font-weight: bold; }
    .tag-midia { background-color: #ffebee; color: #c62828; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 5px; }
    .tag-video { background-color: #f3e5f5; color: #7b1fa2; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .btn-link { text-decoration: none; display: inline-block; margin-top: 10px; color: #2980b9; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📡 Radar News DF - Inteligência de Pauta")
st.markdown("**Monitoramento Oficial com Detecção de Local e Mídia**")

if st.button('🔄 RASTREAR NOVAS OCORRÊNCIAS', type="primary", use_container_width=True):
    st.rerun()

st.write("---")

col1, col2, col3, col4 = st.columns(4)

# Função auxiliar para desenhar o card
def desenhar_card(nome_fonte, icone, dados, cor_borda):
    titulo, link, local, foto, video = dados
    
    html_tags = ""
    if local != "Local não citado":
        html_tags += f'<span class="tag-local">📍 {local}</span><br><br>'
    
    if video: html_tags += '<span class="tag-video">🎥 TEM VÍDEO</span> '
    if foto: html_tags += '<span class="tag-midia">📸 TEM FOTO</span>'
    
    if not video and not foto:
        html_tags += '<span style="font-size:12px; color:#999">Apenas texto</span>'

    if titulo:
        st.success(f"{icone} {nome_fonte}: Online")
        st.markdown(f"""
        <div class="card" style="border-top: 5px solid {cor_borda}">
            {html_tags}
            <div class="titulo">{titulo}</div>
            <a href="{link}" target="_blank" class="btn-link">🔗 ABRIR MATÉRIA</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning(f"{nome_fonte} (Sem novidades)")

# --- EXIBIÇÃO ---
with col1:
    dados_pcdf = buscar_pcdf()
    desenhar_card("PCDF", "🚨", dados_pcdf, "#000000")

with col2:
    dados_pmdf = buscar_pmdf()
    desenhar_card("PMDF", "🚓", dados_pmdf, "#d32f2f")

with col3:
    dados_cbmdf = buscar_cbmdf()
    desenhar_card("BOMBEIROS", "🔥", dados_cbmdf, "#fbc02d")

with col4:
    dados_pcgo = buscar_pcgo()
    desenhar_card("PCGO", "🕵️‍♂️", dados_pcgo, "#1976d2")

st.caption(f"Dados processados às {datetime.now().strftime('%H:%M:%S')} - Varredura automática nas matérias.")