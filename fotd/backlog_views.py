from django.http import JsonResponse
from .myjira import get_item_links
from .models import BacklogQuery

def ajax_get_item_links(request, id):
    """
    Get the links of a CA item from JIRA
    """

    url = 'https://jiradc.ext.net.nokia.com/rest/api/2/issue/{}'.format(id)
    links = get_item_links(url)
    return JsonResponse(links, safe=False)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from .models import BacklogQuery
import json

@csrf_exempt
def ajax_update_item_links(request, fid):
    print(f'ajax_update_item_links: {fid}')

    if request.method == 'POST':
        try:
            # 解析 JSON 数据
            data = json.loads(request.body)
            data.pop('dirty', None)  # remove dirty flag

            backlog_query, created = BacklogQuery.objects.update_or_create(
                feature_id=fid,
                defaults={'item_links': data}
            )

            return JsonResponse({'status': 'success', 'created': created})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except ObjectDoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Object does not exist'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)