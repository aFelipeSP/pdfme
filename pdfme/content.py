from typing import Optional, Union

TABLE_PROPERTIES = ('widths', 'borders', 'fills')
PARAGRAPH_PROPERTIES = (
    'text_align', 'line_height', 'indent',
    'list_text', 'list_style', 'list_indent'
)

Number = Union[float, int]
StrOrDict = Union[str, dict]
ProcessElement = Union[str, list, tuple, dict]
class PDFContent:
    """This class represents a group of elements (paragraphs, images, tables)
    to be added to a :class:`pdfme.pdf.PDF` instance; what is called a "content
    box" in this library.

    This class receives as the first argument a dict representing the
    layout of the elements that are going to be added to the PDF.
    This dict must have a ``content`` key with a tuple or a list as its
    value, containing the elements to be added.

    The elements are arranged by using method ``run`` from top to bottom, and
    from left to right in order, in the rectangle defined by args ``x``, ``y``,
    ``width`` and ``height``. The elements are added to this rectangle, until
    they are all inside of it, or until all of the vertical space is used and
    the rest of the elements can not be added. In these two cases method ``run``
    finishes,  and the property ``finished`` will be True if all the elements
    were added, and False if the vertical space ran out.
    If ``finished`` is False, you can set a new rectangle (on a new page for
    example) and use method ``run`` again (passing the parameters of the new
    rectangle) to add the remaining elements that couldn't be added in
    the last rectangle. You can keep doing this until all of the elements are
    added and therefore property ``finished`` is True.

    By using method ``run`` the elements are not really added to the PDF object.
    After calling ``run``, the properties ``fills`` and ``lines`` will be
    populated with the fills and lines of the tables that fitted inside the
    rectangle, and ``parts`` will be filled with the paragraphs and images that
    fitted inside the rectangle too, and you have to add them by yourself to
    the PDF object before using method ``run`` again (in case ``finished`` is
    False), because they will be redefined for the next rectangle after calling
    it again. You can check the ``content`` method in `PDF`_ module to see how
    this process is done.

    This process of creating new pages to fit all of the elements of a content
    box is done automatically when you use :class:`pdfme.document.PDFDocument`
    or ::func:`pdfme.document.build_pdf`

    A ``cols`` key with a dict as a value can be included to arrange the
    elements in more than one column. For example, to use 2 columns, and to set
    a gap space between the 2 columns of 20 points, a dict like this one can be
    used:

    .. code-block:: python

        {
            'cols': {'count': 2, 'gap': 20},
            'content': ['This is a lot of text ...'],
        }

    The elements in the ``content`` list can be one of the following:

    * A paragraph that can be a string, a list, a tuple or a dictionary with a
      key starting with a ``.``. To know more about paragraphs check
      :class:`pdfme.text.PDFText`. Additional to the keys that can be included
      inside ``style`` key of a paragraph dict like the one you pass to
      :class:`pdfme.text.PDFText`, you can include the following too:
      ``text_align``, ``line_height``, ``indent``, ``list_text``, ``list_style``
      and ``list_indent``. For information about these attributes check
      :class:`pdfme.text.PDFText`. Here is an example of a paragraph dict:

      .. code-block:: python

        {
            'style': {
                'text_align': 'j',
                'line_height': 1.5,
                'list_text': '1. ',
            },
            '.b': 'This is a bold text.'
        }

      This paragraph dict yields a justified paragraph with a line height of 1.5
      times the original line height and with a **1** on the left of the
      paragraph.

    * An image that should be a dict with a ``image`` key, holding the path of
      the image, or the bytes of the image. In case ``image`` is of type bytes
      two more keys should be added to this dict: ``image_name`` and
      ``extension``, being the first a unique name for the image and the second
      the extension or format of the image (ex. "jpg"). This dict can have a
      ``style`` dict, to tell this class what should it do when an image don't
      fit a column through the key ``image_place``. This attribute can be
      "normal" or "flow"(default) and both of them will take the image to the
      next column or rectangle, but the second one will try to accommodate the
      elements coming after the image to fill the space left by it.
      Here is an example of an image dict:

      .. code-block:: python

        {
            'style': { 'image_place': 'flow' },
            'image': '/path/to/an/image.jpg'
        }

    * A table that should be a dict with a ``table`` key with the table data,
      and optionally any or all of the following keys: ``widths``, ``borders``
      and ``fills``. To know more about these keys check their meaning in
      :class:`pdfme.table.PDFTable`.
      Here is an example of a table dict:

      .. code-block:: python

        {
            'table': [['col1', 'col2', 'col3'], ['value1', 'value2', 'value3']],
            'widths': [1,2,3],
            'borders': [{'pos': 'h0,1,3;:', 'width': 2, 'color': 0}]
        }

    * A content box that can be a dict like the one being explained here, and
      can contain other elements inside it recursively. This can be used to
      insert a new section with more columns (for example a 2 columns content
      box, inside another 2 columns content box).

    * A group element that is a list of paragraphs, images or tables that should
      be placed all in the same page. This can be used for example to place an
      image with a description, with the guarantee that both will be in the same
      page. Be careful though, because the group element should fit the
      width and max height of the containing box, or else an error will be
      raised. This can be "relaxed" by setting ``min_height`` property style in
      the images inside the group. If an image does not have this property it
      will take as much space as possible, and if it does it will be shrinked as
      much as possible (without shrinking it beyond ``min_height``) to make the
      other elements in the group fit in the available height. If there are more
      than one images in the group with ``min_height`` style property they will
      be shrinked together proportionally. If you want to ensure that some image
      will be shrinked until its ``min_height``, use the ``shrink`` style
      property.
      Here is an example of a group element:

      .. code-block:: python

        {
            "style": {"margin_left": 80, "margin_right": 80},
            "group": [
                {"image": "tests/image_test.jpg", "min_height": 200},
                {".": "Figure 1: Description of figure 1"}
            ]
        }

    Each element in the content box can have margins to keep it separated from
    the other elements, and these margins can be set inside the ``style`` dict
    of the content box dict with the following keys: ``margin_top``,
    ``margin_left``, ``margin_bottom`` and ``margin_right``. Default value for
    all of them is 0, except for ``margin_bottom`` that have a default value of
    5.

    All of the children elements in the content box will inherit the
    the content box style.

    Args:
        content (dict): A content dict.
        fonts (PDFFonts): A PDFFonts object used to build paragraphs.
        x (int, float): The x position of the left of the rectangle.
        y (int, float): The y position of the top of the rectangle.
        width (int, float): The width of the rectangle where the contents will
            be arranged.
        height (int, float): The height of the rectangle where the contents will
            be arranged.
        pdf (PDF, optional): A PDF object used to get string styles inside the
            elements.

    Raises:
        TypeError: if ``content`` is not a dict

    .. _PDF: https://github.com/aFelipeSP/pdfme/blob/main/pdfme/pdf.py
    """

    def __init__(
        self, content: dict, fonts: 'PDFFonts', x: Number, y: Number,
        width: Number, height: Number, pdf: 'PDF'=None
    ) -> None:
        if not isinstance(content, dict):
            raise TypeError('content must be a dict: {}'.format(content))

        self.content = content
        self.finished = False
        self.pdf_content_part = None
        self.setup(x, y, width, height)
        self.fonts = fonts
        self.current_height = 0
        self.pdf = pdf

    def setup(
        self, x: Number=None, y: Number=None, width: Number=None,
        height: Number=None
    ) -> None:
        """Function to change any or all of the parameters of the rectangle of
        the content.

        Args:
            x (int, float, optional): The x coordinate of the left of the
                rectangle.
            y (int, float, optional): The y coordinate of the top of the
                rectangle.
            width (int, float, optional): The width of the rectangle where the
                contents will be arranged.
            height (int, float, optional): The height of the rectangle where the
                contents will be arranged.
        """
        if x is not None:
            self.x = x
        if y is not None:
            self.min_y = y
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height

        self.max_y = self.min_y - self.height

    def run(
        self, x: Number=None, y: Number=None, width: Number=None,
        height: Number=None
    ) -> None:
        """Function to arrange this object elements in the rectangle defined by
        x, y, width and height.

        More information about this method in this class definition.

        Args:
            x (int, float, optional): The x position of the left of the
                rectangle.
            y (int, float, optional): The y position of the top of the
                rectangle.
            width (int, float, optional): The width of the rectangle where the
                contents will be arranged.
            height (int, float, optional): The height of the rectangle where the
                contents will be arranged.
        """
        self.setup(x, y, width, height)
        self.fills = []
        self.lines = []
        self.parts = []
        content_part = self.pdf_content_part
        if content_part is None:
            self.pdf_content_part = content_part = PDFContentPart(
                self.content, self, self.x, self.width, self.min_y, self.max_y,
                last=True
            )
        else:
            content_part.setup(self.x, self.width, self.min_y, self.max_y)

        ret = content_part.run()
        self.current_height = content_part.min_y - (
            content_part.max_y if content_part.cols_n > 1 else content_part.y
        )
        if ret == 'continue':
            self.finished = True

    def get_state(self) -> dict:
        """Method to get the current state of this content box. This can be used
        later in method :meth:`pdfme.content.PDFContent.set_state` to restore
        this state in this content box (like a checkpoint in a videogame).

        Returns:
            dict: a dict with the state of this content box.
        """
        return self.pdf_content_part.get_state()

    def set_state(
        self, section_element_index: int=None, section_delayed: list=None,
        children_memory: list=None
    ) -> None:
        """Method to set the state of this content box.

        The 3 arguments of this method define the current state of this content
        box, and with this method you can change that state.

        Args:
            section_element_index (int, optional): the index of the current
                element being added.
            section_delayed (list, optional): a list of delayed elements, that
                should be added before continuing with the rest of elements.
            children_memory (list, optional): if the current element is in turn
                a content box, this list says what the indexes of the nested
                content boxes inside this content box are.
        """
        self.pdf_content_part.set_state(
            section_element_index, section_delayed, children_memory
        )
