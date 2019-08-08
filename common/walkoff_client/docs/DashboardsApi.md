# walkoff_client.DashboardsApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_dashboard**](DashboardsApi.md#create_dashboard) | **POST** /dashboards | Create a dashboard
[**delete_dashboard**](DashboardsApi.md#delete_dashboard) | **DELETE** /dashboards/{dashboard} | Delete a dashboard
[**read_all_dashboards**](DashboardsApi.md#read_all_dashboards) | **GET** /dashboards | Read all dashboards
[**read_dashboard**](DashboardsApi.md#read_dashboard) | **GET** /dashboards/{dashboard} | Get a dashboard by id
[**update_dashboard**](DashboardsApi.md#update_dashboard) | **PUT** /dashboards | Update a dashboard


# **create_dashboard**
> Dashboard create_dashboard(dashboard)

Create a dashboard

Creates a dashboard from the JSON in request body

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
api_instance = walkoff_client.DashboardsApi(walkoff_client.ApiClient(configuration))
dashboard = walkoff_client.Dashboard() # Dashboard | The dashboard object to be created

try:
    # Create a dashboard
    api_response = api_instance.create_dashboard(dashboard)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DashboardsApi->create_dashboard: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dashboard** | [**Dashboard**](Dashboard.md)| The dashboard object to be created | 

### Return type

[**Dashboard**](Dashboard.md)

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

# **delete_dashboard**
> Dashboard delete_dashboard(dashboard)

Delete a dashboard

Deletes a dashboard by ID

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
api_instance = walkoff_client.DashboardsApi(walkoff_client.ApiClient(configuration))
dashboard = 'dashboard_example' # str | ID of the global to be fetched

try:
    # Delete a dashboard
    api_response = api_instance.delete_dashboard(dashboard)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DashboardsApi->delete_dashboard: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dashboard** | [**str**](.md)| ID of the global to be fetched | 

### Return type

[**Dashboard**](Dashboard.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Workflow updated. |  -  |
**404** | Dashboard does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_all_dashboards**
> list[Dashboard] read_all_dashboards(page=page)

Read all dashboards

Retrieves all dashboards currently stored in the database.

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
api_instance = walkoff_client.DashboardsApi(walkoff_client.ApiClient(configuration))
page = 56 # int | page of data to get (optional)

try:
    # Read all dashboards
    api_response = api_instance.read_all_dashboards(page=page)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DashboardsApi->read_all_dashboards: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| page of data to get | [optional] 

### Return type

[**list[Dashboard]**](Dashboard.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | No dashboards exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_dashboard**
> Dashboard read_dashboard(dashboard)

Get a dashboard by id

Retrieve a single dashboard from database by ID.

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
api_instance = walkoff_client.DashboardsApi(walkoff_client.ApiClient(configuration))
dashboard = 'dashboard_example' # str | ID of the global to be fetched

try:
    # Get a dashboard by id
    api_response = api_instance.read_dashboard(dashboard)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DashboardsApi->read_dashboard: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dashboard** | [**str**](.md)| ID of the global to be fetched | 

### Return type

[**Dashboard**](Dashboard.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | No dashboard with that ID exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_dashboard**
> InlineResponse200 update_dashboard(dashboard)

Update a dashboard

Updates a whole dashboard using the JSON request body

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
api_instance = walkoff_client.DashboardsApi(walkoff_client.ApiClient(configuration))
dashboard = walkoff_client.Dashboard() # Dashboard | The dashboard object to be updated

try:
    # Update a dashboard
    api_response = api_instance.update_dashboard(dashboard)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DashboardsApi->update_dashboard: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dashboard** | [**Dashboard**](Dashboard.md)| The dashboard object to be updated | 

### Return type

[**InlineResponse200**](InlineResponse200.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | Dashboard does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

