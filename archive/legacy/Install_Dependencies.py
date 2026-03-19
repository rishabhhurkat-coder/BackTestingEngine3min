import os
import ast
import subprocess
import sys
import pkgutil

# -------------------------------
# CONFIG
# -------------------------------
TARGET_FOLDER = r"G:\My Drive\H&L\EMA 200 TRADES"   # CHANGE THIS

# -------------------------------
# GET STANDARD LIBRARIES
# -------------------------------
def get_stdlib_modules():
    return set(sys.builtin_module_names)

# -------------------------------
# EXTRACT IMPORTS FROM FILE
# -------------------------------
def extract_imports_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        try:
            tree = ast.parse(file.read(), filename=filepath)
        except:
            return set()

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports

# -------------------------------
# SCAN FOLDER
# -------------------------------
def scan_folder(folder):
    all_imports = set()

    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                imports = extract_imports_from_file(path)
                all_imports.update(imports)

    return all_imports

# -------------------------------
# CHECK IF INSTALLED
# -------------------------------
def is_installed(package):
    return pkgutil.find_loader(package) is not None

# -------------------------------
# INSTALL PACKAGE
# -------------------------------
def install_package(package):
    print(f"Installing: {package}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# -------------------------------
# MAIN FLOW
# -------------------------------
def main():
    print("🔍 Scanning project...")
    stdlib = get_stdlib_modules()
    imports = scan_folder(TARGET_FOLDER)

    # Remove stdlib
    external_packages = sorted(pkg for pkg in imports if pkg not in stdlib)

    print("\n📦 Found dependencies:")
    for pkg in external_packages:
        print(f"- {pkg}")

    print("\n🔧 Checking installations...")

    for pkg in external_packages:
        if not is_installed(pkg):
            try:
                install_package(pkg)
            except Exception as e:
                print(f"❌ Failed to install {pkg}: {e}")

    print("\n📄 Generating requirements.txt ...")
    with open("requirements.txt", "w") as f:
        subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=f)

    print("✅ Done.")

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    main()