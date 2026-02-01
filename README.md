# GSA Tracker (Streamlit Staff Portal)

## Requirements

- Python 3.10+ (3.11 recommended)

## Setup

1. Create a virtual environment

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set values as needed.

See [Streamlit Secrets Management](https://docs.streamlit.io/develop/concepts/connections/secrets-management) for details.

## Configuration (`.streamlit/secrets.toml`)

| Key               | Description                                              | Default              |
|-------------------|----------------------------------------------------------|----------------------|
| `SYSTEM_EMAIL`    | Email for the initial SUPER_ADMIN user.                  | `user@example.com`   |
| `SYSTEM_PASSWORD` | Password for the initial SUPER_ADMIN user.               | `ChangeMeNow!`       |

The database file is stored as `portal_data.json` in the project root.

## Run

```bash
streamlit run app.py
```

## Notes

- The app stores data in a local JSON file (`portal_data.json`). Treat it like application data; avoid committing it to git.
- `.streamlit/secrets.toml` is gitignored by default.

