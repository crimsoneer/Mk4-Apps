#!/usr/bin/env python3

"""Toolchain for working with the TiLDA Mk4

Usage
------------------------------------

Reboot badge
$ tilda_tools reset

Soft reboot badge and start specific app
$ tilda_tools reset --boot my_app

Update files on the badge to match the current local version, restarts afterwards
$ tilda_tools sync

Update files in folder(s) to match current local version
$ tilda_tools sync my_game shared
$ tilda_tools sync <pattern1> <pattern2> ...

Sync (as above), but execute my_app after reboot
$ tilda_toold.py sync --boot my_app [<other sync parameter>]

Sync (as above), but execute a single file afterwards without copying it to the badge
$ tilda_toold.py sync --run some_other_file.py

Executes a single file on the badge without copying anything (Using pyboard.py)
$ tilda_tools run my_app/main.py

Runs local validation (doesn't require a badge, but doesn't run unit tests)
$ tilda_tools validate

Runs local validation and badge-side tests
$ tilda_tools test

Update firmware on badge (warning, this will delete all settings etc. stored on the badge!)
$ tilda_tools firmware-update

Setup wifi.json to be copied to the badge on every sync
$ tilda_tools wifi

Common parameters
-----------------

-d --device  : serial interface (default: auto)
-s --storage : path to flash storage

"""

import sys, glob
import sync, pyboard_util, wifi
from resources import *

def main():
    import argparse
    cmd_parser = argparse.ArgumentParser(description='Toolchain for working with the TiLDA Mk4')
    cmd_parser.add_argument('command', nargs=1, help='command [test|reset|sync|run|validate|wifi|firmware-update]', choices=['test', 'reset', 'sync', 'validate', 'run', 'wifi', 'firmware-update'])
    cmd_parser.add_argument('-d', '--device', help='the serial device of the badge')
    cmd_parser.add_argument('-s', '--storage', help='the usb mass storage path of the badge')
    cmd_parser.add_argument('-b', '--baudrate', default=115200, help='the baud rate of the serial device')
    cmd_parser.add_argument('-v', '--verbose', action='store_true', help='adds more output')
    cmd_parser.add_argument('--print_resources', action='store_true', help='prints resources in json')
    cmd_parser.add_argument('--boot', help='defines which app to boot into after reboot')
    cmd_parser.add_argument('--run', help='like run, but after a sync')
    cmd_parser.add_argument('-w', '--wait', default=0, type=int, help='seconds to wait for USB connected board to become available')
    cmd_parser.add_argument('paths', nargs='*', help='input files')
    args = cmd_parser.parse_args()
    command = args.command[0]
    path = sync.get_root()

    if command == "firmware-update":
        import pydfu_util # to avoid having a "usb" dependency for other calls
        pydfu_util.firmware_update(args.verbose)

    if command == "wifi":
        wifi.select_wifi()

    if command in ["test", "validate", "sync"]:
        resources = get_resources(path)
        add_metadata(path, resources)
        validate(path, resources)
        resolve_dependencies(resources)
        remove_upip(resources)
        if args.print_resources:
            print(pretty_print_resources(resources))
        errors = get_error_summary(resources)
        if errors:
            print("Problems found:\n")
            print(errors)
            sys.exit(1)
        print("Local Test: PASS")
        if command == "test":
            command = "sync"
            if len(args.paths) == 0:
                args.run = "test/main.py"
            else:
                if "." not in args.paths[0]:
                    args.paths[0] = "lib/%s.py" % args.paths[0]
                args.run = args.paths[0]


    if command in ["reset", "sync"]:
        pyboard_util.stop_badge(args, args.verbose)

    if command == "sync":
        paths = args.paths if len(args.paths) else None
        sync.sync(get_storage(args), paths, resources, args.verbose)

    if command in ["reset", "sync"]:
        sync.set_boot_app(get_storage(args), args.boot or "")
        pyboard_util.soft_reset(args)
        if args.run:
            command = "run"
            args.paths = [args.run]

    if command == "run":
        pyboard_util.check_run(args)
        pyboard_util.run(args)


    pyboard_util.close_pyb()

def find_storage():
    # todo: find solution for windows and linux
    for pattern in ['/Volumes/PYBFLASH', '/Volumes/NO NAME']:
        for path in glob.glob(pattern):
            return path
    print("Couldn't find badge storage - Please make it's plugged in and reset it if necessary")
    sys.exit(1)

def get_storage(args):
    if not args.storage:
        args.storage = find_storage()
    return args.storage



if __name__ == "__main__":
    main()

