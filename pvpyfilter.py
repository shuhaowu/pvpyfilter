from abc import ABCMeta, abstractmethod
from enum import Enum
import inspect
import textwrap

import lxml.etree as ET

# Inspired mostly from https://blog.kitware.com/easy-customization-of-the-paraview-python-programmable-filter-property-panel/
# With documentations from https://www.paraview.org/Wiki/ParaView/Plugin_HowTo


def multi_line_hint():
  elem = ET.Element("Hints")
  elem.append(ET.Element("Widget", type="multi_line"))
  return elem


class ProgrammableFilter(metaclass=ABCMeta):
  """
  Attributes that can be defined on this class:

  - [REQUIRED] label:                   the label shown in the filters menu in PV.
  - [REQUIRED] __doc__ (via docstring): the long help message
  - [REQUIRED] input_data_type:         the input data type (only if number_of_inputs >= 1)
  - [OPTIONAL] output_data_type:        the output data type
  - [OPTIONAL] short_help:              the short help message
  - [OPTIONAL] number_of_inputs:        the number of inputs the filter takes
                                        (default: 1)
  - [OPTIONAL] script_invisible:        determine if the scritps are invisible
                                        or not (default: False)

  classmethod definition:
  - [REQUIRED] def request_data():          Script goes into here.
  - [OPTIONAL] def request_information():   Information goes into here.
  - [OPTIONAL] def request_update_extent(): Script goes into here.
  - [OPTIONAL] def extra_xml() -> xml.etree.ElementTree.Element:
                 Extra XML elements to include

  property definitions are in done in class variables with the Property
  objects.
  """
  DATA_TYPE_MAP = {
    "":                          "8",  # same as input
    "vtkPolyData":               "0",
    "vtkStructuredGrid":         "2",
    "vtkRectilinearGrid":        "3",
    "vtkUnstructuredGrid":       "4",
    "vtkImageData":              "6",
    "vtkUniformGrid":            "10",
    "vtkMultiblockDataSet":      "13",
    "vtkHierarchicalBoxDataSet": "15",
    "vtkTable":                  "19",
  }

  @staticmethod
  @abstractmethod
  def request_data(inputs, output, *args, **kwargs):
    """
    Implement this method in your class to set the Script part of the
    PythonProgrammableFilter. You can pass in the parameters you defined as
    argumens to this method so you're not even referring to variables that
    is not technically defined within the confines of your .py file.

    Note: you cannot access variables using closure or access other methods of
    the class (or super) as the source code of this function is used directly
    as the Script of the python programmable filter. There are no easy ways get
    around this limitation as the script source code is sent to the server to
    be executed as opposed to the actual python function objects (and
    associated scopes).

    Further note: if you updated the plugin and already saved a particular
    PVSM, you have to copy the updated script manually to the saved insance as
    the pvsm contains a copy of the script as defined here.
    """
    pass

  @staticmethod
  def extra_xml():
    return None

  @classmethod
  def properties(cls):
    properties = []
    variables = vars(cls)
    for varname, value in variables.items():
      if isinstance(value, Property):
        properties.append((varname, value))

    return properties

  @classmethod
  def xml_element(cls):
    number_of_inputs = getattr(cls, "number_of_inputs", 1)

    # Generate the "top level" XML
    root = ET.Element("ServerManagerConfiguration")

    proxy_group_name = "filters" if number_of_inputs > 0 else "sources"
    proxy_group = ET.Element("ProxyGroup", name=proxy_group_name)

    source_proxy = ET.Element("SourceProxy", {
      "name":  cls.__name__,
      "class": "vtkPythonProgrammableFilter",
      "label": cls.label,
    })

    docstr = inspect.cleandoc(cls.__doc__)
    documentation = ET.Element("Documentation", {
      "long_help":  docstr,
      "short_help": getattr(cls, "short_help", docstr),
    })

    # Generate InputProperty
    if number_of_inputs >= 1:
      input_property = ET.Element("InputProperty", name="Input")

      if number_of_inputs > 1:
        input_property.set("clean_command", "RemoveAllInputs")
        input_property.set("command", "AddInputConnection")
        input_property.set("multiple_input", "1")
      else:
        input_property.set("command", "SetInputConnection")

      proxy_group_domain = ET.Element("ProxyGroupDomain", name="groups")
      proxy_group_domain.append(ET.Element("Group", name="sources"))
      proxy_group_domain.append(ET.Element("Group", name="filters"))

      data_type_domain = ET.Element("DataTypeDomain", name="input_type")
      data_type_domain.append(ET.Element("DataType", value=cls.input_data_type))

      input_property.append(proxy_group_domain)
      input_property.append(data_type_domain)

    # Generate all the properties xml
    properties = []
    for name, prop in cls.properties():
      prop.set_name(name)
      properties.append(prop.xml_element())

    # Any custom defined xml
    extra_xml = cls.extra_xml()

    # Output data type
    output_data_set_type = ET.Element("IntVectorProperty", {
      "command":            "SetOutputDataSetType",
      "default_values":     cls.DATA_TYPE_MAP[getattr(cls, "output_data_type", "")],
      "name":               "OutputDataSetType",
      "number_of_elements": "1",
      "panel_visibility":   "never"
    })
    output_data_set_type_doc = ET.Element("Documentation")
    output_data_set_type_doc.text = "The value of this property determines the dataset type for the output of the programmable filter."
    output_data_set_type.append(output_data_set_type_doc)

    # Script
    request_data = ET.Element("StringVectorProperty", {
      "name":               "Script",
      "command":            "SetScript",
      "number_of_elements": "1",
      "default_values":     cls._function_source("request_data"),
      "panel_visibility":   "never" if getattr(cls, "script_invisible") else "advanced",
    })
    request_data.append(multi_line_hint())

    request_information = ET.Element("StringVectorProperty", {
      "name":               "InformationScript",
      "label":              "RequestInformationScript",
      "command":            "SetInformationScript",
      "number_of_elements": "1",
      "default_values":     cls._function_source("request_information"),
      "panel_visibility":   "never" if getattr(cls, "script_invisible") else "advanced",
    })
    request_information.append(multi_line_hint())

    request_update_extent = ET.Element("StringVectorProperty", {
      "name":               "UpdateExtentScript",
      "label":              "RequestUpdateExtentScript",
      "command":            "SetUpdateExtentScript",
      "number_of_elements": "1",
      "default_values":     cls._function_source("request_update_extent"),
      "panel_visibility":   "never" if getattr(cls, "script_invisible") else "advanced",
    })
    request_update_extent.append(multi_line_hint())

    # Actually build the xml document
    root.append(proxy_group)
    proxy_group.append(source_proxy)
    source_proxy.append(documentation)
    if number_of_inputs >= 1:
      source_proxy.append(input_property)

    for property_xml in properties:
      source_proxy.append(property_xml)

    if extra_xml:
      source_proxy.append(extra_xml)

    source_proxy.append(output_data_set_type)
    source_proxy.append(request_data)
    source_proxy.append(request_information)
    source_proxy.append(request_update_extent)

    return root

  @classmethod
  def _function_source(cls, function_name):
    f = getattr(cls, function_name, None)
    if not f:
      return ""

    lines = inspect.getsourcelines(f)[0]
    if len(lines) <= 1:
      raise ValueError("classmethod {} must have at least a single line of code".format(function_name))

    found_def_start = False
    found_def_end = False
    for i, line in enumerate(lines):
      line = line.strip()
      if not found_def_start:
        if line.startswith("def"):
          found_def_start = True

      if found_def_start and not found_def_end:
        if line.endswith(":"):
          found_def_end = True

      if found_def_start and found_def_end:
        break

    return textwrap.dedent("".join(lines[i + 1:]))

  @classmethod
  def xml(cls):
    return ET.tostring(cls.xml_element(), pretty_print=True)

  @classmethod
  def save(cls, filename):
    with open(filename, "w") as f:
      f.write(cls.xml())


