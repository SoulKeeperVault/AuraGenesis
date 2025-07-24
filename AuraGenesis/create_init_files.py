import os

def add_init_files(root_dir=".", target_folders=None):
    if target_folders is None:
        # Default folders expected to be packages
        target_folders = ["aura_core", "schemas"]

    for folder in target_folders:
        folder_path = os.path.join(root_dir, folder)
        init_file = os.path.join(folder_path, "__init__.py")

        if os.path.isdir(folder_path):
            if not os.path.exists(init_file):
                with open(init_file, "w") as f:
                    f.write("# Auto-generated init file for package structure\n")
                print(f"✅ Created: {init_file}")
            else:
                print(f"⚠️ Already exists: {init_file}")
        else:
            print(f"❌ Not a directory: {folder_path}")

if __name__ == "__main__":
    add_init_files()
