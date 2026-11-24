import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from parse_dump import parse_dump  # noqa: E402


def test_parse_dump_counts_copy_rows_and_columns():
    dump = """--
-- PostgreSQL database dump
--
CREATE TABLE public.users (
    id integer NOT NULL,
    name text NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id)
);

COPY public.users (id, name) FROM stdin;
1\talice
2\tbob
\\.

CREATE TABLE public.events (
    id bigint NOT NULL,
    payload jsonb
);

COPY public.events (id, payload) FROM stdin;
1\t{\"k\": 1}
\\.
"""
    meta = parse_dump(dump)

    assert sorted(meta.tables) == ["public.events", "public.users"]
    assert meta.tables["public.users"].columns == ["id", "name"]
    assert meta.tables["public.users"].rows == 2
    assert meta.tables["public.events"].columns == ["id", "payload"]
    assert meta.tables["public.events"].rows == 1
