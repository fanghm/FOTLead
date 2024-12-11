import getpass
import traceback
import urllib.parse
from datetime import timedelta

from django.conf import settings
from jira import JIRA, JIRAError

from .globals import _get_fb_end_date, _get_fb_start_date

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


def _get_rep_link(epics, start, end, anchor):
    rep_start = _get_fb_start_date(start) - timedelta(days=14)
    rep_end = _get_fb_end_date(end)

    q = {
        "period": "week",
        "target_curve": "Execution Phase Curve",
        "features__featurelavalamp__jira_id": ",".join(f'"{epic}"' for epic in epics),
        "ft": "%s,%s" % (rep_start.strftime("%Y-%m-%d"), rep_end.strftime("%Y-%m-%d")),
    }

    safe_str = urllib.parse.urlencode(q)
    # print(f"ReP query string: {q}\n{safe_str}")

    url = "https://rep-portal.ext.net.nokia.com/charts/tep/?%s" % safe_str
    return '<a href="%s" target="_blank">%s</a>' % (url, anchor)
    # return url

def extract_issue_fields(issue, field_dict, save_none_value=True):
    issue_dict = {"Key": issue["key"]}

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
        elif field_name in ("Release"):
            issue_dict[field_name] = value[0]["value"]
        elif field_name in ("Assignee"):
            issue_dict[field_name] = value["displayName"]
            issue_dict["Assignee_Email"] = value["emailAddress"]
        else:
            issue_dict[field_name] = value

    return issue_dict

def calculate_progress(issue_dict, total_logged, total_remaining):
    logged_effort = issue_dict.get("Logged_Effort")
    if not logged_effort:
        logged_effort = 0
    logged = float(logged_effort)
    total_logged += logged

    time_remaining = issue_dict.get("Time_Remaining")
    if not time_remaining:
        time_remaining = 0
    remaining = float(time_remaining)
    total_remaining += remaining

    issue_dict["Total_Effort"] = logged + remaining
    issue_dict["Progress"] = (logged / issue_dict["Total_Effort"] * 100) if issue_dict["Total_Effort"] > 0 else 0

    return total_logged, total_remaining

import requests

"""
return a link's field dict without "Key" field
"""
def fetch_json_data(url, auth):
    epic_field_dict = {
        "Item_Type": "issuetype", # name
        # "Item_ID": "customfield_38702",
        "Summary": "summary", # too much text
        "Status": "status", # name
        "Assignee": "assignee", # displayName, emailAddress
        "Start_FB": "customfield_38694",
        "End_FB": "customfield_38693",
        "Logged_Effort": "customfield_43290",
        "Time_Remaining": "customfield_43291",

        # Useful CA/EI fields
        "RC_FB": "customfield_43490", # value
        "FB_Committed_Status": "customfield_38758", # value
        "Risk_Status": "customfield_38754", # value

        # Useful Epic fields
        "Team": "customfield_29790", # name
        "Labels": "labels", # test case number
    }

    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        json_issue = response.json()
        print(f"{json_issue['fields']['issuetype']['name']}: {json_issue['key']}")
        return extract_issue_fields(json_issue, epic_field_dict, False)
    else:
        print(f"Failed to access {url}, status code: {response.status_code}")
        return {}

import re

def get_testcase_number(labels):
    for label in labels:
        match = re.match(r'TC#(\d+)#', label)
        if match:
            return match.group(1)
    return None

def process_issue_links(issue, issue_dict, is_planned_test_item):
    """
    get the linked issue's fields and store them in a list
    link_list = [
        {"Key", "FPB-xxx|FCA_xxx|..."},
        {"Item_Type", "Epic|CA"},
        ...
    ]
    """

    link_list = []
    issue_dict["epics"] = []
    if "issuelinks" not in issue["fields"]:
        print(f"Exception: no issue links for {issue['key']}!")
        return

    print(f"\nProcessing links for {issue['key']}")
    for link in issue["fields"]["issuelinks"]:
        link_dict = {}

        if (
            "inwardIssue" in link
            and link["inwardIssue"]["fields"]["status"]["name"] not in ("Done", "Obsolete")
        ):
            if link["inwardIssue"]["fields"]["issuetype"]["name"] == "Entity Item":
                issue_dict["Entity_Item"] = "[{}] {}".format(
                    issue_dict["Release"], link["inwardIssue"]["fields"]["summary"]
                )
                continue    # skip EI link

            # print(f"Found CA link: {link['inwardIssue']['self']}")
            link_dict = fetch_json_data(
                link["inwardIssue"]["self"],
                JIRA_AUTH_CREDENTIAL
            )

            link_dict["Relationship"] = link["type"]["inward"]
            link_list.append(link_dict)

        # child/epics
        elif (
            "outwardIssue" in link
            and link["outwardIssue"]["fields"]["status"]["name"] not in ("Done", "Obsolete")
        ):
            link_dict = fetch_json_data(
                link["outwardIssue"]["self"],
                JIRA_AUTH_CREDENTIAL
            )

            if is_planned_test_item and link_dict["Item_Type"]  == 'Epic':
                link_dict["TC_Number"] = get_testcase_number(link_dict.get("Labels", []))
                issue_dict["epics"].append(link["outwardIssue"]["key"])

            # remove the 'labels' field from link_dict
            link_dict.pop("Labels", None)
            # link_dict.pop("Item_ID", None)
            # link_dict.pop("Summary", None)

            link_dict["Relationship"] = link["type"]["outward"]
            link_list.append(link_dict)

    issue_dict.pop("issuelinks", None)  # too much text
    issue_dict["links"] = link_list
    return

