import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib3
import re
from datetime import datetime
import pytz

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Pauta Fácil - Diagnóstico", layout="wide", page_icon="🛠️")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CABEÇALHOS PARA TENTAR BURLAR O BLOQUEIO ---
# Tentamos parecer um navegador brasileiro comum
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

# --- FUNÇÃO DE DIAGNÓSTICO ---
def buscar_com_diagnostico(url, nome_fonte):
    """ Tenta acessar e retorna o STATUS exato (Sucesso ou Erro) """
    try:
        # Timeout curto para não travar
        r = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'lxml') # Usando lxml que é mais forte
            
            # Tenta achar qualquer link para provar que leu
            links = soup.find_all('a', href=True)
            if len(links) > 0:
                # Retorna sucesso e o título do primeiro link relevante encontrado
                for link in links:
                    txt = link.get_text().strip()
                    if len(txt) > 20:
                        return "SUCESSO", f"Leu: {txt[:40]}...", url
                return "SUCESSO", "Site lido, mas nenhum título longo achado.", url
            else:
                return "ALERTA", "Site abriu, mas não tem links (Bloqueio de script?)", url
        
        elif r.status_code == 403:
            return "BLOQUEADO", "Erro 403: O site recusou a conexão (Provável bloqueio de IP Gringo)", url
        elif r.status_code == 406:
            return "BLOQUEADO", "Erro 406: O site não aceitou nosso 'User-Agent'", url
        else:
            return "ERRO", f"Status Code: {r.status_code}", url

    except requests.exceptions.ConnectTimeout:
        return "TIMEOUT", "O site demorou demais para responder (Bloqueio silencioso)", url
    except requests.exceptions.ConnectionError:
        return "ERRO REDE", "Falha de conexão direta", url
    except Exception as e:
        return "ERRO CRÍTICO", str(e), url

# --- FRONT-END ---
st.title("🛠️ Painel de Diagnóstico de Conexão")
st.warning("Este painel serve para descobrir por que os sites não estão carregando.")

if st.button("RODAR DIAGNÓSTICO", type="primary"):
    
    col1, col2 = st.columns(2)
    
    # Lista de sites para testar
    sites = [
        ("PCDF", "https://www.pcdf.df.gov.br/noticias"),
        ("PMDF", "https://portal.pm.df.gov.br/ocorrencias/"),
        ("PCGO", "https://policiacivil.go.gov.br/noticias"),
        ("Metrópoles", "https://www.metropoles.com/distrito-federal")
    ]
    
    for nome, url in sites:
        status, msg, link = buscar_com_diagnostico(url, nome)
        
        cor = "green" if status == "SUCESSO" else "red"
        icone = "✅" if status == "SUCESSO" else "❌"
        
        st.markdown(f"""
        <div style="padding:15px; border-radius:10px; background:white; border-left: 5px solid {cor}; margin-bottom:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
            <strong>{icone} {nome}</strong><br>
            <span style="font-size:12px; font-family:monospace;">{msg}</span>
        </div>
        """, unsafe_allow_html=True)
