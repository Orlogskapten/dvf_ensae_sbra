import os
from py7zr import unpack_7zarchive
import shutil


def actions(data_path=r"../data/shp_csv/", unziped_location=r"../data/unziped"):
    #     data_path= "data/shp_csv/"

    all_dir = os.listdir(data_path)
    print(all_dir)

    all_dir_path = list(map(lambda x: data_path + x, all_dir))
    print(all_dir_path)

    unziped_path = []
    for folder_path in all_dir_path:
        file_name = os.listdir(folder_path)[0]  # because there is only one file per folder
        unziped_path.append(folder_path + "/" + file_name)
    print(unziped_path)

    try:
        shutil.register_unpack_format('7zip', ['.7z'], unpack_7zarchive)
    except:
        pass

    # Extraction
    for unziped in unziped_path:
        shutil.unpack_archive(unziped, unziped_location)

    # Lighting our folders (around 15go of data)
    all_dir = os.listdir(unziped_location)

    for chiant in all_dir:
        full_file_unzipped = os.listdir(unziped_location + "/" + chiant)
        # I hate double for loop
        for item in full_file_unzipped:
            if item.endswith((".cpg", ".dbf", ".prj", ".cpg", ".prj")):
                os.remove(os.path.join(unziped_location + "/" + chiant, item))
    pass


if __name__ == '__main__':
    import sys

    # parse sys.argv[1:] using optparse or argparse or what have you
    actions()
    print("Finish")
