# walkoff_client.SchedulerApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_scheduled_task**](SchedulerApi.md#create_scheduled_task) | **POST** /scheduledtasks | Create a new Scheduled Task
[**delete_scheduled_task**](SchedulerApi.md#delete_scheduled_task) | **DELETE** /scheduledtasks/{scheduled_task_id} | Delete the scheduled task
[**get_scheduler_status**](SchedulerApi.md#get_scheduler_status) | **GET** /scheduler | Get the current scheduler status.
[**read_all_scheduled_tasks**](SchedulerApi.md#read_all_scheduled_tasks) | **GET** /scheduledtasks | Get all the scheduled tasks
[**read_scheduled_task**](SchedulerApi.md#read_scheduled_task) | **GET** /scheduledtasks/{scheduled_task_id} | Get the scheduled task
[**update_scheduled_task**](SchedulerApi.md#update_scheduled_task) | **PUT** /scheduledtasks/{scheduled_task_id} | Update a new Scheduled Task
[**update_scheduler_status**](SchedulerApi.md#update_scheduler_status) | **PUT** /scheduler | Update the status of the scheduler


# **create_scheduled_task**
> list[ScheduledTask] create_scheduled_task(add_scheduled_task)

Create a new Scheduled Task

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
api_instance = walkoff_client.SchedulerApi(walkoff_client.ApiClient(configuration))
add_scheduled_task = walkoff_client.AddScheduledTask() # AddScheduledTask | The new Scheduled Task object

try:
    # Create a new Scheduled Task
    api_response = api_instance.create_scheduled_task(add_scheduled_task)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SchedulerApi->create_scheduled_task: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **add_scheduled_task** | [**AddScheduledTask**](AddScheduledTask.md)| The new Scheduled Task object | 

### Return type

[**list[ScheduledTask]**](ScheduledTask.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Success |  -  |
**400** | Scheduled task already exists |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_scheduled_task**
> delete_scheduled_task(scheduled_task_id)

Delete the scheduled task

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
api_instance = walkoff_client.SchedulerApi(walkoff_client.ApiClient(configuration))
scheduled_task_id = 'scheduled_task_id_example' # str | The ID of the scheduled task.

try:
    # Delete the scheduled task
    api_instance.delete_scheduled_task(scheduled_task_id)
except ApiException as e:
    print("Exception when calling SchedulerApi->delete_scheduled_task: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **scheduled_task_id** | **str**| The ID of the scheduled task. | 

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
**404** | Scheduled task does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_scheduler_status**
> Scheduler get_scheduler_status()

Get the current scheduler status.

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
api_instance = walkoff_client.SchedulerApi(walkoff_client.ApiClient(configuration))

try:
    # Get the current scheduler status.
    api_response = api_instance.get_scheduler_status()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SchedulerApi->get_scheduler_status: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**Scheduler**](Scheduler.md)

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

# **read_all_scheduled_tasks**
> list[ScheduledTask] read_all_scheduled_tasks()

Get all the scheduled tasks

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
api_instance = walkoff_client.SchedulerApi(walkoff_client.ApiClient(configuration))

try:
    # Get all the scheduled tasks
    api_response = api_instance.read_all_scheduled_tasks()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SchedulerApi->read_all_scheduled_tasks: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**list[ScheduledTask]**](ScheduledTask.md)

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

# **read_scheduled_task**
> ScheduledTask read_scheduled_task(scheduled_task_id)

Get the scheduled task

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
api_instance = walkoff_client.SchedulerApi(walkoff_client.ApiClient(configuration))
scheduled_task_id = 'scheduled_task_id_example' # str | The ID of the scheduled task.

try:
    # Get the scheduled task
    api_response = api_instance.read_scheduled_task(scheduled_task_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SchedulerApi->read_scheduled_task: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **scheduled_task_id** | **str**| The ID of the scheduled task. | 

### Return type

[**ScheduledTask**](ScheduledTask.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | Scheduled task does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_scheduled_task**
> ScheduledTask update_scheduled_task(scheduled_task_id, scheduled_task)

Update a new Scheduled Task

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
api_instance = walkoff_client.SchedulerApi(walkoff_client.ApiClient(configuration))
scheduled_task_id = 'scheduled_task_id_example' # str | The ID of the scheduled task.
scheduled_task = walkoff_client.ScheduledTask() # ScheduledTask | The updated Scheduled Task object

try:
    # Update a new Scheduled Task
    api_response = api_instance.update_scheduled_task(scheduled_task_id, scheduled_task)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SchedulerApi->update_scheduled_task: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **scheduled_task_id** | **str**| The ID of the scheduled task. | 
 **scheduled_task** | [**ScheduledTask**](ScheduledTask.md)| The updated Scheduled Task object | 

### Return type

[**ScheduledTask**](ScheduledTask.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**400** | Scheduled task name already exists |  -  |
**404** | Scheduled task does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_scheduler_status**
> InlineResponse2001 update_scheduler_status(inline_object1)

Update the status of the scheduler

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
api_instance = walkoff_client.SchedulerApi(walkoff_client.ApiClient(configuration))
inline_object1 = walkoff_client.InlineObject1() # InlineObject1 | 

try:
    # Update the status of the scheduler
    api_response = api_instance.update_scheduler_status(inline_object1)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SchedulerApi->update_scheduler_status: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **inline_object1** | [**InlineObject1**](InlineObject1.md)|  | 

### Return type

[**InlineResponse2001**](InlineResponse2001.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

