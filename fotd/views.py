from django.shortcuts import render
from django.shortcuts import render
from .models import Feature, FeatureRoles, TeamMember, Task, StatusUpdate, Link
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
    tasks = Task.objects.filter(feature__id=fid)  # Fetch all records from the Feature table
    for task in tasks:
        task.statusUpdates = StatusUpdate.objects.filter(task=task).order_by('-id')[:3]  # Fetch the latest 3 StatusUpdate records linked to this task
        
    #logging.debug(tasks)  # Add logging to dump the content of tasks
    # Create a context dictionary with the fetched data
    context = {
        'tasks': tasks, 
        'today': date.today()
        }
    return render(request, 'fotd/task.html', context)

@csrf_exempt
def ajax_statusupdate(request, tid):
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