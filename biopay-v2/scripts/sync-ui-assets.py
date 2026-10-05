"""Copy the shared UI styles and components to each independent Docker build context."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
source = root / 'frontend/merchant-web/app'
for target in [root/'frontend/customer-web/app',
               root/'services/payment-core/src/main/resources/static',
               root/'services/biometric-risk/app/static']:
    target.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source/'globals.css', target/'globals.css')
shutil.copyfile(source/'ui.js', root/'frontend/customer-web/app/ui.js')
print('Shared UI assets synchronized.')
