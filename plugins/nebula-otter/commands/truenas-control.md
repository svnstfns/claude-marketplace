# /truenas-control

Start, stop, or restart a single app.

## Usage
/truenas-control <app-name> <action>

`action` is one of: start, stop, restart

## What this does
Routes to `start_app`, `stop_app`, or `restart_app` (which calls app.redeploy).
