package main

import (
	"../executors"
	"../status_messages"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	s"strings"
	"github.com/go-redis/redis"
	"sync"
	"syscall"
	"time"
)

var cwd, _ = os.Getwd()
var path = filepath.Dir(cwd)
var app_name = os.Getenv("APP_NAME")
var app_version = os.Getenv("APP_VERSION")
var app_group = app_name + ":" + app_version
var stdoutPtr, stderrPtr, filePtr, dirPtr, streaming_ptr *bool
var file_path_ptr, file_delim_ptr, dir_path_ptr, stream_ptr, id_ptr *string
var cmd_ptr, arg_ptr, msg_ptr *string
var watchers executors.Watchers
var command, args []string
var stream, id_ string
var msg map[string]interface{}

func main() {
	localPtr := flag.Bool("local", false, "run action locally")

	stream_ptr = flag.String("stream", "", "redis stream")
	id_ptr = flag.String("message_id", "", "message id")
	msg_ptr = flag.String("message", "", "redis message")

	stream = *stream_ptr
	id_ = *id_ptr

	// Action
	cmd_ptr = flag.String("command", "", "command to run")
	arg_ptr = flag.String("arguments", "[]", "command arguments")

	streaming_ptr = flag.Bool("streaming", false, "action streaming or not")

	// Execution Arguments
	stdoutPtr = flag.Bool("stdout", false, "listen for stdout")
	stderrPtr = flag.Bool("stderr", false, "listen for stderr")
	filePtr = flag.Bool("file", false, "listen on file")
	dirPtr = flag.Bool("dir", false, "listen on directory")

	// File Args
	file_path_ptr = flag.String("file_watch_path", "", "file path to watch")
	file_delim_ptr = flag.String("file_delim", "\n", "file reader delimeter")

	// Dir Args
	dir_path_ptr = flag.String("dir_watch_path", "/", "directory to watch")

	// Execute Command Line Parsing
	flag.Parse()

	host  := ""
	if *localPtr == true{
		host = "localhost:6379"
	}else{
		host = "resource_redis:6379"
	}

	watchers = executors.Create_watcher(*stdoutPtr, *stderrPtr, *filePtr, *dirPtr, *file_path_ptr, *file_delim_ptr, *dir_path_ptr)

	//Generate Command and Arguments
	command = []string{*cmd_ptr}
	args = s.Split(*arg_ptr, ",")
	command = append(command, args...)

	//Parse Message
	msg_bytes := []byte(*msg_ptr)
	json.Unmarshal(msg_bytes, &msg)

	//Start Redis connection
	client := redis.NewClient(&redis.Options{
		Addr:     host,
		Password: "", // no password set
		DB:       0,  // use default DB
	})

	fmt.Println("Executing Action")

	var wg sync.WaitGroup
	wg.Add(1)
	go execute_action(app_name, command, watchers, *streaming_ptr, &wg, cwd)
	wg.Add(1)
	go process_result(watchers, &wg, msg, client)
	wg.Wait()

	fmt.Println("SHUTTING DOWN")
	executors.Close_watchers(watchers)
	shutdown(client)
}

func execute_action(action string, command []string, watchers executors.Watchers, streaming bool,  group *sync.WaitGroup, cwd string){
	var wg sync.WaitGroup

	cmd_state := executors.ExecutionState{State: 0}

	cmd := exec.Command(command[0], command[1:]...)
	stdoutIn, _ := cmd.StdoutPipe()
	stderrIn, _ := cmd.StderrPipe()

	watchers.Status <- 1
	cmd.Start()

	if watchers.Stdout{
		wg.Add(1)
		go executors.Stdout(stdoutIn, watchers.Stdwatch, &wg)
	}
	if watchers.Stderr{
		wg.Add(1)
		go executors.Stderr(stderrIn, watchers.Errwatch, &wg)
	}
	if watchers.File{
		wg.Add(1)
		go executors.File(watchers.FileArgs.Path, watchers.Filewatch, cmd_state, watchers.FileArgs.Delim, &wg)
	}
	if watchers.Dir{
		wg.Add(1)
		go executors.Dir(watchers.DirArgs.Path, watchers.Dirwatch, watchers.Status, &wg)
	}


	err := cmd.Wait()
	cmd_state.Set(2)
	if watchers.File {
		wg.Done()
	}
	if watchers.Dir {
		wg.Done()
	}

	wg.Wait()

	//Check if non-zero error code
	if err != nil{
		if exiterr, ok := err.(*exec.ExitError); ok {
			if st, ok := exiterr.Sys().(syscall.WaitStatus); ok {
				fmt.Println("Exit status %d", st.ExitStatus())
				watchers.Status <- -1
			}
		}
	}
	watchers.Status <- 3
	group.Done()
}

func process_result(watchers executors.Watchers, group *sync.WaitGroup, msg map[string]interface{}, client *redis.Client) {
	var starting_time, completed_time string
	var out []byte

	for{
		select {
		case s := <- watchers.Status:
			if s == 1{
				starting_time = time.Now().Format("2006-01-02 15:04:05.999999")
				status_messages.Action_start_message(msg, starting_time, client)
			} else if s == 3{
				completed_time = time.Now().Format("2006-01-02 15:04:05.999999")
				fmt.Println(out)
				status_messages.Action_result_message(msg, string(out), "SUCCESS", starting_time, completed_time, client)
				group.Done()
			} else if s == -1{
				completed_time = time.Now().Format("2006-01-02 15:04:05.999999")
				status_messages.Action_result_message(msg, string(out), "FAILURE", starting_time, completed_time, client)
				group.Done()
			}
		case data := <- watchers.Stdwatch:
			out = append(out, data...)
		case data := <- watchers.Errwatch:
			out = append(out, data...)
		case data := <- watchers.Filewatch:
			out = append(out, data...)
		case data := <- watchers.Dirwatch:
			out = append(out, data...)
		}

	}
}

func shutdown(client *redis.Client){
	err := client.XAck(stream, app_group, id_).Err()
	if err != nil {
		fmt.Println(err)
	}

	err = client.XDel(stream, id_).Err()
	if err != nil {
		fmt.Println(err)
	}
}