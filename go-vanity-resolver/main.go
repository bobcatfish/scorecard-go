package main

import (
	"flag"
	"fmt"
	"os"

	"golang.org/x/tools/go/vcs"
)

func main() {
	url := flag.String("url", "", "The vanity url to resolve")
	flag.Parse()
	if *url == "" {
		fmt.Fprintf(os.Stderr, "Must provide vanity url to resolve\n")
		os.Exit(1)
	}

	r, err := vcs.RepoRootForImportPath(*url, false)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Couldn't get repo for %s: %v\n", *url, err)
		os.Exit(1)
	}
	fmt.Println(r.Repo)
}
