from jira import JIRA
import urllib.parse
from datetime import timedelta
from django.conf import settings
from .globals import _get_fb_start_date, _get_fb_end_date

JIRA_FIELD_TEXT2 = 'customfield_38727'
JIRA_FIELD_RISK_STATUS = 'customfield_38754'

def _initJira():
    return JIRA(server = "https://jiradc.ext.net.nokia.com", basic_auth=(settings.AUTH_USERNAME, settings.AUTH_PASSWORD))

def _get_rep_link(epics, start, end):
    q = {
        'period': 'week', 
        'target_curve': 'Execution Phase Curve',
        'features__featurelavalamp__jira_id':  ','.join(f'"{epic}"' for epic in epics),
        'ft': f"{ (_get_fb_start_date(start) - timedelta(days=14)).strftime('%Y-%m-%d')},{_get_fb_end_date(end).strftime('%Y-%m-%d')}"
    }

    safe_str = urllib.parse.urlencode(q)
    #print(f"ReP query string: {q}\n{safe_str}")

    return f'<a href="https://rep-portal.ext.net.nokia.com/charts/tep/?{safe_str}" target="_blank">ReP</a>'
    
# TODO: for items with secondary links, get the actual logged effort and progress info
def _queryJira(jql_str, field_dict, keys_to_hide):
    jira = _initJira()
    json_result = jira.search_issues(jql_str, 0, 200, fields=list(field_dict.values()), json_result=True)

    result = []
    subfeatures = set()
    start_earliest = None
    end_latest = None
    rfc_ratio = committed_ratio = 0
    rfc_count = committed_count = 0
    total_spent = total_remaining = 0
    total_count = json_result['total']
    print(f"Total count: {total_count}")

    for issue in json_result['issues']:
        # the first field is always the key
        issue_dict = {'Key': issue['key']}
        for field_name, custom_name in field_dict.items():
            value = issue['fields'][custom_name]

            if not value:
                issue_dict[field_name] = None
            elif field_name in ('Competence_Area', 'Activity_Type', 'RC_Status', 'RC_FB', 'FB_Committed_Status', 'Stretch_Goal_Reason', 'Risk_Status'):
                issue_dict[field_name] = value['value']
            elif field_name in ('Release'):
                issue_dict[field_name] = value[0]['value']
            elif field_name in ('Assignee'):
                issue_dict[field_name] = value['displayName']
                issue_dict['Assignee_Email'] = value['emailAddress']
            else:
                issue_dict[field_name] = value

        # calc progress
        if issue_dict['Logged_Effort']:
            spent = float(issue_dict['Logged_Effort'])
            total_spent += spent
        else:
            spent = 0

        if issue_dict['Time_Remaining']:
            remaining = issue_dict['Time_Remaining']
            total_remaining += remaining
        else:
            remaining = issue_dict['Time_Remaining'] = 0

        if (spent + remaining) > 0:
            issue_dict['Progress'] = spent / (spent + remaining) * 100
        else:
            issue_dict['Progress'] = 0

        result.append(issue_dict)

        # get sub-feature from Item_ID like 'CB011098-SR-A-CP2_RAN_SysSpec'
        tokens = issue_dict['Item_ID'].split('-', 3)
        if len(tokens) >= 3:
            subfeatures.add(tokens[2])
            issue_dict['Sub_Feature'] = '-'.join(tokens[:3])
        else:
            issue_dict['Sub_Feature'] = 'Unknown'
            print(f"Exception: malformatted Item ID - {issue_dict['Item_ID']}")

        # Get EI from issue link
        epics = []
        is_ST = issue_dict['Activity_Type'] == 'System Testing'
        issue_dict['EI'] = issue_dict['ReP'] = None
        if 'issuelinks' not in issue['fields']:
            print(f"Exception: no issue links for {issue['key']}!")
        else:
            for link in issue['fields']['issuelinks']:
                if 'inwardIssue' in link:   # parent
                    if link['inwardIssue']['key'] != issue_dict['Parent_Id']:   # just to check exceptional links
                        print(f"Exception: the {issue['key']}'s inwardIssue link {link['inwardIssue']['key']} is not for its parent {issue_dict['Parent_Id']}")
                    
                    issue_dict['EI'] = f"[{issue_dict['Release']}] {link['inwardIssue']['fields']['summary']}"
                    #print(f"SI: {issue_dict['Sub_Feature']}, EI: {issue_dict['EI']}")

                elif is_ST and 'outwardIssue' in link and link['outwardIssue']['fields']['status']['name'] != 'Obsolete':  # child
                    #link['outwardIssue']['fields']['issuetype']['name'] == 'Epic'
                    print(f"Found ST {link['outwardIssue']['fields']['issuetype']['name']} child: {link['outwardIssue']['key']}")
                    epics.append(link['outwardIssue']['key'])

        if is_ST and len(epics) > 0:
            issue_dict['ReP'] = _get_rep_link(epics, issue_dict['Start_FB'] , issue_dict['End_FB'])

        # statistics
        if start_earliest is None or (issue_dict['Start_FB'] and issue_dict['Start_FB'] < start_earliest):
            start_earliest = issue_dict['Start_FB']

        if end_latest is None or (issue_dict['End_FB'] and issue_dict['End_FB'] > end_latest):
            end_latest = issue_dict['End_FB']

        if issue_dict['RC_Status']:
            if issue_dict['RC_Status'].startswith('Committed'):
                committed_count += 1
            if issue_dict['RC_Status'].startswith(('Committed', 'Ready')):
                rfc_count += 1

    if total_count > 0:
        rfc_ratio = int(rfc_count * 100 / total_count)
        committed_ratio = int(committed_count * 100 / total_count)

    fields_to_display = [k for k in result[0].keys() if k not in keys_to_hide] if result else []
    print(f"Fields to display:")
    for index, field in enumerate(fields_to_display):
        print(f"{index}: {field}")

    return (result, subfeatures, fields_to_display, start_earliest, end_latest, rfc_ratio, committed_ratio, total_spent, total_remaining)

