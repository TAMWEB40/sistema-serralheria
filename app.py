import streamlit as st
import google.generativeai as genai
import json
import pandas as pd

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Orçamentos Pro - JPL Trailers",
    layout="wide",
    page_icon="🛠️"
)

# -----------------------------------------------------------------------------
# INICIALIZAÇÃO DO ESTADO DA SESSÃO (SESSION STATE)
# -----------------------------------------------------------------------------
if 'dados_ia' not in st.session_state:
    st.session_state['dados_ia'] = {
        'escopo_tecnico': "Aguardando processamento do pedido...",
        'materiais': [
            {"Item": "Ferro / Metalon / Chapa (Ajustar abaixo)", "Quantidade": 4.0, "Unidade": "barras", "Preco_Unitario": 120.0},
            {"Item": "Consumíveis (Solda / Disco de Corte)", "Quantidade": 1.0, "Unidade": "unid", "Preco_Unitario": 50.0},
            {"Item": "Tinta Automotiva / Primer", "Quantidade": 1.0, "Unidade": "lata", "Preco_Unitario": 80.0}
        ]
    }

if 'df_equipe' not in st.session_state:
    # Sua equipe pré-configurada da oficina
    st.session_state['df_equipe'] = pd.DataFrame([
        {"Trabalhador": "Jonatã Carvalho", "Diária (R$)": 150.0, "Alocado": True},
        {"Trabalhador": "Dantas", "Diária (R$)": 120.0, "Alocado": True},
        {"Trabalhador": "Ezequiel", "Diária (R$)": 120.0, "Alocado": False}
    ])

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA CHAVE DA API GEMINI
# -----------------------------------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key="SUA_CHAVE_DE_TESTE_AQUI")

# -----------------------------------------------------------------------------
# ---- PAINEL DE CONFIGURAÇÕES NA VISUALIZAÇÃO PRINCIPAL ----
with st.expander("⚙️ Painel de Controle e Parâmetros do Orçamento", expanded=True):
    
    st.header("🏢 Dados da Empresa (Cabeçalho)")
    nome_empresa = st.text_input("Nome da Empresa", "JPL Trailers")
    cnpj_cpf = st.text_input("CNPJ / CPF", "00.000.000/0001-00")
    responsavel = st.text_input("Nome do Responsável", "Jonatã Carvalho")
    telefone = st.text_input("Telefone / WhatsApp", "(71) 99999-9999")
    endereco = st.text_input("Endereço", "Salvador, Bahia")
    rede_social = st.text_input("Rede Social", "https://www.tiktok.com/")

    st.markdown("---")
    st.header("👤 Dados do Cliente")
    cliente_nome = st.text_input("Nome do Cliente", "Nome do Cliente Exemplo")
    cliente_cpf = st.text_input("CPF / CNPJ do Cliente", "000.000.000-00")
    cliente_tel = st.text_input("WhatsApp do Cliente", "(71) 98888-8888")
    cliente_end = st.text_input("Endereço do Cliente", "Salvador, Bahia")

    st.markdown("---")
    st.header("💰 Parâmetros Financeiros")
    valor_diaria_total = st.number_input("Custo Total da Diária (R$)", value=350.00, step=10.0)
    margem_lucro = st.slider("Margem de Lucro (%)", min_value=10, max_value=100, value=40, step=5)

# NOVO: Tabela dinâmica de diárias por trabalhador
st.sidebar.subheader("👷 Equipe e Mão de Obra")
df_equipe_atualizado = st.sidebar.data_editor(
    st.session_state['df_equipe'],
    column_config={
        "Alocado": st.column_config.CheckboxColumn("Alocado?", default=True),
        "Diária (R$)": st.column_config.NumberColumn("Diária (R$)", min_value=0.0, format="R$ %.2f"),
        "Trabalhador": st.column_config.TextColumn("Nome do Profissional")
    },
    num_rows="dynamic",
    key="editor_equipe_v2"
)
st.session_state['df_equipe'] = df_equipe_atualizado

# -----------------------------------------------------------------------------
# CONTEÚDO PRINCIPAL
# -----------------------------------------------------------------------------
st.title("🛠️ Sistema de Orçamentos Inteligente")
st.write("Insira a conversa do WhatsApp abaixo para extrair materiais e formatar o escopo do projeto.")

st.markdown("---")

