import traceback

from django.contrib import messages
from django.shortcuts import render

from .globals import _get_fbs
from .myjira import jira_get_apo_backlog


def apod(request):
    print(f"apod: {request.session['fb']}")
    try:
        current_fb = request.session['fb'][2:]
        query_result = jira_get_apo_backlog(current_fb)
        result = query_result.backlog_items
        start_earliest = query_result.start_earliest
        end_latest = query_result.end_latest
        display_fields = query_result.display_fields

        if not (start_earliest and end_latest):  # no plan at all, for a new feature
            print("Fatal: no backlog/plan at all")
            display_sprints = [current_fb]
        elif start_earliest < current_fb:
            display_sprints = _get_fbs(current_fb, end_latest)
        else:
            display_sprints = _get_fbs(start_earliest, end_latest)

        context = {
            'display_fields': display_fields,
            'display_sprints': display_sprints,
            'new_keys': [],  # new_keys,
            'changed_items': [],  # changed_items,
            'current_fb': current_fb,
            'link_prefix': 'https://jiradc.ext.net.nokia.com/browse/',
            'backlog_items': result,
        }
        return render(request, 'apod/apod.html', context)

    except Exception as e:
        print(f"Exception in JIRA query: {traceback.format_exc()}")
        error_message = f"Failed to connect to JIRA: {e}"
        messages.error(request, error_message)
        return render(request, 'fotd/error.html')
