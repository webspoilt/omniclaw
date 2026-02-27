import sys
import traceback
sys.path.append('.')

try:
    import omniclaw
except Exception as e:
    traceback.print_exc()
