from dataclasses import dataclass


@dataclass
class InferenceRecord:
    example_id: int
    input_text: str
    input_tokens: int
    output_text: str
    output_tokens: int
    new_tokens: int
    inference_time_s: float
    tokens_per_second: float
    gpu_num_samples: int
    gpu_duration_ms: int
    gpu_power_avg_w: float
    gpu_power_max_w: float
    gpu_power_min_w: float
    gpu_memory_avg_mib: float
    gpu_memory_max_mib: int
    gpu_gpu_util_avg: float
    gpu_gpu_util_max: int
    gpu_temp_avg_c: float
    gpu_temp_max_c: int
    gpu_energy_j: float
