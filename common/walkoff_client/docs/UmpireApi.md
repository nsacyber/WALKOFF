# walkoff_client.UmpireApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**build_image**](UmpireApi.md#build_image) | **POST** /umpire/build/{app_name}/{app_version} | Builds image in Minio
[**build_status_from_id**](UmpireApi.md#build_status_from_id) | **POST** /umpire/build/{build_id} | Gets build status given a specific ID
[**get_build_status**](UmpireApi.md#get_build_status) | **GET** /umpire/build | Gets build status of all current build
[**get_file_contents**](UmpireApi.md#get_file_contents) | **GET** /umpire/file/{app_name}/{app_version} | Get contents of specified file.
[**list_all_files**](UmpireApi.md#list_all_files) | **GET** /umpire/files/{app_name}/{app_version} | List all files
[**save_umpire_file**](UmpireApi.md#save_umpire_file) | **POST** /umpire/save/{app_name}/{app_version} | Pushes image from minio to /apps and overwrites it.
[**update_file**](UmpireApi.md#update_file) | **POST** /umpire/file_upload | Updates a file in Minio


# **build_image**
> WorkflowJSON build_image(app_name, app_version)

Builds image in Minio

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
api_instance = walkoff_client.UmpireApi(walkoff_client.ApiClient(configuration))
app_name = 'app_name_example' # str | The name of the app to list.
app_version = 'app_version_example' # str | The version number of the app to list.

try:
    # Builds image in Minio
    api_response = api_instance.build_image(app_name, app_version)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UmpireApi->build_image: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **app_name** | **str**| The name of the app to list. | 
 **app_version** | **str**| The version number of the app to list. | 

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

# **build_status_from_id**
> WorkflowJSON build_status_from_id(build_id)

Gets build status given a specific ID

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
api_instance = walkoff_client.UmpireApi(walkoff_client.ApiClient(configuration))
build_id = 'build_id_example' # str | The name of the app to list.

try:
    # Gets build status given a specific ID
    api_response = api_instance.build_status_from_id(build_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UmpireApi->build_status_from_id: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **build_id** | **str**| The name of the app to list. | 

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

# **get_build_status**
> WorkflowJSON get_build_status()

Gets build status of all current build

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
api_instance = walkoff_client.UmpireApi(walkoff_client.ApiClient(configuration))

try:
    # Gets build status of all current build
    api_response = api_instance.get_build_status()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UmpireApi->get_build_status: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

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

# **get_file_contents**
> WorkflowJSON get_file_contents(app_name, app_version, file_path)

Get contents of specified file.

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
api_instance = walkoff_client.UmpireApi(walkoff_client.ApiClient(configuration))
app_name = 'app_name_example' # str | The name of the app to list.
app_version = 'app_version_example' # str | The version number of the app to list.
file_path = 'file_path_example' # str | Whether or not to delete all workflow statuses, defaults to false

try:
    # Get contents of specified file.
    api_response = api_instance.get_file_contents(app_name, app_version, file_path)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UmpireApi->get_file_contents: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **app_name** | **str**| The name of the app to list. | 
 **app_version** | **str**| The version number of the app to list. | 
 **file_path** | **str**| Whether or not to delete all workflow statuses, defaults to false | 

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

# **list_all_files**
> WorkflowJSON list_all_files(app_name, app_version)

List all files

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
api_instance = walkoff_client.UmpireApi(walkoff_client.ApiClient(configuration))
app_name = 'app_name_example' # str | The name or ID of the app to list.
app_version = 'app_version_example' # str | The name or ID of the app to list.

try:
    # List all files
    api_response = api_instance.list_all_files(app_name, app_version)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UmpireApi->list_all_files: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **app_name** | **str**| The name or ID of the app to list. | 
 **app_version** | **str**| The name or ID of the app to list. | 

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

# **save_umpire_file**
> WorkflowJSON save_umpire_file(app_name, app_version)

Pushes image from minio to /apps and overwrites it.

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
api_instance = walkoff_client.UmpireApi(walkoff_client.ApiClient(configuration))
app_name = 'app_name_example' # str | The name of the app to list.
app_version = 'app_version_example' # str | The version number of the app to list.

try:
    # Pushes image from minio to /apps and overwrites it.
    api_response = api_instance.save_umpire_file(app_name, app_version)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UmpireApi->save_umpire_file: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **app_name** | **str**| The name of the app to list. | 
 **app_version** | **str**| The version number of the app to list. | 

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

# **update_file**
> WorkflowJSON update_file(upload_file)

Updates a file in Minio

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
api_instance = walkoff_client.UmpireApi(walkoff_client.ApiClient(configuration))
upload_file = walkoff_client.UploadFile() # UploadFile | 

try:
    # Updates a file in Minio
    api_response = api_instance.update_file(upload_file)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling UmpireApi->update_file: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **upload_file** | [**UploadFile**](UploadFile.md)|  | 

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
**200** | Success |  -  |
**404** | Workflow does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

