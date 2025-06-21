import shutil
from datetime import datetime

src = 'content.json'
dst = f'backup_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'
shutil.copy(src, dst)
print(f'✅ Backup saved as {dst}')
