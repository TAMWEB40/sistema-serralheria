import streamlit as st
import google.generativeai as genai

# Configuração correta da chave de API
# Dica: No Streamlit Cloud, configure a sua chave nos "Secrets" como GEMINI_API_KEY
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key="SUA_CHAVE_DE_TESTE_AQUI")

# --- Dentro da Etapa 1, quando o utilizador clica no botão de processar ---
texto_cliente = st.text_area("Cole aqui o texto enviado pelo cliente...")

if st.button("🚀 Processar Texto com Inteligência Artificial"):
    if texto_cliente:
        try:
            # Utilizar o modelo correto e estável
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Chamada simples, sem argumentos inesperados como 'api_version'
            response = model.generate_content(
                f"Processe o seguinte pedido de serralharia e extraia os materiais: {texto_cliente}"
            )
            
            # Verificar se a resposta foi gerada com sucesso antes de aceder aos dados
            if response.text:
                st.success("Texto processado com sucesso!")
                st.write(response.text)
                # Aqui insere a sua lógica para preencher a tabela/variáveis
            else:
                st.warning("A IA não conseguiu gerar uma resposta válida. Tente novamente.")
                
        except Exception as e:
            st.error(f"Erro ao processar com a IA. Detalhe: {e}")
    else:
        st.error("Por favor, insira o texto do cliente antes de processar.")
