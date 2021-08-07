import os
from abc import ABC, abstractmethod
import copy
import logging

from pyfiglet import Figlet
from PyInquirer.prompt import prompt
import PyInquirer
from prompt_toolkit.styles import Style

import config
import helper_functions


def what_module_is_this():
    return __name__


def show_app_title():
    print(Figlet().renderText(config.APP_NAME))
    f = Figlet(font='slant')
    print(f.renderText(config.APP_SUB_NAME))


def _exit_if_keyboard_interrupt(answer):
    """Check if user used keyboard interrupt on question"""
    # PyInquirer intercepts keyboard interrupt and returns {} check for {} and exit gracefully if found
    if answer == {}:
        raise KeyboardInterrupt  # will be caught by yanom.py handle_unhandled_exception() method


class InquireCommandLineInterface(ABC):
    """
    Abstract class to define a consistent style format for child classes

    Methods
    -------
    run_cli:
        This abstract method should be the only public method in child classes and will execute methods required to
        ask for input, process responses as required and return required values.
    """
    def __init__(self):

        self.style = Style.from_dict({
            'separator': '#cc5454',
            'questionmark': '#673ab7 bold noreverse',
            'selected': '#cc5454 noreverse',  # default
            'pointer': '#673ab7 bold',
            'instruction': '',  # default
            'answer': '#f44336 bold',
            'question': '',
        })

    @abstractmethod
    def run_cli(self):  # pragma: no cover
        pass


