import urllib.parse
from datetime import timedelta

from django.conf import settings
from jira import JIRA

from .globals import _get_fb_end_date, _get_fb_start_date

JIRA_TEXT2 = "customfield_38727"
JIRA_RISK_STATUS = "customfield_38754"
JIRA_SERVER_URL = "https://jiradc.ext.net.nokia.com"


def _initJira():
    credentials = (settings.AUTH_USERNAME, settings.AUTH_PASSWORD)
    return JIRA(server=JIRA_SERVER_URL, basic_auth=credentials)


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


# TODO: for items with secondary links, get the actual logged effort and progress info
def _queryJira(jql_str, field_dict, keys_to_hide, max_results=200, start_at=0):
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
    total_spent = total_remaining = 0
    total_count = json_result["total"]
    print(f"Total count: {total_count}")

    for issue in json_result["issues"]:
        # the first field is always the key
        issue_dict = {"Key": issue["key"]}
        for field_name, custom_name in field_dict.items():
            value = issue["fields"][custom_name]

            if not value:
                issue_dict[field_name] = None
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

        # calc progress
        if issue_dict["Logged_Effort"]:
            spent = float(issue_dict["Logged_Effort"])
            total_spent += spent
        else:
            spent = 0

        if issue_dict["Time_Remaining"]:
            remaining = issue_dict["Time_Remaining"]
            total_remaining += remaining
        else:
            remaining = issue_dict["Time_Remaining"] = 0

        if (spent + remaining) > 0:
            issue_dict["Progress"] = spent / (spent + remaining) * 100
        else:
            issue_dict["Progress"] = 0

        result.append(issue_dict)

        # get sub-feature from Item_ID like 'CB011098-SR-A-CP2_RAN_SysSpec'
        tokens = issue_dict["Item_ID"].split("-", 3)
        if len(tokens) >= 3:
            subfeatures.add(tokens[2])
            issue_dict["Sub_Feature"] = "-".join(tokens[:3])
        else:
            issue_dict["Sub_Feature"] = "Unknown"
            print(f"Exception: malformatted Item ID - {issue_dict['Item_ID']}")

        # Get EI from issue link
        epics = []
        is_test_planned = (
            issue_dict["Activity_Type"] in ["System Testing", "Entity Testing"]
            and issue_dict["Start_FB"]
            and issue_dict["End_FB"]
        )

        issue_dict["EI"] = issue_dict["ReP"] = None
        if "issuelinks" not in issue["fields"]:
            print(f"Exception: no issue links for {issue['key']}!")
        else:
            for link in issue["fields"]["issuelinks"]:
                if "inwardIssue" in link:
                    # just to check if inwardIssue is always the parent, seems not
                    # can be 'cloned to' link
                    if link["inwardIssue"]["key"] != issue_dict["Parent_Id"]:
                        print(
                            "%s: inwardIssue %s is not for its parent %s"
                            % (
                                issue["key"],
                                link["inwardIssue"]["key"],
                                issue_dict["Parent_Id"],
                            )
                        )

                    issue_dict["EI"] = "[{}] {}".format(
                        issue_dict["Release"], link["inwardIssue"]["fields"]["summary"]
                    )
                    # print(f"SI: {issue_dict['Sub_Feature']}, EI: {issue_dict['EI']}")

                # child/epics
                elif (
                    is_test_planned
                    and "outwardIssue" in link
                    and link["outwardIssue"]["fields"]["status"]["name"] != "Obsolete"
                ):
                    # link['outwardIssue']['fields']['issuetype']['name'] == 'Epic'
                    print(
                        "Found ST/ET %s: %s"
                        % (
                            link["outwardIssue"]["fields"]["issuetype"]["name"],
                            link["outwardIssue"]["key"],
                        )
                    )
                    epics.append(link["outwardIssue"]["key"])

        if is_test_planned and len(epics) > 0:
            issue_dict["ReP"] = _get_rep_link(
                epics, issue_dict["Start_FB"], issue_dict["End_FB"], "ReP"
            )

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

    print("Fields to display:")
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
        total_spent,
        total_remaining,
    )


