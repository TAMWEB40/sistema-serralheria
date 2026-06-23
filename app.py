import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from fpdf import FPDF

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Sistema de Orçamentos Pro - JPL Trailers", layout="wide", page_icon="🛠️")

# FUNÇÃO PARA GERAR O ORÇAMENTO EM PDF
def gerar_pdf(dados_empresa, escopo, prazo, total_geral, qtd_trab, valor_diaria):
    pdf = FPDF()
    pdf.add_page()
    
    # Função interna auxiliar para tratar acentuação padrão brasileira no FPDF
    def tratar_texto(texto):
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    # Cabeçalho da Empresa
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, tratar_texto(dados_empresa['nome'].upper()), ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, tratar_texto(f"CNPJ / CPF: {dados_empresa['cnpj']} | Contato/WhatsApp: {dados_empresa['whatsapp']}"), ln=True, align="C")
    pdf.cell(0, 5, tratar_texto(f"Responsável Técnico: {dados_empresa['responsavel']} | Localidade: {dados_empresa['endereco']}"), ln=True, align="C")
    pdf.ln(10)
    
    # Linha Divisória Visual
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Título do Documento
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, tratar_texto("ORÇAMENTO FORMAL DE SERVIÇO"), ln=True, align="L")
    pdf.ln(3)
    
    # Descrição do Escopo do Projeto
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, tratar_texto("1. Descrição do Escopo Técnico:"), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, tratar_texto(escopo))
    pdf.ln(5)
    
    # Detalhamento de Execução e Prazos
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, tratar_texto("2. Cronograma e Recursos Estimados:"), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, tratar_texto(f"- Período de execução estimado: {prazo} dias úteis."), ln=True)
    pdf.cell(0, 6, tratar_texto(f"- Dimensionamento da equipe técnica alocada: {qtd_trab} profissional(is)."), ln=True)
    pdf.ln(8)
    
    # Linha Divisória de Fechamento Financeiro
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    # Valor de Investimento Total do Cliente
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, tratar_texto(f"VALOR TOTAL DO INVESTIMENTO: R$ {total_geral:,.2f}"), ln=True)
    
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 6, tratar_texto("* Condições de pagamento padrão: A combinar diretamente com o responsável técnico."), ln=True)
    pdf.cell(0, 5, tratar_texto("* Este documento é uma estimativa com base nas dimensões e parâmetros informados."), ln=True)
    
    return pdf.output()


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

# Campos atualizados para dimensionamento manual da equipe
qtd_trabalhadores = st.sidebar.number_input("Quantidade de Trabalhadores", min_value=1, value=1, step=1)
valor_diaria_individual = st.sidebar.number_input("Valor da Diária por Trabalhador (R$)", min_value=0.0, value=150.0, step=10.0)

# Multiplicação automática para gerar a diária operacional completa
valor_diaria_total = float(qtd_trabalhadores * valor_diaria_individual)
st.sidebar.info(f"💵 Custo Diário da Equipe: R$ {valor_diaria_total:.2f}")

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

# Base padrão de segurança caso a IA falhe
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
        with st.spinner("Analisando o projeto com a inteligência artificial do Google..."):
            try:
                # Configura a chave de forma limpa
                api_key_limpa = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
                genai.configure(api_key=api_key_limpa)
                
                prompt = f"""
                Você é um mestre orçamentista de serralheria experiente no mercado brasileiro. Analise o seguinte pedido de serviço: "{texto_cliente}"
                
                Gere uma estimativa realista com os materiais necessários (itens como metalon, tubos, chapas, eletrodos, discos de corte ou tintas), quantidades prováveis, unidade de medida correspondente, preço unitário estimado e o prazo total de fabricação em dias.
                
                Siga exatamente esta estrutura JSON:
                {{
                  "prazo_dias": 4,
                  "materiais": [
                    {{"Item": "Metalon 40x40 Chapa 18", "Quantidade": 3.0, "Unidade": "barras", "Preco_Unitario": 95.0}},
                    {{"Item": "Disco de Corte 4.1/2", "Quantidade": 2.0, "Unidade": "unid", "Preco_Unitario": 7.0}}
                  ]
                }}
                """
                
                # Chamada com o modelo correto e configuração nativa para JSON estruturado
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                texto_resposta = response.text.strip()
                
                st.session_state.dados_orcamento = json.loads(texto_resposta)
                st.success("Texto interpretado com sucesso! Confira e ajuste os dados gerados na tabela abaixo.")
                
            except Exception as e:
                st.session_state.dados_orcamento = base_padrao
                st.error(f"Aviso técnico: A IA respondeu fora do padrão estrutural. Siga ajustando manualmente na tabela abaixo se necessário.")

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

