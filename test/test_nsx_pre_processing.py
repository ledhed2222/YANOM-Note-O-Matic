from collections import namedtuple
import os
from pathlib import Path
import re

import pytest

import sn_note_page
from nsx_pre_processing import NoteStationPreProcessing

Attachments = namedtuple('Attachments', 'image_ref path_relative_to_notebook')


@pytest.fixture
def attachments():
    """Provide a dict containing named tuple that will simulate the attachment objects in the real attachment dict"""
    return Attachments('MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n', Path('myfile.txt'))


@pytest.fixture
def note_1(nsx):
    note_page_json = {'parent_id': 'note_book1',
                      'title': 'Page 1 title',
                      'mtime': 1619298559,
                      'ctime': 1619298539,
                      'content': 'content', 'tag': ['1'],
                      'attachment': {"_-m4Hhgmp34U85IwTdWfbWw": {"md5": "e79072f793f22434740e64e93cfe5926",
                                                                 "name": "ns_attach_image_787491613404344687.png",
                                                                 "size": 186875,
                                                                 "width": 1848,
                                                                 "height": 1306,
                                                                 "type": "image/png",
                                                                 "ctime": 1616084097,
                                                                 "ref": "MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n"},
                                     "_YOgkfaY7aeHcezS-jgGSmA": {"md5": "6c4b828f227a096d3374599cae3f94ec",
                                                                 "name": "Record 2021-02-15 16:00:13.webm", "size": 9627, "width": 0,
                                                                 "height": 0,
                                                                 "type": "video/webm",
                                                                 "ctime": 1616084097},
                                     "_yITQrdarvsdg3CkL-ifh4Q": {"md5": "c4ee8b831ad1188509c0f33f0c072af5",
                                                                 "name": "example-attachment.pdf",
                                                                 "size": 14481,
                                                                 "width": 0,
                                                                 "height": 0,
                                                                 "type": "application/pdf",
                                                                 "ctime": 1616084097},
                                     "file_dGVzdCBwYWdlLnBkZjE2MTkyOTg3MjQ2OTE=": {"md5": "27a9aadc878b718331794c8bc50a1b8c",
                                                                                   "name": "test page.pdf",
                                                                                   "size": 320357,
                                                                                   "width": 0,
                                                                                   "height": 0,
                                                                                   "type": "application/pdf",
                                                                                   "ctime": 1619295124}
                                     }
                      }

    note_page = sn_note_page.NotePage(nsx, 1, note_page_json)
    note_page.notebook_folder_name = 'note_book1'
    note_page._file_name = 'page-1-title.md'
    note_page._raw_content = """<div>Pie Chart</div><div></div><div><div class=\"syno-ns-chart-object\" style=\"width: 520px; height: 350px;\" chart-data=\"[[&quot;&quot;,&quot;cost&quot;,&quot;price&quot;,&quot;value&quot;,&quot;total value&quot;],[&quot;something&quot;,500,520,540,520],[&quot;something else&quot;,520,540,560,540],[&quot;another thing&quot;,540,560,580,560]]\" chart-config=\"{&quot;range&quot;:&quot;A1:E4&quot;,&quot;direction&quot;:&quot;row&quot;,&quot;rowHeaderExisted&quot;:true,&quot;columnHeaderExisted&quot;:true,&quot;title&quot;:&quot;Pie chart title&quot;,&quot;chartType&quot;:&quot;pie&quot;,&quot;xAxisTitle&quot;:&quot;x-axis title&quot;,&quot;yAxisTitle&quot;:&quot;y axis ttile&quot;}\"></div></div><div><iframe src=\"https://www.youtube.com/embed/SqdxNUMO2cg\" width=\"420\" height=\"315\" frameborder=\"0\" allowfullscreen=\"\" youtube=\"true\" anchorhref=\"https://www.youtube.com/watch?v=SqdxNUMO2cg\">&nbsp;</iframe></div><div>Below is a hyperlink to the internet</div><div><a href=\"https://github.com/kevindurston21/YANOM-Note-O-Matic\">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></div><div>Below is a 3x3 Table</div><div><table style=\"width: 240px; height: 90px;\"><tbody><tr><td><b>cell R1C1</b></td><td><b>cell R1C2</b></td><td><b>cell R1C3</b></td></tr><tr><td>cell R2C1</td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td>cell R3C1</td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table></div><div>Below&nbsp;is an image of the design of the&nbsp;line chart as seen in note-station</div><div><img class=\" syno-notestation-image-object\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" width=\"600\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div>"""

    return note_page


