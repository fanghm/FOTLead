from django.shortcuts import render
from django.shortcuts import render
from .models import Feature, FeatureUpdate, FeatureRoles, TeamMember, Task, StatusUpdate, Link, Sprint
from datetime import date, datetime, timedelta
import logging
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers

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
    request.session['fb'], sprint_day, passed_percent = _get_fb()

    context = {
        'features_with_task_count': features_with_task_count,
        'sprint_day': sprint_day,
        'passed_percent': passed_percent,
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

def task(request, tid):
    task = Task.objects.get(id=tid)
    context = {
        'task': task,
        }
    return render(request, 'fotd/task.html', context)

@csrf_exempt
def ajax_feature_update(request, fid):
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
                setattr(task, key, value)
                if (key == "status" and value == "Completed"):
                    done = True
                    print(f"Task {task.title} is done")

        task.save()

        if done:
            FeatureUpdate.objects.create(feature=task.feature, update_date=date.today(), is_key=False, update_text='Task done: ' + task.title)

        return JsonResponse({'status': 'success', 'message': 'Task updated successfully'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'Invalid request'})

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

def fb(request):
    sprints = Sprint.objects.all()
    context = {
        'sprints': sprints,
        'today': date.today().strftime('%Y-%m-%d')
        }
    return render(request, 'fotd/fb.html', context)

def _get_fb():
    today = date.today()
    start_fb = f'FB{str(today.year)[-2:]}{today.month*2:02d}'
    sprints = Sprint.objects.filter(fb__gte=start_fb).order_by('fb')[:3]
    #print(sprints)
    #print(start_fb)

    for sprint in sprints:
        if (today >= sprint.start_date and today <= sprint.end_date):
            sprint_day = (today - sprint.start_date).days + 1
            print(f'{today} is in {sprint.fb}, day {sprint_day}')
            passed_percent = int(sprint_day * 100 / 14)

            if (today >= sprint.start_date + timedelta(days=7)):
                return (sprint.fb + '.2', sprint_day, passed_percent)
            else:
                return (sprint.fb + '.1', sprint_day, passed_percent)

    return ('N/A', 0)