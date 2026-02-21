#!/bin/bash
###############################################################################
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHITELIST_FILE="${SCRIPT_DIR}/process_whitelist.json"

OUTPUT_DIR="/tmp/linux_audit_$(date +%Y%m%d_%H%M%S)"
JSON_OUTPUT="${OUTPUT_DIR}/audit_data.json"
mkdir -p "$OUTPUT_DIR"

# 颜色定义（用于终端输出）
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}   Linux系统进程与端口自动分析脚本${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

###############################################################################
# 第一部分：收集系统基本信息
###############################################################################
echo -e "${GREEN}[1/5] 正在收集系统基本信息...${NC}"

# 获取系统信息
HOSTNAME=$(hostname)
OS_NAME=$(cat /etc/os-release 2>/dev/null | grep "^NAME=" | cut -d'"' -f2 || echo "Unknown")
OS_VERSION=$(cat /etc/os-release 2>/dev/null | grep "^VERSION=" | cut -d'"' -f2 || echo "Unknown")
OS_ID=$(cat /etc/os-release 2>/dev/null | grep "^ID=" | cut -d'"' -f2 || echo "unknown")
KERNEL_VERSION=$(uname -r)
ARCH=$(uname -m)
UPTIME=$(uptime -p 2>/dev/null || uptime)
CPU_INFO=$(grep "model name" /proc/cpuinfo | head -1 | cut -d':' -f2 | xargs)
CPU_CORES=$(nproc)
MEMORY_TOTAL=$(free -h 2>/dev/null | awk '/^Mem:/ {print $2}' || echo "N/A")
MEMORY_USED=$(free -h 2>/dev/null | awk '/^Mem:/ {print $3}' || echo "N/A")
DISK_USAGE=$(df -h / 2>/dev/null | awk 'NR==2 {print $3"/"$2" ("$5")"}' || echo "N/A")
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")

echo "  主机名: $HOSTNAME"
echo "  操作系统: $OS_NAME $OS_VERSION"
echo "  内核版本: $KERNEL_VERSION"
echo "  架构: $ARCH"
echo "  运行时间: $UPTIME"

###############################################################################
# 第二部分：收集所有进程信息
###############################################################################
echo -e "${GREEN}[2/5] 正在收集进程信息...${NC}"

# 获取所有进程详细信息
ps aux > "${OUTPUT_DIR}/all_processes.txt"

# 获取进程树
pstree -p 2>/dev/null > "${OUTPUT_DIR}/process_tree.txt" || echo "pstree not available" > "${OUTPUT_DIR}/process_tree.txt"

# 统计进程数量
TOTAL_PROCESSES=$(wc -l < "${OUTPUT_DIR}/all_processes.txt")
TOTAL_PROCESSES=$((TOTAL_PROCESSES - 1))  # 减去标题行
echo "  发现进程数量: $TOTAL_PROCESSES"

# 获取各用户进程数量
USER_PROCESSES=$(tail -n +2 "${OUTPUT_DIR}/all_processes.txt" 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn | awk '{printf "  %-10s %d个进程\n", $2, $1}')

# 获取CPU占用前十的进程
echo "  CPU占用前十的进程:"
CPU_TOP10=$(tail -n +2 "${OUTPUT_DIR}/all_processes.txt" 2>/dev/null | sort -nrk 3 | head -10 | awk '{printf "  PID:%-6s CPU:%-5s MEM:%-5s USER:%-10s COMMAND:%s\n", $2, $3, $4, $1, $11}')
echo "$CPU_TOP10"

# 获取内存占用前十的进程
echo "  内存占用前十的进程:"
MEM_TOP10=$(tail -n +2 "${OUTPUT_DIR}/all_processes.txt" 2>/dev/null | sort -nrk 4 | head -10 | awk '{printf "  PID:%-6s CPU:%-5s MEM:%-5s USER:%-10s COMMAND:%s\n", $2, $3, $4, $1, $11}')
echo "$MEM_TOP10"

###############################################################################
# 第三部分：收集端口信息
###############################################################################
echo -e "${GREEN}[3/5] 正在收集端口信息...${NC}"

# 获取所有监听端口
if command -v ss &> /dev/null; then
    ss -tulnp > "${OUTPUT_DIR}/listening_ports.txt" 2>/dev/null
    PORT_INFO=$(ss -tulnp 2>/dev/null)
elif command -v netstat &> /dev/null; then
    netstat -tulnp > "${OUTPUT_DIR}/listening_ports.txt" 2>/dev/null
    PORT_INFO=$(netstat -tulnp 2>/dev/null)
else
    echo "  警告: 未找到ss或netstat命令"
    PORT_INFO=""
fi

# 统计端口数量
LISTENING_PORTS=$(echo "$PORT_INFO" | grep -c "LISTEN" 2>/dev/null || echo "0")
echo "  监听端口数量: $LISTENING_PORTS"

# 获取已建立连接
ESTABLISHED_CONN=$(echo "$PORT_INFO" | grep -c "ESTAB" 2>/dev/null | tr -d '\n' || echo "0")

###############################################################################
# 第四部分：系统默认进程对比分析
###############################################################################
echo -e "${GREEN}[4/5] 正在进行进程对比分析...${NC}"

# 定义各发行版的默认系统进程
get_default_processes() {
    local os_id=$1
    case "$os_id" in
        ubuntu|debian)
            echo "systemd systemd-journal systemd-network systemd-resolve dbus cron rsyslogd sshd agetty polkitd unattended-upgr networkd-dispa"
            ;;
        centos|rhel|fedora|rocky|almalinux)
            echo "systemd systemd-journal systemd-network systemd-resolve dbus crond rsyslogd sshd agetty polkitd NetworkManager tuned"
            ;;
        alpine)
            echo "init crond syslogd sshd getty"
            ;;
        arch|manjaro)
            echo "systemd systemd-journal systemd-network systemd-resolve dbus cronie rsyslogd sshd agetty polkitd NetworkManager"
            ;;
        suse|opensuse*)
            echo "systemd systemd-journal systemd-network systemd-resolve dbus cron rsyslogd sshd agetty polkitd NetworkManager"
            ;;
        *)
            echo "systemd dbus cron rsyslogd sshd"
            ;;
    esac
}

