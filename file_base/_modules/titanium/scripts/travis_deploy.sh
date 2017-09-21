#!/usr/bin/env bash

function git_tag(){
    # Get the deploy key by using Travis's stored variables to decrypt deploy_key.enc
    ENCRYPTED_KEY_VAR="encrypted_${ENCRYPTION_LABEL}_key"
    ENCRYPTED_IV_VAR="encrypted_${ENCRYPTION_LABEL}_iv"
    ENCRYPTED_KEY=${!ENCRYPTED_KEY_VAR}
    ENCRYPTED_IV=${!ENCRYPTED_IV_VAR}
    openssl aes-256-cbc -K $ENCRYPTED_KEY -iv $ENCRYPTED_IV -in deploy_key.enc -out deploy_key -d
    chmod 600 deploy_key
    eval `ssh-agent -s`
    ssh-add deploy_key

    current_ver=$(bumpversion --list --dry-run --allow-dirty patch | sed -n -e 's/^.*\(current_version=\)//p') \
    && git config --global user.email "builds@travis-ci.com" \
    && git config --global user.name "Travis CI" \
    && git tag $current_ver -a -m "Generated tag from TravisCI build $current_ver" \
    && git push git@github.com:splksusqa/titanium.git --tags
}

if [ "$TRAVIS_BRANCH" = "$BDBRANCH" ] && [ "$TRAVIS_PYTHON_VERSION" = "$BDPYVERSION" ] && [ "$TRAVIS_PULL_REQUEST" == "false" ];then
    echo "build on current branch!"
    git_tag || { echo 'fail to tag' ; exit 1; }
    python setup.py sdist || { echo 'fail to build' ; exit 1; }
    dist_file=$( find . -name *.tar.gz )
    curl -F package=@$dist_file $PYPISITE
else
    echo "No need for current branch to build"
fi;