import kiln_ai.coreadd as coreadd
import kiln_studio.server as server


def test_import() -> None:
    assert server.studio_path() != ""
    assert coreadd.add(1, 1) == 2
