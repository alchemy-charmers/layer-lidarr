import os
import pytest
import subprocess

# Treat all tests as coroutines
pytestmark = pytest.mark.asyncio

juju_repository = os.getenv('JUJU_REPOSITORY', '.').rstrip('/')
series = ['xenial',
          'bionic',
          pytest.param('cosmic', marks=pytest.mark.xfail(reason='canary')),
          ]
sources = [('local', '{}/builds/lidarr'.format(juju_repository)),
           ('jujucharms', 'cs:~pirate-charmers/lidarr'),
           ]


# Uncomment for re-using the current model, useful for debugging functional tests
# @pytest.fixture(scope='module')
# async def model():
#     from juju.model import Model
#     model = Model()
#     await model.connect_current()
#     yield model
#     await model.disconnect()


# Custom fixtures
@pytest.fixture(params=series)
def series(request):
    return request.param


@pytest.fixture(params=sources, ids=[s[0] for s in sources])
def source(request):
    return request.param


@pytest.fixture
async def app(model, series, source):
    app_name = 'lidarr-{}-{}'.format(series, source[0])
    return await model._wait_for_new('application', app_name)


async def test_lidarr_deploy(model, series, source, request):
    # Starts a deploy for each series
    # Using subprocess b/c libjuju fails with JAAS
    # https://github.com/juju/python-libjuju/issues/221
    application_name = 'lidarr-{}-{}'.format(series, source[0])
    cmd = ['juju', 'deploy', source[1], '-m', model.info.name,
           '--series', series, application_name]
    if request.node.get_closest_marker('xfail'):
        cmd.append('--force')
    subprocess.check_call(cmd)


async def test_depoy_supporting_apps(model):
    await model.deploy('cs:~chris.sanders/sabnzbd',
                       series='xenial',
                       application_name='sabnzbd')
    await model.deploy('cs:~chris.sanders/plex',
                       series='xenial',
                       application_name='plex')


async def test_charm_upgrade(model, app, request):
    if app.name.endswith('local'):
        pytest.skip("No need to upgrade the local deploy")
    unit = app.units[0]
    await model.block_until(lambda: unit.agent_status == 'idle')
    cmd = ['juju',
           'upgrade-charm',
           '--switch={}'.format(sources[0][1]),
           '-m', model.info.name,
           app.name,
           ]
    if request.node.get_closest_marker('xfail'):
        cmd.append('--force')
    subprocess.check_call(cmd)
    await model.block_until(lambda: unit.agent_status == 'executing')


# Tests
async def test_lidarr_status(model, app):
    # Verifies status for all deployed series of the charm
    await model.block_until(lambda: app.status == 'active')
    unit = app.units[0]
    await model.block_until(lambda: unit.agent_status == 'idle')


async def test_mono_version(app, jujutools):
    unit = app.units[0]
    compare = await jujutools.compare_version('mono-runtime', '5.0.0', unit)
    assert compare == 1  # 1 means the package is newer than the compared version


async def test_disable_auth_action(app):
    unit = app.units[0]
    action = await unit.run_action('disable-auth')
    action = await action.wait()
    assert action.status == 'completed'


async def test_disable_indexers_action(app):
    unit = app.units[0]
    action = await unit.run_action('disable-indexers')
    action = await action.wait()
    assert action.status == 'completed'


async def test_enable_indexers_action(app):
    unit = app.units[0]
    action = await unit.run_action('enable-indexers')
    action = await action.wait()
    assert action.status == 'completed'


async def test_plex_status(model):
    # Verifies status for all deployed series of the charm
    plex = model.applications['plex']
    await model.block_until(lambda: plex.status == 'active')


async def test_plex_relation(app):
    await app.add_relation('plex-info', 'plex:plex-info')
    # await model.block_until(lambda: plex.status == 'maintenance')
    # await model.block_until(lambda: plex.status == 'active')


async def test_sab_status(model):
    # Verifies status for all deployed series of the charm
    sab = model.applications['sabnzbd']
    await model.block_until(lambda: sab.status == 'active')


async def test_sab_relation(app):
    await app.add_relation('usenet-downloader', 'sabnzbd:usenet-downloader')
    # await model.block_until(lambda: sab.status == 'maintenance')
    # await model.block_until(lambda: sab.status == 'active')
