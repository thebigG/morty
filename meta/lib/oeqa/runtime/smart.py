import unittest
import re
import oe
import subprocess
from oeqa.oetest import oeRuntimeTest, skipModule
from oeqa.utils.decorators import *
from oeqa.utils.httpserver import HTTPService

def setUpModule():
    if not oeRuntimeTest.hasFeature("package-management"):
        skipModule("Image doesn't have package management feature")
    if not oeRuntimeTest.hasPackage("smartpm"):
        skipModule("Image doesn't have smart installed")
    if "package_rpm" != oeRuntimeTest.tc.d.getVar("PACKAGE_CLASSES", True).split()[0]:
        skipModule("Rpm is not the primary package manager")

class SmartTest(oeRuntimeTest):

    @skipUnlessPassed('test_smart_help')
    def smart(self, command, expected = 0):
        command = 'smart %s' % command
        status, output = self.target.run(command, 1500)
        message = os.linesep.join([command, output])
        self.assertEqual(status, expected, message)
        self.assertFalse("Cannot allocate memory" in output, message)
        return output

class SmartBasicTest(SmartTest):

    @testcase(716)
    @skipUnlessPassed('test_ssh')
    def test_smart_help(self):
        self.smart('--help')

    @testcase(968)
    def test_smart_version(self):
        self.smart('--version')

    @testcase(721)
    def test_smart_info(self):
        self.smart('info python-smartpm')

    @testcase(421)
    def test_smart_query(self):
        self.smart('query python-smartpm')

    @testcase(720)
    def test_smart_search(self):
        self.smart('search python-smartpm')

    @testcase(722)
    def test_smart_stats(self):
        self.smart('stats')

