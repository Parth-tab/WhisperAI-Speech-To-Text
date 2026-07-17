def _get_windows_default_communications_device_name():
    try:
        import ctypes
        from ctypes import wintypes
        from ctypes.wintypes import DWORD, WORD, BYTE
        
        class GUID(ctypes.Structure):
            _fields_ = [("Data1", DWORD), ("Data2", WORD), ("Data3", WORD), ("Data4", BYTE * 8)]
        
        class PROPVARIANT(ctypes.Structure):
            class _U(ctypes.Union):
                _fields_ = [("pwszVal", ctypes.c_wchar_p), ("ulVal", ctypes.c_ulong), ("boolVal", ctypes.c_short)]
            _fields_ = [("vt", ctypes.c_ushort), ("wReserved1", ctypes.c_ushort), ("wReserved2", ctypes.c_ushort), ("wReserved3", ctypes.c_ushort), ("u", _U)]
        
        CLSID_MMDeviceEnumerator = GUID(0xbcde0395, 0xe52f, 0x467c, (BYTE*8)(0x8e,0x3d,0xc4,0x57,0x92,0x91,0x69,0x2e))
        IID_IMMDeviceEnumerator = GUID(0xa95664d2, 0x9614, 0x4f35, (BYTE*8)(0xa7,0x46,0xde,0x8d,0xb6,0x36,0x17,0xe6))
        PKEY_Device_FriendlyName = type("PROPERTYKEY", (ctypes.Structure,), {"_fields_": [("fmtid", GUID), ("pid", DWORD)]})(GUID(0xa45c254e, 0xdf1c, 0x4efd, (BYTE*8)(0x80,0x20,0x67,0xd1,0x46,0xa8,0x50,0xe0)), 14)
        
        ole32 = ctypes.windll.ole32
        ole32.CoInitialize(None)
        
        class IPropertyStoreVtbl(ctypes.Structure):
            _fields_ = [("QueryInterface", ctypes.c_void_p), ("AddRef", ctypes.c_void_p), ("Release", ctypes.c_void_p), ("GetCount", ctypes.c_void_p), ("GetAt", ctypes.c_void_p), ("GetValue", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.POINTER(type(PKEY_Device_FriendlyName)), ctypes.POINTER(PROPVARIANT)))]
        class IPropertyStore(ctypes.Structure):
            _fields_ = [("lpVtbl", ctypes.POINTER(IPropertyStoreVtbl))]
        class IMMDeviceVtbl(ctypes.Structure):
            _fields_ = [("QueryInterface", ctypes.c_void_p), ("AddRef", ctypes.c_void_p), ("Release", ctypes.c_void_p), ("Activate", ctypes.c_void_p), ("OpenPropertyStore", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.POINTER(IPropertyStore)))), ("GetId", ctypes.c_void_p), ("GetState", ctypes.c_void_p)]
        class IMMDevice(ctypes.Structure):
            _fields_ = [("lpVtbl", ctypes.POINTER(IMMDeviceVtbl))]
        class IMMDeviceEnumeratorVtbl(ctypes.Structure):
            _fields_ = [("QueryInterface", ctypes.c_void_p), ("AddRef", ctypes.c_void_p), ("Release", ctypes.c_void_p), ("EnumAudioEndpoints", ctypes.c_void_p), ("GetDefaultAudioEndpoint", ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.POINTER(IMMDevice))))]
        class IMMDeviceEnumerator(ctypes.Structure):
            _fields_ = [("lpVtbl", ctypes.POINTER(IMMDeviceEnumeratorVtbl))]
        
        enum_ptr = ctypes.POINTER(IMMDeviceEnumerator)()
        if ole32.CoCreateInstance(ctypes.byref(CLSID_MMDeviceEnumerator), None, 1, ctypes.byref(IID_IMMDeviceEnumerator), ctypes.byref(enum_ptr)) == 0:
            try:
                dev_ptr = ctypes.POINTER(IMMDevice)()
                if enum_ptr.contents.lpVtbl.contents.GetDefaultAudioEndpoint(enum_ptr, 1, 2, ctypes.byref(dev_ptr)) == 0:
                    try:
                        store_ptr = ctypes.POINTER(IPropertyStore)()
                        if dev_ptr.contents.lpVtbl.contents.OpenPropertyStore(dev_ptr, 0, ctypes.byref(store_ptr)) == 0:
                            try:
                                prop = PROPVARIANT()
                                if store_ptr.contents.lpVtbl.contents.GetValue(store_ptr, ctypes.byref(PKEY_Device_FriendlyName), ctypes.byref(prop)) == 0:
                                    name = prop.u.pwszVal
                                    ole32.PropVariantClear(ctypes.byref(prop))
                                    return name
                            finally:
                                if getattr(store_ptr.contents.lpVtbl.contents.Release, "argtypes", None) is None:
                                    store_ptr.contents.lpVtbl.contents.Release.argtypes = [ctypes.c_void_p]
                                    store_ptr.contents.lpVtbl.contents.Release.restype = ctypes.c_ulong
                                store_ptr.contents.lpVtbl.contents.Release(store_ptr)
                    finally:
                        if getattr(dev_ptr.contents.lpVtbl.contents.Release, "argtypes", None) is None:
                            dev_ptr.contents.lpVtbl.contents.Release.argtypes = [ctypes.c_void_p]
                            dev_ptr.contents.lpVtbl.contents.Release.restype = ctypes.c_ulong
                        dev_ptr.contents.lpVtbl.contents.Release(dev_ptr)
            finally:
                if getattr(enum_ptr.contents.lpVtbl.contents.Release, "argtypes", None) is None:
                    enum_ptr.contents.lpVtbl.contents.Release.argtypes = [ctypes.c_void_p]
                    enum_ptr.contents.lpVtbl.contents.Release.restype = ctypes.c_ulong
                enum_ptr.contents.lpVtbl.contents.Release(enum_ptr)
    except Exception:
        pass
    finally:
        ole32.CoUninitialize()
    return None