class Property(metaclass=ABCMeta):
  DEFAULT = None

  @classmethod
  @abstractmethod
  def tag_name(cls):
    raise NotImplementedError

  def __init__(self, label=None, default=None, help=""):
    self.name = None
    self.label = label

    self.default = self.__class__.DEFAULT if default is None else default
    if type(self.default) is not list and type(self.default) is not tuple:
      self.default = [self.default]
    else:
      self.default = list(self.default)

    if len(self.default) > 3:
      raise ValueError("the maximum number of values a property can have is 3")

    if len(self.default) > 1 and type(self.default[0]) is str:
      raise ValueError("only numbers can have more than 1 values")

    self.help = help

  def set_name(self, name):
    self.name = name
    if self.label is None:
      self.label = self.name.replace("_", " ").title()

  def xml_element(self):
    if self.name is None:
      raise RuntimeError("name is not set. please use the ProgrammableFilter.xml method instead of calling this directly")

    root = ET.Element(self.__class__.tag_name())
    root.set("name", self.name)
    root.set("label", self.label)
    root.set("initial_string", self.name)  # TODO: what is the initial string?
    root.set("command", "SetParameter")
    root.set("animateable", "1")           # TODO: what is animateable?
    root.set("default_values", self.default_values())
    root.set("number_of_elements", str(len(self.default)))

    if self.help:
      documentation = ET.Element("Documentation")
      documentation.text = self.help
      root.append(documentation)

    return root

  def default_values(self):
    return " ".join(map(str, self.default))


