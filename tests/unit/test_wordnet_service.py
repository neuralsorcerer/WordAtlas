from wordatlas.services.wordnet_service import cache_info, clear_caches, synsets_for


def test_cache_info_and_clear():
    synsets_for("happy")
    synsets_for("run")
    info_before = cache_info()
    assert info_before["synsets_for"]["currsize"] >= 1

    clear_caches()
    info_after = cache_info()
    assert info_after["synsets_for"]["currsize"] == 0
