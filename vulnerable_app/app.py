"""
Vulnerable demo app, DO NOT DEPLOY. Built as a target for the vuln-hunter agents.

A tiny "employee portal" with 6 classic vulnerability classes baked in
(7 instances total). The hunter agent's job is to find them all;
the fixer agent's job is to patch them without breaking the app.
"""

import hashlib
import pickle
import subprocess

# VULN 1: hardcoded credential
API_KEY = "sk-live-9f3k2m7q1x"

# "password" stored as unsalted MD5
USERS = {"admin": "5f4dcc3b5aa765d61d8327deb882cf99"}


def db_execute(query):
    # Stub, the agents analyze how queries are *built*, not the DB itself.
    return f"[db] {query}"


def login(username, password):
    # VULN 2: SQL injection via f-string interpolation
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    return db_execute(query)


def search_users(term):
    # VULN 2 (again): SQL injection via string concatenation, a second
    # instance for the hunter to catch (tests thoroughness, not just luck)
    query = "SELECT * FROM users WHERE name LIKE '%" + term + "%'"
    return db_execute(query)


def verify_password(username, password):
    # VULN 3: weak password storage, unsalted MD5, crackable in seconds
    return hashlib.md5(password.encode()).hexdigest() == USERS.get(username)


def run_report(report_name):
    # VULN 4: command injection, user input straight into a shell command
    result = subprocess.run(
        f"generate_report --name {report_name}",
        shell=True, capture_output=True, text=True,
    )
    return result.stdout


def load_session(data):
    # VULN 5: insecure deserialization, untrusted pickle payload
    return pickle.loads(data)


def render_greeting(name):
    # VULN 6: reflected XSS, unescaped user input in HTML output
    return f"<h1>Welcome back, {name}!</h1>"


if __name__ == "__main__":
    print(login("admin", "password"))
    print(render_greeting("Ada"))
