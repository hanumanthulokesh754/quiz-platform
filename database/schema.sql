-- Quiz Management & Online Assessment Platform
-- PostgreSQL schema (run this in the Supabase SQL editor)

create extension if not exists "pgcrypto";

-- ============================================================
-- USERS
-- ============================================================
create table if not exists users (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    email text not null unique,
    password text not null,             -- bcrypt hash
    role text not null check (role in ('ADMIN', 'STUDENT')) default 'STUDENT',
    status text not null check (status in ('ACTIVE', 'INACTIVE')) default 'ACTIVE',
    created_at timestamptz not null default now()
);

-- ============================================================
-- CATEGORIES
-- ============================================================
create table if not exists categories (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    description text,
    created_at timestamptz not null default now()
);

-- ============================================================
-- QUIZZES
-- ============================================================
create table if not exists quizzes (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    description text,
    category_id uuid references categories(id) on delete set null,
    difficulty text check (difficulty in ('EASY', 'INTERMEDIATE', 'HARD')),
    duration_minutes integer not null,          -- quiz duration
    passing_score numeric not null default 60,  -- percentage
    max_attempts integer not null default 1,
    status text not null check (status in ('DRAFT', 'PUBLISHED', 'UNPUBLISHED')) default 'DRAFT',
    thumbnail_url text,
    negative_marks numeric not null default 0,       -- marks deducted per wrong answer (0 = disabled)
    randomize_questions boolean not null default false,
    randomize_options boolean not null default false,
    created_by uuid references users(id),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- ============================================================
-- QUESTIONS
-- ============================================================
create table if not exists questions (
    id uuid primary key default gen_random_uuid(),
    quiz_id uuid not null references quizzes(id) on delete cascade,
    question_text text not null,
    marks numeric not null default 1,
    explanation text,
    difficulty text check (difficulty in ('EASY', 'INTERMEDIATE', 'HARD')),
    created_at timestamptz not null default now()
);

-- ============================================================
-- OPTIONS
-- ============================================================
create table if not exists options (
    id uuid primary key default gen_random_uuid(),
    question_id uuid not null references questions(id) on delete cascade,
    option_text text not null,
    is_correct boolean not null default false
);

-- ============================================================
-- ATTEMPTS
-- ============================================================
create table if not exists attempts (
    id uuid primary key default gen_random_uuid(),
    quiz_id uuid not null references quizzes(id) on delete cascade,
    user_id uuid not null references users(id) on delete cascade,
    score numeric,
    percentage numeric,
    correct_answers integer default 0,
    incorrect_answers integer default 0,
    unanswered integer default 0,
    time_taken_seconds integer,
    status text not null check (status in ('IN_PROGRESS', 'COMPLETED', 'EXPIRED')) default 'IN_PROGRESS',
    started_at timestamptz not null default now(),
    completed_at timestamptz
);

-- ============================================================
-- ANSWERS
-- ============================================================
create table if not exists answers (
    id uuid primary key default gen_random_uuid(),
    attempt_id uuid not null references attempts(id) on delete cascade,
    question_id uuid not null references questions(id) on delete cascade,
    selected_option_id uuid references options(id),
    is_correct boolean
);

-- ============================================================
-- Helpful indexes
-- ============================================================
create index if not exists idx_quizzes_status on quizzes(status);
create index if not exists idx_quizzes_category on quizzes(category_id);
create index if not exists idx_questions_quiz on questions(quiz_id);
create index if not exists idx_options_question on options(question_id);
create index if not exists idx_attempts_user on attempts(user_id);
create index if not exists idx_attempts_quiz on attempts(quiz_id);
create index if not exists idx_answers_attempt on answers(attempt_id);

-- ============================================================
-- Migration for databases created before negative marking /
-- randomization existed — safe to run even if columns already exist.
-- ============================================================
alter table quizzes add column if not exists negative_marks numeric not null default 0;
alter table quizzes add column if not exists randomize_questions boolean not null default false;
alter table quizzes add column if not exists randomize_options boolean not null default false;

-- Enforce "max attempts" and "one selected option per answer" at the app layer;
-- Supabase RLS policies should be added separately if using client-side Supabase access.
-- This project accesses Supabase via the service key from the Flask backend only,
-- so table-level RLS can stay locked down (deny-all) for anon/public roles.
