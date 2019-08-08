# walkoff_client.SettingsApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**read_settings**](SettingsApi.md#read_settings) | **GET** /settings | Reads the settings
[**update_settings**](SettingsApi.md#update_settings) | **PUT** /settings | Updates the settings


# **read_settings**
> Settings read_settings()

Reads the settings

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
api_instance = walkoff_client.SettingsApi(walkoff_client.ApiClient(configuration))

try:
    # Reads the settings
    api_response = api_instance.read_settings()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SettingsApi->read_settings: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**Settings**](Settings.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**401** | Unauthorized access |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_settings**
> update_settings(settings)

Updates the settings

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
api_instance = walkoff_client.SettingsApi(walkoff_client.ApiClient(configuration))
settings = walkoff_client.Settings() # Settings | The settings object

try:
    # Updates the settings
    api_instance.update_settings(settings)
except ApiException as e:
    print("Exception when calling SettingsApi->update_settings: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **settings** | [**Settings**](Settings.md)| The settings object | 

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
**200** | Success |  -  |
**401** | Unauthorized access |  -  |
**515** | Could not write settings to file |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

