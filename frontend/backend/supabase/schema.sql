-- Reference schema for the Supabase project. The backend creates these tables
-- itself on startup (db.init), so running this is optional. Useful if you want
-- Lovable's Supabase integration to see the tables before the backend has run.

create table if not exists prompts (
  id serial primary key,
  text text not null,
  source text not null,
  created_at timestamptz default now()
);
create table if not exists drafts (
  prompt_id integer not null,
  idx integer not null,
  text text not null,
  final_answer text,
  features text not null,
  primary key (prompt_id, idx)
);
create table if not exists selections (
  id serial primary key,
  prompt_id integer not null,
  profile_id text not null,
  chosen integer not null,
  margins text not null,
  probs text not null,
  ask_first integer not null,
  seed integer not null default 0,
  profile_snapshot text not null,
  created_at timestamptz default now()
);
create table if not exists feedback (
  id serial primary key,
  prompt_id integer not null,
  profile_id text not null,
  draft_idx integer not null,
  accepted integer not null,
  features text not null,
  created_at timestamptz default now()
);
create table if not exists profiles (
  id text primary key,
  data text not null
);

-- The backend connects with the database password (service role), so RLS is
-- not required for it. If you expose these tables to the browser through
-- Lovable's Supabase client later, enable RLS first:
-- alter table prompts enable row level security;  (and the rest)
