import pathlib
import sys

# Add the project root to Python path
project_root = pathlib.Path(__file__).parent.parent.parent
print(project_root)
sys.path.append(str(project_root))

import datetime
import streamlit as st
import requests
from src.settings import settings


def get_stream(prompt):
    response = requests.post(f'http://{settings.gateway.url}/chat', json={'prompt': prompt})

    request_id = response.json()['correlation_id']

    # Receive
    with requests.get(f'http://{settings.gateway.url}/stream/{request_id}', stream=True) as r:
        for line in r.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    data = decoded[6:]
                    yield data


title_row = st.container(
    horizontal=True,
    vertical_alignment='bottom',
)

with title_row:
    st.title(
        # ":material/cognition_2: Streamlit AI assistant", anchor=False, width="stretch"
        'Streamlit AI assistant',
        anchor=False,
        width='stretch',
    )

user_just_asked_initial_question = 'initial_question' in st.session_state and st.session_state.initial_question

user_just_clicked_suggestion = 'selected_suggestion' in st.session_state and st.session_state.selected_suggestion

user_first_interaction = user_just_asked_initial_question or user_just_clicked_suggestion

has_message_history = 'messages' in st.session_state and len(st.session_state.messages) > 0

# Show a different UI when the user hasn't asked a question yet.
if not user_first_interaction and not has_message_history:
    st.session_state.messages = []

    with st.container():
        st.chat_input('Ask a question...', key='initial_question')

    st.button(
        '&nbsp;:small[:gray[:material/balance: Legal disclaimer]]',
        type='tertiary',
        # on_click=show_disclaimer_dialog,
    )

    st.stop()

# Show chat input at the bottom when a question has been asked.
user_message = st.chat_input('Ask a follow-up...')

if not user_message:
    if user_just_asked_initial_question:
        user_message = st.session_state.initial_question

with title_row:

    def clear_conversation():
        st.session_state.messages = []
        st.session_state.initial_question = None
        st.session_state.selected_suggestion = None

    st.button(
        'Restart',
        icon=':material/refresh:',
        on_click=clear_conversation,
    )

if 'prev_question_timestamp' not in st.session_state:
    st.session_state.prev_question_timestamp = datetime.datetime.fromtimestamp(0)

# Display chat messages from history as speech bubbles.
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message['role']):
        if message['role'] == 'assistant':
            st.container()  # Fix ghost message bug.

        st.markdown(message['content'])

        # if message["role"] == "assistant":

if user_message:
    # When the user posts a message...

    # Streamlit's Markdown engine interprets "$" as LaTeX code (used to
    # display math). The line below fixes it.
    user_message = user_message.replace('$', r'\$')

    # Display message as a speech bubble.
    with st.chat_message('user'):
        st.text(user_message)

    # Display assistant response as a speech bubble.
    with st.chat_message('assistant'):
        # with st.spinner("Waiting..."):
        #     # Rate-limit the input if needed.
        #     question_timestamp = datetime.datetime.now()
        #     time_diff = question_timestamp - st.session_state.prev_question_timestamp
        #     st.session_state.prev_question_timestamp = question_timestamp

        #     user_message = user_message.replace("'", "")

        # Put everything after the spinners in a container to fix the
        # ghost message bug.
        with st.container():
            # Stream the LLM response.
            response = st.write_stream(get_stream(user_message))

            # Add messages to chat history.
            st.session_state.messages.append({'role': 'user', 'content': user_message})
            st.session_state.messages.append({'role': 'assistant', 'content': response})
