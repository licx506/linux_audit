# Linux系统进程与端口自动分析脚本

一个功能强大的Linux系统安全巡检工具，能够自动收集系统进程和端口信息，与系统默认进程白名单进行对比分析，并生成专业的PDF巡检报告。

## 功能特性

- **系统信息收集**：自动收集主机名、操作系统版本、内核版本、硬件配置等基本信息
- **进程全面分析**：
  - 列出所有运行中的进程
  - 与系统默认进程白名单进行对比
  - 识别系统进程、用户进程和可疑进程
  - 检测潜在的安全威胁
- **用户分析**：
  - 统计各用户进程数量和类型分布
  - 标记存在可疑进程的用户
- **白名单配置**：
  - 使用 JSON 文件配置各发行版默认系统进程
  - 每个白名单条目支持描述和风险等级
  - 提供 Web 页面可视化编辑白名单
- **端口安全扫描**：
  - 列出所有监听端口
  - 识别高风险和中风险端口
  - 分析端口所属进程
- **PDF报告生成**：生成专业格式的巡检报告，包含：
  - 执行摘要和风险评估
  - 详细的进程、用户和端口分析
  - 安全建议和加固方案
  - 附录参考资料

## 文件说明

```
linux_audit/
├── linux_process_audit.sh    # 数据收集与分析脚本
├── generate_pdf_report.py    # PDF报告生成脚本（基于 reportlab）
├── run_audit.sh              # 一键运行脚本（支持编辑白名单）
├── process_whitelist.json    # 进程白名单配置（按发行版划分，含描述和风险）
├── whitelist_editor.py       # Web 白名单编辑器
├── font/                     # PDF 生成所需中文字体
└── README.md                 # 使用说明
```

## 系统要求

- Linux操作系统（支持Ubuntu、Debian、CentOS、RHEL、Fedora、Rocky、AlmaLinux、Alpine、Arch、openSUSE等）
- Bash 4.0+
- Python 3.6+（用于生成PDF和运行白名单编辑器）
- Python `reportlab` 库（用于PDF生成）
- 以下命令（通常已预装）：
  - `ps` - 进程查看
  - `ss` 或 `netstat` - 网络连接查看
  - `pstree` - 进程树查看（可选）

## 安装依赖

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip net-tools psmisc
pip3 install reportlab
```

### CentOS/RHEL/Fedora
```bash
sudo yum install -y python3 python3-pip net-tools psmisc
pip3 install reportlab
# 或
sudo dnf install -y python3 python3-pip net-tools psmisc
pip3 install reportlab
```

### Alpine
```bash
apk add python3 py3-pip net-tools psmisc
pip3 install reportlab
```

## 使用方法

### 方法一：一键运行（推荐）

```bash
cd linux_audit
chmod +x run_audit.sh
sudo bash run_audit.sh
```

### 方法二：分步执行

1. **收集系统数据**
   ```bash
   sudo bash linux_process_audit.sh
   ```
   脚本会输出JSON数据文件路径。

2. **生成PDF报告**
   ```bash
   python3 generate_pdf_report.py /tmp/linux_audit_*/audit_data.json
   ```

### 方法三：仅收集数据

如果只需要原始数据，可以只运行数据收集脚本：

```bash
sudo bash linux_process_audit.sh
```

数据将保存在 `/tmp/linux_audit_YYYYMMDD_HHMMSS/` 目录下。

### 方法四：编辑进程白名单（Web 页面）

使用内置 Web 编辑器可视化维护各发行版的系统进程白名单：

```bash
cd linux_audit
sudo bash run_audit.sh edit-whitelist
```

脚本会在本机启动一个 HTTP 服务（默认 `http://127.0.0.1:8000/`），并尝试自动打开浏览器。你可以在页面中直接编辑 `process_whitelist.json`，包括每个进程的名称、描述和风险等级。

## 输出文件

运行完成后，会生成以下文件：

- **PDF报告**：`linux_process_audit_report_YYYYMMDD_HHMMSS.pdf`
- **原始数据**：`audit_data.json`
- **进程列表**：`all_processes.txt`
- **端口列表**：`listening_ports.txt`
- **进程树**：`process_tree.txt`

## 报告内容

生成的PDF报告包含以下章节：

1. **执行摘要**
   - 巡检概况
   - 关键发现
   - 风险评估

2. **系统基本信息**
   - 硬件信息（CPU、内存）
   - 系统状态（OS版本、内核、运行时间）

