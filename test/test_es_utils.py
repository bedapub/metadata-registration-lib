from metadata_registration_lib.es_utils import get_nb_pages


def test_get_nb_pages():
    assert get_nb_pages(nb_hits=12, es_size=5) == 3
    assert get_nb_pages(nb_hits=12, es_size=20) == 1
    assert get_nb_pages(nb_hits=20, es_size=20) == 1
    assert get_nb_pages(nb_hits=20, es_size=21) == 1
    assert get_nb_pages(nb_hits=21, es_size=20) == 2
