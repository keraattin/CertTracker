#!/usr/bin/env python3


# Libraries
##############################################################################
import json
import os
import re

import pytest

dukpy = pytest.importorskip("dukpy")
##############################################################################


# Values
##############################################################################
SITE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "site"
)
JS = os.path.join(SITE, "js")

# Enough of a browser for the scripts to load and for the helpers to be
# handed something element shaped. They are never exercised against a real
# document here; the point is to catch code that does not run at all.
DOM_STUB = """
function __element(){
  return {
    textContent: "", title: "", className: "", hidden: false,
    children: [],
    appendChild: function(child){ this.children.push(child); }
  };
}
var document = {
  createElement: function(){ return __element(); },
  getElementById: function(){ return __element(); },
  getElementsByClassName: function(){ return [__element()]; }
};
function fetch(){ throw new Error("not exercised"); }
var Swal = { fire: function(){} };
function $(){ return { modal: function(){} }; }
"""


def read(name):
    with open(os.path.join(JS, name), encoding="utf-8") as handle:
        return handle.read()


def read_page(name):
    with open(os.path.join(SITE, name), encoding="utf-8") as handle:
        return handle.read()


SCRIPTS = sorted(
    name for name in os.listdir(JS) if name.endswith(".js")
)
##############################################################################


# Loading
##############################################################################
@pytest.mark.parametrize("name", SCRIPTS)
def test_script_parses_and_loads(name):
    # A syntax error here would only show up as a blank page in a browser.
    dukpy.evaljs(DOM_STUB + read(name) + "\n1")
##############################################################################


# Datetime Helpers
##############################################################################
DATETIME_JS = None


def run_datetime(expression):
    global DATETIME_JS
    if DATETIME_JS is None:
        DATETIME_JS = DOM_STUB + read("datetime.js")
    return dukpy.evaljs(DATETIME_JS + expression)


# Exactly how Flask serializes a datetime, which is what the frontend has
# to read.
API_DATE = "Wed, 30 Sep 2026 23:59:59 GMT"


def test_api_date_format_is_parseable():
    epoch = run_datetime(
        "var d = new Date(" + json.dumps(API_DATE) + ");"
        "isNaN(d.getTime()) ? null : d.getTime()"
    )
    assert epoch == 1790812799000


def test_local_time_is_not_the_raw_value():
    rendered = run_datetime("toLocalTime(" + json.dumps(API_DATE) + ")")
    assert rendered != API_DATE
    assert "GMT" not in rendered


@pytest.mark.parametrize("value", [None, ""])
def test_missing_datetimes_render_as_a_dash(value):
    # Rows written before a column existed carry nulls.
    assert run_datetime("toLocalTime(" + json.dumps(value) + ")") == "-"


def test_unparseable_values_are_left_alone():
    assert run_datetime("toLocalTime('not a date')") == "not a date"


def test_write_local_time_keeps_the_original_in_the_title():
    text, title = run_datetime(
        "var e = __element();"
        "writeLocalTime(e, " + json.dumps(API_DATE) + ");"
        "[e.textContent, e.title]"
    )
    assert title == API_DATE
    assert text != API_DATE
##############################################################################


# Wiring
##############################################################################
def test_no_datetime_is_printed_raw():
    # Every date has to go through the helpers, otherwise it reaches the
    # page as UTC and reads as the wrong day.
    pattern = re.compile(
        r"\.textContent\s*=\s*\w+\.(not_before|not_after|last_update|last_check)\b"
    )
    offenders = [
        (name, match.group(0))
        for name in SCRIPTS
        for match in pattern.finditer(read(name))
    ]
    assert offenders == []


@pytest.mark.parametrize("page", ["index.html", "certificates.html"])
def test_datetime_script_is_loaded_first(page):
    scripts = re.findall(r'<script src="js/([a-z]+\.js)"></script>', read_page(page))
    assert "datetime.js" in scripts
    others = [name for name in scripts if name != "datetime.js"]
    assert scripts.index("datetime.js") < min(scripts.index(n) for n in others)


def test_the_api_is_called_on_the_same_origin():
    # nginx proxies /api to the api service. An absolute address here
    # would pin the deployment to whatever host was hardcoded, which is
    # exactly what this replaced.
    offenders = [
        (name, match.group(0))
        for name in SCRIPTS
        for match in re.finditer(r"https?://[^\"'\s]+", read(name))
    ]
    assert offenders == []


def test_every_api_call_is_a_relative_path():
    calls = [
        match.group(1)
        for name in SCRIPTS
        for match in re.finditer(r"""["'](/api[^"']*)["']""", read(name))
    ]
    assert calls, "the frontend should call the api somewhere"
    assert all(call.startswith("/api") for call in calls)


def test_nginx_serves_the_api_under_the_same_host():
    conf = os.path.join(os.path.dirname(SITE), "nginx.conf")
    with open(conf, encoding="utf-8") as handle:
        text = handle.read()
    assert "location /api" in text
    assert "proxy_pass http://api:5000" in text
    # The health endpoint sits outside /api and needs its own rule.
    assert "location /health" in text


def test_every_element_id_the_dashboard_uses_exists():
    page = read_page("index.html")
    wanted = set(re.findall(
        r"getElementById\(['\"]([A-Za-z]+)['\"]\)", read("main.js")
    ))
    missing = [name for name in wanted if 'id="' + name + '"' not in page]
    assert missing == []


def test_every_element_id_the_details_modal_uses_exists():
    page = read_page("certificates.html")
    wanted = set(re.findall(
        r"getElementById\(['\"](details[A-Za-z]+)['\"]\)", read("certificates.js")
    ))
    assert wanted, "the details modal should reference some fields"
    missing = [name for name in wanted if 'id="' + name + '"' not in page]
    assert missing == []
##############################################################################
