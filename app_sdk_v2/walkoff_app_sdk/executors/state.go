package executors

import "sync"

type ExecutionState struct{
	State int
	Mutex sync.Mutex
}

func (s *ExecutionState) Set(n int) {
	s.Mutex.Lock()
	s.State = n
	s.Mutex.Unlock()
}

func (s *ExecutionState) Value() int {
	s.Mutex.Lock()
	n := s.State
	s.Mutex.Unlock()
	return n
}
