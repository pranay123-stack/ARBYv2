#!/usr/bin/env python3

import sys
sys.path.insert(0, '/workspace/arbitech')

try:
    from risk import BankrollValidator
    from storage.models import RiskConfig
    print("✓ Imports successful")
    
    # Create a simple risk config
    risk_config = RiskConfig(name="test")
    print("✓ RiskConfig created")
    
    # Try to instantiate BankrollValidator
    validator = BankrollValidator(risk_config)
    print("✓ BankrollValidator instantiated successfully")
    print(f"Validator type: {type(validator)}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()