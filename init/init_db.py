# pip install jira

import json
import sqlite3
from datetime import date, datetime, timedelta

from django.conf import settings
from jira import JIRA

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FOTLead.settings')
# django.setup()


def _initJira():
    return JIRA(
        server="https://jiradc.ext.net.nokia.com",
        basic_auth=(settings.AUTH_USERNAME, settings.AUTH_PASSWORD),
    )


def dumpAsHtml(item):
    fid, _ = item.fields.summary.split(' ', 1)
    with open(fid.strip() + "_info.html", 'w', encoding='utf-8') as out:
        html = '<html><head><meta charset="utf-8"><style>'
        html = html + '.field {color: #4da0ff;font-weight: bold;}'
        html = html + '</style></head><body><table>'
        out.write(html)

        count = 0
        for field_name in dir(item.fields):
            if not field_name.startswith('__'):
                value = getattr(item.fields, field_name)
                if value:
                    # print(f'{field_name}={value}')
                    out.write(
                        f"<tr><td class='field'>{field_name}</td> "
                        f"<td>{value}</td></tr>\n"
                    )
                    count += 1

        out.write('</table></body></html>')
    print(f"{fid} - total fields: {count}\n")


# add features into the fotd_feature table
def updateDb(results):
    conn = sqlite3.connect('../db.sqlite3')
    cursor = conn.cursor()

    for item in results:
        # fid = item.fields.customfield_38702 #customfield_37381 #ItemID
        # name = item.fields.customfield_38703    #none for CNI
        labels = ', '.join(item.fields.labels) if item.fields.labels else 'N/A'
        desc = item.fields.description
        summary = (
            item.fields.summary
        )  # get name from summary as no dedicated 'name' field for CNI
        if summary.startswith('CNI'):
            fid, name = summary.split(' - ', 1)
            fp_link = 'https://jiradc.ext.net.nokia.com/browse/' + fid.strip()

            pdm = item.fields.assignee.displayName if item.fields.assignee else 'N/A'
            desc = (
                labels + '\n' + desc.substring(0, 200)
            )  # too much text for CNI, limit to 200 chars
        else:
            fid, name = summary.split(' ', 1)
            fp_link = item.fields.customfield_38715  # FP Link

            deps = item.fields.customfield_44990  # pre-condition, no such field for CNI
            milestone = item.fields.customfield_38728  # eg: Candidate for P2 content

            pdm = (
                item.fields.customfield_38709
                if item.fields.customfield_38709
                else 'N/A'
            )  # str object instead of User object
            desc = f"{desc}\n{deps}\n{milestone}\n{labels}"

        release = item.fields.customfield_38710[:4]  # might be incorrect for LLF
        priority = (
            int(item.fields.customfield_38716) if item.fields.customfield_38716 else 0
        )
        # commit_status = item.fields.customfield_38728 #Committed at I1.1
        # fs_status = item.fields.customfield_38705   #FS3 Approved
        risk = (
            item.fields.customfield_38754.value
            if item.fields.customfield_38754
            else 'Green'
        )
        text2 = (
            item.fields.customfield_38727 if item.fields.customfield_38727 else 'N/A'
        )

        fotl = (
            item.fields.customfield_38695.displayName
            if item.fields.customfield_38695
            else 'N/A'
        )  # FOT Leader
        apm = (
            item.fields.customfield_43891.displayName
            if item.fields.customfield_43891
            else 'N/A'
        )  # APM
        lese = (
            item.fields.customfield_48390.displayName
            if item.fields.customfield_48390
            else 'N/A'
        )  # LESE

        print(f"---> {fid} <---")
        print('Starting to insert into Feature table...')
        cursor.execute(
            '''
            INSERT INTO fotd_feature (id, name, release, priority, milestone, phase,
            fusion_link, fp_link, cfam_link, gantt_link, rep_link,
            risk, text2, desc, created_at )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''',
            (
                fid,
                name,
                release,
                priority,
                'tba',
                'Planning',
                'jira link',
                fp_link,
                'cfam doc',
                'powerbi link',
                'rep link',
                risk,
                text2,
                desc,
            ),
        )

        # 获取最后一次插入的行的 ID
        # feature_id = cursor.lastrowid

        print('starting to insert into FeatureRoles table...')
        cursor.execute(
            '''
            INSERT INTO fotd_featureroles (feature_id, pdm, fot_lead, apm, cfam_lead,
            lese, ftl, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''',
            (fid, pdm, fotl, apm, 'tba', lese, 'N/A', ''),
        )

        print('starting to insert into FeatureUpdate table...')
        cursor.execute(
            '''insert into fotd_featureupdate
            (feature_id, update_date, update_text, is_key, created_at)
            values (?, date('now'), 'Initial creation', 1, CURRENT_TIMESTAMP)
        ''',
            (fid,),
        )

        # 提交事务
        conn.commit()

    # 关闭连接
    conn.close()


