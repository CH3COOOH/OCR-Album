import easyocr
import torch
import warnings

warnings.filterwarnings('ignore')

class OCRFactory:
	def __init__(self, n_thread=2, gpu=False):
		self.reader = easyocr.Reader(
			['ch_sim', 'en'],
			gpu=gpu,
			download_enabled=False,
			verbose=False,
			model_storage_directory='./models'
		)
		torch.set_num_threads(n_thread)
	
	def img2Text(self, img_path):
		r = self.reader.readtext(img_path, paragraph=False)
		# print(r)
		s = []
		for fo in r:
			s.append(fo[1])
		return ''.join(s)

if __name__ == '__main__':
	import sys
	pth = sys.argv[1]
	ocr = OCRFactory()
	print(ocr.img2Text(pth))