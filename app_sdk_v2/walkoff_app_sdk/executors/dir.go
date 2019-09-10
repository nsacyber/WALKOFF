package executors

import (
	"fmt"
	"github.com/fsnotify/fsnotify"
	"sync"
)

func Dir(dirname string, output chan []byte, status chan int, wg *sync.WaitGroup){
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		fmt.Println("ERROR", err)
	}
	defer watcher.Close()

	go func() {
		for {
			select {
			case event := <-watcher.Events:
				fmt.Println([]byte(event.Name))
				output <- []byte(event.Name)
			case err := <-watcher.Errors:
				if err != nil{
					fmt.Println("ERROR", err)
				}

			}

			select{
			case msg := <- status:
				if msg == 2{
					break
				}
			default:
			}
		}
	}()

	if err := watcher.Add(dirname); err != nil {
		fmt.Println("ERROR", err)
	}
	wg.Done()
}

