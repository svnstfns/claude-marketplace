# /truenas-list

List apps on the NAS, optionally filtered by state.

## Usage
/truenas-list [state]

`state` is optional. Valid values: RUNNING, STOPPED, CRASHED, DEPLOYING, STOPPING

## What this does
Calls `list_apps` with the given status_filter.
