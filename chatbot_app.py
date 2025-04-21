import streamlit as st
import replicate
import os
import time

# Código adaptado y actualizado de https://github.com/sfc-gh-cnantasenamat/streamlit-replicate-app
# y de https://github.com/a16z-infra/llama2-chatbot


# Configuración inicial
st.set_page_config(
    page_title="Streamlit Replicate Chatbot",
    page_icon=":robot:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado
# CSS personalizado
custom_css = """
    <style>
        .stTextArea textarea {font-size: 13px;}
        div[data-baseweb="select"] > div {font-size: 13px !important;}
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Información de modelos
# Información de modelos
model_info = {
    'meta-llama-3-8b-instruct': {
        'endpoint': 'meta/meta-llama-3-8b-instruct',
        'doc_link': 'https://replicate.com/meta/meta-llama-3-8b-instruct',
        'uses_top_p': True,
        'min_tokens': 64
    },
    'meta-llama-3-70b-instruct': {
        'endpoint': 'meta/meta-llama-3-70b-instruct',
        'doc_link': 'https://replicate.com/meta/meta-llama-3-70b-instruct',
        'uses_top_p': True,
        'min_tokens': 64
    },
    'meta-llama-3.1-405b-instruct': {
        'endpoint': 'meta/meta-llama-3.1-405b-instruct',
        'doc_link': 'https://replicate.com/meta/meta-llama-3.1-405b-instruct',
        'uses_top_p': True,
        'min_tokens': 64
    },
    'meta-llama-4-17b-maverick-instruct': {
        'endpoint': 'meta/llama-4-maverick-instruct',
        'doc_link': 'https://replicate.com/meta/llama-4-maverick-instruct',
        'uses_top_p': True,
        'min_tokens': 64
    },
    'anthropic-claude-3.7-sonnet': {
        'endpoint': 'anthropic/claude-3.7-sonnet',
        'doc_link': 'https://replicate.com/anthropic/claude-3.7-sonnet',
        'uses_top_p': False,
        'min_tokens': 1024
    }
}

# Inicialización de variables
# Inicialización de variables
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
if "model" not in st.session_state:
    st.session_state.model = 'meta/meta-llama-3-8b-instruct'
if "selected_model" not in st.session_state:
    st.session_state.selected_model = 'meta-llama-3-8b-instruct'
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "top_p" not in st.session_state:
    st.session_state.top_p = 0.9
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 512
if "pre_prompt" not in st.session_state:
    st.session_state.pre_prompt = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."


# Barra lateral
with st.sidebar:
    st.title('🤖 Streamlit Replicate Chatbot')
    
    # API key
    if 'REPLICATE_API_TOKEN' in st.secrets:
        st.success('API key already provided!', icon='✅')
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        replicate_api = st.text_input('Enter Replicate API token:', type='password')
        if not (replicate_api.startswith('r8_') and len(replicate_api)==40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')

    
    
    # Selección del modelo
    # Selección del modelo
    st.subheader('Models and parameters')
    model_options = list(model_info.keys())
    
    selected_model = st.sidebar.selectbox(
        'Choose a model', model_options, 
        index=model_options.index(st.session_state.selected_model)
    )
    
    # Forzar recarga para aplicar cambios de modelo
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
        st.session_state.model = model_info[selected_model]['endpoint']
        st.rerun()
    
    current_model = st.session_state.selected_model
    current_model_info = model_info[current_model]

    # Link de documentación
    doc_link = current_model_info['doc_link']
    st.markdown(f"👉 [Learn more about this model]({doc_link}) 👈")    
    
    # Forzar recarga para aplicar cambios de modelo

    
    # Link de documentación


    # Deslizador de Temperatura
    st.session_state.temperature = st.sidebar.slider(
        'temperature', 
        min_value=0.0, 
        max_value=5.0, 
        value=st.session_state.temperature, 
        step=0.05
    )
    if st.session_state.temperature >= 1:
        st.info('Values exceeding 1 produce more creative and random outputs as well as increased likelihood of hallucination.')
    if st.session_state.temperature < 0.1:
        st.warning('Values approaching 0 produce deterministic outputs. The recommended starting value is 0.7')

    # Deslizador de Top-p
    st.session_state.top_p = st.sidebar.slider(
        'top_p', 
        min_value=0.00, 
        max_value=1.0, 
        value=st.session_state.top_p, 
        step=0.05, 
        disabled=not current_model_info['uses_top_p']
    )
    if not current_model_info['uses_top_p']:
        st.warning(f'{current_model} does not use the top_p parameter.')
    else:
        if st.session_state.top_p < 0.5:
            st.warning('Low top_p values (<0.5) can make output more focused but less diverse. Recommended starting value is 0.9')
        if st.session_state.top_p == 1.0:
            st.info('A top_p value of 1.0 means no nucleus sampling is applied (considers all tokens).')

    # Deslizador de Max tokens
    min_tokens = current_model_info['min_tokens']
    st.session_state.max_tokens = st.sidebar.slider(
        'max_length', 
        min_value=min_tokens, 
        max_value=4096, 
        value=max(min_tokens, st.session_state.max_tokens), 
        step=8
    )
    if min_tokens > 64:
        st.warning(f'{current_model} requires at least {min_tokens} input tokens.')

    # Prompt de sistema editable
    st.subheader("System Prompt")
    new_prompt = st.text_area(
        'Edit the prompt that guides the model:',
        st.session_state.pre_prompt,
        height=100
    )
    if new_prompt != st.session_state.pre_prompt and new_prompt.strip():
        st.session_state.pre_prompt = new_prompt
    
    # Botón de limpiar historial 
    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    st.button('Clear Chat', on_click=clear_chat_history, use_container_width=True)

# API token
os.environ['REPLICATE_API_TOKEN'] = replicate_api

# Generación de respuesta
def generate_response(prompt_input):
    string_dialogue = st.session_state.pre_prompt + "\n\n"
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    
    # Parámetros base
    input_params = {
        "prompt": f"{string_dialogue}User: {prompt_input}\n\nAssistant: ",
        "temperature": st.session_state.temperature,
        "max_tokens": st.session_state.max_tokens,
        "repetition_penalty": 1,
    }
    
    # Añadir top_p solo si el modelo lo utiliza
    current_model = st.session_state.selected_model
    if model_info[current_model]['uses_top_p']:
        input_params["top_p"] = st.session_state.top_p
    
    # Stream de respuestas
    for event in replicate.stream(st.session_state.model, input=input_params):
        yield str(event)


# Mostrar mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Entrada del usuario
if prompt := st.chat_input("Type your message here...", disabled=not replicate_api):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generar respuesta
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(st.session_state.messages[-1]["content"])
            full_response = st.write_stream(response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
