import datetime
import getpass
import json
import re
import traceback
import urllib.parse
from datetime import timedelta

import requests
from django.conf import settings
from jira import JIRA, JIRAError

from .data import BacklogQueryResult
from .globals import _get_fb_end_date, _get_fb_start_date, _get_remaining_fb_count

BASE_URL = "https://jiradc.ext.net.nokia.com/rest/api/2"
HEADERS = {
    "Authorization": "Bearer ODk1MDkzMzM5NDQxOnJhJcfSGPfSKjTAKKAJxnei+WJG",
    "Content-Type": "application/json",
}


def send_request(method, endpoint, data=None):
    print(f"Sending PAT request to {endpoint}")
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
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
    except json.JSONDecodeError:
        print("Response content is not in JSON format")
    return None


JIRA_TEXT2 = "customfield_38727"
JIRA_RISK_STATUS = "customfield_38754"

JIRA_SERVER_URL = "https://jiradc.ext.net.nokia.com"
JIRA_AUTH_CREDENTIAL = (settings.AUTH_USERNAME, settings.AUTH_PASSWORD)

TEXT2_TEMPLATE = """A) Update Version: [24.11.17] <$username>\n\n
B) Risk Situation and Management:
N/A\n
C) Feature Blocking Prontos: (F-level)
N/A"""


def _initJira():
    return JIRA(server=JIRA_SERVER_URL, basic_auth=JIRA_AUTH_CREDENTIAL)


# Generate ReP link for ET/ST CA item
def _get_rep_link(epics, start, end):
    rep_start = _get_fb_start_date(start) - timedelta(days=14)
    rep_end = _get_fb_end_date(end)

    q = {
        "period": "week",
        "target_curve": "Execution Phase Curve",
        "features__featurelavalamp__jira_id": ",".join(f'"{epic}"' for epic in epics),
        "ft": "%s,%s" % (rep_start.strftime("%Y-%m-%d"), rep_end.strftime("%Y-%m-%d")),
    }

    safe_str = urllib.parse.urlencode(q)
    url = "https://rep-portal.ext.net.nokia.com/charts/tep/?%s" % safe_str
    # print(f"ReP query string: {q}\n{safe_str}")
    return url


def extract_issue_fields(issue, field_dict, save_none_value=True):
    issue_dict = {"ID": issue["id"], "Key": issue["key"]}

    for field_name, custom_name in field_dict.items():
        if custom_name in issue["fields"]:
            value = issue["fields"][custom_name]
        else:
            value = None

        if not value:
            if save_none_value:
                issue_dict[field_name] = None
            continue
        elif field_name in ("Item_Type", "Team", "Status"):
            issue_dict[field_name] = value["name"]
        elif field_name in (
            "Competence_Area",
            "Activity_Type",
            "RC_Status",
            "RC_FB",
            "FB_Committed_Status",
            "Stretch_Goal_Reason",
            "Risk_Status",
        ):
            issue_dict[field_name] = value["value"]
        elif field_name in ("Release", "PSR"):
            issue_dict[field_name] = value[0]["value"]
        elif field_name in ("Assignee"):
            issue_dict[field_name] = value["displayName"]
            issue_dict["Assignee_Email"] = value["emailAddress"]
        else:
            issue_dict[field_name] = value

    return issue_dict


def calculate_effort_and_progress(
    issue_dict, total_logged, total_remaining, current_fb=None
):
    """
    Calculate the total logged effort, total remaining effort, and progress
    """

    logged_effort = issue_dict.get("Logged_Effort", 0)
    logged = float(logged_effort) if logged_effort is not None else 0.0
    total_logged += logged

    time_remaining = issue_dict.get("Time_Remaining", 0)
    remaining = float(time_remaining) if time_remaining is not None else 0.0
    total_remaining += remaining

    issue_dict["Total_Effort"] = logged + remaining
    issue_dict["Progress"] = (
        (logged / issue_dict["Total_Effort"] * 100)
        if issue_dict["Total_Effort"] > 0
        else 0
    )

    if current_fb:
        remaining_fb = _get_remaining_fb_count(
            issue_dict["Start_FB"], issue_dict["End_FB"], current_fb
        )
        issue_dict["Effort_Per_FB"] = round(remaining / remaining_fb)

    return total_logged, total_remaining