DEFAULT_PROCS=""
if command -v python3 &> /dev/null && [ -f "$WHITELIST_FILE" ]; then
    DEFAULT_PROCS=$(python3 - "$OS_ID" "$WHITELIST_FILE" << 'PY'
import sys
import json

os_id = sys.argv[1]
path = sys.argv[2]

data = {}
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    data = {}

values = data.get(os_id) or data.get("default") or []
names = []

if isinstance(values, dict):
    values = values.get("items", [])

for item in values:
    if isinstance(item, str):
        names.append(item)
    elif isinstance(item, dict):
        name = item.get("name")
        if name:
            names.append(str(name))

print(" ".join(names))
PY
)
fi

if [ -z "$DEFAULT_PROCS" ]; then
    DEFAULT_PROCS=$(get_default_processes "$OS_ID")
fi

# 分析进程
analyze_processes() {
    local suspicious_procs=""
    local system_procs=""
    local user_procs=""
    local unknown_procs=""
    
    # 读取进程列表（跳过标题行）
    tail -n +2 "${OUTPUT_DIR}/all_processes.txt" | while read -r line; do
        user=$(echo "$line" | awk '{print $1}')
        pid=$(echo "$line" | awk '{print $2}')
        cpu=$(echo "$line" | awk '{print $3}')
        mem=$(echo "$line" | awk '{print $4}')
        cmd=$(echo "$line" | awk '{print $11}')
        proc_name=$(basename "$cmd" 2>/dev/null || echo "$cmd")
        
        # 判断进程类型
        is_default=0
        for default_proc in $DEFAULT_PROCS; do
            if echo "$proc_name" | grep -q "$default_proc"; then
                is_default=1
                break
            fi
        done
        
        # 输出进程信息
        if [ "$user" = "root" ]; then
            if [ $is_default -eq 1 ]; then
                echo "{\"type\":\"system\",\"user\":\"$user\",\"pid\":$pid,\"cpu\":\"$cpu\",\"mem\":\"$mem\",\"name\":\"$proc_name\",\"cmd\":\"$cmd\"}"
            else
                # 检查是否为可疑进程
                if echo "$cmd" | grep -qE "(nc|netcat|ncat|python.*-c|perl.*-e|bash.*-i|sh.*-i|curl.*\||wget.*\||base64|eval|exec)"; then
                    echo "{\"type\":\"suspicious\",\"user\":\"$user\",\"pid\":$pid,\"cpu\":\"$cpu\",\"mem\":\"$mem\",\"name\":\"$proc_name\",\"cmd\":\"$cmd\"}"
                else
                    echo "{\"type\":\"root_other\",\"user\":\"$user\",\"pid\":$pid,\"cpu\":\"$cpu\",\"mem\":\"$mem\",\"name\":\"$proc_name\",\"cmd\":\"$cmd\"}"
                fi
            fi
        elif [ "$user" = "$(whoami)" ] || [ "$user" != "root" ]; then
            echo "{\"type\":\"user\",\"user\":\"$user\",\"pid\":$pid,\"cpu\":\"$cpu\",\"mem\":\"$mem\",\"name\":\"$proc_name\",\"cmd\":\"$cmd\"}"
        fi
    done
}

