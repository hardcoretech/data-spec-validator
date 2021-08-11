#!/usr/bin/env python

import os
from os.path import abspath, dirname, join
import os.path
import argparse
import configparser
import subprocess


CUR_DIR = dirname(abspath(__file__))
ROOT_DIR = abspath(join(CUR_DIR, '..'))


def parse_args():
    parser = argparse.ArgumentParser(description='data-spec-validator admin')
    subparsers = parser.add_subparsers()

    # === build  === #
    parser_build = subparsers.add_parser('build', help='build package')
    parser_build.set_defaults(func=build)

    # === upload  === #
    parser_upload = subparsers.add_parser('upload', help='upload to pypi')
    parser_upload.add_argument('--repo', dest='repo', default='pypi', choices=('pypi', 'testpypi'), help='upload repo, pypi or testpypi')
    parser_upload.set_defaults(func=upload)

    args = parser.parse_args()
    args.func(args)


def build(args):
    subprocess.check_call('python setup.py sdist', shell=True)
    subprocess.check_call('rm -vrf ./build ./*.egg-info', shell=True)


def upload(args):
    # remove old dist
    subprocess.check_call('rm -rf ./dist', shell=True)

    # build again
    build(args)

    if args.repo == 'pypi':
        ans = input("Are you sure to upload package to pypi?\n(y/N)")
        if ans.lower() != 'y':
            return

    # read local .pypirc first
    repo_pypirc_path = join(ROOT_DIR, '.pypirc')
    config_arg = f'--config-file={repo_pypirc_path}' if os.path.exists(repo_pypirc_path) else ''
    repo_arg = '-r testpypi' if args.repo == 'testpypi' else ''
    subprocess.check_call(f'twine upload {repo_arg} {config_arg} dist/*', shell=True)


def main():
    os.chdir(ROOT_DIR)
    parse_args()


if __name__ == '__main__':
    main()

