package executors

type Watchers struct {
	Stdout bool
	Stderr bool
	File bool
	Dir bool

	FileArgs FileWatchArgs
	DirArgs DirWatchArgs
	StdArgs StdWatchArgs
	ErrArgs ErrWatchArgs

	Stdwatch chan []byte
	Errwatch chan []byte
	Filewatch chan []byte
	Dirwatch chan []byte
	Status chan int
}

type FileWatchArgs struct {
	Path string
	Delim byte
}

type DirWatchArgs struct {
	Path string
}

type StdWatchArgs struct {
}

type ErrWatchArgs struct {
}

func Create_watcher(stdoutPtr bool, stderrPtr bool, filePtr bool, dirPtr bool,
					file_path string, file_delimeter string, dir_watch string) Watchers{
	var out Watchers
	if stdoutPtr {
		out.Stdout = true
		out.Stdwatch = make(chan []byte)

		out.StdArgs = StdWatchArgs{}
	}
	if stderrPtr {
		out.Stderr = true
		out.Errwatch = make(chan []byte)

		out.ErrArgs = ErrWatchArgs{}
	}
	if filePtr {
		out.File = true
		out.Filewatch = make(chan []byte)

		//Add File Args
		delim := []byte(file_delimeter)
		args := FileWatchArgs{Path: file_path, Delim: delim[0]}
		out.FileArgs = args
	}
	if dirPtr {
		out.Dir = true
		out.Dirwatch = make(chan []byte)

		//Add Dir Args
		args := DirWatchArgs{Path: dir_watch}
		out.DirArgs = args
	}
	out.Status = make(chan int)
	return out
}

func Close_watchers(watchers Watchers){
	if watchers.Stdout{
		close(watchers.Stdwatch)
	}
	if watchers.Stderr{
		close(watchers.Stdwatch)
	}
	if watchers.File{
		close(watchers.Filewatch)
	}
	if watchers.Dir{
		close(watchers.Dirwatch)
	}
}