# 执行分析
PROCESS_ANALYSIS=$(analyze_processes)

# 分类统计
SYSTEM_PROC_COUNT=$(echo "$PROCESS_ANALYSIS" | grep -c '"type":"system"' || echo "0")
USER_PROC_COUNT=$(echo "$PROCESS_ANALYSIS" | grep -c '"type":"user"' || echo "0")
ROOT_OTHER_COUNT=$(echo "$PROCESS_ANALYSIS" | grep -c '"type":"root_other"' || echo "0")
SUSPICIOUS_COUNT=$(echo "$PROCESS_ANALYSIS" | grep -c '"type":"suspicious"' || echo "0")

echo "  系统进程: $SYSTEM_PROC_COUNT"
echo "  用户进程: $USER_PROC_COUNT"
echo "  Root其他进程: $ROOT_OTHER_COUNT"
if [ "$SUSPICIOUS_COUNT" -gt 0 ]; then
    echo -e "  ${RED}警告: 发现 $SUSPICIOUS_COUNT 个可疑进程!${NC}"
fi

###############################################################################
# 第五部分：端口详细分析
###############################################################################
echo -e "${GREEN}[5/5] 正在分析端口信息...${NC}"

analyze_ports() {
    if command -v ss &> /dev/null; then
        ss -tulnp 2>/dev/null | grep "LISTEN" | while read -r line; do
            proto=$(echo "$line" | awk '{print $1}')
            local_addr=$(echo "$line" | awk '{print $5}')
            port=$(echo "$local_addr" | awk -F':' '{print $NF}')
            process=$(echo "$line" | grep -oP 'users:\(\("\K[^"]+' || echo "unknown")
            
            # 判断端口风险级别
            risk="low"
            case "$port" in
                22|80|443)
                    risk="normal"
                    ;;
                21|23|25|110|143|3306|5432|6379|8080|8443)
                    risk="medium"
                    ;;
                135|139|445|1433|3389|5900|6666|6667)
                    risk="high"
                    ;;
                *)
                    if [ "$port" -gt 49152 ]; then
                        risk="dynamic"
                    fi
                    ;;
            esac
            
            echo "{\"proto\":\"$proto\",\"port\":$port,\"address\":\"$local_addr\",\"process\":\"$process\",\"risk\":\"$risk\"}"
        done
    elif command -v netstat &> /dev/null; then
        netstat -tulnp 2>/dev/null | grep "LISTEN" | while read -r line; do
            proto=$(echo "$line" | awk '{print $1}')
            local_addr=$(echo "$line" | awk '{print $4}')
            port=$(echo "$local_addr" | awk -F':' '{print $NF}')
            process=$(echo "$line" | awk '{print $7}' | cut -d'/' -f2 || echo "unknown")
            pid=$(echo "$line" | awk '{print $7}' | cut -d'/' -f1 || echo "0")
            
            risk="low"
            case "$port" in
                22|80|443)
                    risk="normal"
                    ;;
                21|23|25|110|143|3306|5432|6379|8080|8443)
                    risk="medium"
                    ;;
                135|139|445|1433|3389|5900|6666|6667)
                    risk="high"
                    ;;
                *)
                    if [ "$port" -gt 49152 ]; then
                        risk="dynamic"
                    fi
                    ;;
            esac
            
            echo "{\"proto\":\"$proto\",\"port\":$port,\"address\":\"$local_addr\",\"process\":\"$process\",\"risk\":\"$risk\"}"
        done
    fi
}

