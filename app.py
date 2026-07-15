import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import os
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Orçamentos Pro - JPL Trailers",
    layout="wide",
    page_icon="🛠️"
)

# -----------------------------------------------------------------------------
# CONEXÃO COM O GOOGLE SHEETS
# -----------------------------------------------------------------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.sidebar.error(f"Erro ao inicializar conexão com Google Sheets: {e}")
    conn = None

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
    # Equipe pré-configurada da oficina
    st.session_state['df_equipe'] = pd.DataFrame([
        {"Trabalhador": "Jonatã Carvalho", "Diária (R$)": 150.0, "Alocado": True},
        {"Trabalhador": "Dantas", "Diária (R$)": 120.0, "Alocado": True},
        {"Trabalhador": "Alan", "Diária (R$)": 120.0, "Alocado": False}
    ])

# Carregamento inicial do histórico direto da planilha do Google Sheets
if 'orcamentos_db' not in st.session_state:
    st.session_state['orcamentos_db'] = {}
    if conn is not None:
        try:
            # Tenta ler a aba "Orcamentos" da planilha conectada
            df_db = conn.read(worksheet="Orcamentos", ttl=0)
            for _, row in df_db.iterrows():
                if pd.notna(row['Identificacao']) and pd.notna(row['Dados_JSON']):
                    st.session_state['orcamentos_db'][str(row['Identificacao'])] = json.loads(str(row['Dados_JSON']))
        except Exception as e:
            # Se a aba ainda não existir ou a planilha estiver limpa, inicia vazio de forma segura
            st.session_state['orcamentos_db'] = {}

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA CHAVE DA API GEMINI
# -----------------------------------------------------------------------------
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key="SUA_CHAVE_DE_TESTE_AQUI")

# -----------------------------------------------------------------------------
# INTERFACE DE HISTÓRICO E EQUIPE (BARRA LATERAL)
# -----------------------------------------------------------------------------
st.sidebar.subheader("📂 Histórico de Orçamentos")
opcoes_orcamentos = ["-- Criar Novo / Selecionar --"] + list(st.session_state['orcamentos_db'].keys())
orcamento_escolhido = st.sidebar.selectbox("Carregar projeto salvo para edição:", opcoes_orcamentos)

if orcamento_escolhido != "-- Criar Novo / Selecionar --":
    if st.sidebar.button("🔄 Carregar Dados para Edição"):
        dados = st.session_state['orcamentos_db'][orcamento_escolhido]
        
        # Repopula todas as variáveis de controle
        st.session_state['nome_empresa'] = dados.get("nome_empresa", "JPL Trailers")
        st.session_state['cnpj_cpf'] = dados.get("cnpj_cpf", "00.000.000/0001-00")
        st.session_state['responsavel'] = dados.get("responsavel", "Jonatã Carvalho")
        st.session_state['telefone'] = dados.get("telefone", "(71) 99999-9999")
        st.session_state['endereco'] = dados.get("endereco", "Salvador, Bahia")
        st.session_state['rede_social'] = dados.get("rede_social", "https://www.tiktok.com/")
        st.session_state['cliente_nome'] = dados.get("cliente_nome", "Nome do Cliente Exemplo")
        st.session_state['cliente_cpf'] = dados.get("cliente_cpf", "000.000.000-00")
        st.session_state['cliente_tel'] = dados.get("cliente_tel", "(71) 98888-8888")
        st.session_state['cliente_end'] = dados.get("cliente_end", "Salvador, Bahia")
        st.session_state['meio_pagamento'] = dados.get("meio_pagamento", "50% de entrada + 50% na entrega")
        st.session_state['observacoes_adicionais'] = dados.get("observacoes_adicionais", "")
        st.session_state['margem_lucro'] = dados.get("margem_lucro", 40)
        st.session_state['custo_almoco'] = dados.get("custo_almoco", 0.0)
        st.session_state['custo_equipamentos'] = dados.get("custo_equipamentos", 0.0)
        st.session_state['custo_deslocamento'] = dados.get("custo_deslocamento", 0.0)
        st.session_state['custo_outros'] = dados.get("custo_outros", 0.0)
        st.session_state['prazo_entrega'] = dados.get("prazo_entrega", 5)
        st.session_state['texto_cliente'] = dados.get("texto_cliente", "")
        
        st.session_state['dados_ia'] = dados.get("dados_ia", {"escopo_tecnico": "", "materiais": []})
        st.session_state['df_equipe'] = pd.DataFrame(dados.get("df_equipe", []))
        st.session_state['valor_diaria_total'] = dados.get("valor_diaria_total", 0.0)
        st.session_state['hash_diaria'] = dados.get("valor_diaria_total", 0.0)
        st.rerun()

