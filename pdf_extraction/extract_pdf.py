"""
Extract PDF Information
"""

# pylint: disable=C0103
# pylint: disable=C0121
# pylint: disable=C0209
# pylint: disable=C0303

import os
import time

import json
import re

import fitz
import tabula
import PySimpleGUI as sg

DEBUG = False

print(fitz.__doc__)

if tuple(map(int, fitz.version[0].split("."))) < (1, 18, 18):
    raise SystemExit("require PyMuPDF v1.18.18+")

def create_directory_if_not_exists(_dir):
    """
    create_directory_if_not_exists
    """
    if not os.path.exists(_dir):
        os.mkdir(_dir)


def fine_replace(txt):
    """
    fine replace
    """
    txt = txt.replace("-\n", "")
    txt = txt.replace("\n", " ")
    txt = txt.replace("'", "")
    return txt


def cut_references(txt):
    """
    cut references
    """
    last_start = len(txt)
    for m in re.finditer("references", txt.lower()):
        last_start = m.start()
    return txt[:last_start]


def dump_to_txt(txt, cut_flag, file_path):
    """
    dump txt
    """
    if cut_flag:
        txt = cut_references(txt)
    with open(file_path, "w", encoding="utf-8", errors="ignore") as file:
        file.write(str(txt))


def dump_to_json(txt, file_path):
    """
    dump json
    """
    txt = json.dumps(txt, ensure_ascii=False)
    dump_to_txt(txt, False, file_path)


def pymupdf_extract_text(file_path):
    """
    Load PDF
    """
    # print(fitz.__doc__)
    doc = fitz.open(file_path)
    md_res = doc.metadata
    num_pages = doc.page_count
    txt = ""

    for page_num in range(num_pages):
        page = doc.load_page(page_num)
        txt += page.get_text()

    txt = fine_replace(txt)

    doc.close()
    return md_res, txt


def pymupdf_extract_image(file_path, output_path):
    """
    extract image
    """
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    os.system("python pipeline/pymu_img.py " + file_path + " " + output_path)


def tabula_extract_table(file_path, output_path):
    """
    tabula_extract_table
    """
    t0 = time.time()
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # Extract tables from the PDF
    tables = tabula.read_pdf(file_path, pages="all")
    id_ext = 0

    for idx, table in enumerate(tables):
        print("Checking table ", idx)
        is_ok = True

        # if is_ok:
        #     is_ok = check_cells_length(table, 60)
        # if is_ok:
        #     is_ok = check_cols_length(table, 60)

        if is_ok:
            table = check_null_ratio(table, 0.7)
            id_ext += 1
            table.to_csv(output_path + "/table" + str(idx) + ".csv", encoding="utf-8")
    t1 = time.time()

    print(str(len(tables)) + " tables in total")
    print(str(id_ext) + " tables extracted")
    print("total time %g sec" % (t1 - t0))


def check_null_ratio(df, rate):
    """
    check_null_ratio
    """
    ret = True
    total = df.shape[1]
    sumation = df.isnull().sum()
    list_isnull = [i / total > rate for i in sumation]
    drop_list = []
    for idv, val in enumerate(list_isnull):
        if val:
            drop_list.append(idv)
            ret = False
    df = df.drop(df.columns[drop_list], axis=1)
    if not ret:
        print("Recreate current table, reason: null rate = ", rate)
    return df


def check_cells_length(df, length):
    """
    check_cells_length
    """
    ret = True
    df_isnull = df.isnull()
    ix, jx = df.shape
    for i in range(ix):
        for j in range(jx):
            if df_isnull.iat[i, j] == False and len(str(df.iat[i, j])) > length:
                ret = False
    if not ret and DEBUG:
        print("Skip current table, reason: cell's value is too long")
        print(df.head())
        print("[END]")
    return ret


def check_cols_length(df, length):
    """
    check_cols_length
    """
    ret = True
    cols = df.columns
    cols_isnull = cols.isnull()
    for i, val in enumerate(cols):
        if cols_isnull[i] == False and len(val) > length:
            ret = False
    if not ret and DEBUG:
        print("Skip current table, reason: col's value is too long")
        print(df.head())
        print("[END]")
    return ret


