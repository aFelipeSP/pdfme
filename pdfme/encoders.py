import zlib

def encode_stream(stream, filter, parameters = {}):
	if filter == b'/FlateDecode':
		return flate_encode(stream)
	elif filter == b'/ASCIIHexDecode':
		raise NotImplementedError('/ASCIIHexDecode')
	elif filter == b'/ASCII85Decode':
		raise NotImplementedError('/ASCII85Decode')
	elif filter == b'/LZWDecode':
		raise NotImplementedError('/LZWDecode')
	elif filter == b'/RunLengthDecode':
		raise NotImplementedError('/RunLengthDecode')
	elif filter == b'/CCITTFaxDecode':
		raise NotImplementedError('/CCITTFaxDecode')
	elif filter == b'/JBIG2Decode':
		raise NotImplementedError('/JBIG2Decode')
	elif filter == b'/DCTDecode':
		raise NotImplementedError('/DCTDecode')
	elif filter == b'/JPXDecode':
		raise NotImplementedError('/JPXDecode')
	elif filter == b'/Crypt':
		raise NotImplementedError('/Crypt')

def flate_encode(stream):
    return zlib.compress(stream)

