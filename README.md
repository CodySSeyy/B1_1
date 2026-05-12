# B1_1
시스템 관제 자동화 스크립트 개발

## 수행 내역
- 설정/명령어 기록 (SSH 포트, 방화벽 규칙, 계정/그룹/ACL, 디렉토리/권한, 환경 변수, cron 등록 등)

## 필수 증거 자료 체크리스트

### SSH 포트 변경(20022) 및 Root 원격 접속 차단 설정 확인 내역
</br>

1. SSH 포트 변경 (22 → 20022) 이유: "자동화된 공격 피하기"

    1-1. 무차별 대입 공격(Brute-force) 방지: 
    
    - 전 세계의 수많은 해킹 봇(Bot)들은 인터넷을 돌아다니며 기본 포트인 22번이 열려 있는 서버를 찾아 자동으로 로그인을 시도 
    - 포트를 20022 같은 임의의 번호로 바꾸는 것만으로도 이런 자동화된 공격의 99%를 걸러냄
</br></br></br>



2. Root 원격 접속 차단 (PermitRootLogin no) 이유: "최종 권한 보호"

    2-1. 아이디 추측 방지
    
    - 모든 리눅스 서버에는 반드시 root라는 아이디가 존재합니다. 해커 입장에서 아이디는 이미 알고 있으니 비밀번호만 맞추면 되는 셈입니다. 일반 사용자 계정으로만 접속하게 만들면 해커는 아이디와 비밀번호 두 가지를 모두 알아내야 하므로 공격 난이도가 비약적으로 상승

</br></br>


```
# 1. 포트 변경 및 Root 로그인 차단 설정 수정
$ sudo sed -i 's/#Port 22/Port 20022/' /etc/ssh/sshd_config
$ sudo sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config

# 2. SSH 서비스 재시작
$ sudo systemctl restart ssh

# 포트 변경 전
$ ss -tulnp
Netid      State       Recv-Q      Send-Q            Local Address:Port             Peer Address:Port      Process
tcp        LISTEN      0           4096              127.0.0.53%lo:53                    0.0.0.0:*
tcp        LISTEN      0           4096                 127.0.0.54:53                    0.0.0.0:*

# 포트 변경 후
$ ss -tulnp | grep 20022
Netid      State       Recv-Q      Send-Q            Local Address:Port             Peer Address:Port      Process
tcp   LISTEN 0      128           0.0.0.0:20022      0.0.0.0:*
tcp   LISTEN 0      128              [::]:20022         [::]:*
```
</br></br>

<span style="color:red"><b>🔴 트러블 슈팅</b></span>

### SSH Socket 설정 충돌
#### 문제 상황
sshd_config를 수정해도 포트가 바뀌지 않는 문제 발생
#### 문제 원인
최근 Ubuntu(22.10 이상)나 최신 배포판에서는 ssh.service가 아닌 ssh.socket이 포트를 관리하므로 sshd_config를 설정해도 포트가 변경되지 않는다.
#### 해결 방법
```
# 1. socket 방식인지 확인
sudo systemctl is-active ssh.socket

# 2. 만약 active라면 socket 설정 수정 필요
sudo systemctl stop ssh.socket
sudo systemctl disable ssh.socket

# 3. 서비스 방식으로 강제 재시작
sudo systemctl restart ssh
```

</br></br>
---

###  방화벽(UFW 또는 firewalld) 활성화 및 20022/tcp, 15034/tcp만 허용 내역

| 항목 | UFW (Uncomplicated Firewall) | firewalld |
| :--- | :--- | :--- |
| **개발 목적** | 사용자 편의성 및 단순함 극대화 | 동적 관리 및 엔터프라이즈 환경 대응 |
| **기본 OS** | Ubuntu, Debian 계열 | RHEL, CentOS, Fedora, AlmaLinux |
| **관리 방식** | **정적(Static)**: 규칙 변경 시 재시작 필요 | **동적(Dynamic)**: 서비스 중단 없이 적용 가능 |
| **핵심 개념** | 포트 및 서비스 위주 | **Zone(구역)** 및 서비스 위주 |
| **설정 저장** | 즉시 반영 (또는 reload 필요) | Runtime(즉시) vs Permanent(영구) 구분 |
| **난이도** | 매우 낮음 (초보자 권장) | 중간 (학습 곡선 존재) |
</br></br>

| 구분 | TCP (Transmission Control Protocol) | UDP (User Datagram Protocol) |
| :--- | :--- | :--- |
| **연결 방식** | 연결 지향형 (3-way handshake) | 비연결형 (No handshake) |
| **신뢰성** | **높음** (데이터 유실 시 재전송) | **낮음** (유실되어도 재전송 없음) |
| **전송 순서** | 보장됨 (Sequence Number 사용) | 보장되지 않음 |
| **속도** | 상대적으로 느림 (제어 로직 포함) | 매우 빠름 (단순 전송) |
| **제어 기능** | 흐름 제어, 혼잡 제어 수행 | 거의 없음 (체크섬 정도만 수행) |
| **전송 단위** | 세그먼트 (Stream 기반) | 데이터그램 (Message 기반) |
</br></br>

