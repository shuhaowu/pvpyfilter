pvpyfilter
==========

**Note: in PV 5.6+, there seem to be capability to directly import a .py file
as a plugin. I've personally not tested it and don't know if it can replace
this library, but if it does, the documentation seem to be here:
https://kitware.github.io/paraview-docs/latest/python/paraview.util.vtkAlgorithm.html**.


pvpyfilter is a library that allows you to define a programmable filter via a
python file. A XML file can be generated from this python file and imported
into paraview, where GUI options will be displayed for the filter.

**Filter definition (See `example_filter.py` (same as listed here))**:


```
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
```

**In Paraview**:

![screenshot](https://github.com/shuhaowu/pvpyfilter/raw/master/programmable_filter.png)


### Installation ###

1. Download this repository
2. cd into the repository
3. `python3 setup.py install [--user]`

### Example Usage ###

1. Define the programmable filter file similar to `example_filter.py`
2. Ensure `if __name__ == "__main__": print(MyExampleFilter.xml().decode("utf-8"))` 
   is in the python file.
3. Call `python3 example_filter.py > example_filter.xml`
4. Import the plugin inside Paraview -> Tools -> Manage Plugins.

### Caveat ###

Please read the doc strings within pvpyfilter.py as there are several caveats
to be aware of when writing `request_data`.
