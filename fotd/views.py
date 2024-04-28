from django.shortcuts import render
from django.shortcuts import render
from .models import Feature, FeatureUpdate, FeatureRoles, TeamMember, Task, StatusUpdate, Link
from datetime import date, datetime
import logging
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

#@login_required
def index(request):
    features = Feature.objects.all()  # Fetch all data from the Feature table
    context = {'features': features}  # Create a context dictionary with the fetched data
    return render(request, 'fotd/index.html', context)

def detail(request, fid):
    feature = Feature.objects.get(id=fid)
    updates = FeatureUpdate.objects.filter(feature__id=fid, is_key=True)
    #roles = FeatureRoles.objects.get(feature__id=fid)

    tasks = Task.objects.filter(feature__id=fid)
    for task in tasks:
        task.statusUpdates = StatusUpdate.objects.filter(task=task).order_by('-id')[:3]  # Fetch the latest 3 status updates of each task
        
    # Create a context dictionary with the fetched data
    context = {
        'feature': feature,
        'updates': updates,
        'tasks': tasks, 
        'today': date.today()
        }
    return render(request, 'fotd/detail.html', context)

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
    feature = Feature.objects.get(id=fid)

    if request.method == 'POST':
        title = request.POST['title']
        owner = request.POST.get('owner', 'FOTL')
        mail = request.POST['mail']
        chat = request.POST['chat']
        meeting = request.POST['meeting']

        date_str = request.POST['date_str']
        due = datetime.strptime(date_str, "%Y-%m-%d").date()

        update = Task.objects.create(feature=feature, title=title, owner=owner, mail=mail, chat=chat, meeting=meeting, due=due)
        return HttpResponse(update)
    else:
        return HttpResponse('No POST data')

@csrf_exempt
def ajax_task_update(request, tid):
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