@pytest.mark.parametrize(
    'raw_content, expected', [
        ("""<div>Pie Chart</div><div></div><div><div class=\"syno-ns-chart-object\" style=\"width: 520px; height: 350px;\" chart-data=\"[[&quot;&quot;,&quot;cost&quot;,&quot;price&quot;,&quot;value&quot;,&quot;total value&quot;],[&quot;something&quot;,500,520,540,520],[&quot;something else&quot;,520,540,560,540],[&quot;another thing&quot;,540,560,580,560]]\" chart-config=\"{&quot;range&quot;:&quot;A1:E4&quot;,&quot;direction&quot;:&quot;row&quot;,&quot;rowHeaderExisted&quot;:true,&quot;columnHeaderExisted&quot;:true,&quot;title&quot;:&quot;Pie chart title&quot;,&quot;chartType&quot;:&quot;pie&quot;,&quot;xAxisTitle&quot;:&quot;x-axis title&quot;,&quot;yAxisTitle&quot;:&quot;y axis ttile&quot;}\"></div></div><div><iframe src=\"https://www.youtube.com/embed/SqdxNUMO2cg\" width=\"420\" height=\"315\" frameborder=\"0\" allowfullscreen=\"\" youtube=\"true\" anchorhref=\"https://www.youtube.com/watch?v=SqdxNUMO2cg\">&nbsp;</iframe></div><div>Below is a hyperlink to the internet</div><div><a href=\"https://github.com/kevindurston21/YANOM-Note-O-Matic\">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></div><div>Below is a 3x3 Table</div><div><table style=\"width: 240px; height: 90px;\"><tbody><tr><td><b>cell R1C1</b></td><td><b>cell R1C2</b></td><td><b>cell R1C3</b></td></tr><tr><td>cell R2C1</td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td>cell R3C1</td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table></div><div>Below&nbsp;is an image of the design of the&nbsp;line chart as seen in note-station</div><div><img class=\" syno-notestation-image-object\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" width=\"600\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div>""",
         r"""<head><title>Page 1 title</title><meta title="Page 1 title"/></head><p>Pie Chart</p><p></p><p><p><img src="attachments/replaced_id_number.png"/></p><p><a href="attachments/replaced_id_number.csv">Chart data file</a></p><p><table border="1" class="dataframe"><thead><tr style="text-align: right;"><th><strong></strong></th><th><strong>cost</strong></th><th><strong>price</strong></th><th><strong>value</strong></th><th><strong>total value</strong></th><th><strong>sum</strong></th><th><strong>percent</strong></th></tr></thead><tbody><tr><th><strong>something</strong></th><td>500</td><td>520</td><td>540</td><td>520</td><td>2080</td><td>32.10</td></tr><tr><th><strong>something else</strong></th><td>520</td><td>540</td><td>560</td><td>540</td><td>2160</td><td>33.33</td></tr><tr><th><strong>another thing</strong></th><td>540</td><td>560</td><td>580</td><td>560</td><td>2240</td><td>34.57</td></tr></tbody></table></p></p><p>iframe-placeholder-id-replaced_id_number</p><p>Below is a hyperlink to the internet</p><p><a href="https://github.com/kevindurston21/YANOM-Note-O-Matic">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></p><p>Below is a 3x3 Table</p><p><table border="1" style="width: 240px; height: 90px;"><thead><tr><td><strong>cell R1C1</strong></td><td><strong>cell R1C2</strong></td><td><strong>cell R1C3</strong></td></tr></thead><tbody><tr><td><strong>cell R2C1</strong></td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td><strong>cell R3C1</strong></td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table></p><p>Below is an image of the design of the line chart as seen in note-station</p><p><img src="myfile.txt" width="600"/></p>""",
         ),
        ("""<div>Pie Chart</div><div></div><div><div class=\"syno-ns-chart-object\" style=\"width: 520px; height: 350px;\" chart-data=\"[[&quot;&quot;,&quot;cost&quot;,&quot;price&quot;,&quot;value&quot;,&quot;total value&quot;],[&quot;something&quot;,500,520,540,520],[&quot;something else&quot;,520,540,560,540],[&quot;another thing&quot;,540,560,580,560]]\" chart-config=\"{&quot;range&quot;:&quot;A1:E4&quot;,&quot;direction&quot;:&quot;row&quot;,&quot;rowHeaderExisted&quot;:true,&quot;columnHeaderExisted&quot;:true,&quot;title&quot;:&quot;Pie chart title&quot;,&quot;chartType&quot;:&quot;pie&quot;,&quot;xAxisTitle&quot;:&quot;x-axis title&quot;,&quot;yAxisTitle&quot;:&quot;y axis ttile&quot;}\"></div></div><div><iframe src=\"https://www.youtube.com/embed/SqdxNUMO2cg\" width=\"420\" height=\"315\" frameborder=\"0\" allowfullscreen=\"\" youtube=\"true\" anchorhref=\"https://www.youtube.com/watch?v=SqdxNUMO2cg\">&nbsp;</iframe></div><div>Below is a hyperlink to the internet</div><div><a href=\"https://github.com/kevindurston21/YANOM-Note-O-Matic\">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></div><div>Below is a 3x3 Table</div><div><table style=\"width: 240px; height: 90px;\"><tbody><tr><td><b>cell R1C1</b></td><td><b>cell R1C2</b></td><td><b>cell R1C3</b></td></tr><tr><td>cell R2C1</td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td>cell R3C1</td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table></div><div>Below&nbsp;is an image of the design of the&nbsp;line chart as seen in note-station</div><div><img adjust="1" class=\" syno-notestation-image-object\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" width=\"600\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div>""",
         r"""<head><title>Page 1 title</title><meta title="Page 1 title"/></head><p>Pie Chart</p><p></p><p><p><img src="attachments/replaced_id_number.png"/></p><p><a href="attachments/replaced_id_number.csv">Chart data file</a></p><p><table border="1" class="dataframe"><thead><tr style="text-align: right;"><th><strong></strong></th><th><strong>cost</strong></th><th><strong>price</strong></th><th><strong>value</strong></th><th><strong>total value</strong></th><th><strong>sum</strong></th><th><strong>percent</strong></th></tr></thead><tbody><tr><th><strong>something</strong></th><td>500</td><td>520</td><td>540</td><td>520</td><td>2080</td><td>32.10</td></tr><tr><th><strong>something else</strong></th><td>520</td><td>540</td><td>560</td><td>540</td><td>2160</td><td>33.33</td></tr><tr><th><strong>another thing</strong></th><td>540</td><td>560</td><td>580</td><td>560</td><td>2240</td><td>34.57</td></tr></tbody></table></p></p><p>iframe-placeholder-id-replaced_id_number</p><p>Below is a hyperlink to the internet</p><p><a href="https://github.com/kevindurston21/YANOM-Note-O-Matic">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></p><p>Below is a 3x3 Table</p><p><table border="1" style="width: 240px; height: 90px;"><thead><tr><td><strong>cell R1C1</strong></td><td><strong>cell R1C2</strong></td><td><strong>cell R1C3</strong></td></tr></thead><tbody><tr><td><strong>cell R2C1</strong></td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td><strong>cell R3C1</strong></td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table></p><p>Below is an image of the design of the line chart as seen in note-station</p><p><img src="myfile.txt" width="600"/></p>""",
         ),
        ("""<div>Pie Chart</div><div></div><div><div class=\"syno-ns-chart-object\" style=\"width: 520px; height: 350px;\" chart-data=\"[[&quot;&quot;,&quot;cost&quot;,&quot;price&quot;,&quot;value&quot;,&quot;total value&quot;],[&quot;something&quot;,500,520,540,520],[&quot;something else&quot;,520,540,560,540],[&quot;another thing&quot;,540,560,580,560]]\" chart-config=\"{&quot;range&quot;:&quot;A1:E4&quot;,&quot;direction&quot;:&quot;row&quot;,&quot;rowHeaderExisted&quot;:true,&quot;columnHeaderExisted&quot;:true,&quot;title&quot;:&quot;Pie chart title&quot;,&quot;chartType&quot;:&quot;pie&quot;,&quot;xAxisTitle&quot;:&quot;x-axis title&quot;,&quot;yAxisTitle&quot;:&quot;y axis ttile&quot;}\"></div></div><div><iframe src=\"https://www.youtube.com/embed/SqdxNUMO2cg\" width=\"420\" height=\"315\" frameborder=\"0\" allowfullscreen=\"\" youtube=\"true\" anchorhref=\"https://www.youtube.com/watch?v=SqdxNUMO2cg\">&nbsp;</iframe></div><div>Below is a hyperlink to the internet</div><div><a href=\"https://github.com/kevindurston21/YANOM-Note-O-Matic\">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></div><div>Below is a 3x3 Table</div><div><table style=\"width: 240px; height: 90px;\"><tbody><tr><td><b>cell R1C1</b></td><td><b>cell R1C2</b></td><td><b>cell R1C3</b></td></tr><tr><td>cell R2C1</td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td>cell R3C1</td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table></div><div>Below&nbsp;is an image of the design of the&nbsp;line chart as seen in note-station</div><div><img adjust="1" class=\" syno-notestation-image-object\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" alt=\"some alt text\" width=\"600\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div>""",
         r"""<head><title>Page 1 title</title><meta title="Page 1 title"/></head><p>Pie Chart</p><p></p><p><p><img src="attachments/replaced_id_number.png"/></p><p><a href="attachments/replaced_id_number.csv">Chart data file</a></p><p><table border="1" class="dataframe"><thead><tr style="text-align: right;"><th><strong></strong></th><th><strong>cost</strong></th><th><strong>price</strong></th><th><strong>value</strong></th><th><strong>total value</strong></th><th><strong>sum</strong></th><th><strong>percent</strong></th></tr></thead><tbody><tr><th><strong>something</strong></th><td>500</td><td>520</td><td>540</td><td>520</td><td>2080</td><td>32.10</td></tr><tr><th><strong>something else</strong></th><td>520</td><td>540</td><td>560</td><td>540</td><td>2160</td><td>33.33</td></tr><tr><th><strong>another thing</strong></th><td>540</td><td>560</td><td>580</td><td>560</td><td>2240</td><td>34.57</td></tr></tbody></table></p></p><p>iframe-placeholder-id-replaced_id_number</p><p>Below is a hyperlink to the internet</p><p><a href="https://github.com/kevindurston21/YANOM-Note-O-Matic">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></p><p>Below is a 3x3 Table</p><p><table border="1" style="width: 240px; height: 90px;"><thead><tr><td><strong>cell R1C1</strong></td><td><strong>cell R1C2</strong></td><td><strong>cell R1C3</strong></td></tr></thead><tbody><tr><td><strong>cell R2C1</strong></td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td><strong>cell R3C1</strong></td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table></p><p>Below is an image of the design of the line chart as seen in note-station</p><p><img alt="some alt text" src="myfile.txt" width="600"/></p>""",
         ),
    ],
    ids=['without adjustment ', 'with adjustment', 'with alt text in image']
)
def test_pre_process_note_page(note_1, attachments, raw_content, expected):
    note_1.conversion_settings.metadata_schema = ['title']  # should be ignored and not added in pre-processing
    note_1._raw_content = raw_content
    note_1.conversion_settings.export_format = 'gfm'

    note_1._attachments = {'an_attachment': attachments}
    note_1.pre_process_content()

    if os.name == 'nt':
        regex = r"\d{13}"
    else:
        regex = r"\d{15}"
    test_string = note_1.pre_processed_content
    substitute_text = 'replaced_id_number'
    result = re.sub(regex, substitute_text, test_string, 0, re.MULTILINE)

    assert result == expected


