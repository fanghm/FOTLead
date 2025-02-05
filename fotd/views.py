import json
import logging
import traceback
from datetime import date, datetime

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from jira import JIRAError

from .mailer import send_email
from .models import (
    BacklogQuery,
    Feature,
    FeatureRoles,
    FeatureUpdate,
    ProgramBoundary,
    Sprint,
    Task,
    TeamMember,
)
from .myjira import jira_get_ca_items, jira_get_text2, jira_set_text2


# @login_required
def index(request):
    features = Feature.objects.exclude(phase='Done').order_by('release', 'id')

    features_with_task_count = []
    for feature in features:
        task_count = feature.task_set.exclude(status='closed').count()
        features_with_task_count.append((feature, task_count))

    # TODO: update the session variables only when the date changes
    request.session['today'] = date.today().strftime('%Y/%m/%d')
    request.session['fb'], sprint_day, passed_percent = _get_fb_info()

    week_number = date.today().isocalendar()[1]
    weekday = date.today().weekday() + 1
    request.session['wk'] = f'Wk{week_number}.{weekday}'

    context = {
        'features_with_task_count': features_with_task_count,
        'sprint_day': sprint_day,
        'passed_percent': passed_percent,
        'top_tasks': Task.objects.filter(top=True, status='Ongoing'),
    }

    return render(request, 'fotd/index.html', context)


def detail(request, fid):
    feature = get_object_or_404(Feature, id=fid)
    updates = FeatureUpdate.objects.filter(feature__id=fid).order_by('update_date')
    # roles = FeatureRoles.objects.get(feature__id=fid)

    tasks = feature.task_set.exclude(status='closed').order_by('due')

    # Fetch the latest 3 status updates of each task
    for task in tasks:
        task.statusUpdates = task.statusupdate_set.order_by('-update_date')[:3]

    # Create a context dictionary with the fetched data
    context = {
        'feature': feature,
        'updates': updates,
        'tasks': tasks,
        'today': date.today(),
    }
    return render(request, 'fotd/detail.html', context)


def feature(request, fid):
    feature = Feature.objects.get(id=fid)
    rel = feature.release[-4:]  # use the last 4 chars since LLF has multiple releases

    context = {
        'feature': feature,
        'ProgramBoundary': ProgramBoundary.objects.filter(release=rel),
    }
    return render(request, 'fotd/feature.html', context)


@csrf_exempt
def ajax_feature_update(request, fid):
    if request.method == 'POST':
        feature = Feature.objects.get(id=fid)

        for key, value in request.POST.items():
            if hasattr(feature, key):
                if key == 'boundary':  # foreign key
                    key = 'boundary_id'

                if value:
                    setattr(feature, key, value)

        feature.save()
        response_data = {'status': 'success', 'message': 'Feature updated successfully'}
        return JsonResponse(response_data)
    else:
        return JsonResponse({'status': 'fail', 'message': 'Invalid request'})


@csrf_exempt
def ajax_feature_status(request, fid):
    feature = Feature.objects.get(id=fid)

    if request.method == 'POST':
        update_text = request.POST['update_text']

        date_str = request.POST['date_str']
        update_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        logging.debug(f"date value: {update_date}, type: {type(update_date)}")

        update = FeatureUpdate.objects.create(
            feature=feature,
            update_date=update_date,
            is_key=True,
            update_text=update_text,
        )
        update_date_str = update.update_date.strftime("%Y/%m/%d")
        return HttpResponse(f'{update_date_str}: {update.update_text}')
    else:
        return HttpResponse('No POST data')


def login(request):
    return render(request, 'fotd/login.html')


# yy: year in 2 digits, e.g. 22 for 2022
def fb(request, yy):
    if len(yy) == 4 and yy.isdigit():
        yy = yy[2:]
    sprints = Sprint.objects.filter(fb__startswith='FB' + yy).order_by('fb')
    context = {'sprints': sprints, 'today': date.today().strftime('%Y-%m-%d')}
    return render(request, 'fotd/fb.html', context)


# TODO: this can be improved, should move to globals.py
# start to search in 4 continous fbs due to below exception on 7/31: current
# sprint not found from ['FB2413', 'FB2414', 'FB2415']
def _get_fb_info():
    today = date.today()
    start_fb = f'FB{str(today.year)[-2:]}{today.month*2-1:02d}'
    sprints = Sprint.objects.filter(fb__gte=start_fb).order_by('fb')[:4]

    for sprint in sprints:
        if today >= sprint.start_date and today <= sprint.end_date:
            sprint_day = (today - sprint.start_date).days + 1
            print(f'{today} is in {sprint.fb}, day {sprint_day}')
            passed_percent = int(sprint_day * 100 / 14)

            # if (today >= sprint.start_date + timedelta(days=7)):
            #     return (sprint.fb + '.2', sprint_day, passed_percent)
            # else:
            #     return (sprint.fb + '.1', sprint_day, passed_percent)
            return (sprint.fb, sprint_day, passed_percent)

    print(f"ERROR: current sprint not found from {[sprint.fb for sprint in sprints]}")
    return ('N/A', 0, 0)