PORT_ANALYSIS=$(analyze_ports)

# 统计风险端口
HIGH_RISK_PORTS=$(echo "$PORT_ANALYSIS" | grep -c '"risk":"high"' 2>/dev/null | tr -d '\n' || echo "0")
MEDIUM_RISK_PORTS=$(echo "$PORT_ANALYSIS" | grep -c '"risk":"medium"' 2>/dev/null | tr -d '\n' || echo "0")
NORMAL_PORTS=$(echo "$PORT_ANALYSIS" | grep -c '"risk":"normal"' 2>/dev/null | tr -d '\n' || echo "0")

# 确保变量为数字
HIGH_RISK_PORTS=${HIGH_RISK_PORTS:-0}
MEDIUM_RISK_PORTS=${MEDIUM_RISK_PORTS:-0}
NORMAL_PORTS=${NORMAL_PORTS:-0}

echo "  正常端口: $NORMAL_PORTS"
echo "  中风险端口: $MEDIUM_RISK_PORTS"
if [ "$HIGH_RISK_PORTS" -gt 0 ] 2>/dev/null; then
    echo -e "  ${RED}高风险端口: $HIGH_RISK_PORTS${NC}"
fi

###############################################################################
# 第六部分：生成JSON报告数据
###############################################################################
echo -e "${GREEN}正在生成JSON报告数据...${NC}"

