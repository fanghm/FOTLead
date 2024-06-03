from jira import JIRA

def _queryJira(jql_str, field_dict):
    jira = JIRA(server = "https://esjirp66.emea.nsn-net.net", basic_auth=('qwn783', 'Lovelife!'))
    json_result = jira.search_issues(jql_str, 0, 50, fields=list(field_dict.values()), json_result=True)

    result = []
    start_earliest = None
    end_latest = None
    for issue in json_result['issues']:
        issue_dict = {'Key': issue['key']}
        for field_name, custom_name in field_dict.items():
            value = issue['fields'][custom_name]
            if not value:
                issue_dict[field_name] = None
            elif field_name in ('Competence_Area', 'Activity_Type', 'RC_Status', 'RC_FB'):
                issue_dict[field_name] = value['value']
            elif field_name in ('Assignee'):
                issue_dict[field_name] = value['displayName']
            else:
                issue_dict[field_name] = value

        if issue_dict['Time_Remaining']:
            remaining = issue_dict['Time_Remaining']
        else:
            remaining = issue_dict['Time_Remaining'] = 0

        if issue_dict['Original_Estimate'] and issue_dict['Original_Estimate'] > remaining:
            issue_dict['Progress'] = (issue_dict['Original_Estimate'] - remaining) / issue_dict['Original_Estimate'] * 100
        else:
            issue_dict['Progress'] = 0
        
        if start_earliest is None or (issue_dict['Start_FB'] and issue_dict['Start_FB'] < start_earliest):
            start_earliest = issue_dict['Start_FB']

        if end_latest is None or (issue_dict['End_FB'] and issue_dict['End_FB'] > end_latest):
            end_latest = issue_dict['End_FB']
            
        result.append(issue_dict)

    return result, (start_earliest, end_latest)

def queryJiraCaItems(fid):
    field_dict = {
        # 'Item ID': 'customfield_38702',
        'Summary': 'summary',
        'Competence_Area': 'customfield_38690',
        'Activity_Type': 'customfield_38750',
        'Assignee': 'assignee',
        'Start_FB': 'customfield_38694',
        'End_FB': 'customfield_38693',
        'Original_Estimate': 'customfield_43292',
        'Time_Remaining': 'customfield_43291',
        'RC_Status': 'customfield_38728',
        'RC_FB': 'customfield_43490',
    }

    jql_str = f'''("Feature ID" ~ {fid}) and issuetype = "Competence Area" AND status not in (done, obsolete) order by "Item ID" '''
    return _queryJira(jql_str, field_dict)