def fetch_json_data(url):
    """
    fetch the json data from the given url and
    return the extracted issue fields in a dict
    """

    epic_field_dict = {
        "Item_Type": "issuetype",  # name
        # "Item_ID": "customfield_38702",
        "Summary": "summary",  # too much text
        "Status": "status",  # name
        "Assignee": "assignee",  # displayName, emailAddress
        "Start_FB": "customfield_38694",
        "End_FB": "customfield_38693",
        "Logged_Effort": "customfield_43290",
        "Time_Remaining": "customfield_43291",
        # Useful CA/EI fields
        "RC_FB": "customfield_43490",  # value
        "Risk_Status": "customfield_38754",  # value
        "FB_Committed_Status": "customfield_38758",  # value
        # Useful Epic fields
        "Team": "customfield_29790",  # name
        "Labels": "labels",  # test case number
    }

    response = requests.get(url, auth=JIRA_AUTH_CREDENTIAL)
    if response.status_code == 200:
        json_issue = response.json()
        # print(f"{json_issue['fields']['issuetype']['name']}: {json_issue['key']}")
        return extract_issue_fields(json_issue, epic_field_dict, False)
    else:
        print(f"Failed to access {url}, status code: {response.status_code}")
        return {}


def get_item_links(url, include_done=False, is_testing=False):
    """
    Query a CA item's links (excluding the parent EI link) and return in a dict
    {
        "links": [
            {
                "Relationship", "is child of|depends on|...",
                "Key", "FPB-xxx|FCA_xxx|...",
                "Item_Type", "Epic|Competence Area",
                ...
            },
            ...
        ],
        "rep": "https://rep-portal.ext.net.nokia.com/charts/tep/?..."
    }

    """
    link_list = []
    epic_list = []

    ca_field_dict = {
        "Activity_Type": "customfield_38750",
        "Start_FB": "customfield_38694",
        "End_FB": "customfield_38693",
        "IssueLinks": "issuelinks",
    }

    response = requests.get(url, auth=JIRA_AUTH_CREDENTIAL)
    if response.status_code != 200:
        print(f"Failed to access {url}, status code: {response.status_code}")
        return []

    json_issue = response.json()
    issue_dict = extract_issue_fields(json_issue, ca_field_dict, True)

    if "IssueLinks" not in issue_dict:
        print(f"Exception: no links for {json_issue['key']}!")
        return []

    link_status_exclude = ["Obsolete"] if include_done else ["Done", "Obsolete"]
    is_testing = (
        issue_dict["Activity_Type"] in ["System Testing", "Entity Testing"]
        and issue_dict["Start_FB"]
        and issue_dict["End_FB"]
    )

    print(f"\nProcessing links for {json_issue['key']}")
    for link in issue_dict["IssueLinks"]:
        link_dict = {}

        # mostly CA items
        if "inwardIssue" in link and link["inwardIssue"]["fields"]["status"][
            "name"
        ] not in (link_status_exclude):
            # skip "is child of" EI item
            if link["inwardIssue"]["fields"]["issuetype"]["name"] == "Entity Item":
                continue

            print(f"Found CA link: {link['inwardIssue']['self']}")
            link_dict = fetch_json_data(link["inwardIssue"]["self"])
            link_dict["Relationship"] = link["type"]["inward"]
            link_list.append(link_dict)

        # mostly epics, and "is primary of" CA items
        elif "outwardIssue" in link and link["outwardIssue"]["fields"]["status"][
            "name"
        ] not in (link_status_exclude):
            link_dict = fetch_json_data(link["outwardIssue"]["self"])
            link_dict["Relationship"] = link["type"]["outward"]

            if link_dict["Item_Type"] == "Competence Area":
                # TODO: No CA info here, need to read from link["outwardIssue"]["self"]
                # link_dict["Comment"] = get_CA_info(link["outwardIssue"]["self"])
                pass
            elif (
                is_testing
                and link_dict["Item_Type"] == "Epic"
                # and "Labels" in link_dict
            ):
                # print(f"Found testing Epic: {link_dict}")
                link_dict["TC_Number"] = get_testcase_number(
                    link_dict.get("Labels", "")
                )
                epic_list.append(link_dict["Key"])

            link_list.append(link_dict)

        # remove the 'labels' field as it might have much text
        link_dict.pop("Labels", None)

    if epic_list:
        rep_link = _get_rep_link(
            epic_list, issue_dict["Start_FB"], issue_dict["End_FB"]
        )
        # print(f"ReP link: {rep_link}")
        return {
            "links": link_list,
            "rep": rep_link,
            "timestamp": datetime.datetime.now(),
        }

    return {"links": link_list, "timestamp": datetime.datetime.now()}


def get_testcase_number(labels):
    for label in labels:
        match = re.match(r'TC#(\d+)#', label)
        if match:
            return match.group(1)
    return None


def get_entity_item_summary(issue):
    if "issuelinks" not in issue["fields"]:
        print(f"Exception: no issue links for {issue['key']}!")
        return None

    for link in issue["fields"]["issuelinks"]:
        if (
            link["type"]["name"] == "Parent"
            and "inwardIssue" in link
            # and link["inwardIssue"]["fields"]["status"]["name"] not in ("Obsolete")
            and link["inwardIssue"]["fields"]["issuetype"]["name"] == "Entity Item"
        ):
            return link["inwardIssue"]["fields"]["summary"]

    return None


