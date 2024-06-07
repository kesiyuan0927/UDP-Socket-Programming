import socket
import time
import statistics
from datetime import datetime
import sys

# 考虑程序健壮性，对命令行参数进行检查
if len(sys.argv) != 3:
    print("您输入的参数个数有误，请重新输入！\n格式为：python udpclient.py <server_ip> <server_port>")
    sys.exit(1)
try:
    server_ip = sys.argv[1]  # 服务器IP地址
    server_port = int(sys.argv[2])  # 服务器端口
    sum_requests = 12  # 发送请求的总数
    timeout = 0.1  # 超时时间设置为100毫秒
    max_attempts = 3  # 最大重传次数
    RTTs = []  # 跟踪往返时间(RTT)和丢包情况
    received_packets = 0  # 成功收到的服务器的数据包
    first_response_time = None  # 初始化时间变量
    last_response_time = None  # 初始化时间变量
except Exception:
    print("您输入的参数格式有误，请检查后重新输入！\n格式为：python udpclient.py <server_ip> <server_port>")
    sys.exit(1)


# 模拟TCP三次握手
def tcp_connect(client_socket):
    try:
        print(f"正在与服务器{(server_ip, server_port)}建立连接...")
        client_socket.sendto(b'SYN', (server_ip, server_port))
        print(f"已向服务器发送SYN包")
        response, _ = client_socket.recvfrom(4096)
        if response.decode() == 'SYN-ACK':
            print(f"成功收到服务器的SYN-ACK包, 正在发送CONNECT-ACK包...")
            client_socket.sendto(b'CONNECT-ACK', (server_ip, server_port))
            print(f"已发送CONNECT-ACK包，成功与服务器{(server_ip, server_port)}建立连接！\n")
    except Exception:
        print(f"与服务器{(server_ip, server_port)}连接建立失败！\n请检查与服务器IP地址和端口是否输入正确，客户端与服务器之间的通信是否正常！")
        return False
    return True


def send_message(client_socket, seq_no, attempts):
    global received_packets, first_response_time, last_response_time
    ver = 2  # 协议版本
    # 存放无意义的字母序列作为填充
    data = seq_no.to_bytes(2, 'big') + bytes([ver]) + b'abcdefgabcdefg' * 100
    try:
        client_socket.sendto(data, (server_ip, server_port))
        print(f"已发送报文: 序号 {seq_no}")
        start_time = time.time()
        response, _ = client_socket.recvfrom(4096)
        rtt = (time.time() - start_time) * 1000
        RTTs.append(rtt)
        received_packets += 1

        # 解析服务器时间
        server_time_str = response[3:].decode()
        server_time = datetime.strptime(server_time_str, '%Y-%m-%d %H:%M:%S')
        if first_response_time is None:
            first_response_time = server_time
        last_response_time = server_time
        print(f"收到序号为 {seq_no}的报文, 来自服务器（{server_ip}:{server_port}）、RTT: {rtt:.3f} ms")
        return True
    except socket.timeout:
        return False

# 数据传输阶段
def tcp_transmission(client_socket):
    global received_packets, first_response_time, last_response_time
    for seq_no in range(1, sum_requests + 1):
        time.sleep(1)    # 可以用于测试多个客户端与服务器的连接
        attempts = 1
        while attempts <= max_attempts:
            if send_message(client_socket, seq_no, attempts):
                break  # 接收成功，跳出循环
            else:
                attempts += 1
        if attempts > max_attempts:
            print(f"序号为{seq_no}的报文, 请求超时！")



# 模拟TCP四次挥手
def tcp_release(client_socket):
    try:
        print(f"\n正在与服务器{(server_ip, server_port)}释放连接...")
        client_socket.sendto(b'FIN', (server_ip, server_port))
        print("已向服务器发送FIN包")
        response1, _ = client_socket.recvfrom(4096)
        response2, _ = client_socket.recvfrom(4096)
        if response1.decode() == 'FIN-ACK' and response2.decode() == 'FIN':
            print("成功收到服务器的FIN-ACK包, 正在发送 RELEASE-ACK...")
            client_socket.sendto(b'RELEASE-ACK', (server_ip, server_port))
            print(f"已发送RELEASE-ACK包，成功与服务器{(server_ip, server_port)}释放连接！")
    except Exception:
        print("与服务器的连接释放失败，连接未正常关闭！")


# 输出汇总信息
def print_result():
    global received_packets, first_response_time, last_response_time
    if RTTs:
        print(f"\n已接收 UDP packets 包数量: {received_packets}")
        print(f"丢包率: {(1 - received_packets / sum_requests) * 100:.2f}%")
        if len(RTTs) > 1:
            print(f"最大 RTT: {max(RTTs):.3f} 毫秒, 最小 RTT: {min(RTTs):.3f} 毫秒, 平均 RTT: {sum(RTTs) / len(RTTs):.3f} 毫秒, RTT 标准差: {statistics.stdev(RTTs):.3f} 毫秒")
        else:
            print(f"最大 RTT: {max(RTTs):.3f} 毫秒, 最小 RTT: {min(RTTs):.3f} 毫秒, 平均 RTT: {sum(RTTs) / len(RTTs):.3f} 毫秒, RTT无标准差（需要至少两个数据点）")
        if first_response_time and last_response_time:
            print(f"server的整体响应时间: {(last_response_time - first_response_time).total_seconds()} 秒")
    else:
        print(f"\n已接收 UDP 数据包数量：0")


def udpclient():
    # 创建UDP套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 设置套接字的超时时间
    client_socket.settimeout(timeout)

    try:
        if tcp_connect(client_socket):       # 尝试与服务器建立连接
            tcp_transmission(client_socket)  # 成功连接后进入数据传输阶段
            tcp_release(client_socket)       # 与服务器释放连接
            print_result()                   # 输出汇总信息
    finally:
        client_socket.close()  # 关闭套接字


if __name__ == "__main__":
    udpclient()