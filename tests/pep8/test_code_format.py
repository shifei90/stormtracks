from glob import glob
import pep8


class TestCodeFormat:
    def __init__(self):
        # ignore E501: line too long.
        self.pep8style = pep8.StyleGuide(ignore='E501', quiet=True)

    def _test_conformance_in_files(self, filenames):
        assert len(filenames) != 0
        for filename in filenames:
            print(filename)
            result = self.pep8style.check_files([filename])
            assert result.total_errors == 0, "Found code style errors (and warnings)."

    def test_1_stormtracks_pep8_conformance(self):
        """Test that stormtracks module conforms to PEP8. (Bar E501)"""
        filenames = glob('../stormtracks/*.py')
        self._test_conformance_in_files(filenames)

    def test_2_demo_pep8_conformance(self):
        """Test that demo module conforms to PEP8. (Bar E501)"""
        filenames = glob('../stormtracks/demo/*.py')
        self._test_conformance_in_files(filenames)

    def test_3_pyro_pep8_conformance(self):
        """Test that pyro module conforms to PEP8. (Bar E501)"""
        filenames = glob('../stormtracks/pyro_cluster/*.py')
        self._test_conformance_in_files(filenames)

    def test_4_settings_pep8_conformance(self):
        """Test that settings module conforms to PEP8. (Bar E501)"""
        filenames = glob('../stormtracks/settings/*.py')
        self._test_conformance_in_files(filenames)

    def test_5_utils_pep8_conformance(self):
        """Test that utils module conforms to PEP8. (Bar E501)"""
        filenames = glob('../stormtracks/utils/*.py')
        self._test_conformance_in_files(filenames)

    def test_6_testts_pep8_conformance(self):
        """Test that all tests conforms to PEP8. (Bar E501)"""
        filenames = glob('functional/*.py')
        self._test_conformance_in_files(filenames)
        filenames = glob('bugs/*.py')
        self._test_conformance_in_files(filenames)
        filenames = glob('interactive/*.py')
        self._test_conformance_in_files(filenames)