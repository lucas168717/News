import pytest

from newsbot import crypto


def test_roundtrip_and_password_change():
    meta, key = crypto.new_meta("correct horse battery")
    payload = crypto.encrypt(key, {"标题": "美股收涨"})
    assert crypto.decrypt(key, payload) == {"标题": "美股收涨"}
    assert crypto.key_for_meta("correct horse battery", meta) == key
    assert crypto.key_for_meta("another password", meta) is None
    with pytest.raises(ValueError):
        crypto.decrypt(crypto.derive_key("x", b"0" * 16, 1000), payload)