# 构建JSON
cat > "$JSON_OUTPUT" << EOJSON
{
    "audit_info": {
        "hostname": "$HOSTNAME",
        "os_name": "$OS_NAME",
        "os_version": "$OS_VERSION",
        "os_id": "$OS_ID",
        "kernel": "$KERNEL_VERSION",
        "architecture": "$ARCH",
        "uptime": "$UPTIME",
        "audit_time": "$CURRENT_TIME",
        "cpu_info": "$CPU_INFO",
        "cpu_cores": $CPU_CORES,
        "memory_total": "$MEMORY_TOTAL",
        "memory_used": "$MEMORY_USED",
        "disk_usage": "$DISK_USAGE"
    },
    "process_summary": {
        "total_processes": $TOTAL_PROCESSES,
        "system_processes": $SYSTEM_PROC_COUNT,
        "user_processes": $USER_PROC_COUNT,
        "root_other_processes": $ROOT_OTHER_COUNT,
        "suspicious_processes": $SUSPICIOUS_COUNT
    },
    "port_summary": {
        "total_listening": $LISTENING_PORTS,
        "established_connections": ${ESTABLISHED_CONN:-0},
        "normal_ports": ${NORMAL_PORTS:-0},
        "medium_risk_ports": ${MEDIUM_RISK_PORTS:-0},
        "high_risk_ports": ${HIGH_RISK_PORTS:-0}
    },
    "processes": [
EOJSON

# 添加进程详情
first=1
echo "$PROCESS_ANALYSIS" | while read -r proc; do
    if [ -n "$proc" ]; then
        if [ $first -eq 1 ]; then
            first=0
        else
            echo "," >> "$JSON_OUTPUT"
        fi
        echo -n "        $proc" >> "$JSON_OUTPUT"
    fi
done

echo "" >> "$JSON_OUTPUT"
echo "    ]," >> "$JSON_OUTPUT"
echo '    "ports": [' >> "$JSON_OUTPUT"

# 添加端口详情
first=1
echo "$PORT_ANALYSIS" | while read -r port; do
    if [ -n "$port" ]; then
        if [ $first -eq 1 ]; then
            first=0
        else
            echo "," >> "$JSON_OUTPUT"
        fi
        echo -n "        $port" >> "$JSON_OUTPUT"
    fi
done

echo "" >> "$JSON_OUTPUT"
echo "    ]," >> "$JSON_OUTPUT"

# 添加用户进程统计
echo '    "user_process_stats": [' >> "$JSON_OUTPUT"
tail -n +2 "${OUTPUT_DIR}/all_processes.txt" 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn | head -10 | while read -r line; do
    count=$(echo "$line" | awk '{print $1}')
    user=$(echo "$line" | awk '{print $2}')
    if [ -n "$prev" ]; then
        echo "," >> "$JSON_OUTPUT"
    fi
    echo -n "        {\"user\": \"$user\", \"count\": $count}" >> "$JSON_OUTPUT"
    prev=1
done

echo "" >> "$JSON_OUTPUT"
echo "    ]," >> "$JSON_OUTPUT"

# 添加CPU占用前十的进程
echo '    "cpu_top_processes": [' >> "$JSON_OUTPUT"
prev=""
tail -n +2 "${OUTPUT_DIR}/all_processes.txt" 2>/dev/null | sort -nrk 3 | head -10 | while read -r line; do
    user=$(echo "$line" | awk '{print $1}')
    pid=$(echo "$line" | awk '{print $2}')
    cpu=$(echo "$line" | awk '{print $3}')
    mem=$(echo "$line" | awk '{print $4}')
    cmd=$(echo "$line" | awk '{print $11}')
    proc_name=$(basename "$cmd" 2>/dev/null || echo "$cmd")
    if [ -n "$prev" ]; then
        echo "," >> "$JSON_OUTPUT"
    fi
    echo -n "        {\"user\": \"$user\", \"pid\": $pid, \"cpu\": \"$cpu\", \"mem\": \"$mem\", \"name\": \"$proc_name\", \"cmd\": \"$cmd\"}" >> "$JSON_OUTPUT"
    prev=1
done

echo "" >> "$JSON_OUTPUT"
echo "    ]," >> "$JSON_OUTPUT"

# 添加内存占用前十的进程
echo '    "mem_top_processes": [' >> "$JSON_OUTPUT"
prev=""
tail -n +2 "${OUTPUT_DIR}/all_processes.txt" 2>/dev/null | sort -nrk 4 | head -10 | while read -r line; do
    user=$(echo "$line" | awk '{print $1}')
    pid=$(echo "$line" | awk '{print $2}')
    cpu=$(echo "$line" | awk '{print $3}')
    mem=$(echo "$line" | awk '{print $4}')
    cmd=$(echo "$line" | awk '{print $11}')
    proc_name=$(basename "$cmd" 2>/dev/null || echo "$cmd")
    if [ -n "$prev" ]; then
        echo "," >> "$JSON_OUTPUT"
    fi
    echo -n "        {\"user\": \"$user\", \"pid\": $pid, \"cpu\": \"$cpu\", \"mem\": \"$mem\", \"name\": \"$proc_name\", \"cmd\": \"$cmd\"}" >> "$JSON_OUTPUT"
    prev=1
done

echo "" >> "$JSON_OUTPUT"
echo "    ]" >> "$JSON_OUTPUT"
echo "}" >> "$JSON_OUTPUT"

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}   数据收集完成!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo "输出文件:"
echo "  JSON数据: $JSON_OUTPUT"
echo "  进程列表: ${OUTPUT_DIR}/all_processes.txt"
echo "  端口列表: ${OUTPUT_DIR}/listening_ports.txt"
echo "  进程树:   ${OUTPUT_DIR}/process_tree.txt"
echo ""
echo -e "${YELLOW}提示: 运行以下命令生成PDF报告:${NC}"
echo "  python3 /mnt/okcomputer/output/linux_audit/generate_pdf_report.py $JSON_OUTPUT"
echo ""

# 输出JSON路径（供其他脚本使用）
echo "$JSON_OUTPUT"
