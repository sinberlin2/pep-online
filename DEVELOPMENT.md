# Developing PEP Online

## Branches = two versions of the site

| Branch | What it is | How you preview | When the world sees it |
|--------|------------|-----------------|------------------------|
| **`main`** | Production — what you’re happy to ship | https://pep-drink.com (after push) | Every `git push origin main` |
| **`dev`** | Work in progress — experiments, half-done pages | **Local:** `npm start` → http://localhost:3000 | **Never** on pep-drink.com (unless you merge to `main`) |

Optional: pushing `dev` can give you a **private Netlify/Cloudflare preview URL** (not your custom domain) so you can open the WIP site on your phone without running a local server.

---

## One-time setup

### Create the `dev` branch (if you don’t have it yet)

```powershell
cd c:\Users\doyle\projects\pep-online
git checkout main
git pull
git checkout -b dev
git push -u origin dev
```

### Host settings (Netlify or Cloudflare)

**Production branch must be `main` only** so pep-drink.com never follows `dev`.

**Netlify:** Site configuration → Build & deploy → Continuous deployment → Production branch = **`main`**.  
Under **Branch deploys**, turn on deploys for branches other than production (so `dev` gets a URL like `dev--your-site.netlify.app`).

**Cloudflare Pages:** Production branch = **`main`**. Enable **Preview deployments** for non-production branches.

Your custom domain (**pep-drink.com**) stays attached only to **production** (`main`).

---

## Day-to-day: work on `dev`, release on `main`

### 1. Start on the dev branch

```powershell
git checkout dev
git pull
npm start
```

Edit files → refresh **http://localhost:3000**. Nothing on pep-drink.com changes.

### 2. Save WIP to GitHub (still not public on your domain)

```powershell
git add .
git commit -m "WIP: flavour carousel tweaks"
git push origin dev
```

- **Local:** still `npm start` on whatever branch you have checked out.
- **Preview (optional):** open the deploy URL Netlify/Cloudflare shows for branch `dev` (bookmark it in the host dashboard).

### 3. Release a new version to pep-drink.com

When this version is ready for the live site:

```powershell
git checkout main
git pull
git merge dev
git push origin main
```

Netlify/Cloudflare redeploys **main** → **https://pep-drink.com** updates in about a minute.

Keep working on `dev` for the next round:

```powershell
git checkout dev
```

### 4. Hotfix straight to production (rare)

```powershell
git checkout main
# fix, commit
git push origin main
git checkout dev
git merge main
git push origin dev
```

Keeps `dev` in sync with anything you fixed on `main`.

---

## Quick reference

```
dev branch  →  npm start (local)  +  optional preview URL on push
                ↓ merge when ready
main branch →  git push  →  pep-drink.com
```

---

## Before you merge `dev` → `main`

- [ ] Spot-check on localhost (or branch preview URL)
- [ ] Image paths under `brand/` load
- [ ] Sign-up forms — captured by Netlify Forms only on the live production site
