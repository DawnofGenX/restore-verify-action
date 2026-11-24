-- PostgreSQL 17 dump fixture (glou-server issue #92 shape)
-- SET transaction_timeout is a PG17+ GUC; PG16 aborts the restore on it.
SET transaction_timeout = '5s';

CREATE TABLE public.users (
    id integer NOT NULL,
    name text NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);

COPY public.users (id, name) FROM stdin;
1	alice
\.
