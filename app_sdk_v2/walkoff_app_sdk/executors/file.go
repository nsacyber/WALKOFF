package executors

import (
	"bufio"
	"fmt"
	"github.com/fsnotify/fsnotify"
	"io"
	"os"
	"sync"
)

func File(filename string, output chan []byte, state ExecutionState, delim byte, wg *sync.WaitGroup){
	doneFlag := false
	file, _ := os.Open(filename)
	watcher, _ := fsnotify.NewWatcher()
	defer watcher.Close()
	_ = watcher.Add(filename)

	r := bufio.NewReader(file)
	for {
		by, err := r.ReadBytes(delim)
		if err == io.EOF && doneFlag {
			break
		}
		if err != nil && err != io.EOF {
			fmt.Println(err)
		}
		output <- by

		if err != io.EOF {
			continue
		}
		if err = waitForChange(watcher); err != nil {
			fmt.Println(err)
		}
		//If command is done, set flag to continue reading file to EOF and return afterwards
		if state.Value() == 2 {
			doneFlag = true
		}
	}

	wg.Done()
}
func waitForChange(w *fsnotify.Watcher) error {
	for {
		select {
		case event := <-w.Events:
			if event.Op&fsnotify.Write == fsnotify.Write {
				return nil
			}
		case err := <-w.Errors:
			fmt.Println(err)
		default:
		}
	}
}
