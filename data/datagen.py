"""
Generates a dataset with the following structure:

example id | input tokens | input string | framework output 1 | framework output 2 | ... | framework output N | output tokens | output string

outputted dataset is saved in a parquet file.

input dataset is given from env variable DATAGEN_DATASET
input model is given from env variable DATAGEN_MODEL
"""

import os
import sys
import time
import signal
import threading
import re
from datetime import datetime

from dotenv import load_dotenv
import torch
import pandas as pd
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, GenerationConfig
from pynvml import nvmlInit, nvmlShutdown

# Load environment variables from .env file (if it exists)
load_dotenv()

# Global flag for graceful shutdown
_interrupted = False


def _handle_sigint(signum, frame):
    """Handle SIGINT (Ctrl+C) for graceful shutdown."""
    global _interrupted
    if _interrupted:
        # Second interrupt - force exit
        print("\nForced exit.", flush=True)
        sys.exit(1)
    _interrupted = True
    print("\n\nInterrupt received. Finishing current example and saving results...", flush=True)

# Add smi_reader to path if needed
sys.path.insert(0, "/content") # for colab
from smi_reader import _read_smi


class GPUMonitor:
    """Background thread that samples GPU metrics at a given interval."""
    
    def __init__(self, gpu_index: int = 0, interval: float = 0.1):
        self.gpu_index = gpu_index
        self.interval = interval
        self.samples = []
        self._stop_event = threading.Event()
        self._thread = None
    
    def _sample_loop(self):
        while not self._stop_event.is_set():
            sample = _read_smi(self.gpu_index)
            sample["timestamp_ms"] = int(time.time() * 1000)
            self.samples.append(sample)
            time.sleep(self.interval)
    
    def start(self):
        self.samples = []
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        return self.samples
    
    def get_summary(self):
        """Compute summary statistics from collected samples."""
        if not self.samples:
            return {}
        
        power_values = [s["power_w"] for s in self.samples if isinstance(s["power_w"], (int, float))]
        memory_values = [s["memory_mib"] for s in self.samples if isinstance(s["memory_mib"], (int, float))]
        gpu_util_values = [s["gpu_util"] for s in self.samples if isinstance(s["gpu_util"], (int, float))]
        temp_values = [s["temp_c"] for s in self.samples if isinstance(s["temp_c"], (int, float))]
        
        summary = {
            "num_samples": len(self.samples),
            "duration_ms": self.samples[-1]["timestamp_ms"] - self.samples[0]["timestamp_ms"] if len(self.samples) > 1 else 0,
        }
        
        if power_values:
            summary["power_avg_w"] = sum(power_values) / len(power_values)
            summary["power_max_w"] = max(power_values)
            summary["power_min_w"] = min(power_values)
        
        if memory_values:
            summary["memory_avg_mib"] = sum(memory_values) / len(memory_values)
            summary["memory_max_mib"] = max(memory_values)
        
        if gpu_util_values:
            summary["gpu_util_avg"] = sum(gpu_util_values) / len(gpu_util_values)
            summary["gpu_util_max"] = max(gpu_util_values)
        
        if temp_values:
            summary["temp_avg_c"] = sum(temp_values) / len(temp_values)
            summary["temp_max_c"] = max(temp_values)
        
        # Estimate energy in Joules (power * time)
        if power_values and summary["duration_ms"] > 0:
            summary["energy_j"] = summary["power_avg_w"] * (summary["duration_ms"] / 1000.0)
        
        return summary


def get_input_text(example, text_columns=None):
    """Extract input text from a dataset example."""
    if text_columns:
        for col in text_columns:
            if col in example and example[col]:
                return str(example[col])
    
    # Common column names for text
    common_cols = ["text", "input", "prompt", "question", "content", "sentence", "instruction"]
    for col in common_cols:
        if col in example and example[col]:
            return str(example[col])
    
    # Fallback: use first string column
    for key, value in example.items():
        if isinstance(value, str) and value.strip():
            return value
    
    return ""


