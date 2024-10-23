import streamlit as st
import pandas as pd
from eightfold_api import EightfoldAPI
import math

def calculate_total_pages(total_count, page_total_count):
    # Assume page size is inferred from pageTotalCount attribute
    if page_total_count == 0:
        return 0

    # Calculate the number of pages required
    pages_needed = math.ceil(total_count / page_total_count)
    return pages_needed

# API domains for different regions
API_DOMAINS = {
    "US Region": "apiv2.eightfold.ai",
    "EU Region": "apiv2.eightfold-eu.ai",
    "Govt Accounts": "apiv2.eightfold-gov.ai",
    "CA Region": "apiv2.eightfold-ca.ai",
    "ME Region": "apiv2.eightfold-me.ai",
    "WU Region": "apiv2.eightfold-wu.ai"
}

# Authorization headers for different Eightfold regions
AUTHORIZATION_HEADERS = {
    "US Region": "MU92YTg4T1JyMlFBVktEZG8wc1dycTdEOnBOY1NoMno1RlFBMTZ6V2QwN3cyeUFvc3QwTU05MmZmaXFFRDM4ZzJ4SFVyMGRDaw==",
    "EU Region": "Vmd6RlF4YklLUnI2d0tNZWRpdVZTOFhJOmdiM1pjYzUyUzNIRmhsNzd5c2VmNTgyOG5jVk05djl1dGVtQ2tmNVEyMnRpV1VJVQ==",
    "Govt Accounts": "UnRRM2NPa1doMlVtVHBHSFlobnl6YnhSOjU1UXcxYXZKclI3VjNRdUMxN2VwSWFadDFEd2hmaG5xempieFE4QlVRMUtFZzFzRg==",
    "CA Region": "Q3hTYzBvaVZuZ2llOFdQMXRsdkxSMlg3OlBJTjVndmRaUVRvc0p3d2Q4SFE1djJMcWNCbVR1d0kybmU5SEU2bFJLT0hLaVNGUw==",
    "ME Region": "NHhsY3BWaVRxa2dPMEd6NENCZXFjb3ZWOkI4MEVGT0J3NGx3M0lGbWd2ZUtzU0tMMTZvQ2IxaUM5dUhkcTFEQjVqZ3cwdzZ2Sg==",
    "WU Region": "YVRmRzdwVkJKRUVzTGZBY2dITENHUFdLOmMzbkRaM3czRGNmcExLUko5c0JmUFJUME1WSGxqVU1wbTNsRHBwUUU1YVVRYmc3Mw=="
}

# Initialize session state for API credentials and popup visibility
if 'api_username' not in st.session_state:
    st.session_state['api_username'] = st.secrets.get("api", {}).get("user", None)
if 'api_password' not in st.session_state:
    st.session_state['api_password'] = st.secrets.get("api", {}).get("password", None)
if 'selected_region' not in st.session_state:
    st.session_state['selected_region'] = "US Region"
if 'api_domain' not in st.session_state:
    st.session_state['api_domain'] = API_DOMAINS['US Region']
if 'refresh_roles' not in st.session_state:
    st.session_state['refresh_roles'] = True
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'rows' not in st.session_state:
    st.session_state['rows'] = []
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'untitled_roles' not in st.session_state:
    st.session_state['untitled_roles'] = []
if 'ef_api' not in st.session_state:
    if st.session_state['api_username'] and st.session_state['api_password']:
        st.session_state['ef_api'] = EightfoldAPI(st.session_state['api_username'], st.session_state['api_password'], st.session_state['api_domain'], AUTHORIZATION_HEADERS[st.session_state['selected_region']])
    else:
        st.session_state['ef_api'] = None

@st.dialog("API Credentials")
def api_credentials():
    st.write("### API Credentials Setup")

    # Selectbox for choosing the region with the selected region from the session state
    selected_region = st.selectbox(
        "Select Eightfold Region",
        options=list(AUTHORIZATION_HEADERS.keys()),
        index=list(AUTHORIZATION_HEADERS.keys()).index(st.session_state['selected_region']),
        help="Choose the region that corresponds to your Eightfold instance."
    )

    # Update the API domain based on the selected region dynamically
    st.session_state['api_domain'] = API_DOMAINS[selected_region]
    st.session_state['selected_region'] = selected_region
    


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
        title = role.get("title", "Untitled Role")

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
        if st.session_state['untitled_roles']:
            with st.expander(f"Found {len(st.session_state['untitled_roles'])} untitled role{'s' if len(st.session_state['untitled_roles']) != 1 else ''}."):
                st.write(st.session_state['untitled_roles'])

    if st.session_state['refresh_roles']:
        st.session_state['df'] = pd.DataFrame(st.session_state['rows'])
        st.session_state['refresh_roles'] = False

    with st.container():
        leftc, rightc = st.columns(2)
        with leftc:
            st.write("### JIE Roles")
        with rightc:
            if st.button('reload roles', icon=":material/refresh:"):
                st.session_state['rows'] = []
                st.session_state['refresh_roles'] = True
                st.rerun()
                

    total_roles = len(st.session_state['rows'])
    st.write(f"Found {total_roles} role{'s' if total_roles != 1 else ''}.")

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

with settings_col:
    st.write("")
    if st.button("API Credentials"):
        api_credentials()

