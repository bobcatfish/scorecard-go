# Scorecard for Go dependencies

This tool provides scorecard results for the depdencies **of a Go project** which are
**hosted on GitHub** (projects not hosted on GitHub cannot yet be scored by OSSF scorecards)
based on the [OSSF Scorecards](https://github.com/ossf/scorecard) project.

This is just a proof of concept and has (at least) the following limitations/room for improvement:
* For projects with a lot of dependencies, GitHub will rate limit you and you'll need to fill the cache in several passes
  * Alternatively the script could be updated to use [scorecard's bigquery cache](https://github.com/ossf/scorecard#public-data)
    but this only contains selective projects and may have stale data
* OSSF scorecard does not recognize versions at all; this script will evaluate all the dependencies at HEAD which is
  likely not the actual version your Go project is using
* This script does not yet support build flags (i.e. it may miss dependencies which are only used when complied with
  a specific build flag)
* Dependencies are being fetched with `go list -f '{{ .Deps }}'`; this may require additional logic to also respect
  replace directives
* Instead of a) evaluating all scorecard checks and b) hardcoding checks to fail on, the script could take as arguments
  which checks to evaluate and which to fail on (and even score thresholds to tolerate)

## Building the image

The image is published to [bobcatfish/scorecard-go](https://hub.docker.com/repository/docker/bobcatfish/scorecard-go).

Build the image with:

```bash
docker build -t bobcatfish/scorecard-go .
```

## Running the image

To use the image:
* Mount in the source code of the Go repo you want to check the dependencies of
* Set [GITHUB_AUTH_TOKEN](https://github.com/ossf/scorecard#authentication-and-setup)

In the container, run:
```bash
scorecard.py --path=<path to the root of the go project>  --package=<the package you want to evaluate>
```

You can use `--cache` to set a cache as well; for projects with a lot of dependencies, GitHub will rate limit you and you'll
need to fill the cache in several passes.

You can see an example of the image being invoked via a Tekton Task in
[scorecard-pipeline.yaml](https://github.com/bobcatfish/catservice/blob/main/tekton/scorecard-pipeline.yaml)
(see [instructions for how to run the Pipeline](https://github.com/bobcatfish/catservice/tree/main/tekton#running-the-scorecard-pipeline)).