# start_fb, end_fb in the string format without "FB" prefix, eg: '2325', '2401'
# return all the fbs in between as a string list, eg: ['2325', '2326', '2401']
def _get_fbs(start_fb, end_fb):
    if end_fb > end_fb:
        return []
    elif start_fb == end_fb:
        return [start_fb]
    else:
        fbs = [start_fb]
        start = int(start_fb)
        while start < int(end_fb):
            if start % 100 == 26:  # 26 fbs in each year
                start = (int(start / 100) + 1) * 100 + 1
            else:
                start += 1
            fbs.append(str(start))
        return fbs


def _add_tag(item, tag):
    if 'tags' not in item:
        item['tags'] = tag
    else:
        item['tags'] += " " + tag


def _add_hint(item, hint):
    if 'hints' not in item:
        item['hints'] = hint
    else:
        item['hints'] += "<br/>" + hint


def check_plan_fitting(result, boundary):
    """
    Check if the plan is fitting to the Program boundary, the rules are as below:
    - Activity type - Entity Specification: sw_done
    - Activity type - SW: sw_done
    - Activity type - CuDo: cudo
    - Activity type - System Testing:
    -   if CA is VAL_PET/VAL_FIVE: pet_five_done
    -   else: st_done
    """

    not_fitting_items = {}
    for item in result:
        if not item['End_FB']:
            continue

        not_fitting = False
        activity_type = item['Activity_Type']
        end_fb = item['End_FB']
        key = item['Key']

        if (
            activity_type in ('SW', 'Entity Specification')
            and end_fb > boundary.sw_done
        ):  # NO QA
            not_fitting_items[key] = boundary.sw_done
            not_fitting = True
        elif activity_type == 'CuDo' and end_fb > boundary.cudo:
            not_fitting_items[key] = boundary.cudo
            not_fitting = True
        elif activity_type == 'System Testing':
            if item['Competence_Area'] in ('VAL_PET', 'VAL_FIVE'):
                if end_fb > boundary.pet_five_done:
                    not_fitting_items[key] = boundary.pet_five_done
                    not_fitting = True
            else:
                if end_fb > boundary.st_done:
                    not_fitting_items[key] = boundary.st_done
                    not_fitting = True

        if not_fitting:
            _add_tag(item, 'not_fitting')
            _add_hint(
                item, f"Not fitting to Program boundary: {not_fitting_items[key]}"
            )  # NO QA

    if not_fitting_items:
        print(f"not_fitting_items: {not_fitting_items}")

    return not_fitting_items


def check_exec_issue(result, current_fb):
    for item in result:
        if not item['End_FB']:
            continue

        if item['End_FB'] == current_fb:
            if item['FB_Committed_Status'] == 'Not Committed':
                _add_tag(item, "not_committed")
                stretch_goal_reason = item.get('Stretch_Goal_Reason', "Not set")
                hint_message = (
                    f"Not committed to current FB, "
                    f"stretch goal reason: {stretch_goal_reason}"
                )
                _add_hint(item, hint_message)
            else:
                _add_tag(item, "duesoon")
                _add_hint(item, "Due at current FB")

        elif item['End_FB'] < current_fb:
            _add_tag(item, "overdue")
            _add_hint(item, f"Item not done at {item['End_FB']} and End FB not updated")
        else:
            pass

        if item['RC_FB'] and item['End_FB'] > item['RC_FB']:
            _add_tag(item, "delayed")
            _add_hint(item, "Delayed! Committed to deliver at " + item['RC_FB'])

        # if item['Start_FB'] < current_fb and item['Progress'] <= 0:
        #     _add_tag(item, "should_start")
        #     _add_hint(item, "Should have started but no progress")

    return


