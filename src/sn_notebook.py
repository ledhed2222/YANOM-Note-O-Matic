import logging
from pathlib import Path

from alive_progress import alive_bar

import config
import helper_functions
from helper_functions import generate_clean_directory_name
from sn_note_page import NotePage
import zip_file_reader


def what_module_is_this():
    return __name__


class Notebook:
    def __init__(self, nsx_file, notebook_id):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self.nsx_file = nsx_file
        self.notebook_id = notebook_id
        self.conversion_settings = self.nsx_file.conversion_settings
        self._notebook_json = self.fetch_notebook_json(notebook_id)
        self.title = self.fetch_notebook_title()
        self.folder_name = ''
        self.create_folder_name()
        self._full_path_to_notebook = None
        self.note_pages = []
        self.note_titles = []
        self._attachment_md5_file_name_dict = {}
        self._null_attachment_list = []
        self._num_image_attachments = 0
        self._num_file_attachments = 0

    def process_notebook_pages(self):
        self.logger.info(f"Processing note book {self.title} - {self.notebook_id}")

        if not config.yanom_globals.is_silent:
            print(f"Processing '{self.title}' Notebook")
            with alive_bar(len(self.note_pages), bar='blocks') as bar:
                for note_page in self.note_pages:
                    self._process_page(note_page, bar)

            return

        for note_page in self.note_pages:
            self._process_page(note_page)

    def _process_page(self, note_page, bar=None):
        note_page.process_note()
        self._num_image_attachments += note_page.image_count
        self._num_file_attachments += note_page.attachment_count
        if note_page.attachments_json is None:
            self._null_attachment_list.append(note_page.title)
        if bar:
            bar()

    def fetch_notebook_json(self, notebook_id):
        if notebook_id == 'recycle-bin':
            return {'title': 'recycle-bin'}

        self.logger.info(f"Fetching json data file {notebook_id} from {self.nsx_file.nsx_file_name}")
        note_book_json = zip_file_reader.read_json_data(self.nsx_file.nsx_file_name, Path(notebook_id))

        if note_book_json is None:
            self.logger.warning("Unable to read notebook json data from nsx file. using 'title': 'Unknown Notebook'")
            return {'title': 'Unknown Notebook'}

        return note_book_json

    def fetch_notebook_title(self):
        notebook_title = self._notebook_json.get('title', None)
        if notebook_title is None:
            self.logger.warning(f"The data for notebook id '{self.notebook_id}' "
                                f"does not have a key for 'title' using 'Unknown Notebook'")
            return 'Unknown Notebook'
        if notebook_title == "":  # The notebook with no title is called 'My Notebook' in note station
            return "My Notebook"

        return notebook_title

    def pair_up_note_pages_and_notebooks(self, note_page: NotePage):
        self.logger.debug(f"Adding note '{note_page.title}' - {note_page.note_id} "
                          f"to Notebook '{self.title}' - {self.notebook_id}")

        note_page.notebook_folder_name = self.folder_name
        note_page.parent_notebook_id = self.notebook_id
        note_page.parent_notebook = self

        while note_page.title in self.note_titles:
            note_page.increment_duplicated_title(self.note_titles)

        self.note_titles.append(note_page.title)
        self.note_pages.append(note_page)

    def create_folder_name(self):
        self.folder_name = Path(generate_clean_directory_name(self.title,
                                                              self.conversion_settings.filename_options))
        self.logger.info(f'For the notebook "{self.title}" the folder name used is is {self.folder_name }')

    def create_notebook_folder(self, parents=True):
        self.logger.debug(f"Creating notebook folder for {self.title}")

        n = 0
        target_path = Path(self.conversion_settings.working_directory,
                           config.yanom_globals.data_dir,
                           self.nsx_file.conversion_settings.export_folder,
                           self.folder_name)

        while target_path.exists():
            n += 1
            target_path = Path(self.conversion_settings.working_directory,
                               config.yanom_globals.data_dir,
                               self.nsx_file.conversion_settings.export_folder,
                               f"{self.folder_name}-{n}")
        try:
            target_path.mkdir(parents=parents, exist_ok=False)
            self.folder_name = Path(target_path.name)
            self._full_path_to_notebook = target_path
        except FileNotFoundError as e:
            msg = f'Unable to create notebook folder there is a problem with the path.\n{e}'
            if helper_functions.are_windows_long_paths_disabled():
                msg = f"{msg}\n Windows long path names are not enabled check path length"
            self.logger.error(f'{msg}')
            self.logger.error(helper_functions.log_traceback(e))
            if not config.yanom_globals.is_silent:
                print(f'{msg}')
        except OSError as e:
            msg = f'Unable to create note book folder\n{e}'
            self.logger.error(f'{msg}')
            self.logger.error(helper_functions.log_traceback(e))
            if not config.yanom_globals.is_silent:
                print(f'{msg}')

    def create_attachment_folder(self):
        if self.full_path_to_notebook:   # if full path is still None then the folder was not created and we can skip
            self.logger.debug(f"Creating attachment folder")
            try:
                Path(self.full_path_to_notebook, self.conversion_settings.attachment_folder_name).mkdir()
            except FileNotFoundError as e:
                msg = f'Unable to create attachment folder there is a problem with the path.\n{e}'
                if helper_functions.are_windows_long_paths_disabled():
                    msg = f"{msg}\n Windows long path names are not enabled check path length"
                self.logger.error(f'{msg}')
                self.logger.error(helper_functions.log_traceback(e))
                if not config.yanom_globals.is_silent:
                    print(f'{msg}')
            except OSError as e:
                msg = f'Unable to create attachment folder\n{e}'
                self.logger.error(f'{msg}')
                self.logger.error(helper_functions.log_traceback(e))
                if not config.yanom_globals.is_silent:
                    print(f'{msg}')

            return

        self.logger.warning(f"Attachment folder for '{self.title}' "
                            f"was not created as the notebook folder has not been created")

    @property
    def full_path_to_notebook(self):
        return self._full_path_to_notebook

    @property
    def attachment_md5_file_name_dict(self):
        return self._attachment_md5_file_name_dict

    def add_attachment_md5_file_name_dict(self, md5, file_name):
        self._attachment_md5_file_name_dict[md5] = file_name

    @property
    def null_attachment_list(self):
        return self._null_attachment_list

    @property
    def num_image_attachments(self):
        return self._num_image_attachments

    @property
    def num_file_attachments(self):
        return self._num_file_attachments