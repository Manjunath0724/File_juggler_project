"""Release packaging script for File Juggler.

Creates a portable standalone distribution zip including:
- Executable bundle (dist/FileJuggler)
- One-click installer batch script (Install-Shortcuts.bat)
- Uninstaller batch script (Uninstall.bat)
- License and documentation
"""

import os
import shutil
import sys
import zipfile
from pathlib import Path


def package_release():
    project_dir = Path(__file__).resolve().parent.parent
    dist_dir = project_dir / "dist"
    bundle_dir = dist_dir / "FileJuggler"
    installer_dir = project_dir / "installer"
    output_zip = dist_dir / "FileJuggler_v1.0.0_Portable.zip"

    if not (bundle_dir / "FileJuggler.exe").exists():
        print(f"[ERROR] Standalone bundle not found at {bundle_dir / 'FileJuggler.exe'}")
        print("Please run build.bat or build.ps1 first.")
        sys.exit(1)

    print(f"Creating portable release zip at: {output_zip}")

    # Copy portable helpers into bundle
    install_bat_src = installer_dir / "portable_install.bat"
    uninstall_bat_src = installer_dir / "portable_uninstall.bat"
    license_src = project_dir / "LICENSE.txt"

    install_bat_dst = bundle_dir / "Install-Shortcuts.bat"
    uninstall_bat_dst = bundle_dir / "Uninstall.bat"
    license_dst = bundle_dir / "LICENSE.txt"

    shutil.copy2(install_bat_src, install_bat_dst)
    shutil.copy2(uninstall_bat_src, uninstall_bat_dst)
    shutil.copy2(license_src, license_dst)

    # Create zip
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(bundle_dir):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(dist_dir)
                zf.write(file_path, arcname=str(rel_path))

    size_mb = output_zip.stat().st_size / (1024 * 1024)
    print(f"[OK] Successfully created release archive: {output_zip.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    package_release()
