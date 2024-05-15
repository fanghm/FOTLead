# JIRA script examples: https://gitlabe2.ext.net.nokia.com/boam-fh-tools/fronthaul-mee-bot/-/blob/master/sample.ipynb
# pip install jira

import sqlite3
from jira import JIRA
from datetime import datetime, timedelta, date

def dumpAsHtml(item):
    fid, _ = item.fields.summary.split(' ', 1)
    with open(fid.strip() + "_info.html", 'w', encoding='utf-8') as out:
        html = '<html><head><meta charset="utf-8"><style>'
        html = html + '.field {color: #4da0ff;font-weight: bold;}'
        html = html + '</style></head><body><table>'
        out.write(html)

        count = 0
        for field_name in dir(item.fields):
            # 忽略 Python 的特殊方法和私有属性
            if not field_name.startswith('__'):
                value = getattr(item.fields, field_name)
                # 如果值为空，则忽略此字段
                if value:
                    #print(f'{field_name}={value}')
                    out.write(f"<tr><td class='field'>{field_name}</td> <td>{value}</td></tr>\n")
                    count += 1

        out.write('</table></body></html>')
    print(f"{fid} - total fields: {count}\n")

def updateDb(results):
    conn = sqlite3.connect('../db.sqlite3')
    cursor = conn.cursor()

    for item in results:        
        #fid = item.fields.customfield_38702 #customfield_37381 #ItemID
        #name = item.fields.customfield_38703    #none for CNI
        labels = ', '.join(item.fields.labels) if item.fields.labels else 'N/A'
        summary = item.fields.summary #get name from summary as no dedicated 'name' field for CNI
        if summary.startswith('CNI'):
            fid, name = summary.split(' - ', 1)
            fp_link = 'https://jiradc.ext.net.nokia.com/browse/' +  fid.strip()

            pdm = item.fields.assignee.displayName if item.fields.assignee else 'N/A'
        else:
            fid, name = summary.split(' ', 1)
            fp_link = item.fields.customfield_38715 #FP Link

            desc = item.fields.description # too much text for CNI
            deps = item.fields.customfield_44990 #pre-condition, no such field for CNI
            milestone = item.fields.customfield_38728 #eg: Candidate for P2 content

            pdm = item.fields.customfield_38709 if item.fields.customfield_38709 else 'N/A' #str object instead of User object 
            labels = f"{desc}\n{deps}\n{milestone}\n{labels}"
        
        release = item.fields.customfield_38710[:4] # might be incorrect for LLF
        priority = int(item.fields.customfield_38716) if item.fields.customfield_38716 else 0
        #commit_status = item.fields.customfield_38728 #Committed at I1.1
        #fs_status = item.fields.customfield_38705   #FS3 Approved
        risk = item.fields.customfield_38754.value if item.fields.customfield_38754 else 'Green'
        text2 = item.fields.customfield_38727 if item.fields.customfield_38727 else 'N/A'
        
        fotl = item.fields.customfield_38695.displayName if item.fields.customfield_38695 else 'N/A' #FOT Leader
        apm = item.fields.customfield_43891.displayName if item.fields.customfield_43891 else 'N/A' #APM
        lese = item.fields.customfield_48390.displayName if item.fields.customfield_48390 else 'N/A' #LESE

        print(f"---> {fid} <---")
        print('Starting to insert into Feature table...')
        cursor.execute('''
            INSERT INTO fotd_feature (id, name, release, priority, milestone, phase,
            fusion_link, fp_link, cfam_link, gantt_link, rep_link, risk, text2, desc, created_at )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (fid, name, release, priority, 'tba', 'Planning',
         'jira link', fp_link, 'cfam doc', 'powerbi link', 'rep link', risk, text2, labels))
        
        # 获取最后一次插入的行的 ID
        #feature_id = cursor.lastrowid
        
        print('starting to insert into FeatureRoles table...')
        cursor.execute('''
            INSERT INTO fotd_featureroles (feature_id, pdm, fot_lead, apm, cfam_lead, lese, ftl, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (fid, pdm, fotl, apm, 'tba', lese, 'N/A', ''))
        
        print('starting to insert into FeatureUpdate table...')
        cursor.execute('''insert into fotd_featureupdate (feature_id, update_date, update_text, is_key, created_at)
            values (?, date('now'), 'Initial creation', 1, CURRENT_TIMESTAMP)
        ''', (fid,))

        # 提交事务
        conn.commit()

    # 关闭连接
    conn.close()

def debug(results):
    for item in results:   
        text2 = item.fields.customfield_38727 if item.fields.customfield_38727 else 'N/A'
        print("text2: " + text2);

def initFeatures():
    #jira = JIRA(server = "https://jiradc.ext.net.nokia.com", basic_auth=('bobot', 'J1ra_Env$'))
    jira = JIRA(server = "https://esjirp66.emea.nsn-net.net", basic_auth=('qwn783', 'Lovelife!'))
    # JIRA query example: 
    # results = jira.search_issues('''project = MEE AND component in (SOAM_BBC, BOAM_FRONTHAUL, FA_FH_RUMGMT) AND status not in (Done, Obsolete, Post-checked, "In Progress") ORDER BY priority DESC''', 0, 200, expand="changelog")

    fields='customfield_38710,customfield_38709,customfield_38695,customfield_43891,customfield_48390,customfield_44990,customfield_38715,customfield_38716,customfield_38754,labels,summary,description,customfield_38727,customfield_38728'
    jql_str = '''project in (FFB) and status not in (done, obsolete) and "FOT Leader" = qwn783'''
    results = jira.search_issues(jql_str 
        , 3 #startAt 
        , 1 #200, #maxResults
        #, fields=fields
        #, expand="changelog"
        #, json_result=True
        )

    print("Total results={}\n".format(len(results)))
    #print(results[1].fields.__dict__)

    #dumpAsHtml(results[0])
    #dumpAsHtml(results[2])
    #updateDb(results)
    debug(results)

yearly_fb_start = [
    ('2020', '2022-01-01'),
    ('2021', '2022-01-01'),
    ('2022', '2022-01-01'),
    ('2023', '2022-01-01'),
    ('2024', '2022-01-03'),
    ('2025', '2022-01-01'),
    ('2026', '2022-01-01'),
]
def initFbDates():
    conn = sqlite3.connect('../db.sqlite3')
    cursor = conn.cursor()

    start = datetime.strptime('2024-01-03', "%Y-%m-%d").date()
    for i in range(1, 27):
        end = start + timedelta(days=13)        
        # print('FB24%02d: %s - %s %s' % (i, start.strftime('%m/%d'), end.strftime('%m/%d'), '***' if (date.today()>=start and date.today()<=end) else ''))
        cursor.execute('''
            INSERT INTO fotd_sprint(fb, start_date, end_date)
            VALUES (?, ?, ?)
        ''', (f'FB24{i:02d}', start, end))
        start = end + timedelta(days=1)

    conn.commit()
    conn.close()

initFbDates()