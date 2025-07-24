# Phase 1: SURGICAL LibreOffice UNO Service Fix
**Date**: January 21, 2025  
**Priority**: CRITICAL - Blocking all document functionality
**Estimated Time**: 2 hours

## THE SINGLE PROBLEM WE'RE SOLVING

```bash
LibreOffice process died:
Failed to start LibreOffice server after all attempts
```

**Location**: `DocAI_Native/app/services/libreoffice_uno_converter_improved.py`
**Method**: `_start_libreoffice_service()` (line ~93)

## ROOT CAUSE ANALYSIS

### Issue 1: Overly Complex Command
Current command has too many flags that may conflict:
```python
cmd = [
    'libreoffice',           # May not be in PATH
    '--headless',            # ✓ Required
    '--invisible',           # ❌ Redundant with headless
    '--nodefault',           # ❌ May cause issues
    '--nolockcheck',         # ❌ May interfere
    '--nologo',              # ✓ Good
    '--norestore',           # ❌ May prevent proper startup
    '--nofirststartwizard',  # ❌ Not needed for headless
    f'--accept=socket,host=localhost,port={self.port};urp;StarOffice.ServiceManager'  # ❌ Too complex
]
```

### Issue 2: Process Killing Interference
`_kill_existing_libreoffice()` is too aggressive and may kill legitimately running LibreOffice instances.

### Issue 3: Fixed Port Problems
Using fixed port 2002 may cause conflicts if port is already in use.

### Issue 4: Long Timeout
30-second timeout with 1-second intervals is too slow for debugging.

### Issue 5: Poor Error Reporting
No visibility into WHY LibreOffice fails to start.

## SURGICAL FIXES (Minimal, Targeted Changes)

### Fix 1: Simplify LibreOffice Command

**Current (Complex)**:
```python
cmd = [
    'libreoffice',
    '--headless', '--invisible', '--nodefault', '--nolockcheck',
    '--nologo', '--norestore', '--nofirststartwizard',
    f'--accept=socket,host=localhost,port={self.port};urp;StarOffice.ServiceManager'
]
```

**New (Minimal)**:
```python
cmd = [
    'soffice',  # Use soffice instead of libreoffice (more reliable)
    '--headless',
    '--nologo',
    f'--accept=socket,host=localhost,port={self.port};urp;'
]
```

**Why This Works**:
- `soffice` is the actual LibreOffice executable
- Removed all potentially problematic flags
- Simplified accept string

### Fix 2: Skip Aggressive Process Killing

**Current**:
```python
def _start_libreoffice_service(self):
    self._kill_existing_libreoffice()  # ❌ Comment this out
```

**New**:
```python
def _start_libreoffice_service(self):
    # Skip killing existing processes to prevent interference
    # self._kill_existing_libreoffice()
    logger.info("Skipping process cleanup to prevent interference")
```

### Fix 3: Enhanced Port Management

**Current**:
```python
def _find_free_port(self):
    for port in range(2002, 2010):  # Limited range
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    return 2002  # Fixed fallback
```

**New (Improved)**:
```python
def _find_free_port(self):
    """Find a truly free port with better logic"""
    # Try expanded range first
    for port in range(2002, 2030):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('localhost', port))
                logger.info(f"Found free port: {port}")
                return port
        except OSError:
            continue
    
    # If no port found, let OS assign one
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))  # OS assigns port
        port = s.getsockname()[1]
        logger.info(f"OS assigned port: {port}")
        return port
```

### Fix 4: Faster Startup Detection

**Current (Slow)**:
```python
for i in range(30):  # 30 seconds
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', self.port))
        sock.close()
        return True
    except socket.error:
        time.sleep(1)  # 1 second intervals
```

**New (Fast)**:
```python
# Faster detection with more frequent checks
start_time = time.time()
while time.time() - start_time < 10:  # 10 second timeout
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.2)  # Short timeout
        sock.connect(('localhost', self.port))
        sock.close()
        elapsed = time.time() - start_time
        logger.info(f"✅ LibreOffice service ready in {elapsed:.1f}s on port {self.port}")
        return True
    except socket.error:
        # Check if process died
        if self.lo_process.poll() is not None:
            logger.error("LibreOffice process terminated during startup")
            return False
        time.sleep(0.2)  # Check every 0.2 seconds (50 checks total)

logger.error("LibreOffice service failed to start within 10 seconds")
return False
```

