# -*- coding: utf-8 -*-
from azstd_py import lowestdb

class PathDB:
    def __init__(self, fname='index.db'):
        self.db = lowestdb.LowestDB([('OCR_TXT', 'TEXT')], db_fname=fname, table_name='IMG_PATH')

    def add_record(self, img_path, text):
        return self.db.insert_row(img_path, [text])
    
    def add_records(self, path_text_matrix):
        return self.db.insert_rows(path_text_matrix)
    
    def search_by_text(self, keyword):
        return self.db.extract_rows_by_keyword('OCR_TXT', keyword)

if __name__ == '__main__':
    db = PathDB()
    print(db.add_record('xxx.jpg', '你好世界'))
    print(db.add_records([
        ['xxa.jpg', '地球毁灭'],
        ['xxb.jpg', '人类灭绝']
        ])
    )
    print(db.search_by_text('灭'))
