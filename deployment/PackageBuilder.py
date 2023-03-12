import json
import os
import shutil


class PackagingError(Exception):
    def __init__(self, command, error):
        self.command = command
        self.error = error
        super().__init__(f"Packaging error - Command: {self.command}: Error: {self.error}")
        return


class VersionInsertionError(Exception):
    def __init__(self, command, error):
        self.command = command
        self.error = error
        super().__init__(f"Version insertion error - Command: {self.command}: Error: {self.error}")
        return


class PackageBuilder:
    def __init__(self, package_name, build_info_filepath, version):
        with open(build_info_filepath, "r") as json_file:
            json_text = json_file.read()
        self.package_name = package_name
        self.build_info = json.loads(json_text)
        self.version = version
        return

    def build_debian(self):
        """
        build the package
        """
        current_folder = os.path.abspath(os.path.dirname(__file__))
        deb_tmp = os.path.join(current_folder, "deb_tmp")
        shutil.rmtree(deb_tmp, ignore_errors=True)
        template_folder = os.path.join(current_folder, f"deb_{self.package_name}")
        shutil.copytree(template_folder, deb_tmp)
        control_file = os.path.join(deb_tmp, "DEBIAN/control")
        version_cmd = r"sed -i 's_<version>_{}_g' {}".format(self.version, control_file)
        error = os.system(version_cmd)
        if error:
            raise VersionInsertionError(version_cmd, error)
        src_folder = os.path.abspath(os.path.join(current_folder, f'../{self.package_name}'))
        deployment_dir = self.build_info["install_prefix_path"][1:]
        lts_target_folder = os.path.join(deb_tmp, deployment_dir)

        for this_file in self.build_info["app_files"]:
            src_file = os.path.abspath(os.path.join(src_folder, this_file))
            dest_file = os.path.abspath(os.path.join(lts_target_folder, this_file))
            dest_folder = os.path.dirname(dest_file)
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            shutil.copy(src_file, dest_file)

        pkg_cmd = f"dpkg -b {deb_tmp} {self.package_name}-{self.version}.deb"
        error = os.system(pkg_cmd)
        if error:
            raise PackagingError(pkg_cmd, error)
        shutil.rmtree(deb_tmp, ignore_errors=True)
        return
