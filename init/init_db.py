# https://gitlabe2.ext.net.nokia.com/boam-fh-tools/fronthaul-mee-bot/-/blob/master/sample.ipynb
# pip install jira

from jira import JIRA
jira = JIRA(server = "https://jiradc.ext.net.nokia.com", basic_auth=('qwn783', 'Lovelife!'))
#results = jira.search_issues('''project = MEE AND component in (SOAM_BBC, BOAM_FRONTHAUL, FA_FH_RUMGMT) AND status not in (Done, Obsolete, Post-checked, "In Progress") ORDER BY priority DESC''', 0, 200, expand="changelog")

fields='customfield_38702,customfield_38703,customfield_38709,customfield_38695,customfield_43891,customfield_48390,customfield_38715,customfield_38716,customfield_38728,customfield_38754,labels,summary,description,customfield_38727,customfield_38728'
results = jira.search_issues('''
    project in (FFB) and status not in (done, obsolete) and "FOT Leader" = qwn783
''', 0, 200, expand="changelog", fields=fields)

print("Total results={}".format(len(results)))

#print(results[1].fields.__dict__)

with open("jira_result.html", 'w', encoding='utf-8') as out:
    html = '<html><head><meta charset="utf-8"><style>'
    html = html + '.field {color: #4da0ff;font-weight: bold;}'
    html = html + '</style></head><body><table>'

    out.write(html)
    item = results[4]
    for field_name in dir(item.fields):
        # 忽略 Python 的特殊方法和私有属性
        if not field_name.startswith('__'):
            value = getattr(item.fields, field_name)
            # 如果值为空，则忽略此字段
            if value:
                #print(f'{field_name}={value}')
                out.write(f"<tr><td class='field'>{field_name}</td> <td>{value}</td></tr>\n")

    out.write('</table></body></html>')


for item in results:
    fid = item.fields.customfield_38702 #customfield_37381 #ItemID
    name = item.fields.customfield_38703
    pdm = item.fields.customfield_38709 #PDM
    fotl = item.fields.customfield_38695 #FOT Leader
    apm = item.fields.customfield_43891 #APM
    lese = item.fields.customfield_48390 #LESE
    fp_link = item.fields.customfield_38715 #FP Link
    priority = item.fields.customfield_38716
    commit_status = item.fields.customfield_38728
    risk_level = item.fields.customfield_38754
    labels = item.fields.labels
    summary = item.fields.summary
    desc = item.fields.description
    text2 = item.fields.customfield_38727
    milestone = item.fields.customfield_38728 #Candidate for P2 content
    print(fid, summary)
    