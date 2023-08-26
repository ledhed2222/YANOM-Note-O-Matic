import logging
from pathlib import Path
import shutil
import sys

import file_mover
import nimbus_converter
from alive_progress import alive_bar

import config
from content_link_management import find_local_file_links_in_content, get_set_of_all_files, process_attachments
from file_converter_HTML_to_MD import HTMLToMDConverter
from file_converter_MD_to_HTML import MDToHTMLConverter
from file_converter_MD_to_MD import MDToMDConverter
import interactive_cli
from nsx_file_converter import NSXFile
from pandoc_converter import PandocConverter
import report
from timer import Timer


def what_module_is_this():
    return __name__


class NotesConvertor:
    """
    A class to direct the conversion of note files into alternative output formats.

    Uses the passed in command line arguments to direct flow to use the ini file conversion settings or the
    interactive command line interface to set the conversion settings.  Then using the conversion settings
    directs the conversion of the required source file type. Once conversion is completed a summary of the process
    is displayed.

    """

    def __init__(self, args, config_data):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self.logger.info(f'Conversion startup')
        self.command_line_args = args
        self.conversion_settings = None
        self._note_page_count = 0
        self._note_book_count = 0
        self._image_count = 0
        self._attachment_count = 0
        self._nsx_backups = []
        self.pandoc_converter = None
        self.config_data = config_data
        self._set_of_found_attachments = set()
        self._set_files_to_convert = set()
        self._orphan_files = set()
        self._encrypted_notes = []
        self._set_of_created_note_files = set()
        self._set_of_renamed_note_files = set()
        self._set_of_not_found_attachments = set()
        self._attachment_details = {}
        self._nsx_null_attachments = {}
        self._encrypted_notes = []
        self._exported_files = set()
        self._report = ''

    def convert_notes(self):
        self.evaluate_command_line_arguments()
        self.create_export_folder_if_required()

        note_formats = {
            'html': self.convert_html,
            'markdown': self.convert_markdown,
            'nsx': self.convert_nsx,
            'nimbus': self.convert_nimbus,
        }

        conversion_to_run = note_formats.get(self.conversion_settings.conversion_input, None)
        conversion_to_run()

        self.generate_results_report()
        self.logger.info("Processing Completed")

    def create_export_folder_if_required(self):
        self.conversion_settings.export_folder_absolute.mkdir(parents=True, exist_ok=True)

    def convert_markdown(self):
        with Timer(name="md_conversion", logger=self.logger.info, silent=bool(config.yanom_globals.is_silent)):
            file_extension = 'md'
            md_files_to_convert = self.generate_file_list(file_extension, self.conversion_settings.source_absolute_root)
            self.exit_if_no_files_found(md_files_to_convert, file_extension)

            if self.conversion_settings.export_format == 'html':
                md_file_converter = MDToHTMLConverter(self.conversion_settings, md_files_to_convert)
            else:
                md_file_converter = MDToMDConverter(self.conversion_settings, md_files_to_convert)

            self.process_files(md_files_to_convert, md_file_converter)

            self.handle_orphan_files_as_required()

    def handle_orphan_files_as_required(self):
        set_of_all_files = get_set_of_all_files(self.conversion_settings.source_absolute_root)
        self._orphan_files = self.get_list_of_orphan_files(set_of_all_files)
        path_to_orphans = ''

        if self.conversion_settings.orphans == 'ignore':
            return

        if self.conversion_settings.orphans == 'copy':
            path_to_orphans = Path(self.conversion_settings.export_folder_absolute)

        if self.conversion_settings.orphans == 'orphan':
            path_to_orphans = Path(self.conversion_settings.export_folder_absolute, 'orphan')

        for file in self._orphan_files:
            relative_to_source = file.relative_to(self.conversion_settings.source_absolute_root)
            new_absolute_path = Path(path_to_orphans, relative_to_source)
            new_absolute_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy2(file, new_absolute_path)

    def generate_file_list(self, file_extension, path_to_files: Path):
        if self.conversion_settings.source.is_file():
            return {self.conversion_settings.source}

        file_list_generator = path_to_files.rglob(f'*{file_extension}')
        file_list = {item for item in file_list_generator}
        return file_list

    def exit_if_no_files_found(self, files_to_convert, file_extension):
        if not files_to_convert:
            self.logger.info(
                f"No .{file_extension} files found at path {self.conversion_settings.source}. Exiting program")
            if not config.yanom_globals.is_silent:
                print(f'No .{file_extension} files found at {self.conversion_settings.source}')
            sys.exit(0)

    def process_files(self, files_to_convert, file_converter):
        self._set_files_to_convert = set(files_to_convert)
        file_count = 0
        self._attachment_count = 0

        if not config.yanom_globals.is_silent:
            print(f"Processing note pages")
            with alive_bar(len(files_to_convert), bar='blocks') as file_bar:
                for file in files_to_convert:
                    file_count = self._convert_note(file_converter, file, file_count, file_bar)

            self._note_page_count = file_count
            return

        for file in files_to_convert:
            file_count = self._convert_note(file_converter, file, file_count)
        self._note_page_count = file_count

    def _convert_note(self, file_converter, file, file_count, file_bar=None):
        file_converter.convert_note(file)
        if file_converter.renamed_note_file:
            self._set_of_renamed_note_files.add(file_converter.renamed_note_file)
        exported_file_path = file_converter.write_post_processed_content()
        self._exported_files.add(exported_file_path)
        file_count += 1

        if not self.conversion_settings.source_absolute_root == self.conversion_settings.export_folder_absolute:
            for attachment in file_converter.current_note_attachment_links.copyable_absolute:
                self._copy_attachment(attachment)

        self._attachment_details[file] = {
            'all': file_converter.current_note_attachment_links.all,
            'valid': file_converter.current_note_attachment_links.valid,
            'invalid': file_converter.current_note_attachment_links.invalid,
            'existing': file_converter.current_note_attachment_links.existing,
            'non_existing': file_converter.current_note_attachment_links.non_existing,
            'copyable': file_converter.current_note_attachment_links.copyable,
            'non_copyable_relative': file_converter.current_note_attachment_links.non_copyable_relative,
            'non_copyable_absolute': file_converter.current_note_attachment_links.non_copyable_absolute,
            'copyable_absolute': file_converter.current_note_attachment_links.copyable_absolute,
        }
        if file_bar:
            file_bar()

        return file_count

    def _copy_attachment(self, attachment):
        if attachment.exists() and attachment.is_file():
            attachment_path_relative_to_source = attachment.relative_to(
                self.conversion_settings.source_absolute_root)
            target_attachment_absolute_path = Path(self.conversion_settings.export_folder_absolute,
                                                   attachment_path_relative_to_source)

            target_attachment_absolute_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy(attachment, target_attachment_absolute_path)
        else:
            self.logger.warning(f'Unable to copy attachment "{attachment}" - It does not exist or is a directory.')

    def get_list_of_orphan_files(self, set_of_all_files):
        orphans = set_of_all_files
        for file, attachments in self._attachment_details.items():
            orphans = orphans \
                      - self._set_files_to_convert \
                      - set(self._exported_files) \
                      - attachments['copyable_absolute'] \
                      - attachments['non_copyable_absolute'] \
                      - self._set_of_renamed_note_files

        return orphans

    def convert_html(self):
        with Timer(name="html_conversion", logger=self.logger.info, silent=bool(config.yanom_globals.is_silent)):
            file_extension = 'html'
            html_files_to_convert = self.generate_file_list(file_extension,
                                                            self.conversion_settings.source_absolute_root)
            self.exit_if_no_files_found(html_files_to_convert, file_extension)
            html_file_converter = HTMLToMDConverter(self.conversion_settings, html_files_to_convert)
            self.process_files(html_files_to_convert, html_file_converter)
            self.handle_orphan_files_as_required()

    def convert_nsx(self):
        file_extension = 'nsx'
        nsx_files_to_convert = self.generate_file_list(file_extension, self.conversion_settings.source_absolute_root)
        self.exit_if_no_files_found(nsx_files_to_convert, file_extension)
        self.pandoc_converter = PandocConverter(self.conversion_settings)
        self._nsx_backups = [NSXFile(file, self.conversion_settings, self.pandoc_converter)
                             for file in nsx_files_to_convert]
        self.process_nsx_files()
        self.check_nsx_attachment_links()

    def convert_nimbus(self):
        with Timer(name="nsx_conversion", logger=self.logger.info, silent=bool(config.yanom_globals.is_silent)):
            file_extension = 'zip'
            nimbus_files_to_convert = self.generate_file_list(file_extension,
                                                              self.conversion_settings.source_absolute_root)

            self.exit_if_no_files_found(nimbus_files_to_convert, file_extension)

            num_images, num_attachments = nimbus_converter.convert_nimbus_notes(self.conversion_settings,
                                                                                nimbus_files_to_convert)

            self._note_page_count = len(nimbus_files_to_convert)
            self._image_count = num_images
            self._attachment_count = num_attachments

    def process_nsx_files(self):
        with Timer(name="nsx_conversion", logger=self.logger.info, silent=bool(config.yanom_globals.is_silent)):
            for nsx_file in self._nsx_backups:
                nsx_file.process_nsx_file()
                self.update_processing_stats(nsx_file)
                self._nsx_null_attachments.update(nsx_file.null_attachments)
                self._encrypted_notes += nsx_file.encrypted_notes
                self._exported_files.update(nsx_file.exported_notes)

    def check_nsx_attachment_links(self):
        if not config.yanom_globals.is_silent:
            print(f"Analysing note page links")
        notes_to_check = self.generate_file_list(file_mover.get_file_suffix_for(self.conversion_settings.export_format),
                                                 self.conversion_settings.export_folder_absolute
                                                 )
        if not config.yanom_globals.is_silent:
            with alive_bar(len(notes_to_check), bar='blocks') as bar:
                for note in notes_to_check:
                    self._nsx_attachment_checks(note, notes_to_check, self.conversion_settings.skip_attachment_checks, bar)
            return

        for note in notes_to_check:
            self._nsx_attachment_checks(note, notes_to_check, self.conversion_settings.skip_attachment_checks)

    def _nsx_attachment_checks(self, note, notes_to_check, skip_checks, bar=None):
        error_mode = 'ignore' if skip_checks else 'strict'
        content = None
        try:
            content = note.read_text(encoding='utf-8', errors=error_mode)
        except UnicodeDecodeError:
            print(f"\nNote {note} has error. Try again with loose error checking if you like\n")
            exit(1)

        all_attachments_paths = find_local_file_links_in_content(self.conversion_settings.export_format,
                                                                 content)

        attachment_links = process_attachments(note,
                                               all_attachments_paths,
                                               notes_to_check,
                                               self.conversion_settings.export_folder_absolute
                                               )

        self._attachment_details[note] = {
            'all': attachment_links.all,
            'valid': attachment_links.valid,
            'invalid': attachment_links.invalid,
            'existing': attachment_links.existing,
            'non_existing': attachment_links.non_existing,
            'copyable': attachment_links.copyable,
            'copyable_absolute': attachment_links.copyable_absolute,
            'non_copyable_relative': attachment_links.non_copyable_relative,
            'non_copyable_absolute': attachment_links.non_copyable_absolute,
        }

        if bar:
            bar()

    def update_processing_stats(self, nsx_file):
        self._note_page_count += nsx_file.note_page_count
        self._note_book_count += nsx_file.note_book_count
        self._image_count += nsx_file.image_count
        self._attachment_count += nsx_file.attachment_count

    def evaluate_command_line_arguments(self):
        self.configure_for_ini_settings()

        if self.command_line_args['source']:
            self.conversion_settings.source = self.command_line_args['source']

        if self.command_line_args['export']:
            self.conversion_settings.export_folder = self.command_line_args['export']

        if self.command_line_args['silent'] or self.command_line_args['ini']:
            return

        self.logger.debug("Starting interactive command line tool")
        self.run_interactive_command_line_interface()

    def run_interactive_command_line_interface(self):
        command_line_interface = interactive_cli.StartUpCommandLineInterface(self.conversion_settings)
        self.conversion_settings = command_line_interface.run_cli()
        self.config_data.conversion_settings = self.conversion_settings  # this will save the setting in the ini file
        self.logger.info("Using conversion settings from interactive command line tool")

    def configure_for_ini_settings(self):
        self.logger.info("Using settings from config  ini file")
        self.conversion_settings = self.config_data.conversion_settings

    def generate_results_report(self):
        report_generator = report.Report(self)
        report_generator.generate_report()
        report_generator.save_results()
        report_generator.output_results_if_not_silent_mode()
        report_generator.log_results()

    @staticmethod
    def print_result_if_any(conversion_count, message):
        if conversion_count == 0:
            return
        plural = ''
        if conversion_count > 1:
            plural = 's'
        print(f'{conversion_count} {message}{plural}')

    @property
    def nsx_backups(self):
        return self._nsx_backups

    @property
    def attachment_count(self):
        return self._attachment_count

    @property
    def image_count(self):
        return self._image_count

    @property
    def note_page_count(self):
        return self._note_page_count

    @property
    def note_book_count(self):
        return self._note_book_count

    @property
    def orphan_files(self):
        return self._orphan_files

    @property
    def attachment_details(self):
        return self._attachment_details

    @property
    def nsx_null_attachments(self):
        return self._nsx_null_attachments

    @property
    def encrypted_notes(self):
        return self._encrypted_notes
