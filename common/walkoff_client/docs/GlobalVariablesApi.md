# walkoff_client.GlobalVariablesApi

All URIs are relative to *http://localhost/walkoff/api*

Method | HTTP request | Description
------------- | ------------- | -------------
[**create_global**](GlobalVariablesApi.md#create_global) | **POST** /globals | Add a global
[**create_global_templates**](GlobalVariablesApi.md#create_global_templates) | **POST** /globals/templates | Add a global
[**delete_global**](GlobalVariablesApi.md#delete_global) | **DELETE** /globals/{global_var} | Remove a global
[**delete_global_templates**](GlobalVariablesApi.md#delete_global_templates) | **DELETE** /globals/templates/{global_template} | Remove a global
[**read_all_global_templates**](GlobalVariablesApi.md#read_all_global_templates) | **GET** /globals/templates | Get all global templates
[**read_all_globals**](GlobalVariablesApi.md#read_all_globals) | **GET** /globals | Get all globals
[**read_global**](GlobalVariablesApi.md#read_global) | **GET** /globals/{global_var} | Read a global
[**read_global_templates**](GlobalVariablesApi.md#read_global_templates) | **GET** /globals/templates/{global_template} | Read a global template
[**update_global**](GlobalVariablesApi.md#update_global) | **PUT** /globals/{global_var} | Update a global
[**update_global_templates**](GlobalVariablesApi.md#update_global_templates) | **PUT** /globals/templates/{global_template} | Update a global template


# **create_global**
> GlobalVariable create_global(global_variable)

Add a global

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
global_variable = walkoff_client.GlobalVariable() # GlobalVariable | 

try:
    # Add a global
    api_response = api_instance.create_global(global_variable)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->create_global: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **global_variable** | [**GlobalVariable**](GlobalVariable.md)|  | 

### Return type

[**GlobalVariable**](GlobalVariable.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Object created |  -  |
**400** | GlobalVariable already exists |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_global_templates**
> GlobalVariableTemplate create_global_templates(global_variable_template)

Add a global

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
global_variable_template = walkoff_client.GlobalVariableTemplate() # GlobalVariableTemplate | 

try:
    # Add a global
    api_response = api_instance.create_global_templates(global_variable_template)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->create_global_templates: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **global_variable_template** | [**GlobalVariableTemplate**](GlobalVariableTemplate.md)|  | 

### Return type

[**GlobalVariableTemplate**](GlobalVariableTemplate.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**201** | Object created |  -  |
**400** | GlobalVariable already exists |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_global**
> delete_global(global_var)

Remove a global

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
global_var = 'global_var_example' # str | ID of the global to be fetched

try:
    # Remove a global
    api_instance.delete_global(global_var)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->delete_global: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **global_var** | [**str**](.md)| ID of the global to be fetched | 

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
**404** | GlobalVariable does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_global_templates**
> delete_global_templates(global_template)

Remove a global

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
global_template = 'global_template_example' # str | ID of the global template to be fetched

try:
    # Remove a global
    api_instance.delete_global_templates(global_template)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->delete_global_templates: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **global_template** | [**str**](.md)| ID of the global template to be fetched | 

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
**404** | GlobalVariableTemplate does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_all_global_templates**
> list[GlobalVariableTemplate] read_all_global_templates(page=page)

Get all global templates

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
page = 56 # int | page of data to get (optional)

try:
    # Get all global templates
    api_response = api_instance.read_all_global_templates(page=page)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->read_all_global_templates: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| page of data to get | [optional] 

### Return type

[**list[GlobalVariableTemplate]**](GlobalVariableTemplate.md)

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

# **read_all_globals**
> list[GlobalVariable] read_all_globals(page=page, to_decrypt=to_decrypt)

Get all globals

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
page = 56 # int | page of data to get (optional)
to_decrypt = 'to_decrypt_example' # str | Determine whether or not to decrypt global variable (optional)

try:
    # Get all globals
    api_response = api_instance.read_all_globals(page=page, to_decrypt=to_decrypt)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->read_all_globals: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page** | **int**| page of data to get | [optional] 
 **to_decrypt** | **str**| Determine whether or not to decrypt global variable | [optional] 

### Return type

[**list[GlobalVariable]**](GlobalVariable.md)

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

# **read_global**
> GlobalVariable read_global(global_var, to_decrypt=to_decrypt)

Read a global

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
global_var = 'global_var_example' # str | ID of the global to be fetched
to_decrypt = 'to_decrypt_example' # str | Determine whether or not to decrypt global variable (optional)

try:
    # Read a global
    api_response = api_instance.read_global(global_var, to_decrypt=to_decrypt)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->read_global: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **global_var** | [**str**](.md)| ID of the global to be fetched | 
 **to_decrypt** | **str**| Determine whether or not to decrypt global variable | [optional] 

### Return type

[**GlobalVariable**](GlobalVariable.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | GlobalVariable does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **read_global_templates**
> GlobalVariableTemplate read_global_templates(global_template)

Read a global template

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
global_template = 'global_template_example' # str | ID of the global template to be fetched

try:
    # Read a global template
    api_response = api_instance.read_global_templates(global_template)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->read_global_templates: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **global_template** | [**str**](.md)| ID of the global template to be fetched | 

### Return type

[**GlobalVariableTemplate**](GlobalVariableTemplate.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | GlobalVariableTemplate does not exist. |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_global**
> GlobalVariable update_global(global_var, global_variable)

Update a global

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
global_var = 'global_var_example' # str | ID of the global to be fetched
global_variable = walkoff_client.GlobalVariable() # GlobalVariable | The new global object to be updated

try:
    # Update a global
    api_response = api_instance.update_global(global_var, global_variable)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->update_global: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **global_var** | [**str**](.md)| ID of the global to be fetched | 
 **global_variable** | [**GlobalVariable**](GlobalVariable.md)| The new global object to be updated | 

### Return type

[**GlobalVariable**](GlobalVariable.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | GlobalVariable does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_global_templates**
> GlobalVariableTemplate update_global_templates(global_template, global_variable_template)

Update a global template

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
api_instance = walkoff_client.GlobalVariablesApi(walkoff_client.ApiClient(configuration))
global_template = 'global_template_example' # str | ID of the global template to be fetched
global_variable_template = walkoff_client.GlobalVariableTemplate() # GlobalVariableTemplate | The new global template to be updated

try:
    # Update a global template
    api_response = api_instance.update_global_templates(global_template, global_variable_template)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling GlobalVariablesApi->update_global_templates: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **global_template** | [**str**](.md)| ID of the global template to be fetched | 
 **global_variable_template** | [**GlobalVariableTemplate**](GlobalVariableTemplate.md)| The new global template to be updated | 

### Return type

[**GlobalVariableTemplate**](GlobalVariableTemplate.md)

### Authorization

[AuthenticationToken](../README.md#AuthenticationToken)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Success |  -  |
**404** | GlobalVariableTemplate does not exist |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