def test_test_pre_process_note_page_obsidian_output(note_1):
    note_1.conversion_settings.export_format = 'obsidian'
    note_1.conversion_settings.metadata_schema = ['title']
    note_1.conversion_settings.export_format = 'obsidian'
    note_1._raw_content = """<div>Below&nbsp;is an image of the design of the&nbsp;line chart as seen in note-station</div><div><img adjust="1" class=\" syno-notestation-image-object\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" alt=\"some alt text\" width=\"600\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div><div>Some more text</div"""
    expected = r"""<head><title>Page 1 title</title><meta title="Page 1 title"/></head><p>Below is an image of the design of the line chart as seen in note-station</p><p><p>replaced_id_number</p></p><p>Some more text&lt;/div</p>"""
    note_1.pre_process_content()

    if os.name == 'nt':
        regex = r"\d{13}"
    else:
        regex = r"\d{15}"
    test_string = note_1.pre_processed_content
    substitute_text = 'replaced_id_number'
    result = re.sub(regex, substitute_text, test_string, 0, re.MULTILINE)

    assert result == expected


def test_pre_process_note_page_1(note_1, attachments):
    note_1.conversion_settings.first_row_as_header = False
    note_1.conversion_settings.first_column_as_header = False
    note_1.conversion_settings.front_matter_format = 'none'

    note_1._attachments = {'an_attachment': attachments}
    note_1.pre_process_content()

    expected = """<p>Pie Chart</p><p></p><p><p><img src="attachments/replaced_id_number.png"></p><p><a href="attachments/replaced_id_number.csv">Chart data file</a></p><p><table border="1" class="dataframe"><thead><tr style="text-align: right;"><th><strong></strong></th><th><strong>cost</strong></th><th><strong>price</strong></th><th><strong>value</strong></th><th><strong>total value</strong></th><th><strong>sum</strong></th><th><strong>percent</strong></th></tr></thead><tbody><tr><th><strong>something</strong></th><td>500</td><td>520</td><td>540</td><td>520</td><td>2080</td><td>32.10</td></tr><tr><th><strong>something else</strong></th><td>520</td><td>540</td><td>560</td><td>540</td><td>2160</td><td>33.33</td></tr><tr><th><strong>another thing</strong></th><td>540</td><td>560</td><td>580</td><td>560</td><td>2240</td><td>34.57</td></tr></tbody></table></p></p><p>iframe-placeholder-id-replaced_id_number</p><p>Below is a hyperlink to the internet</p><p><a href="https://github.com/kevindurston21/YANOM-Note-O-Matic">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></p><p>Below is a 3x3 Table</p><p><table border="1" style="width: 240px; height: 90px;"><tbody><tr><td><b>cell R1C1</b></td><td><b>cell R1C2</b></td><td><b>cell R1C3</b></td></tr><tr><td>cell R2C1</td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td>cell R3C1</td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table></p><p>Below is an image of the design of the line chart as seen in note-station</p><p><img src="myfile.txt" width="600"/></p>"""

    if os.name == 'nt':
        regex = r"\d{13}"
    else:
        regex = r"\d{15}"
    test_string = note_1.pre_processed_content
    substitute_text = 'replaced_id_number'
    result = re.sub(regex, substitute_text, test_string, 0, re.MULTILINE)

    assert result == expected


