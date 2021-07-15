import zlib

def encode_stream(stream: bytes, filter: bytes, parameters: dict=None) -> bytes:
	"""Function to use ``filter`` method to encode ``stream``, using
	``parameters`` if required.

	Args:
		stream (bytes): the stream to be encoded.
		filter (bytes): the method to use for the encoding process.
		parameters (dict, optional): if necessary, this dict contains the
			parameters required by the ``filter`` method.

	Raises:
		NotImplementedError: if the filter passed is not implemented yet.
		Exception: if the filter passed doesn't exist.

	Returns:
		bytes: the encoded stream.
	"""
	if parameters is None:
		parameters = {}

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
	else:
		raise Exception("Filter {} not found".format(filter.decode('latin')))

def flate_encode(stream: bytes) -> bytes:
	"""Function that encodes a bytes stream using the zlib.compress method.

	Args:
		stream (bytes): stream to be encoded.

	Returns:
		bytes: the encoded stream.
	"""
	return zlib.compress(stream)

