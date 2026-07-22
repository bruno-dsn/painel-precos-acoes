# Importar as bibliotecas
import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import date

# Configuração da página
st.set_page_config(
    page_title="Painel de Ações",
    page_icon="📈",
    layout="wide"
)

# Dicionário com algumas ações da B3 (ticker: nome da empresa)
# Fica fácil adicionar mais ações depois, só incluir uma linha nova aqui
ACOES = {
    "ITUB4.SA": "Itaú Unibanco (ITUB4)",
    "PETR4.SA": "Petrobras (PETR4)",
    "VALE3.SA": "Vale (VALE3)",
    "ABEV3.SA": "Ambev (ABEV3)",
    "BBDC4.SA": "Bradesco (BBDC4)",
    "BBAS3.SA": "Banco do Brasil (BBAS3)",
    "B3SA3.SA": "B3 (B3SA3)",
    "WEGE3.SA": "WEG (WEGE3)",
    "MGLU3.SA": "Magazine Luiza (MGLU3)",
    "ITSA4.SA": "Itaúsa (ITSA4)",
}


# Função para carregar os dados (com cache para não baixar de novo a cada clique)
# ttl="1h" evita bater no Yahoo Finance repetidas vezes em pouco tempo
@st.cache_data(ttl="1h", show_spinner="Buscando cotações no Yahoo Finance...")
def carregar_dados(tickers, data_inicio, data_fim):
    dados = yf.download(tickers, start=data_inicio, end=data_fim)["Close"]

    # Quando só tem 1 ticker, o yfinance devolve uma Series em vez de DataFrame
    if isinstance(dados, pd.Series):
        dados = dados.to_frame(name=tickers[0])

    return dados.dropna(how="all")


# ---------- Barra lateral ----------
st.sidebar.title("⚙️ Configurações")

nomes_selecionados = st.sidebar.multiselect(
    "Escolha uma ou mais ações",
    options=list(ACOES.values()),
    default=[ACOES["ITUB4.SA"]]
)

col1, col2 = st.sidebar.columns(2)
data_inicio = col1.date_input("Data inicial", value=date(2015, 1, 1), max_value=date.today())
data_fim = col2.date_input("Data final", value=date.today(), max_value=date.today())

st.sidebar.caption(
    "Fonte dos dados: Yahoo Finance, via biblioteca yfinance. "
    "Cotações de fechamento diário, não é cotação em tempo real."
)

# ---------- Área principal ----------
st.title("📈 Painel de Preços de Ações")
st.write(
    "Acompanhe a evolução do preço de algumas ações da B3. "
    "Escolha as ações e o período na barra lateral ao lado."
)

# Se nada foi selecionado, para aqui e avisa o usuário
if not nomes_selecionados:
    st.warning("Selecione ao menos uma ação na barra lateral para começar.")
    st.stop()

if data_inicio >= data_fim:
    st.error("A data inicial precisa ser anterior à data final.")
    st.stop()

# Traduz os nomes escolhidos de volta para os tickers do Yahoo Finance
tickers_selecionados = [ticker for ticker, nome in ACOES.items() if nome in nomes_selecionados]

# O Yahoo Finance às vezes limita o número de requisições (erro comum e temporário)
try:
    dados = carregar_dados(tickers_selecionados, data_inicio, data_fim)
except Exception:
    st.error(
        "Não consegui buscar os dados agora. O Yahoo Finance costuma limitar "
        "requisições vindas em sequência muito rápida — aguarde um pouco e "
        "tente novamente."
    )
    st.stop()

if dados.empty:
    st.error("Não encontrei dados para esse período. Tente outra data.")
    st.stop()

dados = dados.rename(columns=ACOES)

# ---------- Métricas rápidas (só quando 1 ação está selecionada) ----------
if len(tickers_selecionados) == 1:
    nome_acao = nomes_selecionados[0]
    serie = dados[nome_acao].dropna()

    preco_atual = serie.iloc[-1]
    preco_inicial = serie.iloc[0]
    variacao = (preco_atual / preco_inicial - 1) * 100
    maxima = serie.max()
    minima = serie.min()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Preço atual", f"R$ {preco_atual:.2f}")
    c2.metric("Variação no período", f"{variacao:.2f}%")
    c3.metric("Máxima", f"R$ {maxima:.2f}")
    c4.metric("Mínima", f"R$ {minima:.2f}")

# ---------- Gráfico ----------
st.subheader("Evolução do preço")

if len(tickers_selecionados) > 1:
    st.caption(
        "Com mais de uma ação selecionada, o gráfico mostra a variação "
        "percentual desde o início do período, para facilitar a comparação."
    )
    dados_normalizados = dados / dados.iloc[0] * 100
    st.line_chart(dados_normalizados)
else:
    st.line_chart(dados)

# ---------- Tabela de dados ----------
st.subheader("Tabela de dados")

configuracao_colunas = {
    coluna: st.column_config.NumberColumn(coluna, format="R$ %.2f")
    for coluna in dados.columns
}

st.dataframe(dados, column_config=configuracao_colunas, use_container_width=True)

csv = dados.to_csv().encode("utf-8")
st.download_button(
    "⬇️ Baixar dados em CSV",
    data=csv,
    file_name="precos_acoes.csv",
    mime="text/csv"
)

# ---------- Rodapé ----------
st.divider()
st.caption(
    "Projeto de estudo com Streamlit + yfinance, feito por Bruno Nunes · "
    "[GitHub](https://github.com/bruno-dsn) · "
    "[LinkedIn](https://www.linkedin.com/in/bruno-dsnunes/)"
)
