from django_mock_queries.mocks import monkey_patch_test_db

from config.settings.local import *

monkey_patch_test_db()