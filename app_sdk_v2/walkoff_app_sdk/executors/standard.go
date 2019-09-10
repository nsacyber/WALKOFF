package executors

import (
	"bufio"
	"fmt"
	"os/exec"
	"sync"
	"syscall"
)

func Execute_standard_action(action string, streaming bool, output chan []byte, error_out chan []byte, status chan string, group *sync.WaitGroup, cwd string) {
	line := []string{"C:\\Users\\aheibel\\Documents\\GitHub\\WALKOFF\\venv\\Scripts\\python.exe", cwd + "\\src\\hello_world.py"}
	result := []byte{}
	errors := []byte{}
	var wg sync.WaitGroup

	cmd := exec.Command(line[0], line[1:]...)
	stdoutIn, _ := cmd.StdoutPipe()
	stderrIn, _ := cmd.StderrPipe()

	scannerOut := bufio.NewScanner(stdoutIn)
	scannerOut.Split(bufio.ScanLines)

	scannerErr := bufio.NewScanner(stderrIn)
	scannerErr.Split(bufio.ScanLines)

	status <- "start"
	cmd.Start()
	wg.Add(1)
	go func(){
		for scannerOut.Scan() {
			m := scannerOut.Bytes()
			if len(m) > 0 {
				//If streaming send directly to output otherwise collect output
				if streaming {
					output <- m
				} else {
					result = append(result, m...)
				}
			}
		}
		wg.Done()
	}()
	wg.Add(1)
	go func(){
		for scannerErr.Scan() {
			m := scannerErr.Bytes()
			if len(m) > 0 {
				//If streaming send directly to output otherwise collect output
				if streaming {
					error_out <- m
				} else {
					errors = append(errors, m...)
				}
			}
		}
		wg.Done()
	}()

	err := cmd.Wait()
	if !streaming {
		output <- result
		error_out <- errors
	}
	if err != nil{
		if exiterr, ok := err.(*exec.ExitError); ok {
			if st, ok := exiterr.Sys().(syscall.WaitStatus); ok {
				fmt.Println("Exit status %d", st.ExitStatus())
				status <- "error"
			}
		}
	}

	status <- "done"
}