def detect_changes(query, result):
    changes = ''
    new_keys = [
        item['Key']
        for item in result
        if not any(item['Key'] == old_item['Key'] for old_item in query.backlog_items)
    ]
    if new_keys:
        print(f"New added keys: {new_keys}")
        changes += f"New added: {new_keys}; "

    changed_items = {
        item['Key']: {'previous': old_item['End_FB'], 'current': item['End_FB']}
        for old_item in query.backlog_items
        for item in result
        if item['Key'] == old_item['Key'] and item['End_FB'] != old_item['End_FB']
    }

    if changed_items:
        endfb_changed_str = ";".join(
            [
                f"{key}: {value['previous']}->{value['current']}"
                for key, value in changed_items.items()
            ]
        )
        print(f"End_FB changes: {endfb_changed_str}")
        changes += f"EndFB changes: {endfb_changed_str}"

    return (new_keys, changed_items, changes)


def backlog(request, fid):
    first_query = False
    jira_query = False

    refresh_query = 'refresh' in request.GET
    query_done = include_done = False
    if 'query_done' in request.GET:
        query_done = request.GET['query_done'] == 'true'

    result = []
    item_links = {}
    start_earliest = end_latest = ''
    display_fields = None
    new_keys = []
    changed_items = {}
    max_results = MAX_RESULT = 200

    query = BacklogQuery.objects.filter(feature_id=fid).first()
    if query is None:
        first_query = True
    else:
        result = query.backlog_items
        item_links = query.item_links
        start_earliest = query.start_earliest
        end_latest = query.end_latest
        display_fields = query.display_fields
        include_done = query.include_done
        new_keys = query.new_keys
        changed_items = query.changed_items

        if len(result) % MAX_RESULT == 0:
            max_results = len(result) * 2

    print(f"{fid}: query_done={query_done}, include_done={include_done}")
    if refresh_query or first_query or (query_done != include_done):
        jira_query = True
        print(f"{fid}: query from JIRA w/ max_results={max_results}")
        try:
            query_result = jira_get_ca_items(fid, max_results, query_done)
            result = query_result.backlog_items
            start_earliest = query_result.start_earliest
            end_latest = query_result.end_latest
            display_fields = query_result.display_fields

        except JIRAError as e:
            error_message = f"Failed to connect to JIRA: {e}"
            messages.error(request, error_message)
            return render(request, 'fotd/error.html')
        except Exception:
            print(f"Exception in JIRA query: {traceback.format_exc()}")
            # Django message framework will add the message to the context,
            # needless to pass it explicitly
            # TODO: report the issue automatically via REST interface
            error_message = (
                "Failed to query from JIRA server, pls report the issue.<br>"
                "For timeout, please make sure you're connected to Nokia Intranet."
            )
            messages.error(request, error_message)
            return render(request, 'fotd/error.html')

        update_defaults = query_result.__dict__
        if not first_query and not query_done:
            (new_keys, changed_items, changes) = detect_changes(query, result)
            update_defaults['new_keys'] = new_keys
            update_defaults['changed_items'] = changed_items
            update_defaults['changes'] = changes

        # 使用 defaults 字典更新数据库
        try:
            BacklogQuery.objects.update_or_create(
                feature_id=fid,
                defaults=update_defaults,
            )
        except Exception as e:
            print(f"Failed to create/update backlog record: {e}")

    current_fb = request.session['fb'][2:]
    if not (start_earliest and end_latest):  # no plan at all, for a new feature
        print(f"{fid}: start/endfb is empty, no plan at all")
        display_sprints = [current_fb]
    elif start_earliest < current_fb and not query_done:
        display_sprints = _get_fbs(current_fb, end_latest)
    else:
        display_sprints = _get_fbs(start_earliest, end_latest)

    context = {
        'fid': fid,
        'display_fields': display_fields,
        'display_sprints': display_sprints,
        # 'rfc_ratio': rfc_ratio,
        # 'committed_ratio': committed_ratio,
        'new_keys': new_keys,
        'changed_items': changed_items,
        'current_fb': current_fb,
        'link_prefix': 'https://jiradc.ext.net.nokia.com/browse/',
        'query_done': query_done,
    }

    if not jira_query:
        context['query_time'] = query.query_time

    if not query_done:
        check_exec_issue(result, current_fb)

        try:
            boundary = Feature.objects.get(id=fid).boundary
            if not boundary:
                release = Feature.objects.get(id=fid).release
                boundary = ProgramBoundary.objects.get(
                    release=release[-4:], category='I1.2/P2 content'
                )

            if boundary:
                context['boundary'] = boundary
                not_fitting_items = check_plan_fitting(result, boundary)
                if not_fitting_items:
                    context['not_fitting_items'] = not_fitting_items
        except Exception as e:
            print(f"Exception in backlog(): {e}")
            traceback.print_exc()

    context.update(
        {
            'backlog_items': result,
            'item_links': json.dumps(item_links),
        }
    )

    return render(request, 'fotd/backlog.html', context)


