package helpers

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