# TODO: for items with secondary links, get the actual logged effort and progress info
def _queryJira(jql_str, field_dict, keys_to_hide, max_results=20, start_at=0):
    jira = _initJira()
    json_result = jira.search_issues(
        jql_str,
        start_at,
        max_results,
        fields=list(field_dict.values()),
        json_result=True,
    )

    result = []
    subfeatures = set()
    start_earliest = None
    end_latest = None
    rfc_ratio = committed_ratio = 0
    rfc_count = committed_count = 0
    total_logged = total_remaining = 0
    total_count = json_result["total"]
    print(f"Total count: {total_count}")

    for issue in json_result["issues"]:
        issue_dict = extract_issue_fields(issue, field_dict)
        result.append(issue_dict)

        # calc progress and total logged/remaining efforts for statistics
        total_logged, total_remaining = calculate_progress(
            issue_dict, total_logged, total_remaining
        )

        # get SI ID from CA's Item_ID like 'CB011098-SR-A-CP2_RAN_SysSpec'
        tokens = issue_dict["Item_ID"].split("-", 3)
        if len(tokens) >= 3:
            subfeatures.add(tokens[2])
            issue_dict["System_Item"] = "-".join(tokens[:3])
        else:
            issue_dict["System_Item"] = "Unknown"
            print(f"Exception: malformatted Item ID - {issue_dict['Item_ID']}")

        # Get EI from issue link
        is_planned_test_item = (
            issue_dict["Activity_Type"] in ["System Testing", "Entity Testing"]
            and issue_dict["Start_FB"]
            and issue_dict["End_FB"]
        )

        issue_dict["Entity_Item"] = issue_dict["ReP"] = None
        process_issue_links(issue, issue_dict, is_planned_test_item)
            
        epics = issue_dict.get("epics", [])
        if is_planned_test_item and len(epics) > 0:
            issue_dict["ReP"] = _get_rep_link(
                epics, issue_dict["Start_FB"], issue_dict["End_FB"], "ReP"
            )
        issue_dict.pop("epics", None)

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
        fields_to_display = [k for k in result[0].keys() if k not in keys_to_hide]

    print("\nFields to display:")
    for index, field in enumerate(fields_to_display):
        print(f"{index}: {field}")

    return (
        result,
        subfeatures,
        fields_to_display,
        start_earliest,
        end_latest,
        rfc_ratio,
        committed_ratio,
        total_logged,
        total_remaining,
    )

def jira_get_ca_items(fid, max_results, feature_done=False):
    """
    CAUTION:
    All the fields in below dict, if not listed in keys_to_hide, will be shown
    in the backlog table (per below sequence)
    """
    field_dict = {
        # 0: Key

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
        # 12: ReP

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
        "Parent_Id": "customfield_29791",
        "issuelinks": "issuelinks",
    }

    keys_to_hide = [
        "Assignee_Email",   # retrieve from Assignee field
        "Item_ID",
        "Summary",
        "RC_FB",
        "FB_Committed_Status",
        "Stretch_Goal_Reason",
        "Risk_Status",
        "Risk_Details",
        "Logged_Effort",
        "Release",
        "Parent_Id",

        # calculated fields
        "epics",
        "links",
    ]

    status_filter = "status not in (done, obsolete)"
    if feature_done:
        status_filter = "status not in (obsolete)"
        max_results = 200

    jql_str = (
        '"Feature ID" ~ {fid} and issuetype = "Competence Area" '
        'AND {status_filter} order by "Item ID"'
    ).format(fid=fid, status_filter=status_filter)

    return _queryJira(jql_str, field_dict, keys_to_hide, max_results)


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
