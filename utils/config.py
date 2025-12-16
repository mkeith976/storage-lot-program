"""Business configuration for the storage lot application.

This module contains configuration flags that control which features
are available based on your business licensing and operations.
"""

# ============================================================================
# BUSINESS LICENSING CONFIGURATION
# ============================================================================

# Set to True ONLY if your business holds a Florida wrecker license
# and is authorized to perform involuntary towing/recovery services.
#
# When False (default):
# - Only "Storage" and "Tow" (voluntary) contract types are available
# - Recovery/involuntary towing features are hidden from UI
# - Lien processes follow voluntary storage timeline rules
# - No impound or recovery-specific fees
#
# When True:
# - Enables "Recovery" contract type for involuntary towing
# - Activates Florida Statute 713.78 compliance features
# - Allows impound/recovery fees and accelerated lien timeline
# - Requires proper licensing and insurance
ENABLE_INVOLUNTARY_TOWS = False

# ============================================================================
# FEE CONFIGURATION
# ============================================================================

# Maximum admin fee allowed in Florida
MAX_ADMIN_FEE = 250.00

# Maximum lien processing fee (if applicable)
MAX_LIEN_FEE = 250.00

# Minimum hours vehicle must be on lot before storage charges apply (Tow contracts)
# Florida allows exemption if vehicle is on lot < 6 hours
TOW_STORAGE_EXEMPTION_HOURS = 6

# ============================================================================
# BUSINESS INFORMATION (Update with your details)
# ============================================================================

BUSINESS_NAME = "Vehicle Storage & Transport LLC"
BUSINESS_ADDRESS = "123 Main St, City, FL 12345"
BUSINESS_PHONE = "(555) 555-5555"
BUSINESS_LICENSE = ""  # Add if applicable

# ============================================================================
# COMPLIANCE NOTES
# ============================================================================
"""
FLORIDA LICENSING REQUIREMENTS:

1. VOLUNTARY TOW/TRANSPORT (No special license required):
   - Customer requests tow service
   - Customer owns or has authority over vehicle
   - No law enforcement involvement
   - This application's default mode (ENABLE_INVOLUNTARY_TOWS = False)

2. INVOLUNTARY TOW/RECOVERY (Requires wrecker license):
   - Law enforcement requested tow
   - Private property impound
   - Abandoned vehicle recovery
   - Requires Florida wrecker license (Chapter 713)
   - Requires proper insurance and bonding
   - Set ENABLE_INVOLUNTARY_TOWS = True only if licensed

ALWAYS CONSULT WITH A FLORIDA ATTORNEY before enabling involuntary
towing features to ensure compliance with state and local regulations.
"""
