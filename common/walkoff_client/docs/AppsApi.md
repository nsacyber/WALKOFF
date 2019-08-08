# walkoff_client.AppsApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_app_api**](AppsApi.md#create_app_api) | **POST** /apps/apis | Create app api
[**delete_app_api**](AppsApi.md#delete_app_api) | **DELETE** /apps/apis/{app} | Delete app api
[**read_all_app_apis**](AppsApi.md#read_all_app_apis) | **GET** /apps/apis | Get all app apis
[**read_app_api**](AppsApi.md#read_app_api) | **GET** /apps/apis/{app} | Get and app&#39;s api
[**update_app_api**](AppsApi.md#update_app_api) | **PUT** /apps/apis/{app} | Replace app api


# **create_app_api**
> AppApi create_app_api(app_api)

Create app api

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
api_instance = walkoff_client.AppsApi(walkoff_client.ApiClient(configuration))
app_api = walkoff_client.AppApi() # AppApi | The app api object to be created

try:
    # Create app api
    api_response = api_instance.create_app_api(app_api)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AppsApi->create_app_api: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **app_api** | [**AppApi**](AppApi.md)| The app api object to be created | 

### Return type

[**AppApi**](AppApi.md)

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

# **delete_app_api**
> delete_app_api(app)

Delete app api

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
api_instance = walkoff_client.AppsApi(walkoff_client.ApiClient(configuration))
app = 'app_example' # str | Name OR ID of the app to get

try:
    # Delete app api
    api_instance.delete_app_api(app)
except ApiException as e:
    print("Exception when calling AppsApi->delete_app_api: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **app** | **str**| Name OR ID of the app to get | 

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
**404** | AppApi does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_all_app_apis**
> list[AppApi] read_all_app_apis(page=page)

Get all app apis

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
api_instance = walkoff_client.AppsApi(walkoff_client.ApiClient(configuration))
page = 56 # int | page of data to get (optional)

try:
    # Get all app apis
    api_response = api_instance.read_all_app_apis(page=page)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AppsApi->read_all_app_apis: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| page of data to get | [optional] 

### Return type

[**list[AppApi]**](AppApi.md)

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

# **read_app_api**
> AppApi read_app_api(app)

Get and app's api

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
api_instance = walkoff_client.AppsApi(walkoff_client.ApiClient(configuration))
app = 'app_example' # str | Name OR ID of the app to get

try:
    # Get and app's api
    api_response = api_instance.read_app_api(app)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AppsApi->read_app_api: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **app** | **str**| Name OR ID of the app to get | 

### Return type

[**AppApi**](AppApi.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | App does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_app_api**
> AppApi update_app_api(app, app_api)

Replace app api

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
api_instance = walkoff_client.AppsApi(walkoff_client.ApiClient(configuration))
app = 'app_example' # str | Name OR ID of the app to get
app_api = walkoff_client.AppApi() # AppApi | The app api object to be updated

try:
    # Replace app api
    api_response = api_instance.update_app_api(app, app_api)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AppsApi->update_app_api: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **app** | **str**| Name OR ID of the app to get | 
 **app_api** | [**AppApi**](AppApi.md)| The app api object to be updated | 

### Return type

[**AppApi**](AppApi.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**400** | AppApi already exists. |  -  |
**404** | AppApi does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

