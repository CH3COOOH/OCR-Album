def ask_input_line(prompt, desc=None):
	if desc == None:
		getstr = input(prompt + '\n> ')
	else:
		getstr = input(prompt + '\n # %s\n> ' % desc)
	return getstr