def run_inference(pipe, input_text, max_new_tokens=128):
    """Run inference on a single input and return output with timing."""
    
    # Format as chat message with explicit brevity instruction
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Provide concise, direct answers."},
        {"role": "user", "content": input_text + "\n\nPlease answer concisely in <= 60 words (or 3 sentences)."}
    ]
    
    # Count input tokens
    tokenizer = pipe.tokenizer
    formatted_input = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    input_tokens = tokenizer(formatted_input, return_tensors="pt")["input_ids"]
    input_token_count = input_tokens.shape[1]
    
    # Use GenerationConfig for consistent generation settings
    gen_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=False,             # greedy decoding -> shorter, predictable
        repetition_penalty=1.2,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id else tokenizer.eos_token_id,
    )
    
    start_time = time.perf_counter()
    
    # Pass generation_config (not separate kwargs)
    output = pipe(messages, generation_config=gen_config)
    
    end_time = time.perf_counter()
    inference_time_s = end_time - start_time
    
    # Extract generated text - handle both string and list formats
    raw_output = output[0]["generated_text"]
    if isinstance(raw_output, list):
        # If it's a list of message dicts, get the last assistant message
        output_text = raw_output[-1]["content"] if raw_output else ""
    else:
        output_text = raw_output
    
    # Post-process: keep only the first 3 sentences to enforce brevity
    sentences = re.split(r'(?<=[.!?])\s+', output_text.strip())
    short_text = ' '.join(sentences[:3])   # keep first 3 sentences
    if len(short_text) > 600:              # safety truncate by chars
        short_text = short_text[:600].rsplit(' ', 1)[0] + "..."
    
    # Count output tokens (of the truncated text)
    output_tokens = tokenizer(short_text, return_tensors="pt")["input_ids"]
    new_tokens = output_tokens.shape[1]
    output_token_count = input_token_count + new_tokens
    
    return {
        "input_tokens": input_token_count,
        "output_tokens": output_token_count,
        "new_tokens": new_tokens,
        "output_text": short_text,
        "inference_time_s": inference_time_s,
        "tokens_per_second": new_tokens / inference_time_s if inference_time_s > 0 else 0,
    }


