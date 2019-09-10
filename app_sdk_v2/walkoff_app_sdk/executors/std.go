package executors

import (
	"bufio"
	"io"
	"sync"
)

func Stdout(stdoutIn io.ReadCloser, output chan []byte, wg *sync.WaitGroup) {
	scannerOut := bufio.NewScanner(stdoutIn)
	scannerOut.Split(bufio.ScanLines)

	for scannerOut.Scan() {
		m := scannerOut.Bytes()
		if len(m) > 0 {
			output <- m
		}
	}
	wg.Done()
}

func Stderr(stderrIn io.ReadCloser, error_out chan []byte, wg *sync.WaitGroup){
	scannerErr := bufio.NewScanner(stderrIn)
	scannerErr.Split(bufio.ScanLines)

	for scannerErr.Scan() {
		m := scannerErr.Bytes()
		if len(m) > 0 {
			error_out <- m
		}
	}
	wg.Done()
}