import imp

import mock


class TestActions():
    def test_disable_auth_action(self, lidarr, monkeypatch):
        mock_function = mock.Mock()
        monkeypatch.setattr(lidarr, 'modify_config', mock_function)
        assert mock_function.call_count == 0
        imp.load_source('disable-auth', './actions/disable-auth')
        assert mock_function.call_count == 1