def test_pre_process_note_page_with_header_row_and_column(note_1):
    note_1.conversion_settings.first_row_as_header = True
    note_1.conversion_settings.first_column_as_header = True
    note_1.conversion_settings.front_matter_format = 'none'
    note_1._raw_content = """<table style=\"width: 240px; height: 90px;\"><tbody><tr><td><b>cell R1C1</b></td><td><b>cell R1C2</b></td><td><b>cell R1C3</b></td></tr><tr><td>cell R2C1</td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td>cell R3C1</td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table>"""
    expected = """<table border="1" style="width: 240px; height: 90px;"><thead><tr><td><strong>cell R1C1</strong></td><td><strong>cell R1C2</strong></td><td><strong>cell R1C3</strong></td></tr></thead><tbody><tr><td><strong>cell R2C1</strong></td><td>cell R1C2</td><td>cell R1C3</td></tr><tr><td><strong>cell R3C1</strong></td><td>cell R1C2</td><td>cell R1C3</td></tr></tbody></table>"""
    note_1.pre_process_content()

    result = note_1.pre_processed_content

    assert result == expected


def test_pre_process_note_page_1_with_single_row_table(note_1):
    note_1.conversion_settings.first_row_as_header = True
    note_1.conversion_settings.first_column_as_header = False
    note_1.conversion_settings.front_matter_format = 'none'
    note_1._raw_content = """<div>Below is a 3x1 Table</div><div><table style=\"width: 240px; height: 90px;\"><tbody><tr><td><b>cell R1C1</b></td><td><b>cell R1C2</b></td><td><b>cell R1C3</b></td></tr></tbody></table></div>"""
    expected = """<p>Below is a 3x1 Table</p><p><table border="1" style="width: 240px; height: 90px;"><tbody><tr><td><b>cell R1C1</b></td><td><b>cell R1C2</b></td><td><b>cell R1C3</b></td></tr></tbody></table></p>"""

    note_1.pre_process_content()

    result = note_1.pre_processed_content

    assert result == expected


