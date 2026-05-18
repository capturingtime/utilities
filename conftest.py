import sys
import os

# The package uses relative imports rooted at the `utilities` package, which lives one
# directory above this file. Add the parent so `from utilities.classes.* import ...`
# resolves correctly when running pytest from within the utilities/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
