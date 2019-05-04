#!/usr/bin/python3


class TestLib():
    def test_pytest(self):
        assert True

    def test_lidarr(self, lidarr):
        ''' See if the helper fixture works to load charm configs '''
        assert isinstance(lidarr.charm_config, dict)

    # Include tests for functions in lib_lidarr
