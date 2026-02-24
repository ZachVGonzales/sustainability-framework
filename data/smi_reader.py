import ctypes
import signal
import time
import argparse
import pynvml
from pynvml import (
    nvmlInit,
    nvmlShutdown,
    nvmlDeviceGetCount,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetName,
    nvmlDeviceGetUUID,
    nvmlDeviceGetPowerUsage,
    nvmlDeviceGetTemperature,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetUtilizationRates,
    nvmlDeviceGetPerformanceState,
    NVML_TEMPERATURE_GPU,
    NVMLError,
    _nvmlGetFunctionPointer
)


HEADER = (
    "Timestamp,Name,GPU Index,UUID,Power Draw (W),Temperature (C),"
    "Memory Used (MiB),Memory Utilization (%),GPU Utilization (%),Pstate"
)


_stop = False


def _handle_stop(signum, frame):
    global _stop
    _stop = True


def _safe_read(call, default=""):
    try:
        return call()
    except NVMLError:
        return default


def _to_str(x):
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="replace")
    return str(x)


def _parse_interval_seconds(args_interval):
    if args_interval is not None:
        try:
            args_interval = float(args_interval)
            return max(0.1, args_interval)
        except ValueError:
            print(f"Invalid interval '{args_interval}' only floating point values are accepted. Using 1.0 now!", flush=True)
            return 1.0

    return 1.0


def _validate_gpu_indices(gpu_indices, device_count):
    seen = set()
    normalized = []
    for i in gpu_indices:
        if i not in seen:
            normalized.append(i)
            seen.add(i)

    if device_count <= 0:
        raise SystemExit("ERROR: No NVIDIA GPUs found (nvmlDeviceGetCount() returned 0).")

    invalid = [i for i in normalized if i < 0 or i >= device_count]
    if invalid:
        raise SystemExit(
            f"ERROR: Requested GPU indices {invalid} do not exist. "
            f"Valid range is 0..{device_count - 1}."
        )
    return normalized


# nvmlMemory_v2_t from NVML headers: total, reserved, free, used + version field
class _nvmlMemory_v2_t(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint),
        ("total", ctypes.c_ulonglong),
        ("reserved", ctypes.c_ulonglong),
        ("free", ctypes.c_ulonglong),
        ("used", ctypes.c_ulonglong),
    ]


def _nvml_struct_version(ctype, ver: int) -> int:
    # NVML_STRUCT_VERSION(type, ver) = sizeof(type) | (ver << 24)
    return ctypes.sizeof(ctype) | (ver << 24)


NVML_MEMORY_V2_VERSION = _nvml_struct_version(_nvmlMemory_v2_t, 2)


def _get_memory_used_mib(handle):
    mib = 1024 * 1024
    
    # Get raw function pointer even if pynvml doesn't expose a wrapper
    fn = _nvmlGetFunctionPointer("nvmlDeviceGetMemoryInfo_v2")
    
    # pynvml provides the handle type alias
    c_dev_t = getattr(pynvml, "c_nvmlDevice_t", ctypes.c_void_p)
    fn.argtypes = [c_dev_t, ctypes.POINTER(_nvmlMemory_v2_t)]
    fn.restype = ctypes.c_int

    mem = _nvmlMemory_v2_t()
    mem.version = NVML_MEMORY_V2_VERSION

    ret = fn(handle, ctypes.byref(mem))
    if ret != 0:
        raise NVMLError(ret)

    # "Actual used" (allocated) excludes reserved
    return max(0, int(mem.used - mem.reserved)) // mib


def _read_smi(gpu_idx):
    handle = nvmlDeviceGetHandleByIndex(gpu_idx)

    gpu_name = _to_str(_safe_read(lambda: nvmlDeviceGetName(handle)))
    gpu_uuid = _to_str(_safe_read(lambda: nvmlDeviceGetUUID(handle)))
    gpu_power_w = _safe_read(lambda: nvmlDeviceGetPowerUsage(handle) / 1000.0)
    gpu_temp_c = _safe_read(lambda: nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU))
    gpu_mem_used_mib = _safe_read(lambda: _get_memory_used_mib(handle))
    util = _safe_read(lambda: nvmlDeviceGetUtilizationRates(handle), None)
    gpu_mem_util = util.memory if util else ""
    gpu_util = util.gpu if util else ""
    gpu_pstate = _safe_read(lambda: f"P{nvmlDeviceGetPerformanceState(handle)}")
    
    return {
        "name": gpu_name,
        "uuid": gpu_uuid,
        "power_w": gpu_power_w,
        "temp_c": gpu_temp_c,
        "memory_mib": gpu_mem_used_mib,
        "memory_util": gpu_mem_util,
        "gpu_util": gpu_util,
        "pstate": gpu_pstate
    }


"""
Don't want two mains in colab
"""

# def main():
#     parser = argparse.ArgumentParser(description="NVML-based GPU telemetry CSV printer (stdout).")
#     parser.add_argument("--interval", type=float, help="Sampling interval in seconds (default: 1.0)")
#     parser.add_argument("--gpus", nargs="+", default=[0], type=int, help="GPU indices to sample. Examples: --gpus 0 1 2  OR  --gpus 1. Default: 0")

#     args = parser.parse_args()

#     interval = _parse_interval_seconds(args.interval)
#     gpu_indices = args.gpus

#     signal.signal(signal.SIGINT, _handle_stop)
#     signal.signal(signal.SIGTERM, _handle_stop)

#     nvmlInit()
#     try:
#         device_count = nvmlDeviceGetCount()
#         _validate_gpu_indices(gpu_indices, device_count)

#         print(HEADER, flush=True)

#         next_t = time.monotonic()
#         while not _stop:
#             ts_ms = int(time.time() * 1000)

#             for idx in gpu_indices:
#                 gpu_values = _read_smi(idx)

#                 print(
#                     f"{ts_ms},{gpu_values['name']},{idx},{gpu_values['uuid']},{gpu_values['power_w']},"
#                     f"{gpu_values['temp_c']},{gpu_values['memory_mib']},{gpu_values['memory_util']},"
#                     f"{gpu_values['gpu_util']},{gpu_values['pstate']}",
#                     flush=True
#                 )

#             next_t += interval
#             time.sleep(max(0.0, next_t - time.monotonic()))

#     finally:
#         nvmlShutdown()
