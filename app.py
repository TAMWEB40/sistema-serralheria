import streamlit as st
import requests
import json
import pandas as pd

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema de Orçamentos Pro - JPL Trailers", layout="wide", page_icon="🛠️")

# ---- PAINEL LATERAL: DADOS DA EMPRESA E PARÂMETROS ----
st.sidebar.header("🏢 Dados da Empresa (Cabeçalho)")
nome_empresa = st.sidebar.text_input("Nome da Empresa", "JPL Trailers")
cnpj_cpf = st.sidebar.text_input("CNPJ / CPF", "00.000.000/0001-00")
responsavel = st.sidebar.text_input("Nome do Responsável", "Jonatã Carvalho")
telefone = st.sidebar.text_input("Telefone / WhatsApp", "(71) 99999-9999")
endereco = st.sidebar.text_input("Endereço", "Salvador, Bahia")
rede_social_url = st.sidebar.text_input("Link da Rede Social (TikTok/Instagram)", "https://www.tiktok.com/")

st.sidebar.markdown("---")
st.sidebar.header("💰 Parâmetros Financeiros")
valor_diaria_total = st.sidebar.number_input("Custo Total da Diária (R$)", value=350.00, step=10.0)
margem_lucro = st.sidebar.slider("Margem de Lucro (%)", min_value=10, max_value=100, value=40, step=5)

# TÍTULO PRINCIPAL
st.title("🛠️ Sistema de Orçamentos Inteligente")
st.write("Cole a conversa do WhatsApp ou a descrição do cliente. A IA vai ler, quantificar os materiais e você confere tudo antes de gerar o preço.")

st.markdown("---")

# ---- ETAPA 1: ENTRADA DA IA ----
st.subheader("Etapa 1: Resumo do Pedido (Conversa do WhatsApp)")
texto_cliente = st.text_area(
    "Cole aqui o texto enviado pelo cliente ou os detalhes que você discutiu:",
    placeholder="Exemplo: Portão basculante de 3x2 metros na chapa 18 com social embutido, pintura automotiva e instalação no Imbuí.",
    height=150
)

# Base padrão de contingência caso a IA falhe
base_padrao = {
    "prazo_dias": 5,
    "materiais": [
        {"Item": "Ferro / Metalon / Chapa (Ajustar abaixo)", "Quantidade": 4.0, "Unidade": "barras", "Preco_Unitario": 120.0},
        {"Item": "Consumíveis (Solda / Disco de Corte)", "Quantidade": 1.0, "Unidade": "unid", "Preco_Unitario": 50.0},
        {"Item": "Tinta Automotiva / Primer", "Quantidade": 1.0, "Unidade": "lata", "Preco_Unitario": 80.0}
    ]
}

# Inicializando estados no sistema
if "dados_orcamento" not in st.session_state:
    st.session_state.dados_orcamento = base_padrao

if st.button("🚀 Processar Texto com Inteligência Artificial"):
    if not texto_cliente:
        st.warning("Por favor, digite ou cole algum texto antes de processar.")
    elif "GEMINI_API_KEY" not in st.secrets:
        st.info("🤖 Modo de Simulação Ativado (Adicione a GEMINI_API_KEY nos Secrets do Streamlit para ativar a IA real).")
    else:
        with st.spinner("Analisando o projeto e calculando materiais..."):
            try:
                api_key = st.secrets["GEMINI_API_KEY"]
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                
                prompt = f"""
                Você é um orçamentista especialista em serralheria brasileira.
                Analise o seguinte pedido: "{texto_cliente}"
                Extraia os materiais necessários e dias de trabalho em formato JSON.
                
                Responda APENAS o JSON puro, sem markdown ou explicações:
                {{
                  "prazo_dias": 5,
                  "materiais": [
                    {{"Item": "Nome do Material", "Quantidade": 2.0, "Unidade": "barras", "Preco_Unitario": 100.0}}
                  ]
                }}
                """
                
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, headers=headers, json=payload)
                response_json = response.json()
                
                # PROTEÇÃO CRUCIAL: Verifica se a resposta do Google tem o campo correto
                if 'candidates' in response_json and response_json['candidates']:
                    texto_resposta = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    if texto_resposta.startswith("```json"):
                        texto_resposta = texto_resposta.replace("```json", "").replace("```", "")
                    
                    st.session_state.dados_orcamento = json.loads(texto_resposta)
                    st.success("Texto interpretado com sucesso! Confira os dados gerados abaixo.")
                else:
                    # Se não vier 'candidates', aplica a base padrão sem quebrar a tela
                    st.session_state.dados_orcamento = base_padrao
                    st.warning("A IA gerou uma resposta incompleta. Carregamos uma planilha padrão editável para você preencher abaixo.")
                    
            except Exception as e:
                st.session_state.dados_orcamento = base_padrao
                st.warning("Não foi possível conectar com a IA temporariamente. Criamos a tabela base para você ajustar manualmente abaixo.")