def check_text2(results):
    for item in results:
        text2 = (
            item.fields.customfield_38727 if item.fields.customfield_38727 else 'N/A'
        )
        print("text2: " + text2)


def initFeatures():
    jira = _initJira()
    # JIRA query example:
    # results = jira.search_issues('''project = MEE AND component
    # in (SOAM_BBC, BOAM_FRONTHAUL, FA_FH_RUMGMT)
    # AND status not in (Done, Obsolete, Post-checked, "In Progress")
    # ORDER BY priority DESC''', 0, 200, expand="changelog")

    fields = (
        'customfield_38710,customfield_38709,customfield_38695,customfield_43891,'
        'customfield_48390,customfield_44990,customfield_38715,customfield_38716,'
        'customfield_38754,labels,summary,description,'
        'customfield_38727,customfield_38728'
    )
    jql_str = (
        'project in (FFB) and status not in (done, obsolete) '
        'and "FOT Leader" = qwn783'
    )
    results = jira.search_issues(
        jql_str,
        3,  # startAt
        1,  # 200, #maxResults
        fields=fields,
        # , expand="changelog"
        # , json_result=True
    )

    print("Total results={}\n".format(len(results)))
    # print(results[1].fields.__dict__)

    # dumpAsHtml(results[0])
    # dumpAsHtml(results[2])
    # updateDb(results)
    # check_text2(results)


