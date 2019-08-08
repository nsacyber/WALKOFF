# WorkflowStatus

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**completed_at** | **datetime** | The timestamp of the end of workflow execution | [optional] 
**execution_id** | **str** | A 32-bit hexadecimal string representing a globally unique identifier | 
**name** | **str** | The name of the workflow. | 
**node_statuses** | [**list[NodeStatus]**](NodeStatus.md) | The statuses of the workflow nodes | 
**started_at** | **datetime** | The timestamp of the start of workflow execution | [optional] 
**status** | **str** | The current status of the workflow | 
**user** | **str** | The user that executed the workflow | [optional] 
**workflow_id** | **str** | A 32-bit hexadecimal string representing a globally unique identifier | 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