class StartUpCommandLineInterface(InquireCommandLineInterface):
    """
    Command line interface to run on program startup.

    Returns a configured child of ConversionSettings class
    """
    def __init__(self, config_ini_conversion_settings):
        super(StartUpCommandLineInterface, self).__init__()
        self.logger = logging.getLogger(f'{config.APP_NAME}.{what_module_is_this()}.{self.__class__.__name__}')
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._default_settings = config_ini_conversion_settings
        self._current_conversion_settings = copy.deepcopy(self._default_settings)
        self._current_conversion_settings.set_quick_setting('manual')
        pass

    def run_cli(self):
        self.logger.debug("Running start up interactive command line")
        show_app_title()

        self._ask_and_set_conversion_input()

        if self._current_conversion_settings.conversion_input == 'markdown':
            self._ask_markdown_conversion_options()
        if self._current_conversion_settings.conversion_input == 'html':
            self._ask_html_conversion_options()
        if self._current_conversion_settings.conversion_input == 'nsx':
            self._ask_nsx_conversion_options()

        self.logger.info(f"Returning settings for {self._current_conversion_settings}")
        return self._current_conversion_settings

    def _ask_and_set_conversion_input(self):
        conversion_input_prompt = {
            'type': 'list',
            'name': 'conversion_input',
            'message': 'What do you wish to convert?',
            'choices': self._default_settings.valid_conversion_inputs,
            'default': self._default_settings.conversion_input,
        }
        answer = prompt(conversion_input_prompt, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.conversion_input = answer['conversion_input']
        if answer['conversion_input'] == 'nsx':
            self._current_conversion_settings.metadata_schema = 'title, ctime, mtime, tag'

    def _ask_markdown_conversion_options(self):
        self._ask_and_set_markdown_input_format()

        if self._current_conversion_settings.quick_setting == 'manual':
            self._ask_and_set_export_format()
            if self._current_conversion_settings.export_format == self._current_conversion_settings.markdown_conversion_input:
                self._nothing_to_convert()
            if not self._current_conversion_settings.export_format == 'html':
                self._ask_and_set_front_matter_format()
                if self._current_conversion_settings.front_matter_format != 'none':
                    self._ask_and_set_metadata_details()
                    self._ask_and_set_metadata_schema()
                else:
                    self._ask_and_set_tag_prefix()

    def _ask_html_conversion_options(self):
        self._ask_and_set_conversion_quick_setting()

        if self._current_conversion_settings.quick_setting == 'manual':
            self._ask_and_set_export_format()
            self._ask_and_set_front_matter_format()
            if self._current_conversion_settings.front_matter_format != 'none':
                self._ask_and_set_metadata_schema()

    def _nothing_to_convert(self):
        self.logger.warning('Input and output formats are the same nothing to convert. Exiting.')
        if not config.silent:
            print('Input and output formats are the same nothing to convert. Exiting.')
        exit(0)

    def _ask_and_set_markdown_input_format(self):
        markdown_conversion_input = {
            'type': 'list',
            'name': 'markdown_conversion_input',
            'message': 'What is the format of your current markdown files?',
            'choices': self._default_settings.valid_markdown_conversion_inputs,
            'default': self._default_settings.markdown_conversion_input,
        }
        answer = prompt(markdown_conversion_input, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.markdown_conversion_input = answer['markdown_conversion_input']

    def _ask_and_set_front_matter_format(self):
        if self._current_conversion_settings.export_format == 'pandoc_markdown':
            self._current_conversion_settings.front_matter_format = 'yaml'
            return

        front_matter_format = {
            'type': 'list',
            'name': 'front_matter_format',
            'message': 'What is the format of meta data front matter do you wish to use?',
            'choices': self._default_settings.valid_front_matter_formats,
            'default': self._default_settings.front_matter_format,
        }
        answer = prompt(front_matter_format, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.front_matter_format = answer['front_matter_format']

    def _ask_nsx_conversion_options(self):
        self._ask_and_set_conversion_quick_setting()

        if self._current_conversion_settings.quick_setting == 'manual':
            self._ask_and_set_export_format()
            if self._current_conversion_settings.export_format != 'html':
                self._ask_markdown_metadata_questions()
            self._ask_and_set_table_details()
            self._ask_and_set_chart_options()
            self._ask_and_set_export_folder_name()
            self._ask_and_set_attachment_folder_name()
            self._ask_and_set_file_name_options()
            self._ask_and_set_space_replacement_character()
            self._ask_and_set_maximum_filename_length()

    def _ask_markdown_metadata_questions(self):
        self._ask_and_set_front_matter_format()
        if self._current_conversion_settings.front_matter_format != 'none':
            self._ask_and_set_metadata_details()
            if self._current_conversion_settings.front_matter_format == 'text':
                self._ask_and_set_tag_prefix()
            self._ask_and_set_metadata_schema()

    def _ask_and_set_conversion_quick_setting(self):
        quick_setting_prompt = {
            'type': 'list',
            'name': 'quick_setting',
            'message': 'Choose a quick setting or manual mode',
            'choices': self._default_settings.valid_quick_settings,
            'default': self._default_settings.quick_setting,
        }
        answer = prompt(quick_setting_prompt, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.set_quick_setting(answer['quick_setting'])
        self._current_conversion_settings.conversion_input = self._current_conversion_settings.conversion_input

    def _ask_and_set_export_format(self):
        export_format_prompt = {
            'type': 'list',
            'name': 'export_format',
            'message': 'Choose an export format',
            'choices': self._default_settings.valid_export_formats,
            'default': self._default_settings.export_format,
        }
        answer = prompt(export_format_prompt, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.export_format = answer['export_format']

    def _set_meta_data_for_html(self):
        self._current_conversion_settings.include_meta_data = True
        self._current_conversion_settings.insert_title = True
        self._current_conversion_settings.insert_creation_time = True
        self._current_conversion_settings.insert_modified_time = True
        self._current_conversion_settings.include_tags = True

    def _ask_and_set_metadata_details(self):
        questions = [
            {
                'type': 'checkbox',
                'message': 'Select meta data details',
                'name': 'metadata_details',
                'choices': [
                    PyInquirer.Separator('= Tag options ='),
                    {
                        'name': 'Spaces in tags',
                        'checked': self._default_settings.spaces_in_tags
                    },
                    {
                        'name': 'Split tags',
                        'checked': self._default_settings.split_tags
                    },
                ],
            }
        ]

        answers = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answers)

        if 'Spaces in tags' in answers['metadata_details']:
            self._current_conversion_settings.spaces_in_tags = True

        if 'Split tags' in answers['metadata_details']:
            self._current_conversion_settings.split_tags = True

    def _ask_and_set_metadata_schema(self):
        questions = [
            {
                'type': 'input',
                'name': 'metadata_schema',
                'message': 'Enter comma delimited list of metadata tags to look for.  Leave blank to use any tags found.',
                'default': ", ".join(self._current_conversion_settings.metadata_schema)
            },
        ]
        answer = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.metadata_schema = answer['metadata_schema']

    def _ask_and_set_table_details(self):
        questions = [
            {
                'type': 'checkbox',
                'message': 'Select table options',
                'name': 'table_options',
                'choices': [
                    PyInquirer.Separator('= Table Options ='),
                    {
                        'name': 'First row of table as header row',
                        'checked': self._default_settings.first_row_as_header
                    },
                    {
                        'name': 'First column of table as header column',
                        'checked': self._default_settings.first_column_as_header
                    },
                ],
            }
        ]

        answers = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answers)

        if 'First row of table as header row' in answers['table_options']:
            self._current_conversion_settings.first_row_as_header = True

        if 'First column of table as header column' in answers['table_options']:
            self._current_conversion_settings.first_column_as_header = True

    def _ask_and_set_chart_options(self):
        questions = [
            {
                'type': 'checkbox',
                'message': 'Select chart options',
                'name': 'chart_options',
                'choices': [
                    PyInquirer.Separator('= Chart Options ='),
                    {
                        'name': 'Include an image of chart',
                        'checked': self._default_settings.chart_image
                    },
                    {
                        'name': 'Include a csv file of chart data',
                        'checked': self._default_settings.chart_csv
                    },
                    {
                        'name': 'Include a data table of chart data',
                        'checked': self._default_settings.chart_data_table
                    },
                ],
            }
        ]

        answers = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answers)

        self._current_conversion_settings.chart_image = 'Include an image of chart' in answers['chart_options']
        self._current_conversion_settings.chart_csv = 'Include a csv file of chart data' in answers['chart_options']
        self._current_conversion_settings.chart_data_table = 'Include a data table of chart data' in answers['chart_options']

    def _ask_and_set_tag_prefix(self):
        questions = [
            {
                'type': 'input',
                'name': 'tag_prefix',
                'message': 'Enter a tag prefix e.g. # or @',
                'default': self._default_settings.tag_prefix
            }
        ]

        answer = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.tag_prefix = answer['tag_prefix']

    def _ask_and_set_export_folder_name(self):
        default_folder_name = str(self._default_settings.export_folder)
        if default_folder_name == '':
            default_folder_name = 'notes'
        questions = [
            {
                'type': 'input',
                'name': 'export_folder',
                'message': 'Enter a directory name for notes to be exported to (blank entry "notes" will be used)',
                'default': default_folder_name
            }
        ]
        answer = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        if answer['export_folder'] == '':
            answer['export_folder'] = 'notes'
        self._current_conversion_settings.export_folder = answer['export_folder']

        if str(self._current_conversion_settings.export_folder) != answer['export_folder']:
            self._ask_to_confirm_changed_path_name(self._current_conversion_settings.export_folder,
                                                   self._ask_and_set_export_folder_name)

    def _ask_and_set_attachment_folder_name(self):
        default_folder_name = str(self._default_settings.attachment_folder_name)
        if default_folder_name == '':
            default_folder_name = 'attachments'

        questions = [
            {
                'type': 'input',
                'name': 'attachment_folder_name',
                'message': 'Enter a directory name for notes to be exported to (blank entry "attachments" will be used)',
                'default': default_folder_name
            },
        ]
        answer = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        if answer['attachment_folder_name'] == '':
            answer['attachment_folder_name'] = 'attachments'
        self._current_conversion_settings.attachment_folder_name = answer['attachment_folder_name']

        if not str(self._current_conversion_settings.attachment_folder_name) == answer['attachment_folder_name']:
            self._ask_to_confirm_changed_path_name(self._current_conversion_settings.attachment_folder_name,
                                                   self._ask_and_set_attachment_folder_name)

    def _ask_to_confirm_changed_path_name(self, new_path, not_accept_change_function):
        message = f"Your submitted folder name has been changed to {new_path}. Do you accept this change?"
        questions = [
            {
                'type': 'confirm',
                'message': message,
                'name': 'accept_change',
                'default': True,
            },
        ]

        answer = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answer)

        if not answer['accept_change']:
            not_accept_change_function()

    def _ask_and_set_file_name_options(self):
        questions = [
            {
                'type': 'checkbox',
                'message': 'Select file and directory naming options',
                'name': 'filename_options',
                'choices': [
                    {
                        'name': 'Allow spaces in file and directory names',
                        'checked': self._default_settings.allow_spaces_in_filenames
                    },
                    {
                        'name': 'Allow unicode characters',
                        'checked': self._default_settings.allow_unicode_in_filenames
                    },
                    {
                        'name': 'Allow uppercase characters',
                        'checked': self._default_settings.allow_uppercase_in_filenames
                    },
                    {
                        'name': 'Allow non-alphanumeric characters',
                        'checked': self._default_settings.allow_non_alphanumeric_in_filenames
                    },
                    {
                        'name': 'Include creation time in the file name',
                        'checked': self._default_settings.creation_time_in_exported_file_name
                    },
                ],
            },
        ]

        answers = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answers)
        self._current_conversion_settings.allow_spaces_in_filenames = \
            'Allow spaces in file and directory names' in answers['filename_options']
        self._current_conversion_settings.allow_spaces_in_filenames = \
            'Allow unicode characters' in answers['filename_options']
        self._current_conversion_settings.allow_uppercase_in_filenames = \
            'Allow uppercase characters' in answers['filename_options']
        self._current_conversion_settings.allow_non_alphanumeric_in_filenames = \
            'Allow non-alphanumeric characters' in answers['filename_options']
        self._current_conversion_settings._creation_time_in_exported_file_name = \
            'Include creation time in the file name' in answers['filename_options']

    def _ask_and_set_space_replacement_character(self):
        questions = [
            {
                'type': 'input',
                'name': 'filename_spaces_replaced_by',
                'message': 'Enter character(s) to replace spaces with',
                'default': self._default_settings.filename_spaces_replaced_by
            },
        ]
        answer = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.filename_spaces_replaced_by = answer['filename_spaces_replaced_by']

    def _ask_and_set_maximum_filename_length(self):
        msg = 'Enter the maximum length for file and directory names (max 255)'
        if os.name == 'nt':
            windows_long_names_text = 'Windows long path names are enabled on this computer'
            if helper_functions.are_windows_long_paths_disabled():
                windows_long_names_text = 'Windows long path names are NOT enabled on this computer'

            msg = f'Enter the maximum length for file and directory names\n{windows_long_names_text}\n(max 64 for windows without long file names enabled else, 255)'

        questions = [
            {
                'type': 'input',
                'name': 'maximum_file_or_directory_name_length',
                'message': msg,
                'default': str(self._default_settings.maximum_file_or_directory_name_length)
            },
        ]
        answer = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        if 'maximum_file_or_directory_name_length' in answer:
            self._current_conversion_settings.maximum_file_or_directory_name_length = answer['maximum_file_or_directory_name_length']

    def _ask_and_set_creation_time_in_file_name(self):
        questions = [
            {
                'type': 'confirm',
                'message': 'Include creation time in the file name',
                'name': 'creation_time_in_exported_file_name',
                'default': self._default_settings.creation_time_in_exported_file_name,
            }
        ]

        answer = prompt(questions, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        self._current_conversion_settings.creation_time_in_exported_file_name = \
            answer['creation_time_in_exported_file_name']


class InvalidConfigFileCommandLineInterface(InquireCommandLineInterface):
    """
    Command Line Interface for errors when validating an imported config.ini file
    """

    def __init__(self):
        super().__init__()

    def run_cli(self):
        return self._ask_what_to_do()

    def _ask_what_to_do(self):
        question = {
            'type': 'list',
            'name': 'what_to_do',
            'message': 'Config file is invalid, please make a choice',
            'choices': ['Create a default configuration', 'Exit program and edit config file']
        }

        answer = prompt(question, style=self.style)
        _exit_if_keyboard_interrupt(answer)
        if answer['what_to_do'] == 'Create a default configuration':
            return 'default'
        return 'exit'
