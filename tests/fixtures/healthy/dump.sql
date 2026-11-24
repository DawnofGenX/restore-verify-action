-- Control fixture: a healthy dump that must PASS the gate.
CREATE TABLE public.users (
    id integer NOT NULL,
    name text NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);

COPY public.users (id, name) FROM stdin;
1	alice
2	bob
\.

CREATE TABLE public.events (
    id bigint NOT NULL,
    payload jsonb
);

COPY public.events (id, payload) FROM stdin;
1	{"k": 1}
2	{"k": 2}
\.
