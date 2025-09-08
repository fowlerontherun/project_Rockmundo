# RockMundo Frontend

## Setup

Install dependencies with [npm](https://www.npmjs.com/):

```bash
npm install
```

## Development

Start a development server that proxies API requests to the FastAPI backend:

```bash
npm run start
```

This launches the app at <http://localhost:3000/>.

## Static HTML Pages

Prebuilt pages live in the `pages/` directory. You can serve them with any static file server, for example:

```bash
npx serve pages
# or
python -m http.server --directory pages
```

When the backend is running, these files are also served under the `/frontend` path.

## Design Tokens

The frontend uses CSS variables as color tokens. Define new colors in `index.css` and `src/index.css` and consume them via `var(--token-name)` or the Tailwind color names configured in `tailwind.config.js`.

| Token | Purpose |
|-------|---------|
| `--bg-color` | Page background |
| `--text-color` | Default text color |
| `--accent-color` | Primary accent for interactive elements |
| `--border-color` | Subtle borders and separators |
| `--surface-color` | Panels and surfaces |
| `--muted-text` | Secondary text |
| `--success-color` | Positive/confirmation backgrounds |
| `--error-color` | Error/destructive backgrounds |
| `--inverse-text-color` | Text used on colored surfaces |

Dark theme overrides live under `[data-theme="dark"]`.
