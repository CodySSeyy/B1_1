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

- 방화벽(UFW 또는 firewalld) 활성화 및 20022/tcp, 15034/tcp만 허용 내역
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

- 계정/그룹(agent-admin/dev/test, agent-common/core) 생성 확인 내역
- 디렉토리 구조 및 권한(ACL 포함) 확인 내역
- 앱 Boot Sequence 5단계 [OK] 및 “Agent READY” 확인 내역
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