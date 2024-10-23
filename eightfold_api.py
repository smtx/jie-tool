import requests
import os

class EightfoldAPI:
    def __init__(self, username, password, api_domain, client_credentials):
        self.username = username
        self.password = password
        self.client_credentials = client_credentials
        self.base_url = f"https://{api_domain}/api/v2"
        self.auth_url = f"https://{api_domain}/oauth/v1/authenticate"
        self.token = self.authenticate()

    def authenticate(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.client_credentials}"
        }
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }

        response = requests.post(self.auth_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["access_token"]

    def patch_request(self, endpoint, data):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.patch(f"{self.base_url}/{endpoint}", headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_request(self, endpoint, start=None, limit=None, exclude=None):
        headers = {"Authorization": f"Bearer {self.token}"}

        url = f"{self.base_url}/{endpoint}"
        query_params = []

        if limit is not None:
            query_params.append(f"limit={limit}")
        
        if start is not None:
            query_params.append(f"start={start}")

        if exclude is not None:
            query_params.append(f"exclude={exclude}")

        # If there are parameters, add them to the URL
        if query_params:
            url += "?" + "&".join(query_params)

        response = requests.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    def batch_fetch_profiles(self, profile_ids, include=None, exclude=None):
        data = {"entityIds": profile_ids}
        return self.post_request("core/profiles/batch-fetch", data, include, exclude)

    def batch_fetch_positions(self, position_ids, include=None, exclude=None):
        data = {"entityIds": position_ids}
        return self.post_request("core/positions/batch-fetch", data, include, exclude)

    def get_roles(self, start = None, limit= None):
        return self.get_request("JIE/roles", start, limit, exclude="education,experience,calibrationNotes,displayTags,idealCandidateUrls,idealCandidates,associatedTags")

    def delete_role(self, role_id):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        response = requests.delete(f"{self.base_url}/JIE/roles/{role_id}", headers=headers)
        response.raise_for_status()
        return response.json()

    def post_request(self, endpoint, data, include=None, exclude=None):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Build the URL with the Query Parameters only if they are defined
        url = f"{self.base_url}/{endpoint}"
        query_params = []

        if include is not None:
            query_params.append(f"include={include}")
        if exclude is not None:
            query_params.append(f"exclude={exclude}")

        # If there are parameters, add them to the URL
        if query_params:
            url += "?" + "&".join(query_params)

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()