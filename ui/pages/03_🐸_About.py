import streamlit as st
from config import DEV, get_page_config, init_session

# Set up page config & init session
st.set_page_config(**get_page_config())
init_session(st.session_state)
# Render session state if in dev mode
if DEV:
    with st.expander("Session state"):
        st.write(st.session_state)

st.write("## 🐸 &nbsp; `Hi, I'm Froggo!`")
st.write("---")

st.write(
    """
#### `I'm here to help you easily browse, search & navigate your audiovisual content.`

#### `I'm a work in progress - still a tadpole, but I'm growing up fast!`
"""
)

st.write("---")

st.write(
    "##### I was made by [Abhay](https://abhay.fyi) so if I screw up, feel free to yell at him on [Twitter](https://twitter.com/hayabhay) or [Github](https://github.com/hayabhay/frogbase/issues)"
)
