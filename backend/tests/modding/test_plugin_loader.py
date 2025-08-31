from backend.modding.loader import PluginLoader


def _create_plugin(tmp_path, monkeypatch, extra_code: str = ""):
    plugin_code = (
        "from backend.modding.interfaces import PluginMeta\n"
        "class Sample:\n"
        "    meta = PluginMeta(name='sample', version='1.0', author='tester')\n"
        "    activated = False\n"
        "    deactivated = False\n"
        "    def activate(self):\n"
        "        self.activated = True\n"
        "    def deactivate(self):\n"
        "        self.deactivated = True\n"
        f"{extra_code}\n"
        "plugin = Sample()\n"
    )
    mod = tmp_path / "myplugin.py"
    mod.write_text(plugin_code)
    monkeypatch.syspath_prepend(str(tmp_path))


def test_plugin_registration_and_enable(tmp_path, monkeypatch):
    _create_plugin(tmp_path, monkeypatch)

    loader = PluginLoader()
    loader.load_from_modules(["myplugin"])
    assert "sample" in loader.plugins
    # plugin should not be enabled until explicitly enabled
    assert loader.registry["sample"].enabled is False
    loader.enable("sample")
    assert loader.registry["sample"].enabled is True
    assert loader.plugins["sample"].activated is True


def test_plugin_disable(tmp_path, monkeypatch):
    _create_plugin(tmp_path, monkeypatch)

    loader = PluginLoader()
    loader.load_from_modules(["myplugin"])
    loader.enable("sample")
    loader.disable("sample")
    assert loader.registry["sample"].enabled is False
    assert loader.plugins["sample"].deactivated is True
