import json
import numpy as np
import torch


class TorchUtils:

    @staticmethod
    # 将嵌入向量转换为数组
    def convert_to_array(x, data_type=torch.float32):
        """
        将嵌入向量转换为数组。
        """
        try:
            # 假设每个元素是 JSON 编码的
            return torch.tensor(np.array(json.loads(x)), dtype=data_type)
        except:
            # 如果转换失败，返回 None 或适当的默认值
            return None
        
    @staticmethod # 设备转移，如果给定的多个参数不在 device 上，则将它们转移到 device 上, 并按照原始顺序返回
    def move_to_device(*args, device):
        """
        设备转移，如果给定的多个参数不在 device 上，则将它们转移到 device 上, 并按照原始顺序返回。
        """
        # 如果没有指定设备，则返回原始参数
        if device is None:
            return args
        
        return [arg.to(device) for arg in args]
