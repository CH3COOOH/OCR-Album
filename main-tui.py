# -*- coding: utf-8 -*-
import dbhandler
from azstd_py import tui

if __name__ == '__main__':
    root = tui.ask_input_line('Root directory:')
    handler = dbhandler.DBHandler(root, 'local.db')
    opt_ope = tui.ask_input_line('Select operation:', '1-Create 2-Query')
    if opt_ope == '1':
        handler.create_tree()
        handler.create_db()
    else:
        while True:
            query = tui.ask_input_line('Input query word:')
            for ans in handler.query(query):
                print(ans[0]+'\n------\n'+ans[1]+'\n======')
