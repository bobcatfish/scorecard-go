# Go Vanity URL resolver

This program is just a wrapper for
[`RepoRootForImportPath`](https://pkg.go.dev/golang.org/x/tools/go/vcs#RepoRootForImportPath)
which is a function used by Go to resolve dependencies but unfortunately not available directly
via a Go command line tool.

This program will take a URL corresponding to a Go package as an argument and will resolve
that URL if it's a vanity URL and print to stdout the URL the package is actually fetched
from.
