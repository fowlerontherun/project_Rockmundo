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
