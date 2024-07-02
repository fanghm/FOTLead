import json
import logging
from datetime import date, datetime, timedelta
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers
from .models import Feature, FeatureUpdate, FeatureRoles, TeamMember, Task, StatusUpdate, Link, Sprint, BacklogQuery, ProgramBoundary
from .myjira import queryJiraCaItems
from .mailer import send_email

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

#@login_required
def index(request):
    features = Feature.objects.order_by('release', 'id')
    
    features_with_task_count = []
    for feature in features:
        task_count = Task.objects.filter(feature__id=feature.id).exclude(status__in=['Completed', 'Removed']).count()
        features_with_task_count.append((feature, task_count))

    # TODO: update the session variables only when the date changes
    request.session['today'] = date.today().strftime('%Y/%m/%d')
    request.session['wk'] = f'Wk{date.today().isocalendar()[1]}.{date.today().weekday() +1}'
    request.session['fb'], sprint_day, passed_percent = _get_fb_info()

    context = {
        'features_with_task_count': features_with_task_count,
        'sprint_day': sprint_day,
        'passed_percent': passed_percent,
        'top_tasks': Task.objects.filter(top=True, status='Ongoing'),
    }

    return render(request, 'fotd/index.html', context)

def detail(request, fid):
    feature = Feature.objects.get(id=fid)
    updates = FeatureUpdate.objects.filter(feature__id=fid).order_by('update_date')
    #roles = FeatureRoles.objects.get(feature__id=fid)

    tasks = Task.objects.filter(feature__id=fid).exclude(status='Completed').order_by('due')
    for task in tasks:
        task.statusUpdates = StatusUpdate.objects.filter(task=task).order_by('-update_date')[:3]  # Fetch the latest 3 status updates of each task
        
    # Create a context dictionary with the fetched data
    context = {
        'feature': feature,
        'updates': updates,
        'tasks': tasks, 
        'today': date.today()
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

def task(request, tid):
    task = Task.objects.get(id=tid)
    context = {
        'task': task,
        }
    return render(request, 'fotd/task.html', context)

@csrf_exempt
def ajax_feature_update(request, fid):
    if request.method == 'POST':
        feature = Feature.objects.get(id=fid)
        for key, value in request.POST.items():
            if hasattr(feature, key):
                if key == 'boundary':
                    value = ProgramBoundary.objects.get(id=value)
                setattr(feature, key, value)

        feature.save()
        return JsonResponse({'status': 'success', 'message': 'Feature updated successfully'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'Invalid request'})

@csrf_exempt
def ajax_feature_status(request, fid):
    feature = Feature.objects.get(id=fid)
    logging.debug('featureId: ' + fid);

    if request.method == 'POST':
        update_text = request.POST['update_text']

        date_str = request.POST['date_str']
        update_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        logging.debug(f"date value: {update_date}, type: {type(update_date)}")

        update = FeatureUpdate.objects.create(feature=feature, update_date=update_date, is_key=True, update_text=update_text)
        return HttpResponse(update)
    else:
        return HttpResponse('No POST data')

@csrf_exempt
def ajax_task_add(request, fid):
    if request.POST['title'] == '' or request.POST['owner'] == '':
        return HttpResponse('Title and Owner are required')

    if request.method == 'POST':

        task_data = request.POST.dict()
        if 'csrfmiddlewaretoken' in task_data:
            del task_data['csrfmiddlewaretoken']
        
        task_data['feature'] = Feature.objects.get(id=fid)
        task_data['due'] = datetime.strptime(task_data['due'], "%Y-%m-%d").date()
        
        task = Task.objects.create(**task_data)
        serializer = TaskSerializer(task)
        
        #print(serializer.data)
        return JsonResponse(serializer.data)
    else:
        return HttpResponse('No POST data')

@csrf_exempt
def ajax_task_update(request, tid):
    if request.method == 'POST':
        done = False
        task = Task.objects.get(pk=tid)
        for key, value in request.POST.items():
            if hasattr(task, key):
                if (key == "status" and value == "Completed"):
                    done = True
                elif (key == "top"):
                    value = (value == "on")
                else:
                    pass

                setattr(task, key, value)

        task.save()

        if done:
            FeatureUpdate.objects.create(feature=task.feature, update_date=date.today(), is_key=False, update_text='Task done: ' + task.title)

        return JsonResponse({'status': 'success', 'message': 'Task updated successfully'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'Invalid request'})

@csrf_exempt
def ajax_task_delete(request, tid):
    task = Task.objects.get(pk=tid)
    task.delete()
    return JsonResponse({'status': 'success', 'message': 'Task deleted successfully'})

@csrf_exempt
def ajax_task_status(request, tid):
    task = Task.objects.get(id=tid)
    logging.debug('taskId: ' + tid);

    if request.method == 'POST':
        update_text = request.POST['update_text']

        date_str = request.POST['date_str']
        update_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        logging.debug(f"date value: {update_date}, type: {type(update_date)}")

        update = StatusUpdate.objects.create(task=task, update_date=update_date, update_text=update_text)
        return HttpResponse(update)
    else:
        return HttpResponse('No POST data')

def login(request):
    return render(request, 'fotd/login.html')

# yy: year in 2 digits, e.g. 22 for 2022
def fb(request, yy):
    sprints = Sprint.objects.filter(fb__startswith='FB'+yy).order_by('fb')
    context = {
        'sprints': sprints,
        'today': date.today().strftime('%Y-%m-%d')
        }
    return render(request, 'fotd/fb.html', context)

def _get_fb_info():
    today = date.today()
    start_fb = f'FB{str(today.year)[-2:]}{today.month*2-1:02d}'
    sprints = Sprint.objects.filter(fb__gte=start_fb).order_by('fb')[:3]

    for sprint in sprints:
        if (today >= sprint.start_date and today <= sprint.end_date):
            sprint_day = (today - sprint.start_date).days + 1
            print(f'{today} is in {sprint.fb}, day {sprint_day}')
            passed_percent = int(sprint_day * 100 / 14)

            # if (today >= sprint.start_date + timedelta(days=7)):
            #     return (sprint.fb + '.2', sprint_day, passed_percent)
            # else:
            #     return (sprint.fb + '.1', sprint_day, passed_percent)
            return (sprint.fb, sprint_day, passed_percent)
    
    print(f"ERROR: Strange that current sprint not found from {[sprint.fb for sprint in sprints]}")
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
            if start%100 == 26: # 26 fbs in each year
                start = (int(start/100) + 1) * 100 + 1
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

# rules:
# Activity type - Entity Specification: sw_done
# Activity type - SW: sw_done
# Activity type - CuDo: cudo
# Activity type - System Testing, except CA is PET/FIVE: st_done
# CA is VAL_PET/VAL_FIVE: pet_five_done
# return: {key, boundary_fb}
def check_plan_fitting(result, boundary):
    not_fitting_items = {}
    for item in result:
        not_fitting = False

        if item['Activity_Type'] in ('SW', 'Entity Specification') and item['End_FB'] > boundary.sw_done:
            not_fitting_items[item['Key']] = boundary.sw_done
            not_fitting = True
        elif item['Activity_Type'] == 'CuDo' and item['End_FB'] > boundary.cudo:
            not_fitting_items[item['Key']] = boundary.cudo
            not_fitting = True
        elif item['Activity_Type'] == 'System Testing':
            if item['Competence_Area'] in ('VAL_PET', 'VAL_FIVE'):
                if item['End_FB'] > boundary.pet_five_done:
                    not_fitting_items[item['Key']] = boundary.pet_five_done
                    not_fitting = True
            else:
                if item['End_FB'] > boundary.st_done:
                    not_fitting_items[item['Key']] = boundary.st_done
                    not_fitting = True

        if not_fitting:
            _add_tag(item, 'not_fitting')
            _add_hint(item, "Not fitting to Program boundary: " + str(not_fitting_items[item['Key']]))

    print(f"not_fitting_items: {not_fitting_items}")
    return not_fitting_items

def check_exec_issue(result, current_fb):
    for item in result:
        if not item['End_FB']:
            continue

        if item['End_FB'] == current_fb:
            if item['RC_Status'] == 'Not Committed':
                _add_tag(item, "not_committed")
                _add_hint(item, "Not_committed, stretch goal reason: " + (item['Stretch_Goal_Reason'] if 'Stretch_Goal_Reason' in item else "Not set"))
            else:
                _add_tag(item, "duesoon")
                _add_hint(item, "Due at current FB")

        elif item['End_FB'] < current_fb:
            _add_tag(item, "overdue")
            _add_hint(item, f"Item not done at {item['End_FB']} and End FB not updated!")
        else:
            pass

        if item['RC_FB'] and item['End_FB'] > item['RC_FB']:
            _add_tag(item, "delayed")
            _add_hint(item, "Delayed! Committed to deliver at " + item['RC_FB'])

        # if item['Start_FB'] and item['Start_FB'] < current_fb and item['Progress'] <= 0:
        #     _add_tag(item, "should_start")
        #     _add_hint(item, "Should have started but no progress")

    return

def backlog(request, fid):
    first_query = False
    query = BacklogQuery.objects.filter(feature__id=fid).first()
    if query is None:
        first_query = True
        #print(f"{fid}: first query")
    else:
        result = query.query_result
        start_earliest = query.start_earliest
        end_latest = query.end_latest
        display_fields = query.display_fields
        rfc_ratio = query.rfc_ratio
        committed_ratio = query.committed_ratio
        subfeatures = query.subfeatures.split(';')
        total_spent = query.total_spent
        total_remaining = query.total_remaining
        #print(f"{fid}: last query at {query.query_time}: {len(result)} items")
    
    jira_query = False
    new_added_keys = []
    endfb_changed_items = {}
    if request.GET.get('refresh') or first_query:
        jira_query = True
        print(f"{fid}: query from JIRA")
        (result, subfeatures, display_fields, start_earliest, end_latest, rfc_ratio, committed_ratio, total_spent, total_remaining) = queryJiraCaItems(fid)

        changes = ''
        if not first_query:
            if len(query.query_result) != len(result):
                # find out new added items
                new_added_keys = [item['Key'] for item in result if not any(item['Key'] == old_item['Key'] for old_item in query.query_result)]
                if new_added_keys:
                    print(f"New added keys: {new_added_keys}")
                    changes += f"New added: {new_added_keys}; "

            # find out End_FB changed items
            endfb_changed_items = {item['Key']: {'previous': old_item['End_FB'], 'current': item['End_FB']}
                                   for old_item in query.query_result 
                                   for item in result 
                                   if item['Key'] == old_item['Key'] and item['End_FB'] != old_item['End_FB']}
            if endfb_changed_items:
                endfb_changed_str = ";".join([
                    f"{key}: {value['previous']}->{value['current']}" 
                    for key, value in endfb_changed_items.items()
                ])
                print(f"End_FB changes: {endfb_changed_str}")
                changes += f"EndFB changes: {endfb_changed_str}"

        mandatory_fields = {
            'feature_id': fid,
            'query_result': result,
            'display_fields': display_fields,
            'subfeatures': ";".join(subfeatures),
            'total_spent': total_spent,
            'total_remaining': total_remaining,
        }
        
        optional_fields = {
            'start_earliest': start_earliest,
            'end_latest': end_latest,
            'rfc_ratio': rfc_ratio,
            'committed_ratio': committed_ratio,
            'changes': changes,
        }
        
        # Remove optional fields with value None or empty string
        optional_fields = {k: v for k, v in optional_fields.items() if v is not None and v != ''}
        
        # Create the db object
        try:
            db_object = BacklogQuery.objects.create(**mandatory_fields, **optional_fields)
        except Exception as e:
            print(f"Failed to create BacklogQuery record: {e}")

    current_fb = request.session['fb'][2:]
    if not (start_earliest and end_latest):   # no plan at all, for a new feature
        print(f"{fid}: start/endfb is empty, no plan at all")
        display_sprints = [current_fb]
    elif start_earliest < current_fb:
        display_sprints = _get_fbs(current_fb, end_latest)
    else:
        display_sprints = _get_fbs(start_earliest, end_latest)

    context = {
        'fid': fid,
        'subfeatures': subfeatures,
        'display_fields': display_fields,
        'display_sprints': display_sprints,
        #'rfc_ratio': rfc_ratio,
        #'committed_ratio': committed_ratio,
        'new_added_keys': new_added_keys,
        'endfb_changed_items': endfb_changed_items,
        'current_fb': current_fb,
        'link_prefix': 'https://jiradc.ext.net.nokia.com/browse/',
        }

    if not jira_query:
        context['query_time'] = query.query_time

    check_exec_issue(result, current_fb)

    try:
        boundary = Feature.objects.get(id=fid).boundary
        if boundary:
            context['boundary'] = boundary
            not_fitting_items = check_plan_fitting(result, boundary)
            if not_fitting_items:
                context['not_fitting_items'] = not_fitting_items
    except Exception as e:
        print(f"An error occurred: {e}")

    context.update({
        'result': result,
    })

    return render(request, 'fotd/backlog.html', context)

def fot(request, fid):
    try:
        feature_roles = FeatureRoles.objects.get(feature__id=fid)
    except ObjectDoesNotExist:
        feature_roles = None

    context = {
        'fid': fid,
        'role': feature_roles,
        'team_members': TeamMember.objects.filter(feature__id=fid)
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
        #'role': get_object_or_404(FeatureRoles, feature__id=fid),
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
                'comment': request.POST.get('comment')
            }
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
                team = team_member['team'],
                apo = team_member['apo'],
                role = team_member['role'],
                name = team_member['name'],
                comment = team_member['comment'],
                feature = feature
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
        fields = ['release', 'category', 'sw_done', 'et_ec', 'et_fer', 'et_done', 'st_ec', 'st_fer', 'st_done', 'pet_five_ec', 'pet_five_fer', 'pet_five_done', 'ta', 'cudo']
        data = {field: request.POST.get(field).strip() for field in fields}
        program_boundary = ProgramBoundary(**data)
        
        try:
            program_boundary.save()
            return JsonResponse({'status': 'success'})
        except IntegrityError as e:
            return JsonResponse({'status': 'error', 'message': 'A unique constraint violation occurred, do not import the same feature boundary repeatedly.'}, status=400)
        except Exception as e:
            print(f"Failed to save into database: {e}")
            return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'}, status=500)

    return JsonResponse({'status': 'error'})


REQ_TYPE_PLANNING = "Planning"
REQ_TYPE_RFC = "RfC"

@csrf_exempt
def ajax_send_email(request, email_type):
    context = json.loads(request.body)
    context.update({
        'fot_lead': request.user.username,
    })
    #print(f"email_type: {email_type}, context: {context}")

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