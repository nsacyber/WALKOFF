# Action

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**walkoff_type** | **str** | Workflow type for json decoder | [optional] 
**app_name** | **str** | The app to which the action belongs | 
**app_version** | **str** | The version of the app to which the action belongs | 
**errors** | **list[str]** | Errors attached to this ExecutionElement | [optional] 
**id_** | **str** | A 32-bit hexadecimal string representing a globally unique identifier | [optional] 
**is_valid** | **bool** | are the parameters of this action valid? | [optional] 
**label** | **str** | User-specified label for the action | 
**name** | **str** | The name of the function this Action will take | 
**parallel_parameter** | [**Parameter**](Parameter.md) |  | [optional] 
**parallelized** | **bool** |  | [optional] [default to False]
**parameters** | [**list[Parameter]**](Parameter.md) | The input parameters to the action | [optional] 
**position** | [**Position**](Position.md) |  | 
**priority** | **int** | The priority for this Action, which will be compared to other Actions with the same parent Action, descending, i.e. 5 is the highest priority. | [optional] [default to 3]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