class PDFContentPart:
    """Class that represent a content element.

    This class has all the logic to arrange the content elements in the
    rectangle defined by ``min_x`` (left), ``min_y`` (top), ``width`` and
    ``max_y`` (bottom). This class needs a reference to a
    :class:`pdfme.content.PDFContent` that will store the information
    of the ``lines``, ``fills`` and ``parts`` of the elements arranged by
    this class, and all of the children ``PDFContentPart`` 's of this object.
    The description of the ``content`` argument is the same that the one
    from :class:`pdfme.content.PDFContent`.

    Args:
        content (dict): A content dict.
        pdf_content (PDFContent): To store the ``fills``, ``lines`` and
            ``parts`` of the elements of the content.
        min_x (int, float): The x position of the left of the rectangle.
        width (int, float): The width of the rectangle where the
            contents will be arranged.
        min_y (int, float): The y position of the top of the rectangle.
        max_y (int, float): The y position of the bottom of the rectangle.
        parent (PDFContentPart, optional): If not None, this is the parent
            of the current object, and it's needed because the arranging process
            made by this object affects the parent arranging process and
            viceversa.
        last (bool, optional): This tells whether this is the last element
            of the list of elements of the parent. Defaults to False.
        inherited_style (dict, optional): The accumulated styles of all of
            the ancestors of the current object.

    Raises:
        TypeError: If content is not a dict
    """
    def __init__(
            self, content: dict, pdf_content: PDFContent, min_x: Number,
            width: Number, min_y: Number, max_y: Number,
            parent: 'PDFContentPart'=None, last: bool=False,
            inherited_style: dict=None
        ) -> None:
        self.p = pdf_content
        self.parent = parent
        self.is_root = parent is None
        self.last = last

        if not isinstance(content, dict):
            raise TypeError(
                '"content" arg must be a dict:'.format(content)
            )

        self.style = {'margin_bottom': 5}
        inherited_style = {} if inherited_style is None else inherited_style
        self.style.update(inherited_style)
        self.style.update(process_style(content.get('style'), self.p.pdf))

        self.column_info = content.get('cols', {})

        if not isinstance(self.column_info, dict):
            raise TypeError(
                '"cols" in content dict must be a dict:'.format(self.column_info)
            )
        self.elements = content.get('content', [])

        self.section_element_index = 0  # index when the last section jump occured
        self.section_delayed = []  # delayed elements when the last section jump occured
        self.children_memory = []  # the last state of this element
        self.partial_children_memory = None

        self.setup(min_x, width, min_y, max_y)

    def setup(
        self, min_x: Number, width: Number, min_y: Number, max_y: Number
    ) -> None:
        """Function to update the rectangle of this element.

        Args:
            min_x (int, float): The x position of the left of the rectangle.
            width (int, float): The width of the rectangle where the
                contents will be arranged.
            min_y (int, float): The y position of the top of the rectangle.
            max_y (int, float): The y position of the bottom of the rectangle.
        """
        self.min_x = min_x
        self.min_y = min_y
        self.go_to_beginning()

        self.full_width = width
        self.max_y = max_y
        self.max_height = self.y - self.max_y
        self.last_bottom = 0

        self.cols_n = self.column_info.get('count', 1)
        self.cols_gap = self.column_info.get('gap', max(width / 25, 7))
        cols_spaces = self.cols_gap * (self.cols_n - 1)
        self.col_width = (width - cols_spaces) / self.cols_n

        self.element_index = self.section_element_index # current index
        self.delayed = copy(self.section_delayed) # current delayed elements
        self.will_reset = False
        self.resetting = False
        self.parts_index = len(self.p.parts)

        self.minim_diff_last = None
        self.minim_diff = None
        self.minim_forward = None

    def get_state(self) -> dict:
        """Method to get the current state of this content box. This can be used
        later in method :meth:`pdfme.content.PDFContentPart.set_state` to
        restore this state in this content box (like a checkpoint in a
        videogame).

        Returns:
            dict: a dict with the state of this content box.
        """
        return {
            'section_element_index': self.section_element_index,
            'section_delayed': copy(self.section_delayed),
            'children_memory': copy(self.children_memory)
        }

    def set_state(
        self, section_element_index: int=None, section_delayed: list=None,
        children_memory: list=None
    ) -> None:
        """Method to set the state of this content box part.

        The arguments of this method define the current state of this content
        box part, and with this method you can change that state.

        Args:
            section_element_index (int, optional): the index of the current
                element being added.
            section_delayed (list, optional): a list of delayed elements, that
                should be added before continuing with the rest of elements.
            children_memory (list, optional): if the current element is in turn
                a content box, this list says what the indexes of the nested
                content boxes inside this content box are.
        """
        self.section_element_index = section_element_index
        self.section_delayed = copy(section_delayed)
        self.children_memory = copy(children_memory)

    def add_delayed(self) -> str:
        '''Function to add the delayed elements to the rectangle.

        This function will try to add the delayed elements to the rectangle
        and it will return a string telling what the main loop should do,
        depending on what happened with the elements when they were being added
        to the rectangle.

        Returns:
            any of the strings mentioned in
            :meth:`pdfme.content.PDFContentPart.add_elements`.
        '''
        n = 0
        while n < len(self.delayed):
            ret = self.process(copy(self.delayed[n]), False)
            if ret in ['interrupt', 'break', 'partial_next']:
                return ret

            if ret.get('delayed'):
                self.delayed[n] = copy(ret['delayed'])
            else:
                self.delayed.pop(n)

            if ret.get('next', False):
                return 'next'

            if ret.get('flow', False):
                n += 1

        if (
            len(self.delayed) > 0 and
            self.element_index >= len(self.elements) - 1
        ):
            return 'next'

        return 'continue'

    def add_elements(self) -> str:
        '''Function to add the elements in content to the rectangle.

        This function will try to add the elements to the rectangle
        and it will return a string telling what the main loop should do,
        depending on what happened with the elements when they were being added
        to the rectangle.

        Returns:
            * ``'interrupt'`` means this element or one of its children reached
              the end of the rectangle of this element's root ancestor, or what
              is the same, this element's :class:`pdfme.content.PDFContent`
              instance (the one saved in ``pdf_content`` attribute). This
              message will propagate to the ancestors until it reach the root
              ancestor and make the ``pdf_content`` to end running. After that
              the user should set a new rectangle, maybe in a new page, and call
              the :meth:`pdfme.content.PDFContent.run` function again to
              keep adding the remaining elements that couldn't be added before.

            * ``'break'`` means an ancestor is resetting and this element should
              stop adding elements.

            * ``'partial_next'`` means an ancestor has some remaining elements
              that need to be added and this element should stop.

            * ``'next'`` means that this element needs to move to the next
              section, to continue adding elements to the rectangle. The next
              section could be the next column of this element, or the next
              section of the parent.

            * ``'continue'`` means this element is done adding all of the
              elements (there could be delayed elements still).

        '''
        len_elems = len(self.elements) - 1
        while self.element_index <= len_elems:
            last = self.element_index == len_elems
            ret = self.process(self.elements[self.element_index], last=last)
            if ret in ['interrupt', 'break', 'partial_next']:
                return ret

            self.element_index += 1
            if ret.get('delayed'):
                self.delayed.append(ret['delayed'])

            if ret.get('next', False):
                return 'next'

        return 'continue'

    def is_element_resetting(self) -> str:
        """Function that returns a string depending on whether this element
        is resetting or not.

        Returns:
            A string telling the main loop what should do next.
        """

        if self.will_reset or self.resetting:
            continue_reset = self.reset()
            return 'retry' if continue_reset else 'continue'
        else:
            return 'break'

    def process_add_ans(self, ans: str) -> str:
        """Function that process the answers from methods
        :meth:`pdfme.content.PDFContentPart.add_delayed` and
        :meth:`pdfme.content.PDFContentPart.add_elements`.

        Args:
            ans (str): Any of the strings described in
                :meth:`pdfme.content.PDFContentPart.add_elements`.

        Returns:
            A string telling the main loop what should do next.
        """
        if ans == 'interrupt':
            return ans
        elif ans == 'partial_next':
            if self.partial_children_memory is None:
                return ans
            else:
                return 'retry'
        elif ans == 'break':
            return self.is_element_resetting()
        elif ans == 'next':
            next_section_ret = self.next_section()
            if next_section_ret == 'break':
                return self.is_element_resetting()
            else:
                return next_section_ret

    def run(self) -> str:
        """Function to run the main loop that will add the content elements to
        the rectangle.

        Returns:
            A string telling the parent what should it do afterwards.
        """

        while True:
            action = self.process_add_ans(self.add_delayed())
            if action == 'retry':
                continue
            elif action in ['interrupt', 'break', 'partial_next']:
                return action

            action = self.process_add_ans(self.add_elements())
            if action == 'retry':
                continue
            elif action in ['interrupt', 'break', 'partial_next']:
                return action

            if len(self.delayed) > 0:
                continue

            if not self.resetting and self.cols_n > 1:
                if self.last_child_of_resetting():
                    break
                self.start_resetting()
                if self.will_reset:
                    self.reset()
                else:
                    return 'break'
            elif self.resetting:
                self.minim_forward = False
                if not self.reset():
                    break
            else:
                break

        return 'continue'

    def last_child_of_resetting(self) -> bool:
        """Function that recursively, towards the ancestors, checks if this
        element is the last element of the last element of one ancestor that
        is resetting.

        Returns:
            True if this element is the last element of an ancestor that is
            resetting.
        """
        parent = self.parent
        if parent:
            if self.last:
                if parent.resetting:
                    parent.mimim_forward = False
                    return True
                else:
                    return parent.last_child_of_resetting()
        return False

    def start_resetting(self) -> None:
        """Function that sets the attribute ``will_reset`` of this element or
        one of its ancestors to True.
        """

        parent = self.parent
        if parent and self.last  and parent.cols_n > 1:
            parent.start_resetting()
            return

        self.will_reset = True

    def reset(self) -> None:
        """Function that first checks if resetting process is over, and if not
        calculates a new value for attribute ``max_y`` and resets all of the
        elements added to the rectangle so far to repeat the arranging process.

        Returns:
            True if resetting process should continue or False if this process
            is done.
        """
        if self.minim_diff_last and self.minim_diff_last - self.minim_diff < 1:
            if self.minim_forward:
                self.minim_diff *= 2
            else:
                return False

        self.will_reset = False
        self.p.parts = self.p.parts[:self.parts_index]
        self.go_to_beginning()

        if self.minim_diff is None:
            self.minim_diff = (self.min_y - self.max_y) / 2
            self.max_y += self.minim_diff
        else:
            self.minim_diff_last = self.minim_diff
            self.minim_diff /= 2
            if self.minim_forward:
                self.max_y -= self.minim_diff
            else:
                self.max_y += self.minim_diff

        self.resetting = True

        self.element_index = self.section_element_index
        self.delayed = copy(self.section_delayed)

        return True

    def go_to_beginning(self) -> None:
        """Function that takes the x and y coordinates of this element to the
        ``min_x`` and ``min_y`` coordinates.
        """
        self.y = self.min_y
        self.x = self.min_x
        self.column = 0
        self.starting = True

    def next_section(self, children_memory: list=None) -> StrOrDict:
        """Function that sets the x and y position of this element in the next
        section.

        The next section could be the next column of this element or the next
        section of one of the ancestors. If some ancestor is resetting, or the
        end of the rectangle of the root element is reached, a string with a
        instruction for the caller will propagate this message towards the
        ancestors to act according to it.

        Args:
            children_memory (list, optional): This is a list containing the
                children's indexes and delayed elements, that is accumulated
                towards the ancestors.

        Returns:
            str, dict: A string containing a message to the main loop, or a dict
            containing the new x and y coordinates that the children are
            going to have from now on.
        """

        if self.column == self.cols_n - 1:
            if self.resetting:
                self.minim_forward = True
                return 'break'
            else:
                self.section_element_index = self.element_index
                self.section_delayed = copy(self.delayed)
                new_index = {
                    'index': self.element_index,
                    'delayed': copy(self.delayed)
                }
                if children_memory is None:
                    self.children_memory = []
                    new_children_memory = [new_index]
                else:
                    self.children_memory = copy(children_memory)
                    new_children_memory = copy(children_memory)
                    new_children_memory.append(new_index)

                if self.is_root:
                    return 'interrupt'

                ret = self.parent.next_section(new_children_memory)
                if ret in ['interrupt', 'break', 'partial_next']:
                    return ret
                self.min_y = ret['min_y']
                self.min_x = ret['min_x']
                self.parts_index = len(self.p.parts)
                self.go_to_beginning()
                return 'retry' if children_memory is None else ret
        else:
            self.column += 1
            self.starting = True
            self.y = self.min_y

            if len(self.delayed) > 0 and children_memory is not None:
                self.partial_children_memory = copy(children_memory)
                return 'partial_next'

            return 'retry' if children_memory is None else \
                {'min_x': self.get_min_x(), 'min_y': self.min_y}

    def get_min_x(self) -> Number:
        """Function to get the x coordinate of the rectangle depending on the
        current column.

        Returns:
            int, float: The x coordinate.
        """
        return self.min_x + self.column * (self.col_width + self.cols_gap)

    def update_dimensions(self, style: dict) -> None:
        """Function that updates the rectangle dimensions of the child element
        that is going to be added to the rectangle of this element.

        Args:
            style (dict): The style dict that contains the margin information
                needed to calculate the child element rectangle dimensions.
        """
        s = style
        self.x = self.get_min_x() + s.get('margin_left', 0)
        self.width = self.col_width - \
            s.get('margin_left', 0) - s.get('margin_right', 0)

        if not self.starting:
            self.y -= self.last_bottom

        self.max_height = max(0, self.y - self.max_y)

    def add_top_margin(self, style: dict) -> None:
        """Function that adds the top margin of the current child element.

        Args:
            style (dict): The style dict that contains the margin information
                needed to calculate the child element top margin.
        """
        if self.starting:
            self.starting = False
        else:
            self.y -=  style.get('margin_top', 0)

    def parse_element(self, element: ProcessElement) -> dict:
        if not isinstance(element, (dict, str, list, tuple)):
            return str(element)
        if isinstance(element, (str, list, tuple)):
            return {'.': element}

        if not isinstance(element, dict):
            raise TypeError(
                'Elements must be of type dict, str, list or tuple:{}'
                .format(element)
            )
        return element

    def process(self, element: ProcessElement, last: bool=False) -> StrOrDict:
        '''Function to add a single child element to the rectangle.

        This function will add an element to the rectangle, using the method
        corresponding to the type of the object (text, image, table or another
        content). Depending on what happens with the element (if it was added or
        delayed) this return a string with a message for the main loop, or a
        dict with information to tell the caller function what should be done
        afterwards.

        Args:
            element (dict, str, list, tuple): The object representing the
                element to be added.
            last (bool): Wheter or not this is the last child element of the
                list of child elements of this element.
        '''
        element = self.parse_element(element)
        style, element_style = self.get_element_styles(element, self.style)

        keys = [key for key in element.keys() if key.startswith('.')]
        if len(keys) > 0 or 'paragraph' in element:
            return self.process_text(element, style, element_style)
        elif 'image' in element:
            return self.process_image(element, style)
        elif 'table' in element or 'table_delayed' in element:
            return self.process_table(element, style, element_style)
        elif 'content' in element:
            return self.process_child(element, style, last)
        elif 'group' in element:
            return self.process_group(element, style)

    def process_text(
        self, element: dict, style: dict, element_style: dict,
        add_parts: bool=True, add_top_margin: bool=True
    ) -> dict:
        """Function that tries to add a paragraph to the current column
        rectangle, and add the remainder to the delayed list

        Args:
            element (dict): The paragraph to be added
            style (dict): The style of the paragraph, combined with the style
                of this element.
            element_style (dict): The style of the paragraph.

        Returns:
            dict: Containing instructions to the caller.
        """
        initial_y = self.y
        if not self.starting and add_top_margin:
            self.y -=  style.get('margin_top', 0)

        self.update_dimensions(style)

        if 'paragraph' in element:
            pdf_text = element['paragraph']
            pdf_text.setup(self.x, self.y, self.width, self.max_height)
            pdf_text.set_state(**element['state'])
            pdf_text.finished = False
            remaining = copy(element)
        else:
            par_style = {
                v: style.get(v) for v in PARAGRAPH_PROPERTIES if v in style
            }
            element['style'] = style.copy()
            pdf_text = PDFText(
                element, self.width, self.max_height, self.x, self.y,
                fonts=self.p.fonts, pdf=self.p.pdf, **par_style
            )
            remaining = {'paragraph': pdf_text, 'style': element_style}

        result = pdf_text.run()
        remaining['last_part'] = pdf_text.last_part
        remaining['last_word'] = pdf_text.last_word
        result['type'] = 'paragraph'

        if add_parts:
            self.p.parts.append(result)

        if pdf_text.current_height > 0:
            self.y -= pdf_text.current_height
            self.starting = False
            self.last_bottom = style.get('margin_bottom', 0)
        else:
            self.y = initial_y

        if pdf_text.finished:
            return {'delayed': None, 'next': False}
        else:
            remaining['state'] = pdf_text.get_state()
            return {'delayed': remaining, 'next': True}

    def process_image(
        self, element: dict, style: dict, add_parts: bool=True,
        add_top_margin: bool=True
    ) -> dict:
        """Function that tries to add an image to the current column rectangle,
        and add it to the delayed list if it can't add it.

        Args:
            element (dict): The image to be added
            style (dict): The style of the image.

        Returns:
            dict: Containing instructions to the caller.
        """
        initial_y = self.y
        if not self.starting and add_top_margin:
            self.y -=  style.get('margin_top', 0)

        self.update_dimensions(style)

        ret = {'delayed': None, 'next': False}
        pdf_image = PDFImage(
            element['image'], element.get('extension'),
            element.get('image_name')
        )
        width = self.width
        height = width * pdf_image.height / pdf_image.width
        x = self.x
        min_height = style.get('min_height', float('inf'))

        can_add = False
        if height < self.max_height:
            can_add = True
        elif min_height <= self.max_height:
            can_add = True
            height = min_height if style.get('shrink', 0) else self.max_height
            new_width = height * pdf_image.width / pdf_image.height
            x += (width - new_width) / 2
            width = new_width

        if can_add:
            self.y -= height
            self.starting = False
            self.last_bottom = style.get('margin_bottom', 0)
            if add_parts:
                self.p.parts.append({
                    'pdf_image': pdf_image, 'type': 'image', 'x': x,
                    'y': self.y, 'width': width, 'height': height
                })
        else:
            self.y = initial_y
            if element.setdefault('tries', 0) >= 50:
                raise Exception(
                    'Image element could not be fitted in the document (try '
                    'adding "min_height" style property to this image for us'
                    ' to know how much we can downsize the image for it to fit)'
                    ': {}'
                    .format(element)
                )
            element['tries'] += 1
            image_place = style.get('image_place', 'flow')
            ret['delayed'] = element
            if image_place == 'normal':
                ret['next'] = True
            elif image_place == 'flow':
                ret['flow'] = True
        return ret

    def process_table(
        self, element: dict, style: dict, element_style: dict,
        add_parts: bool=True, add_top_margin: bool=True
    ) -> dict:
        """Function that tries to add a table to the current column rectangle,
        and add the remainder to the delayed list.

        Args:
            element (dict): The table to be added.
            style (dict): The style of the table, combined with the style
                of this element.
            element_style (dict): The style of the table.

        Returns:
            dict: Containing instructions to the caller.
        """
        initial_y = self.y
        if not self.starting and add_top_margin:
            self.y -=  style.get('margin_top', 0)

        self.update_dimensions(style)

        if 'table_delayed' in element:
            pdf_table = element['table_delayed']
            pdf_table.setup(self.x, self.y, self.width, self.max_height)
            pdf_table.set_state(**element['state'])
            pdf_table.finished = False
            remaining = copy(element)
        else:
            table_props = {
                v: element.get(v) for v in TABLE_PROPERTIES
                if v in element
            }
            pdf_table = PDFTable(
                element['table'], self.p.fonts, self.x, self.y,
                self.width, self.max_height, style=style, pdf=self.p.pdf,
                **table_props
            )
            remaining = {'table_delayed': pdf_table, 'style': element_style}

        pdf_table.run()

        if add_parts:
            self.p.parts.extend(pdf_table.parts)
            self.p.lines.extend(pdf_table.lines)
            self.p.fills.extend(pdf_table.fills)

        if pdf_table.current_height > 0:
            self.y -= pdf_table.current_height
            self.starting = False
            self.last_bottom = style.get('margin_bottom', 0)
        else:
            self.y = initial_y

        if not pdf_table.finished:
            remaining['state'] = pdf_table.get_state()
            return {'delayed': remaining, 'next': True}
        else:
            return {'delayed': None, 'next': False}

    def process_child(
        self, element: dict, style: dict, last: bool, add_top_margin: bool=True
    ) -> StrOrDict:
        """Function that tries to add a child content to the current column
        rectangle.

        Args:
            element (dict): The child to be added
            style (dict): The style of the child, combined with the style
                of this element.
            last (bool): whether or not this is the last child of this element.

        Returns:
            str, dict: Containing instructions to the caller.
        """
        initial_y = self.y
        if not self.starting and add_top_margin:
            self.y -=  style.get('margin_top', 0)

        self.update_dimensions(style)

        pdf_content = PDFContentPart(
            element, self.p, self.get_min_x(), self.col_width, self.y,
            self.max_y, self, last, style.copy()
        )
        down_condition1 = len(self.children_memory) > 0 and \
            self.element_index == self.section_element_index
        down_condition2 = self.partial_children_memory is not None

        if down_condition1 or down_condition2:
            child = self.children_memory[-1] if down_condition1 else \
                self.partial_children_memory[-1]
            pdf_content.section_element_index = child['index']
            pdf_content.section_delayed = copy(child['delayed'])
            pdf_content.element_index = child['index']
            pdf_content.delayed = copy(child['delayed'])
            pdf_content.children_memory = self.children_memory[:-1] \
                if down_condition1 else self.partial_children_memory[:-1]

            self.partial_children_memory = None

        action = pdf_content.run()

        if action != 'partial_next':
            current_height = pdf_content.min_y - (
                pdf_content.max_y if pdf_content.cols_n > 1 else pdf_content.y
            )
            if current_height > 0:
                self.y -= current_height
                self.starting = False
                self.last_bottom = style.get('margin_bottom', 0)
            else:
                self.y = initial_y

        if action in ['interrupt', 'break', 'partial_next']:
            return action
        else:
            self.starting = False
            return {'delayed': None, 'next': False}

    def get_element_styles(self, element: dict, inherited_style: dict):
        keys = [key for key in element.keys() if key.startswith('.')]

        style = {}
        style.update(inherited_style)
        if len(keys) > 0:
            style.update(parse_style_str(keys[0][1:], self.p.fonts))
        element_style = process_style(element.get('style'), self.p.pdf)
        style.update(element_style)
        return style, element_style

    def process_group_element(
        self, element: dict, inherited_style: dict, add_element: bool=False,
        add_top_margin: bool=True, min_height: Optional[Number] = None
    ):
        element = self.parse_element(element)
        style, element_style = self.get_element_styles(element, inherited_style)

        if min_height is not None:
            style['min_height'] = min_height

        keys = [key for key in element.keys() if key.startswith('.')]
        if len(keys) > 0 or 'paragraph' in element:
            return self.process_text(
                element, style, element_style, add_element, add_top_margin
            )
        elif 'image' in element:
            style['shrink'] = True
            return self.process_image(
                element, style, add_element, add_top_margin
            )
        elif 'table' in element or 'table_delayed' in element:
            return self.process_table(
                element, style, element_style, add_element, add_top_margin
            )
        else:
            raise Exception(
                'Element not allowed in a group element: {}'.format(element)
            )

    def process_group(self, group_element: dict, style: dict):
        """Function that tries to add a group element to the current column
        rectangle, and add it to the delayed list if it can't add it. If after
        50 tries it can not add the group element, it will throw an exception.

        Args:
            group_element (dict): The group element to be added
            style (dict): The style of the group element, combined with the
                style of this content element.

        Returns:
            dict: Containing instructions to the caller.
        """
        initial_y = self.y

        if not self.starting:
            self.y -=  style.get('margin_top', 0)

        images = {}
        images_size = 0

        for i, element in enumerate(group_element['group']):
            if isinstance(element, dict) and 'image' in element:
                image_style, _ = self.get_element_styles(element, style)
                if 'min_height' in image_style:
                    min_height = image_style['min_height']
                    images[i] = min_height
                    images_size += min_height

            ans = self.process_group_element(
                element, style, add_element=False, add_top_margin=i != 0
            )
            if not (isinstance(ans, dict) and ans.get('delayed') is None):
                if group_element.setdefault('tries', 0) >= 50:
                    raise Exception(
                        'Group element could not be fitted in the document: {}'
                        .format(group_element)
                    )
                group_element['tries'] += 1
                self.y = initial_y
                return {'delayed': group_element, 'next': False, 'flow': True}

        new_images_size = images_size + self.y - self.max_y
        image_ratio = new_images_size / images_size if len(images) else 1
        self.y = initial_y

        for i, element in enumerate(group_element['group']):
            min_height = None
            if i in images:
                min_height = images[i]
                min_height *= 1 if style.get('shrink', 0) else image_ratio
            self.process_group_element(
                element, style, add_element=True, add_top_margin=i != 0,
                min_height=min_height
            )

        return {'delayed': None, 'next': False}

from .fonts import PDFFonts
from .image import PDFImage
from .pdf import PDF
from .text import PDFText
from .table import PDFTable
from .utils import parse_style_str, process_style, copy