#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset

MANDOLIN_VERSION=`grep "API_VERSION =" app/main.py | sed 's/ //g' | sed 's/"//g'`
export $MANDOLIN_VERSION
echo "About to release the version $API_VERSION of Mandolin"
echo "Git tags:"
git for-each-ref --format='%(*creatordate:raw)%(creatordate:raw) %(refname) %(*objectname) %(objectname)' refs/tags | sort -n | awk '{ print $4, $3; }'
echo ""
read -p "Are you sure (y/N)? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
fi

# Check if there are no uncommited changes
git status --porcelain --untracked-files=no | grep '^.M' > /dev/null
CHANGED=$?
if [[ $CHANGED ]]
then
  echo "There are uncommitted changes"
  exit 1
fi

git status --porcelain --untracked-files=no | grep '^U.' > /dev/null
CONFLICTS=$?
if [[ $CONFLICTS ]]
then
  echo "There are merge or rebase conflicts"
  exit 1
fi

git status --porcelain --untracked-files=no | grep '^' > /dev/null
CLEAN=$((1 - $?))
if [[ $CLEAN ]]
then
  echo "There are *no* changes, conflicts, or uncommitted staged files"
  exit 1
fi

rm -f openapi.json
fastapi run app/main.py --port 8000 &
sleep 2
curl -f http://localhost:8000/openapi.json -o openapi.json
ps -ef | grep fastapi | grep -v grep | awk '{print $2}' | xargs kill -9

npm i
./node_modules/.bin/openapi-generator-cli generate

echo ""
read -p "Create the tag $API_VERSION (y/N)? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    [[ "$0" = "$BASH_SOURCE" ]] && exit 1 || return 1
fi

git tag -a "v$API_VERSION" -m "Release v$API_VERSION"
git push origin main --follow-tags

cd ../mandolin-python-client
git add .
git commit -m "Automatic generation of the client for the version $API_VERSION of Mandolin"
git tag -a "v$API_VERSION" -m "Release v$API_VERSION"
git push origin main --follow-tags

cd ../mandolin