import pytest
from ai_tests.support import Audit


@pytest.fixture
def audit(request):
    case = 'AI-WBF-' + request.node.path.stem.rsplit('_', 1)[-1]
    recorder = Audit(case)
    try:
        yield recorder
    finally:
        recorder.save()
