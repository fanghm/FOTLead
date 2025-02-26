import html
import json

import requests
from bs4 import BeautifulSoup

"""
curl -X POST https://jiradc.ext.net.nokia.com/rest/pat/latest/tokens
-H "Content-Type: application/json"
-d "{\"name\": \"__PAT_FOTD_Dashboard__\", \"expirationDuration\": 360}"
--user "qwn783:<passwd>"

"""
BASE_URL = "https://jiradc.ext.net.nokia.com/rest/api/2"
HEADERS = {
    "Authorization": "Bearer ODk1MDkzMzM5NDQxOnJhJcfSGPfSKjTAKKAJxnei+WJG",
    "Content-Type": "application/json",
}


def send_request(method, endpoint, data=None):
    url = f"{BASE_URL}/{endpoint}"
    try:
        if method == "POST":
            response = requests.post(url, headers=HEADERS, data=json.dumps(data))
        elif method == "GET":
            response = requests.get(url, headers=HEADERS)
        else:
            raise ValueError("Unsupported HTTP method")

        response.raise_for_status()
        return response.json()
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.RequestException,
        json.JSONDecodeError,
    ) as err:
        print(f"An error of type {type(err).__name__} occurred: {err}")
        if 'response' in locals() and response is not None:
            print(f"Response status code: {response.status_code}")
            # print(f"Response content: {response.text}")
            save_error_response(response.text)
        else:
            print("No response available.")
    return None


def save_error_response(content):
    # Save the HTML content to pat_error.html
    with open('pat_error.html', 'w', encoding='utf-8') as file:
        file.write(content)

    # Parse the HTML content and extract text
    soup = BeautifulSoup(content, 'html.parser')
    for script in soup.find_all('script'):
        script.decompose()

    text_content = soup.get_text(separator='\n', strip=True)

    # Save the text content to pat_error.txt
    with open('pat_error.txt', 'w', encoding='utf-8') as file:
        file.write(text_content)

    print("Response content saved into pat_error.html and pat_error.txt")


def read_error_response():
    try:
        with open('pat_error.html', 'r', encoding='utf-8') as file:
            content = file.read()

        # Parse the HTML content and extract text
        soup = BeautifulSoup(content, 'html.parser')
        for script in soup.find_all('script'):
            script.decompose()

        text_content = soup.get_text(separator='\n', strip=True)

        # Unescape HTML entities
        text_content = html.unescape(text_content)

        # Save the text content to pat_error.txt
        with open('pat_error1.html', 'w', encoding='utf-8') as file:
            file.write(text_content)

        print("Response content saved into pat_error.html and pat_error.txt")
    except Exception as e:
        print(f"An error occurred while reading or processing the file: {e}")


def create_sub_task(
    parent_issue_key, summary, description, project_key, issue_type="Sub-task"
):
    payload = {
        "fields": {
            "project": {"key": project_key},
            "parent": {"key": parent_issue_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
        }
    }
    data = send_request("POST", "issue", payload)
    if data:
        print("Sub-task created successfully:")
        print(json.dumps(data, indent=4))


def get_ca_items(fid):
    status_filter = "status not in (done, obsolete)"
    jql_str = (
        f'"Feature ID" ~ {fid} and issuetype = "Competence Area" '
        f'AND {status_filter} order by "Item ID"'
    )
    query = {
        "jql": jql_str,
        "startAt": 0,
        "maxResults": 200,
        # "fields": ["id", "key", "summary", "status"]
    }
    data = send_request("POST", "search", query)
    if data:
        with open(fid + '.json', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data, indent=4))

        # issues = data.get('issues', [])
        # for issue in issues:
        #     issue_id = issue['id']
        #     issue_key = issue['key']
        #     summary = issue['fields'].get('summary', 'No summary')
        #     status = issue['fields']['status']['name']
        #     print(f"Issue ID: {issue_id}, Key: {issue_key}, \
        #       Summary: {summary}, Status: {status}")


def get_issue_links(issue_link_id):
    data = send_request("GET", f"issueLink/{issue_link_id}")
    if data:
        print(data)
        with open('pat.html', 'w', encoding='utf-8') as file:
            file.write(json.dumps(data, indent=4))


if __name__ == "__main__":
    # parent_issue_key = "PARENT-123"
    # summary = "Sub-task summary"
    # description = "Sub-task description"
    # project_key = "PROJECT"
    # create_sub_task(parent_issue_key, summary, description, project_key)
    get_ca_items("CB014465-SR")
    # get_issue_links("16156602")

    # read_error_response()
