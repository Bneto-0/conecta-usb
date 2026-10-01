"""Integra exclusivamente a janela do processo de vídeo criado pelo Conecta."""
import ctypes
from ctypes import wintypes as w

api = ctypes.WinDLL('user32', use_last_error=True)
CALLBACK = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
api.EnumWindows.argtypes = [CALLBACK, w.LPARAM]
api.GetWindowThreadProcessId.argtypes = [w.HWND, ctypes.POINTER(w.DWORD)]
api.GetParent.argtypes = [w.HWND]
api.GetParent.restype = w.HWND
api.IsWindowVisible.argtypes = [w.HWND]
api.SetParent.argtypes = [w.HWND, w.HWND]
api.SetParent.restype = w.HWND
api.GetWindowLongPtrW.argtypes = [w.HWND, ctypes.c_int]
api.GetWindowLongPtrW.restype = ctypes.c_ssize_t
api.SetWindowLongPtrW.argtypes = [w.HWND, ctypes.c_int, ctypes.c_ssize_t]
api.SetWindowLongPtrW.restype = ctypes.c_ssize_t
api.SetWindowPos.argtypes = [w.HWND, w.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, w.UINT]

def find_process_window(pid):
    matches = []
    @CALLBACK
    def visit(hwnd, _):
        owner = w.DWORD()
        api.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and api.IsWindowVisible(hwnd):
            matches.append(hwnd)
        return True
    api.EnumWindows(visit, 0)
    return matches[0] if matches else None

def embed(hwnd, parent):
    style = api.GetWindowLongPtrW(hwnd, -16)
    style = (style & ~(0x80000000 | 0x00C00000 | 0x00040000)) | 0x40000000
    ctypes.set_last_error(0)
    api.SetWindowLongPtrW(hwnd, -16, style)
    if ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    ctypes.set_last_error(0)
    api.SetParent(hwnd, parent)
    if ctypes.get_last_error() or api.GetParent(hwnd) != parent:
        raise OSError('Não foi possível integrar a janela de vídeo ao aplicativo.')

def resize(hwnd, width, height):
    if not api.SetWindowPos(hwnd, None, 0, 0, max(1, width), max(1, height), 0x0004 | 0x0020 | 0x0040):
        raise ctypes.WinError(ctypes.get_last_error())
