import socket
import random
from datetime import datetime
import select


def udpserver():
    # 服务器设置
    server_ip = '127.0.0.1'  # 服务器的IP地址
    server_port = 6666       # 服务器的端口号
    loss_probability = 0.3   # 丢包概率设为30%

    # 创建UDP套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))  # 绑定IP和端口
    server_socket.setblocking(0)    # 设置套接字为非阻塞模式
    print(f"服务器正在运行在 {server_ip}:{server_port}")

    seq_queues = {}  # 用于记录已经接受到的每个客户端发送的数据包序列号，避免处理重复的数据包
    try:
        while True:
            readable, _, _ = select.select([server_socket], [], [], 0.5)
            for sock in readable:
                client_data, client_address = sock.recvfrom(4096)  # 从客户端接收数据
                decoded_data = client_data.decode()
                if decoded_data == 'SYN':
                    print(f"收到客户端{client_address}的SYN包")
                    sock.sendto(b'SYN-ACK', client_address)      # 收到SYN消息，回复SYN-ACK
                    print(f"向客户端{client_address}返回SYN-ACK包")

                elif decoded_data == 'CONNECT-ACK':
                    print(f"成功与客户端{client_address}建立连接！")
                    break

                elif decoded_data == 'FIN':
                    print(f"\n收到客户端{client_address}的FIN包，发送FIN-ACK确认包")
                    sock.sendto(b'FIN-ACK', client_address)      # 收到FIN消息，回复FIN-ACK
                    print(f"发送FIN包，服务器也已准备好关闭连接")
                    sock.sendto(b'FIN', client_address)          # 收到FIN消息，回复FIN

                elif decoded_data == 'RELEASE-ACK':
                    print(f"成功与客户端{client_address}释放连接！\n")
                    break

                else:
                    # 解析序列号和版本号
                    seq_no, ver = int.from_bytes(client_data[:2], 'big'), client_data[2]
                    if client_address not in seq_queues:
                        seq_queues[client_address] = []
                    if seq_no in seq_queues[client_address]:
                        print(f"收到客户端{client_address}重传的数据包：序号 {seq_no}，版本 {ver}")
                        continue  # 如果序列号已经处理过，跳过此次处理
                    seq_queues[client_address].append(seq_no)  # 记录序列号
                    print(f"\n收到来自客户端{client_address}的数据包：序号 {seq_no}，版本 {ver}")

                    if random.random() < loss_probability:
                        print(f"向客户端{client_address}模拟丢包")
                        continue  # 根据设置的丢包概率随机丢弃一些包

                    # 将服务器时间附加到响应中
                    server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    response = client_data[:3] + server_time.encode()
                    sock.sendto(response, client_address)
                    print(f"向客户端{client_address}回复报文，包含服务器时间: {server_time}")
    finally:
        server_socket.close()  # 最终关闭服务器套接字
        print("服务器套接字已关闭。")

if __name__ == "__main__":
    udpserver()