st.sidebar.markdown("---")
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

# Cálculo imediato do custo diário dos trabalhadores marcados como Alocado
df_alocados = df_equipe_atualizado[df_equipe_atualizado["Alocado"] == True]
custo_diario_equipe_calculado = float((df_alocados["Diária (R$)"]).sum())
qtd_profissionais_alocados = len(df_alocados)

# Sincronização inteligente de valores de diária sem gerar conflitos de estado no Streamlit
if 'hash_diaria' not in st.session_state:
    st.session_state['hash_diaria'] = custo_diario_equipe_calculado
    st.session_state['valor_diaria_total'] = custo_diario_equipe_calculado

if st.session_state['hash_diaria'] != custo_diario_equipe_calculado:
    st.session_state['valor_diaria_total'] = custo_diario_equipe_calculado
    st.session_state['hash_diaria'] = custo_diario_equipe_calculado

# -----------------------------------------------------------------------------
# CONFIGURAÇÕES NA VISUALIZAÇÃO PRINCIPAL
# -----------------------------------------------------------------------------
with st.expander("⚙️ Painel de Controle e Parâmetros do Orçamento", expanded=True):
    st.header("🏢 Dados da Empresa (Cabeçalho)")
    nome_empresa = st.text_input("Nome da Empresa", value="JPL Trailers", key="nome_empresa")
    cnpj_cpf = st.text_input("CNPJ / CPF", value="00.000.000/0001-00", key="cnpj_cpf")
    responsavel = st.text_input("Nome do Responsável", value="Jonatã Carvalho", key="responsavel")
    telefone = st.text_input("Telefone / WhatsApp", value="(71) 99999-9999", key="telefone")
    endereco = st.text_input("Endereço", value="Salvador, Bahia", key="endereco")
    rede_social = st.text_input("Rede Social", value="https://www.tiktok.com/", key="rede_social")

    st.markdown("---")
    st.header("👤 Dados do Cliente")
    cliente_nome = st.text_input("Nome do Cliente", value="Nome do Cliente Exemplo", key="cliente_nome")
    cliente_cpf = st.text_input("CPF / CNPJ do Cliente", value="000.000.000-00", key="cliente_cpf")
    cliente_tel = st.text_input("WhatsApp do Cliente", value="(71) 98888-8888", key="cliente_tel")
    cliente_end = st.text_input("Endereço do Cliente", value="Salvador, Bahia", key="cliente_end")

    st.markdown("---")
    st.header("📝 Termos, Condições e Observações")
    meio_pagamento = st.text_input("Meio de Pagamento", value="50% de entrada + 50% na entrega", key="meio_pagamento")
    observacoes_adicionais = st.text_area("Observações / Garantia do Orçamento", value="Garantia de 1 ano na estrutura metálica contra defeitos de fabricação.", key="observacoes_adicionais")

    st.markdown("---")
    st.header("💰 Parâmetros Financeiros")
    
    # Campo integrado e seguro, sem duplicidade de chaves diretas
    valor_diaria_total_campo = st.number_input(
        "Custo Total da Diária (R$)", 
        value=float(st.session_state.get('valor_diaria_total', custo_diario_equipe_calculado)), 
        step=10.0,
        key="valor_diaria_total_manual"
    )
    # Atualiza a sessão conforme edição manual no campo
    st.session_state['valor_diaria_total'] = valor_diaria_total_campo
    
    margem_lucro = st.slider("Margem de Lucro (%)", min_value=10, max_value=100, value=int(st.session_state.get('margem_lucro', 40)), step=5, key="margem_lucro")

    st.markdown("---")
    st.subheader("🚀 Custos Adicionais Extra-Oficina")
    custo_almoco = st.number_input("Custo com Almoço / Alimentação (R$)", value=float(st.session_state.get('custo_almoco', 0.0)), step=10.0, key="custo_almoco")
    custo_equipamentos = st.number_input("Custo com Equipamentos / Locação externa (R$)", value=float(st.session_state.get('custo_equipamentos', 0.0)), step=10.0, key="custo_equipamentos")
    custo_deslocamento = st.number_input("Custo com Deslocamento / Frete (R$)", value=float(st.session_state.get('custo_deslocamento', 0.0)), step=10.0, key="custo_deslocamento")
    custo_outros = st.number_input("Outros Custos Adicionais (R$)", value=float(st.session_state.get('custo_outros', 0.0)), step=10.0, key="custo_outros")