class SmartRepoTest(SmartTest):

    @classmethod
    def create_index(self, arg):
        index_cmd = arg
        try:
            bb.note("Executing '%s' ..." % index_cmd)
            result = subprocess.check_output(index_cmd, stderr=subprocess.STDOUT, shell=True).decode("utf-8")
        except subprocess.CalledProcessError as e:
            return("Index creation command '%s' failed with return code %d:\n%s" %
                    (e.cmd, e.returncode, e.output.decode("utf-8")))
        if result:
            bb.note(result)
        return None

    @classmethod
    def setUpClass(self):
        self.repolist = []

        # Index RPMs
        rpm_createrepo = bb.utils.which(os.getenv('PATH'), "createrepo")
        index_cmds = []
        rpm_dirs_found = False
        archs = (oeRuntimeTest.tc.d.getVar('ALL_MULTILIB_PACKAGE_ARCHS', True) or "").replace('-', '_').split()
        for arch in archs:
            rpm_dir = os.path.join(oeRuntimeTest.tc.d.getVar('DEPLOY_DIR_RPM', True), arch)
            idx_path = os.path.join(oeRuntimeTest.tc.d.getVar('WORKDIR', True), 'rpm', arch)
            db_path = os.path.join(oeRuntimeTest.tc.d.getVar('WORKDIR', True), 'rpmdb', arch)
            if not os.path.isdir(rpm_dir):
                continue
            if os.path.exists(db_path):
                bb.utils.remove(dbpath, True)
            lockfilename = oeRuntimeTest.tc.d.getVar('DEPLOY_DIR_RPM', True) + "/rpm.lock"
            lf = bb.utils.lockfile(lockfilename, False)
            oe.path.copyhardlinktree(rpm_dir, idx_path)
            # Full indexes overload a 256MB image so reduce the number of rpms
            # in the feed. Filter to p* since we use the psplash packages and
            # this leaves some allarch and machine arch packages too.
            bb.utils.remove(idx_path + "*/[a-oq-z]*.rpm")
            bb.utils.unlockfile(lf)
            index_cmds.append("%s --dbpath %s --update -q %s" % (rpm_createrepo, db_path, idx_path))
            rpm_dirs_found = True
         # Create repodata??
        result = oe.utils.multiprocess_exec(index_cmds, self.create_index)
        if result:
            bb.fatal('%s' % ('\n'.join(result)))
        self.repo_server = HTTPService(oeRuntimeTest.tc.d.getVar('WORKDIR', True), oeRuntimeTest.tc.target.server_ip)
        self.repo_server.start()

    @classmethod
    def tearDownClass(self):
        self.repo_server.stop()
        for i in self.repolist:
            oeRuntimeTest.tc.target.run('smart channel -y --remove '+str(i))

    @testcase(1143)
    def test_smart_channel(self):
        self.smart('channel', 1)

    @testcase(719)
    def test_smart_channel_add(self):
        image_pkgtype = self.tc.d.getVar('IMAGE_PKGTYPE', True)
        deploy_url = 'http://%s:%s/%s' %(self.target.server_ip, self.repo_server.port, image_pkgtype)
        pkgarchs = self.tc.d.getVar('PACKAGE_ARCHS', True).replace("-","_").split()
        for arch in os.listdir('%s/%s' % (self.repo_server.root_dir, image_pkgtype)):
            if arch in pkgarchs:
                self.smart('channel -y --add {a} type=rpm-md baseurl={u}/{a}'.format(a=arch, u=deploy_url))
                self.repolist.append(arch)
        self.smart('update')

    @testcase(969)
    def test_smart_channel_help(self):
        self.smart('channel --help')

    @testcase(970)
    def test_smart_channel_list(self):
        self.smart('channel --list')

    @testcase(971)
    def test_smart_channel_show(self):
        self.smart('channel --show')

    @testcase(717)
    def test_smart_channel_rpmsys(self):
        self.smart('channel --show rpmsys')
        self.smart('channel --disable rpmsys')
        self.smart('channel --enable rpmsys')

    @testcase(1144)
    @skipUnlessPassed('test_smart_channel_add')
    def test_smart_install(self):
        self.smart('remove -y psplash-default')
        self.smart('install -y psplash-default')

    @testcase(728)
    @skipUnlessPassed('test_smart_install')
    def test_smart_install_dependency(self):
        self.smart('remove -y psplash')
        self.smart('install -y psplash-default')

    @testcase(723)
    @skipUnlessPassed('test_smart_channel_add')
    def test_smart_install_from_disk(self):
        self.smart('remove -y psplash-default')
        self.smart('download psplash-default')
        self.smart('install -y ./psplash-default*')

    @testcase(725)
    @skipUnlessPassed('test_smart_channel_add')
    def test_smart_install_from_http(self):
        output = self.smart('download --urls psplash-default')
        url = re.search('(http://.*/psplash-default.*\.rpm)', output)
        self.assertTrue(url, msg="Couln't find download url in %s" % output)
        self.smart('remove -y psplash-default')
        self.smart('install -y %s' % url.group(0))

    @testcase(729)
    @skipUnlessPassed('test_smart_install')
    def test_smart_reinstall(self):
        self.smart('reinstall -y psplash-default')

    @testcase(727)
    @skipUnlessPassed('test_smart_channel_add')
    def test_smart_remote_repo(self):
        self.smart('update')
        self.smart('install -y psplash')
        self.smart('remove -y psplash')

    @testcase(726)
    def test_smart_local_dir(self):
        self.target.run('mkdir /tmp/myrpmdir')
        self.smart('channel --add myrpmdir type=rpm-dir path=/tmp/myrpmdir -y')
        self.target.run('cd /tmp/myrpmdir')
        self.smart('download psplash')
        output = self.smart('channel --list')
        for i in output.split("\n"):
            if ("rpmsys" != str(i)) and ("myrpmdir" != str(i)):
                self.smart('channel --disable '+str(i))
        self.target.run('cd $HOME')
        self.smart('install psplash')
        for i in output.split("\n"):
            if ("rpmsys" != str(i)) and ("myrpmdir" != str(i)):
                self.smart('channel --enable '+str(i))
        self.smart('channel --remove myrpmdir -y')
        self.target.run("rm -rf /tmp/myrpmdir")

    @testcase(718)
    def test_smart_add_rpmdir(self):
        self.target.run('mkdir /tmp/myrpmdir')
        self.smart('channel --add myrpmdir type=rpm-dir path=/tmp/myrpmdir -y')
        self.smart('channel --disable myrpmdir -y')
        output = self.smart('channel --show myrpmdir')
        self.assertTrue("disabled = yes" in output, msg="Failed to disable rpm dir")
        self.smart('channel --enable  myrpmdir -y')
        output = self.smart('channel --show myrpmdir')
        self.assertFalse("disabled = yes" in output, msg="Failed to enable rpm dir")
        self.smart('channel --remove myrpmdir -y')
        self.target.run("rm -rf /tmp/myrpmdir")

    @testcase(731)
    @skipUnlessPassed('test_smart_channel_add')
    def test_smart_remove_package(self):
        self.smart('install -y psplash')
        self.smart('remove -y psplash')
