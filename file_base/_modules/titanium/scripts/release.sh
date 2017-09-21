#!/usr/bin/env bash

version_type=$1
if [ "$version_type" == "" ]; then
   echo "need argument like 'master/minor/patch'"
   return
fi

#check command
if [ ! -x "$(command -v hub)" ]; then echo "need --> brew install hub" && return; fi
if [ ! -x "$(command -v bumpversion)" ]; then echo "need --> pip install bumpversion" && return; fi

function is_on_develop(){
    return $(test "$(git rev-parse --abbrev-ref HEAD)" = "develop")
}
is_on_develop
if [ $? != 0 ]; then
    echo "branch is not on develop"
    return
fi

function is_repo_clean(){
    return $(test -z "$(git status --porcelain | sed '/^.*??.*$/d')")
}

is_repo_clean
if [ $? != 0 ]; then
    echo "repo is not clean, please commit changed file before release"
    return
fi

new_ver=$(bumpversion --list --dry-run --allow-dirty $version_type | sed -n -e 's/^.*\(new_version=\)//p')
if [ "$new_ver" == "" ];then
    echo "fail to fetch new version"
else
    echo "starting release $new_ver"
    new_branch=$(echo release/$new_ver)
    git checkout -b $new_branch develop
    bumpversion $version_type
    git push --set-upstream origin $new_branch
    # open pull-request
    hub pull-request -o -m "review of release $new_ver" -b master -h $new_branch
fi
