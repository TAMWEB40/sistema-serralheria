import streamlit as st
from datetime import datetime

# Configuração da página para rodar perfeitamente em Celular e Notebook
st.set_page_config(page_title="Serralharia Pro", page_icon="🛠️", layout="centered")

# Ocultar menus padrões do Streamlit para o PDF ficar limpo na impressão
esconder_elementos = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none !important;}
    </style>
"""
st.markdown(esconder_elementos, unsafe_allow_html=True)

# --- BANCO DE DADOS DE PREÇOS DE REFERÊNCIA POR M² ---
# Você pode alterar esses valores de custo e horas direto aqui no código depois
PRECOS_M2_REFERENCIA = {
    "Cobertura (Estrutura + Telha Simples)": {"material": 140.0, "horas": 0.6},
    "Cobertura (Estrutura + Telha Sanduíche)": {"material": 240.0, "horas": 0.8},
    "Portão Basculante (Fechado/Chapa)": {"material": 260.0, "horas": 1.5},
    "Portão Deslizante Gradeado": {"material": 160.0, "horas": 1.0},
    "Estrutura Metálica p/ Galpão": {"material": 310.0, "horas": 1.2},
    "Corrimão / Guarda-Corpo (Metro Linear)": {"material": 90.0, "horas": 0.8}
}

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Sistema de Orçamentos Serralheria")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar no Sistema"):
        if usuario == "admin" and senha == "serralheiro123":
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    st.stop()

# --- ESTADO DO MODO DE IMPRESSÃO ---
if "modo_impressao" not in st.session_state:
    st.session_state["modo_impressao"] = False

# --- SE NÃO ESTIVER NO MODO IMPRESSÃO: MOSTRA O PAINEL DE CÁLCULO ---
if not st.session_state["modo_impressao"]:
    st.title("🛠️ Serralheria Pro")
    st.write("Gere orçamentos rápidos, precisos e profissionais.")
    
    aba = st.radio("Selecione o Modo de Orçamento:", ["Por Metro Quadrado (m²)", "Por Itens Detalhados"], horizontal=True)

    # Painel Lateral de Custos Fixos
    st.sidebar.header("⚙️ Custos Fixos da Oficina")
    VALOR_HORA = st.sidebar.number_input("Valor da sua Hora (R$)", value=50.0, step=5.0)
    TAXA_CONSUMIVEIS = st.sidebar.slider("Taxa de Consumíveis (Discos/Solda) %", 0, 15, 5)

    st.subheader("📋 Dados do Cliente e Serviço")
    nome_cliente = st.text_input("Nome do Cliente", value="Cliente Padrão")
    tipo_servico = st.selectbox("Tipo de Serviço", ["Cobertura", "Estrutura Metálica", "Portão", "Grades/Esquadrias", "Outros"])
    descricao_detalhada = st.text_area("Descrição detalhada do que será feito", placeholder="Ex: Fabricação de portão basculante em chapa 18 com social embutido...")

    custo_material_total = 0.0
    horas_estimadas_total = 0.0
    detalhe_modelo = ""

    if aba == "Por Metro Quadrado (m²)":
        st.subheader("📐 Cálculo por Área")
        modelo = st.selectbox("Selecione o Modelo Padrão:", list(PRECOS_M2_REFERENCIA.keys()))
        detalhe_modelo = modelo
        
        col1, col2 = st.columns(2)
        with col1:
            largura = st.number_input("Largura / Frente (metros)", value=1.0, min_value=0.1, step=0.5)
        with col2:
            comprimento = st.number_input("Comprimento / Altura (metros)", value=1.0, min_value=0.1, step=0.5)
        
        area = largura * comprimento
        st.info(f"📐 Área Total: **{area:.2f} m²**")
        
        custo_material_total = area * PRECOS_M2_REFERENCIA[modelo]["material"]
        horas_estimadas_total = area * PRECOS_M2_REFERENCIA[modelo]["horas"]
    else:
        st.subheader("🔩 Cálculo Detalhado (Peça por Peça)")
        custo_material_total = st.number_input("Custo Bruto Total dos Materiais (R$)", value=0.0, step=50.0)
        horas_estimadas_total = st.number_input("Horas Estimadas de Trabalho (Total)", value=0.0, step=1.0)

    st.subheader("🚚 Custos Extras e Margem")
    col3, col4 = st.columns(2)
    with col3:
        deslocamento = st.number_input("Frete / Deslocamento (R$)", value=0.0, step=10.0)
    with col4:
        equipamentos = st.number_input("Equipamentos Extras (R$)", value=0.0, step=10.0)

    margem_lucro = st.slider("Margem de Lucro Desejada (%)", 10, 150, 40)

    # --- PROCESSAMENTO DOS CÁLCULOS ---
    consumiveis_calculado = custo_material_total * (TAXA_CONSUMIVEIS / 100)
    custo_material_final = custo_material_total + consumiveis_calculado
    mao_de_obra_calculada = horas_estimadas_total * VALOR_HORA
    custo_total_producao = custo_material_final + mao_de_obra_calculada + deslocamento + equipamentos
    
    fator_margem = 1 + (margem_lucro / 100)
    preco_final_cliente = custo_total_producao * fator_margem

    # --- SALVAR NA SESSÃO PARA GERAR O PDF ---
    st.session_state["dados_orcamento"] = {
        "cliente": nome_cliente,
        "servico": tipo_servico,
        "descricao": descricao_detalhada,
        "modelo": detalhe_modelo,
        "total": preco_final_cliente,
        "data": datetime.now().strftime("%d/%m/%Y")
    }

    # Painel de Resumo Oculto para o Serralheiro
    st.markdown("---")
    st.subheader("💰 Resumo Interno (Só você enxerga)")
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.write(f"**Materiais + Consumíveis:** R$ {custo_material_final:.2f}")
        st.write(f"**Mão de Obra ({horas_estimadas_total:.1f}h):** R$ {mao_de_obra_calculada:.2f}")
        st.write(f"**Logística e Extras:** R$ {(deslocamento + equipamentos):.2f}")
        st.write(f"📉 **Custo Real de Produção:** R$ {custo_total_producao:.2f}")
        st.write(f"💵 **Seu Lucro Líquido:** R$ {(preco_final_cliente - custo_total_producao):.2f}")
    with col_res2:
        st.success(f"### Preço para o Cliente:\n## R$ {preco_final_cliente:.2f}")

    # Botões de Ação
    st.markdown("---")
    if st.button("📄 Gerar Visualização em PDF para o Cliente"):
        st.session_state["modo_impressao"] = True
        st.rerun()

# --- MODO DE IMPRESSÃO: MONTA A FOLHA LIMPA DO ORÇAMENTO ---
else:
    dados = st.session_state["dados_orcamento"]
    
    # Layout da Folha de Orçamento
    st.markdown("### 🛠️ J&L METALURGICA E SERRALHERIA")
    st.write("Salvador - BA | Contato via WhatsApp")
    st.markdown("---")
    
    st.subheader("📄 ORÇAMENTO DE SERVIÇO")
    st.write(f"**Data de Emissão:** {dados['data']}")
    st.write(f"**Validade da Proposta:** 10 dias")
    st.write(f"**Cliente:** {dados['cliente']}")
    st.write(f"**Tipo de Projeto:** {dados['servico']} {f'({dados['modelo']})' if dados['modelo'] else ''}")
    
    st.markdown("**Descrição dos Serviços:**")
    if dados['descricao']:
        st.info(dados['descricao'])
    else:
        st.write("Fabricação e instalação conforme especificações combinadas com o cliente.")
        
    st.markdown("---")
    st.markdown(f"## VALOR TOTAL DO INVESTIMENTO:\n# R$ {dados['total']:.2f}")
    st.markdown("---")
    
    st.caption("⚙️ **Termos e Condições:**\n"
               "- Incluso materiais descritos, fabricação, solda, acabamento e instalação padrão.\n"
               "- Qualquer alteração no projeto original após aprovação alterará o valor final.\n"
               "- Forma de pagamento a combinar.")

    # Botões para voltar ou acionar comando de impressão
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("⬅️ Voltar e Editar"):
            st.session_state["modo_impressao"] = False
            st.rerun()
    with col_btn2:
        st.write("💡 *Para salvar em PDF, clique nos 3 pontinhos do seu navegador (Chrome/Safari), vá em 'Compartilhar' ou 'Imprimir' e escolha 'Salvar como PDF'.*")