# Força conversão para tipos numéricos evitando erros de exibição
df_editado["Quantidade"] = pd.to_numeric(df_editado["Quantidade"], errors='coerce').fillna(0)
df_editado["Preco_Unitario"] = pd.to_numeric(df_editado["Preco_Unitario"], errors='coerce').fillna(0)

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
    **{nome_empresa}** | *Responsável:* {responsavel} | *CNPJ/CPF:* {cnpj_cpf}  
    *Contato / WhatsApp:* {telefone} | *Local:* {endereco}  
    🌐 [Siga nossa Rede Social no TikTok / Instagram]({rede_social_url})
    """)
    
    st.write(f"**Descrição do Escopo:** {texto_cliente if texto_cliente else 'Projeto sob medida em serralheria.'}")
    st.write(f"**Prazo de Entrega:** {prazo_final} dias úteis após aprovação.")
    
    st.markdown("---")
    st.markdown(f"## 💰 Valor Total do Investimento: **R$ {preco_final_cliente:,.2f}**")
    st.write("*Condições de pagamento: A combinar com o responsável técnico.*")
    
    # SEÇÃO PARA EXPORTAÇÃO EM PDF OFICIAL
    st.markdown("---")
    st.subheader("📥 Exportar Documento para o WhatsApp")
    
    dados_empresa_pdf = {
        "nome": nome_empresa,
        "cnpj": cnpj_cpf,
        "responsavel": responsavel,
        "whatsapp": telefone,
        "endereco": endereco
    }
    
    try:
        # Montagem do PDF utilizando os bytes em memória do Streamlit
        pdf_gerado_bytes = gerar_pdf(
            dados_empresa=dados_empresa_pdf,
            escopo=texto_cliente if texto_cliente else 'Projeto sob medida em serralheria.',
            prazo=prazo_final,
            total_geral=preco_final_cliente,
            qtd_trab=qtd_trabalhadores,
            valor_diaria=valor_diaria_individual
        )
        
        st.download_button(
            label="📥 Baixar Orçamento Oficial em PDF",
            data=bytes(pdf_gerado_bytes),
            file_name=f"Orcamento_JPL_{responsavel.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as erro_pdf:
        st.error(f"Erro ao processar arquivo PDF: {erro_pdf}")

with tab_interna:
    st.markdown("### 📊 Painel de Custos Internos e Lucro")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gastos com Material", f"R$ {custo_materiais_total:,.2f}")
    col2.metric("Pagamento de Diárias", f"R$ {custo_mao_de_obra_total:,.2f}")
    col3.metric("Lucro Líquido Limpo", f"R$ {lucro_liquido_empresa:,.2f}", delta=f"{margem_lucro}% Margem")
    
    st.write("---")
    st.write("📋 **Lista de Compras Pronta para Enviar ao Fornecedor:**")
    
    texto_copiar = ""
    for _, linha in df_editado.iterrows():
        unidade_txt = linha['Unidade'] if 'Unidade' in df_editado.columns else 'unid'
        texto_copiar += f"- {linha['Quantidade']} {unidade_txt} de {linha['Item']}\n"
        
    st.text_area("Copie a lista abaixo e mande direto para a distribuidora de ferro:", value=texto_copiar, height=120)
