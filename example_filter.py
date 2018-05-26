from enum import Enum
from pvpyfilter import *

# flake8: noqa

class MyEnum(Enum):
  value1 = 1
  value2 = 2


class MyExampleFilter(ProgrammableFilter):
  """
  My example filter created using xml.

  It does somethings...
  """

  label            = "My Example Filter"
  # input_data_type can also be a list, e.g. ["vtkPolyData", "vtkUnstructuredGrid"]
  input_data_type  = "vtkPolyData"
  output_data_type = ""
  short_help       = "My example filter"
  number_of_inputs = 1
  script_invisible = False

  scalar_str    = String("scalar string", help="scalar string")
  boolean       = Boolean("boolean variable")
  many_ints     = Integer("many integers", default=[0, 1, 2], help="many integers")
  double_slider = Double("double with slider", default=0.5, slider=[0.0, 1.0], help="double with slider")
  int_enum      = IntegerEnum("integer based enums", enum=MyEnum, default=MyEnum.value1, help="many integers")

  @staticmethod
  def request_data(inputs,
                   output,
                   scalar_str,
                   boolean,
                   many_ints,
                   double_slider,
                   int_enum):
    print("scalar_str", scalar_str)
    print("boolean", boolean)
    print("many_ints", many_ints)
    print("double_slider", double_slider)
    print("int_enum", int_enum <= 1)


if __name__ == "__main__":
  print(MyExampleFilter.xml().decode("utf-8"))
