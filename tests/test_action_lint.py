"""On-screen action lint (action-polish) and its Markdown rendering."""

from conftest import load_script

from app.pipeline.screenplay import render_md

al = load_script("action-polish/_action_lint.py")


def scene(beats, blocking="Mẹ ngồi bên bàn trà, con đứng ở cửa"):
    sc = {"id": "SC1", "cast": {"char_01": "char_01_o1", "char_02": "char_02_o1"}, "beats": beats}
    if blocking:
        sc["blocking"] = blocking
    return {"episode": 1, "characters": {"char_01": {"name": "Mẹ"}, "char_02": {"name": "Con"}}, "scenes": [sc]}


def beat(s, e, chars, acting=None, line=None, who="char_01"):
    b = {"start_sec": s, "end_sec": e, "shot_size": "CU", "characters": chars, "action": "Bàn trà"}
    if acting is not None:
        b["acting"] = acting
    if line:
        b["dialogue"] = [{"character": who, "line": line, "voiceover": False}]
    return b


def flags(ep):
    items, cov = al.check_episode(ep)
    return [(it.get("beat"), it.get("character"), i) for it in items for i in it["issues"]], cov


def test_listener_without_acting_is_missing():
    ep = scene([beat(0, 2, ["char_01", "char_02"], [{"character": "char_01", "does": "tay run run rót trà",
                                                       "face": "cười gượng", "holds": "ấm trà"}],
                     line="Con không sao đâu.")])
    found, cov = flags(ep)
    assert found == [(0, "char_02", "missing")]
    assert cov == {"beats": 1, "covered": 0, "pct": 0}


def test_voice_only_characters_and_no_blocking():
    ep = scene([beat(0, 2, ["char_01", "voice_loa"], [{"character": "char_01", "does": "đặt chén xuống khay", "face": "", "holds": ""}]),
                beat(2, 4, ["char_02"], [{"character": "char_02", "does": "cởi giày ở bậc cửa", "face": "", "holds": ""}])],
               blocking="")
    found, _ = flags(ep)
    assert found == [(None, None, "no_blocking")]


def test_held_object_must_be_put_down():
    a1 = [{"character": "char_01", "does": "nhấc ấm trà", "face": "", "holds": "ấm trà (prop_04)"}]
    gone = [{"character": "char_01", "does": "khoanh tay trước ngực", "face": "", "holds": ""}]
    put = [{"character": "char_01", "does": "đặt ấm xuống khay, khoanh tay", "face": "", "holds": ""}]
    assert ("prop_vanish" in {f[2] for f in flags(scene([beat(0, 2, ["char_01"], a1), beat(2, 4, ["char_01"], gone)]))[0]})
    assert flags(scene([beat(0, 2, ["char_01"], a1), beat(2, 4, ["char_01"], put)]))[0] == []


def test_vague_abstract_and_overloaded():
    ep = scene([beat(0, 1.5, ["char_01"], [{"character": "char_01", "does": "nhìn con", "face": ""}]),
                beat(1.5, 3, ["char_01"], [{"character": "char_01", "does": "buồn bã", "face": ""}]),
                beat(3, 4.5, ["char_01"], [{"character": "char_01", "does": "đứng dậy, rót trà, lau bàn, mở cửa", "face": ""}])])
    assert {(b, i) for b, _, i in flags(ep)[0]} == {(0, "vague"), (1, "abstract"), (2, "overloaded")}


def test_markdown_shows_acting_and_blocking():
    ep = scene([beat(0, 2, ["char_01"], [{"character": "char_01", "does": "tay run run rót trà",
                                          "face": "mím môi", "holds": "ấm trà"}], line="Con không sao đâu.")])
    md = render_md(ep)
    assert "Vị trí: Mẹ ngồi bên bàn trà" in md
    assert "Bàn trà<br>**Mẹ**: tay run run rót trà; mặt: mím môi; cầm: ấm trà |" in md