def jira_get_ca_items(fid, feature_done=False):
    """
    CAUTION:
    All the fields in below dict, if not listed in keys_to_hide, will be shown
    in the backlog table (per below sequence)
    """
    field_dict = {
        # 0: Key
        "Item_ID": "customfield_38702",
        "Summary": "summary",
        # 1-8
        "Competence_Area": "customfield_38690",
        "Activity_Type": "customfield_38750",
        "Assignee": "assignee",
        "Start_FB": "customfield_38694",
        "End_FB": "customfield_38693",
        "Original_Estimate": "customfield_43292",
        "Time_Remaining": "customfield_43291",
        "RC_Status": "customfield_38728",
        # 9: Progress
        # 10: SI/Sub_Feature
        # 11: EI
        # 12: ReP
        "RC_FB": "customfield_43490",
        "FB_Committed_Status": "customfield_38758",  # value
        "Stretch_Goal_Reason": "customfield_43893",  # value
        "Risk_Status": "customfield_38754",  # value
        "Risk_Details": "customfield_38435",
        "Logged_Effort": "customfield_43290",
        "Parent_Id": "customfield_29791",
        "issuelinks": "issuelinks",  # for EI info
        "Release": "customfield_38724",  # value
    }

    keys_to_hide = [
        "Release",
        "Parent_Id",
        "issuelinks",
        "Assignee_Email",
        "Item_ID",
        "Summary",
        "FB_Committed_Status",
        "Stretch_Goal_Reason",
        "Risk_Status",
        "Risk_Details",
        "Logged_Effort",
        "RC_FB",
    ]

    status_filter = "status not in (done, obsolete)"
    if feature_done:
        status_filter = "status not in (obsolete)"

    jql_str = (
        '("Feature ID" ~ {fid}) and issuetype = "Competence Area" '
        'AND {status_filter} order by "Item ID"'
    ).format(fid=fid, status_filter=status_filter)

    return _queryJira(jql_str, field_dict, keys_to_hide)


def jira_get_text2(fid):
    try:
        jira = _initJira()
        jql_str = """project in (FFB) AND "Feature ID" ~ """ + fid
        # print('jira_get_text2 jql: ' + jql_str)

        json_result = jira.search_issues(
            jql_str, 0, 1, fields=f"{JIRA_TEXT2}, {JIRA_RISK_STATUS}", json_result=True
        )

        issue = json_result["issues"][0]
        jira_key = issue["key"]
        text2_desc = (
            issue["fields"][JIRA_TEXT2] if JIRA_TEXT2 in issue["fields"] else "Not set"
        )

        risk_status = (
            issue["fields"][JIRA_RISK_STATUS]["value"]
            if JIRA_RISK_STATUS in issue["fields"] and issue["fields"][JIRA_RISK_STATUS]
            else "Green"
        )
        # print(f'{fid} key: {jira_key} Text2:{text2_desc}\n')
        return {
            "status": "success",
            "text2_desc": text2_desc,
            "jira_key": jira_key,
            "risk_status": risk_status,
        }
    except Exception as e:
        print("Exception in jira_get_text2():\n" + str(e) + "\n" + issue)
        return {"status": "error", "message": str(e)}


def jira_set_text2(jira_key, text2_desc, risk_status):
    try:
        jira = _initJira()
        issue = jira.issue(jira_key, expand="changelog")
        update_dict = {JIRA_TEXT2: text2_desc, JIRA_RISK_STATUS: {"value": risk_status}}
        issue.update(fields=update_dict)
        return {"status": "success"}

    except Exception as e:
        print("Exception in jira_set_text2():\n" + str(e))
        return {"status": "error", "message": str(e)}
