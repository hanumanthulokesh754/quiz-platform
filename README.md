# Quiz Management & Online Assessment Platform

Full-stack quiz platform: Flask + Supabase (Postgres) backend, vanilla HTML/CSS/JS frontend.
Two roles — **Admin** (manages quizzes, questions, categories, students, results) and
**Student** (browses, attempts, and reviews quizzes).

## Project structure

```
quiz-platform/
├── backend/              Flask API
│   ├── app.py            App entrypoint — registers all blueprints
│   ├── config.py         Env-driven config
│   ├── extensions.py     Supabase client
│   ├── create_admin.py   CLI to create the first Admin account
│   ├── routes/           One blueprint per resource (auth, users, quizzes, ...)
│   └── utils/            JWT/role decorators + server-side scoring
├── database/
│   └── schema.sql        Run this in the Supabase SQL editor
└── frontend/              Vanilla HTML/CSS/JS, no build step
    ├── auth/              Login / register
    ├── student/           Dashboard, quiz browsing, attempt flow, results, leaderboard
    ├── admin/             Dashboard, quiz/question/category/user management, results
    └── assets/            Shared css/js (api.js, layout.js, style.css)
```

## Setup

### 1. Database (Supabase)
1. Create a project at supabase.com.
2. Open the SQL editor and run `database/schema.sql`.
3. In Project Settings > API, copy the **Project URL** and the **service_role key**
   (not the anon key — the backend needs full access and enforces auth itself).
4. Because the backend uses the service-role key exclusively, you can leave RLS
   enabled with no public policies (deny-all for anon/authenticated).

### 2. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # then fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, JWT_SECRET
python create_admin.py                                # create your first Admin login
python app.py                                          # runs on http://localhost:5000
```

### 3. Frontend
No build step — it's static HTML/CSS/JS. Serve the `frontend/` folder with any
static server, e.g.:
```bash
cd frontend
python -m http.server 5500
```
Then open `http://localhost:5500`. `assets/js/api.js` points at
`http://localhost:5000/api` — update `API_BASE` there (and `FRONTEND_ORIGIN`
in the backend `.env`) if you serve from different ports/hosts.

Students self-register from the login page. The Admin account is created
via `create_admin.py` — there's deliberately no public admin signup.

## What's scaffolded vs. left as TODO

**Working end-to-end:** registration/login (JWT), admin quiz/question/category
CRUD + publish, student quiz browsing, timed attempts with server-validated
scoring and expiry, results with answer review, attempt history, leaderboard,
admin results/analytics dashboard, user activate/deactivate.

**Stubbed / left for you to extend:**
- `forgot-password` / `reset-password` — endpoints exist but don't send email yet.
- Rate limiting, security headers beyond CORS — add `flask-limiter` /
  `flask-talisman` before deploying publicly.
- Remaining advanced features from the spec (quiz scheduling, certificates,
  email notifications, CSV/Excel question import, dark mode) — not built yet;
  the schema and scoring util are structured so they can be added incrementally.
- The `answers` review join in `routes/attempts.py` (`get_attempt`) assumes a
  Supabase FK constraint name — check it against your actual schema if that
  query errors.

### Negative marking & randomization (implemented)
- Set per-quiz in the admin "new quiz" form: a negative-marks value (marks
  deducted per wrong answer — 0 disables it) and two checkboxes to randomize
  question order and/or option order per attempt.
- Scoring (`utils/scoring.py`) deducts `negative_marks` for each wrong answer
  and clamps the total at zero — unanswered questions are never penalized.
- Shuffling (`utils/randomization.py`) is seeded from the attempt's own id, so
  a page refresh or a resumed in-progress attempt always sees the same order
  — it doesn't re-shuffle on every request, and two different students (or
  two different attempts) get independent orders.
- If you already ran the original `schema.sql`, re-run the "Migration"
  section near the bottom of that file to add the three new `quizzes`
  columns (`negative_marks`, `randomize_questions`, `randomize_options`).

## Deploying
Matches your usual setup: backend to Render (or similar — set the same env
vars from `.env.example`), frontend to Vercel as a static site (update
`API_BASE` in `api.js` to the deployed backend URL first).