st.subheader("Etapa 1: Resumo do Pedido (Conversa do WhatsApp)")
texto_cliente = st.text_area("Cole aqui a mensagem do cliente para a IA interpretar:", height=120)

if st.button("🚀 Processar Texto com Inteligência Artificial"):
    if texto_cliente:
        with st.spinner("A IA está gerando a lista de materiais e estruturando o escopo técnico formal..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Prompt otimizado para separar escopo técnico da mensagem bruta
                prompt = f"""
                Você é um assistente especialista em serralheria, estruturas metálicas e reboques.
                O cliente enviou a seguinte mensagem/pedido:
                "{texto_cliente}"
                
                Com base nessa mensagem, realize as seguintes tarefas:
                1. Escreva uma 'Descrição do Escopo Técnico' formal, comercial e profissional que descreva o serviço que será executado (sem gírias e bem estruturado).
                2. Identifique os materiais necessários para este serviço e estime a quantidade, unidade e um preço unitário padrão de mercado em Reais (R$).
                
                Retorne a resposta OBRIGATORIAMENTE no formato JSON abaixo, sem qualquer outro texto explicativo antes ou depois:
                {{
                    "escopo_tecnico": "Texto do escopo técnico profissional aqui.",
                    "materiais": [
                        {{"Item": "Nome do Material 1", "Quantidade": 2.0, "Unidade": "barras", "Preco_Unitario": 120.0}},
                        {{"Item": "Nome do Material 2", "Quantidade": 1.0, "Unidade": "unid", "Preco_Unitario": 50.0}}
                    ]
                }}
                """
                
                response = model.generate_content(prompt)
                texto_resposta = response.text.strip()
                
                if "```json" in texto_resposta:
                    texto_resposta = texto_resposta.split("```json")[1].split("```")[0].strip()
                elif "```" in texto_resposta:
                    texto_resposta = texto_resposta.split("```")[1].split("```")[0].strip()
                
                dados_limpos = json.loads(texto_resposta)
                
                st.session_state['dados_ia']['escopo_tecnico'] = dados_limpos.get("escopo_tecnico", "Serviço personalizado de serralheria.")
                st.session_state['dados_ia']['materiais'] = dados_limpos.get("materiais", [])
                st.success("Texto interpretado com sucesso!")
                
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

st.markdown("---")

st.subheader("Etapa 2: Conferência e Ajustes")
prazo_entrega = st.number_input("Prazo de Entrega Estimado (Dias)", min_value=1, value=5, step=1)

# AJUSTADO: Campo de texto livre para você refinar o escopo técnico trazido pela IA
escopo_corrigido = st.text_area(
    "📝 Descrição do Escopo Técnico (Editável):", 
    value=st.session_state['dados_ia']['escopo_tecnico'],
    height=100
)

st.write("📋 **Lista de Materiais Necessários** (Ajuste quantidades ou preços dando duplo clique):")
df_materiais = pd.DataFrame(st.session_state['dados_ia']['materiais'])

df_materiais_ajustado = st.data_editor(
    df_materiais,
    column_config={
        "Quantidade": st.column_config.NumberColumn("Quantidade", min_value=0.0, format="%.2f"),
        "Preco_Unitario": st.column_config.NumberColumn("Preço Unitário (R$)", min_value=0.0, format="R$ %.2f"),
        "Unidade": st.column_config.TextColumn("Unidade"),
        "Item": st.column_config.TextColumn("Item / Material")
    },
    num_rows="dynamic",
    key="editor_materiais_v2"
)

# -----------------------------------------------------------------------------
# CÁLCULOS
# -----------------------------------------------------------------------------
df_materiais_ajustado["Total_Item"] = df_materiais_ajustado["Quantidade"] * df_materiais_ajustado["Preco_Unitario"]
custo_total_materiais = float(df_materiais_ajustado["Total_Item"].sum())

# Soma das diárias apenas dos trabalhadores ativos/marcados na tabela lateral
df_alocados = df_equipe_atualizado[df_equipe_atualizado["Alocado"] == True]
custo_diario_equipe = float((df_alocados["Diária (R$)"]).sum())
custo_total_mao_obra = custo_diario_equipe * prazo_entrega
qtd_profissionais_alocados = len(df_alocados)

custo_geral_projeto = custo_total_materiais + custo_total_mao_obra
preco_venda_final = custo_geral_projeto * (1 + (margem_lucro / 100))

st.markdown("---")

# ETAPA 3: Exibição do Orçamento Final Formatado
st.subheader("Etapa 3: Orçamento Final")

orcamento_html = f"""
<div style="background-color: white; padding: 30px; border: 1px solid #d3d3d3; border-radius: 5px; color: black; font-family: Arial, sans-serif;">
    
    <div style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 15px;">
        <h2 style="margin: 0; color: #111;">{nome_empresa.upper()}</h2>
        <p style="margin: 5px 0; font-size: 13px; color: #555;">
            CNPJ/CPF: {cnpj_cpf} | Contato/WhatsApp: {telefone}<br>
            Responsável Técnico: {responsavel} | Localidade: {endereco}<br>
            Rede Social: {rede_social}
        </p>
    </div>
    
    <div style="margin-top: 20px; background-color: #f9f9f9; padding: 12px; border-radius: 4px; border-left: 4px solid #007acc;">
        <h4 style="margin: 0 0 8px 0; color: #007acc;">DADOS DO CLIENTE</h4>
        <table style="width: 100%; font-size: 13px; color: #333;">
            <tr>
                <td style="width: 50%;"><strong>Cliente:</strong> {cliente_nome}</td>
                <td style="width: 50%;"><strong>CPF/CNPJ:</strong> {cliente_cpf}</td>
            </tr>
            <tr>
                <td style="width: 50%;"><strong>WhatsApp:</strong> {cliente_tel}</td>
                <td style="width: 50%;"><strong>Endereço:</strong> {cliente_end}</td>
            </tr>
        </table>
    </div>

    <h3 style="text-align: center; margin-top: 25px; letter-spacing: 1px; color: #222;">ORÇAMENTO FORMAL DE SERVIÇO</h3>
    
    <div style="margin-top: 15px;">
        <h4 style="margin-bottom: 5px; color: #111;">1. Descrição do Escopo Técnico:</h4>
        <p style="font-size: 14px; line-height: 1.5; margin: 0; color: #333; text-align: justify;">
            {escopo_corrigido}
        </p>
    </div>
    
    <div style="margin-top: 20px;">
        <h4 style="margin-bottom: 5px; color: #111;">2. Cronograma e Recursos Estimados:</h4>
        <ul style="font-size: 14px; margin: 0; padding-left: 20px; color: #333;">
            <li>Período de execução estimado: <strong>{prazo_entrega} dias úteis</strong>.</li>
            <li>Dimensionamento da equipe técnica alocada: <strong>{qtd_profissionais_alocados} profissional(is)</strong>.</li>
        </ul>
    </div>
    
    <div style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px;">
        <h4 style="margin-bottom: 8px; color: #111;">Resumo dos Componentes do Projeto:</h4>
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
            <thead>
                <tr style="background-color: #f2f2f2; border-bottom: 1px solid #ddd;">
                    <th style="padding: 6px;">Item</th>
                    <th style="padding: 6px;">Qtd</th>
                    <th style="padding: 6px;">Unidade</th>
                </tr>
            </thead>
            <tbody>
"""

for _, row in df_materiais_ajustado.iterrows():
    orcamento_html += f"""
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 6px; color: #444;">{row['Item']}</td>
                    <td style="padding: 6px; color: #444;">{row['Quantidade']:.2f}</td>
                    <td style="padding: 6px; color: #444;">{row['Unidade']}</td>
                </tr>
    """

orcamento_html += f"""
            </tbody>
        </table>
    </div>

    <div style="margin-top: 30px; border-top: 2px solid #333; padding-top: 15px; text-align: right;">
        <h3 style="margin: 0; color: #111;">VALOR TOTAL DO INVESTIMENTO: <span style="color: #2e7d32;">R$ {preco_venda_final:,.2f}</span></h3>
        <p style="margin: 5px 0 0 0; font-size: 12px; font-style: italic; color: #666;">
            * Condições de pagamento: A combinar diretamente com a gerência.<br>
            * Estimativa válida com base nas especificações técnicas fornecidas.
        </p>
    </div>
</div>
"""

st.markdown("\n".join([linha.strip() for linha in orcamento_html.split("\n")]), unsafe_allow_html=True)

# Indicadores informativos de conferência rápida
st.subheader(f"💰 Resumo Geral: R$ {preco_venda_final:,.2f}")
st.write(f"*(Custo Materiais: R$ {custo_total_materiais:,.2f} | Custo Mão de Obra total: R$ {custo_total_mao_obra:,.2f} | Margem: {margem_lucro}%)*")