def main():
    # Load configuration from environment variables
    dataset_name = os.environ.get("DATAGEN_DATASET")
    model_name = os.environ.get("DATAGEN_MODEL", "NousResearch/Hermes-3-Llama-3.2-3B")
    
    if not dataset_name:
        raise ValueError("DATAGEN_DATASET environment variable must be set")
    if not model_name:
        raise ValueError("DATAGEN_MODEL environment variable must be set")
    
    # Optional configuration
    dataset_split = os.environ.get("DATAGEN_SPLIT", "train")
    dataset_config = os.environ.get("DATAGEN_CONFIG", None)
    max_samples = int(os.environ.get("DATAGEN_MAX_SAMPLES", "100"))
    max_new_tokens = int(os.environ.get("DATAGEN_MAX_NEW_TOKENS", "128"))  # Default 128 for shorter outputs
    gpu_index = int(os.environ.get("DATAGEN_GPU_INDEX", "0"))
    output_file = os.environ.get("DATAGEN_OUTPUT", "datagen_output.parquet")
    text_column = os.environ.get("DATAGEN_TEXT_COLUMN", None)
    sampling_interval = float(os.environ.get("DATAGEN_SAMPLE_INTERVAL", "0.1"))
    save_interval = int(os.environ.get("DATAGEN_SAVE_INTERVAL", "10"))  # Save every N examples (0 = only at end)
    
    text_columns = text_column.split(",") if text_column else None
    
    print(f"Configuration:")
    print(f"  Dataset: {dataset_name} (split: {dataset_split}, config: {dataset_config})")
    print(f"  Model: {model_name}")
    print(f"  Max samples: {max_samples}")
    print(f"  Max new tokens: {max_new_tokens}")
    print(f"  GPU index: {gpu_index}")
    print(f"  Output file: {output_file}")
    print(f"  Sampling interval: {sampling_interval}s")
    print(f"  Save interval: {save_interval if save_interval > 0 else 'only at end'}")
    print()
    
    # Set up SIGINT handler for graceful shutdown
    signal.signal(signal.SIGINT, _handle_sigint)
    
    # Initialize NVML for GPU monitoring
    nvmlInit()
    
    try:
        # Load dataset
        print(f"Loading dataset '{dataset_name}'...")
        if dataset_config:
            dataset = load_dataset(dataset_name, dataset_config, split=dataset_split)
        else:
            dataset = load_dataset(dataset_name, split=dataset_split)
        
        # Limit samples
        if max_samples and max_samples < len(dataset):
            dataset = dataset.select(range(max_samples))
        
        print(f"Loaded {len(dataset)} examples")
        print()
        
        # Load model and tokenizer
        print(f"Loading model '{model_name}'...")
        device = torch.device(f"cuda:{gpu_index}" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {device}")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True,
        )

        model.eval()
        
        # Create pipeline following official example
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
        )
        
        print("Model loaded successfully")
        print()
        
        # Initialize GPU monitor
        gpu_monitor = GPUMonitor(gpu_index=gpu_index, interval=sampling_interval)
        
        # Process each example
        results = []
        
        for idx, example in enumerate(dataset):
            # Check for interrupt
            if _interrupted:
                print(f"\nStopping after {len(results)} examples due to interrupt.")
                break
            
            input_text = get_input_text(example, text_columns)
            
            if not input_text:
                print(f"[{idx+1}/{len(dataset)}] Skipping example {idx}: no input text found")
                continue
            
            print(f"[{idx+1}/{len(dataset)}] Processing example {idx} ({len(input_text)} chars)...")
            
            # Start GPU monitoring
            gpu_monitor.start()
            
            # Run inference
            inference_result = run_inference(
                pipe, input_text, max_new_tokens=max_new_tokens
            )
            
            # Stop GPU monitoring and get summary
            gpu_monitor.stop()
            gpu_summary = gpu_monitor.get_summary()
            
            # Build result row
            result = {
                "example_id": idx,
                "input_text": input_text,
                "input_tokens": inference_result["input_tokens"],
                "output_text": inference_result["output_text"],
                "output_tokens": inference_result["output_tokens"],
                "new_tokens": inference_result["new_tokens"],
                "inference_time_s": inference_result["inference_time_s"],
                "tokens_per_second": inference_result["tokens_per_second"],
                **{f"gpu_{k}": v for k, v in gpu_summary.items()},
            }
            
            results.append(result)
            
            # Print progress
            print(f"    Input tokens: {inference_result['input_tokens']}, "
                  f"New tokens: {inference_result['new_tokens']}, "
                  f"Time: {inference_result['inference_time_s']:.2f}s, "
                  f"Tokens/s: {inference_result['tokens_per_second']:.1f}")
            if "power_avg_w" in gpu_summary:
                print(f"    GPU Power: {gpu_summary['power_avg_w']:.1f}W avg, "
                      f"Memory: {gpu_summary.get('memory_max_mib', 'N/A')} MiB max, "
                      f"Energy: {gpu_summary.get('energy_j', 0):.2f}J")
            print()
            
            # Save intermediate results if save_interval is set
            if save_interval > 0 and len(results) % save_interval == 0:
                print(f"Saving checkpoint at {len(results)} examples to '{output_file}'...")
                df = pd.DataFrame(results)
                df.to_parquet(output_file, index=False)
                print(f"Checkpoint saved.\n")
        
        # Save results to parquet
        if results:
            print(f"Saving {len(results)} results to '{output_file}'...")
            df = pd.DataFrame(results)
            df.to_parquet(output_file, index=False)
            print("Done!")
        else:
            print("No results to save.")
        
        # Print summary statistics
        if results:
            print()
            print("=== Summary ===")
            print(f"Total examples processed: {len(results)}")
            print(f"Total inference time: {sum(r['inference_time_s'] for r in results):.2f}s")
            print(f"Average tokens/second: {sum(r['tokens_per_second'] for r in results) / len(results):.1f}")
            
            energy_values = [r.get("gpu_energy_j", 0) for r in results if r.get("gpu_energy_j")]
            if energy_values:
                print(f"Total energy consumed: {sum(energy_values):.2f}J")
                print(f"Average energy per example: {sum(energy_values) / len(energy_values):.2f}J")
    
    finally:
        nvmlShutdown()


if __name__ == "__main__":
    main()

