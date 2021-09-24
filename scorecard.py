#!/usr/bin/env python3

"""
scorecard.py evaluates if all dependencies for a project pass scorecard based requirements

The script takes the path to the project's go.mod file as an argument and for each entry,
retrieves all of it's dependencies, and so on. It then runs the OSSF scorecard against all
supported repos (i.e. github repos) and reports which checks are failed. If required checks
are failed the script will fail.

Requires:
- go to be installed.
- go-vanity-resolver to be compiled and available in PATH
- The scorecard binary (https://github.com/ossf/scorecard) to be installed and available in PATH
- GITHUB_AUTH_TOKEN to be set (https://github.com/ossf/scorecard#authentication)
"""
import argparse
import collections
import json
import os
import shlex
import signal
import subprocess
import sys
from tqdm import tqdm
from typing import Dict, List, Any


REQUIRED_CHECKS=[
  "Binary-Artifacts",
  "Vulnerabilities",
]


class Dependency(dict):
    def __init__(self, names, url, score):
        dict.__init__(self, names=names, url=url, score=score)


def get_deps(package: str) -> List[str]:
    deps = subprocess.run( ["go", "list", "-f", "{{ join .Deps \"\\n\" }}", package] , capture_output=True)
    if deps.returncode != 0:
        print(deps.stderr)
        deps.check_returncode()

    return list(set(deps.stdout.decode("utf-8").split()))


def get_std_lib() -> List[str]:
    deps = subprocess.run(shlex.split("go list std"), capture_output=True, check=True)
    return list(set(deps.stdout.decode("utf-8").split()))


def change_dir(path :str) -> None:
    abspath = os.path.abspath(path)
    os.chdir(abspath)


def resolve_urls(deps: List[str], cache: Dict[str, Dependency]) -> Dict[str, Dependency]:
    resolved_deps = dict(cache)
    known_deps = [name for dep in resolved_deps.values() for name in dep["names"]]
    for dep in tqdm(deps):
        if dep not in known_deps:
            resolved = subprocess.run(["go-vanity-resolver", "-url", dep], capture_output=True)
            if resolved.returncode != 0:
                print(resolved.stderr)
                resolved.check_returncode()
            resolved_url = resolved.stdout.decode("utf-8").strip()
            if resolved_url in resolved_deps:
                resolved_deps[resolved_url]["names"].append(dep)
            else:
                resolved_deps[resolved_url] = Dependency(names=[dep], url=resolved_url, score=[])
    return resolved_deps


def cache_from_file(path: str) -> Dict[str, Dependency]:
    dependencies = {}
    try:
        with open(path) as cache_file:
            cache = json.load(cache_file)
    # If there is no cache yet, act like the cache is empty
    except (IOError, json.decoder.JSONDecodeError):
        return {}

    for url, d in cache.items():
        dependencies[url] = Dependency(d["names"], d["url"], d["score"])

    return dependencies


def update_cache(path: str, dep_scores: Dict[str, Dependency]):
    # If there is no cache yet, create the file to start one
    with open(path, 'w+') as cache_file:
        json.dump(dep_scores, cache_file)


def scorecard(cache: str, deps: Dict[str, Dependency]) -> Dict[str, Dependency]:
    scored_deps = dict(deps)

    # If this gets interrupted, still update the cache before exiting
    def signal_handler(sig, frame):
        if cache != None:
            update_cache(cache, scored_deps)
        exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    for url, dependency in tqdm(scored_deps.items()):
        if len(dependency["score"]) == 0:
            if not url.startswith("https://github.com"):
                continue
            command = "scorecard --repo={} --format=json".format(url)
            results = subprocess.run(shlex.split(command), capture_output=True)
            if results.returncode != 0:
                print(results.stderr)
                results.check_returncode()
            score = json.loads(results.stdout.decode("utf-8"))["checks"]
            scored_deps[url]["score"] = score
    return scored_deps


def eval_scorecard_results(deps: Dict[str, Dependency]):
    failures = collections.defaultdict(list)

    for dep in deps.values():
        for s in dep["score"]:
            if s["score"] <= 0:
                failures[s["name"]].append({"url": dep["url"], "score": s["score"], "reason": s["reason"]})

    required_failures = collections.defaultdict(list)
    for failed_check, f in failures.items():
        print("*****{} Failures *****".format(failed_check))
        for failure in f:
            print("{} score: {} reason: {}".format(failure["url"], failure["score"], failure["reason"]))
            if failed_check in REQUIRED_CHECKS:
                required_failures[failed_check].append(failure["url"])

    if len(required_failures) > 0:
        sys.exit("Required checks failed:\n{}".format(
            "\n".join(["{}: {}".format(failed_check, ",".join(failures)) for failed_check, failures in required_failures.items()])))


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description="List all the recursive dependencies for a Go project")
    arg_parser.add_argument("--path", type=str, required=True,
                            help="The path to the root directory of the repo with the go code")
    arg_parser.add_argument("--package", type=str, required=True,
                            help="The package to get the dependencies of")
    arg_parser.add_argument("--cache", type=str, required=False,
                            help="Optional path to the json file containing mappings and scores")
    arg_parser.add_argument("--skip_lookup", default=False, action='store_true',
                            help="Set this to True to skip lookups and only use the cache")
    args = arg_parser.parse_args()

    if args.cache == "" and args.skip_lookup:
        sys.exit("Must provide cache file with --skip_lookup")

    change_dir(args.path)
    deps = get_deps(args.package)
    std_lib = get_std_lib()
    deps = [dep for dep in deps if dep not in std_lib]

    resolved_deps = {}
    if args.cache != None:
        resolved_deps = cache_from_file(args.cache)

    if not args.skip_lookup:
        resolved_deps = resolve_urls(deps, resolved_deps)
        resolved_deps = scorecard(args.cache, resolved_deps)

    if args.cache != None and not args.skip_lookup:
        update_cache(args.cache, resolved_deps)

    eval_scorecard_results(resolved_deps)