3. **用户分析**
   - 用户进程数量分布
   - 各类型进程（系统 / 用户 / Root 其他 / 可疑）在用户间的分布
   - 存在可疑进程的用户列表

4. **进程分析**
   - 进程概览和统计
   - 系统进程详情
   - 用户进程详情
   - CPU / 内存占用前十进程
   - 可疑进程分析

5. **端口分析**
   - 端口概览
   - 监听端口详情
   - 风险端口识别

6. **安全建议**
   - 进程安全建议
   - 端口安全建议
   - 系统加固建议

7. **附录**
   - 常见端口参考
   - 脚本使用说明
   - 报告信息

## 风险等级说明

### 进程风险

- **系统进程**：与系统默认进程白名单匹配的进程，通常为操作系统核心服务
- **用户进程**：普通用户运行的应用
- **可疑进程**：可能包含恶意代码或异常行为的进程

### 端口风险

- **正常**：常用服务端口（22/SSH、80/HTTP、443/HTTPS）
- **中风险**：需要关注的服务端口（21/FTP、23/Telnet、3306/MySQL等）
- **高风险**：潜在危险端口（135/139/445/SMB、3389/RDP等）
- **动态端口**：临时端口（>49152）

## 可疑进程检测规则

脚本会标记包含以下特征的可疑进程：

- 包含 `nc`、`netcat`、`ncat`（网络工具）
- 包含 `python -c`、`perl -e`（内联代码执行）
- 包含 `bash -i`、`sh -i`（交互式Shell）
- 包含 `curl |`、`wget |`（管道下载执行）
- 包含 `base64`、`eval`、`exec`（编码执行）

## 自定义配置

### 修改默认进程白名单

默认系统进程白名单保存在 `process_whitelist.json` 中，按发行版 `ID`（例如 `ubuntu`、`centos`、`alpine`）划分：

```json
{
  "ubuntu": [
    {
      "name": "systemd",
      "desc": "系统初始化与服务管理",
      "risk": "low"
    },
    {
      "name": "sshd",
      "desc": "SSH 远程登录服务",
      "risk": "medium"
    }
  ]
}
```

- `name`：进程名（用于匹配 `ps` 输出中的进程名称）
- `desc`：该进程的功能描述
- `risk`：该系统进程本身的风险等级（low / medium / high）

推荐使用一键命令启动 Web 编辑器进行修改：

```bash
cd linux_audit
sudo bash run_audit.sh edit-whitelist
```

高级用法：仍然可以编辑 `linux_process_audit.sh` 中的 `get_default_processes` 函数，作为白名单的兜底配置（当 JSON 文件缺失或解析失败时使用）。

### 修改端口风险等级

编辑 `linux_process_audit.sh` 中的 `analyze_ports` 函数，修改端口风险判断：

```bash
case "$port" in
    22|80|443)
        risk="normal"
        ;;
    你的端口)
        risk="你的风险等级"
        ;;
esac
```

## 常见问题

### Q: 脚本需要root权限吗？
A: 建议使用root权限运行，以获取完整的进程和端口信息。非root用户可能无法查看所有进程。

### Q: PDF生成失败怎么办？
A: 请检查以下内容：
- 是否已安装 Python 3（`python3 --version`）
- 是否已安装 `reportlab` 库（`python3 -c "import reportlab"`）

如果未安装 `reportlab`，可以使用：

```bash
pip3 install reportlab
```

### Q: 如何查看历史报告？
A: 所有报告和数据都保存在 `/tmp/linux_audit_*/` 目录下，按时间命名。

### Q: 支持哪些Linux发行版？
A: 支持Ubuntu、Debian、CentOS、RHEL、Fedora、Rocky Linux、AlmaLinux、Alpine、Arch Linux、openSUSE等主流发行版。

### Q: 如何定期自动运行？
A: 可以添加到crontab：
```bash
# 每天凌晨2点运行
0 2 * * * cd /path/to/linux_audit && sudo bash run_audit.sh
```

## 安全提示

1. 本脚本仅用于系统安全巡检，不会修改系统配置
2. 建议在非生产环境先测试
3. 对于标记的可疑进程，请人工核实后再采取行动
4. 定期检查系统日志，配合本工具使用效果更佳

## 许可证

MIT License

## 更新日志

### v1.0 (2024)
- 初始版本发布
- 支持主流Linux发行版
- 进程和端口分析功能
- PDF报告生成功能
