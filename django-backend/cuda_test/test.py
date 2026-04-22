import torch
import sys

def test_pytorch_gpu():
    """测试PyTorch是否能够使用GPU"""
    
    print("=" * 50)
    print("PyTorch GPU 测试工具")
    print("=" * 50)
    
    # 1. 检查PyTorch版本
    print(f"\n1. PyTorch版本: {torch.__version__}")
    
    # 2. 检查CUDA是否可用
    cuda_available = torch.cuda.is_available()
    print(f"\n2. CUDA是否可用: {cuda_available}")
    
    if not cuda_available:
        print("\n❌ CUDA不可用！可能的原因：")
        print("   - 没有安装NVIDIA GPU驱动")
        print("   - 安装了CPU版本的PyTorch")
        print("   - CUDA版本不兼容")
        print("\n解决方案：")
        print("   - 安装NVIDIA驱动: https://www.nvidia.com/Download/index.aspx")
        print("   - 安装GPU版PyTorch: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        return False
    
    # 3. CUDA相关信息
    print(f"\n3. CUDA版本: {torch.version.cuda}")
    print(f"4. cuDNN版本: {torch.backends.cudnn.version()}")
    
    # 4. GPU设备信息
    gpu_count = torch.cuda.device_count()
    print(f"\n5. 可用GPU数量: {gpu_count}")
    
    for i in range(gpu_count):
        print(f"\n   GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"   计算能力: {torch.cuda.get_device_capability(i)}")
        print(f"   显存总量: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
    
    # 5. 当前GPU设备
    current_device = torch.cuda.current_device()
    print(f"\n6. 当前使用的GPU: {current_device}")
    print(f"   设备名称: {torch.cuda.get_device_name(current_device)}")
    
    # 6. 测试GPU计算
    print("\n7. 执行GPU计算测试...")
    try:
        # 创建GPU张量
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        
        # 执行矩阵乘法
        z = torch.matmul(x, y)
        
        # 同步GPU（确保计算完成）
        torch.cuda.synchronize()
        
        print("   ✅ GPU计算成功完成！")
        print(f"   张量形状: {z.shape}")
        print(f"   张量设备: {z.device}")
        
    except Exception as e:
        print(f"   ❌ GPU计算失败: {e}")
        return False
    
    # 7. 内存使用情况
    print("\n8. GPU内存使用情况:")
    print(f"   已分配: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
    print(f"   已缓存: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")
    
    # 8. 清理内存
    torch.cuda.empty_cache()
    
    print("\n" + "=" * 50)
    print("✅ GPU已成功启用，测试通过！")
    print("=" * 50)
    
    return True

def test_basic_operations():
    """测试基本的GPU操作"""
    print("\n" + "=" * 50)
    print("GPU基本操作测试")
    print("=" * 50)
    
    # 创建CPU张量
    cpu_tensor = torch.randn(5, 5)
    print(f"\nCPU张量:\n{cpu_tensor}")
    print(f"设备: {cpu_tensor.device}")
    
    # 移动到GPU
    if torch.cuda.is_available():
        gpu_tensor = cpu_tensor.cuda()
        print(f"\nGPU张量:\n{gpu_tensor}")
        print(f"设备: {gpu_tensor.device}")
        
        # GPU上的操作
        result = gpu_tensor @ gpu_tensor.T  # 矩阵乘以转置
        print(f"\nGPU计算结果形状: {result.shape}")
        print(f"结果设备: {result.device}")
        
        # 移回CPU
        cpu_result = result.cpu()
        print(f"\n移回CPU后的设备: {cpu_result.device}")
        
        return True
    else:
        print("\n❌ CUDA不可用，跳过GPU操作测试")
        return False

if __name__ == "__main__":
    # 运行测试
    success = test_pytorch_gpu()
    
    if success:
        test_basic_operations()
        print("\n🎉 所有测试通过！PyTorch可以正常使用GPU加速。")
        sys.exit(0)
    else:
        print("\n⚠️  GPU测试失败，PyTorch将使用CPU运行。")
        sys.exit(1)