st.markdown("---")

# ---- ETAPA 2: ÁREA DE CONFERÊNCIA (EDITÁVEL) ----
st.subheader("Etapa 2: Conferência e Ajustes")
st.write("Altere qualquer valor abaixo se achar necessário. A IA sugere, mas quem dá a palavra final é você.")

prazo_final = st.number_input("Prazo de Entrega Estimado (Dias)", value=int(st.session_state.dados_orcamento.get("prazo_dias", 5)), min_value=1)

df_materiais_original = pd.DataFrame(st.session_state.dados_orcamento.get("materiais"))

st.write("**Lista de Materiais Necessários (Dê um duplo clique na célula para alterar quantidade ou preço):**")
df_editado = st.data_editor(df_materiais_original, num_rows="dynamic", use_container_width=True)

st.markdown("---")

# ---- ETAPA 3: CÁLCULOS E EXIBIÇÃO DE RESULTADOS ----
st.subheader("Etapa 3: Orçamento Final")

df_editado["Total_Item"] = df_editado["Quantidade"] * df_editado["Preco_Unitario"]
custo_materiais_total = float(df_editado["Total_Item"].sum())
custo_mao_de_obra_total = float(prazo_final * valor_diaria_total)

custo_total_producao = custo_materiais_total + custo_mao_de_obra_total
preco_final_cliente = custo_total_producao * (1 + (margem_lucro / 100))
lucro_liquido_empresa = preco_final_cliente - custo_total_producao

tab_cliente, tab_interna = st.tabs(["👤 VISÃO DO CLIENTE (O que enviar)", "🛠️ VISÃO DA EMPRESA (O que só você vê)"])

with tab_cliente:
    st.markdown(f"### 📄 ORÇAMENTO DE SERVIÇO")
    
    st.info(f"""
    **{nome_empresa}** *Responsável:* {responsavel} | *CNPJ/CPF:* {cnpj_cpf}  
    *Contato / WhatsApp:* {telefone} | *Local:* {endereco}  
    🌐 [Siga nossa Rede Social no TikTok / Instagram]({rede_social_url})
    """)
    
    st.write(f"**Descrição do Escopo:** {texto_cliente if texto_cliente else 'Projeto sob medida em serralheria.'}")
    st.write(f"**Prazo de Entrega:** {prazo_final} dias úteis após aprovação.")
    
    st.markdown("---")
    st.markdown(f"## 💰 Valor Total do Investimento: **R$ {preco_final_cliente:,.2f}**")
    st.write("*Condições de pagamento: A combinar com o responsável técnico.*")

with tab_interna:
    st.markdown("### 📊 Painel de Custos Internos e Lucro")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gastos com Material", f"R$ {custo_materials_total:,.2f}")
    col2.metric("Pagamento de Diárias", f"R$ {custo_mao_de_obra_total:,.2f}")
    col3.metric("Lucro Líquido Limpo", f"R$ {lucro_liquido_empresa:,.2f}", delta=f"{margem_lucro}% Margem")
    
    st.write("---")
    st.write("📋 **Lista de Compras Pronta para Enviar ao Fornecedor:**")
    
    texto_copiar = ""
    for _, linha in df_editado.iterrows():
        unidade_txt = linha['Unidade'] if 'Unidade' in df_editado.columns else 'unid'
        texto_copiar += f"- {linha['Quantidade']} {unidade_txt} de {linha['Item']}\n"
        
    st.text_area("Copie a lista abaixo e mande direto para a distribuidora de ferro:", value=texto_copiar, height=120)
