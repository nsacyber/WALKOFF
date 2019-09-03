# WorkflowJSON

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**walkoff_type** | **str** | Workflow type for json decoder | [optional] 
**actions** | [**list[Action]**](Action.md) | Action nodes in workflow | [optional] 
**branches** | [**list[Branch]**](Branch.md) | Edges connecting nodes in workflow | [optional] 
**conditions** | [**list[Condition]**](Condition.md) | Condition nodes in workflow | [optional] 
**description** | **str** | Description of the workflow | [optional] 
**errors** | **list[str]** | Errors attached to this ExecutionElement | [optional] 
**execution_id** | **str** | A 32-bit hexadecimal string representing a globally unique identifier | [optional] 
**id_** | **str** | A 32-bit hexadecimal string representing a globally unique identifier | [optional] 
**is_valid** | **bool** | Is this workflow able to be run? | [optional] 
**name** | **str** | The name of the workflow. | 
**permissions** | **list[object]** |  | [optional] 
**start** | **str** | A 32-bit hexadecimal string representing a globally unique identifier | [optional] 
**tags** | **list[str]** | Tag for workflow | [optional] 
**transforms** | [**list[Transform]**](Transform.md) | Transform nodes in workflow | [optional] 
**triggers** | [**list[Trigger]**](Trigger.md) | Trigger nodes in workflow | [optional] 
**workflow_variables** | [**list[WorkflowVariable]**](WorkflowVariable.md) | The environment variables for this workflow | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


