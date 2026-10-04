import sqlite3

from schemas.character import CharacterCreate
from services.character_service import CharacterService


def _character(name: str) -> CharacterCreate:
    return CharacterCreate(name=name, genre="rock", trait="bold", birthplace="London")


def test_characters_are_scoped_to_account(tmp_path):
    db = str(tmp_path / "characters.db")
    svc = CharacterService(db)
    a = svc.create_character(_character("Alpha"), 10)
    b = svc.create_character(_character("Beta"), 20)

    assert [c["id"] for c in svc.list_characters(10)] == [a["id"]]
    assert [c["id"] for c in svc.list_characters(20)] == [b["id"]]
    assert svc.owns_character(10, a["id"])
    assert not svc.owns_character(10, b["id"])


def test_account_cannot_mutate_another_accounts_character(tmp_path):
    db = str(tmp_path / "characters.db")
    svc = CharacterService(db)
    char = svc.create_character(_character("Gamma"), 10)

    assert svc.update_character(char["id"], _character("Stolen"), 20) is None
    assert svc.delete_character(char["id"], 20) is False
    assert svc.get_character(char["id"])["name"] == "Gamma"


def test_legacy_unowned_characters_are_not_exposed(tmp_path):
    db = str(tmp_path / "characters.db")
    svc = CharacterService(db)
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO characters (name, genre, trait, birthplace) VALUES (?, ?, ?, ?)",
            ("Legacy", "rock", "bold", "London"),
        )

    assert svc.list_characters(10) == []
