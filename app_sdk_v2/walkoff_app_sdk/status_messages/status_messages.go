package status_messages

import (
	"encoding/json"
	"fmt"
	"github.com/go-redis/redis"
)

func Action_start_message(msg map[string]interface{}, starting_time string, client *redis.Client){
	type NodeStatusMessage map[string]interface{}
	type ActionStart map[string]interface{}

	//format parameters
	var parameter_result []string
	_ = json.Unmarshal([]byte(fmt.Sprintf("%s", msg["parameters"])), &parameter_result )

	action_result := make(ActionStart)
	action_result["name"] = fmt.Sprintf("%s", msg["name"])
	action_result["node_id"] = fmt.Sprintf("%s", msg["id_"])
	action_result["label"] = fmt.Sprintf("%s", msg["label"])
	action_result["app_name"] = fmt.Sprintf("%s", msg["app_name"])
	action_result["execution_id"] = fmt.Sprintf("%s", msg["execution_id"])
	action_result["status"] = "EXECUTING"
	action_result["started_at"] = starting_time

	ar, _ := json.Marshal(action_result)

	result := make(NodeStatusMessage)
	result[fmt.Sprintf("%s", msg["execution_id"])] = string(ar)

	message, err := client.XAdd(&redis.XAddArgs{
		Stream:       fmt.Sprintf("%v:results", msg["execution_id"]),
		Values:       result,
	}).Result()
	if err != nil{
		fmt.Println("Error processing result in fn action_start_message")
		fmt.Println(err)
	}
	_ = message
}

func Action_result_message(msg map[string]interface{}, out string, status string, starting_time string, completed_time string, client *redis.Client){
	type NodeStatusMessage map[string]interface{}
	type ActionResult map[string]interface{}
	type OutputResult map[string]interface{}

	//o, _ := json.Marshal(output)

	//format parameters
	var parameter_result []string
	_ = json.Unmarshal([]byte(fmt.Sprintf("%s", msg["parameters"])), &parameter_result )

	action_result := make(ActionResult)
	action_result["name"] = fmt.Sprintf("%s", msg["name"])
	action_result["node_id"] = fmt.Sprintf("%s", msg["id_"])
	action_result["label"] = fmt.Sprintf("%s", msg["label"])
	action_result["app_name"] = fmt.Sprintf("%s", msg["app_name"])
	action_result["execution_id"] = fmt.Sprintf("%s", msg["execution_id"])
	action_result["combined_id"] = fmt.Sprintf("%s:%s", msg["id_"], msg["execution_id"])
	action_result["result"] = out
	action_result["status"] = status
	action_result["started_at"] = starting_time
	action_result["completed_at"] = completed_time
	action_result["parameters"] = parameter_result

	ar, _ := json.Marshal(action_result)

	result := make(NodeStatusMessage)
	result[fmt.Sprintf("%s", msg["execution_id"])] = string(ar)

	message, err := client.XAdd(&redis.XAddArgs{
		Stream:       fmt.Sprintf("%v:results", msg["execution_id"]),
		Values: 	  result,
	}).Result()
	if err != nil{
		fmt.Println("Error processing result in fn action_result_message")
		fmt.Println(err)
	}
	_ = message
}
