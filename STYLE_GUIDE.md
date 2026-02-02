# Python Style Guide - LCA Test Data Management System

This project follows the **Google Python Style Guide** with Pylint enforcement.

## Table of Contents

1. [Code Organization](#code-organization)
2. [Naming Conventions](#naming-conventions)
3. [Documentation](#documentation)
4. [Formatting](#formatting)
5. [Imports](#imports)
6. [Type Hints](#type-hints)
7. [Running Pylint](#running-pylint)

## Code Organization

### Module Structure

Each Python file should follow this order:

1. **Module docstring** - Describes the module's purpose
2. **Imports** - Organized in specific order (see Imports section)
3. **Module-level constants** - ALL_CAPS naming
4. **Classes** - One or more class definitions
5. **Functions** - Module-level functions (if any)
6. **Main block** - `if __name__ == "__main__":` (if applicable)

### Example:

```python
"""Module docstring explaining what this module does.

Detailed description if needed.

Typical usage example:
    foo = ClassFoo()
    bar = foo.function_bar()
"""

import os
import sys

from third_party import lib
from my_project import other_module

CONSTANT_VALUE = 42


class MyClass:
    """Class docstring."""
    
    def __init__(self):
        """Constructor docstring."""
        pass


def main():
    """Main function docstring."""
    pass


if __name__ == "__main__":
    main()
```

## Naming Conventions

Following Google Python Style Guide:

| Type | Convention | Example |
|------|------------|---------|
| Modules | `lowercase_with_underscores` | `database.py` |
| Packages | `lowercase` | `widgets` |
| Classes | `CapWords` | `DatabaseManager` |
| Functions | `lowercase_with_underscores()` | `get_all_data()` |
| Methods | `lowercase_with_underscores()` | `init_ui()` |
| Constants | `ALL_CAPS_WITH_UNDERSCORES` | `MAX_RECORDS` |
| Variables | `lowercase_with_underscores` | `user_name` |
| Private | `_leading_underscore` | `_internal_var` |

### Special Cases

- **Qt Widgets**: Use descriptive names like `submit_btn`, `project_filter`
- **DataFrames**: Use `df` for local scope, descriptive names for class attributes
- **Database**: Use `db` for DatabaseManager instances

## Documentation

### Module Docstrings

Every module must have a docstring at the top:

```python
"""Short one-line summary.

Longer description if needed. Explain the module's purpose,
main classes, and typical usage.

Typical usage example:
    db = DatabaseManager()
    data = db.get_all_data()
"""
```

### Class Docstrings

Every class must have a docstring:

```python
class MyClass:
    """Short summary of the class.
    
    Longer description explaining the class purpose and behavior.
    
    Attributes:
        attribute1: Description of attribute1.
        attribute2: Description of attribute2.
    """
```

### Function/Method Docstrings

Every public function and method must have a docstring:

```python
def my_function(param1: str, param2: int) -> bool:
    """Short summary of what the function does.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1.
        param2: Description of param2.
        
    Returns:
        Description of return value.
        
    Raises:
        ValueError: When param1 is invalid.
    """
```

### Inline Comments

- Use sparingly for complex logic
- Place on separate line above the code
- Use complete sentences

```python
# Calculate the total based on filtered results
total = sum(filtered_values)
```

## Formatting

### Line Length

- Maximum 100 characters per line
- Break long lines using parentheses

```python
# Good
result = some_function(
    parameter1, 
    parameter2,
    parameter3
)

# Bad
result = some_function(parameter1, parameter2, parameter3, parameter4, parameter5)
```

### Indentation

- Use 4 spaces (no tabs)
- Continuation lines should align with opening delimiter

```python
# Good
my_list = [
    1, 2, 3,
    4, 5, 6,
]

# Good
result = my_function(
    arg1,
    arg2,
    arg3
)
```

### Blank Lines

- 2 blank lines between top-level definitions
- 1 blank line between method definitions
- Use blank lines sparingly within functions

### Whitespace

```python
# Good
spam(ham[1], {eggs: 2})
x = 1
y = 2

# Bad
spam( ham[ 1 ], { eggs: 2 } )
x=1
y=2
```

## Imports

### Import Order

1. Standard library imports
2. Related third party imports
3. Local application imports

Separate each group with a blank line.

```python
# Standard library
import os
import sys
from typing import Any, Dict, List

# Third party
import pandas as pd
from PyQt5.QtWidgets import QWidget

# Local
from database import DatabaseManager
from widgets.dashboard_widget import DashboardWidget
```

### Import Style

```python
# Good
import os
import sys
from typing import Dict, List

# Bad
import os, sys
from typing import *
```

## Type Hints

Use type hints for all function signatures:

```python
def process_data(data: pd.DataFrame, filter_value: str) -> Dict[str, Any]:
    """Process the dataframe with given filter."""
    pass

def init_ui(self) -> None:
    """Initialize the user interface."""
    pass
```

### Common Type Hints

```python
from typing import Any, Dict, List, Optional, Tuple

def example(
    name: str,
    age: int,
    data: Dict[str, Any],
    items: List[str],
    optional_param: Optional[int] = None
) -> Tuple[bool, str]:
    """Example function with type hints."""
    return True, "Success"
```

## Running Pylint

### Install Pylint

```bash
pip install pylint
```

### Run Pylint on All Files

**Windows:**
```bash
run_pylint.bat
```

**Linux/Mac:**
```bash
chmod +x run_pylint.sh
./run_pylint.sh
```

### Run Pylint on Specific File

```bash
pylint main.py
```

### Pylint Configuration

The project includes a `.pylintrc` file with custom configuration:
- Line length: 100 characters
- Disabled warnings for Qt naming conventions
- Custom good names: i, j, k, db, df, ax

### Pylint Score

Aim for a score of **8.0 or higher** for all modules.

## Code Review Checklist

Before committing code, ensure:

- [ ] All files have module docstrings
- [ ] All classes have docstrings with attributes listed
- [ ] All public functions/methods have docstrings
- [ ] Type hints are used for all function signatures
- [ ] Imports are organized correctly
- [ ] Line length is under 100 characters
- [ ] Naming conventions are followed
- [ ] Pylint score is 8.0 or higher
- [ ] No unused imports or variables

## Examples from Project

### Good Example - database.py

```python
"""Database management module for LCA Test Data Management System.

This module provides the DatabaseManager class for handling all database operations
including initialization, data import, CRUD operations, and queries.
"""

import sqlite3
from typing import Any, Dict, Tuple

import pandas as pd


class DatabaseManager:
    """Manages SQLite database operations for LCA Test Data.
    
    Attributes:
        db_path: Path to the SQLite database file.
    """
    
    def __init__(self, db_path: str = "lca_test_data.db") -> None:
        """Initializes the DatabaseManager.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.init_database()
```

## References

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 - Docstring Conventions](https://www.python.org/dev/peps/pep-0257/)
- [Pylint Documentation](https://pylint.pycqa.org/)
