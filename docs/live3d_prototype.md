# live3d Prototype

The `live3d` module is a minimal experiment for visualising gig completion
results in 3D. It uses `matplotlib` to render a single bar showing the
crowd attendance for a gig.

## Build

Install the optional dependency:

```bash
pip install matplotlib
```

## Run

Create some gig data and then render it:

```bash
# assuming an existing SQLite database with gigs
python -m live3d --gig-id 1 --db path/to/gig.db
```

The command fetches the gig's completion data using
`backend.services.gig_service` and displays the attendance as a 3D bar.