@pytest.mark.parametrize(
    'pre_processed_content, expected, export_format', [
        ("""<div><img src="attachments/12345678.png" width="600"/></div>""",
         """<div><p>replaced_id_number</p></div>""",
         'obsidian'
         ),
        ("""<div><img src="attachments/12345678.png" width="600"/></div>""",
         """<div><img src="attachments/12345678.png" width="600"/></div>""",
         'gfm'
         ),
        ("""<div><img alt="Some alt text" src="attachments/12345678.png"/></div>""",
         """<div><img alt="Some alt text" src="attachments/12345678.png"/></div>""",
         'obsidian',
         ),
        ("""<div><img alt="Some alt text" src="attachments/12345678.png"/></div>""",
         """<div><img alt="Some alt text" src="attachments/12345678.png"/></div>""",
         'gfm',
         ),
        ("""<div><img alt="Some alt text" /></div>""",
         """<div><img alt="Some alt text" src=""/></div>""",
         'gfm',
         ),
    ],
)
def test_process_image_tags(note_1, pre_processed_content, expected, export_format):
    pre_processor = NoteStationPreProcessing(note_1)
    pre_processor.pre_processed_content = pre_processed_content
    pre_processor._note.conversion_settings.export_format = export_format

    pre_processor.process_image_tags()

    test_string = pre_processor.pre_processed_content

    # replace the generated 15 digit id-numbers with placeholder text to allow comparison
    regex = r"\d{15}"
    substitute_text = 'replaced_id_number'
    result = re.sub(regex, substitute_text, test_string, 0, re.MULTILINE)

    assert result == expected


def test_get_image_relative_path_force_exception_and_confirm_is_handled(note_1):
    attachments = Attachments('not_going_to_match', Path('my_file.txt'))
    note_1._attachments = {'an_attachment': attachments}
    pre_processor = NoteStationPreProcessing(note_1)

    pre_processor.get_image_relative_path('1234')
    # if no AttributeError Raised the exception was handled