def jira_get_ca_items(fid, query_done=False):
    # CAUTION:
    # All the fields in below dictionary, if not listed in keys_to_hide, will be shown in the backlog table (per the sequence) 
    field_dict = {
        #0: Key
        'Item_ID': 'customfield_38702',
        'Summary': 'summary',

        #1-8
        'Competence_Area': 'customfield_38690',
        'Activity_Type': 'customfield_38750',
        'Assignee': 'assignee',
        'Start_FB': 'customfield_38694',
        'End_FB': 'customfield_38693',
        'Original_Estimate': 'customfield_43292',
        'Time_Remaining': 'customfield_43291',
        'RC_Status': 'customfield_38728',

        #9: Progress
        #10: SI/Sub_Feature
        #11: EI
        #12: ReP
        
        'RC_FB': 'customfield_43490',
        'FB_Committed_Status': 'customfield_38758', #value
        'Stretch_Goal_Reason': 'customfield_43893', #value
        'Risk_Status': 'customfield_38754',     #value
        'Risk_Details': 'customfield_38435',
        'Logged_Effort': 'customfield_43290',

        'Parent_Id': 'customfield_29791',
        'issuelinks': 'issuelinks', # for EI info
        'Release': 'customfield_38724', #value
    }

    keys_to_hide = ['Release', 'Parent_Id', 'issuelinks', 'Assignee_Email', 'Item_ID', 'Summary', 'FB_Committed_Status', 'Stretch_Goal_Reason', 'Risk_Status', 'Risk_Details', 'Logged_Effort', 'RC_FB']

    if query_done:
        jql_str = f'''("Feature ID" ~ {fid}) and issuetype = "Competence Area" AND status not in (obsolete) order by "Item ID" '''
    else:
        jql_str = f'''("Feature ID" ~ {fid}) and issuetype = "Competence Area" AND status not in (done, obsolete) order by "Item ID" '''

    return _queryJira(jql_str, field_dict, keys_to_hide)


def jira_get_text2(fid):
    try:
        jira = _initJira()
        jql_str = '''project in (FFB) AND "Feature ID" ~ ''' + fid
        #print('jira_get_text2 jql: ' + jql_str)

        json_result = jira.search_issues(jql_str 
                , 0 #startAt 
                , 1 #200, #maxResults
                , fields=f'{JIRA_FIELD_TEXT2}, {JIRA_FIELD_RISK_STATUS}'    # text 2
                #, expand="changelog"
                , json_result=True
                )

        issue = json_result['issues'][0]
        jira_key = issue['key']
        text2_desc = issue['fields'][JIRA_FIELD_TEXT2] if JIRA_FIELD_TEXT2 in issue['fields'] else 'Not set'
        risk_status = issue['fields'][JIRA_FIELD_RISK_STATUS]['value'] if JIRA_FIELD_RISK_STATUS in issue['fields'] and issue['fields'][JIRA_FIELD_RISK_STATUS] else 'Green'
        #print(f'{fid} key: {jira_key} Text2:{text2_desc}\n')
        return {'status': 'success', 'text2_desc': text2_desc, 'jira_key': jira_key, 'risk_status': risk_status}

    except Exception as e:
        print("Exception in jira_get_text2():\n" + str(e) + '\n' + issue)
        return {'status': 'error', 'message': str(e)}

def jira_set_text2(jira_key, text2_desc, risk_status):
    try:
        jira = _initJira()
        issue = jira.issue(jira_key, expand="changelog")
        update_dict = {
            JIRA_FIELD_TEXT2: text2_desc,
            JIRA_FIELD_RISK_STATUS: {'value': risk_status}
        }
        issue.update(fields = update_dict)
        return {'status': 'success'}

    except Exception as e:
        print("Exception in jira_set_text2():\n" + str(e))
        return {'status': 'error', 'message': str(e)}