# TODO: for items with secondary links, get the actual logged effort and progress info
def _queryJira(
    jql_str,
    field_dict,
    fields_to_hide,
    include_done,
    check_links=True,
    max_results=200,
    current_fb=None,
):
    jira = _initJira()
    json_result = jira.search_issues(
        jql_str,
        0,
        max_results,
        fields=list(field_dict.values()),
        json_result=True,
    )

    # query = {
    #     "jql": jql_str,
    #     "startAt": 0,
    #     "maxResults": max_results,
    #     "fields": list(field_dict.values())
    # }
    # json_result = send_request("POST", "search", query)

    result = []
    start_earliest = end_latest = None
    rfc_ratio = committed_ratio = 0
    rfc_count = committed_count = 0
    total_logged = total_remaining = 0

    total_count = json_result.get("total", 0)
    print(f"Total count: {total_count}")

    for issue in json_result.get("issues", []):
        issue_dict = extract_issue_fields(issue, field_dict)
        result.append(issue_dict)

        total_logged, total_remaining = calculate_effort_and_progress(
            issue_dict, total_logged, total_remaining, current_fb
        )

        # Get SI ID from CA's Item_ID like 'CB011098-SR-A-CP2_RAN_SysSpec'
        tokens = issue_dict["Item_ID"].split("-", 3)
        if len(tokens) >= 3:
            issue_dict["System_Item"] = "-".join(tokens[:3])
        else:
            issue_dict["System_Item"] = "Unknown"
            print(f"Exception: malformatted Item ID - {issue_dict['Item_ID']}")

        # Get EI from issue link
        if check_links:
            issue_dict["Entity_Item"] = "[{}] {}".format(
                issue_dict["Release"], get_entity_item_summary(issue)
            )

        issue_dict.pop("issuelinks", None)  # too much text
        issue_dict.pop("Item_ID", None)

        # statistics
        if start_earliest is None or (
            issue_dict["Start_FB"] and issue_dict["Start_FB"] < start_earliest
        ):
            start_earliest = issue_dict["Start_FB"]

        if end_latest is None or (
            issue_dict["End_FB"] and issue_dict["End_FB"] > end_latest
        ):
            end_latest = issue_dict["End_FB"]

        if issue_dict["RC_Status"]:
            if issue_dict["RC_Status"].startswith("Committed"):
                committed_count += 1
            if issue_dict["RC_Status"].startswith(("Committed", "Ready")):
                rfc_count += 1

    if total_count > 0:
        rfc_ratio = int(rfc_count * 100 / total_count)
        committed_ratio = int(committed_count * 100 / total_count)

    fields_to_display = []
    if result:
        fields_to_display = [k for k in result[0].keys() if k not in fields_to_hide]

    print("\nFields to display:")
    for index, field in enumerate(fields_to_display):
        print(f"{index}: {field}")

    print("Start earliest: %s, End latest: %s" % (start_earliest, end_latest))
    return BacklogQueryResult(
        backlog_items=result,
        display_fields=fields_to_display,
        start_earliest=start_earliest,
        end_latest=end_latest,
        rfc_ratio=rfc_ratio,
        committed_ratio=committed_ratio,
        total_logged=total_logged,
        total_remaining=total_remaining,
        include_done=include_done,
    )


def jira_get_apo_backlog(current_fb, apo_login_name="cqt437"):
    print(f"jira_get_apo_backlog: {apo_login_name}")
    field_dict = {
        # 0: Key
        #
        # 1-5
        "Summary": "summary",
        "PSR": "customfield_38724",  # value
        "RC_Status": "customfield_38728",
        "Start_FB": "customfield_38694",
        "End_FB": "customfield_38693",
        "Time_Remaining": "customfield_43291",
        #
        # hidden fields
        "Competence_Area": "customfield_38690",
        "Activity_Type": "customfield_38750",
        "Assignee": "assignee",
        "Item_ID": "customfield_38702",
        "RC_FB": "customfield_43490",
        "FB_Committed_Status": "customfield_38758",  # value
        "Stretch_Goal_Reason": "customfield_43893",  # value
        "Risk_Status": "customfield_38754",  # value
        "Risk_Details": "customfield_38435",
        "Logged_Effort": "customfield_43290",
        # mandatory to get EI summary
        # "issuelinks": "issuelinks",
    }

    fields_to_hide = [
        "ID",
        "Assignee_Email",
        "Effort_Per_FB",  # calculated field
        "Competence_Area",
        "Activity_Type",
        "Assignee",
        "Item_ID",
        "RC_FB",
        "FB_Committed_Status",
        "Stretch_Goal_Reason",
        "Risk_Status",
        "Risk_Details",
        "Logged_Effort",
        "Progress",
        "System_Item",
        "Entity_Item",
        # "Effort_Per_FB",  # calculated field
    ]

    jql_str = (
        'issuetype = "Competence Area" AND assignee in ({apo_login_name}) '
        'and status not in (done, obsolete) and "Σ Time Remaining (h)" > 0 '
        'order by "Planned System Release" '
    ).format(apo_login_name=apo_login_name)

    return _queryJira(
        jql_str, field_dict, fields_to_hide, False, False, 300, current_fb
    )


