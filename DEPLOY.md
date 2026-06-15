# Deploy PEP Online to pep-drink.com

Your site is **static** (HTML/CSS/JS) — no server required. You connect a free host to your GitHub repo, then point **pep-drink.com** DNS at that host.

**Domain:** `pep-drink.com` (recommended: also `www.pep-drink.com`)  
**Repo:** `github.com/sinberlin2/pep-online`

---

## What you need

1. **pep-drink.com** (and access to its DNS at your registrar)
2. Access to your **domain registrar** (where you bought it: GoDaddy, Namecheap, Cloudflare, etc.)
3. This project pushed to **GitHub** on `main`
4. (Optional) **Formspree** URL in `js/config.js` so the venue form sends email in production

---

## Recommended: Cloudflare Pages (free + easy DNS if domain is on Cloudflare)

### A. Deploy the site

1. Sign in at [dash.cloudflare.com](https://dash.cloudflare.com)
2. **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
3. Authorize GitHub → select **sinberlin2/pep-online**
4. Build settings:
   - **Production branch:** `main`
   - **Build command:** *(leave empty)*
   - **Build output directory:** `/` (project root — `index.html` is at the top)
5. **Save and deploy** — you get a URL like `pep-online.pages.dev`

### B. Add your custom domain

1. Pages project → **Custom domains** → **Set up a custom domain**
2. Enter **`www.pep-drink.com`** and **`pep-drink.com`** (apex)
3. Cloudflare shows **DNS records** to add (often automatic if the domain is already in the same account)
4. Wait a few minutes — **SSL** is automatic

### C. If the domain is at another registrar

At your registrar’s DNS panel, add what Cloudflare shows, typically:

| Type | Name | Value |
|------|------|--------|
| CNAME | `www` | `pep-online.pages.dev` (your actual `*.pages.dev` hostname) |

For **pep-drink.com** (no www), follow Cloudflare’s wizard — they usually add apex automatically or use CNAME flattening.

**If DNS is NOT on Cloudflare** (e.g. GoDaddy, Namecheap), add only what your Pages dashboard shows for `pep-drink.com` and `www.pep-drink.com`.

---

## Alternative: Netlify

1. [app.netlify.com](https://app.netlify.com) → **Add new site** → **Import from Git** → GitHub → `pep-online`
2. Build: **empty** command, publish directory **`.`**
3. **Domain settings** → **Add custom domain** → follow DNS instructions (CNAME `www` → `your-site.netlify.app`)

---

## After go-live checklist

- [ ] Open `https://pep-drink.com` and `https://www.pep-drink.com` (both should work)
- [ ] Open `https://pep-drink.com/for-venues.html`
- [ ] Test mobile menu and images (especially `brand/directions/provided/assets/product/bg_removed/`)
- [ ] Set `FORM_ENDPOINT` in `js/config.js` for Formspree (see main README)
- [ ] Submit a test message on **Join the pilot**

---

## Updating the site later

**Production** (pep-drink.com) only updates from **`main`**:

```bash
git checkout main
git merge dev
git push origin main
```

Day-to-day work happens on **`dev`** with `npm start` locally — see **[DEVELOPMENT.md](DEVELOPMENT.md)**.

Cloudflare Pages / Netlify redeploy **production** automatically when `main` changes. Pushes to **`dev`** can get a separate preview URL (not pep-drink.com) if branch deploys are enabled in the host dashboard.

---

## What we cannot do from code alone

- Buying or registering the domain (you did this ✓)
- Changing DNS at your registrar (you do this in their dashboard)
- Pushing to GitHub (you run `git push` from your machine)

---

## Namecheap + pep-drink.com (your setup)

Registrar: **Namecheap**. Easiest path: **Netlify** for the site + DNS records in Namecheap.

### Step 1 — Deploy on Netlify

1. [app.netlify.com](https://app.netlify.com) → **Add new site** → **Import an existing project** → **GitHub** → **pep-online**
2. Branch `main`, build command **empty**, publish directory **`.`**
3. Note your Netlify URL, e.g. `pep-online.netlify.app`

### Step 2 — Add domain in Netlify

1. **Site configuration** → **Domain management** → **Add a domain**
2. Add **`pep-drink.com`** and **`www.pep-drink.com`**
3. Netlify shows the exact DNS records — use those values in Step 3 (they may differ slightly per site)

Typical Netlify values:

| Type | Host | Value |
|------|------|--------|
| A | `@` | `75.2.60.5` |
| CNAME | `www` | `your-site-name.netlify.app` |

### Step 3 — Namecheap DNS

1. [namecheap.com](https://www.namecheap.com) → **Domain List** → **Manage** next to **pep-drink.com**
2. **Advanced DNS** tab
3. Remove old **Parking** / conflicting `A` or `CNAME` records for `@` and `www` if present
4. Add the records Netlify gave you (table above if they match)
5. **Save** — propagation often 5–30 minutes (up to 24h)

**URL Redirect (optional):** If you only use `www` on Netlify, add a Namecheap redirect:  
`@` → `https://www.pep-drink.com` (301 permanent) so `pep-drink.com` always works.

### Step 4 — HTTPS

Netlify provisions **SSL** automatically after DNS is correct. In Netlify → **Domain management**, wait until both domains show **Verified**.

### Alternative: Cloudflare Pages + Namecheap DNS

1. Deploy on **Cloudflare Pages** (Git → `pep-online`) → get `something.pages.dev`
2. In Pages → add custom domains `www.pep-drink.com` and `pep-drink.com`
3. In **Namecheap → Advanced DNS**:
   - **CNAME** `www` → `something.pages.dev` (exact hostname from Cloudflare)
   - **URL Redirect** `@` → `https://www.pep-drink.com` (301) — Namecheap cannot CNAME the apex easily
4. Or move DNS to Cloudflare (free): Namecheap → **Nameservers** → Custom → Cloudflare’s two nameservers (then Cloudflare manages everything)

---

## Quick checklist for Namecheap

- [ ] Site deployed on Netlify (or Cloudflare Pages)
- [ ] `git push` so GitHub has latest files
- [ ] DNS records added in Namecheap **Advanced DNS**
- [ ] `https://www.pep-drink.com` loads
- [ ] `https://pep-drink.com` loads (redirect or A record)
- [ ] Formspree set in `js/config.js`
