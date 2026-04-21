"""
CUDA GPU Detection and Inference Testing Module

This module provides utilities to detect CUDA availability and test GPU inference capabilities.
"""

import torch
import numpy as np
from typing import Dict, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CUDADetector:
    """Detect and test CUDA GPU availability and capabilities."""

    @staticmethod
    def is_cuda_available() -> bool:
        """
        Check if CUDA is available on the system.
        
        Returns:
            bool: True if CUDA is available, False otherwise.
        """
        return torch.cuda.is_available()

    @staticmethod
    def get_cuda_device_count() -> int:
        """
        Get the number of available CUDA devices (GPUs).
        
        Returns:
            int: Number of available GPUs.
        """
        if not torch.cuda.is_available():
            return 0
        return torch.cuda.device_count()

    @staticmethod
    def get_current_device() -> int:
        """
        Get the current active CUDA device index.
        
        Returns:
            int: Index of current device, or -1 if CPU only.
        """
        if not torch.cuda.is_available():
            return -1
        return torch.cuda.current_device()

    @staticmethod
    def get_device_name(device_id: int = 0) -> str:
        """
        Get the name of a specific CUDA device.
        
        Args:
            device_id: Index of the GPU device.
            
        Returns:
            str: Name of the GPU device.
        """
        if not torch.cuda.is_available() or device_id >= torch.cuda.device_count():
            return "CPU"
        return torch.cuda.get_device_name(device_id)

    @staticmethod
    def get_cuda_version() -> str:
        """
        Get CUDA version information.
        
        Returns:
            str: CUDA version string.
        """
        return torch.version.cuda if torch.cuda.is_available() else "Not Available"

    @staticmethod
    def get_cudnn_version() -> str:
        """
        Get cuDNN version information.
        
        Returns:
            str: cuDNN version string.
        """
        return str(torch.backends.cudnn.version()) if torch.cuda.is_available() else "Not Available"

    @staticmethod
    def get_device_properties(device_id: int = 0) -> Dict[str, any]:
        """
        Get detailed properties of a CUDA device.
        
        Args:
            device_id: Index of the GPU device.
            
        Returns:
            dict: Dictionary containing device properties.
        """
        if not torch.cuda.is_available():
            return {"error": "CUDA not available"}

        if device_id >= torch.cuda.device_count():
            return {"error": f"Device {device_id} not found"}

        props = torch.cuda.get_device_properties(device_id)
        
        return {
            "device_id": device_id,
            "device_name": props.name,
            "total_memory_gb": props.total_memory / (1024 ** 3),
            "major_version": props.major,
            "minor_version": props.minor,
            "multi_processor_count": props.multi_processor_count,
            "max_threads_per_multiprocessor": props.max_threads_per_multi_processor,
        }

    @staticmethod
    def get_memory_info(device_id: int = 0) -> Dict[str, float]:
        """
        Get GPU memory information.
        
        Args:
            device_id: Index of the GPU device.
            
        Returns:
            dict: Dictionary containing memory information (in GB).
        """
        if not torch.cuda.is_available():
            return {"error": "CUDA not available"}

        torch.cuda.reset_peak_memory_stats(device_id)
        torch.cuda.empty_cache()
        
        total_memory = torch.cuda.get_device_properties(device_id).total_memory / (1024 ** 3)
        reserved_memory = torch.cuda.memory_reserved(device_id) / (1024 ** 3)
        allocated_memory = torch.cuda.memory_allocated(device_id) / (1024 ** 3)
        free_memory = reserved_memory - allocated_memory

        return {
            "total_memory_gb": total_memory,
            "reserved_memory_gb": reserved_memory,
            "allocated_memory_gb": allocated_memory,
            "free_memory_gb": free_memory,
        }


