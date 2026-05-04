# -*- coding: utf-8 -*-
import json
import scanner
from azstd_py import tui

if __name__ == '__main__':
    with open('config.json', 'r') as o:
        conf = json.load(o)
    print('Root directory: ' + conf['root'])
    print('Database location: ' + conf['db_path'])
    handler = scanner.Scanner(conf['root'],
                              conf['db_path'],
                              n_thread=conf['torch_thread'],
                              gpu=conf['use_gpu'])
    opt_ope = tui.ask_input_line('Select operation:', '1-Create 2-Query')
    if opt_ope == '1':
        handler.create_tree()
        handler.create_db()
    else:
        while True:
            query = tui.ask_input_line('Input query word:')
            for ans in handler.query(query):
                print(ans[0]+'\n------\n'+ans[1]+'\n======')
