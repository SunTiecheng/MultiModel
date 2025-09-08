# 打开（或创建）cameras.txt 文件，准备写入
with open('cameras.txt', 'w') as file:
    # 循环生成 1 到 150 的序号
    for i in range(1, 151):
        # 格式化输出内容
        # line = f"{i} PINHOLE 1920 1080 2666.6666666666665 2250.0 960 540\n"
        line = f"{i} PINHOLE 1620 1080 2250.0 2250.0 810 540\n"
        # line = f"{i} PINHOLE 1620 1080 134305.0 131350.0 810 540\n"
        # line = f"{i} OPENCV 1920 1080 2666.6666666666665 2250.0 960 540 0 0 0 0\n"
        # line = f"1 PINHOLE 1920 1080 2666.6666666666665 2250.0 960 540\n"
        # 写入到文件
        file.write(line)

print("文件生成完毕，保存为 cameras.txt")