def pdf_extraction(_loading_window, _folder_path, _flags, _list_dir):
    """
    pdf_extraction
    """
    progress_bar = _loading_window["-PROGRESS-"]
    progress_text = _loading_window["-PROGRESS-TEXT-"]
    progress_text.update("Progress: 0%")
    progress_bar.update(0)

    max_p = len(os.listdir(_folder_path))
    i_doc = 0
    for filename in os.listdir(_folder_path):
        if filename.endswith(".pdf"):
            # data extraction
            pdf_path = os.path.join(_folder_path, filename)
            (metadata, text) = pymupdf_extract_text(pdf_path)
            if _flags[0]:
                md_loc = _list_dir[0] + filename + ".txt"
                dump_to_json(metadata, md_loc)
            if _flags[1]:
                text_loc = _list_dir[1] + filename + ".txt"
                dump_to_txt(text, True, text_loc)
            if _flags[2]:
                img_loc = _list_dir[2] + filename
                pymupdf_extract_image(pdf_path, img_loc)
            if _flags[3]:
                table_loc = _list_dir[3] + filename
                tabula_extract_table(pdf_path, table_loc)

        # progress bar
        i_doc += 1
        perc = ((i_doc) / max_p) * 100
        progress_text.update(f"Progress: {round(perc, 2)}%      File: {filename}")
        progress_bar.update(perc)

        # terminate handler
        event, values = _loading_window.read(timeout=0)
        if event == sg.WINDOW_CLOSED:
            print(f"Extraction terminated. Last extracted file:{filename}, progress:{round(perc, 2)}%")
            return True  # User closed the loading window
    return False  # Loading completed without interruption

layout = [
    [sg.Text("Select a folder:")],
    [sg.Input(key="-INPUT-", disabled=True), sg.FolderBrowse()],
    [sg.Text("Select destination folder:")],
    [sg.Input(key="-OUTPUT-", disabled=True, default_text="output"), sg.FolderBrowse()],
    [sg.Text("Options:")],
    [
        sg.Column(
            [
                [
                    sg.Checkbox("Metadata", default=True, key="-METADATA-", size=(7, 1)),
                    sg.Checkbox("Texts", default=True, key="-TEXTS-", size=(7, 1)),
                    sg.Checkbox("Images", default=True, key="-IMAGES-", size=(7, 1)),
                    sg.Checkbox("Tables", default=True, key="-TABLES-", size=(7, 1)),
                ]
            ],
            element_justification="center",
        )
    ],
    [sg.Button("Extract", key="-EXTRACT-")],
]


# Run the app
if __name__ == "__main__":
    window = sg.Window("PDF Extraction", layout)
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED:
            break
        if event == "-EXTRACT-":
            if values["-INPUT-"] == "" or values["-OUTPUT-"] == "":
                sg.popup("Select both folder path!", title="Error!")
            else:
                folder_path = values["-INPUT-"]
                output_dir = values["-OUTPUT-"]
                checkbox_values = [
                    values["-METADATA-"],
                    values["-TEXTS-"],
                    values["-IMAGES-"],
                    values["-TABLES-"],
                ]

                # create directory if not exists
                metadata_dir = output_dir + "/metadata/"
                text_dir = output_dir + "/text/"
                img_dir = output_dir + "/img/"
                table_dir = output_dir + "/table/"
                list_dir = [metadata_dir, text_dir, img_dir, table_dir]
                cd = [create_directory_if_not_exists(item) for item in list_dir]

                # Hide the first window
                window.hide()

                loading_layout = [
                    [sg.Text("Loading...")],
                    [
                        sg.ProgressBar(
                            max_value=100, orientation="h", size=(20, 20), key="-PROGRESS-"
                        )
                    ],
                    [sg.Text("Progress: 0%", key="-PROGRESS-TEXT-")],
                ]

                loading_window = sg.Window("Loading", loading_layout, finalize=True)

                if pdf_extraction(loading_window, folder_path, checkbox_values, list_dir):
                    break

                loading_window.close()

                sg.popup(
                    f"Extracted file(s) directory: {output_dir}",
                    title="Completed",
                )

                break

    window.close()
