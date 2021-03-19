# Chase API

Deploy as a flask app, and set the base URL (with protocol and trailing slash) as `api_base_url` in config.yml files as needed.

## Endpoint Documentation

### General

**`/`**

GET: List team and placefile links

### Team

**`/team`**

GET: List all current teams and references to their respective view-only endpoints
PUSH: Create a new team. Fails if team already exists with provided ID. Returns needed auth info back to user.

**`/team/{team-id}`**

GET: List all current team info (position, vehicle, status, etc.), with references to placefiles
PUT (auth req): Update default allowed attributes of team (speed, direction, refuel). Return updated status (same as GET, but with any extra handshake stuff required, and maybe without placefiles?).

**`/team/{team-id}/location`**

GET: Return just the team's location
PUT (auth req): Special endpoint for initial setting of location on setup (fails if location already present, unless `force=True`, which may be a cheat code/easter egg/admin thing)

**`/team/{team-id}/vehicle`**

GET: Return just the team's vehicle info
PUT (auth req): Special endpoint for initial setting of vehicle on setup (fails if vehicle already present, unless `force=True`, which may be a cheat code/easter egg/admin thing)

**`/team/{team-id}/points`**

GET: Return just the team's points
PUT (admin auth req): Special endpoint for admin to adjust point amount

**`/team/{team-id}/balance`**

GET: Return just the team's balance
PUT (admin auth req): Special endpoint for admin to adjust balance

**`/team/{team-id}/verify`**

PUT (auth req): Test if the login credentials provided are valid
- Fields
    - needs_setup (bool)
    - setup_step (str)
    - team_name (str)

### Placefile

(all the below are only GET, no auth)

**`/placefile`**

List links to all placefile endpoints (NOT content)

**`/placefile/lsr`**

List current LSR information, with link to content
Give an error if not loaded (see `/placefile/lsr/load`)

**`/placefile/lsr/content`**

("Content-type: text/plain")

The actual, dynamically generated LSR placefile.

**`/placefile/lsr/load`**

Admin-only, hidden endpoint taking start, end, and wfos arguments (which are then passed as sts, ets and wfos to IEM GeoJSON endpoint) and loaded raw contents into the database. Actual lsrs are munged dynamically as the simulation runs.

**`/placefile/team`**

Link to:

- Individual team reference points
- All team files

**`/placefile/team/current`**

Current location (with direction hint) of all teams information, with actual content at `./content` link

**`/placefile/team/tracks`**

Current location of all teams, but with trailing track markers at a configurable number of history steps. As above re: `./content`.

**`/placefile/team/history`**

Current and all prior locations of all teams. As above re:`./content`.

**Likewise**

- **`/placefile/team/{team-id}/current`**
- **`/placefile/team/{team-id}/tracks`**
- **`/placefile/team/{team-id}/history`**

### Vehicle

**`/vehicle`**

List all vehicles shown in the application, with detailed information

**`/vehicle/{vehicle-id}`**

List properties for the given vehicle.

### Admin

**`simulation/timings`**

The only admin GET, really...gets the timing information as needed to convert between archive and current time.

**`simulation/start`**

Used by the `run-case` backend script to update the batch of settings associated with the start of the chase.

**`simulation/config`**

API-based way to tweak a single setting in the database's main config. Use with caution.

Hint: to stop the running of the case, `PUT {"simulation_running": 0}`.

**`simulation/hazard_config`**

API-based way to tweak a single setting in the database's hazard config. Use with caution.
