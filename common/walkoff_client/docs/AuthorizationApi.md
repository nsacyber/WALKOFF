# walkoff_client.AuthorizationApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**login**](AuthorizationApi.md#login) | **POST** /auth | Login and get access and refresh tokens
[**logout**](AuthorizationApi.md#logout) | **POST** /auth/logout | Logout of walkoff
[**refresh**](AuthorizationApi.md#refresh) | **POST** /auth/refresh | Get a fresh access token


# **login**
> Token login(authentication)

Login and get access and refresh tokens

### Example

```python
from __future__ import print_function
import time
import walkoff_client
from walkoff_client.rest import ApiException
from pprint import pprint

# Create an instance of the API class
api_instance = walkoff_client.AuthorizationApi()
authentication = walkoff_client.Authentication() # Authentication | The username and password

try:
    # Login and get access and refresh tokens
    api_response = api_instance.login(authentication)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AuthorizationApi->login: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **authentication** | [**Authentication**](Authentication.md)| The username and password | 

### Return type

[**Token**](Token.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Success |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **logout**
> logout(inline_object)

Logout of walkoff

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
api_instance = walkoff_client.AuthorizationApi(walkoff_client.ApiClient(configuration))
inline_object = walkoff_client.InlineObject() # InlineObject | 

try:
    # Logout of walkoff
    api_instance.logout(inline_object)
except ApiException as e:
    print("Exception when calling AuthorizationApi->logout: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **inline_object** | [**InlineObject**](InlineObject.md)|  | 

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
**204** | Success |  -  |
**400** | Invalid refresh token |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **refresh**
> Token refresh()

Get a fresh access token

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
api_instance = walkoff_client.AuthorizationApi(walkoff_client.ApiClient(configuration))

try:
    # Get a fresh access token
    api_response = api_instance.refresh()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AuthorizationApi->refresh: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

[**Token**](Token.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**401** | Unauthorized |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

