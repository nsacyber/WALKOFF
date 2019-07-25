# walkoff_client.TempInternalApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**update_workflow_status**](TempInternalApi.md#update_workflow_status) | **PATCH** /internal/workflowstatus/{execution_id} | Patch parts of a WorkflowStatusMessage object


# **update_workflow_status**
> WorkflowStatus update_workflow_status(execution_id, event, json_patch)

Patch parts of a WorkflowStatusMessage object

For internal use only. This endpoint should only be available to the docker network.

### Example

```python
from __future__ import print_function
import time
import walkoff_client
from walkoff_client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = walkoff_client.TempInternalApi()
execution_id = 'execution_id_example' # str | execution_id of workflow status to update
event = 'event_example' # str | The event type that is being submitted
json_patch = walkoff_client.JSONPatch() # JSONPatch | 

try:
    # Patch parts of a WorkflowStatusMessage object
    api_response = api_instance.update_workflow_status(execution_id, event, json_patch)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling TempInternalApi->update_workflow_status: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **execution_id** | **str**| execution_id of workflow status to update | 
 **event** | **str**| The event type that is being submitted | 
 **json_patch** | [**JSONPatch**](JSONPatch.md)|  | 

### Return type

[**WorkflowStatus**](WorkflowStatus.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Updated WorkflowStatusMessage entry |  -  |
**400** | Invalid input error. |  -  |
**404** | WorkflowStatusMessage does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

