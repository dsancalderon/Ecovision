"""Enumerate Windows DirectShow camera names, without opening their video streams."""
import ctypes as C
import sys
import uuid


def available_cameras():
    if sys.platform != 'win32':
        return []
    HRESULT = C.c_long
    pointer = C.c_void_p

    class GUID(C.Structure):
        _fields_ = [('bytes', C.c_ubyte * 16)]

    def guid(value):
        return GUID.from_buffer_copy(uuid.UUID(value).bytes_le)

    def call(obj, slot, result, args, *values):
        table = C.cast(obj, C.POINTER(C.POINTER(pointer))).contents
        return C.WINFUNCTYPE(result, pointer, *args)(table[slot])(obj, *values)

    def release(obj):
        if obj:
            call(obj, 2, C.c_ulong, [])

    ole = C.WinDLL('ole32')
    ole.CoInitializeEx.argtypes = [pointer, C.c_ulong]
    ole.CoInitializeEx.restype = HRESULT
    # HRESULT handling is explicit so an already initialized request thread is safe.
    initialized = ole.CoInitializeEx(None, 2)
    if initialized not in (0, 1, -2147417850):
        raise OSError('No se pudo consultar las cámaras de Windows.')
    device_enum, monikers = pointer(), pointer()
    devices = []
    try:
        clsid = guid('62BE5D10-60EB-11D0-BD3B-00A0C911CE86')
        interface = guid('29840822-5B84-11D0-BD3B-00A0C911CE86')
        category = guid('860BB310-5D01-11D0-BD3B-00A0C911CE86')
        property_bag = guid('55272A00-42CB-11CE-8135-00AA004BB851')
        ole.CoCreateInstance.argtypes = [C.POINTER(GUID), pointer, C.c_ulong, C.POINTER(GUID), C.POINTER(pointer)]
        if ole.CoCreateInstance(C.byref(clsid), None, 1, C.byref(interface), C.byref(device_enum)) < 0:
            raise OSError('No se pudo enumerar las cámaras de Windows.')
        hr = call(device_enum, 3, HRESULT, [C.POINTER(GUID), C.POINTER(pointer), C.c_ulong], C.byref(category), C.byref(monikers), 0)
        if hr == 1:
            return []
        if hr < 0:
            raise OSError('No se pudo leer la lista de cámaras.')
        while True:
            moniker, bag = pointer(), pointer()
            fetched = C.c_ulong()
            if call(monikers, 3, HRESULT, [C.c_ulong, C.POINTER(pointer), C.POINTER(C.c_ulong)], 1, C.byref(moniker), C.byref(fetched)) != 0:
                break
            try:
                name = f'Cámara {len(devices) + 1}'
                if call(moniker, 9, HRESULT, [pointer, pointer, C.POINTER(GUID), C.POINTER(pointer)], None, None, C.byref(property_bag), C.byref(bag)) >= 0:
                    variant = C.create_string_buffer(24 if C.sizeof(pointer) == 8 else 16)
                    if call(bag, 3, HRESULT, [C.c_wchar_p, pointer, pointer], 'FriendlyName', C.byref(variant), None) >= 0:
                        if C.c_ushort.from_buffer(variant).value == 8:
                            name = C.wstring_at(pointer.from_buffer(variant, 8).value)
                        C.WinDLL('oleaut32').VariantClear(C.byref(variant))
                devices.append({'index': len(devices), 'name': name})
            finally:
                release(bag)
                release(moniker)
        return devices
    finally:
        release(monikers)
        release(device_enum)
        if initialized in (0, 1):
            ole.CoUninitialize()
