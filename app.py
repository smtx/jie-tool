import streamlit as st
import pandas as pd
from eightfold_api import EightfoldAPI
import math
from constants import API_DOMAINS, AUTHORIZATION_HEADERS

def calculate_total_pages(total_count, page_total_count):
    # Assume page size is inferred from pageTotalCount attribute
    if page_total_count == 0:
        return 0

    # Calculate the number of pages required
    pages_needed = math.ceil(total_count / page_total_count)
    return pages_needed


def initialize_session_state():
    """Initializes session state variables."""
    default_state = {
        'api_username': st.secrets.get("api", {}).get("user", None),
        'api_password': st.secrets.get("api", {}).get("password", None),
        'selected_region': st.secrets.get("api", {}).get("region", "US Region"),
        'api_domain': API_DOMAINS[st.secrets.get("api", {}).get("region", "US Region")],
        'refresh_roles': True,
        'df': None,
        'rows': [],
        'token': None,
        'untitled_roles': [],
        'ef_api': None
    }
    for key, value in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if st.session_state['api_username'] and st.session_state['api_password']:
        st.session_state['ef_api'] = EightfoldAPI(
            st.session_state['api_username'],
            st.session_state['api_password'],
            st.session_state['api_domain'],
            AUTHORIZATION_HEADERS[st.session_state['selected_region']]
        )

initialize_session_state()

@st.dialog("API Credentials Setup")
def api_credentials():    
    # Form for the API credentials
    with st.form(key='api_credentials_form', border=False):
        # Pre-fill the fields with existing session state values, if available
        api_username = st.text_input(
            "Username",
            value=st.session_state['api_username'] or "",
        )
        api_password = st.text_input(
            "Password",
            value=st.session_state['api_password'] or "",
            type="password",
        )

        # Selectbox for choosing the region with the selected region from the session state
        selected_region = st.selectbox(
            "Select Eightfold Region",
            options=list(AUTHORIZATION_HEADERS.keys()),
            index=list(AUTHORIZATION_HEADERS.keys()).index(st.session_state['selected_region']),
            help="Choose the region that corresponds to your Eightfold instance."
        )
        st.write("")
        # Form submission buttons
        settings_col, submit_col = st.columns([2, 1])
        with submit_col:
            is_submitted = st.form_submit_button("Save Credentials")

        with settings_col:
            st.link_button("Eightfold API Settings", "https://app.eightfold.ai/integrations/api_server_config")

        # Handle form submission
        if is_submitted:
            # Save the API credentials and region in the session state
            st.session_state['api_username'] = api_username
            st.session_state['api_password'] = api_password
            st.session_state['selected_region'] = selected_region

            # initialize EF API
            st.session_state['ef_api'] = EightfoldAPI(api_username, api_password, st.session_state['api_domain'], AUTHORIZATION_HEADERS[selected_region])

            # Rerun the script to ensure the popup closes immediately
            st.rerun()

@st.dialog("Are you sure?")
def delete_roles(selected_rows):
    rows = st.session_state['rows']
    st.markdown("### 🫣💀⚠️")
    st.write(f"You are about to delete {len(selected_rows)} role{'s' if len(selected_rows) != 1 else ''}.")
    _, button_col = st.columns([3, 2])
    with button_col:
        if st.button("Yes, Delete them", type="primary"):
            progress_text = "Deleting Roles. Please wait."
            my_bar = st.progress(0, text=progress_text)
            for idx, id in enumerate(selected_rows):
                st.session_state['ef_api'].delete_role(rows[id]['ID'])

                percentage = int(100 * idx / len(selected_rows))
                my_bar.progress(percentage)

            st.session_state['refresh_roles'] = True
            st.session_state['rows'] = []
            st.rerun()

def append_roles(roles):
    for role in roles["data"]:
        role_id = role.get("id")
        title = role.get("title")

        skills = role.get("skillProficiencies") or []
        skill_names = [skill.get("name", "Unknown") for skill in skills][:25]
        skill_list = ", ".join(skill_names) if skill_names else "N/A"

        locations = role.get("locations") or []
        location_list = ", ".join(locations[:25]) if locations else "N/A" 

        if not title:
            st.session_state['untitled_roles'].append(role_id)
        else: 
            st.session_state['rows'].append({
                "ID": role_id,
                "Title": title,
                "Skills": skill_list,
                "Locations": location_list
            })

# Layout setup with columns for button placement
header_col, settings_col = st.columns([4, 1])
st.logo(
    "https://smtx.s3.us-east-1.amazonaws.com/nformal-small-logo.png",
    size="large",
    link="https://nformal.io",
)
with header_col:
    if st.session_state['ef_api']:
        st.write("connected as " + st.session_state['ef_api'].username)
        st.write("# JIE/Talent Design Tool")
        if st.button('reload roles', icon=":material/refresh:", disabled=not st.session_state['ef_api']):
            st.session_state['rows'] = []
            st.session_state['refresh_roles'] = True
            st.rerun()
    else:
        api_credentials()

with settings_col:
    st.write("")
    if st.button("API Credentials"):
        api_credentials()


if st.session_state['ef_api'] and st.session_state['refresh_roles']:
    with st.spinner('Getting roles...'):
        my_bar = st.progress(0)
        roles = st.session_state['ef_api'].get_roles(0, 100)
        append_roles(roles)
        
        total_pages = calculate_total_pages(roles['meta']['totalCount'], roles['meta']['pageTotalCount'])-1

        for page in range(1,total_pages):
            percentage = int(100 * page / total_pages)
            my_bar.progress(percentage)
            append_roles(st.session_state['ef_api'].get_roles(page*100, 100))
        my_bar.empty()

    if st.session_state['refresh_roles']:
        st.session_state['df'] = pd.DataFrame(st.session_state['rows'])
        st.session_state['refresh_roles'] = False

    with st.container():
        leftc, rightc = st.columns(2)
        with leftc:
            st.write("### JIE Roles")                

    total_roles = len(st.session_state['rows'])
    st.write(f"Found {total_roles} role{'s' if total_roles != 1 else ''}.")

if st.session_state['rows']:
    roleTable = st.dataframe(
        st.session_state['df'],
        key="data",
        height=700,
        column_config={
            "Skills": st.column_config.ListColumn(
                "Skills",
                help="Skills configured for this role.",
                width="large",
            ),
            "Locations": st.column_config.ListColumn(
                "Locations",
                help="Locations configured for this role.",
                width="small",
            )
        },
        on_select="rerun",
        selection_mode=["multi-row"],
    )

    # Layout setup with columns for button placement
    left_col, button_col = st.columns([6, 3])
    with left_col:
        if st.session_state['untitled_roles']:
            with st.expander(f"Found {len(st.session_state['untitled_roles'])} untitled role{'s' if len(st.session_state['untitled_roles']) != 1 else ''}."):
                st.write(st.session_state['untitled_roles'])
    with button_col:
        selected_count = len(roleTable.selection["rows"])
        button_label = f"Delete {selected_count} Selected Role{'s' if selected_count != 1 else ''}"
        if selected_count > 0:
            if st.button(
                button_label,
                use_container_width=True,
                icon="🔥",
            ):
                delete_roles(roleTable.selection['rows'])


