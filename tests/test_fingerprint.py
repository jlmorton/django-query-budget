from django_query_budget.fingerprint import fingerprint_sql

def test_replaces_integer_literals():
    assert fingerprint_sql('SELECT * FROM "users" WHERE "id" = 42') == 'select * from "users" where "id" = ?'

def test_replaces_string_literals_single_quotes():
    assert fingerprint_sql("SELECT * FROM users WHERE name = 'alice'") == "select * from users where name = ?"

def test_replaces_string_literals_double_quotes_values():
    assert fingerprint_sql('''SELECT * FROM "users" WHERE "name" = 'bob' ''') == 'select * from "users" where "name" = ?'

def test_replaces_multiple_literals():
    assert fingerprint_sql("SELECT * FROM t WHERE a = 1 AND b = 'foo' AND c = 3.14") == "select * from t where a = ? and b = ? and c = ?"

def test_collapses_whitespace():
    assert fingerprint_sql("SELECT  *   FROM    users   WHERE   id = 1") == "select * from users where id = ?"

def test_in_list():
    assert fingerprint_sql("SELECT * FROM t WHERE id IN (1, 2, 3, 4, 5)") == "select * from t where id in (?)"

def test_preserves_structure():
    assert fingerprint_sql('SELECT "a", "b" FROM "t" WHERE "x" = 1 ORDER BY "a" LIMIT 10') == 'select "a", "b" from "t" where "x" = ? order by "a" limit ?'

def test_escaped_single_quotes():
    assert fingerprint_sql("SELECT * FROM t WHERE name = 'it''s'") == "select * from t where name = ?"

def test_no_lowercase_option():
    assert fingerprint_sql('SELECT * FROM "Users" WHERE "Id" = 42', lowercase=False) == 'SELECT * FROM "Users" WHERE "Id" = ?'

def test_empty_string():
    assert fingerprint_sql("") == ""

def test_no_literals():
    assert fingerprint_sql("SELECT * FROM users") == "select * from users"
