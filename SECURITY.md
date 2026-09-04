# Security

This program can place **live orders** with real money.

## Do not put secrets in git

The desk reads two environment variables from a file you keep **outside** this repo:

- `POLYMARKET_KEY_ID`
- `POLYMARKET_SECRET_KEY`

Create keys at [polymarket.us/developer](https://polymarket.us/developer). Official steps: [Get your API keys](https://docs.polymarket.us/getting-started/quickstart). Copy `env.example`, fill it in, and point `POLY_ENV` at that file. Never commit the filled-in copy. `.env` and `*.env` are gitignored.

Do not paste keys into issues, pull requests, or chat.

## Runtime files

Fills, tape dumps, and session files live under `~/.grok/desk` (or `$POLY_DESK`). Those are not source code. Do not copy them into this repository.

## If a key leaked

Revoke it in Polymarket US settings and create a new pair. Treat an old key as burned.

## Reporting

Open a GitHub issue **without** attaching keys, `.env` files, or account screenshots that show balances you do not want public.
