-- =====================================================================
-- AWTRIX TC001 -- Widget-Snapshot (Supabase)
-- ---------------------------------------------------------------------
-- Eine Zeile JSON, die der GitHub-Actions-Cron (main.py -> sources.set_snapshot)
-- bei jedem Lauf schreibt und die native iOS-WidgetKit-App (ios/) per
-- anon/publishable Key liest.
--
-- EINMALIG im Supabase SQL-Editor ausfuehren. Danach im markierten INSERT
-- weiter unten den REVENUE_TOKEN eintragen (derselbe Wert wie das GitHub-Secret
-- REVENUE_TOKEN), sonst werden Schreibzugriffe abgelehnt.
-- =====================================================================

-- 1) Einzeilige Snapshot-Tabelle (id ist fix 1) --------------------------
create table if not exists public.awtrix_snapshot (
  id          int primary key default 1,
  data        jsonb       not null default '{}'::jsonb,
  updated_at  timestamptz not null default now(),
  constraint awtrix_snapshot_singleton check (id = 1)
);

insert into public.awtrix_snapshot (id, data)
values (1, '{}'::jsonb)
on conflict (id) do nothing;

-- 2) Schreib-Token (privat) ---------------------------------------------
create table if not exists public.awtrix_widget_secret (
  name  text primary key,
  value text not null
);

-- >>> EINMALIG ausfuehren und <DEIN_REVENUE_TOKEN> ersetzen: <<<
-- insert into public.awtrix_widget_secret (name, value)
--   values ('write_token', '<DEIN_REVENUE_TOKEN>')
--   on conflict (name) do update set value = excluded.value;

-- 3) RLS an, aber KEINE Policies -> anon/authenticated kommen NICHT direkt
--    an die Tabellen. Zugriff laeuft nur ueber die SECURITY-DEFINER-Funktionen.
alter table public.awtrix_snapshot      enable row level security;
alter table public.awtrix_widget_secret enable row level security;

-- 4) Schreiben (token-geschuetzt) ---------------------------------------
create or replace function public.awtrix_set_snapshot(p_data jsonb, p_token text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if p_token is null or p_token <> (
       select value from public.awtrix_widget_secret where name = 'write_token'
     ) then
    raise exception 'invalid write token';
  end if;
  update public.awtrix_snapshot
     set data = p_data, updated_at = now()
   where id = 1;
end;
$$;

-- 5) Lesen (oeffentlich; anon-Key genuegt) ------------------------------
--    Haengt updated_at als ISO-8601 mit ins JSON, damit das Widget die
--    Aktualitaet anzeigen kann.
create or replace function public.awtrix_get_snapshot()
returns jsonb
language sql
security definer
set search_path = public
stable
as $$
  select jsonb_set(
           data,
           '{updated_at}',
           to_jsonb(to_char(updated_at at time zone 'UTC',
                            'YYYY-MM-DD"T"HH24:MI:SS"Z"'))
         )
    from public.awtrix_snapshot
   where id = 1;
$$;

-- 6) Ausfuehrrechte ------------------------------------------------------
revoke all on function public.awtrix_set_snapshot(jsonb, text) from public;
revoke all on function public.awtrix_get_snapshot()            from public;
grant execute on function public.awtrix_set_snapshot(jsonb, text) to anon, authenticated;
grant execute on function public.awtrix_get_snapshot()            to anon, authenticated;