### Fix 5: Enhanced Error Logging

**Add detailed error logging**:
```python
def _start_libreoffice_service(self):
    logger.info("=== LibreOffice Service Startup Debug ===")
    logger.info(f"Port: {self.port}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        self.lo_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=True
        )
        logger.info(f"LibreOffice process started with PID: {self.lo_process.pid}")
        
        # Rest of startup logic...
        
    except Exception as e:
        logger.error(f"Failed to start LibreOffice process: {e}")
        return False
    
    # If startup verification fails, log detailed info
    if self.lo_process.poll() is not None:
        stdout, stderr = self.lo_process.communicate()
        logger.error("=== LibreOffice Process Debug Info ===")
        logger.error(f"Exit code: {self.lo_process.returncode}")
        logger.error(f"STDOUT: {stdout.decode('utf-8', errors='ignore')}")
        logger.error(f"STDERR: {stderr.decode('utf-8', errors='ignore')}")
        logger.error("==========================================")
        return False
```

## IMPLEMENTATION STEPS

### Step 1: Backup Original File
```bash
cp /media/erl/New\ Volume/ai_agent/BROWSER\ AGENT/docai_final/DocAI_Native/app/services/libreoffice_uno_converter_improved.py /media/erl/New\ Volume/ai_agent/BROWSER\ AGENT/docai_final/DocAI_Native/app/services/libreoffice_uno_converter_improved.py.backup
```

### Step 2: Apply Surgical Fixes
Make the 5 targeted changes above in the file.

### Step 3: Test Service Startup
```bash
cd /media/erl/New\ Volume/ai_agent/BROWSER\ AGENT/docai_final/DocAI_Native
python3 -c "
from app.services.libreoffice_uno_converter_improved import render_document_with_uno_images
import sys
result = render_document_with_uno_images('/path/to/test.docx')
if result and result.get('success'):
    print('✅ SUCCESS: LibreOffice service working!')
    print(f'Method: {result.get(\"method\")}')
    print(f'Images: {result.get(\"images_found\", 0)}')
else:
    print('❌ FAILED: LibreOffice service not working')
    if result:
        print(f'Error: {result.get(\"error\")}')
    sys.exit(1)
"
```

### Step 4: Verify with DocAI Native App
1. Start the native app: `python3 main.py`
2. Open a document file
3. Verify it displays in the central container

## SUCCESS CRITERIA

✅ **LibreOffice Service Starts**: No more "process died" error
✅ **Document Converts**: HTML output generated successfully  
✅ **App Functions**: Documents display in DocAI Native viewer
✅ **Logs are Clear**: Detailed debug info shows what's happening

## TESTING CHECKLIST

- [ ] LibreOffice service starts without errors
- [ ] Test document converts to HTML
- [ ] HTML content is valid (not empty)
- [ ] Native app can display documents
- [ ] Error logging provides useful information
- [ ] Port allocation works correctly
- [ ] No interference with existing LibreOffice processes

## IF FIXES DON'T WORK

### Diagnostic Steps:
1. Check if `soffice` is in PATH: `which soffice`
2. Test manual LibreOffice headless: `soffice --headless --nologo --accept="socket,host=localhost,port=2003;urp;"`
3. Check port availability: `netstat -tulpn | grep 2002-2030`
4. Test UNO availability: `python3 -c "import uno; print('UNO available')"`

### Alternative Approaches:
1. **Use separate process**: Don't embed, just launch LibreOffice separately
2. **Use different converter**: pandoc, unoconv, or similar tools
3. **HTML-only mode**: Focus on getting existing HTML conversion working

## ROLLBACK PLAN

If the fixes break anything:
```bash
cp /media/erl/New\ Volume/ai_agent/BROWSER\ AGENT/docai_final/DocAI_Native/app/services/libreoffice_uno_converter_improved.py.backup /media/erl/New\ Volume/ai_agent/BROWSER\ AGENT/docai_final/DocAI_Native/app/services/libreoffice_uno_converter_improved.py
```

## EXPECTED TIMELINE

- **Analysis**: 15 minutes ✅ (Done)
- **Implementation**: 30 minutes
- **Testing**: 45 minutes  
- **Documentation**: 30 minutes
- **Total**: 2 hours

This surgical approach focuses ONLY on making LibreOffice UNO service work reliably before attempting any advanced features.