def jira_get_ca_items(fid, max_results, include_done=False):
    """
    CAUTION:
    All the fields in below dict, if not listed in fields_to_hide, will be shown
    in the backlog table (per below sequence)
    """

    field_dict = {
        # 0: Key
        #
        # 1-8
        "Competence_Area": "customfield_38690",
        "Activity_Type": "customfield_38750",
        "Assignee": "assignee",
        "Start_FB": "customfield_38694",
        "End_FB": "customfield_38693",
        # Original_Estimate (customfield_43292) field is no longer available in JIRA,
        # replaced it with calculated field "Total_Effort"
        "Total_Effort": "customfield_43292",
        "Time_Remaining": "customfield_43291",
        "RC_Status": "customfield_38728",
        # 9: Progress
        # 10: SI/System_Item
        # 11: EI/Entity_Item
        #
        # hidden fields
        "Item_ID": "customfield_38702",
        "Summary": "summary",
        "RC_FB": "customfield_43490",
        "FB_Committed_Status": "customfield_38758",  # value
        "Stretch_Goal_Reason": "customfield_43893",  # value
        "Risk_Status": "customfield_38754",  # value
        "Risk_Details": "customfield_38435",
        "Logged_Effort": "customfield_43290",
        "Release": "customfield_38724",  # value
        # mandatory to get EI summary
        "issuelinks": "issuelinks",
    }

    fields_to_hide = [
        "ID",
        "Assignee_Email",  # retrieve from Assignee field
        "Item_ID",
        "Summary",
        "RC_FB",
        "FB_Committed_Status",
        "Stretch_Goal_Reason",
        "Risk_Status",
        "Risk_Details",
        "Logged_Effort",
        "Release",
        "Effort_Per_FB",  # calculated field
    ]

    status_filter = "status not in (done, obsolete)"
    if include_done:
        status_filter = "status not in (obsolete)"
        max_results = 200

    jql_str = (
        '"Feature ID" ~ {fid} and issuetype = "Competence Area" '
        'AND {status_filter} order by "Item ID"'
    ).format(fid=fid, status_filter=status_filter)

    return _queryJira(
        jql_str, field_dict, fields_to_hide, include_done, True, max_results
    )


def jira_get_text2(fid):
    try:
        jira = _initJira()
        jql_str = """project in (FFB) AND "Feature ID" ~ """ + fid
        # print('jira_get_text2 jql: ' + jql_str)

        json_result = jira.search_issues(
            jql_str, 0, 1, fields=f"{JIRA_TEXT2}, {JIRA_RISK_STATUS}", json_result=True
        )

        # print("jira_get_text2 result: " + str(json_result))
        if json_result["total"] == 0:
            return {
                "status": "error",
                "message": (
                    "No result returned from JIRA, "
                    "please ensure the feature ID is correct!"
                ),
            }

        issue = json_result["issues"][0]
        jira_key = issue["key"]
        fields = issue["fields"]

        text2_desc = fields.get(JIRA_TEXT2)
        if text2_desc is None:
            text2_desc = TEXT2_TEMPLATE.replace("$username", getpass.getuser())

        risk_status_field = fields.get(JIRA_RISK_STATUS)
        if risk_status_field and "value" in risk_status_field:
            risk_status = risk_status_field["value"]
        else:
            risk_status = "Green"

        return {
            "status": "success",
            "text2_desc": text2_desc,
            "jira_key": jira_key,
            "risk_status": risk_status,
        }
    except Exception as e:
        print("Exception in jira_get_text2():\n" + str(e) + "\n" + json_result)
        return {"status": "error", "message": str(e)}


def jira_set_text2(jira_key, text2_desc, risk_status):
    try:
        jira = _initJira()
        issue = jira.issue(jira_key, expand="changelog")
        update_dict = {JIRA_TEXT2: text2_desc, JIRA_RISK_STATUS: {"value": risk_status}}
        issue.update(fields=update_dict)
        return {"status": "success"}

    except JIRAError as e:
        print("JIRAError in jira_set_text2():\n" + str(e))
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    except Exception as e:
        print("Exception in jira_set_text2():\n" + str(e))
        print("Exception type:", type(e))
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
