import streamlit as st
import google.generativeai as genai

st.title("🧪 Teste de Conexão com o Google Gemini")
st.write("Vamos descobrir qual o modelo correto que funciona com a tua chave de API.")

# Verificar e configurar a chave de API de forma limpa
if "GEMINI_API_KEY" in st.secrets:
    api_key_limpa = st.secrets["GEMINI_API_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=api_key_limpa)
    st.success("🔑 Chave GEMINI_API_KEY detetada com sucesso nos Secrets!")
else:
    st.error("❌ Chave GEMINI_API_KEY NÃO encontrada nos Secrets do Streamlit.")

# Entrada de texto para teste
texto_cliente = st.text_area("Insere um texto para testar a IA:", "Portão basculante de 3x2 metros na chapa 18")

# SELETOR DE MODELOS: Evita ter de mudar o código se um falhar
modelo_selecionado = st.selectbox(
    "Escolha o modelo da IA para testar:", 
    ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
)

if st.button("🚀 Testar Conexão com a IA"):
    if not texto_cliente:
        st.warning("Por favor, digite um texto antes de testar.")
    else:
        with st.spinner(f"A ligar ao Google usando o modelo {modelo_selecionado}..."):
            try:
                # Inicializa o modelo selecionado na lista
                model = genai.GenerativeModel(modelo_selecionado)
                response = model.generate_content(f"Resuma brevemente os materiais necessários para: {texto_cliente}")
                
                if response.text:
                    st.balloons()
                    st.success(f"🎉 CONEXÃO BEM-SUCEDIDA COM O MODELO: {modelo_selecionado}!")
                    st.write("**Resposta recebida da IA:**")
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"❌ Falha com o modelo {modelo_selecionado}.")
                st.error(f"Erro reportado pelo servidor: {str(e)}")
