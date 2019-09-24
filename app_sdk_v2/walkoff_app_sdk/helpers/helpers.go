package helpers

import (
	"fmt"
	"os"
)

/**
  HELPER FUNCTIONS
*/
func Index(vs []string, t string) int {
	for i, v := range vs {
		if v == t {
			return i
		}
	}
	return -1
}

func Include(vs []string, t string) bool {
	return Index(vs, t) >= 0
}

func Diff(new []string, old []string) []string {
	out := []string{}
	for i := range new {
		if Index(old, new[i]) == -1 {
			out = append(out, new[i])
		}
	}
	return out
}

func Same(new []string, old []string) []string {
	out := []string{}
	for i := range new {
		if Index(old, new[i]) != -1 {
			out = append(out, new[i])
		}
	}
	return out
}

func CreateFile(p string) *os.File {
	f, err := os.Create(p)
	if err != nil {
		panic(err)
	}
	return f
}

func WriteFile(f *os.File) {
	fmt.Fprintln(f, "data")
}

func CloseFile(f *os.File) {
	err := f.Close()

	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		os.Exit(1)
	}
}