class Boolean(Property):
  DEFAULT = 0

  @classmethod
  def tag_name(cls):
    return "IntVectorProperty"

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.default = list(map(int, self.default))

    if len(self.default) > 1:
      raise ValueError("boolean properties can only have 1 entry")

  def xml_element(self):
    root = super().xml_element()
    root.append(ET.Element("BooleanDomain", name="bool"))
    return root


class Integer(Property):
  DEFAULT = 0

  @classmethod
  def tag_name(cls):
    return "IntVectorProperty"


class String(Property):
  DEFAULT = ""

  @classmethod
  def tag_name(cls):
    return "StringVectorProperty"

  def __init__(self, *args, multi_line=False, **kwargs):
    super().__init__(*args, **kwargs)
    self.multi_line = multi_line
    if self.multi_line:
      raise NotImplementedError("A PV issue prevents multi_line from working: https://gitlab.kitware.com/paraview/paraview/issues/18045")

  def xml_element(self):
    root = super().xml_element()
    if self.multi_line:
      root.append(multi_line_hint())

    return root


class IntegerEnum(Property):
  DEFAULT = None

  @classmethod
  def tag_name(cls):
    return "IntVectorProperty"

  def __init__(self, *args, enum=None, **kwargs):
    super().__init__(*args, **kwargs)

    if enum is None:
      raise AttributeError("must specify enum")

    if not issubclass(enum, Enum):
      raise TypeError("enum must be an enum.Enum")

    if not isinstance(self.default[0], enum):
      raise TypeError("default must be an instance of the specified enum")

    self.default[0] = self.default[0].value
    self.enum = enum

  def xml_element(self):
    root = super().xml_element()

    enumeration_domain = ET.Element("EnumerationDomain", name="enum")

    for item in self.enum:
      entry = ET.Element("Entry", value=str(item.value), text=item.name)
      enumeration_domain.append(entry)

    root.append(enumeration_domain)
    return root


class Double(Property):
  DEFAULT = "0.0"

  @classmethod
  def tag_name(cls):
    return "DoubleVectorProperty"

  def __init__(self, *args, slider=None, **kwargs):
    """
    The slider argument allows you to specify a tuple of (min, max), which will
    create a slider in the Paraview GUI.
    """
    super().__init__(*args, **kwargs)

    if type(slider) is not tuple and len(slider) != 2:
      raise TypeError("slider must be a tuple of 2")

    self.slider = slider

  def xml_element(self):
    root = super().xml_element()
    if self.slider:
      range_element = ET.Element(
        "DoubleRangeDomain",
        name="range",
        min=str(self.slider[0]),
        max=str(self.slider[1])
      )
      root.append(range_element)

    return root
