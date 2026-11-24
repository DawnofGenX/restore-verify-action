-- PicPeak issue #2482 shape: a restore error in the middle of a COPY.
-- A naive `psql -f` keeps going and exits 0; the gate must fail and report
-- the duplicate-key error plus a row-count mismatch.
CREATE TABLE public.users (
    id integer NOT NULL,
    name text NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);

COPY public.users (id, name) FROM stdin;
1	alice
1	alice
\.
