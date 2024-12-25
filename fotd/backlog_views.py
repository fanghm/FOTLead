import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import BacklogQuery
from .myjira import get_item_links


def _fetch_item_links(id, include_done=False):
    """
    Fetch the links of a CA item from JIRA
    """
    url = 'https://jiradc.ext.net.nokia.com/rest/api/2/issue/{}'.format(id)
    return get_item_links(url, include_done=include_done)


@csrf_exempt
def ajax_get_item_links(request, id):
    """
    Get the links of a CA item from JIRA
    """
    links = _fetch_item_links(id)
    return JsonResponse(links, safe=False)


@csrf_exempt
def ajax_get_all_links(request, id):
    """
    Get all the links of a CA item from JIRA, including the closed ones
    """
    links = _fetch_item_links(id, include_done=True)
    return JsonResponse(links, safe=False)


@csrf_exempt
def ajax_update_item_links(request, fid):
    print(f'Saving link data for feature {fid}')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            data.pop('dirty', None)  # remove dirty flag

            backlog_query, created = BacklogQuery.objects.update_or_create(
                feature_id=fid, defaults={'item_links': data}
            )

            return JsonResponse({'status': 'success', 'created': created})
        except json.JSONDecodeError:
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid JSON'}, status=400
            )
        except ObjectDoesNotExist:
            return JsonResponse(
                {'status': 'error', 'message': 'Object does not exist'}, status=404
            )
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse(
        {'status': 'error', 'message': 'Invalid request method'}, status=405
    )
