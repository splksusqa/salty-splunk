def installed(name, **kwargs):
	'''
	'''
	__salt__['splunk.install'](**kwargs)
	comment = "Splunk is installed"
	return {'name': name, 'changes': {}, 'result': True, 'comment': comment}