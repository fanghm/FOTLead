from jira import JIRA
from django.conf import settings

JIRA_FIELD_TEXT2 = 'customfield_38727'
JIRA_FIELD_RISK_STATUS = 'customfield_38754'

def _initJira():
    return JIRA(server = "https://jiradc.ext.net.nokia.com", basic_auth=(settings.AUTH_USERNAME, settings.AUTH_PASSWORD))

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

        # get sub-feature set
        tokens = issue_dict['Item_ID'].split('-', 3)
        if len(tokens) >= 3:
            subfeatures.add(tokens[2])
            issue_dict['Sub_Feature'] = '-'.join(tokens[:3])
        else:
            issue_dict['Sub_Feature'] = 'Unknown'
            print(f"Exception: malformatted Item ID - {issue_dict['Item_ID']}")

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

    return (result, subfeatures, fields_to_display, start_earliest, end_latest, rfc_ratio, committed_ratio, total_spent, total_remaining)

# NOTE: the fields will be shown in the backlog table per below sequence, if not hidden
def jira_get_ca_items(fid, query_done=False):
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
        #10: Sub_Feature
        
        'RC_FB': 'customfield_43490',
        'FB_Committed_Status': 'customfield_38758', #value
        'Stretch_Goal_Reason': 'customfield_43893', #value
        'Risk_Status': 'customfield_38754',     #value
        'Risk_Details': 'customfield_38435',
        'Logged_Effort': 'customfield_43290',
    }

    keys_to_hide = ['Assignee_Email', 'Item_ID', 'Summary', 'FB_Committed_Status', 'Stretch_Goal_Reason', 'Risk_Status', 'Risk_Details', 'Logged_Effort', 'RC_FB']
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
        text2 = issue['fields'][JIRA_FIELD_TEXT2]
        risk_status = issue['fields'][JIRA_FIELD_RISK_STATUS]['value']
        #print(f'{fid} key: {jira_key} Text2:{text2}\n')
        return {'status': 'success', 'text2': text2, 'jira_key': jira_key, 'risk_status': risk_status}

    except Exception as e:
        print("Error in jira_get_text2():\n" + str(e))
        return {'status': 'error', 'message': str(e)}

def jira_set_text2(jira_key, text2, risk_status):
    try:
        jira = _initJira()
        issue = jira.issue(jira_key, expand="changelog")
        update_dict = {
            JIRA_FIELD_TEXT2: text2,
            JIRA_FIELD_RISK_STATUS: {'value': risk_status}
        }
        issue.update(fields = update_dict)
        return {'status': 'success'}

    except Exception as e:
        print("Error in jira_set_text2():\n" + str(e))
        return {'status': 'error', 'message': str(e)}