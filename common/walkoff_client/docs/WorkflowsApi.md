# walkoff_client.WorkflowsApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_workflow**](WorkflowsApi.md#create_workflow) | **POST** /workflows | Create a workflow
[**delete_workflow**](WorkflowsApi.md#delete_workflow) | **DELETE** /workflows/{workflow} | Delete a workflow
[**read_all_workflows**](WorkflowsApi.md#read_all_workflows) | **GET** /workflows | Read all workflows in playbook
[**read_workflow**](WorkflowsApi.md#read_workflow) | **GET** /workflows/{workflow} | Read a workflow
[**update_workflow**](WorkflowsApi.md#update_workflow) | **PUT** /workflows/{workflow} | Update a workflow


# **create_workflow**
> WorkflowJSON create_workflow(workflow_json, source=source)

Create a workflow

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
api_instance = walkoff_client.WorkflowsApi(walkoff_client.ApiClient(configuration))
workflow_json = walkoff_client.WorkflowJSON() # WorkflowJSON | The workflow object to be created
source = 'source_example' # str | The ID of the workflow to clone (optional)

try:
    # Create a workflow
    api_response = api_instance.create_workflow(workflow_json, source=source)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling WorkflowsApi->create_workflow: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workflow_json** | [**WorkflowJSON**](WorkflowJSON.md)| The workflow object to be created | 
 **source** | [**str**](.md)| The ID of the workflow to clone | [optional] 

### Return type

[**WorkflowJSON**](WorkflowJSON.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Workflow created. |  -  |
**400** | Workflow already exists. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_workflow**
> delete_workflow(workflow)

Delete a workflow

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
api_instance = walkoff_client.WorkflowsApi(walkoff_client.ApiClient(configuration))
workflow = 'workflow_example' # str | The name or ID of the workflow to get.

try:
    # Delete a workflow
    api_instance.delete_workflow(workflow)
except ApiException as e:
    print("Exception when calling WorkflowsApi->delete_workflow: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workflow** | **str**| The name or ID of the workflow to get. | 

### Return type

void (empty response body)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**204** | Success |  -  |
**404** | Workflow does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_all_workflows**
> list[WorkflowMetaData] read_all_workflows(page=page)

Read all workflows in playbook

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
api_instance = walkoff_client.WorkflowsApi(walkoff_client.ApiClient(configuration))
page = 56 # int | page of data to get (optional)

try:
    # Read all workflows in playbook
    api_response = api_instance.read_all_workflows(page=page)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling WorkflowsApi->read_all_workflows: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| page of data to get | [optional] 

### Return type

[**list[WorkflowMetaData]**](WorkflowMetaData.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | No workflows exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_workflow**
> WorkflowJSON read_workflow(workflow, mode=mode)

Read a workflow

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
api_instance = walkoff_client.WorkflowsApi(walkoff_client.ApiClient(configuration))
workflow = 'workflow_example' # str | The name or ID of the workflow to get.
mode = 'mode_example' # str | Set to export to send as file. (optional)

try:
    # Read a workflow
    api_response = api_instance.read_workflow(workflow, mode=mode)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling WorkflowsApi->read_workflow: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workflow** | **str**| The name or ID of the workflow to get. | 
 **mode** | **str**| Set to export to send as file. | [optional] 

### Return type

[**WorkflowJSON**](WorkflowJSON.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | Workflow does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_workflow**
> InlineResponse2002 update_workflow(workflow, workflow_json)

Update a workflow

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
api_instance = walkoff_client.WorkflowsApi(walkoff_client.ApiClient(configuration))
workflow = 'workflow_example' # str | The name or ID of the workflow to get.
workflow_json = walkoff_client.WorkflowJSON() # WorkflowJSON | The fields of the workflow object to be updated

try:
    # Update a workflow
    api_response = api_instance.update_workflow(workflow, workflow_json)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling WorkflowsApi->update_workflow: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **workflow** | **str**| The name or ID of the workflow to get. | 
 **workflow_json** | [**WorkflowJSON**](WorkflowJSON.md)| The fields of the workflow object to be updated | 

### Return type

[**InlineResponse2002**](InlineResponse2002.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**400** | Workflow already exists. |  -  |
**404** | Workflow does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

