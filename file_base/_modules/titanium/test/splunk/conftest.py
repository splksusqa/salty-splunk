import pytest
from titanium import installer
from titanium.splunk import get_splunk


def pytest_addoption(parser):
    parser.addoption(
        "--splunk-home", default="/opt/splunk",
        dest="splunk_home", help="where to install splunk")
    parser.addoption(
        "--skip-install-splunk", action='store_true',
        dest='skip_install_splunk',
        help="add this option if splunk is ready to be tested")
    parser.addoption(
        "--pkg-url", dest="pkg_url",
        help="url to the package for testing")
    parser.addoption(
        "--license-path", dest="license_path",
        help="path to the license for testing")
    parser.addoption(
        "--no-teardown", dest="no_teardown", action="store_true",
        help="do not teardown splunk after testing")


@pytest.fixture(scope='session')
def install(request):
    config = request.config

    if not config.getoption('--skip-install-splunk'):
        my_installer = installer.InstallerFactory.create_installer(
            config.getoption('--pkg-url'), 'splunk',
            config.getoption('--splunk-home'))
        yield my_installer.install()
    else:
        yield None

    if not config.getoption('--no-teardown'):
        my_installer.uninstall()


@pytest.fixture(scope='function')
def splunk(request):
    config = request.config
    splunk = get_splunk(config.getoption('--splunk-home'))
    yield splunk
    if not splunk.is_running():
        splunk.start()


@pytest.fixture(scope='function')
def license(request):
    config = request.config
    yield config.getoption('--license-path')
