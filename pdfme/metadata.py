
from typing import Literal

class PDFMetadata:
    '''Represents a PDF Metadata

    This class implements PDF's Extensible Metadata
    Platform (XPM) interface for representing a document's 
    metadata.
    '''

    def __init__(self) -> None:
        self.nss = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'pdf': 'http://ns.adobe.com/pdf/1.3/',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'xmp': 'http://ns.adobe.com/xap/1.0/',
            'x': 'adobe:ns:meta/'
       }
        self.metadata = {}

        self.XMP_PACKET_ID = 'W5M0MpCehiHzreSzNTczkc9d'

    def xmp_packet(self, writable: bool = True):
        '''Wraps all metadata information as an XMP packet.

        Args:
            writable (bool): Whether the metadata is read-only or not.

        Returns:
            bytes: The XMP packet as bytes.
        '''
        
        body = '\n'.join(self.metadata.values())
        xmp = (
            f'<?xpacket begin="" id="{self.XMP_PACKET_ID}"?>'
            f'<x:xmpmeta xmlns:x="{self.nss["x"]}">'
            f'<rdf:RDF xmlns:rdf="{self.nss["rdf"]}">'
            f'<rdf:Description '
            f'xmlns:dc="{self.nss["dc"]}" '
            f'xmlns:pdf="{self.nss["pdf"]}" '
            f'xmlns:xmp="{self.nss["xmp"]}" '
            f'about="">'
            f'{body}'
            f'</rdf:Description>'
            f'</rdf:RDF>'
            f'</x:xmpmeta>'
            f'{" " * 2000}'
            f'<?xpacket end="{"w" if writable else "r"}">'
        )

        return xmp.encode('latin')

    def _add_rdf_array(self, _type: Literal['alt', 'seq', 'bag'], contents: list):
        '''Creates an RDF Array

        Args:
            _type (str): The type of array to create.
            contents (list): The entries of this array.

        Returns:
            (str): The created array.
        '''

        entries = [
            '<rdf:li>' + 
            item + '</rdf:li>' for item in contents
        ]
        tag_name = _type.capitalize()
        tag = (
            f'<rdf:{tag_name}>\n' + '\n'.join(entries) + f'</rdf:{tag_name}>\n'
        )
        return tag

    def _add_tag(self, entry_name, entry):
        '''
        Creates an XML tag.

        Args:
            entry_name (str): Tag name.
            entry (str): Tag content.

        Returns:
            (str): The created tag.
        '''
        return f'<{entry_name}>{entry}</{entry_name}>'

    def add_title(self, title: str):
        '''
        Add document title.

        Args:
            title (str): The document title.
        '''
        rdf_entry = self._add_rdf_array('alt', [title])
        dc_title = self._add_tag('dc:title', rdf_entry)
        self.metadata['title'] = dc_title

    def add_creator(self, author: list):
        '''
        Add document authors.

        Args:
            creators (list): The document creators.

        Raises:
            ValueError:
        '''
        if not author:
            return

        if not isinstance(author, list):
            raise ValueError(
                'Metadata Error: "author" must be of type "list". Got type '
                '{_type}'.format(_type=type(creators))
                )

        rdf_entry = self._add_rdf_array('seq', author)
        dc_creator = self._add_tag('dc:creator', rdf_entry)
        self.metadata['creator'] = dc_creator

    def add_description(self, description: str):
        '''
        Add document description.

        Args:
            description (str): The document description.
        '''
        rdf_desciption = self._add_rdf_array('alt', [description])
        dc_description = self._add_tag('dc:description', rdf_desciption)
        self.metadata['description'] = dc_description

    def add_subject(self, subject: list):
        '''
        Add document subject.

        Args:
            subject (list): The subjects for the document.

        Raises:
            ValueError:
        '''
        if not subject:
            return

        if not isinstance(subject, list):
            raise ValueError(
                'Metadata Error: "subject" must be of type "list". Got type {_type}'.format(
                    _type=type(subject))
                    )

        rdf_subject = self._add_rdf_array('bag', subject)
        dc_subject = self._add_tag('dc:subject', rdf_subject)
        self.metadata['subject'] = dc_subject

    def add_producer(self, name: str):
        '''
        Add document producer.

        Args:
            name (str): The framework creating the document.
        '''
        producer = self._add_tag('pdf:Producer', name)
        self.metadata['producer'] = producer

    def add_create_date(self, datetime_iso: str):
        '''
        Add document creation date.

        Args:
            datetime_iso (str): The date/time at which the document was 
                created in ISO format.
        '''
        datetime_entry = self._add_tag('xmp:CreateDate', datetime_iso)
        self.metadata['create_date'] = datetime_entry
        self.add_modify_date(datetime_iso)

    def add_modify_date(self, datetime_iso: str):
        '''
        Add document modify date.

        Args:
            datetime_iso (str): The date/time at which the document was 
                modified in ISO format.
        '''
        datetime_entry = self._add_tag('xmp:ModifyDate', datetime_iso)
        self.metadata['modify_date'] = datetime_entry

    def add_language(self, language: str = 'en'):
        '''
        Add document language

        Args:
            language (str): The document language. Defaults to English 
                Language.
        '''
        rdf_lang = self._add_rdf_array('bag', [language])
        dc_language = self._add_tag('dc:language', rdf_lang)
        self.metadata['language'] = dc_language

    def add_create_tool(self, name: str):
        '''
        Add document creation tool 

        Args:
            name (str): The application responsible for creating the document.
        '''
        create_tool = self._add_tag('xmp:CreateTool', name)
        self.metadata['create_tool'] = create_tool

