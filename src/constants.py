from os import path
from traceback import print_exc

from toolkit.fileutils import Fileutils
from toolkit.logger import Logger

O_FUTL = Fileutils()
S_DATA = '../data/'
S_LOG = S_DATA + 'log.txt'
S_SYM = '../factory/symbols.yml'

logging = Logger(10)

if not O_FUTL.is_file_exists(S_LOG):
    logging.info('creating data dir')
    O_FUTL.add_path(S_LOG)
    ce_path = S_DATA + 'CE/ce.txt'
    O_FUTL.is_mk_filepath(ce_path)
    pe_path = S_DATA + 'PE/pe.txt'
    O_FUTL.is_mk_filepath(pe_path)
elif O_FUTL.is_file_not_2day(S_LOG):
    O_FUTL.nuke_file(S_LOG)


def yml_to_obj(arg=None):
    try:
        if not arg:
            parent = path.dirname(path.abspath(__file__))
            logging.debug(f'{parent=}')
            grand_parent_path = path.dirname(parent)
            logging.debug(f'{grand_parent_path=}')
            folder = path.basename(grand_parent_path)
            lst = folder.split('_')
            file = '-'.join(reversed(lst))
            file = '../../' + file + '.yml'
        else:
            file = S_DATA + arg

        flag = O_FUTL.is_file_exists(file)

        if not flag and arg:
            logging.info(f'using default {file=}')
            O_FUTL.copy_file('../factory/', '../data/', 'settings.yml')
        elif not flag and arg is None:
            logging.error(f'fill the {file=} file and try again')
            __import__('sys').exit()
    except Exception as e:
        logging.error(e)
        print_exc()
        __import__('sys').exit(1)
    else:
        return O_FUTL.get_lst_fm_yml(file)


D_SYMBOL = O_FUTL.get_lst_fm_yml(S_SYM)
logging.info('symbols\n*****************')


def set_logger():
    try:
        O_SETG = yml_to_obj('settings.yml')
        if O_SETG.get('log', None):
            level = O_SETG['log'].get('level', 10)
            if not O_SETG['log'].get('show', None):
                return Logger(level)
            else:
                lg = Logger(level, S_LOG)
                for h in lg.handlers:
                    h.setLevel(level)
                return lg
        return Logger(10)
    except Exception as e:
        logging.error(f'set logger error: {e}')
        print_exc()
        __import__('sys').exit(1)


logging = set_logger()