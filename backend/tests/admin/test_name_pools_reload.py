from services.admin_service import AdminService, AdminActionRepository
from backend.utils import name_generator


def test_add_name_updates_pools(tmp_path, monkeypatch):
    # Preserve originals to restore after test
    orig_dir = name_generator.DATA_DIR
    orig_male = name_generator.MALE_FIRST_NAMES.copy()
    orig_female = name_generator.FEMALE_FIRST_NAMES.copy()
    orig_last = name_generator.LAST_NAMES.copy()

    try:
        # Setup temporary data files
        (tmp_path / "male_names.csv").write_text("John\n")
        (tmp_path / "female_names.csv").write_text("Jane\n")
        (tmp_path / "surnames.csv").write_text("Doe\n")

        monkeypatch.setattr(name_generator, "DATA_DIR", tmp_path)
        name_generator.reload_name_pools()

        svc = AdminService(AdminActionRepository(db_path=":memory:"))

        svc.add_name_to_pool("male", "Alex")
        assert "Alex" in name_generator.MALE_FIRST_NAMES

        svc.add_name_to_pool(None, "Smith")
        assert "Smith" in name_generator.LAST_NAMES
    finally:
        # Restore global state
        name_generator.DATA_DIR = orig_dir
        name_generator.MALE_FIRST_NAMES = orig_male
        name_generator.FEMALE_FIRST_NAMES = orig_female
        name_generator.LAST_NAMES = orig_last