```
$ sudo ufw allow 20022/tcp
$ sudo ufw allow 15034/tcp
Rules updated
Rules updated (v6)

# 방화벽 확인
$ sudo ufw status
To                         Action      From
--                         ------      ----
20022/tcp                  ALLOW       Anywhere
15034/tcp                  ALLOW       Anywhere
20022/tcp (v6)             ALLOW       Anywhere (v6)
15034/tcp (v6)             ALLOW       Anywhere (v6)
```
</br></br>
---

### 계정/그룹(agent-admin/dev/test, agent-common/core) 생성 확인 내역

</br>

```
# 그룹 생성
$ sudo groupadd agent-common
$ sudo groupadd agent-core

# 그룹 생성 확인
$ sudo getent group
agent-common:x:1001:
agent-core:x:1002:

# 계정 생성 및 그룹 지정 
$ sudo useradd -m -G agent-common,agent-core agent-admin
$ sudo useradd -m -G agent-common,agent-core agent-dev
$ sudo useradd -m -G agent-common agent-test

# 계정 생성 확인
$ getent group agent-common
agent-common:x:1001:agent-admin,agent-dev,agent-test
$ getent group agent-core
agent-core:x:1002:agent-admin,agent-dev
```

### 출력 결과 해석 예시
  agent-admin:x:1001:user1,user2
   1. agent-admin: 그룹 이름
   2. x: 그룹 비밀번호 (보통 사용 안 함)
   3. 1001: 그룹 GID
</br>

### 유저 생성 시 유저 이름과 같은 그룹이 생성되는 이유
```
$ sudo useradd -m -G agent-common,agent-core agent-admin
$ getent group
agent-admin:x:1003:
```

사용자를 생성할 때 해당 사용자 전용의 그룹을 자동으로 만들고, 이를 사용자의 기본 그룹(Primary Group)으로 설정
</br>

#### 이유
만약 모든 사용자의 기본 그룹이 users나 common 같은 공통 그룹이라면 한 사용자가 파일을 만들 때 그룹 권한(rw-r-----)이 다른 사용자에게 노출될 위험이 큽니다. 

전용 그룹을 사용하면 본인 외에는 그룹 권한으로도 파일에 접근할 수 없어 안전합니다.

</br></br>
---

### 디렉토리 구조 및 권한(ACL 포함) 확인 내역

#### 접근 제어 목록(Access Control List)
Access Control List (ACL)는 파일과 디렉토리에 대해 세분화된 사용자 및 그룹 권한을 설정할 수 있게 해주는 기능입니다. 
</br>
기본적인 리눅스 권한 시스템은 소유자, 그룹, 기타에 대한 권한을 제공하는 반면, ACL을 통해서는 특정 사용자 또는 그룹에 대해 더 구체적인 권한을 부여할 수 있습니다.

#### 1.&nbsp; ACL이 필요한 이유 (기존 방식의 한계)

기존 리눅스 방식은 파일 하나당 "주인 1명, 그룹 1개"만 지정할 수 있습니다. 

   * 상황: project.txt라는 파일이 있습니다.
       * 주인: 철수 (읽기/쓰기)
       * 그룹: 개발팀 (읽기전용)
       * 나머지: 아무 권한 없음

   * 문제 발생: 갑자기 보안팀의 영희에게만 이 파일을 읽을 수 있게 해달라는 요청이 왔습니다.
       * 기존 방식으로는? 
           1. 영희를 개발팀에 넣는다? (영희가 개발팀의 다른 모든 파일까지 보게 됨 - 보안 위반)
           2. 나머지(Others)에게 읽기 권한을 준다? (전 직원이 다 보게 됨 - 보안 위반)
           3. 파일을 복사해서 준다? (데이터가 동기화 안 됨)

  이때 ACL을 쓰면 "이 파일에 대해서만 영희(특정 유저)에게 읽기 권한을 추가해!"라고 딱 집어서 명령할 수 있습니다.

#### 2.&nbsp; 주요 명령어

* getfacl (get file acl): 파일에 설정된 ACL 상세 정보를 확인합니다.
* setfacl (set file acl): 권한을 설정하거나 삭제합니다.

    sudo setfacl -d -m g:agent-common:rwx $AGENT_HOME/upload_files
    -  setfacl: "권한 목록(ACL)을 설정"
    -  -d: "앞으로 이 폴더 안에 생길 모든 파일들에게도 똑같이 적용 (Default),"
    -  -m: "기존 권한에 다음 내용을 수정/추가 (Modify)."
    -  g:agent-common:rwx: "agent-common 그룹에게 읽기/쓰기/실행(rwx) 권한 부여"
    -  $AGENT_HOME/upload_files: "대상 폴더"

</br></br>

