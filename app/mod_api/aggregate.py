aggregator_docs = {"description": "An aggregation function for processing other functions",
		   "doc_href":"None",
		   "methods":["GET", "POST"],
		   "name":"aggregator",
		   "parameters":{"arguments":{
			"function":{},
			"iterable":{}, 
			"iterable_argument":{}},
		   "server":[]},
		   "status":"success"}

def aggregator(func, iterable, iterable_argument, *args, **kwargs):
	iterable_response = {}
    	for i in iterable:
	    args.append(i)
	    response = func(args, kwargs)
	    
	pass
