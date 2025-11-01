#!/usr/bin/env python3

import sys
sys.path.insert(0, '/workspace/arbitech')

try:
    from risk import BankrollValidator
    print("✓ BankrollValidator imported successfully")
    print(f"BankrollValidator class: {BankrollValidator}")
    print(f"BankrollValidator.__init__ signature: {BankrollValidator.__init__.__code__.co_varnames[:BankrollValidator.__init__.__code__.co_argcount]}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from storage.models import RiskConfig
    print("✓ RiskConfig imported successfully")
    print(f"RiskConfig class: {RiskConfig}")
except Exception as e:
    print(f"❌ RiskConfig import failed: {e}")
    import traceback
    traceback.print_exc()