class GPUInferenceTest:
    """Test GPU inference capabilities."""

    @staticmethod
    def test_gpu_inference(model_size: int = 1000, test_iterations: int = 5) -> Dict[str, any]:
        """
        Test GPU inference performance.
        
        Args:
            model_size: Size of tensor for testing (default: 1000x1000).
            test_iterations: Number of iterations to run (default: 5).
            
        Returns:
            dict: Results containing GPU availability and performance metrics.
        """
        if not torch.cuda.is_available():
            logger.warning("CUDA is not available. Using CPU.")
            return {"gpu_available": False, "device": "CPU"}

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")

        try:
            # Warm up
            _ = torch.randn(model_size, model_size, device=device)
            torch.cuda.synchronize()

            # Test tensor operations
            results = {
                "gpu_available": True,
                "device_name": torch.cuda.get_device_name(0),
                "cuda_version": torch.version.cuda,
            }

            # Matrix multiplication test
            import time
            times = []
            for _ in range(test_iterations):
                torch.cuda.reset_peak_memory_stats()
                
                start = time.time()
                a = torch.randn(model_size, model_size, device=device)
                b = torch.randn(model_size, model_size, device=device)
                c = torch.mm(a, b)
                torch.cuda.synchronize()
                end = time.time()
                
                times.append(end - start)

            results["avg_inference_time_ms"] = np.mean(times) * 1000
            results["inference_times_ms"] = [t * 1000 for t in times]

            return results

        except Exception as e:
            logger.error(f"GPU inference test failed: {str(e)}")
            return {"gpu_available": False, "error": str(e)}

    @staticmethod
    def test_tensor_on_gpu(tensor_size: Tuple[int, ...] = (100, 100)) -> bool:
        """
        Test if tensors can be moved to GPU.
        
        Args:
            tensor_size: Size of test tensor.
            
        Returns:
            bool: True if tensor operation on GPU successful.
        """
        if not torch.cuda.is_available():
            logger.warning("CUDA not available")
            return False

        try:
            device = torch.device("cuda")
            tensor = torch.randn(tensor_size)
            tensor = tensor.to(device)
            
            # Perform a simple operation
            result = tensor * 2
            
            logger.info("Tensor operation on GPU successful")
            return True
        except Exception as e:
            logger.error(f"Tensor operation on GPU failed: {str(e)}")
            return False


def print_cuda_info():
    """Print comprehensive CUDA and GPU information."""
    detector = CUDADetector()
    
    print("=" * 60)
    print("CUDA and GPU Information")
    print("=" * 60)
    
    print(f"\n1. CUDA Available: {detector.is_cuda_available()}")
    
    if detector.is_cuda_available():
        print(f"2. Number of GPUs: {detector.get_cuda_device_count()}")
        print(f"3. Current Device: {detector.get_current_device()}")
        print(f"4. CUDA Version: {detector.get_cuda_version()}")
        print(f"5. cuDNN Version: {detector.get_cudnn_version()}")
        
        for i in range(detector.get_cuda_device_count()):
            print(f"\n--- GPU {i}: {detector.get_device_name(i)} ---")
            
            props = detector.get_device_properties(i)
            for key, value in props.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
            
            memory = detector.get_memory_info(i)
            print(f"\n  Memory Info:")
            for key, value in memory.items():
                print(f"    {key}: {value:.2f}")
    else:
        print("CUDA is not available. GPU inference is not possible.")
    
    print("\n" + "=" * 60)


def test_inference_performance():
    """Run GPU inference performance test."""
    print("\n" + "=" * 60)
    print("GPU Inference Performance Test")
    print("=" * 60 + "\n")
    
    tester = GPUInferenceTest()
    results = tester.test_gpu_inference(model_size=1000, test_iterations=5)
    
    print("Results:")
    for key, value in results.items():
        if isinstance(value, list):
            print(f"  {key}: {[f'{v:.4f}' for v in value]}")
        elif isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Print CUDA and GPU information
    print_cuda_info()
    
    # Test GPU inference
    test_inference_performance()
    
    # Test tensor operations on GPU
    print("\nTesting tensor operations on GPU...")
    tester = GPUInferenceTest()
    success = tester.test_tensor_on_gpu()
    print(f"Tensor GPU test: {'✓ Passed' if success else '✗ Failed'}")
