# walkoff_client.WorkflowQueueApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**clear_workflow_status**](WorkflowQueueApi.md#clear_workflow_status) | **DELETE** /workflowqueue/cleardb | Removes workflow statuses from the execution database. It will delete all of them or ones older than a certain number of days
[**control_workflow**](WorkflowQueueApi.md#control_workflow) | **PATCH** /workflowqueue/{execution} | Abort or trigger a workflow
[**execute_workflow**](WorkflowQueueApi.md#execute_workflow) | **POST** /workflowqueue | Execute a workflow
[**get_all_workflow_status**](WorkflowQueueApi.md#get_all_workflow_status) | **GET** /workflowqueue | Get status information on the workflows currently executing
[**get_workflow_status**](WorkflowQueueApi.md#get_workflow_status) | **GET** /workflowqueue/{execution} | Get status information on a currently executing workflow


# **clear_workflow_status**
> clear_workflow_status(all_=all_, days=days)

Removes workflow statuses from the execution database. It will delete all of them or ones older than a certain number of days

### Example

* Bearer (JWT) Authentication (AuthenticationToken):
```python
from __future__ import print_function
import time
import walkoff_client
from walkoff_client.rest import ApiException
from pprint import pprint
configuration = walkoff_client.Configuration()
# Configure Bearer authorization (JWT): AuthenticationToken
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/walkoff/api
configuration.host = "http://localhost/walkoff/api"
# Create an instance of the API class
api_instance = walkoff_client.WorkflowQueueApi(walkoff_client.ApiClient(configuration))
all_ = True # bool | Whether or not to delete all workflow statuses, defaults to false (optional)
days = 56 # int | The number of days of workflow statuses to keep (optional)

try:
    # Removes workflow statuses from the execution database. It will delete all of them or ones older than a certain number of days
    api_instance.clear_workflow_status(all_=all_, days=days)
except ApiException as e:
    print("Exception when calling WorkflowQueueApi->clear_workflow_status: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **all_** | **bool**| Whether or not to delete all workflow statuses, defaults to false | [optional] 
 **days** | **int**| The number of days of workflow statuses to keep | [optional] 

### Return type

void (empty response body)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Success |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **control_workflow**
> control_workflow(execution, control_workflow)

Abort or trigger a workflow

### Example

* Bearer (JWT) Authentication (AuthenticationToken):
```python
from __future__ import print_function
import time
import walkoff_client
from walkoff_client.rest import ApiException
from pprint import pprint
configuration = walkoff_client.Configuration()
# Configure Bearer authorization (JWT): AuthenticationToken
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/walkoff/api
configuration.host = "http://localhost/walkoff/api"
# Create an instance of the API class
api_instance = walkoff_client.WorkflowQueueApi(walkoff_client.ApiClient(configuration))
execution = 'execution_example' # str | The ID of the execution to get.
control_workflow = walkoff_client.ControlWorkflow() # ControlWorkflow | 

try:
    # Abort or trigger a workflow
    api_instance.control_workflow(execution, control_workflow)
except ApiException as e:
    print("Exception when calling WorkflowQueueApi->control_workflow: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **execution** | [**str**](.md)| The ID of the execution to get. | 
 **control_workflow** | [**ControlWorkflow**](ControlWorkflow.md)|  | 

### Return type

void (empty response body)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Success. |  -  |
**400** | Invalid input error. |  -  |
**404** | Workflow does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **execute_workflow**
> str execute_workflow(execute_workflow)

Execute a workflow

### Example

* Bearer (JWT) Authentication (AuthenticationToken):
```python
from __future__ import print_function
import time
import walkoff_client
from walkoff_client.rest import ApiException
from pprint import pprint
configuration = walkoff_client.Configuration()
# Configure Bearer authorization (JWT): AuthenticationToken
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/walkoff/api
configuration.host = "http://localhost/walkoff/api"
# Create an instance of the API class
api_instance = walkoff_client.WorkflowQueueApi(walkoff_client.ApiClient(configuration))
execute_workflow = walkoff_client.ExecuteWorkflow() # ExecuteWorkflow | 

try:
    # Execute a workflow
    api_response = api_instance.execute_workflow(execute_workflow)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling WorkflowQueueApi->execute_workflow: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **execute_workflow** | [**ExecuteWorkflow**](ExecuteWorkflow.md)|  | 

### Return type

**str**

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Success asynchronous. |  -  |
**400** | Invalid input error. |  -  |
**404** | Workflow does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_all_workflow_status**
> list[WorkflowStatusSummary] get_all_workflow_status(page=page)

Get status information on the workflows currently executing

### Example

* Bearer (JWT) Authentication (AuthenticationToken):
```python
from __future__ import print_function
import time
import walkoff_client
from walkoff_client.rest import ApiException
from pprint import pprint
configuration = walkoff_client.Configuration()
# Configure Bearer authorization (JWT): AuthenticationToken
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/walkoff/api
configuration.host = "http://localhost/walkoff/api"
# Create an instance of the API class
api_instance = walkoff_client.WorkflowQueueApi(walkoff_client.ApiClient(configuration))
page = 56 # int | page of data to get (optional)

try:
    # Get status information on the workflows currently executing
    api_response = api_instance.get_all_workflow_status(page=page)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling WorkflowQueueApi->get_all_workflow_status: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| page of data to get | [optional] 

### Return type

[**list[WorkflowStatusSummary]**](WorkflowStatusSummary.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_workflow_status**
> WorkflowStatus get_workflow_status(execution)

Get status information on a currently executing workflow

### Example

* Bearer (JWT) Authentication (AuthenticationToken):
```python
from __future__ import print_function
import time
import walkoff_client
from walkoff_client.rest import ApiException
from pprint import pprint
configuration = walkoff_client.Configuration()
# Configure Bearer authorization (JWT): AuthenticationToken
configuration.access_token = 'YOUR_BEARER_TOKEN'

# Defining host is optional and default to http://localhost/walkoff/api
configuration.host = "http://localhost/walkoff/api"
# Create an instance of the API class
api_instance = walkoff_client.WorkflowQueueApi(walkoff_client.ApiClient(configuration))
execution = 'execution_example' # str | The ID of the execution to get.

try:
    # Get status information on a currently executing workflow
    api_response = api_instance.get_workflow_status(execution)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling WorkflowQueueApi->get_workflow_status: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **execution** | [**str**](.md)| The ID of the execution to get. | 

### Return type

[**WorkflowStatus**](WorkflowStatus.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | Object does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

