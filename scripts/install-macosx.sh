#!/usr/bin/env bash
APP_NAME=$1
test -f $HOME/Applications/${APP_NAME} || rm -rf $HOME/Applications/${APP_NAME}
mv ./dist/${APP_NAME} $HOME/Applications
