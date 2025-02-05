import logging
from datetime import date, datetime

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers

from .models import Feature, FeatureUpdate, StatusUpdate, Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


def edit_task(request, tid):
    task = Task.objects.get(id=tid)
    context = {
        'task': task,
    }
    return render(request, 'task/task_edit.html', context)


def view_task(request, tid):
    task = get_object_or_404(Task, pk=tid)
    task.statusUpdates = StatusUpdate.objects.filter(task=task).order_by('-update_date')
    return render(request, 'task/task_view.html', {'task': task})


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

        # print(serializer.data)
        return JsonResponse(serializer.data)
    else:
        return HttpResponse('No POST data')


@csrf_exempt
def ajax_task_update(request, tid):
    if request.method == 'POST':
        done = False
        task = Task.objects.get(pk=tid)
        task.top = False
        for key, value in request.POST.items():
            if hasattr(task, key):
                if key == "status":
                    done = value == "closed"
                elif key == "top":
                    value = value == "on"
                else:
                    pass

                setattr(task, key, value)
                # print(f'Task update: {key}: {value}')

        task.save()

        if done:
            FeatureUpdate.objects.create(
                feature=task.feature,
                update_date=date.today(),
                is_key=False,
                update_text=(
                    f'Task done: <a href="/task/view/{task.id}">' f'{task.title}</a>'
                ),
            )

        return JsonResponse(
            {'status': 'success', 'message': 'Task updated successfully'}
        )

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
    logging.debug('taskId: ' + tid)

    if request.method == 'POST':
        update_text = request.POST['update_text']

        date_str = request.POST['date_str']
        update_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        logging.debug(f"date value: {update_date}, type: {type(update_date)}")

        update = StatusUpdate.objects.create(
            task=task, update_date=update_date, update_text=update_text
        )
        return HttpResponse(update)
    else:
        return HttpResponse('No POST data')