def jiraQuery(fid, field_dict):
    jira = _initJira()
    jql_str = (
        f'("Feature ID" ~ {fid}) and issuetype = "Competence Area" '
        f'AND status not in (obsolete) order by "Item ID"'
    )
    print('jql: ' + jql_str)
    json_result = jira.search_issues(
        jql_str, 0, 200, json_result=True
    )  # , fields=list(field_dict.values())

    # print("Total results={}\n".format(len(results)))
    # print(json_result)
    with open(f'{fid}.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(json_result))

    # for issue in json_result['issues']:
    #     print(issue['key'])
    #     for field_name, custom_name in field_dict.items():
    #         value = issue['fields'][custom_name]
    #         if not value:
    #             print(f"{field_name}=>None")
    #         elif field_name in ('Competence Area', 'Activity Type', 'RC Status'):
    #             print(f"{field_name}=>{value['value']}")
    #         elif field_name in ('Assignee'):
    #             print(f"{field_name}=>{value['displayName']}")
    #         else:
    #             print(f"{field_name}=>{value}")
    #     print('---')
    return json_result


# short fb (in 2 weeks) starts from year 2022
# Dove: https://app.powerbi.com/groups/me/apps/85a81867-e9aa-4ef2-93d1-f93e3a7ef551/
# reports/2d8bffaa-0679-499f-876d-b6668c85ab86/ReportSection247cdc907596091d4603?
# experience=power-bi
yearly_fb_start = {
    '2022': '2022-01-05',
    '2023': '2023-01-04',
    '2024': '2024-01-03',
    '2025': '2025-01-01',
}


# init the fotd_sprint table with fb dates
def initFbDates():
    conn = sqlite3.connect('../db.sqlite3')
    cursor = conn.cursor()

    start = datetime.strptime('2025-01-01', "%Y-%m-%d").date()
    for i in range(1, 27):
        end = start + timedelta(days=13)
        print(
            'FB25%02d: %s - %s %s'
            % (
                i,
                start.strftime('%m/%d'),
                end.strftime('%m/%d'),
                '***' if (date.today() >= start and date.today() <= end) else '',
            )
        )
        cursor.execute(
            '''
            INSERT INTO fotd_sprint(fb, start_date, end_date)
            VALUES (?, ?, ?)
        ''',
            (f'FB25{i:02d}', start, end),
        )
        start = end + timedelta(days=1)

    conn.commit()
    conn.close()


# find the index a fb within the fb list
def _find_fb_index(fb_list, fb_value):
    for index, item in enumerate(fb_list):
        if item['fb'] == fb_value:
            return index

    print(f"ERROR: {fb_value} not found in the list")
    return -1


# a rewrite of the tool function for testing
def _get_fb_info(today, full_year_sprints):
    # today = date.today()
    start_fb = f'FB{str(today.year)[-2:]}{today.month*2-1:02d}'
    # sprints = Sprint.objects.filter(fb__gte=start_fb).order_by('fb')[:4]
    index_of_start_fb = _find_fb_index(full_year_sprints, start_fb)
    sprints = full_year_sprints[index_of_start_fb : index_of_start_fb + 4]  # noqa: E203
    # tune the number to see how many fbs we need to find the day's sprint
    # print(sprints)

    i = 0
    for sprint in sprints:
        i += 1
        # print(
        #     f'{today} - {sprint["fb"]} - '
        #     f'{sprint["start_date"]} - {sprint["end_date"]}'
        # )
        if today >= sprint["start_date"] and today <= sprint["end_date"]:
            # sprint_day = (today - sprint['start_date']).days + 1
            # print(f'{today} is in {sprint.fb}, day {sprint_day}')
            # passed_percent = int(sprint_day * 100 / 14)

            print(f'{today}: {i}')
            # return (sprint['fb'], sprint_day, passed_percent)
            return

    print(f"ERROR: {today} - Strange that current sprint not found from {sprints}")
    # return ('N/A', 0, 0)
    exit(1)


# test _get_fb_info
# fb_dates:
# [
#   {'fb': 'FB2501', 'start_date': '2025-01-01', 'end_date': '2025-01-14'},
# ...,
# ]
def test_get_fb_info(year):
    if year not in yearly_fb_start:
        print('fb start not defined for the year: ' + year)
        return

    start_str = yearly_fb_start[year]
    start_date = start = end = datetime.strptime(start_str, "%Y-%m-%d").date()

    fb_dates = []
    for i in range(1, 27):
        end = start + timedelta(days=13)
        # print({
        #     'fb': f'FB{year[-2:]}{i:02d}',
        #     'start': start.strftime('%Y-%m-%d'),
        #     'end': end.strftime('%Y-%m-%d')
        # })

        fb_dates.append(
            {'fb': f'FB{year[-2:]}{i:02d}', 'start_date': start, 'end_date': end}
        )

        start = end + timedelta(days=1)

    # print(fb_dates)
    start = start_date
    # end = start + timedelta(days=20)
    while start < end:
        _get_fb_info(start, fb_dates)
        start += timedelta(days=1)

    return fb_dates


fields = (
    'assignee, summary, fixVersions, customfield_38750'  # Act Type
    + ', customfield_38690'  # Competence Area
    + ', customfield_48891'  # start fb number, eg: 2412.0
    + ', customfield_38694'  # start fb
    + ', customfield_48890'  # end fb number, eg: 2410.0
    + ', customfield_38693'  # end fb
    + ', customfield_43292'  # orig ee
    + ', customfield_43291'  # remaining ee
    + ', customfield_38702'  # item id
    + ', customfield_38728'
)  # RC status

field_dict = {
    'Item ID': 'customfield_38702',
    'Competence Area': 'customfield_38690',
    'Activity Type': 'customfield_38750',
    'Assignee': 'assignee',
    # 'Start FB, eg: 2412.0': 'customfield_48891',
    'Start FB': 'customfield_38694',
    # 'end fb number, eg: 2410.0': 'customfield_48890',
    'End FB': 'customfield_38693',
    'Original Estimate': 'customfield_43292',
    'Time Remaining': 'customfield_43291',
    'RC Status': 'customfield_38728',  #
    'RC FB': 'customfield_43490',
    'Text_2': 'customfield_38727',
}


def get_text2(fid):
    jira = _initJira()
    jql_str = '''project in (FFB) AND "Feature ID" ~ ''' + fid
    print('jql: ' + jql_str)

    json_result = jira.search_issues(
        jql_str,
        0,  # startAt
        1,  # 200, #maxResults
        fields='customfield_38727',
        # expand="changelog",
        json_result=True,
    )
    # print(json.dumps(json_result))

    total = json_result['total']
    if total != 1:
        print("Unexpected result number: " + total)
        return

    issue = json_result['issues'][0]
    text2 = issue['fields']['customfield_38727']
    print(fid + ' Text2:\n' + text2)


def update_desc():
    jira = _initJira()
    issue = jira.issue("FFB-48449", expand="changelog")
    issue.update(
        assignee={'name': 'qwn783'},
        description='''
    Generated by bobot, please fill in numbers and don't remove this table!
    ''',
    )


# --- main entry ----
jiraQuery('CB011098-SR', field_dict)

# initFbDates()
# get_text2('CNI-113494')
# test_get_fb_info('2025')