```
# 1. 환경 변수 설정 (권장: /home/agent-admin/agent-app)
$ export AGENT_HOME=/home/agent-admin/agent-app

# 2. 디렉토리 생성 (sudo 권한 필요)
$ sudo mkdir -p $AGENT_HOME/upload_files
$ sudo mkdir -p $AGENT_HOME/api_keys
$ sudo mkdir -p /var/log/agent-app

# 3. 기본 소유권 설정 (관리자 계정 할당)
$ sudo chown agent-admin:agent-admin $AGENT_HOME

# 소유 그룹 변경 및 기본 권한(UGO) 설정
$ sudo chgrp agent-common $AGENT_HOME/upload_files
$ sudo chmod 770 $AGENT_HOME/upload_files

# ACL 적용: 그룹 권한 명시 및 향후 생성 파일 권한 상속(Default ACL)
$ sudo setfacl -m g:agent-common:rwx $AGENT_HOME/upload_files
$ sudo setfacl -d -m g:agent-common:rwx $AGENT_HOME/upload_files

# 소유 그룹 변경 및 기본 권한 설정 (Others 접근 완전 차단)
$ sudo chgrp agent-core $AGENT_HOME/api_keys /var/log/agent-app
$ sudo chmod 770 $AGENT_HOME/api_keys /var/log/agent-app

# ACL 적용: 핵심 관리 그룹(agent-core) 외 접근 불가 명시
$ sudo setfacl -m g:agent-core:rwx $AGENT_HOME/api_keys
$ sudo setfacl -m g:agent-core:rwx /var/log/agent-app
$ sudo setfacl -d -m g:agent-core:rwx /var/log/agent-app

$ getfacl $AGENT_HOME/upload_files
# file: home/agent-admin/agent-app/upload_files
# owner: root
# group: agent-common
user::rwx
group::rwx
other::---

$ getfacl $AGENT_HOME/api_keys
# file: home/agent-admin/agent-app/api_keys
# owner: root
# group: root
user::rwx
group::r-x
group:agent-core:rwx
mask::rwx
other::r-x

$getfacl /var/log/agent-app
# file: var/log/agent-app
# owner: root
# group: root
user::rwx
group::r-x
group:agent-core:rwx
mask::rwxe
other::r-x
default:user::rwx
default:group::r-x
default:group:agent-core:rwx 
default:mask::rwx
default:other::r-x
```
</br>

| 명령어 | 풀네임 | 변경 대상 (대상) | 주요 용도 |
| :--- | :--- | :--- | :--- |
| **chown** | change owner | 소유 사용자 (& 소유 그룹) | 파일의 '주인'을 바꿀 때 사용 |
| **chgrp** | change group | 소유 그룹 | 파일을 관리하는 '그룹'만 바꿀 때 사용 |
| **chmod** | change mode | 읽기/쓰기/실행 권한 | 주인이든 누구든 '할 수 있는 일'을 정할 때 사용 |

</br>

| 대상 | 파일 내용 읽기/쓰기 | 파일 설정(권한/그룹) 변경 | 파일 소유자 변경 (chown) |
| :--- | :--- | :--- | :--- |
| **소유 사용자** | 가능 (본인 설정에 따라) | 가능 | 불가능 (root만 가능) |
| **소유 그룹** | 가능 (주인이 허락한 경우) | 불가능 | 불가능 |
| **나머지(Other)** | 가능 (주인이 허락한 경우) | 불가능 | 불가능 |
| **Root 계정** | **무조건 가능** | **무조건 가능** | **무조건 가능** |
</br></br>
---

### 앱 Boot Sequence 5단계 [OK] 및 “Agent READY” 확인 내역

```
# agent-admin 으로 계정으로 접속
$ sudo su agent-admin

# 1. ~/.bashrc 파일 끝에 환경 변수 블록 추가
$ cat << 'EOF' >> ~/.bashrc

export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys/t_secret.key
export AGENT_LOG_DIR=/var/log/agent-app
EOF

# 2. 수정된 내용을 현재 터미널에 즉시 반영
$ source ~/.bashrc



```

- monitor.sh 실행 결과(프로세스/포트/리소스/경고) 내역
- /var/log/agent-app/monitor.log 누적 기록 확인(최근 라인) 내역
- crontab 매분 실행 등록 및 자동 실행 확인(1분 후 로그 증가) 내역

## 자동화 스크립트 소스코드
- monitor.sh : 시스템 상태 수집 및 로깅 스크립트

---
- SSH 포트 변경과 Root 원격 접속 차단이 왜 기본 보안에 해당하는지 설명할 수 있다.

- UFW 또는 firewalld 중 하나를 선택해 “필요 포트만 허용”하는 방화벽 정책을 구성하고 검증할 수 있다.
- 역할 기반 계정/그룹과 ACL을 통해 “공유 디렉토리”와 “보안 디렉토리”를 분리하는 이유를 설명할 수 있다.
- 환경 변수(AGENT_HOME 등)로 실행 환경을 고정하는 이유와 검증 방법을 설명할 수 있다.
- 쉘 스크립트로 프로세스/포트/리소스 상태를 수집하고, 로그로 남겨 운영 문제를 추적하는 흐름을 설명할 수 있다.
- crontab으로 모니터링을 주기 실행시키고, 로그 보존 정책(압축/삭제)이 왜 필요한지 설명할 수 있다.