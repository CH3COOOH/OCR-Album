from azstd_py import afile
import pathdb
import ocr

class Scanner:
    def __init__(self, dir_root, db_fname, n_thread, gpu):
        self.root = dir_root
        self.n_thread = n_thread
        self.gpu = gpu
        self.db = pathdb.PathDB(fname=db_fname)
        self.ocr = None
        self.tree = None

    def create_tree(self):
        self.tree = afile.fileLstMaker(self.root, filter_=['.jpg', '.JPG', '.png', '.PNG'])
        return self.tree
    
    def create_db(self, batch_size=10):
        if self.ocr == None:
            self.ocr = ocr.OCRFactory(n_thread=self.n_thread, gpu=self.gpu)
        batch = []
        n_files = len(self.tree)
        n_record = 0
        for img in self.tree:
            n_record += 1
            print(f"Reading: {n_record}/{n_files}")
            text = self.ocr.img2Text(img)
            if text == '':
                continue
            if batch_size == 1:
                if self.db.add_record(img, text) != 0:
                    print('**Unable to insert record: ' + img)
                continue
            batch.append([img, text])
            if len(batch) == batch_size:
                if self.db.add_records(batch) != 0:
                    print('**Unable to insert batch')
                batch = []
        if len(batch) != 0:
            if self.db.add_records(batch) != 0:
                print('**Unable to insert batch')
        return 0
    
    def query(self, keyword):
        return self.db.search_by_text(keyword)

if __name__ == '__main__':
    dbh = Scanner('test_img', 'testimgdb.db')
    print(dbh.create_tree())
    print(dbh.create_db())
    print(dbh.query('哈耶克'))