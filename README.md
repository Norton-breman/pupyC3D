# pupyC3D

[![PyPI version](https://badge.fury.io/py/pupyC3D.svg)](https://badge.fury.io/py/pupyC3D)
[![Python](https://img.shields.io/pypi/pyversions/pupyC3D.svg)](https://pypi.org/project/pupyC3D/)

A pure Python library for reading and writing C3D files, commonly used in biomechanics and motion capture applications.

## Features

- **Pure Python**: No external dependencies except NumPy
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Full C3D support**: Read and write C3D files with complete parameter and data access
- **Multiple processor formats**: Supports Intel, DEC, and MIPS processor formats
- **Easy to use**: Simple API for accessing 3D coordinates, parameters, and metadata

## Installation

### From PyPI (recommended)

```bash
pip install pupyC3D
```

### From source

```bash
# Clone the repository
git clone https://github.com/Norton-breman/pupyC3D.git
cd pupyC3D

# Install in development mode
pip install -e .
```

## Quick Start

### Reading a C3D file

```python
from pupyC3D import C3DFile

# Load a C3D file
c3d = C3DFile('example.c3d')

# Access header information
print(f"Number of 3D points: {c3d.point_count}")
print(f"Number of frames: {c3d.frame_count}")

# Access parameter groups
point_group = c3d.get_parameter_group('POINT')
if point_group:
    labels_param = point_group.get_parameter('LABELS')
    if labels_param:
        print(f"Point labels: {labels_param.value}")

# Access points data
points_list = c3d.get_point_names()
point_data = c3d.get_point_data(points_list[0])
# getting multiple points data
points_data = c3d.get_points_data(points_list)
# Access analog data
if c3d.analog_count > 0:
    analog_list = c3d.get_analog_names()
    analog_data = c3d.get_analog_data(analog_list[0])
```

### Writing a C3D file

```python
from pupyC3D import C3DFile
import numpy as np

# Create a new C3D file
c3d = C3DFile()

# Add parameter groups and parameters
point_group = c3d.add_parameter_group('POINT')
if point_group:
    labels_param = point_group.add_parameter('LABELS')
    labels_param.value = np.array(['MARKER1', 'MARKER2', 'MARKER3'])
    labels_param.data_type = -1  # String type

# Save the file
c3d.write('output.c3d', overwrite=True)
```

## C3D File Format

C3D files contain:
- **Header**: Basic file information (number of points, frames, etc.)
- **Parameters**: Organized in groups (POINT, ANALOG, TRIAL, etc.)
- **Data**: 3D coordinates and analog data

## API Reference

### Main Classes

- `C3DFile`: Main class for reading/writing C3D files
- `ParameterGroup`: Container for related parameters
- `Parameter`: Individual parameter with typed data
- `ProcStream`: Low-level binary data processor

### Key Methods

- `C3DFile.read_file()`: Load C3D file from disk
- `C3DFile.write()`: Save C3D file to disk
- `C3DFile.get_parameter_group()`: Access parameter groups by name or ID
- `C3DFile.add_parameter_group()`: Create new parameter groups

## Requirements

- Python 3.6+
- NumPy

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
See the [LICENSE](https://creativecommons.org/licenses/by-nc/4.0/) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Antoine MARIN (antoine.marin@univ-rennes2.fr)

## Changelog

### v0.1.0
- Initial release
- Basic C3D reading and writing functionality
- Support for Intel, DEC, and MIPS processor formats
- Complete parameter and data access 