# -----------------------------------------------------------------------------
# CONTEÚDO PRINCIPAL
# -----------------------------------------------------------------------------
st.title("🛠️ Sistema de Orçamentos Inteligente")
st.write("Insira a conversa do WhatsApp abaixo para extrair materiais e formatar o escopo do projeto.")

st.markdown("---")

st.subheader("Etapa 1: Resumo do Pedido (Conversa do WhatsApp)")
texto_cliente = st.text_area("Cole aqui a mensagem do cliente para a IA interpretar:", value=st.session_state.get('texto_cliente', ''), height=120, key="texto_cliente")

if st.button("🚀 Processar Texto com Inteligência Artificial"):
    if texto_cliente:
        with st.spinner("A IA está gerando a lista de materiais e estruturando o escopo técnico formal..."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = f"""
                Você é um assistente especialista em serralheria, estruturas metálicas e reboques.
                O cliente enviou a seguinte mensagem/pedido:
                "{texto_cliente}"
                
                Com base nessa mensagem, realize as seguintes tarefas:
                1. Escreva uma 'Descrição do Escopo Técnico' formal, comercial e profissional que descreva o serviço que será executado (sem gírias e bem estruturado).
                2. Identifique os materiais necessários para este serviço e estime a quantidade, unidade e um preço unitário padrão de mercado em Reais (R$).
                
                Retorne a resposta OBRIGATORIAMENTE no formato JSON abaixo:
                {{
                    "escopo_tecnico": "Texto do escopo técnico profissional aqui.",
                    "materiais": [
                        {{"Item": "Nome do Material 1", "Quantidade": 2.0, "Unidade": "barras", "Preco_Unitario": 120.0}},
                        {{"Item": "Nome do Material 2", "Quantidade": 1.0, "Unidade": "unid", "Preco_Unitario": 50.0}}
                    ]
                }}
                """
                
                # Força o Gemini a responder estritamente em formato JSON estruturado
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                texto_resposta = response.text.strip()
                
                dados_limpos = json.loads(texto_resposta)
                
                st.session_state['dados_ia']['escopo_tecnico'] = dados_limpos.get("escopo_tecnico", "Serviço personalizado de serralheria.")
                st.session_state['dados_ia']['materiais'] = dados_limpos.get("materiais", [])
                st.success("Texto interpretado com sucesso!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao processar com a IA: {e}")

st.markdown("---")

st.subheader("Etapa 2: Conferência e Ajustes")
prazo_entrega = st.number_input("Prazo de Entrega Estimado (Dias)", min_value=1, value=int(st.session_state.get('prazo_entrega', 5)), step=1, key="prazo_entrega")

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
# CÁLCULOS ATUALIZADOS COM CUSTOS OPERACIONAIS ADICIONAIS
# -----------------------------------------------------------------------------
if not df_materiais_ajustado.empty:
    df_materiais_ajustado["Total_Item"] = df_materiais_ajustado["Quantidade"] * df_materiais_ajustado["Preco_Unitario"]
    custo_total_materials = float(df_materiais_ajustado["Total_Item"].sum())
else:
    custo_total_materials = 0.0

custo_total_mao_obra = float(st.session_state['valor_diaria_total'] * prazo_entrega)
custo_extras_total = float(custo_almoco + custo_equipamentos + custo_deslocamento + custo_outros)

custo_geral_projeto = custo_total_materials + custo_total_mao_obra + custo_extras_total
preco_venda_final = custo_geral_projeto * (1 + (margem_lucro / 100))
lucro_estimado = preco_venda_final - custo_geral_projeto

st.markdown("---")

# ETAPA 3: Exibição do Orçamento Final Formatado
st.subheader("Etapa 3: Orçamento Final")

html_extras = ""
if custo_almoco > 0: html_extras += f"<li>Alimentação / Almoço: <strong>R$ {custo_almoco:,.2f}</strong></li>"
if custo_equipamentos > 0: html_extras += f"<li>Locação de Equipamentos especiais: <strong>R$ {custo_equipamentos:,.2f}</strong></li>"
if custo_deslocamento > 0: html_extras += f"<li>Logística / Deslocamento / Frete: <strong>R$ {custo_deslocamento:,.2f}</strong></li>"
if custo_outros > 0: html_extras += f"<li>Outros custos operacionais previstos: <strong>R$ {custo_outros:,.2f}</strong></li>"

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
            <li>Dimensionamento da equipe técnica alocada: <strong>{qtd_profissionais_alocados} professional(is)</strong>.</li>
            {f'<li>Custos adicionais operacionais incluídos no escopo:<ul>{html_extras}</ul></li>' if html_extras else ''}
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

if not df_materiais_ajustado.empty:
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

    <div style="margin-top: 25px; background-color: #f5f5f5; padding: 15px; border-radius: 4px; border-left: 4px solid #2e7d32;">
        <p style="margin: 0; font-size: 14px; color: #333;"><strong>💳 Condições de Pagamento:</strong> {meio_pagamento}</p>
        <p style="margin: 8px 0 0 0; font-size: 14px; color: #333;"><strong>📝 Observações:</strong> {observacoes_adicionais}</p>
    </div>

    <div style="margin-top: 30px; border-top: 2px solid #333; padding-top: 15px; text-align: right;">
        <h3 style="margin: 0; color: #111;">VALOR TOTAL DO INVESTIMENTO: <span style="color: #2e7d32;">R$ {preco_venda_final:,.2f}</span></h3>
        <p style="margin: 5px 0 0 0; font-size: 12px; font-style: italic; color: #666;">
            * Estimativa válida com base nas especificações técnicas fornecidas e insumos atuais.
        </p>
    </div>
</div>
"""

# Renderiza o HTML estruturado
st.markdown("\n".join([linha.strip() for linha in orcamento_html.split("\n")]), unsafe_allow_html=True)

st.markdown("---")

# 📥 EXPORTAR DOCUMENTO 
st.subheader("📥 Exportar Documento")

html_completo_para_impressao = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Orcamento_{cliente_nome.replace(' ', '_')}</title>
    <style>
        @media print {{
            .btn-imprimir {{ display: none !important; }}
            @page {{
                size: auto;
                margin: 0;
            }}
            body {{ 
                background-color: white !important; 
                padding: 20mm 15mm !important; 
            }}
        }}
    </style>
</head>
<body style="background-color: #f4f4f4; padding: 20px;">
    <div class="btn-imprimir" style="max-width: 900px; margin: 0 auto 20px auto; text-align: center;">
        <button onclick="window.print();" style="padding: 12px 30px; font-size: 16px; font-weight: bold; background-color: #2e7d32; color: white; border: none; border-radius: 4px; cursor: pointer; box-shadow: 0px 2px 5px rgba(0,0,0,0.2);">
            🖨️ CLIQUE AQUI PARA IMPRIMIR OU SALVAR EM PDF
        </button>
    </div>
    <div style="max-width: 900px; margin: 0 auto;">
        {orcamento_html}
    </div>
</body>
</html>
"""

st.download_button(
    label="📥 Baixar Arquivo do Orçamento (Abra e Salve como PDF)",
    data=html_completo_para_impressao,
    file_name=f"Orcamento_{cliente_nome.replace(' ', '_')}.html",
    mime="text/html"
)

# -----------------------------------------------------------------------------
# RESUMO FINANCEIRO COMPLETO E DETALHADO (MÉTRICAS)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📊 Resumo Geral e Análise de Custos Internos")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Custo Materiais", f"R$ {custo_total_materials:,.2f}")
with col2:
    st.metric("Custo Mão de Obra", f"R$ {custo_total_mao_obra:,.2f}")
with col3:
    st.metric("Custos Extras", f"R$ {custo_extras_total:,.2f}")
with col4:
    st.metric("Margem aplicada", f"{margem_lucro}%")

col5, col6 = st.columns(2)
with col5:
    st.metric("Custo Bruto Total do Projeto", f"R$ {custo_geral_projeto:,.2f}")
with col6:
    st.metric("Lucro Estimado para Oficina", f"R$ {lucro_estimado:,.2f}")

# -----------------------------------------------------------------------------
# PERSISTÊNCIA NUVEM - SALVAMENTO DE DADOS NO GOOGLE SHEETS
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("💾 Histórico da Oficina: Gravar Orçamento")
nome_projeto_salvar = st.text_input("Defina uma identificação para salvar este orçamento (Ex: Cliente - Tipo do Serviço):", value=f"{cliente_nome} - {prazo_entrega} dias")

if st.button("💾 Salvar / Atualizar no Histórico"):
    if conn is None:
        st.error("Sem conexão ativa com o Google Sheets. Verifique a configuração das credenciais no seu Secrets.")
    else:
        # Remove temporariamente a coluna visual "Total_Item" para gravar a estrutura limpa
        if 'Total_Item' in df_materiais_ajustado.columns:
            df_salvar_m = df_materiais_ajustado.drop(columns=['Total_Item'])
        else:
            df_salvar_m = df_materiais_ajustado

        # Converte dados do editor em dicionário Python de tipos puros (evita falha de serialização JSON)
        materiais_dict = []
        for m in df_salvar_m.to_dict(orient='records'):
            materiais_dict.append({
                "Item": str(m.get("Item", "")),
                "Quantidade": float(m.get("Quantidade", 0.0)),
                "Unidade": str(m.get("Unidade", "")),
                "Preco_Unitario": float(m.get("Preco_Unitario", 0.0))
            })

        equipe_dict = []
        for eq in df_equipe_atualizado.to_dict(orient='records'):
            equipe_dict.append({
                "Trabalhador": str(eq.get("Trabalhador", "")),
                "Diária (R$)": float(eq.get("Diária (R$)", 0.0)),
                "Alocado": bool(eq.get("Alocado", False))
            })

        dados_ia_atualizados = {
            "escopo_tecnico": escopo_corrigido,
            "materiais": materiais_dict
        }

        # Estruturação de gravação final
        st.session_state['orcamentos_db'][nome_projeto_salvar] = {
            "nome_empresa": nome_empresa,
            "cnpj_cpf": cnpj_cpf,
            "responsavel": responsavel,
            "telefone": telefone,
            "endereco": endereco,
            "rede_social": rede_social,
            "cliente_nome": cliente_nome,
            "cliente_cpf": cliente_cpf,
            "cliente_tel": cliente_tel,
            "cliente_end": cliente_end,
            "meio_pagamento": meio_pagamento,
            "observacoes_adicionais": observacoes_adicionais,
            "valor_diaria_total": float(st.session_state['valor_diaria_total']),
            "margem_lucro": int(margem_lucro),
            "custo_almoco": float(custo_almoco),
            "custo_equipamentos": float(custo_equipamentos),
            "custo_deslocamento": float(custo_deslocamento),
            "custo_outros": float(custo_outros),
            "prazo_entrega": int(prazo_entrega),
            "texto_cliente": texto_cliente,
            "dados_ia": dados_ia_atualizados,
            "df_equipe": equipe_dict
        }

        # Estrutura a planilha para atualização segura em formato tabular (ID, JSON_INTEGRO)
        linhas_planilha = []
        for chave, valor in st.session_state['orcamentos_db'].items():
            linhas_planilha.append({
                "Identificacao": str(chave),
                "Dados_JSON": json.dumps(valor, ensure_ascii=False)
            })
        df_salvar = pd.DataFrame(linhas_planilha)

        # Envia de forma atômica para o Google Sheets
        try:
            conn.update(worksheet="Orcamentos", data=df_salvar)
            st.success(f"Sucesso! O orçamento '{nome_projeto_salvar}' foi sincronizado na nuvem (Google Sheets).")
            st.rerun()
        except Exception as e:
            st.error(f"Falha física ao sincronizar com Google Sheets: {e}. Certifique-se de que a aba 'Orcamentos' existe na planilha conectada.")