def fot(request, pk):
    try:
        feature_roles = FeatureRoles.objects.get(feature__id=pk)
    except ObjectDoesNotExist:
        feature_roles = None

    context = {
        'fid': pk,
        'role': feature_roles,
        'team_members': TeamMember.objects.filter(feature__id=pk),
    }

    if feature_roles:
        return render(request, 'fotd/fot.html', context)
    else:
        return render(request, 'fotd/fot_add.html', context)


def fot_add(request, fid):
    try:
        feature_roles = FeatureRoles.objects.get(feature__id=fid)
    except ObjectDoesNotExist:
        feature_roles = None

    context = {
        'fid': fid,
        'role': feature_roles,
        # 'role': get_object_or_404(FeatureRoles, feature__id=fid),
        'team_members': TeamMember.objects.filter(feature__id=fid),
    }
    return render(request, 'fotd/fot_add.html', context)


@csrf_exempt
def ajax_add_feature_roles(request, fid):
    if request.method == 'POST':
        feature = Feature.objects.get(id=fid)
        new_role, created = FeatureRoles.objects.update_or_create(
            feature=feature,
            defaults={
                'pdm': request.POST.get('pdm'),
                'apm': request.POST.get('apm'),
                'cfam_lead': request.POST.get('cfam_lead'),
                'fot_lead': request.POST.get('fot_lead'),
                'lese': request.POST.get('lese'),
                'ftl': request.POST.get('ftl'),
                'comment': request.POST.get('comment'),
            },
        )

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@csrf_exempt
def ajax_add_fot_members(request, fid):
    feature = Feature.objects.get(id=fid)

    if request.method == 'POST':
        team_members = json.loads(request.body)
        for team_member in team_members:
            new_member = TeamMember(
                team=team_member['team'],
                apo=team_member['apo'],
                role=team_member['role'],
                name=team_member['name'],
                comment=team_member['comment'],
                feature=feature,
            )
            new_member.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


def add_program_boundary(request):
    context = {
        'boundaries': ProgramBoundary.objects.all().order_by('release'),
    }
    return render(request, 'fotd/boundary.html', context)


@csrf_exempt
def ajax_program_boundary(request):
    if request.method == 'POST':
        fields = [
            'release',
            'category',
            'sw_done',
            'et_ec',
            'et_fer',
            'et_done',
            'st_ec',
            'st_fer',
            'st_done',
            'pet_five_ec',
            'pet_five_fer',
            'pet_five_done',
            'ta',
            'cudo',
        ]
        data = {field: request.POST.get(field).strip() for field in fields}
        program_boundary = ProgramBoundary(**data)

        try:
            program_boundary.save()
            return JsonResponse({'status': 'success'})
        except IntegrityError:
            message = (
                'A unique constraint violation occurred, '
                'do not import the same feature boundary repeatedly.'
            )
            return JsonResponse({'status': 'error', 'message': message}, status=400)
        except Exception as e:
            print(f"Failed to save into database: {e}")
            message = 'An unexpected error occurred.'
            return JsonResponse({'status': 'error', 'message': message}, status=500)

    return JsonResponse({'status': 'error'}, status=400)


REQ_TYPE_PLANNING = "Planning"
REQ_TYPE_RFC = "RfC"


@csrf_exempt
def ajax_send_email(request, email_type):
    context = json.loads(request.body)
    context.update(
        {
            'fot_lead': request.user.username,
        }
    )
    # print(f"email_type: {email_type}, context: {context}")

    if email_type == REQ_TYPE_RFC:
        send_email(email_type, context)
        pass
    elif email_type == REQ_TYPE_PLANNING:
        # specific handling for Planning email
        send_email(email_type, context)
        pass
    else:
        pass

    return JsonResponse({'status': 'success', 'email_type': email_type})


@csrf_exempt
def ajax_get_text2(request, fid):
    result = jira_get_text2(fid)
    # print(f"ajax_get_text2: {result}")

    if result['status'] == 'success':
        return JsonResponse(result)
    else:
        return JsonResponse(result, status=500)


@csrf_exempt
@require_POST
def ajax_set_text2(request, fid):
    jira_key = request.POST.get('jira_key')
    text2_desc = request.POST.get('text2_desc')
    risk_status = request.POST.get('risk_status')
    result = jira_set_text2(jira_key, text2_desc, risk_status)

    if result['status'] == 'success':
        feature = Feature.objects.get(id=fid)
        feature.text2_desc = text2_desc
        feature.text2_date = date.today()
        feature.risk_status = risk_status
        feature.risk_summary = request.POST.get('risk_summary')
        feature.save()
        return JsonResponse(result)
    else:
        return JsonResponse(result, status=500)
